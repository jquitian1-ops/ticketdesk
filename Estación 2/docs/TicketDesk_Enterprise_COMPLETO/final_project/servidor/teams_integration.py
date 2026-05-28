"""
TicketDesk — Integración con Microsoft Teams
=============================================
Envía notificaciones automáticas a canales de Teams cuando:
  - Se crea un ticket nuevo
  - Se asigna o reasigna un ticket
  - Un ticket cambia de estado
  - Un ticket de prioridad Crítica lleva más de 1 hora sin atender
  - Un servidor cae (integración con connectivity_monitor.py)

Requisitos:
    pip install requests

Configuración en Teams:
  1. Abre el canal de Teams donde quieres recibir alertas
  2. Haz clic en "..." → "Conectores"
  3. Busca "Incoming Webhook" → Configurar
  4. Dale un nombre (ej. "TicketDesk") y copia la URL del webhook
  5. Pega la URL en TEAMS_CONFIG abajo

Uso:
    from teams_integration import TeamsNotifier
    notifier = TeamsNotifier()
    notifier.ticket_creado(ticket)
"""

import requests
import json
import logging
from datetime import datetime
from typing import Optional

log = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# CONFIG — Configura tus webhooks de Teams aquí
# ─────────────────────────────────────────────
TEAMS_CONFIG = {
    # Webhook principal — recibe todas las notificaciones
    "webhook_general": "https://empresa.webhook.office.com/webhookb2/TU-WEBHOOK-GENERAL",

    # Webhook para tickets críticos (puede ser el mismo o uno diferente)
    "webhook_criticos": "https://empresa.webhook.office.com/webhookb2/TU-WEBHOOK-CRITICOS",

    # Webhook para alertas de conectividad
    "webhook_conectividad": "https://empresa.webhook.office.com/webhookb2/TU-WEBHOOK-CONECTIVIDAD",

    # URL base del sistema de tickets (para los botones "Ver ticket")
    "ticketdesk_url": "http://localhost:5050",

    # Notificar siempre, solo críticos, o desactivado
    "notify_on": ["Crítica", "Alta", "Media", "Baja"],  # Quita prioridades para no notificar

    # Notificar cuando cambia estado
    "notify_status_change": True,

    # Timeout de conexión
    "timeout_seconds": 10,
}

PRIORITY_COLORS = {
    "Crítica": "FF3D3D",
    "Alta":    "D4500A",
    "Media":   "B58500",
    "Baja":    "1A7A4A",
}

PRIORITY_ICONS = {
    "Crítica": "🔴",
    "Alta":    "🟠",
    "Media":   "🟡",
    "Baja":    "🟢",
}

STATUS_ICONS = {
    "Abierto":      "🔵",
    "En progreso":  "🟡",
    "Resuelto":     "✅",
    "Cerrado":      "⚫",
}


class TeamsNotifier:
    """Cliente de notificaciones para Microsoft Teams via Incoming Webhooks."""

    def __init__(self, config: dict = None):
        self.cfg = config or TEAMS_CONFIG

    def _send(self, webhook_url: str, payload: dict) -> bool:
        """Envía un payload JSON al webhook de Teams."""
        if not webhook_url or "TU-WEBHOOK" in webhook_url:
            log.warning("Webhook de Teams no configurado. Omitiendo notificación.")
            return False
        try:
            resp = requests.post(
                webhook_url,
                json=payload,
                timeout=self.cfg.get("timeout_seconds", 10),
                headers={"Content-Type": "application/json"},
            )
            if resp.status_code == 200:
                log.info(f"Notificación enviada a Teams: {resp.status_code}")
                return True
            else:
                log.warning(f"Teams respondió {resp.status_code}: {resp.text[:100]}")
                return False
        except requests.exceptions.ConnectionError:
            log.error("No se pudo conectar al webhook de Teams. Verifica la URL.")
            return False
        except Exception as e:
            log.error(f"Error enviando a Teams: {e}")
            return False

    def _ticket_url(self, ticket_id: str) -> str:
        return f"{self.cfg['ticketdesk_url']}/?ticket={ticket_id}"

    # ──────────────────────────────
    # TICKET CREADO
    # ──────────────────────────────
    def ticket_creado(self, ticket: dict, asignado_por_ia: bool = False) -> bool:
        """Notifica cuando se crea un ticket nuevo."""
        if ticket.get("priority") not in self.cfg.get("notify_on", []):
            return False

        color    = PRIORITY_COLORS.get(ticket.get("priority", ""), "888888")
        icon     = PRIORITY_ICONS.get(ticket.get("priority", ""), "⚪")
        ia_badge = " _(asignado por IA)_" if asignado_por_ia else ""

        payload = {
            "@type":      "MessageCard",
            "@context":   "http://schema.org/extensions",
            "themeColor": color,
            "summary":    f"Nuevo ticket: {ticket.get('id')} — {ticket.get('title')}",
            "sections": [{
                "activityTitle":    f"{icon} **Nuevo ticket {ticket.get('id')}**",
                "activitySubtitle": f"Prioridad **{ticket.get('priority')}** · {ticket.get('category')}",
                "activityImage":    "https://adaptivecards.io/content/cats/1.png",
                "facts": [
                    {"name": "Título",     "value": ticket.get("title", "")},
                    {"name": "Asignado a", "value": f"{ticket.get('assignee', '—')}{ia_badge}"},
                    {"name": "SLA",        "value": self._sla_text(ticket.get("priority"))},
                    {"name": "Categoría",  "value": ticket.get("category", "—")},
                    {"name": "Descripción","value": (ticket.get("desc") or "Sin descripción")[:200]},
                ],
                "markdown": True,
            }],
            "potentialAction": [
                {
                    "@type": "OpenUri",
                    "name":  "Ver ticket completo",
                    "targets": [{"os": "default", "uri": self._ticket_url(ticket.get("id", ""))}],
                },
                {
                    "@type": "OpenUri",
                    "name":  "Abrir TicketDesk",
                    "targets": [{"os": "default", "uri": self.cfg["ticketdesk_url"]}],
                },
            ],
        }

        # Críticos van al canal dedicado también
        webhook = self.cfg["webhook_criticos"] if ticket.get("priority") == "Crítica" else self.cfg["webhook_general"]
        return self._send(webhook, payload)

    # ──────────────────────────────
    # CAMBIO DE ESTADO
    # ──────────────────────────────
    def ticket_estado_cambiado(self, ticket: dict, estado_anterior: str, cambiado_por: str) -> bool:
        """Notifica cuando cambia el estado de un ticket."""
        if not self.cfg.get("notify_status_change", True):
            return False
        if ticket.get("priority") not in self.cfg.get("notify_on", []):
            return False

        color   = PRIORITY_COLORS.get(ticket.get("priority", ""), "888888")
        icon    = STATUS_ICONS.get(ticket.get("status", ""), "🔵")
        icon_pr = PRIORITY_ICONS.get(ticket.get("priority", ""), "⚪")

        payload = {
            "@type":      "MessageCard",
            "@context":   "http://schema.org/extensions",
            "themeColor": color,
            "summary":    f"Ticket {ticket.get('id')} cambió a {ticket.get('status')}",
            "sections": [{
                "activityTitle":    f"{icon} **Cambio de estado — {ticket.get('id')}**",
                "activitySubtitle": f"{ticket.get('title')}",
                "facts": [
                    {"name": "Estado anterior", "value": f"{STATUS_ICONS.get(estado_anterior,'')} {estado_anterior}"},
                    {"name": "Nuevo estado",    "value": f"{icon} **{ticket.get('status')}**"},
                    {"name": "Cambiado por",    "value": cambiado_por},
                    {"name": "Prioridad",       "value": f"{icon_pr} {ticket.get('priority')}"},
                    {"name": "Asignado a",      "value": ticket.get("assignee", "—")},
                ],
                "markdown": True,
            }],
            "potentialAction": [{
                "@type": "OpenUri",
                "name":  "Ver ticket",
                "targets": [{"os": "default", "uri": self._ticket_url(ticket.get("id", ""))}],
            }],
        }

        # Si se resuelve, incluir link a encuesta
        if ticket.get("status") in ("Resuelto", "Cerrado"):
            payload["sections"][0]["facts"].append({
                "name": "Encuesta", "value": "⭐ Recuerda completar la encuesta de satisfacción"
            })

        return self._send(self.cfg["webhook_general"], payload)

    # ──────────────────────────────
    # REASIGNACIÓN
    # ──────────────────────────────
    def ticket_reasignado(self, ticket: dict, asignado_anterior: str, asignado_nuevo: str, motivo: str = "") -> bool:
        """Notifica cuando un ticket es reasignado."""
        payload = {
            "@type":      "MessageCard",
            "@context":   "http://schema.org/extensions",
            "themeColor": "8B5CF6",
            "summary":    f"Ticket {ticket.get('id')} reasignado a {asignado_nuevo}",
            "sections": [{
                "activityTitle":    f"🔄 **Ticket reasignado — {ticket.get('id')}**",
                "activitySubtitle": ticket.get("title", ""),
                "facts": [
                    {"name": "Antes",     "value": asignado_anterior},
                    {"name": "Ahora",     "value": f"**{asignado_nuevo}**"},
                    {"name": "Prioridad", "value": f"{PRIORITY_ICONS.get(ticket.get('priority',''),'⚪')} {ticket.get('priority')}"},
                    {"name": "Motivo",    "value": motivo or "Sin especificar"},
                ],
                "markdown": True,
            }],
            "potentialAction": [{
                "@type": "OpenUri",
                "name":  "Ver ticket",
                "targets": [{"os": "default", "uri": self._ticket_url(ticket.get("id", ""))}],
            }],
        }
        return self._send(self.cfg["webhook_general"], payload)

    # ──────────────────────────────
    # ALERTA SLA VENCIDO
    # ──────────────────────────────
    def alerta_sla_vencido(self, ticket: dict, horas_vencido: float) -> bool:
        """Notifica cuando un ticket supera su SLA."""
        payload = {
            "@type":      "MessageCard",
            "@context":   "http://schema.org/extensions",
            "themeColor": "FF0000",
            "summary":    f"SLA VENCIDO — {ticket.get('id')}",
            "sections": [{
                "activityTitle":    f"⏰ **SLA VENCIDO — {ticket.get('id')}**",
                "activitySubtitle": f"{ticket.get('title')}",
                "facts": [
                    {"name": "Asignado a",    "value": ticket.get("assignee", "—")},
                    {"name": "Prioridad",     "value": f"{PRIORITY_ICONS.get(ticket.get('priority',''),'⚪')} {ticket.get('priority')}"},
                    {"name": "Horas vencido", "value": f"**{round(horas_vencido, 1)}h** fuera de SLA"},
                    {"name": "Estado actual", "value": ticket.get("status", "—")},
                ],
                "markdown": True,
            }],
            "potentialAction": [
                {
                    "@type": "OpenUri",
                    "name":  "⚡ Atender ahora",
                    "targets": [{"os": "default", "uri": self._ticket_url(ticket.get("id", ""))}],
                },
            ],
        }
        return self._send(self.cfg["webhook_criticos"], payload)

    # ──────────────────────────────
    # ALERTA DE CONECTIVIDAD
    # ──────────────────────────────
    def alerta_servidor_caido(self, servidor: dict, ticket_id: str) -> bool:
        """Notifica cuando el monitor detecta un servidor caído."""
        payload = {
            "@type":      "MessageCard",
            "@context":   "http://schema.org/extensions",
            "themeColor": "FF0000",
            "summary":    f"ALERTA: {servidor.get('name')} sin conectividad",
            "sections": [{
                "activityTitle":    f"🔴 **Servidor caído: {servidor.get('name')}**",
                "activitySubtitle": f"IP: `{servidor.get('host')}` · Ticket automático creado",
                "facts": [
                    {"name": "Servidor",         "value": servidor.get("name", "")},
                    {"name": "Host / IP",         "value": servidor.get("host", "")},
                    {"name": "Detectado a las",   "value": datetime.now().strftime("%H:%M:%S")},
                    {"name": "Ticket generado",   "value": f"**{ticket_id}** — Prioridad Crítica"},
                ],
                "markdown": True,
            }],
            "potentialAction": [{
                "@type": "OpenUri",
                "name":  "Ver ticket de conectividad",
                "targets": [{"os": "default", "uri": self._ticket_url(ticket_id)}],
            }],
        }
        return self._send(self.cfg["webhook_conectividad"], payload)

    # ──────────────────────────────
    # REPORTE DIARIO
    # ──────────────────────────────
    def reporte_diario(self, stats: dict) -> bool:
        """Envía el reporte diario de tickets al canal de Teams."""
        total  = stats.get("total", 0)
        open_  = stats.get("open", 0)
        crit   = stats.get("critical", 0)
        res    = stats.get("resolved_today", 0)
        sla_ok = stats.get("sla_compliance_pct", 0)

        payload = {
            "@type":      "MessageCard",
            "@context":   "http://schema.org/extensions",
            "themeColor": "1A5FA8",
            "summary":    f"Reporte diario TicketDesk — {datetime.now().strftime('%d/%m/%Y')}",
            "sections": [{
                "activityTitle":    f"📊 **Reporte diario — {datetime.now().strftime('%d/%m/%Y')}**",
                "activitySubtitle": "Resumen de operaciones del día",
                "facts": [
                    {"name": "Total tickets",         "value": str(total)},
                    {"name": "Abiertos",              "value": f"🟡 {open_}"},
                    {"name": "Críticos sin resolver", "value": f"🔴 {crit}"},
                    {"name": "Resueltos hoy",         "value": f"✅ {res}"},
                    {"name": "Cumplimiento SLA",      "value": f"{'✅' if sla_ok >= 80 else '⚠️'} {sla_ok}%"},
                ],
                "markdown": True,
            }],
            "potentialAction": [{
                "@type": "OpenUri",
                "name":  "Ver dashboard completo",
                "targets": [{"os": "default", "uri": self.cfg["ticketdesk_url"]}],
            }],
        }
        return self._send(self.cfg["webhook_general"], payload)

    def _sla_text(self, priority: str) -> str:
        sla_map = {"Crítica": "4 horas", "Alta": "8 horas", "Media": "24 horas", "Baja": "72 horas"}
        return sla_map.get(priority, "—")


# ──────────────────────────────
# MONITOR DE SLA (ejecutar en background)
# ──────────────────────────────
def monitor_sla(tickets: list, notifier: TeamsNotifier, already_notified: set) -> set:
    """
    Revisa todos los tickets abiertos y alerta si vencieron su SLA.
    Devuelve el set actualizado de tickets ya notificados.
    """
    SLA_HOURS = {"Crítica": 4, "Alta": 8, "Media": 24, "Baja": 72}
    for t in tickets:
        if t.get("status") in ("Resuelto", "Cerrado"):
            continue
        limit = SLA_HOURS.get(t.get("priority", ""), 24)
        elapsed = (datetime.now() - datetime.fromisoformat(t["created"])).total_seconds() / 3600
        if elapsed > limit and t["id"] not in already_notified:
            notifier.alerta_sla_vencido(t, elapsed - limit)
            already_notified.add(t["id"])
            log.warning(f"SLA vencido notificado: {t['id']} — {round(elapsed - limit, 1)}h fuera")
    return already_notified


# ──────────────────────────────
# EJEMPLO DE USO
# ──────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    notifier = TeamsNotifier()

    # Ejemplo: notificar ticket nuevo
    ticket_ejemplo = {
        "id":       "TKT-0007",
        "title":    "Error DUMP ST22 en módulo SD",
        "priority": "Crítica",
        "category": "SAP / ABAP",
        "assignee": "Juan García",
        "desc":     "Dump RAISE_EXCEPTION en ZSD_FACTURACION. Afecta producción.",
        "created":  datetime.now().isoformat(),
        "status":   "Abierto",
    }

    print("Enviando notificación de ticket nuevo a Teams...")
    ok = notifier.ticket_creado(ticket_ejemplo, asignado_por_ia=True)
    print("Enviado correctamente." if ok else "Error — verifica la URL del webhook.")

    # Ejemplo: reporte diario
    stats_ejemplo = {
        "total": 6, "open": 3, "critical": 2,
        "resolved_today": 1, "sla_compliance_pct": 83
    }
    print("\nEnviando reporte diario...")
    notifier.reporte_diario(stats_ejemplo)
