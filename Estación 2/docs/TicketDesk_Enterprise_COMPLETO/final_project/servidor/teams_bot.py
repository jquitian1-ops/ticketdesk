"""
TicketDesk — Bot de Microsoft Teams
=====================================
Bot completo para gestionar tickets directamente desde Teams.

Comandos disponibles:
  /nuevo <título>          — Crear ticket nuevo
  /ver <TKT-XXXX>          — Ver detalle de un ticket
  /mis                     — Ver mis tickets asignados
  /tomar <TKT-XXXX>        — Tomar un ticket abierto
  /progreso <TKT-XXXX>     — Cambiar a En progreso
  /resolver <TKT-XXXX>     — Marcar como resuelto
  /cerrar <TKT-XXXX>       — Cerrar un ticket
  /comentar <TKT-XXXX> <texto> — Agregar comentario
  /buscar <texto>          — Buscar tickets
  /pendientes              — Ver tickets sin asignar
  /sla                     — Ver tickets con SLA vencido
  /stats                   — Estadísticas del día
  /ayuda                   — Mostrar ayuda

Requisitos:
    pip install flask requests python-dotenv

Configuración en Azure / Teams:
  1. Registrar Bot en Azure Bot Service (portal.azure.com)
  2. Crear canal de Microsoft Teams
  3. Copiar MICROSOFT_APP_ID y MICROSOFT_APP_PASSWORD al .env
  4. Configurar el endpoint del bot: https://tuservidor.com/api/teams/bot

Variables de entorno requeridas (.env):
  MICROSOFT_APP_ID=tu-app-id
  MICROSOFT_APP_PASSWORD=tu-app-password
  TICKETDESK_API_URL=http://localhost:5050
  TICKETDESK_API_KEY=tu-api-key
  BOT_PORT=3978

Modo demo (sin Azure):
  Si no están configuradas las credenciales de Azure,
  el bot corre en modo simulación con respuestas de prueba.
"""

import os
import json
import re
import logging
import requests
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── CONFIG ────────────────────────────────────────────
MS_APP_ID       = os.environ.get("MICROSOFT_APP_ID", "")
MS_APP_PASSWORD = os.environ.get("MICROSOFT_APP_PASSWORD", "")
TD_API_URL      = os.environ.get("TICKETDESK_API_URL", "http://localhost:5050")
TD_API_KEY      = os.environ.get("TICKETDESK_API_KEY", "")
BOT_PORT        = int(os.environ.get("BOT_PORT", "3978"))
DEMO_MODE       = not MS_APP_ID or not MS_APP_PASSWORD

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

app = Flask(__name__)

# ── TOKEN MANAGER ─────────────────────────────────────
_token_cache = {"token": None, "expires": 0}

def get_ms_token():
    """Obtiene token OAuth2 de Microsoft para llamar a Bot Connector."""
    if DEMO_MODE:
        return "demo-token"
    import time
    if _token_cache["token"] and time.time() < _token_cache["expires"]:
        return _token_cache["token"]
    try:
        r = requests.post(
            "https://login.microsoftonline.com/botframework.com/oauth2/v2.0/token",
            data={
                "grant_type":    "client_credentials",
                "client_id":     MS_APP_ID,
                "client_secret": MS_APP_PASSWORD,
                "scope":         "https://api.botframework.com/.default",
            },
            timeout=10,
        )
        data = r.json()
        import time as _t
        _token_cache["token"]   = data["access_token"]
        _token_cache["expires"] = _t.time() + data.get("expires_in", 3600) - 60
        return _token_cache["token"]
    except Exception as e:
        log.error(f"Error obteniendo token MS: {e}")
        return None

# ── TICKETDESK API ────────────────────────────────────
def td_headers():
    return {"Content-Type": "application/json", "X-API-Key": TD_API_KEY}

def td_get(path):
    try:
        r = requests.get(f"{TD_API_URL}{path}", headers=td_headers(), timeout=10)
        return r.json() if r.ok else None
    except Exception as e:
        log.error(f"TD GET {path}: {e}")
        return None

def td_post(path, body):
    try:
        r = requests.post(f"{TD_API_URL}{path}", json=body, headers=td_headers(), timeout=10)
        return r.json() if r.ok else None
    except Exception as e:
        log.error(f"TD POST {path}: {e}")
        return None

def td_put(path, body):
    try:
        r = requests.put(f"{TD_API_URL}{path}", json=body, headers=td_headers(), timeout=10)
        return r.json() if r.ok else None
    except Exception as e:
        log.error(f"TD PUT {path}: {e}")
        return None

# ── TICKET HELPERS ────────────────────────────────────
SLA_H = {"Crítica": 4, "Alta": 8, "Media": 24, "Baja": 72}
P_EMOJI = {"Crítica": "🔴", "Alta": "🟠", "Media": "🟡", "Baja": "🟢"}
S_EMOJI = {"Abierto": "🔵", "En progreso": "🟡", "Resuelto": "✅", "Cerrado": "⚫"}

def sla_status(ticket):
    if ticket.get("status") in ("Resuelto", "Cerrado"):
        return "✅ Resuelto"
    sla_h  = SLA_H.get(ticket.get("priority", "Media"), 24)
    try:
        elapsed = (datetime.now() - datetime.fromisoformat(ticket["created"])).total_seconds() / 3600
    except Exception:
        return "—"
    over = elapsed - sla_h
    if over > 0:
        return f"⏰ Vencido {round(over, 1)}h"
    rem = sla_h - elapsed
    return f"⏱ {round(rem, 1)}h restantes"

def fmt_ticket_card(t, short=False):
    """Formatea un ticket como texto para Teams."""
    pe = P_EMOJI.get(t.get("priority",""), "⚪")
    se = S_EMOJI.get(t.get("status",""), "❓")
    if short:
        return (
            f"**{t['id']}** — {t['title'][:60]}{'...' if len(t.get('title',''))>60 else ''}\n"
            f"{pe} {t.get('priority','—')} &nbsp;·&nbsp; {se} {t.get('status','—')} "
            f"&nbsp;·&nbsp; 👤 {t.get('assignee') or '*(Sin asignar)*'}"
        )
    cmts = len(t.get("comments", []))
    return (
        f"**{t['id']}** — {t['title']}\n\n"
        f"| Campo | Valor |\n|---|---|\n"
        f"| Estado | {se} {t.get('status','—')} |\n"
        f"| Prioridad | {pe} {t.get('priority','—')} |\n"
        f"| Categoría | {t.get('category','—')} |\n"
        f"| Asignado | {t.get('assignee') or '*(Sin asignar)*'} |\n"
        f"| SLA | {sla_status(t)} |\n"
        f"| Comentarios | {cmts} |\n"
        f"| Creado | {t.get('created','')[:10]} |\n\n"
        f"**Descripción:**\n{t.get('desc','Sin descripción.')[:300]}"
        f"{'...' if len(t.get('desc',''))>300 else ''}"
    )

def fmt_stats(stats):
    return (
        f"📊 **Estadísticas TicketDesk**\n\n"
        f"| | |\n|---|---|\n"
        f"| Total tickets | {stats.get('total', 0)} |\n"
        f"| 🔵 Abiertos | {stats.get('open', 0)} |\n"
        f"| 🔴 Críticos activos | {stats.get('critical', 0)} |\n"
        f"| ⭐ Satisfacción | {stats.get('satisfaction_avg') or '—'} |\n"
    )

# ── DEMO DATA (modo sin Azure) ────────────────────────
DEMO_TICKETS = [
    {"id":"TKT-0001","title":"Error DUMP ST22 en facturación","priority":"Crítica","status":"Abierto","category":"SAP / ABAP","assignee":"Juan García","desc":"Dump en ZSD_FACTURACION","created":"2026-05-10T08:00:00","comments":[]},
    {"id":"TKT-0002","title":"Servidor BD sin respuesta","priority":"Alta","status":"En progreso","category":"Red / Conectividad","assignee":"María López","desc":"DB-PRD-01 no responde","created":"2026-05-10T10:00:00","comments":[]},
    {"id":"TKT-0003","title":"Parches Windows pendientes","priority":"Media","status":"Abierto","category":"Software","assignee":"","desc":"42 actualizaciones pendientes","created":"2026-05-09T09:00:00","comments":[]},
]

def demo_get_tickets(): return DEMO_TICKETS
def demo_get_ticket(tid): return next((t for t in DEMO_TICKETS if t["id"]==tid), None)

# ── COMMAND PROCESSOR ─────────────────────────────────
def process_command(text, sender_name, sender_id):
    """
    Procesa el comando del usuario y devuelve una respuesta en Markdown.
    """
    text = text.strip()
    # Quitar mención al bot (@TicketDesk)
    text = re.sub(r'<at>.*?</at>', '', text).strip()
    parts = text.split(None, 2)
    cmd   = parts[0].lower() if parts else ""

    # ── /ayuda ─────────────────────────────────────────
    if cmd in ("/ayuda", "/help", "ayuda", "help"):
        return (
            "🤖 **TicketDesk Bot — Comandos disponibles**\n\n"
            "| Comando | Descripción |\n|---|---|\n"
            "| `/nuevo <título>` | Crear ticket nuevo |\n"
            "| `/ver TKT-XXXX` | Ver detalle de un ticket |\n"
            "| `/mis` | Ver mis tickets asignados |\n"
            "| `/pendientes` | Tickets sin asignar |\n"
            "| `/tomar TKT-XXXX` | Tomar un ticket |\n"
            "| `/progreso TKT-XXXX` | Cambiar a En progreso |\n"
            "| `/resolver TKT-XXXX` | Marcar como resuelto |\n"
            "| `/cerrar TKT-XXXX` | Cerrar un ticket |\n"
            "| `/comentar TKT-XXXX <texto>` | Agregar comentario |\n"
            "| `/buscar <texto>` | Buscar tickets |\n"
            "| `/sla` | Tickets con SLA vencido |\n"
            "| `/stats` | Estadísticas del sistema |\n\n"
            f"🔗 Sistema completo: {TD_API_URL}"
        )

    # ── /stats ─────────────────────────────────────────
    if cmd == "/stats":
        if DEMO_MODE:
            return fmt_stats({"total":3,"open":2,"critical":1,"satisfaction_avg":4.5})
        data = td_get("/api/stats")
        return fmt_stats(data) if data else "❌ No se pudo conectar con TicketDesk."

    # ── /mis ───────────────────────────────────────────
    if cmd == "/mis":
        if DEMO_MODE:
            tks = [t for t in demo_get_tickets() if t.get("assignee") == sender_name]
        else:
            data = td_get(f"/api/tickets?assignee={requests.utils.quote(sender_name)}")
            tks  = data.get("tickets", []) if data else []
        if not tks:
            return f"✅ No tienes tickets asignados en este momento, **{sender_name.split()[0]}**."
        lines = [f"📋 **Tus tickets ({len(tks)})**\n"]
        for t in tks[:10]:
            lines.append(fmt_ticket_card(t, short=True))
        return "\n\n".join(lines)

    # ── /pendientes ────────────────────────────────────
    if cmd == "/pendientes":
        if DEMO_MODE:
            tks = [t for t in demo_get_tickets() if not t.get("assignee") and t.get("status")=="Abierto"]
        else:
            data = td_get("/api/tickets?status=Abierto")
            tks  = [t for t in (data.get("tickets",[]) if data else []) if not t.get("assignee")]
        if not tks:
            return "✅ No hay tickets sin asignar."
        lines = [f"📭 **Tickets sin asignar ({len(tks)})**\n"]
        for t in tks[:8]:
            lines.append(fmt_ticket_card(t, short=True))
        return "\n\n".join(lines)

    # ── /sla ───────────────────────────────────────────
    if cmd == "/sla":
        if DEMO_MODE:
            tks = demo_get_tickets()
        else:
            data = td_get("/api/tickets")
            tks  = data.get("tickets", []) if data else []
        vencidos = []
        for t in tks:
            if t.get("status") in ("Resuelto","Cerrado"): continue
            sla_h = SLA_H.get(t.get("priority","Media"), 24)
            try:
                elapsed = (datetime.now()-datetime.fromisoformat(t["created"])).total_seconds()/3600
                if elapsed > sla_h:
                    vencidos.append((t, round(elapsed-sla_h, 1)))
            except Exception:
                pass
        if not vencidos:
            return "✅ Ningún ticket tiene el SLA vencido."
        vencidos.sort(key=lambda x: x[1], reverse=True)
        lines = [f"⏰ **Tickets con SLA vencido ({len(vencidos)})**\n"]
        for t, over in vencidos[:8]:
            pe = P_EMOJI.get(t.get("priority",""),"⚪")
            lines.append(f"**{t['id']}** {pe} — {t['title'][:50]} — **{over}h sobre SLA** — {t.get('assignee') or '*(Sin asignar)*'}")
        return "\n\n".join(lines)

    # ── /ver ───────────────────────────────────────────
    if cmd == "/ver" and len(parts) >= 2:
        tid = parts[1].upper()
        if not re.match(r'^TKT-\d+$', tid):
            return f"❌ ID de ticket inválido. Formato correcto: TKT-0001"
        if DEMO_MODE:
            t = demo_get_ticket(tid)
        else:
            data = td_get(f"/api/tickets/{tid}")
            t = data.get("ticket") if data else None
        if not t:
            return f"❌ No encontré el ticket **{tid}**."
        return fmt_ticket_card(t)

    # ── /buscar ────────────────────────────────────────
    if cmd == "/buscar" and len(parts) >= 2:
        q = parts[1] if len(parts)==2 else parts[1]+" "+parts[2]
        if DEMO_MODE:
            tks = [t for t in demo_get_tickets() if q.lower() in t["title"].lower() or q.lower() in t.get("desc","").lower()]
        else:
            data = td_get(f"/api/tickets/search?q={requests.utils.quote(q)}")
            tks  = data.get("tickets",[]) if data else []
        if not tks:
            return f"🔍 Sin resultados para **\"{q}\"**."
        lines = [f"🔍 **Resultados para \"{q}\" ({len(tks)})**\n"]
        for t in tks[:8]:
            lines.append(fmt_ticket_card(t, short=True))
        return "\n\n".join(lines)

    # ── /tomar ─────────────────────────────────────────
    if cmd == "/tomar" and len(parts) >= 2:
        tid = parts[1].upper()
        if DEMO_MODE:
            t = demo_get_ticket(tid)
            if t: t["assignee"]=sender_name; t["status"]="En progreso"
        else:
            data = td_put(f"/api/tickets/{tid}", {"assignee": sender_name, "status": "En progreso", "changed_by": sender_name})
            t = data.get("ticket") if data else None
        if not t:
            return f"❌ No encontré el ticket **{tid}**."
        return (f"✅ **{tid}** tomado por **{sender_name}**\n\n"
                f"Estado: 🟡 En progreso\n"
                f"Título: {t.get('title','')}\n\n"
                f"💡 Usa `/resolver {tid}` cuando esté listo.")

    # ── /progreso ──────────────────────────────────────
    if cmd == "/progreso" and len(parts) >= 2:
        tid = parts[1].upper()
        if DEMO_MODE:
            t = demo_get_ticket(tid)
            if t: t["status"]="En progreso"
        else:
            data = td_put(f"/api/tickets/{tid}", {"status": "En progreso", "changed_by": sender_name})
            t = data.get("ticket") if data else None
        if not t:
            return f"❌ No encontré el ticket **{tid}**."
        return f"🟡 **{tid}** marcado como **En progreso** por {sender_name}."

    # ── /resolver ──────────────────────────────────────
    if cmd == "/resolver" and len(parts) >= 2:
        tid = parts[1].upper()
        nota = " ".join(parts[2:]) if len(parts) > 2 else ""
        if DEMO_MODE:
            t = demo_get_ticket(tid)
            if t: t["status"]="Resuelto"
        else:
            body = {"status": "Resuelto", "changed_by": sender_name}
            data = td_put(f"/api/tickets/{tid}", body)
            t = data.get("ticket") if data else None
            if t and nota:
                td_post(f"/api/tickets/{tid}/comments", {"author": sender_name, "text": "Resolución: "+nota})
        if not t:
            return f"❌ No encontré el ticket **{tid}**."
        return (f"✅ **{tid}** marcado como **Resuelto** por {sender_name}.\n"
                +(f"\n📝 Nota: {nota}" if nota else "")+
                "\n\n⭐ El usuario recibirá una encuesta de satisfacción.")

    # ── /cerrar ────────────────────────────────────────
    if cmd == "/cerrar" and len(parts) >= 2:
        tid = parts[1].upper()
        if DEMO_MODE:
            t = demo_get_ticket(tid)
            if t: t["status"]="Cerrado"
        else:
            data = td_put(f"/api/tickets/{tid}", {"status": "Cerrado", "changed_by": sender_name})
            t = data.get("ticket") if data else None
        if not t:
            return f"❌ No encontré el ticket **{tid}**."
        return f"⚫ **{tid}** cerrado por {sender_name}."

    # ── /comentar ──────────────────────────────────────
    if cmd == "/comentar" and len(parts) >= 3:
        tid  = parts[1].upper()
        text = parts[2]
        if DEMO_MODE:
            t = demo_get_ticket(tid)
            if t and not t.get("comments"): t["comments"]=[]
            if t: t["comments"].append({"author":sender_name,"text":text,"date":datetime.now().isoformat()})
        else:
            data = td_post(f"/api/tickets/{tid}/comments", {"author": sender_name, "text": text})
            t = demo_get_ticket(tid) if DEMO_MODE else ({"id":tid} if data else None)
        if not t:
            return f"❌ No encontré el ticket **{tid}** o no se pudo agregar el comentario."
        return f"💬 Comentario agregado a **{tid}** por {sender_name}:\n> {text}"

    # ── /nuevo ─────────────────────────────────────────
    if cmd == "/nuevo":
        title = " ".join(parts[1:]).strip() if len(parts) > 1 else ""
        if not title:
            return (
                "Para crear un ticket escribe:\n"
                "`/nuevo <título del problema>`\n\n"
                "Ejemplo: `/nuevo Error al abrir SAP en equipo almacén`"
            )
        body = {
            "title":      title,
            "desc":       f"Ticket creado por {sender_name} desde Microsoft Teams.",
            "category":   "Otro",
            "priority":   "Media",
            "status":     "Abierto",
            "assignee":   "",
            "createdBy":  sender_id,
            "requester":  sender_name,
            "tags":       "teams",
            "created_by": sender_name,
        }
        if DEMO_MODE:
            new_id = f"TKT-{str(len(DEMO_TICKETS)+1).zfill(4)}"
            DEMO_TICKETS.append({**body,"id":new_id,"created":datetime.now().isoformat(),"comments":[]})
            return (f"✅ Ticket **{new_id}** creado por {sender_name}\n\n"
                    f"📋 **{title}**\n"
                    f"🟠 Prioridad: Media &nbsp;·&nbsp; 🔵 Estado: Abierto\n\n"
                    f"El equipo de TI lo atenderá pronto.\n"
                    f"Usa `/ver {new_id}` para seguimiento.")
        data = td_post("/api/tickets", body)
        if not data or not data.get("success"):
            return "❌ No se pudo crear el ticket. Verifica la conexión con TicketDesk."
        t = data.get("ticket", {})
        return (f"✅ Ticket **{t.get('id')}** creado por {sender_name}\n\n"
                f"📋 **{title}**\n"
                f"🟠 Prioridad: Media &nbsp;·&nbsp; 🔵 Estado: Abierto\n\n"
                f"El equipo de TI lo atenderá pronto.\n"
                f"Usa `/ver {t.get('id')}` para seguimiento.")

    # ── Sin comando reconocido ─────────────────────────
    return (
        f"👋 Hola **{sender_name.split()[0]}**. No reconocí ese comando.\n\n"
        "Escribe `/ayuda` para ver todos los comandos disponibles.\n\n"
        "**Comandos rápidos:**\n"
        "• `/nuevo <problema>` — Reportar un problema\n"
        "• `/mis` — Ver mis tickets\n"
        "• `/pendientes` — Tickets sin asignar\n"
        "• `/stats` — Estadísticas"
    )

# ── BOT ENDPOINT ──────────────────────────────────────
def send_reply(service_url, conversation_id, activity_id, reply_to, text, token):
    """Envía una respuesta al canal de Teams."""
    if DEMO_MODE:
        log.info(f"[DEMO] Respuesta: {text[:80]}...")
        return True
    endpoint = f"{service_url}/v3/conversations/{conversation_id}/activities/{activity_id}"
    headers  = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload  = {
        "type":         "message",
        "from":         {"id": MS_APP_ID, "name": "TicketDesk Bot"},
        "conversation": {"id": conversation_id},
        "recipient":    reply_to,
        "replyToId":    activity_id,
        "text":         text,
        "textFormat":   "markdown",
    }
    try:
        r = requests.post(endpoint, json=payload, headers=headers, timeout=10)
        return r.ok
    except Exception as e:
        log.error(f"Error enviando respuesta: {e}")
        return False

@app.route("/api/teams/bot", methods=["POST"])
def bot_webhook():
    """Endpoint principal que recibe mensajes de Teams."""
    try:
        activity = request.get_json(silent=True) or {}
        activity_type = activity.get("type", "")

        if activity_type != "message":
            return jsonify({"status": "ok"}), 200

        text     = activity.get("text", "").strip()
        sender   = activity.get("from", {})
        s_name   = sender.get("name", "Usuario")
        s_id     = sender.get("id", "")
        svc_url  = activity.get("serviceUrl", "")
        conv_id  = activity.get("conversation", {}).get("id", "")
        act_id   = activity.get("id", "")

        log.info(f"Mensaje de {s_name}: {text[:80]}")

        token   = get_ms_token()
        reply   = process_command(text, s_name, s_id)
        send_reply(svc_url, conv_id, act_id, sender, reply, token)

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        log.error(f"Error en bot webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/teams/bot/test", methods=["POST"])
def bot_test():
    """Endpoint de prueba para simular mensajes sin Teams."""
    data = request.get_json(silent=True) or {}
    text   = data.get("text", "/ayuda")
    sender = data.get("sender", "Especialista Demo")
    reply  = process_command(text, sender, "demo-id")
    return jsonify({"success": True, "command": text, "reply": reply})

@app.route("/api/teams/bot/health")
def bot_health():
    return jsonify({
        "status":    "ok",
        "bot":       "TicketDesk Bot — Manufacturas Eliot",
        "demo_mode": DEMO_MODE,
        "api_url":   TD_API_URL,
        "commands":  ["/nuevo","/ver","/mis","/pendientes","/tomar","/progreso","/resolver","/cerrar","/comentar","/buscar","/sla","/stats","/ayuda"],
    })

if __name__ == "__main__":
    log.info("="*60)
    log.info("TicketDesk Bot — Microsoft Teams")
    log.info(f"Puerto       : {BOT_PORT}")
    log.info(f"API URL      : {TD_API_URL}")
    log.info(f"Modo         : {'DEMO (sin Azure)' if DEMO_MODE else 'PRODUCCIÓN'}")
    if DEMO_MODE:
        log.warning("Bot en modo demo. Configura MICROSOFT_APP_ID y MICROSOFT_APP_PASSWORD para producción.")
        log.info(f"Prueba local : POST http://localhost:{BOT_PORT}/api/teams/bot/test")
        log.info(f'Ejemplo      : {{"text": "/ayuda", "sender": "Juan García"}}')
    log.info("="*60)
    app.run(host="0.0.0.0", port=BOT_PORT, debug=False)
