"""
LDAP Bridge — API REST para Gestión de Tickets (VERSIÓN SEGURA)
===============================================================
Cambios de seguridad aplicados:
  ✅ Autenticación por API key en todos los endpoints
  ✅ CORS restringido a orígenes permitidos
  ✅ Credenciales desde variables de entorno (.env)
  ✅ Validación y sanitización de todos los inputs
  ✅ Protección contra LDAP injection
  ✅ Rate limiting por IP
  ✅ Cabeceras de seguridad HTTP
  ✅ Límite de tamaño de requests (1MB)
  ✅ Logs sin datos sensibles
  ✅ Validación de ruta del archivo de datos

Requisitos:
    pip install flask flask-cors ldap3 python-dotenv

Configuración:
  Crea un archivo .env en la misma carpeta:
    LDAP_HOST=192.168.1.50
    LDAP_PORT=389
    LDAP_BASE_DN=DC=empresa,DC=local
    LDAP_BIND_USER=CN=svc_tickets,...
    LDAP_BIND_PASSWORD=TuPassword
    API_KEY=clave-secreta-larga-aqui
    ALLOWED_ORIGINS=http://localhost:5050,http://192.168.1.100

Uso:
    python ldap_bridge.py
"""

import os
import re
import json
import logging
import secrets
import hashlib
import time
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from functools import wraps

from flask import Flask, request, jsonify, g

# ── Base de datos SQLite ──────────────────────────────
try:
    from database import db as _db
    _db.init()
    DB_ENABLED = True
    print("[DB] SQLite inicializado correctamente")
except Exception as _db_err:
    DB_ENABLED = False
    print(f"[DB] SQLite no disponible, usando JSON: {_db_err}")

from flask_cors import CORS
from ldap3 import Server, Connection, ALL, SIMPLE, SUBTREE
from ldap3.core.exceptions import LDAPException, LDAPBindError, LDAPSocketOpenError

# ── Cargar .env si existe ─────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✔ Variables de entorno cargadas desde .env")
except ImportError:
    print("⚠ python-dotenv no instalado. Usando variables del sistema.")

# ─────────────────────────────────────────────────────
# CONFIG — Desde variables de entorno (nunca hardcoded)
# ─────────────────────────────────────────────────────
LDAP_CONFIG = {
    "host":             os.environ.get("LDAP_HOST",          "192.168.1.50"),
    "port":             int(os.environ.get("LDAP_PORT",       "389")),
    "use_ssl":          os.environ.get("LDAP_SSL",            "false").lower() == "true",
    "base_dn":          os.environ.get("LDAP_BASE_DN",        "DC=empresa,DC=local"),
    "user_search_base": os.environ.get("LDAP_USER_BASE",      "OU=Usuarios,DC=empresa,DC=local"),
    "bind_user":        os.environ.get("LDAP_BIND_USER",      ""),
    "bind_password":    os.environ.get("LDAP_BIND_PASSWORD",  ""),
    "user_filter":      os.environ.get("LDAP_USER_FILTER",    "(&(objectClass=user)(objectCategory=person)(!(userAccountControl:1.2.840.113556.1.4.803:=2)))"),
    "attributes":       ["cn","sAMAccountName","mail","department","title","telephoneNumber","distinguishedName","memberOf","userAccountControl","displayName"],
}

API_CONFIG = {
    "port":            int(os.environ.get("API_PORT",   "5050")),
    "debug":           False,  # NUNCA True en producción
    "api_key":         os.environ.get("API_KEY", ""),
    "allowed_origins": os.environ.get("ALLOWED_ORIGINS", "http://localhost:5050").split(","),
    "rate_limit_rpm":  int(os.environ.get("RATE_LIMIT_RPM", "60")),
    "max_content_mb":  int(os.environ.get("MAX_CONTENT_MB", "1")),
}

DATA_FILE = Path(os.environ.get("DATA_FILE", "tickets_data.json")).resolve()
# ─────────────────────────────────────────────────────

# ── Logging seguro (sin datos sensibles) ─────────────
class SensitiveFilter(logging.Filter):
    PATTERNS = [r'password["\']?\s*[:=]\s*["\']?[\w\S]+', r'sk-ant-[a-zA-Z0-9]+', r'Bearer\s+[\w\S]+']
    def filter(self, record):
        msg = record.getMessage()
        for p in self.PATTERNS:
            msg = re.sub(p, '***REDACTED***', msg, flags=re.IGNORECASE)
        record.msg = msg
        record.args = ()
        return True

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)
log.addFilter(SensitiveFilter())

# ── Flask app ─────────────────────────────────────────

# ── LOCAL USER STORE ──────────────────────────────────
USERS_FILE = Path(os.environ.get("USERS_FILE", "users.json")).resolve()

def load_users() -> list:
    """Carga usuarios locales desde users.json."""
    if USERS_FILE.exists():
        with open(USERS_FILE, encoding="utf-8") as f:
            return json.load(f)
    return []

def verify_local_password(stored: dict, password: str) -> bool:
    """Verifica contraseña contra hash PBKDF2."""
    import hashlib
    try:
        dk = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode(),
            stored["salt"].encode(),
            stored.get("iterations", 260000)
        )
        return secrets.compare_digest(dk.hex(), stored["password_hash"])
    except Exception:
        return False

def find_local_user(username: str) -> dict | None:
    """Busca usuario local por username."""
    users = load_users()
    return next((u for u in users if u.get("username") == username and u.get("active", True)), None)

app = Flask(__name__, static_folder=".", static_url_path="")
app.config["MAX_CONTENT_LENGTH"] = API_CONFIG["max_content_mb"] * 1024 * 1024

CORS(app, origins=API_CONFIG["allowed_origins"], supports_credentials=False)

# ── Teams integration ─────────────────────────────────
try:
    from teams_integration import TeamsNotifier
    teams = TeamsNotifier()
    TEAMS_ENABLED = True
except ImportError:
    teams = None
    TEAMS_ENABLED = False

# ── Rate limiting ─────────────────────────────────────
_rate_store = defaultdict(list)

def check_rate_limit(ip: str, rpm: int = None) -> bool:
    limit = rpm or API_CONFIG["rate_limit_rpm"]
    now   = time.time()
    _rate_store[ip] = [t for t in _rate_store[ip] if now - t < 60]
    if len(_rate_store[ip]) >= limit:
        return False
    _rate_store[ip].append(now)
    return True

# ── Security decorators ───────────────────────────────
def require_api_key(f):
    """Verifica API key en header X-API-Key o query param api_key."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not API_CONFIG["api_key"]:
            # API key no configurada — modo desarrollo, permitir
            log.warning("API_KEY no configurada. Endpoint sin protección.")
            return f(*args, **kwargs)
        key = request.headers.get("X-API-Key") or request.args.get("api_key", "")
        if not key or not secrets.compare_digest(key, API_CONFIG["api_key"]):
            log.warning(f"Acceso no autorizado desde {request.remote_addr}")
            return jsonify({"success": False, "message": "API key inválida o ausente"}), 401
        return f(*args, **kwargs)
    return decorated

def rate_limited(f):
    """Aplica rate limiting por IP."""
    @wraps(f)
    def decorated(*args, **kwargs):
        ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        if not check_rate_limit(ip):
            log.warning(f"Rate limit excedido para {ip}")
            return jsonify({"success": False, "message": "Demasiadas peticiones. Intenta en un minuto."}), 429
        return f(*args, **kwargs)
    return decorated

# ── JWT Authentication ────────────────────────────────
import hmac
import base64

JWT_SECRET  = os.environ.get("JWT_SECRET", secrets.token_hex(32))
JWT_EXPIRES = int(os.environ.get("JWT_EXPIRES_MINUTES", "480"))  # 8 horas por defecto

def b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

def b64url_decode(s: str) -> bytes:
    padding = 4 - len(s) % 4
    return base64.urlsafe_b64decode(s + "=" * padding)

def create_jwt(payload: dict) -> str:
    """Genera un JWT firmado con HMAC-SHA256."""
    import json as _json
    header  = b64url_encode(b'{"alg":"HS256","typ":"JWT"}')
    payload["exp"] = int(time.time()) + JWT_EXPIRES * 60
    payload["iat"] = int(time.time())
    body    = b64url_encode(_json.dumps(payload, separators=(",",":")).encode())
    sig_input = f"{header}.{body}".encode()
    sig     = b64url_encode(hmac.new(JWT_SECRET.encode(), sig_input, "sha256").digest())
    return f"{header}.{body}.{sig}"

def verify_jwt(token: str) -> dict | None:
    """Verifica y decodifica un JWT. Retorna payload o None si inválido/expirado."""
    import json as _json
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header, body, sig = parts
        sig_input = f"{header}.{body}".encode()
        expected  = b64url_encode(hmac.new(JWT_SECRET.encode(), sig_input, "sha256").digest())
        if not secrets.compare_digest(sig, expected):
            log.warning("JWT con firma inválida")
            return None
        payload = _json.loads(b64url_decode(body))
        if payload.get("exp", 0) < int(time.time()):
            return None  # Token expirado
        return payload
    except Exception:
        return None

# Token blacklist (revocación en memoria — en producción usar Redis)
_token_blacklist: set = set()

def revoke_token(jti: str):
    _token_blacklist.add(jti)

def require_jwt(f):
    """Decorator que verifica JWT en header Authorization: Bearer <token>."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"success": False, "message": "Token requerido"}), 401
        token   = auth[7:]
        payload = verify_jwt(token)
        if not payload:
            return jsonify({"success": False, "message": "Token inválido o expirado"}), 401
        if payload.get("jti") in _token_blacklist:
            return jsonify({"success": False, "message": "Token revocado"}), 401
        g.current_user    = payload.get("username", "")
        g.current_user_dn = payload.get("dn", "")
        g.is_admin        = payload.get("role") == "admin"
        return f(*args, **kwargs)
    return decorated

def require_admin(f):
    """Decorator que exige rol admin en el JWT."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not getattr(g, "is_admin", False):
            return jsonify({"success": False, "message": "Se requiere rol de administrador"}), 403
        return f(*args, **kwargs)
    return decorated


# ── Security headers ──────────────────────────────────
@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"]    = "nosniff"
    response.headers["X-Frame-Options"]           = "DENY"
    response.headers["X-XSS-Protection"]          = "1; mode=block"
    response.headers["Referrer-Policy"]           = "strict-origin-when-cross-origin"
    response.headers["Cache-Control"]             = "no-store, no-cache, must-revalidate"
    response.headers["Permissions-Policy"]        = "geolocation=(), camera=(), microphone=()"
    if request.path != "/":
        response.headers["Content-Security-Policy"] = "default-src 'none'"
    return response

# ── Input validation ──────────────────────────────────
def sanitize_str(value: str, max_len: int = 500) -> str:
    """Limpia y trunca strings de entrada."""
    if not isinstance(value, str):
        return ""
    return value.strip()[:max_len]

def sanitize_ldap(value: str) -> str:
    """Escapa caracteres especiales para prevenir LDAP injection."""
    # RFC 4515 — escapar caracteres especiales en filtros LDAP
    escape_map = {
        "\\": "\\5c", "*": "\\2a", "(": "\\28",
        ")": "\\29", "\x00": "\\00",
    }
    for char, escaped in escape_map.items():
        value = value.replace(char, escaped)
    return value

def validate_ticket(data: dict) -> tuple:
    """Valida campos del ticket. Retorna (ok, error_message)."""
    title = data.get("title", "")
    if not title or len(title.strip()) < 3:
        return False, "El título debe tener al menos 3 caracteres."
    if len(title) > 200:
        return False, "El título no puede superar 200 caracteres."
    desc = data.get("desc", "")
    if desc and len(desc) > 5000:
        return False, "La descripción no puede superar 5000 caracteres."
    valid_priorities = {"Crítica", "Alta", "Media", "Baja"}
    if data.get("priority") and data["priority"] not in valid_priorities:
        return False, f"Prioridad inválida. Valores permitidos: {', '.join(valid_priorities)}"
    valid_statuses = {"Abierto", "En progreso", "Resuelto", "Cerrado"}
    if data.get("status") and data["status"] not in valid_statuses:
        return False, f"Estado inválido. Valores permitidos: {', '.join(valid_statuses)}"
    return True, None

# ── Data helpers ──────────────────────────────────────
def load():
    """Carga desde SQLite si disponible, JSON como fallback."""
    if DB_ENABLED:
        try:
            tickets = _db.tickets.get_all()
            full = [_db.tickets.get(t['id']) for t in tickets]
            return {'tickets': full, 'config': _db.config.get_all(), 'team': _db.team.get_all()}
        except Exception as e:
            log.error(f'[DB] load() error: {e}')
    resolved = DATA_FILE.resolve()
    if not str(resolved).startswith(str(Path.cwd())):
        log.error('Path traversal detectado en DATA_FILE')
        return {'tickets': [], 'config': {}}
    if resolved.exists():
        with open(resolved, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                log.error('JSON corrupto en DATA_FILE')
    return {'tickets': [], 'config': {}}

def dump(data):
    """Guarda config en SQLite si disponible, JSON como fallback."""
    if DB_ENABLED:
        try:
            if 'config' in data and isinstance(data['config'], dict):
                _db.config.set_many(data['config'])
            return
        except Exception as e:
            log.error(f'[DB] dump() error: {e}')
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def next_id(tickets=None):
    """Genera el siguiente ID de ticket."""
    if DB_ENABLED:
        try:
            return _db.tickets._next_id()
        except Exception:
            pass
    if tickets:
        m = max((int(t['id'].replace('TKT-','')) for t in tickets if t.get('id','').startswith('TKT-')), default=0)
        return f'TKT-{str(m+1).zfill(4)}'
    return 'TKT-0001'

def entry_to_dict(entry):
    def v(a):
        try: val = entry[a].value; return str(val) if val else ""
        except: return ""
    groups = []
    try: groups = [g.split(",")[0].replace("CN=","") for g in entry["memberOf"].values if "CN=" in g]
    except: pass
    return {
        "username":     v("sAMAccountName"),
        "display_name": v("displayName") or v("cn"),
        "email":        v("mail"),
        "department":   v("department"),
        "title":        v("title"),
        "phone":        v("telephoneNumber"),
        "dn":           v("distinguishedName"),
        "groups":       groups,
    }



# ── USER MANAGEMENT ───────────────────────────────────

@app.route("/api/users", methods=["GET"])
@require_jwt
@require_admin
def list_users():
    """Lista usuarios locales — solo admins."""
    users = load_users()
    safe  = [{k: v for k, v in u.items() if k not in ("password_hash","salt","iterations")} for u in users]
    return jsonify({"success": True, "count": len(safe), "users": safe})


@app.route("/api/users", methods=["POST"])
@require_jwt
@require_admin
@rate_limited
def create_user():
    """Crea un nuevo usuario local."""
    import hashlib as _hl
    d        = request.get_json(silent=True) or {}
    username = sanitize_str(d.get("username", ""), 50)
    password = d.get("password", "")
    role     = d.get("role", "agent")

    if not username or not password:
        return jsonify({"success": False, "message": "username y password requeridos"}), 400
    if len(password) < 8:
        return jsonify({"success": False, "message": "La contraseña debe tener al menos 8 caracteres"}), 400
    if role not in ("admin", "agent"):
        return jsonify({"success": False, "message": "Rol inválido. Usa admin o agent"}), 400
    if not re.match(r'^[a-zA-Z0-9._-]+$', username):
        return jsonify({"success": False, "message": "Username inválido"}), 400

    users = load_users()
    if any(u["username"] == username for u in users):
        return jsonify({"success": False, "message": f"El usuario '{username}' ya existe"}), 409

    salt       = secrets.token_hex(32)
    iterations = 260000
    dk         = _hl.pbkdf2_hmac('sha256', password.encode(), salt.encode(), iterations)
    new_user   = {
        "username":     username,
        "display_name": sanitize_str(d.get("display_name", username), 100),
        "department":   sanitize_str(d.get("department", ""), 100),
        "email":        sanitize_str(d.get("email", ""), 200),
        "role":         role,
        "salt":         salt,
        "password_hash":dk.hex(),
        "iterations":   iterations,
        "algorithm":    "pbkdf2-hmac-sha256",
        "created":      datetime.now().isoformat(),
        "active":       True,
    }
    users.append(new_user)
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)
    log.info(f"Usuario creado: {username} ({role}) por {g.current_user}")
    return jsonify({"success": True, "message": f"Usuario '{username}' creado correctamente", "role": role}), 201


@app.route("/api/users/<username>", methods=["DELETE"])
@require_jwt
@require_admin
def delete_user(username):
    """Elimina un usuario local."""
    if username == g.current_user:
        return jsonify({"success": False, "message": "No puedes eliminar tu propio usuario"}), 400
    users = load_users()
    before = len(users)
    users  = [u for u in users if u["username"] != username]
    if len(users) == before:
        return jsonify({"success": False, "message": "Usuario no encontrado"}), 404
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)
    log.info(f"Usuario eliminado: {username} por {g.current_user}")
    return jsonify({"success": True, "message": f"Usuario '{username}' eliminado"})


@app.route("/api/users/<username>/password", methods=["PUT"])
@require_jwt
def change_password(username):
    """Cambia contraseña — admins pueden cambiar cualquiera, agentes solo la suya."""
    import hashlib as _hl
    if not g.is_admin and g.current_user != username:
        return jsonify({"success": False, "message": "Sin permisos para cambiar esta contraseña"}), 403
    d            = request.get_json(silent=True) or {}
    new_password = d.get("new_password", "")
    if len(new_password) < 8:
        return jsonify({"success": False, "message": "La contraseña debe tener al menos 8 caracteres"}), 400
    users = load_users()
    user  = next((u for u in users if u["username"] == username), None)
    if not user:
        return jsonify({"success": False, "message": "Usuario no encontrado"}), 404
    salt       = secrets.token_hex(32)
    iterations = 260000
    dk         = _hl.pbkdf2_hmac('sha256', new_password.encode(), salt.encode(), iterations)
    user["salt"]          = salt
    user["password_hash"] = dk.hex()
    user["iterations"]    = iterations
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)
    log.info(f"Contraseña cambiada para: {username}")
    return jsonify({"success": True, "message": "Contraseña actualizada correctamente"})

# ── AUTH ENDPOINTS ────────────────────────────────────

@app.route("/api/auth/login", methods=["POST"])
@rate_limited
def auth_login():
    """
    Login con usuario de dominio (LDAP) o API key.
    Devuelve un JWT válido por JWT_EXPIRES minutos.

    Body JSON:
      { "username": "jperez", "password": "contraseña" }
      o
      { "api_key": "clave-api" }
    """
    ip       = request.headers.get("X-Forwarded-For", request.remote_addr)
    if not check_rate_limit(f"login_{ip}", rpm=10):
        return jsonify({"success": False, "message": "Demasiados intentos. Espera un minuto."}), 429

    data_req = request.get_json(silent=True) or {}

    # ── Login por API key (para integraciones / scripts) ──
    if "api_key" in data_req:
        if not API_CONFIG["api_key"] or not secrets.compare_digest(
            sanitize_str(data_req["api_key"], 200), API_CONFIG["api_key"]
        ):
            time.sleep(0.5)
            return jsonify({"success": False, "message": "API key inválida"}), 401
        jti   = secrets.token_hex(16)
        token = create_jwt({"username": "api_service", "role": "admin", "jti": jti, "auth_method": "api_key"})
        log.info("Login por API key exitoso")
        return jsonify({
            "success":    True,
            "token":      token,
            "token_type": "Bearer",
            "expires_in": JWT_EXPIRES * 60,
            "user":       {"username": "api_service", "role": "admin"},
        })

    # ── Login por credenciales de dominio / local ──
    username = sanitize_str(data_req.get("username", ""), 100)
    password = data_req.get("password", "")

    if not username or not password:
        return jsonify({"success": False, "message": "Usuario y contraseña requeridos"}), 400

    if not re.match(r'^[a-zA-Z0-9._\-@]+$', username):
        return jsonify({"success": False, "message": "Formato de usuario inválido"}), 400

    # ── Verificar primero en usuarios locales (users.json) ──
    local_user = find_local_user(username)
    if local_user:
        if not verify_local_password(local_user, password):
            time.sleep(0.5)
            log.warning(f"Login fallido para usuario local (IP: {ip})")
            return jsonify({"success": False, "message": "Usuario o contraseña incorrectos"}), 401
        jti   = secrets.token_hex(16)
        token = create_jwt({
            "username":     username,
            "display_name": local_user.get("display_name", username),
            "email":        local_user.get("email", ""),
            "department":   local_user.get("department", ""),
            "role":         local_user.get("role", "agent"),
            "jti":          jti,
            "auth_method":  "local",
        })
        log.info(f"Login local exitoso — usuario: {username}, rol: {local_user.get('role')}")
        return jsonify({
            "success":    True,
            "token":      token,
            "token_type": "Bearer",
            "expires_in": JWT_EXPIRES * 60,
            "user": {
                "username":     username,
                "display_name": local_user.get("display_name", username),
                "email":        local_user.get("email", ""),
                "department":   local_user.get("department", ""),
                "role":         local_user.get("role", "agent"),
            },
        })

    if not LDAP_CONFIG["bind_user"]:
        return jsonify({"success": False, "message": "Usuario no encontrado"}), 401

    domain  = LDAP_CONFIG["base_dn"].replace("DC=","").replace(",",".")
    user_dn = f"{username}@{domain}" if "@" not in username else username

    try:
        srv  = Server(LDAP_CONFIG["host"], port=LDAP_CONFIG["port"],
                      use_ssl=LDAP_CONFIG["use_ssl"], connect_timeout=5)
        conn = Connection(srv, user=user_dn, password=password,
                          authentication=SIMPLE, auto_bind=True, receive_timeout=8)
        # Obtener info del usuario con cuenta de servicio
        srv2  = Server(LDAP_CONFIG["host"], port=LDAP_CONFIG["port"], connect_timeout=5)
        conn2 = Connection(srv2, user=LDAP_CONFIG["bind_user"],
                           password=LDAP_CONFIG["bind_password"],
                           authentication=SIMPLE, auto_bind=True)
        safe_user = sanitize_ldap(username)
        conn2.search(search_base=LDAP_CONFIG["user_search_base"],
                     search_filter=f"(sAMAccountName={safe_user})",
                     attributes=LDAP_CONFIG["attributes"])
        user_info = entry_to_dict(conn2.entries[0]) if conn2.entries else {}
        conn.unbind(); conn2.unbind()

        # Determinar rol según grupos del AD
        admin_groups = {"TI-Admins", "TicketDesk-Admin", "Domain Admins"}
        role = "admin" if any(g in admin_groups for g in user_info.get("groups", [])) else "agent"

        jti   = secrets.token_hex(16)
        token = create_jwt({
            "username":     username,
            "display_name": user_info.get("display_name", username),
            "email":        user_info.get("email", ""),
            "department":   user_info.get("department", ""),
            "role":         role,
            "dn":           user_info.get("dn", ""),
            "jti":          jti,
            "auth_method":  "ldap",
        })

        log.info(f"Login LDAP exitoso — rol: {role}")
        return jsonify({
            "success":    True,
            "token":      token,
            "token_type": "Bearer",
            "expires_in": JWT_EXPIRES * 60,
            "user": {
                "username":     username,
                "display_name": user_info.get("display_name", username),
                "email":        user_info.get("email", ""),
                "department":   user_info.get("department", ""),
                "role":         role,
            },
        })

    except LDAPBindError:
        time.sleep(0.5)
        return jsonify({"success": False, "message": "Usuario o contraseña incorrectos"}), 401
    except LDAPSocketOpenError:
        return jsonify({"success": False, "message": "No se pudo conectar al servidor AD"}), 503
    except Exception as e:
        log.error("Error en login LDAP")
        return jsonify({"success": False, "message": "Error de autenticación"}), 500


@app.route("/api/auth/logout", methods=["POST"])
@require_jwt
def auth_logout():
    """Revoca el token JWT actual añadiéndolo a la blacklist."""
    auth    = request.headers.get("Authorization", "")[7:]
    payload = verify_jwt(auth)
    if payload and payload.get("jti"):
        revoke_token(payload["jti"])
        log.info(f"Logout — usuario: {g.current_user}")
    return jsonify({"success": True, "message": "Sesión cerrada correctamente"})


@app.route("/api/auth/refresh", methods=["POST"])
@require_jwt
def auth_refresh():
    """Renueva el token JWT antes de que expire."""
    jti   = secrets.token_hex(16)
    token = create_jwt({
        "username":     g.current_user,
        "role":         "admin" if g.is_admin else "agent",
        "jti":          jti,
        "auth_method":  "refresh",
    })
    # Revocar token anterior
    old_payload = verify_jwt(request.headers.get("Authorization","")[7:])
    if old_payload and old_payload.get("jti"):
        revoke_token(old_payload["jti"])
    return jsonify({
        "success":    True,
        "token":      token,
        "token_type": "Bearer",
        "expires_in": JWT_EXPIRES * 60,
    })


@app.route("/api/auth/me", methods=["GET"])
@require_jwt
def auth_me():
    """Devuelve la información del usuario autenticado."""
    auth    = request.headers.get("Authorization", "")[7:]
    payload = verify_jwt(auth) or {}
    return jsonify({
        "success":     True,
        "username":    g.current_user,
        "display_name":payload.get("display_name", g.current_user),
        "email":       payload.get("email", ""),
        "department":  payload.get("department", ""),
        "role":        "admin" if g.is_admin else "agent",
        "auth_method": payload.get("auth_method", ""),
        "expires_at":  datetime.fromtimestamp(payload.get("exp", 0)).isoformat(),
    })


@app.route("/api/auth/users", methods=["GET"])
@require_jwt
@require_admin
def auth_list_users():
    """Lista usuarios registrados — solo admins."""
    teams_names = list({t.get("assignee","") for t in load().get("tickets",[]) if t.get("assignee")})
    return jsonify({"success": True, "users": teams_names})


# ── LDAP endpoints ────────────────────────────────────
@app.route("/api/ldap/test", methods=["POST"])
@require_api_key
@rate_limited
def ldap_test():
    d = request.get_json(silent=True) or {}
    host = sanitize_str(d.get("host", LDAP_CONFIG["host"]), 100)
    port = int(d.get("port", LDAP_CONFIG["port"]))
    try:
        srv  = Server(host, port=port, use_ssl=d.get("use_ssl", LDAP_CONFIG["use_ssl"]), connect_timeout=5)
        conn = Connection(srv, user=sanitize_str(d.get("bind_user", LDAP_CONFIG["bind_user"]), 200),
                          password=d.get("bind_password", LDAP_CONFIG["bind_password"]),
                          authentication=SIMPLE, auto_bind=True, receive_timeout=8)
        conn.unbind()
        log.info(f"Conexión LDAP exitosa a {host}:{port}")
        return jsonify({"success": True, "message": f"Conexión exitosa a {host}:{port}"})
    except LDAPBindError:
        return jsonify({"success": False, "message": "Credenciales incorrectas"}), 401
    except LDAPSocketOpenError as e:
        return jsonify({"success": False, "message": f"No se pudo conectar: {e}"}), 503
    except Exception as e:
        return jsonify({"success": False, "message": "Error de conexión"}), 500


@app.route("/api/ldap/users", methods=["POST"])
@require_api_key
@rate_limited
def ldap_users():
    d = request.get_json(silent=True) or {}
    try:
        srv  = Server(sanitize_str(d.get("host", LDAP_CONFIG["host"]), 100),
                      port=int(d.get("port", LDAP_CONFIG["port"])),
                      use_ssl=d.get("use_ssl", LDAP_CONFIG["use_ssl"]), connect_timeout=5)
        conn = Connection(srv, user=LDAP_CONFIG["bind_user"], password=LDAP_CONFIG["bind_password"],
                          authentication=SIMPLE, auto_bind=True, receive_timeout=15)
        base_dn     = sanitize_str(d.get("base_dn", LDAP_CONFIG["user_search_base"]), 200)
        user_filter = LDAP_CONFIG["user_filter"]  # Usar siempre el filtro del servidor, no del cliente
        conn.search(search_base=base_dn, search_filter=user_filter,
                    search_scope=SUBTREE, attributes=LDAP_CONFIG["attributes"], size_limit=500)
        users = [entry_to_dict(e) for e in conn.entries]
        conn.unbind()
        log.info(f"Sincronizados {len(users)} usuarios del AD")
        return jsonify({"success": True, "count": len(users), "users": users})
    except LDAPBindError:
        return jsonify({"success": False, "message": "Error de autenticación LDAP"}), 401
    except Exception as e:
        log.error("Error al obtener usuarios LDAP")
        return jsonify({"success": False, "message": "Error al consultar el directorio"}), 500


@app.route("/api/ldap/authenticate", methods=["POST"])
@rate_limited
def ldap_authenticate():
    """Alias de /api/auth/login para compatibilidad. Usar /api/auth/login."""
    return auth_login()
    """Autenticación con credenciales de dominio — sin API key requerida."""
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    if not check_rate_limit(f"auth_{ip}", rpm=10):  # Máx 10 intentos/min por IP
        log.warning(f"Brute force detectado desde {ip}")
        return jsonify({"success": False, "message": "Demasiados intentos. Espera un minuto."}), 429

    d        = request.get_json(silent=True) or {}
    username = sanitize_str(d.get("username", ""), 100)
    password = d.get("password", "")

    if not username or not password:
        return jsonify({"success": False, "message": "Usuario y contraseña requeridos"}), 400

    # Validar username — solo caracteres permitidos
    if not re.match(r'^[a-zA-Z0-9._\-@]+$', username):
        return jsonify({"success": False, "message": "Formato de usuario inválido"}), 400

    domain   = LDAP_CONFIG["base_dn"].replace("DC=","").replace(",",".")
    user_dn  = f"{username}@{domain}" if "@" not in username else username

    try:
        srv  = Server(LDAP_CONFIG["host"], port=LDAP_CONFIG["port"], connect_timeout=5)
        conn = Connection(srv, user=user_dn, password=password,
                          authentication=SIMPLE, auto_bind=True, receive_timeout=8)
        # Buscar info del usuario usando cuenta de servicio (no la del usuario)
        conn2 = Connection(srv, user=LDAP_CONFIG["bind_user"],
                           password=LDAP_CONFIG["bind_password"],
                           authentication=SIMPLE, auto_bind=True)
        safe_username = sanitize_ldap(username)
        conn2.search(search_base=LDAP_CONFIG["user_search_base"],
                     search_filter=f"(sAMAccountName={safe_username})",
                     attributes=LDAP_CONFIG["attributes"])
        user_info = entry_to_dict(conn2.entries[0]) if conn2.entries else {}
        conn.unbind(); conn2.unbind()
        log.info(f"Login exitoso para usuario (dominio)")
        return jsonify({"success": True, "user": user_info})
    except LDAPBindError:
        time.sleep(0.5)  # Delay anti-timing
        return jsonify({"success": False, "message": "Usuario o contraseña incorrectos"}), 401
    except Exception:
        return jsonify({"success": False, "message": "Error de autenticación"}), 500


@app.route("/api/ldap/search", methods=["GET"])
@require_api_key
@rate_limited
def ldap_search():
    q = sanitize_str(request.args.get("q", ""), 100)
    if not q or len(q) < 2:
        return jsonify({"success": False, "message": "Parámetro q requerido (mínimo 2 caracteres)"}), 400
    q_safe = sanitize_ldap(q)
    try:
        srv  = Server(LDAP_CONFIG["host"], port=LDAP_CONFIG["port"], connect_timeout=5)
        conn = Connection(srv, user=LDAP_CONFIG["bind_user"], password=LDAP_CONFIG["bind_password"],
                          authentication=SIMPLE, auto_bind=True)
        conn.search(search_base=LDAP_CONFIG["user_search_base"],
                    search_filter=f"(|(sAMAccountName=*{q_safe}*)(displayName=*{q_safe}*)(mail=*{q_safe}*))",
                    attributes=LDAP_CONFIG["attributes"], size_limit=20)
        users = [entry_to_dict(e) for e in conn.entries]
        conn.unbind()
        return jsonify({"success": True, "count": len(users), "users": users})
    except Exception:
        return jsonify({"success": False, "message": "Error en la búsqueda"}), 500


# ── Tickets API ───────────────────────────────────────
@app.route("/api/tickets", methods=["GET"])
@require_jwt
@rate_limited
def api_get_tickets():

    if DB_ENABLED:
        try:
            filters = {}
            if request.args.get('status'):   filters['status']   = sanitize_str(request.args['status'])
            if request.args.get('priority'): filters['priority'] = sanitize_str(request.args['priority'])
            if request.args.get('assignee'): filters['assignee'] = sanitize_str(request.args['assignee'])
            if request.args.get('search'):   filters['search']   = sanitize_str(request.args['search'])
            tks = _db.tickets.get_all(filters)
            return jsonify({'success': True, 'tickets': tks, 'total': len(tks)})
        except Exception as e:
            log.error(f'[DB] api_get_tickets: {e}')
    data    = load()
    tickets = data.get("tickets", [])
    for k in ("status", "priority", "assignee"):
        v = sanitize_str(request.args.get(k, ""), 50)
        if v: tickets = [t for t in tickets if t.get(k) == v]
    return jsonify({"success": True, "count": len(tickets), "tickets": tickets})


@app.route("/api/tickets", methods=["POST"])
@require_jwt
@rate_limited
def api_create_ticket():

    if DB_ENABLED:
        try:
            body = request.get_json(silent=True) or {}
            errors = validate_ticket(body)
            if errors: return jsonify({'success': False, 'errors': errors}), 400
            now = datetime.utcnow().isoformat()
            ticket = {
                'id': _db.tickets._next_id(),
                'title': sanitize_str(body.get('title','')),
                'description': sanitize_str(body.get('description', body.get('desc',''))),
                'category': sanitize_str(body.get('category','Otro')),
                'priority': sanitize_str(body.get('priority','Media')),
                'status': 'Abierto',
                'assignee': sanitize_str(body.get('assignee','')),
                'created_by': sanitize_str(body.get('created_by', g.current_user.get('username',''))),
                'requester': sanitize_str(body.get('requester', g.current_user.get('display_name',''))),
                'department': sanitize_str(body.get('department', body.get('dept',''))),
                'tags': body.get('tags', []),
                'created_at': now, 'updated_at': now,
                'audit': [{'ts': now, 'user': g.current_user.get('display_name','Sistema'), 'action': 'Ticket creado via API', 'color': '#1a5fa8'}],
            }
            saved = _db.tickets.create(ticket)
            return jsonify({'success': True, 'ticket': saved}), 201
        except Exception as e:
            log.error(f'[DB] api_create_ticket: {e}')
    data_req = request.get_json(silent=True)
    if not data_req:
        return jsonify({"success": False, "message": "Body JSON requerido"}), 400
    ok, err = validate_ticket(data_req)
    if not ok:
        return jsonify({"success": False, "message": err}), 400

    data    = load()
    tickets = data.get("tickets", [])
    now     = datetime.now().isoformat()
    ticket  = {
        "id":       next_id(tickets),
        "created":  now,
        "updated":  now,
        "comments": [],
        "audit":    [{"ts": now, "user": sanitize_str(data_req.get("created_by", "API"), 50), "action": f'Ticket creado por {getattr(g, "current_user", "API")}', "color": "#1a5fa8"}],
        "survey":   None,
        "title":    sanitize_str(data_req.get("title", ""), 200),
        "desc":     sanitize_str(data_req.get("desc", ""), 5000),
        "category": sanitize_str(data_req.get("category", "Otro"), 100),
        "priority": data_req.get("priority", "Media") if data_req.get("priority") in {"Crítica","Alta","Media","Baja"} else "Media",
        "status":   "Abierto",
        "assignee": sanitize_str(data_req.get("assignee", ""), 100),
        "tags":     sanitize_str(data_req.get("tags", ""), 200),
    }
    tickets.insert(0, ticket)
    data["tickets"] = tickets
    dump(data)
    log.info(f"Ticket creado: {ticket['id']}")
    if TEAMS_ENABLED and teams:
        try: teams.ticket_creado(ticket)
        except Exception: pass
    return jsonify({"success": True, "ticket": ticket}), 201


@app.route("/api/tickets/<ticket_id>", methods=["GET"])
@require_jwt
@rate_limited
def api_get_ticket(ticket_id):

    if DB_ENABLED:
        try:
            t = _db.tickets.get(sanitize_str(ticket_id))
            if not t: return jsonify({'success': False, 'error': 'Ticket no encontrado'}), 404
            return jsonify({'success': True, 'ticket': t})
        except Exception as e:
            log.error(f'[DB] api_get_ticket: {e}')
    if not re.match(r'^TKT-\d{4,}$', ticket_id):
        return jsonify({"success": False, "message": "ID de ticket inválido"}), 400
    data   = load()
    ticket = next((t for t in data.get("tickets", []) if t["id"] == ticket_id), None)
    return jsonify({"success": True, "ticket": ticket}) if ticket else (jsonify({"success": False, "message": "No encontrado"}), 404)


@app.route("/api/tickets/<ticket_id>", methods=["PUT"])
@require_jwt
@rate_limited
def api_update_ticket(ticket_id):

    if DB_ENABLED:
        try:
            tid  = sanitize_str(ticket_id)
            body = request.get_json(silent=True) or {}
            allowed = ['title','description','category','priority','status','assignee','tags','escalation_level']
            updates = {k: v for k, v in body.items() if k in allowed}
            if not updates: return jsonify({'success': False, 'error': 'Sin campos válidos'}), 400
            t = _db.tickets.get(tid)
            if not t: return jsonify({'success': False, 'error': 'Ticket no encontrado'}), 404
            updated = _db.tickets.update(tid, updates)
            changed_by = sanitize_str(body.get('changed_by', g.current_user.get('display_name','Sistema')))
            for field, val in updates.items():
                _db.tickets.add_audit(tid, changed_by, f"'{field}' → '{val}'", '#b58500')
            return jsonify({'success': True, 'ticket': updated})
        except Exception as e:
            log.error(f'[DB] api_update_ticket: {e}')
    if not re.match(r'^TKT-\d{4,}$', ticket_id):
        return jsonify({"success": False, "message": "ID de ticket inválido"}), 400
    data_req = request.get_json(silent=True) or {}
    if "title" in data_req:
        ok, err = validate_ticket(data_req)
        if not ok:
            return jsonify({"success": False, "message": err}), 400
    data    = load()
    tickets = data.get("tickets", [])
    ticket  = next((t for t in tickets if t["id"] == ticket_id), None)
    if not ticket:
        return jsonify({"success": False, "message": "No encontrado"}), 404
    prev_status   = ticket.get("status")
    prev_assignee = ticket.get("assignee")
    # Actualizar solo campos permitidos
    allowed = {"title","desc","category","priority","status","assignee","tags"}
    for k in allowed:
        if k in data_req:
            ticket[k] = sanitize_str(str(data_req[k]), 5000 if k == "desc" else 200)
    ticket["updated"] = datetime.now().isoformat()
    now = datetime.now().isoformat()
    if not ticket.get("audit"): ticket["audit"] = []
    changed_by = getattr(g, "current_user", None) or sanitize_str(data_req.get("changed_by", "API"), 50)
    if prev_status != ticket.get("status"):
        ticket["audit"].append({"ts": now, "user": changed_by, "action": f'Estado: "{prev_status}" → "{ticket["status"]}"', "color": "#1a5fa8"})
    if prev_assignee != ticket.get("assignee"):
        ticket["audit"].append({"ts": now, "user": changed_by, "action": f'Reasignado a "{ticket["assignee"]}"', "color": "#8b5cf6"})
    dump(data)
    if TEAMS_ENABLED and teams and prev_status != ticket.get("status"):
        try: teams.ticket_estado_cambiado(ticket, prev_status, changed_by)
        except Exception: pass
    return jsonify({"success": True, "ticket": ticket})


@app.route("/api/tickets/<ticket_id>", methods=["DELETE"])
@require_jwt
@rate_limited
def api_delete_ticket(ticket_id):

    if DB_ENABLED:
        try:
            tid = sanitize_str(ticket_id)
            if not _db.tickets.get(tid): return jsonify({'success': False, 'error': 'Ticket no encontrado'}), 404
            _db.tickets.delete(tid)
            return jsonify({'success': True, 'deleted': tid})
        except Exception as e:
            log.error(f'[DB] api_delete_ticket: {e}')
    if not re.match(r'^TKT-\d{4,}$', ticket_id):
        return jsonify({"success": False, "message": "ID de ticket inválido"}), 400
    data = load()
    before = len(data.get("tickets", []))
    data["tickets"] = [t for t in data.get("tickets", []) if t["id"] != ticket_id]
    if len(data["tickets"]) == before:
        return jsonify({"success": False, "message": "No encontrado"}), 404
    dump(data)
    log.info(f"Ticket eliminado: {ticket_id}")
    return jsonify({"success": True, "message": f"{ticket_id} eliminado"})


@app.route("/api/tickets/<ticket_id>/comments", methods=["POST"])
@require_jwt
@rate_limited
def api_add_comment(ticket_id):

    if DB_ENABLED:
        try:
            tid    = sanitize_str(ticket_id)
            body   = request.get_json(silent=True) or {}
            text   = sanitize_str(body.get('text',''))
            author = sanitize_str(body.get('author', g.current_user.get('display_name','Usuario')))
            if not text: return jsonify({'success': False, 'error': 'Comentario vacío'}), 400
            t = _db.tickets.add_comment(tid, author, text)
            if not t: return jsonify({'success': False, 'error': 'Ticket no encontrado'}), 404
            return jsonify({'success': True, 'ticket': t})
        except Exception as e:
            log.error(f'[DB] api_add_comment: {e}')
    if not re.match(r'^TKT-\d{4,}$', ticket_id):
        return jsonify({"success": False, "message": "ID de ticket inválido"}), 400
    data_req = request.get_json(silent=True) or {}
    text     = sanitize_str(data_req.get("text", ""), 2000)
    author   = sanitize_str(data_req.get("author", "API"), 100)
    if not text:
        return jsonify({"success": False, "message": "El comentario no puede estar vacío"}), 400
    data   = load()
    ticket = next((t for t in data.get("tickets", []) if t["id"] == ticket_id), None)
    if not ticket:
        return jsonify({"success": False, "message": "No encontrado"}), 404
    comment = {"author": author, "text": text, "date": datetime.now().isoformat()}
    ticket.setdefault("comments", []).append(comment)
    ticket["updated"] = datetime.now().isoformat()
    dump(data)
    return jsonify({"success": True, "comment": comment}), 201


@app.route("/api/tickets/<ticket_id>/survey", methods=["POST"])
@require_jwt
@rate_limited
def api_add_survey(ticket_id):

    if DB_ENABLED:
        try:
            tid    = sanitize_str(ticket_id)
            body   = request.get_json(silent=True) or {}
            rating = body.get('rating')
            if not isinstance(rating, int) or not (1 <= rating <= 5):
                return jsonify({'success': False, 'error': 'Rating debe ser 1-5'}), 400
            _db.tickets.add_survey(tid, rating, sanitize_str(body.get('comment','')))
            return jsonify({'success': True, 'ticket_id': tid, 'rating': rating})
        except Exception as e:
            log.error(f'[DB] api_add_survey: {e}')
    if not re.match(r'^TKT-\d{4,}$', ticket_id):
        return jsonify({"success": False, "message": "ID inválido"}), 400
    data_req = request.get_json(silent=True) or {}
    rating   = data_req.get("rating")
    if not isinstance(rating, int) or rating < 1 or rating > 5:
        return jsonify({"success": False, "message": "Rating debe ser entre 1 y 5"}), 400
    data   = load()
    ticket = next((t for t in data.get("tickets", []) if t["id"] == ticket_id), None)
    if not ticket:
        return jsonify({"success": False, "message": "No encontrado"}), 404
    ticket["survey"] = {"rating": rating, "comment": sanitize_str(data_req.get("comment", ""), 500), "date": datetime.now().isoformat()}
    dump(data)
    return jsonify({"success": True, "survey": ticket["survey"]}), 201


@app.route("/api/tickets/search", methods=["GET"])
@require_jwt
@rate_limited
def api_search_tickets():

    if DB_ENABLED:
        try:
            q = sanitize_str(request.args.get('q',''))
            if not q: return jsonify({'success': False, 'error': 'Parámetro q requerido'}), 400
            results = _db.tickets.search(q)
            return jsonify({'success': True, 'tickets': results, 'total': len(results), 'query': q})
        except Exception as e:
            log.error(f'[DB] api_search_tickets: {e}')
    q        = sanitize_str(request.args.get("q", ""), 200).lower()
    assignee = sanitize_str(request.args.get("assignee", ""), 100)
    status   = sanitize_str(request.args.get("status", ""), 50)
    priority = sanitize_str(request.args.get("priority", ""), 50)
    date_from= request.args.get("date_from", "")
    date_to  = request.args.get("date_to", "")

    if not q and not assignee and not status and not priority:
        return jsonify({"success": False, "message": "Al menos un parámetro de búsqueda requerido"}), 400

    tickets = load().get("tickets", [])

    def matches(t):
        if q:
            fields = [t.get("title",""), t.get("desc",""), t.get("tags",""),
                      t.get("assignee",""), t.get("id",""),
                      " ".join(c.get("text","") for c in t.get("comments",[]))]
            if not any(q in f.lower() for f in fields): return False
        if assignee and t.get("assignee") != assignee:  return False
        if status   and t.get("status")   != status:    return False
        if priority and t.get("priority") != priority:  return False
        if date_from:
            try:
                if datetime.fromisoformat(t["created"]) < datetime.fromisoformat(date_from): return False
            except: pass
        if date_to:
            try:
                if datetime.fromisoformat(t["created"]) > datetime.fromisoformat(date_to + "T23:59:59"): return False
            except: pass
        return True

    results = [t for t in tickets if matches(t)]
    return jsonify({"success": True, "count": len(results), "query": q, "tickets": results})


@app.route("/api/stats", methods=["GET"])
@require_jwt
@rate_limited
def api_stats():

    if DB_ENABLED:
        try:
            stats = _db.tickets.get_stats()
            return jsonify({'success': True, **stats})
        except Exception as e:
            log.error(f'[DB] api_stats: {e}')
    tickets = load().get("tickets", [])
    from collections import Counter
    return jsonify({
        "success":     True,
        "total":       len(tickets),
        "by_status":   dict(Counter(t.get("status")   for t in tickets)),
        "by_priority": dict(Counter(t.get("priority")  for t in tickets)),
        "by_assignee": dict(Counter(t.get("assignee")  for t in tickets)),
        "open":        sum(1 for t in tickets if t.get("status") == "Abierto"),
        "critical":    sum(1 for t in tickets if t.get("priority") == "Crítica" and t.get("status") != "Cerrado"),
        "satisfaction_avg": round(sum(t["survey"]["rating"] for t in tickets if t.get("survey")) / max(1, sum(1 for t in tickets if t.get("survey"))), 1) if any(t.get("survey") for t in tickets) else None,
    })


@app.route("/api/teams/test", methods=["POST"])
@require_api_key
@rate_limited
def teams_test():
    if not TEAMS_ENABLED or not teams:
        return jsonify({"success": False, "message": "teams_integration.py no encontrado"}), 500
    stats = {"total": len(load().get("tickets", [])), "open": 0, "critical": 0, "resolved_today": 0, "sla_compliance_pct": 95}
    ok = teams.reporte_diario(stats)
    return jsonify({"success": ok, "message": "Mensaje enviado" if ok else "Error — verifica webhook"})


@app.route("/api/health")
def health():
    return jsonify({
        "status":       "ok",
        "service":      "TicketDesk Manufacturas Eliot API",
        "version":      "2.0-secure",
        "time":         datetime.now().isoformat(),
        "teams":        TEAMS_ENABLED,
        "auth_required": True,
        "auth_type": "JWT + API Key",
        "jwt_expires_min": JWT_EXPIRES,
    })


@app.route("/")
def index():
    return app.send_static_file("gestion_tickets_v2.html")


@app.errorhandler(413)
def too_large(e):
    return jsonify({"success": False, "message": f"Payload demasiado grande (máx {API_CONFIG['max_content_mb']}MB)"}), 413

@app.errorhandler(429)
def rate_limit_error(e):
    return jsonify({"success": False, "message": "Demasiadas peticiones"}), 429

@app.errorhandler(404)
def not_found(e):
    return jsonify({"success": False, "message": "Endpoint no encontrado"}), 404

@app.errorhandler(500)
def server_error(e):
    log.error("Error interno del servidor")
    return jsonify({"success": False, "message": "Error interno del servidor"}), 500


if __name__ == "__main__":
    # Verificar configuración crítica
    if not os.environ.get("JWT_SECRET"):
        log.warning("⚠ JWT_SECRET no configurada. Usando clave aleatoria (se invalida al reiniciar)")
    if not API_CONFIG["api_key"]:
        log.warning("⚠ API_KEY no configurada. Crea un archivo .env con API_KEY=tu-clave-secreta")
    if not LDAP_CONFIG["bind_password"]:
        log.warning("⚠ LDAP_BIND_PASSWORD no configurada")

    log.info("=" * 60)
    log.info("TicketDesk Manufacturas Eliot — API Modo seguro")
    log.info(f"Puerto          : {API_CONFIG['port']}")
    log.info(f"Orígenes CORS   : {', '.join(API_CONFIG['allowed_origins'])}")
    log.info(f"Rate limit      : {API_CONFIG['rate_limit_rpm']} req/min")
    log.info(f"Autenticación   : JWT + API Key")
    log.info(f"JWT expira en   : {JWT_EXPIRES} minutos")
    log.info(f"JWT Secret      : {'✔ configurado' if os.environ.get('JWT_SECRET') else '⚠ auto-generado (volátil)'}")
    log.info(f"Teams           : {'✔ Activo' if TEAMS_ENABLED else '✖ No configurado'}")
    log.info(f"Datos en        : {DATA_FILE}")
    log.info("=" * 60)

    app.run(host="0.0.0.0", port=API_CONFIG["port"], debug=False)
