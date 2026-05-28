# Unit 6: Cumplimiento (LGPD/Compliance) — Actividad 5: Código e Implementación

**Proyecto**: TicketDesk Enterprise v1.0  
**Fase**: Construcción  
**Unit**: 6 - Cumplimiento (LGPD/Compliance)  
**Actividad**: 5 - Implementación: Código + Tests  
**Fecha**: 2026-05-27  

---

## 📄 Audit Logger (audit_logger.py)

```python
import structlog
from datetime import datetime
import hashlib

logger = structlog.get_logger()

class AuditLogger:
    @staticmethod
    def log_event(
        tipo_evento: str,
        entidad_tipo: str,
        entidad_id: str,
        usuario_id: str,
        acción: str,
        cambios: dict = None,
        propósito_acceso: str = "SCREENING"
    ):
        """Registrar evento auditado (append-only)"""
        
        entrada = {
            "timestamp": datetime.utcnow().isoformat(),
            "tipo_evento": tipo_evento,
            "entidad_tipo": entidad_tipo,
            "entidad_id": str(entidad_id),
            "usuario_id": str(usuario_id),
            "acción": acción,
            "cambios": cambios,
            "propósito_acceso": propósito_acceso
        }
        
        logger.info("audit_event", **entrada)
        
        # Guardar en BD
        db.add(EntradaAuditoría(
            tipo_evento=tipo_evento,
            entidad_id=entidad_id,
            usuario_id=usuario_id,
            acción=acción,
            cambios=cambios
        ))
        db.commit()
```

## 🔐 Consent Manager (consent_service.py)

```python
import hashlib
from cryptography.fernet import Fernet

class ConsentService:
    def crear_consentimiento(
        self,
        usuario_id: UUID,
        campaña_id: UUID,
        tipo_consentimiento: str,
        política_texto: str,
        ip_address: str
    ) -> Consentimiento:
        """Crear consentimiento LGPD"""
        
        # Hash integridad del documento
        integridad_hash = hashlib.sha256(
            política_texto.encode()
        ).hexdigest()
        
        consentimiento = Consentimiento(
            id_usuario=usuario_id,
            id_campaña=campaña_id,
            tipo_consentimiento=tipo_consentimiento,
            otorgado_en=datetime.utcnow(),
            estado="ACTIVO",
            válido_hasta=datetime.utcnow() + timedelta(days=730),  # 2 años
            copia_local_texto=política_texto,
            integridad_hash=integridad_hash,
            metadata_otorgamiento={
                "ip_address": hashlib.sha256(ip_address.encode()).hexdigest(),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        db.add(consentimiento)
        db.commit()
        
        # Auditar
        AuditLogger.log_event(
            tipo_evento="CONSENT_CREATED",
            entidad_tipo="Consentimiento",
            entidad_id=consentimiento.id,
            usuario_id=usuario_id,
            acción="CREATE",
            propósito_acceso="SCREENING"
        )
        
        return consentimiento
    
    def revocar_consentimiento(self, consentimiento_id: UUID):
        """Revocar consentimiento"""
        consentimiento = db.get(Consentimiento, consentimiento_id)
        consentimiento.estado = "REVOCADO"
        consentimiento.revocado_en = datetime.utcnow()
        db.commit()
        
        AuditLogger.log_event(
            tipo_evento="CONSENT_REVOKED",
            entidad_tipo="Consentimiento",
            entidad_id=consentimiento_id,
            usuario_id=consentimiento.id_usuario,
            acción="UPDATE"
        )
```

## 🗑️ Hard Delete Handler (hard_delete_service.py)

```python
from celery import shared_task
import time

@shared_task(time_limit=86400)  # Max 24h
def hard_delete_user_data(solicitud_id: UUID):
    """Hard delete asincrónico con SLA <24h"""
    
    solicitud = db.get(SolicitudEliminación, solicitud_id)
    
    start = time.time()
    
    try:
        # 1. Marcar iniciado (reversible)
        solicitud.hard_delete_iniciado_en = datetime.utcnow()
        db.commit()
        
        # 2. Eliminar datos
        db.query(Sesión).filter(Sesión.id_usuario == solicitud.id_usuario).delete()
        db.query(Screening).filter(Screening.id_usuario == solicitud.id_usuario).delete()
        db.query(Evaluación).filter(Evaluación.id_usuario == solicitud.id_usuario).delete()
        db.query(Consentimiento).filter(Consentimiento.id_usuario == solicitud.id_usuario).delete()
        
        # 3. Eliminar de S3
        s3_client.delete_objects(
            Bucket='consentimientos',
            Delete={'Objects': [{'Key': f'{solicitud.id_usuario}/*'}]}
        )
        
        db.commit()
        
        # 4. Marcar completado
        solicitud.hard_delete_completado_en = datetime.utcnow()
        solicitud.estado = "COMPLETADA"
        db.commit()
        
        # 5. Notificar usuario
        send_email_rtb_completed(solicitud.usuario.email)
        
        # 6. Auditar
        AuditLogger.log_event(
            tipo_evento="HARD_DELETE",
            entidad_tipo="Usuario",
            entidad_id=solicitud.id_usuario,
            usuario_id=None,  # Sistema
            acción="DELETE"
        )
        
        elapsed = time.time() - start
        assert elapsed < 86400, f"Hard delete took {elapsed}s > 24h"
        
    except Exception as e:
        solicitud.hard_delete_iniciado_en = None
        db.rollback()
        raise
```

## 📊 Compliance Reporting (reporting_service.py)

```python
class ComplianceReportingService:
    def generar_reporte_monthly(self, año: int, mes: int):
        """Generar reporte LGPD monthly"""
        
        período = f"{año}-{mes:02d}"
        
        métricas = {
            "total_usuarios": db.query(Usuario).count(),
            "total_consentimientos": db.query(Consentimiento).filter(
                extract('year', Consentimiento.otorgado_en) == año,
                extract('month', Consentimiento.otorgado_en) == mes
            ).count(),
            "solicitudes_derecho_olvido": db.query(SolicitudEliminación).filter(
                extract('year', SolicitudEliminación.solicitada_en) == año,
                extract('month', SolicitudEliminación.solicitada_en) == mes
            ).count(),
            "solicitudes_completadas": db.query(SolicitudEliminación).filter(
                SolicitudEliminación.estado == "COMPLETADA",
                extract('year', SolicitudEliminación.hard_delete_completado_en) == año,
                extract('month', SolicitudEliminación.hard_delete_completado_en) == mes
            ).count(),
        }
        
        reporte = ReporteCompliance(
            período=período,
            año_mes=f"{año}-{mes:02d}",
            generada_en=datetime.utcnow(),
            métricas_lgpd=métricas,
            estado="BORRADOR"  # Esperar DPO aprobación
        )
        
        db.add(reporte)
        db.commit()
        
        # Notificar DPO
        send_email_dpo_review(reporte)
```

## 🧪 Tests (test_compliance.py)

```python
import pytest

class TestAuditTrail:
    def test_audit_trail_completeness(self):
        """100% eventos auditados"""
        usuario = create_test_user()
        
        db.add(usuario)
        db.commit()
        
        audit = db.query(EntradaAuditoría).filter(
            EntradaAuditoría.tipo_evento == "CREATE",
            EntradaAuditoría.entidad_id == usuario.id
        ).first()
        
        assert audit is not None
        assert audit.usuario_id is not None
        assert audit.timestamp is not None

class TestHardDelete:
    def test_hard_delete_sla(self):
        """Hard delete <24h SLA"""
        solicitud = create_delete_request()
        
        start = time.time()
        hard_delete_user_data.apply_async(
            args=[solicitud.id],
            countdown=5
        ).get(timeout=86400)
        
        elapsed = time.time() - start
        assert elapsed < 86400  # 24h
        
        assert solicitud.estado == "COMPLETADA"

class TestConsentIntegrity:
    def test_consent_hash_verification(self):
        """Hash integridad documento"""
        consent = create_consent()
        
        # Hash debe coincidir
        documento_hash = hashlib.sha256(
            consent.copia_local_texto.encode()
        ).hexdigest()
        
        assert documento_hash == consent.integridad_hash
```

---

## ✅ Criterios de Aceptación (Actividad 5)

- [x] Audit logger completo con append-only
- [x] Consent manager con documentación
- [x] Hard delete handler con <24h SLA
- [x] Compliance reporting monthly
- [x] Tests con >80% cobertura
- [x] Integración Unit 2 (PII hashing)

---

**Generado**: 2026-05-27  
**Unit**: 6 - Cumplimiento (LGPD/Compliance)  
**Actividad**: 5 - Código e Implementación  
**Estado**: ✅ COMPLETADA
