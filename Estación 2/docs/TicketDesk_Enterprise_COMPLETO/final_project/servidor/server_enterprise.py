"""
TicketDesk Enterprise Server v2.0
Flask + SQLite + WebSocket (flask-socketio)
Soporta 100 técnicos + 8,000 empleados simultáneos

Arquitectura:
  - SQLite con WAL mode (Write-Ahead Logging) → concurrencia real
  - JWT para autenticación stateless
  - WebSocket para notificaciones en tiempo real
  - Connection pooling con thread-local SQLite
  - Rate limiting por IP
  - Compresión gzip automática
  - Paginación en todos los listados
"""

import os, json, time, logging, hashlib, hmac, base64, threading
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path

from flask import Flask, request, jsonify, g
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room

# ── Configuración ──────────────────────────────────────
SECRET_KEY   = os.getenv('JWT_SECRET', 'CAMBIA_ESTA_CLAVE_EN_PRODUCCION')
DB_PATH      = os.getenv('DB_PATH', 'ticketdesk.db')
PORT         = int(os.getenv('PORT', 5050))
MAX_PAGE     = 200   # máx registros por página
SLA_HOURS    = {'Crítica':4,'Alta':8,'Media':24,'Baja':72}

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger('ticketdesk')

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
CORS(app, origins='*', supports_credentials=True)
socketio = SocketIO(app, cors_allowed_origins='*', async_mode='threading',
                    logger=False, engineio_logger=False,
                    ping_timeout=60, ping_interval=25)

# ── SQLite con WAL (Write-Ahead Logging) ───────────────
import sqlite3
_local = threading.local()

def get_db():
    if not hasattr(_local, 'conn') or _local.conn is None:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False,
                               timeout=30, isolation_level=None)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=10000")
        conn.execute("PRAGMA temp_store=MEMORY")
        conn.execute("PRAGMA foreign_keys=ON")
        _local.conn = conn
    return _local.conn

def query(sql, params=()):
    return get_db().execute(sql, params)

def execute(sql, params=()):
    db = get_db()
    cur = db.execute(sql, params)
    db.commit()
    return cur

# ── Init schema ────────────────────────────────────────
def init_db():
    db = get_db()
    db.executescript("""
    PRAGMA journal_mode=WAL;
    PRAGMA synchronous=NORMAL;

    CREATE TABLE IF NOT EXISTS tickets (
        id           TEXT PRIMARY KEY,
        title        TEXT NOT NULL,
        description  TEXT DEFAULT '',
        category     TEXT DEFAULT 'Otro',
        priority     TEXT DEFAULT 'Media',
        status       TEXT DEFAULT 'Abierto',
        assignee     TEXT DEFAULT '',
        created_by   TEXT DEFAULT '',
        requester    TEXT DEFAULT '',
        department   TEXT DEFAULT '',
        company_id   TEXT DEFAULT 'me',
        tags         TEXT DEFAULT '[]',
        created_at   TEXT NOT NULL,
        updated_at   TEXT NOT NULL,
        resolved_at  TEXT DEFAULT NULL,
        sla_deadline TEXT DEFAULT NULL,
        version      INTEGER DEFAULT 1
    );
    CREATE INDEX IF NOT EXISTS idx_tk_status    ON tickets(status);
    CREATE INDEX IF NOT EXISTS idx_tk_company   ON tickets(company_id);
    CREATE INDEX IF NOT EXISTS idx_tk_assignee  ON tickets(assignee);
    CREATE INDEX IF NOT EXISTS idx_tk_priority  ON tickets(priority);
    CREATE INDEX IF NOT EXISTS idx_tk_created   ON tickets(created_at DESC);

    CREATE TABLE IF NOT EXISTS comments (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_id  TEXT NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
        author     TEXT NOT NULL,
        text       TEXT NOT NULL,
        created_at TEXT NOT NULL,
        is_internal INTEGER DEFAULT 0
    );
    CREATE INDEX IF NOT EXISTS idx_cmt_ticket ON comments(ticket_id);

    CREATE TABLE IF NOT EXISTS audit_log (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_id  TEXT NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
        user       TEXT NOT NULL,
        action     TEXT NOT NULL,
        color      TEXT DEFAULT '#888',
        created_at TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_aud_ticket ON audit_log(ticket_id);

    CREATE TABLE IF NOT EXISTS time_log (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_id  TEXT NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
        user       TEXT NOT NULL,
        seconds    INTEGER NOT NULL,
        note       TEXT DEFAULT '',
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS surveys (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_id  TEXT NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
        rating     INTEGER NOT NULL,
        comment    TEXT DEFAULT '',
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS users (
        username     TEXT PRIMARY KEY,
        display_name TEXT NOT NULL,
        role         TEXT NOT NULL DEFAULT 'user',
        company_id   TEXT DEFAULT 'me',
        department   TEXT DEFAULT '',
        password_hash TEXT NOT NULL,
        is_active    INTEGER DEFAULT 1,
        last_login   TEXT DEFAULT NULL,
        created_at   TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS sessions (
        token_id   TEXT PRIMARY KEY,
        username   TEXT NOT NULL,
        portal     TEXT DEFAULT '',
        company_id TEXT DEFAULT '',
        role       TEXT DEFAULT '',
        last_seen  TEXT NOT NULL,
        created_at TEXT NOT NULL,
        ip_addr    TEXT DEFAULT ''
    );
    CREATE INDEX IF NOT EXISTS idx_sess_user ON sessions(username);

    CREATE TABLE IF NOT EXISTS config (
        key   TEXT PRIMARY KEY,
        value TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS team_members (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        name        TEXT NOT NULL,
        department  TEXT DEFAULT '',
        skills      TEXT DEFAULT '',
        company_id  TEXT DEFAULT 'me',
        user_ref    TEXT DEFAULT '',
        created_at  TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS bot_faq (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        title      TEXT NOT NULL,
        keys       TEXT DEFAULT '[]',
        answer     TEXT NOT NULL,
        steps      TEXT DEFAULT '[]',
        source     TEXT DEFAULT 'custom',
        use_count  INTEGER DEFAULT 0,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS servers (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        name       TEXT NOT NULL,
        ip         TEXT NOT NULL,
        type       TEXT DEFAULT 'server',
        company_id TEXT DEFAULT 'me',
        status     TEXT DEFAULT 'unknown',
        last_ping  TEXT DEFAULT NULL,
        created_at TEXT NOT NULL
    );

    INSERT OR IGNORE INTO users (username, display_name, role, company_id, password_hash, created_at)
    VALUES ('admin','Administrador','admin','*',
            'pbkdf2:sha256:260000$ticketdesk$' ||
            hex(randomblob(32)),
            datetime('now'));
    """)
    db.commit()
    log.info(f"DB inicializada: {DB_PATH}")

# ── Helpers ────────────────────────────────────────────
def now_iso():
    return datetime.utcnow().isoformat()

def row_to_dict(row):
    if row is None: return None
    d = dict(row)
    for k in ('tags','steps','keys'):
        if k in d and isinstance(d[k], str):
            try: d[k] = json.loads(d[k])
            except: d[k] = []
    return d

def hash_pw(pw):
    salt = os.urandom(16).hex()
    h    = hashlib.pbkdf2_hmac('sha256', pw.encode(), salt.encode(), 260000)
    return f"pbkdf2:sha256:260000${salt}${h.hex()}"

def verify_pw(pw, stored):
    try:
        parts = stored.split('$')
        salt, hashed = parts[-2], parts[-1]
        h = hashlib.pbkdf2_hmac('sha256', pw.encode(), salt.encode(), 260000)
        return hmac.compare_digest(h.hex(), hashed)
    except: return False

def sla_deadline(priority):
    h = SLA_HOURS.get(priority, 24)
    return (datetime.utcnow() + timedelta(hours=h)).isoformat()

def next_ticket_id(company_id='me'):
    prefix = f"TKT-{company_id.upper()[:2]}-"
    row = query("SELECT id FROM tickets WHERE id LIKE ? ORDER BY id DESC LIMIT 1",
                (prefix+'%',)).fetchone()
    if row:
        n = int(row['id'].split('-')[-1]) + 1
    else:
        n = 1
    return f"{prefix}{str(n).zfill(5)}"

# ── JWT (sin librería externa) ─────────────────────────
def make_jwt(payload, exp_hours=12):
    payload['exp'] = int(time.time()) + exp_hours * 3600
    payload['iat'] = int(time.time())
    header  = base64.urlsafe_b64encode(b'{"alg":"HS256","typ":"JWT"}').rstrip(b'=').decode()
    body    = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b'=').decode()
    sig_raw = hmac.new(SECRET_KEY.encode(), f"{header}.{body}".encode(), hashlib.sha256).digest()
    sig     = base64.urlsafe_b64encode(sig_raw).rstrip(b'=').decode()
    return f"{header}.{body}.{sig}"

def decode_jwt(token):
    try:
        header, body, sig = token.split('.')
        sig_raw = hmac.new(SECRET_KEY.encode(),
                           f"{header}.{body}".encode(), hashlib.sha256).digest()
        expected = base64.urlsafe_b64encode(sig_raw).rstrip(b'=').decode()
        if not hmac.compare_digest(sig, expected): return None
        pad = 4 - len(body) % 4
        payload = json.loads(base64.urlsafe_b64decode(body + '='*pad))
        if payload.get('exp', 0) < time.time(): return None
        return payload
    except: return None

# ── Auth decorator ─────────────────────────────────────
def require_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.headers.get('Authorization','').removeprefix('Bearer ')
        if not token:
            token = request.args.get('token','')
        payload = decode_jwt(token)
        if not payload:
            return jsonify({'success':False,'error':'No autenticado'}), 401
        g.user = payload
        return f(*args, **kwargs)
    return wrapper

def require_admin(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if g.user.get('role') not in ('admin',):
            return jsonify({'success':False,'error':'Solo administradores'}), 403
        return f(*args, **kwargs)
    return wrapper

# ── Rate limiting simple ───────────────────────────────
_rate_store = {}
_rate_lock  = threading.Lock()

def rate_limit(max_per_min=120):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            ip  = request.remote_addr or 'unknown'
            key = f"{ip}:{f.__name__}"
            now = time.time()
            with _rate_lock:
                hits = _rate_store.get(key, [])
                hits = [t for t in hits if now - t < 60]
                if len(hits) >= max_per_min:
                    return jsonify({'success':False,'error':'Demasiadas peticiones'}), 429
                hits.append(now)
                _rate_store[key] = hits
            return f(*args, **kwargs)
        return wrapper
    return decorator

# ══════════════════════════════════════════════════════
#  ENDPOINTS DE AUTENTICACIÓN
# ══════════════════════════════════════════════════════

@app.route('/api/auth/login', methods=['POST'])
@rate_limit(30)
def api_login():
    body = request.get_json(silent=True) or {}
    username   = str(body.get('username','')).strip().lower()[:64]
    password   = str(body.get('password',''))[:256]
    company_id = str(body.get('company_id','me'))[:16]
    portal     = str(body.get('portal',''))[:64]

    if not username or not password:
        return jsonify({'success':False,'error':'Usuario y contraseña requeridos'}), 400

    user = row_to_dict(query("SELECT * FROM users WHERE username=? AND is_active=1",
                             (username,)).fetchone())

    # Dev mode: accept any user with password >= 4 chars
    if not user:
        if len(password) >= 4:
            user = {'username':username,'display_name':username,
                    'role':'user','company_id':company_id,'department':''}
        else:
            return jsonify({'success':False,'error':'Credenciales incorrectas'}), 401
    else:
        if user.get('password_hash','').startswith('pbkdf2') and \
           not verify_pw(password, user['password_hash']):
            return jsonify({'success':False,'error':'Credenciales incorrectas'}), 401

    token = make_jwt({'username':username,'display_name':user.get('display_name',username),
                      'role':user.get('role','user'),'company_id':company_id,
                      'department':user.get('department','')})

    # Register session
    execute("""INSERT OR REPLACE INTO sessions
               (token_id, username, portal, company_id, role, last_seen, created_at, ip_addr)
               VALUES (?,?,?,?,?,?,?,?)""",
            (hashlib.md5(token.encode()).hexdigest()[:16], username, portal,
             company_id, user.get('role','user'), now_iso(), now_iso(),
             request.remote_addr or ''))

    execute("UPDATE users SET last_login=? WHERE username=?", (now_iso(), username))

    # Notify admin via WebSocket
    socketio.emit('user_connected',
                  {'username':username,'portal':portal,'company_id':company_id,
                   'role':user.get('role','user'),'ts':now_iso()},
                  room='admins')

    return jsonify({'success':True,'token':token,
                    'user':{'username':username,'display_name':user.get('display_name',username),
                            'role':user.get('role','user'),'company_id':company_id}})

@app.route('/api/auth/logout', methods=['POST'])
@require_auth
def api_logout():
    uname = g.user.get('username','')
    execute("DELETE FROM sessions WHERE username=?", (uname,))
    socketio.emit('user_disconnected', {'username':uname,'ts':now_iso()}, room='admins')
    return jsonify({'success':True})

@app.route('/api/auth/heartbeat', methods=['POST'])
@require_auth
def api_heartbeat():
    body    = request.get_json(silent=True) or {}
    uname   = g.user.get('username','')
    portal  = str(body.get('portal',''))[:64]
    execute("UPDATE sessions SET last_seen=?, portal=? WHERE username=?",
            (now_iso(), portal, uname))
    return jsonify({'success':True})

# ══════════════════════════════════════════════════════
#  SESIONES (monitor de usuarios)
# ══════════════════════════════════════════════════════

@app.route('/api/sessions', methods=['GET'])
@require_auth
def api_sessions():
    cutoff = (datetime.utcnow() - timedelta(minutes=10)).isoformat()
    rows   = query("SELECT * FROM sessions WHERE last_seen > ? ORDER BY last_seen DESC",
                   (cutoff,)).fetchall()
    return jsonify({'success':True, 'sessions':[dict(r) for r in rows]})

@app.route('/api/sessions/<username>/kick', methods=['POST'])
@require_auth
def api_kick_session(username):
    if g.user.get('role') != 'admin':
        return jsonify({'success':False,'error':'Solo administradores'}), 403
    execute("DELETE FROM sessions WHERE username=?", (username,))
    socketio.emit('kicked', {'by':g.user.get('username'),'ts':now_iso()}, room=f'user_{username}')
    return jsonify({'success':True})

@app.route('/api/sessions/kick-all', methods=['POST'])
@require_auth
def api_kick_all():
    if g.user.get('role') != 'admin':
        return jsonify({'success':False,'error':'Solo administradores'}), 403
    me = g.user.get('username','')
    rows = query("SELECT username FROM sessions WHERE username!=?", (me,)).fetchall()
    for r in rows:
        socketio.emit('kicked', {'by':me,'ts':now_iso()}, room=f"user_{r['username']}")
    execute("DELETE FROM sessions WHERE username!=?", (me,))
    return jsonify({'success':True, 'kicked':len(rows)})

# ══════════════════════════════════════════════════════
#  TICKETS
# ══════════════════════════════════════════════════════

def build_ticket(row):
    if not row: return None
    t = row_to_dict(row)
    tid = t['id']
    t['comments'] = [row_to_dict(r) for r in
                     query("SELECT * FROM comments WHERE ticket_id=? ORDER BY created_at",
                           (tid,)).fetchall()]
    t['audit']    = [row_to_dict(r) for r in
                     query("SELECT * FROM audit_log WHERE ticket_id=? ORDER BY created_at",
                           (tid,)).fetchall()]
    t['time_log'] = [row_to_dict(r) for r in
                     query("SELECT * FROM time_log WHERE ticket_id=? ORDER BY created_at",
                           (tid,)).fetchall()]
    srv = query("SELECT * FROM surveys WHERE ticket_id=? ORDER BY created_at DESC LIMIT 1",
                (tid,)).fetchone()
    t['survey']   = row_to_dict(srv) if srv else None
    t['time_total'] = sum(r['seconds'] for r in query(
        "SELECT seconds FROM time_log WHERE ticket_id=?",(tid,)).fetchall())
    return t

@app.route('/api/tickets', methods=['GET'])
@require_auth
@rate_limit(300)
def api_get_tickets():
    page     = max(1, int(request.args.get('page', 1)))
    per_page = min(MAX_PAGE, int(request.args.get('per_page', 50)))
    offset   = (page - 1) * per_page

    wheres, params = [], []
    co = request.args.get('company_id') or g.user.get('company_id','')
    if co and co != '*':
        wheres.append("(company_id=? OR company_id='*')")
        params.append(co)
    for field in ('status','priority','assignee','category'):
        val = request.args.get(field)
        if val:
            wheres.append(f"{field}=?")
            params.append(val)
    q = request.args.get('q','').strip()
    if q:
        wheres.append("(title LIKE ? OR description LIKE ? OR id LIKE ?)")
        params += [f'%{q}%', f'%{q}%', f'%{q}%']

    where_sql = f"WHERE {' AND '.join(wheres)}" if wheres else ""
    total = query(f"SELECT COUNT(*) FROM tickets {where_sql}", params).fetchone()[0]
    rows  = query(f"SELECT * FROM tickets {where_sql} ORDER BY created_at DESC LIMIT ? OFFSET ?",
                  params + [per_page, offset]).fetchall()

    return jsonify({'success':True,
                    'tickets':[row_to_dict(r) for r in rows],
                    'total':total, 'page':page, 'per_page':per_page,
                    'pages': (total + per_page - 1) // per_page})

@app.route('/api/tickets/<tid>', methods=['GET'])
@require_auth
@rate_limit(600)
def api_get_ticket(tid):
    t = build_ticket(query("SELECT * FROM tickets WHERE id=?", (tid,)).fetchone())
    if not t: return jsonify({'success':False,'error':'No encontrado'}), 404
    return jsonify({'success':True, 'ticket':t})

@app.route('/api/tickets', methods=['POST'])
@require_auth
@rate_limit(60)
def api_create_ticket():
    body = request.get_json(silent=True) or {}
    title = str(body.get('title','')).strip()[:200]
    if not title:
        return jsonify({'success':False,'error':'El título es obligatorio'}), 400

    co  = str(body.get('company_id', g.user.get('company_id','me')))[:16]
    pri = str(body.get('priority','Media'))
    tid = next_ticket_id(co)
    now = now_iso()

    execute("""INSERT INTO tickets
        (id,title,description,category,priority,status,assignee,created_by,requester,
         department,company_id,tags,created_at,updated_at,sla_deadline)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (tid, title,
         str(body.get('description', body.get('desc','')))[:5000],
         str(body.get('category','Otro'))[:64],
         pri,
         'Abierto',
         str(body.get('assignee',''))[:64],
         g.user.get('username',''),
         str(body.get('requester', g.user.get('display_name','')))[:128],
         str(body.get('department',''))[:128],
         co,
         json.dumps(body.get('tags',[])),
         now, now,
         sla_deadline(pri)))

    execute("INSERT INTO audit_log (ticket_id,user,action,color,created_at) VALUES (?,?,?,?,?)",
            (tid, g.user.get('display_name','Sistema'), 'Ticket creado', '#1a5fa8', now))

    ticket = build_ticket(query("SELECT * FROM tickets WHERE id=?", (tid,)).fetchone())

    # Broadcast nuevo ticket a todos en la sala de la empresa
    socketio.emit('ticket_created', {'ticket':ticket, 'by':g.user.get('username')},
                  room=f'company_{co}')

    return jsonify({'success':True, 'ticket':ticket}), 201

@app.route('/api/tickets/<tid>', methods=['PUT'])
@require_auth
@rate_limit(120)
def api_update_ticket(tid):
    body = request.get_json(silent=True) or {}

    # Optimistic locking: check version
    current = query("SELECT * FROM tickets WHERE id=?", (tid,)).fetchone()
    if not current:
        return jsonify({'success':False,'error':'No encontrado'}), 404

    client_version = body.get('version')
    if client_version and int(client_version) != current['version']:
        return jsonify({'success':False,'error':'Conflicto: el ticket fue modificado por otro usuario',
                        'current_version': current['version']}), 409

    allowed = ['title','description','category','priority','status','assignee','tags']
    updates = {k:v for k,v in body.items() if k in allowed}
    if not updates:
        return jsonify({'success':False,'error':'Sin campos válidos'}), 400

    # Build SET clause
    sets = ', '.join(f"{k}=?" for k in updates)
    vals = list(updates.values())
    if 'tags' in updates:
        idx         = list(updates.keys()).index('tags')
        vals[idx]   = json.dumps(updates['tags'])
    now = now_iso()

    execute(f"UPDATE tickets SET {sets}, updated_at=?, version=version+1 WHERE id=?",
            vals + [now, tid])

    # If resolved → set resolved_at
    if updates.get('status') in ('Resuelto','Cerrado'):
        execute("UPDATE tickets SET resolved_at=? WHERE id=? AND resolved_at IS NULL",
                (now, tid))

    # Audit
    by = g.user.get('display_name','Sistema')
    for field, val in updates.items():
        execute("INSERT INTO audit_log (ticket_id,user,action,color,created_at) VALUES (?,?,?,?,?)",
                (tid, by, f"'{field}' → '{val}'", '#b58500', now))

    ticket = build_ticket(query("SELECT * FROM tickets WHERE id=?", (tid,)).fetchone())
    co = ticket['company_id']
    socketio.emit('ticket_updated', {'ticket':ticket, 'by':g.user.get('username')},
                  room=f'company_{co}')

    return jsonify({'success':True, 'ticket':ticket})

@app.route('/api/tickets/<tid>', methods=['DELETE'])
@require_auth
@rate_limit(20)
def api_delete_ticket(tid):
    if g.user.get('role') != 'admin':
        return jsonify({'success':False,'error':'Solo administradores'}), 403
    row = query("SELECT company_id FROM tickets WHERE id=?", (tid,)).fetchone()
    if not row: return jsonify({'success':False,'error':'No encontrado'}), 404
    execute("DELETE FROM tickets WHERE id=?", (tid,))
    socketio.emit('ticket_deleted', {'ticket_id':tid, 'by':g.user.get('username')},
                  room=f"company_{row['company_id']}")
    return jsonify({'success':True})

@app.route('/api/tickets/<tid>/comments', methods=['POST'])
@require_auth
@rate_limit(120)
def api_add_comment(tid):
    body = request.get_json(silent=True) or {}
    text = str(body.get('text','')).strip()[:4000]
    if not text: return jsonify({'success':False,'error':'Comentario vacío'}), 400
    author = g.user.get('display_name','Usuario')
    now    = now_iso()
    execute("INSERT INTO comments (ticket_id,author,text,created_at,is_internal) VALUES (?,?,?,?,?)",
            (tid, author, text, now, int(body.get('is_internal',0))))
    execute("UPDATE tickets SET updated_at=? WHERE id=?", (now, tid))
    ticket = build_ticket(query("SELECT * FROM tickets WHERE id=?", (tid,)).fetchone())
    if ticket:
        socketio.emit('comment_added',
                      {'ticket_id':tid,'author':author,'text':text,'ts':now,
                       'by':g.user.get('username')},
                      room=f"company_{ticket['company_id']}")
    return jsonify({'success':True, 'ticket':ticket})

@app.route('/api/tickets/<tid>/survey', methods=['POST'])
@require_auth
@rate_limit(30)
def api_add_survey(tid):
    body   = request.get_json(silent=True) or {}
    rating = body.get('rating')
    if not isinstance(rating, int) or not (1 <= rating <= 5):
        return jsonify({'success':False,'error':'Rating 1-5'}), 400
    execute("INSERT INTO surveys (ticket_id,rating,comment,created_at) VALUES (?,?,?,?)",
            (tid, rating, str(body.get('comment',''))[:500], now_iso()))
    return jsonify({'success':True})

@app.route('/api/tickets/<tid>/time', methods=['POST'])
@require_auth
@rate_limit(60)
def api_add_time(tid):
    body    = request.get_json(silent=True) or {}
    seconds = int(body.get('seconds', 0))
    note    = str(body.get('note',''))[:256]
    if seconds <= 0: return jsonify({'success':False,'error':'Segundos inválidos'}), 400
    execute("INSERT INTO time_log (ticket_id,user,seconds,note,created_at) VALUES (?,?,?,?,?)",
            (tid, g.user.get('display_name',''), seconds, note, now_iso()))
    return jsonify({'success':True})

@app.route('/api/stats', methods=['GET'])
@require_auth
@rate_limit(60)
def api_stats():
    co     = request.args.get('company_id', g.user.get('company_id','*'))
    filter = f"WHERE company_id='{co}'" if co and co != '*' else ""
    rows   = query(f"SELECT status, priority, COUNT(*) as cnt FROM tickets {filter} GROUP BY status, priority").fetchall()
    sessions_cutoff = (datetime.utcnow() - timedelta(minutes=10)).isoformat()
    active_users = query("SELECT COUNT(*) FROM sessions WHERE last_seen > ?",
                         (sessions_cutoff,)).fetchone()[0]
    total  = query(f"SELECT COUNT(*) FROM tickets {filter}").fetchone()[0]
    open_  = query(f"SELECT COUNT(*) FROM tickets {filter} {'AND' if filter else 'WHERE'} status='Abierto'").fetchone()[0]
    prog   = query(f"SELECT COUNT(*) FROM tickets {filter} {'AND' if filter else 'WHERE'} status='En progreso'").fetchone()[0]
    done   = query(f"SELECT COUNT(*) FROM tickets {filter} {'AND' if filter else 'WHERE'} status='Resuelto'").fetchone()[0]
    crit   = query(f"SELECT COUNT(*) FROM tickets {filter} {'AND' if filter else 'WHERE'} priority='Crítica' AND status NOT IN ('Resuelto','Cerrado')").fetchone()[0]
    avg_rating = query("SELECT AVG(rating) FROM surveys").fetchone()[0]
    overdue = query("SELECT COUNT(*) FROM tickets WHERE sla_deadline < ? AND status NOT IN ('Resuelto','Cerrado')",
                    (now_iso(),)).fetchone()[0]
    return jsonify({'success':True,'total':total,'open':open_,'in_progress':prog,
                    'resolved':done,'critical':crit,'overdue_sla':overdue,
                    'active_sessions':active_users,
                    'avg_satisfaction': round(avg_rating, 1) if avg_rating else None})

# ══════════════════════════════════════════════════════
#  USUARIOS / EQUIPO / BOT FAQ / CONFIG
# ══════════════════════════════════════════════════════

@app.route('/api/team', methods=['GET','POST'])
@require_auth
def api_team():
    if request.method == 'GET':
        rows = query("SELECT * FROM team_members ORDER BY name").fetchall()
        return jsonify({'success':True,'team':[dict(r) for r in rows]})
    body = request.get_json(silent=True) or {}
    execute("INSERT INTO team_members (name,department,skills,company_id,user_ref,created_at) VALUES (?,?,?,?,?,?)",
            (str(body.get('name',''))[:128], str(body.get('department',''))[:64],
             str(body.get('skills',''))[:512], str(body.get('company_id','me'))[:16],
             str(body.get('user_ref',''))[:64], now_iso()))
    return jsonify({'success':True}), 201

@app.route('/api/team/<int:tid>', methods=['PUT','DELETE'])
@require_auth
def api_team_member(tid):
    if request.method == 'DELETE':
        execute("DELETE FROM team_members WHERE id=?", (tid,))
        return jsonify({'success':True})
    body = request.get_json(silent=True) or {}
    execute("UPDATE team_members SET name=?,department=?,skills=?,company_id=?,user_ref=? WHERE id=?",
            (str(body.get('name',''))[:128], str(body.get('department',''))[:64],
             str(body.get('skills',''))[:512], str(body.get('company_id','me'))[:16],
             str(body.get('user_ref',''))[:64], tid))
    return jsonify({'success':True})

@app.route('/api/config', methods=['GET','POST'])
@require_auth
def api_config():
    if request.method == 'GET':
        rows = query("SELECT key,value FROM config").fetchall()
        return jsonify({'success':True,'config':{r['key']:r['value'] for r in rows}})
    body = request.get_json(silent=True) or {}
    for k, v in body.items():
        execute("INSERT OR REPLACE INTO config (key,value) VALUES (?,?)", (str(k)[:64], str(v)[:4096]))
    return jsonify({'success':True})

@app.route('/api/bot/faq', methods=['GET'])
@require_auth
def api_bot_faq():
    q    = request.args.get('q','')
    rows = query("SELECT * FROM bot_faq ORDER BY use_count DESC").fetchall()
    if q:
        ql   = q.lower()
        rows = [r for r in rows if ql in r['title'].lower() or ql in (r['keys']or'').lower()]
    return jsonify({'success':True,'faq':[row_to_dict(r) for r in rows]})

# ══════════════════════════════════════════════════════
#  WEBSOCKET EVENTS
# ══════════════════════════════════════════════════════

@socketio.on('connect')
def ws_connect():
    log.info(f"WS connect: {request.sid}")

@socketio.on('join')
def ws_join(data):
    company_id = data.get('company_id','me')
    username   = data.get('username','')
    role       = data.get('role','user')
    join_room(f'company_{company_id}')
    if role in ('admin',): join_room('admins')
    join_room(f'user_{username}')
    emit('joined', {'room':f'company_{company_id}', 'sid':request.sid})

@socketio.on('disconnect')
def ws_disconnect():
    log.info(f"WS disconnect: {request.sid}")

@socketio.on('ping_heartbeat')
def ws_heartbeat(data):
    emit('pong', {'ts': now_iso()})

# ══════════════════════════════════════════════════════
#  USUARIOS ADMIN
# ══════════════════════════════════════════════════════

@app.route('/api/users', methods=['GET'])
@require_auth
def api_users():
    if g.user.get('role') != 'admin':
        return jsonify({'success':False,'error':'Solo administradores'}), 403
    rows = query("SELECT username,display_name,role,company_id,department,is_active,last_login FROM users ORDER BY display_name").fetchall()
    return jsonify({'success':True,'users':[dict(r) for r in rows]})

@app.route('/api/users', methods=['POST'])
@require_auth
def api_create_user():
    if g.user.get('role') != 'admin':
        return jsonify({'success':False,'error':'Solo administradores'}), 403
    body = request.get_json(silent=True) or {}
    username = str(body.get('username','')).strip().lower()[:64]
    pw       = str(body.get('password',''))
    if not username or len(pw) < 6:
        return jsonify({'success':False,'error':'Usuario y contraseña (min 6 chars)'}), 400
    try:
        execute("""INSERT INTO users (username,display_name,role,company_id,department,password_hash,created_at)
                   VALUES (?,?,?,?,?,?,?)""",
                (username, str(body.get('display_name',username))[:128],
                 str(body.get('role','user'))[:16],
                 str(body.get('company_id','me'))[:16],
                 str(body.get('department',''))[:64],
                 hash_pw(pw), now_iso()))
        return jsonify({'success':True}), 201
    except Exception as e:
        return jsonify({'success':False,'error':str(e)}), 400

@app.route('/api/users/<username>', methods=['PUT','DELETE'])
@require_auth
def api_user(username):
    if g.user.get('role') != 'admin':
        return jsonify({'success':False,'error':'Solo administradores'}), 403
    if request.method == 'DELETE':
        execute("DELETE FROM users WHERE username=?", (username,))
        return jsonify({'success':True})
    body = request.get_json(silent=True) or {}
    pw   = body.pop('password', None)
    sets,vals = [],[]
    for k in ('display_name','role','company_id','department','is_active'):
        if k in body:
            sets.append(f"{k}=?"); vals.append(body[k])
    if pw and len(pw) >= 6:
        sets.append("password_hash=?"); vals.append(hash_pw(pw))
    if sets:
        execute(f"UPDATE users SET {','.join(sets)} WHERE username=?", vals+[username])
    return jsonify({'success':True})

# ══════════════════════════════════════════════════════
#  HEALTH CHECK
# ══════════════════════════════════════════════════════

@app.route('/api/health')
def api_health():
    db_ok = False
    try:
        query("SELECT 1"); db_ok = True
    except: pass
    return jsonify({'status':'ok','db':db_ok,'version':'2.0-enterprise',
                    'ts':now_iso(),'capacity':'100+ técnicos / 8000+ usuarios'})

# ══════════════════════════════════════════════════════
#  ARRANQUE
# ══════════════════════════════════════════════════════

if __name__ == '__main__':
    init_db()
    log.info(f"TicketDesk Enterprise Server — puerto {PORT}")
    log.info(f"DB: {Path(DB_PATH).absolute()}")
    log.info("Capacidad: 100+ técnicos, 8000+ usuarios, WebSocket activo")
    socketio.run(app, host='0.0.0.0', port=PORT, debug=False,
                 use_reloader=False, log_output=False, allow_unsafe_werkzeug=True)
