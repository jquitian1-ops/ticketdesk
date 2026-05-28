"""
TicketDesk — Base de datos SQLite
===================================
Módulo de acceso a datos para TicketDesk v2.0
Motor: SQLite (archivo local ticketdesk.db)

Tablas:
  tickets         — Tickets de soporte
  comments        — Comentarios por ticket
  audit_log       — Historial de cambios
  time_log        — Registro de tiempo trabajado
  users           — Usuarios del sistema
  team_members    — Equipo de especialistas TI
  config          — Configuración del sistema (clave-valor)
  surveys         — Encuestas de satisfacción
  bot_faq         — Preguntas frecuentes del bot (custom + learned)
  metrics_cache   — Caché de métricas para dashboard
  servers         — Servidores monitoreados
  notifications   — Log de notificaciones enviadas

Uso:
  from database import db
  db.init()
  ticket = db.tickets.create({...})
  tickets = db.tickets.get_all()
"""

import sqlite3
import json
import os
import hashlib
import hmac
import time
from datetime import datetime, timedelta
from contextlib import contextmanager
from pathlib import Path

DB_PATH = os.environ.get("TICKETDESK_DB", "ticketdesk.db")

# ── Conexión ─────────────────────────────────────────
@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def row_to_dict(row):
    if row is None:
        return None
    d = dict(row)
    # Parse JSON fields
    for key in ('tags', 'metadata', 'keys', 'steps', 'suggest', 'settings'):
        if key in d and d[key]:
            try:
                d[key] = json.loads(d[key])
            except Exception:
                pass
    return d

def rows_to_list(rows):
    return [row_to_dict(r) for r in rows]

# ── Inicializar esquema ───────────────────────────────
SCHEMA = """
-- ── TICKETS ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS tickets (
    id          TEXT PRIMARY KEY,
    title       TEXT NOT NULL,
    description TEXT,
    category    TEXT DEFAULT 'Otro',
    priority    TEXT DEFAULT 'Media' CHECK(priority IN ('Baja','Media','Alta','Crítica')),
    status      TEXT DEFAULT 'Abierto' CHECK(status IN ('Abierto','En progreso','Resuelto','Cerrado')),
    assignee    TEXT DEFAULT '',
    created_by  TEXT DEFAULT '',
    requester   TEXT DEFAULT '',
    department  TEXT DEFAULT '',
    tags        TEXT DEFAULT '[]',
    escalation_level INTEGER DEFAULT 0,
    bot_session INTEGER DEFAULT 0,
    created_at  TEXT DEFAULT (datetime('now')),
    updated_at  TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_tickets_status   ON tickets(status);
CREATE INDEX IF NOT EXISTS idx_tickets_priority ON tickets(priority);
CREATE INDEX IF NOT EXISTS idx_tickets_assignee ON tickets(assignee);
CREATE INDEX IF NOT EXISTS idx_tickets_created  ON tickets(created_at);

-- ── COMENTARIOS ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS comments (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id   TEXT NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    author      TEXT NOT NULL,
    text        TEXT NOT NULL,
    created_at  TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_comments_ticket ON comments(ticket_id);

-- ── AUDIT LOG ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS audit_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id   TEXT NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    user_name   TEXT NOT NULL,
    action      TEXT NOT NULL,
    color       TEXT DEFAULT '#888888',
    created_at  TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_audit_ticket ON audit_log(ticket_id);

-- ── TIME LOG ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS time_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id   TEXT NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    user_name   TEXT NOT NULL,
    seconds     INTEGER NOT NULL DEFAULT 0,
    note        TEXT DEFAULT '',
    started_at  TEXT,
    saved_at    TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_timelog_ticket ON time_log(ticket_id);

-- ── USUARIOS ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    username    TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    password_hash TEXT,
    role        TEXT DEFAULT 'user' CHECK(role IN ('admin','agent','user')),
    department  TEXT DEFAULT '',
    email       TEXT DEFAULT '',
    active      INTEGER DEFAULT 1,
    last_login  TEXT,
    created_at  TEXT DEFAULT (datetime('now'))
);

-- ── EQUIPO TI ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS team_members (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    department  TEXT DEFAULT '',
    ai_profile  TEXT DEFAULT '',
    active      INTEGER DEFAULT 1,
    created_at  TEXT DEFAULT (datetime('now'))
);

-- ── CONFIGURACIÓN ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS config (
    key         TEXT PRIMARY KEY,
    value       TEXT,
    updated_at  TEXT DEFAULT (datetime('now'))
);

-- ── ENCUESTAS ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS surveys (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id   TEXT NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    rating      INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
    comment     TEXT DEFAULT '',
    created_at  TEXT DEFAULT (datetime('now'))
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_surveys_ticket ON surveys(ticket_id);

-- ── BOT FAQ ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS bot_faq (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL,
    keys        TEXT DEFAULT '[]',
    answer      TEXT NOT NULL,
    steps       TEXT DEFAULT '[]',
    suggest     TEXT DEFAULT '[]',
    source      TEXT DEFAULT 'custom' CHECK(source IN ('custom','learned','builtin')),
    use_count   INTEGER DEFAULT 0,
    original_question TEXT DEFAULT '',
    learned_at  TEXT DEFAULT (datetime('now')),
    last_used   TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_botfaq_source ON bot_faq(source);

-- ── SERVIDORES MONITOREADOS ───────────────────────────
CREATE TABLE IF NOT EXISTS servers (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    host        TEXT NOT NULL UNIQUE,
    server_type TEXT DEFAULT 'Servidor',
    status      TEXT DEFAULT 'online' CHECK(status IN ('online','offline','unknown')),
    last_check  TEXT,
    last_down   TEXT,
    created_at  TEXT DEFAULT (datetime('now'))
);

-- ── NOTIFICACIONES LOG ────────────────────────────────
CREATE TABLE IF NOT EXISTS notifications (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    type        TEXT NOT NULL,
    title       TEXT NOT NULL,
    body        TEXT DEFAULT '',
    ticket_id   TEXT,
    sent_to     TEXT DEFAULT '',
    channel     TEXT DEFAULT 'push',
    created_at  TEXT DEFAULT (datetime('now'))
);

-- ── MÉTRICAS CACHE ────────────────────────────────────
CREATE TABLE IF NOT EXISTS metrics_cache (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_key  TEXT NOT NULL,
    value       REAL NOT NULL,
    period      TEXT DEFAULT 'daily',
    date        TEXT DEFAULT (date('now')),
    updated_at  TEXT DEFAULT (datetime('now'))
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_metrics_key_date ON metrics_cache(metric_key, date);
"""

def init_db():
    """Crea todas las tablas y datos iniciales."""
    with get_conn() as conn:
        conn.executescript(SCHEMA)

        # Usuario admin por defecto
        conn.execute("""
            INSERT OR IGNORE INTO users (username, display_name, password_hash, role, department)
            VALUES (?, ?, ?, ?, ?)
        """, ('admin', 'Administrador', _hash_password('FfSEN/Y7W06#7Wod'), 'admin', 'TI'))

        # Config inicial
        defaults = {
            'company_name': 'Manufacturas Eliot',
            'sla_critica': '4',
            'sla_alta': '8',
            'sla_media': '24',
            'sla_baja': '72',
            'escalation_enabled': 'true',
            'escalation_interval': '300000',
            'bot_enabled': 'true',
            'version': '2.0',
        }
        for k, v in defaults.items():
            conn.execute("INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)", (k, v))

    print(f"Base de datos inicializada: {DB_PATH}")

def _hash_password(password: str) -> str:
    salt = os.urandom(16).hex()
    h    = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 260000)
    return f"{salt}:{h.hex()}"

def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt, h = stored_hash.split(':')
        check = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 260000)
        return hmac.compare_digest(check.hex(), h)
    except Exception:
        return False

# ══════════════════════════════════════════════════════
# REPOSITORIOS
# ══════════════════════════════════════════════════════

class TicketRepo:
    def create(self, data: dict) -> dict:
        tid = data.get('id') or self._next_id()
        now = datetime.utcnow().isoformat()
        with get_conn() as conn:
            conn.execute("""
                INSERT INTO tickets
                  (id,title,description,category,priority,status,assignee,
                   created_by,requester,department,tags,created_at,updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                tid, data.get('title',''), data.get('description',''),
                data.get('category','Otro'), data.get('priority','Media'),
                data.get('status','Abierto'), data.get('assignee',''),
                data.get('created_by',''), data.get('requester',''),
                data.get('department',''),
                json.dumps(data.get('tags', [])),
                data.get('created_at', now), now
            ))
            if data.get('audit'):
                for a in data['audit']:
                    conn.execute(
                        "INSERT INTO audit_log (ticket_id,user_name,action,color,created_at) VALUES (?,?,?,?,?)",
                        (tid, a.get('user',''), a.get('action',''), a.get('color','#888'), a.get('ts', now))
                    )
        return self.get(tid)

    def get(self, tid: str) -> dict:
        with get_conn() as conn:
            row = conn.execute("SELECT * FROM tickets WHERE id=?", (tid,)).fetchone()
            if not row:
                return None
            t = row_to_dict(row)
            t['comments'] = rows_to_list(conn.execute(
                "SELECT * FROM comments WHERE ticket_id=? ORDER BY created_at", (tid,)).fetchall())
            t['audit']    = rows_to_list(conn.execute(
                "SELECT * FROM audit_log WHERE ticket_id=? ORDER BY created_at", (tid,)).fetchall())
            t['timeLog']  = rows_to_list(conn.execute(
                "SELECT * FROM time_log WHERE ticket_id=? ORDER BY saved_at", (tid,)).fetchall())
            survey = conn.execute("SELECT * FROM surveys WHERE ticket_id=?", (tid,)).fetchone()
            t['survey'] = row_to_dict(survey) if survey else None
            return t

    def get_all(self, filters: dict = None) -> list:
        filters = filters or {}
        q    = "SELECT * FROM tickets WHERE 1=1"
        args = []
        if filters.get('status'):
            q += " AND status=?"; args.append(filters['status'])
        if filters.get('priority'):
            q += " AND priority=?"; args.append(filters['priority'])
        if filters.get('assignee'):
            q += " AND assignee=?"; args.append(filters['assignee'])
        if filters.get('created_by'):
            q += " AND created_by=?"; args.append(filters['created_by'])
        if filters.get('search'):
            q += " AND (title LIKE ? OR description LIKE ?)"; s = f"%{filters['search']}%"; args += [s, s]
        q += " ORDER BY created_at DESC"
        with get_conn() as conn:
            rows = conn.execute(q, args).fetchall()
        return rows_to_list(rows)

    def update(self, tid: str, data: dict) -> dict:
        now = datetime.utcnow().isoformat()
        fields = {k: v for k, v in data.items()
                  if k in ('title','description','category','priority','status','assignee','tags','escalation_level')}
        if not fields:
            return self.get(tid)
        if 'tags' in fields and isinstance(fields['tags'], list):
            fields['tags'] = json.dumps(fields['tags'])
        set_clause = ', '.join(f"{k}=?" for k in fields)
        vals = list(fields.values()) + [now, tid]
        with get_conn() as conn:
            conn.execute(f"UPDATE tickets SET {set_clause}, updated_at=? WHERE id=?", vals)
        return self.get(tid)

    def delete(self, tid: str) -> bool:
        with get_conn() as conn:
            conn.execute("DELETE FROM tickets WHERE id=?", (tid,))
        return True

    def add_comment(self, tid: str, author: str, text: str) -> dict:
        now = datetime.utcnow().isoformat()
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO comments (ticket_id,author,text,created_at) VALUES (?,?,?,?)",
                (tid, author, text, now)
            )
            conn.execute("UPDATE tickets SET updated_at=? WHERE id=?", (now, tid))
        return self.get(tid)

    def add_audit(self, tid: str, user: str, action: str, color: str = '#888') -> None:
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO audit_log (ticket_id,user_name,action,color) VALUES (?,?,?,?)",
                (tid, user, action, color)
            )

    def add_time_log(self, tid: str, user: str, seconds: int, note: str = '', started: str = None) -> None:
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO time_log (ticket_id,user_name,seconds,note,started_at) VALUES (?,?,?,?,?)",
                (tid, user, seconds, note, started or datetime.utcnow().isoformat())
            )

    def add_survey(self, tid: str, rating: int, comment: str = '') -> None:
        with get_conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO surveys (ticket_id,rating,comment) VALUES (?,?,?)",
                (tid, rating, comment)
            )

    def search(self, query: str) -> list:
        q = f"%{query}%"
        with get_conn() as conn:
            rows = conn.execute("""
                SELECT DISTINCT t.* FROM tickets t
                LEFT JOIN comments c ON c.ticket_id = t.id
                WHERE t.title LIKE ? OR t.description LIKE ?
                   OR t.assignee LIKE ? OR t.tags LIKE ?
                   OR c.text LIKE ?
                ORDER BY t.created_at DESC LIMIT 50
            """, (q, q, q, q, q)).fetchall()
        return rows_to_list(rows)

    def get_sla_overdue(self) -> list:
        """Devuelve tickets con SLA vencido."""
        sla_map = {'Crítica': 4, 'Alta': 8, 'Media': 24, 'Baja': 72}
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM tickets WHERE status NOT IN ('Resuelto','Cerrado')"
            ).fetchall()
        result = []
        now = datetime.utcnow()
        for row in rows:
            t = row_to_dict(row)
            limit_h = sla_map.get(t['priority'], 24)
            try:
                created = datetime.fromisoformat(t['created_at'])
                elapsed = (now - created).total_seconds() / 3600
                if elapsed > limit_h:
                    t['sla_over_hours'] = round(elapsed - limit_h, 1)
                    result.append(t)
            except Exception:
                pass
        result.sort(key=lambda x: x.get('sla_over_hours', 0), reverse=True)
        return result

    def get_stats(self) -> dict:
        with get_conn() as conn:
            total    = conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
            open_    = conn.execute("SELECT COUNT(*) FROM tickets WHERE status='Abierto'").fetchone()[0]
            progress = conn.execute("SELECT COUNT(*) FROM tickets WHERE status='En progreso'").fetchone()[0]
            resolved = conn.execute("SELECT COUNT(*) FROM tickets WHERE status='Resuelto'").fetchone()[0]
            closed   = conn.execute("SELECT COUNT(*) FROM tickets WHERE status='Cerrado'").fetchone()[0]
            critical = conn.execute("SELECT COUNT(*) FROM tickets WHERE priority='Crítica' AND status NOT IN ('Resuelto','Cerrado')").fetchone()[0]
            avg_sat  = conn.execute("SELECT AVG(rating) FROM surveys").fetchone()[0]
            total_time = conn.execute("SELECT SUM(seconds) FROM time_log").fetchone()[0] or 0
        return {
            'total': total, 'open': open_, 'in_progress': progress,
            'resolved': resolved, 'closed': closed, 'critical': critical,
            'satisfaction_avg': round(avg_sat, 2) if avg_sat else None,
            'total_time_hours': round(total_time / 3600, 1),
        }

    def _next_id(self) -> str:
        with get_conn() as conn:
            row = conn.execute("SELECT id FROM tickets ORDER BY id DESC LIMIT 1").fetchone()
        if row:
            try:
                n = int(row[0].replace('TKT-', '')) + 1
            except Exception:
                n = 1
        else:
            n = 1
        return f"TKT-{str(n).zfill(4)}"


class UserRepo:
    def create(self, data: dict) -> dict:
        with get_conn() as conn:
            conn.execute("""
                INSERT INTO users (username,display_name,password_hash,role,department,email)
                VALUES (?,?,?,?,?,?)
            """, (
                data['username'], data.get('display_name', data['username']),
                _hash_password(data.get('password', '')) if data.get('password') else None,
                data.get('role', 'user'), data.get('department', ''), data.get('email', '')
            ))
        return self.get(data['username'])

    def get(self, username: str) -> dict:
        with get_conn() as conn:
            row = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        return row_to_dict(row)

    def get_all(self) -> list:
        with get_conn() as conn:
            rows = conn.execute("SELECT * FROM users WHERE active=1 ORDER BY username").fetchall()
        return rows_to_list(rows)

    def authenticate(self, username: str, password: str) -> dict:
        user = self.get(username)
        if not user or not user.get('active'):
            return None
        if not user.get('password_hash'):
            return None
        if not verify_password(password, user['password_hash']):
            return None
        with get_conn() as conn:
            conn.execute("UPDATE users SET last_login=? WHERE username=?",
                         (datetime.utcnow().isoformat(), username))
        return user

    def change_password(self, username: str, new_password: str) -> bool:
        with get_conn() as conn:
            conn.execute("UPDATE users SET password_hash=? WHERE username=?",
                         (_hash_password(new_password), username))
        return True

    def delete(self, username: str) -> bool:
        with get_conn() as conn:
            conn.execute("UPDATE users SET active=0 WHERE username=?", (username,))
        return True


class ConfigRepo:
    def get(self, key: str, default=None):
        with get_conn() as conn:
            row = conn.execute("SELECT value FROM config WHERE key=?", (key,)).fetchone()
        if row is None:
            return default
        try:
            return json.loads(row[0])
        except Exception:
            return row[0]

    def set(self, key: str, value) -> None:
        v = json.dumps(value) if not isinstance(value, str) else value
        with get_conn() as conn:
            conn.execute("""
                INSERT INTO config (key, value, updated_at) VALUES (?,?,datetime('now'))
                ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
            """, (key, v))

    def get_all(self) -> dict:
        with get_conn() as conn:
            rows = conn.execute("SELECT key, value FROM config").fetchall()
        result = {}
        for row in rows:
            try:
                result[row[0]] = json.loads(row[1])
            except Exception:
                result[row[0]] = row[1]
        return result

    def set_many(self, data: dict) -> None:
        with get_conn() as conn:
            for k, v in data.items():
                val = json.dumps(v) if not isinstance(v, str) else v
                conn.execute("""
                    INSERT INTO config (key, value, updated_at) VALUES (?,?,datetime('now'))
                    ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
                """, (k, val))


class BotFAQRepo:
    def get_all(self, source: str = None) -> list:
        with get_conn() as conn:
            if source:
                rows = conn.execute(
                    "SELECT * FROM bot_faq WHERE source=? ORDER BY use_count DESC, learned_at DESC",
                    (source,)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM bot_faq ORDER BY use_count DESC, learned_at DESC"
                ).fetchall()
        return rows_to_list(rows)

    def create(self, data: dict) -> dict:
        with get_conn() as conn:
            conn.execute("""
                INSERT INTO bot_faq (title,keys,answer,steps,suggest,source,use_count,original_question)
                VALUES (?,?,?,?,?,?,?,?)
            """, (
                data['title'],
                json.dumps(data.get('keys', [])),
                data['answer'],
                json.dumps(data.get('steps', [])),
                json.dumps(data.get('suggest', ['si, se resolvio','Crear ticket'])),
                data.get('source', 'custom'),
                data.get('use_count', 0),
                data.get('originalQuestion', ''),
            ))
            fid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        return self.get(fid)

    def get(self, fid: int) -> dict:
        with get_conn() as conn:
            row = conn.execute("SELECT * FROM bot_faq WHERE id=?", (fid,)).fetchone()
        return row_to_dict(row)

    def update(self, fid: int, data: dict) -> dict:
        fields = {}
        if 'title'  in data: fields['title']  = data['title']
        if 'answer' in data: fields['answer'] = data['answer']
        if 'keys'   in data: fields['keys']   = json.dumps(data['keys'])
        if 'steps'  in data: fields['steps']  = json.dumps(data['steps'])
        if 'use_count' in data: fields['use_count'] = data['use_count']
        if 'last_used' in data: fields['last_used'] = data['last_used']
        if not fields:
            return self.get(fid)
        set_clause = ', '.join(f"{k}=?" for k in fields)
        with get_conn() as conn:
            conn.execute(f"UPDATE bot_faq SET {set_clause} WHERE id=?", list(fields.values()) + [fid])
        return self.get(fid)

    def delete(self, fid: int) -> bool:
        with get_conn() as conn:
            conn.execute("DELETE FROM bot_faq WHERE id=?", (fid,))
        return True

    def increment_use(self, fid: int) -> None:
        with get_conn() as conn:
            conn.execute(
                "UPDATE bot_faq SET use_count=use_count+1, last_used=datetime('now') WHERE id=?",
                (fid,)
            )

    def search(self, query: str) -> list:
        q = f"%{query.lower()}%"
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM bot_faq WHERE lower(keys) LIKE ? OR lower(title) LIKE ? ORDER BY use_count DESC",
                (q, q)
            ).fetchall()
        return rows_to_list(rows)


class TeamRepo:
    def get_all(self) -> list:
        with get_conn() as conn:
            rows = conn.execute("SELECT * FROM team_members WHERE active=1 ORDER BY name").fetchall()
        return rows_to_list(rows)

    def create(self, name: str, department: str = '', ai_profile: str = '') -> dict:
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO team_members (name,department,ai_profile) VALUES (?,?,?)",
                (name, department, ai_profile)
            )
            mid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        return self.get(mid)

    def get(self, mid: int) -> dict:
        with get_conn() as conn:
            row = conn.execute("SELECT * FROM team_members WHERE id=?", (mid,)).fetchone()
        return row_to_dict(row)

    def update(self, mid: int, data: dict) -> dict:
        with get_conn() as conn:
            conn.execute(
                "UPDATE team_members SET name=?, department=?, ai_profile=? WHERE id=?",
                (data.get('name'), data.get('department',''), data.get('ai_profile',''), mid)
            )
        return self.get(mid)

    def delete(self, mid: int) -> bool:
        with get_conn() as conn:
            conn.execute("UPDATE team_members SET active=0 WHERE id=?", (mid,))
        return True


class ServerRepo:
    def get_all(self) -> list:
        with get_conn() as conn:
            rows = conn.execute("SELECT * FROM servers ORDER BY name").fetchall()
        return rows_to_list(rows)

    def create(self, name: str, host: str, server_type: str = 'Servidor') -> dict:
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO servers (name,host,server_type) VALUES (?,?,?)",
                (name, host, server_type)
            )
            sid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        return self.get(sid)

    def get(self, sid: int) -> dict:
        with get_conn() as conn:
            row = conn.execute("SELECT * FROM servers WHERE id=?", (sid,)).fetchone()
        return row_to_dict(row)

    def update_status(self, host: str, status: str) -> None:
        now = datetime.utcnow().isoformat()
        with get_conn() as conn:
            if status == 'offline':
                conn.execute(
                    "UPDATE servers SET status=?, last_check=?, last_down=? WHERE host=?",
                    (status, now, now, host)
                )
            else:
                conn.execute(
                    "UPDATE servers SET status=?, last_check=? WHERE host=?",
                    (status, now, host)
                )


class MetricsRepo:
    def upsert(self, key: str, value: float, period: str = 'daily') -> None:
        with get_conn() as conn:
            conn.execute("""
                INSERT INTO metrics_cache (metric_key, value, period, date, updated_at)
                VALUES (?, ?, ?, date('now'), datetime('now'))
                ON CONFLICT(metric_key, date)
                DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
            """, (key, value, period))

    def get(self, key: str, days: int = 30) -> list:
        since = (datetime.utcnow() - timedelta(days=days)).date().isoformat()
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT date, value FROM metrics_cache WHERE metric_key=? AND date>=? ORDER BY date",
                (key, since)
            ).fetchall()
        return [{'date': r[0], 'value': r[1]} for r in rows]


# ── Façade principal ──────────────────────────────────
class Database:
    def __init__(self):
        self.tickets = TicketRepo()
        self.users   = UserRepo()
        self.config  = ConfigRepo()
        self.bot_faq = BotFAQRepo()
        self.team    = TeamRepo()
        self.servers = ServerRepo()
        self.metrics = MetricsRepo()

    def init(self):
        init_db()
        return self

    def migrate_from_json(self, json_path: str) -> dict:
        """
        Migra datos desde el archivo tickets_data.json del sistema anterior.
        Devuelve un resumen de lo importado.
        """
        if not os.path.exists(json_path):
            return {'error': f'Archivo no encontrado: {json_path}'}

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        tickets_imported = 0
        errors = []

        # Soporte para estructura {"tickets": [...]} o directamente [...]
        raw_tickets = data if isinstance(data, list) else data.get('tickets', [])

        for t in raw_tickets:
            try:
                # Normalizar campos
                ticket_data = {
                    'id':          t.get('id') or t.get('_id'),
                    'title':       t.get('title', ''),
                    'description': t.get('desc') or t.get('description', ''),
                    'category':    t.get('category', 'Otro'),
                    'priority':    t.get('priority', 'Media'),
                    'status':      t.get('status', 'Abierto'),
                    'assignee':    t.get('assignee', ''),
                    'created_by':  t.get('createdBy') or t.get('created_by', ''),
                    'requester':   t.get('requester', ''),
                    'department':  t.get('dept') or t.get('department', ''),
                    'tags':        t.get('tags', []) if isinstance(t.get('tags'), list) else (t.get('tags','').split(',') if t.get('tags') else []),
                    'created_at':  t.get('created') or t.get('created_at'),
                    'audit':       t.get('audit', []),
                }
                existing = self.tickets.get(ticket_data['id']) if ticket_data['id'] else None
                if existing:
                    continue  # Skip duplicados

                self.tickets.create(ticket_data)

                # Comentarios
                for c in t.get('comments', []):
                    self.tickets.add_comment(
                        ticket_data['id'],
                        c.get('author', ''),
                        c.get('text', '')
                    )

                # Time log
                for tl in t.get('timeLog', []):
                    self.tickets.add_time_log(
                        ticket_data['id'],
                        tl.get('by', ''),
                        tl.get('secs', 0),
                        tl.get('note', ''),
                        tl.get('started'),
                    )

                # Encuesta
                if t.get('survey') and t['survey'].get('rating'):
                    self.tickets.add_survey(
                        ticket_data['id'],
                        t['survey']['rating'],
                        t['survey'].get('comment', '')
                    )

                tickets_imported += 1
            except Exception as e:
                errors.append(f"{t.get('id','?')}: {e}")

        # Migrar bot_custom_faq si viene en el JSON
        for faq in data.get('bot_custom_faq', []):
            try:
                self.bot_faq.create({**faq, 'source': 'custom'})
            except Exception:
                pass

        # Migrar equipo
        for m in data.get('team', []):
            try:
                self.team.create(m.get('name',''), m.get('dept',''), m.get('profile',''))
            except Exception:
                pass

        return {
            'tickets_imported': tickets_imported,
            'errors': errors,
            'total_in_file': len(raw_tickets),
        }

    def export_to_json(self, output_path: str) -> str:
        """Exporta toda la BD a un JSON compatible con el sistema anterior."""
        tickets = self.tickets.get_all()
        full_tickets = []
        for t in tickets:
            full = self.tickets.get(t['id'])
            full_tickets.append(full)

        export_data = {
            'tickets':       full_tickets,
            'team':          self.team.get_all(),
            'bot_custom_faq': self.bot_faq.get_all(source='custom'),
            'config':        self.config.get_all(),
            'exported_at':   datetime.utcnow().isoformat(),
            'version':       '2.0',
        }
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        return output_path


db = Database()


# ── CLI de utilidades ─────────────────────────────────
if __name__ == '__main__':
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'init'

    if cmd == 'init':
        db.init()
        print("Base de datos creada correctamente.")

    elif cmd == 'migrate':
        db.init()
        path = sys.argv[2] if len(sys.argv) > 2 else 'tickets_data.json'
        result = db.migrate_from_json(path)
        print(f"Migración completada:")
        print(f"  Importados: {result['tickets_imported']} / {result['total_in_file']}")
        if result['errors']:
            print(f"  Errores:    {len(result['errors'])}")
            for e in result['errors'][:5]:
                print(f"    - {e}")

    elif cmd == 'stats':
        db.init()
        stats = db.tickets.get_stats()
        print("Estadísticas actuales:")
        for k, v in stats.items():
            print(f"  {k}: {v}")

    elif cmd == 'export':
        db.init()
        out = sys.argv[2] if len(sys.argv) > 2 else 'ticketdesk_export.json'
        db.export_to_json(out)
        print(f"Exportado a: {out}")

    elif cmd == 'reset':
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
            print(f"Base de datos eliminada: {DB_PATH}")
        db.init()
        print("Base de datos recreada.")

    else:
        print("Comandos: init | migrate [archivo.json] | stats | export [salida.json] | reset")
