# Unit 6: Cumplimiento (LGPD/Compliance) — Actividad 3: Decisiones de Arquitectura (ADR)

**Proyecto**: TicketDesk Enterprise v1.0  
**Fase**: Construcción  
**Unit**: 6 - Cumplimiento (LGPD/Compliance)  
**Actividad**: 3 - Diseño NFR: Architecture Decision Records (ADR)  
**Fecha**: 2026-05-27  

---

## 🎯 ADR-UNIT6-001: Encriptación Datos en Reposo (AES-256 con KMS vs Customer-Managed Keys vs TDE)

**Título**: Elegir estrategia encriptación datos sensibles almacenados

**Estado**: ✅ ACEPTADA

### Contexto

Datos sensibles (consentimientos, evaluaciones, audit logs) deben encriptarse:
- Compliance LGPD requerido
- Claves gestionadas de forma segura
- Performance impact mínimo
- Auditoría acceso a claves

### Opciones

**Opción 1: AWS KMS (Key Management Service)** ✅ ELEGIDA
- ✅ Claves gestionadas por AWS (compliance)
- ✅ Auditoría automática CloudTrail
- ✅ Rotation automática yearly
- ✅ Bajo costo (~$1/mes + API calls)

**Opción 2: Customer-Managed Keys**
- ✅ Control total de claves
- ❌ Responsabilidad operator (rotation, backup)
- ❌ Mayor complejidad
- ❌ Riesgo pérdida claves

**Opción 3: TDE (Transparent Data Encryption)**
- ✅ Built-in PostgreSQL
- ❌ Menos granular (tabla, no registro)
- ❌ Sin auditoría externa

### Decisión

**✅ AWS KMS (server-side encryption) para documentos S3 + PII en PostgreSQL**

### Consecuencias

```python
# S3 encryption with KMS
import boto3

s3_client = boto3.client('s3')

def guardar_consentimiento_s3(consent_id: UUID, documento: str):
    """Guardar consentimiento encriptado en S3"""
    s3_client.put_object(
        Bucket='consentimientos-TicketDesk',
        Key=f'{consent_id}/documento.json',
        Body=json.dumps({'consentimiento': documento}),
        ServerSideEncryption='aws:kms',
        SSEKMSKeyId=os.getenv('KMS_KEY_ARN'),
        Metadata={'consent_id': str(consent_id)}
    )

# PostgreSQL PII encryption (aplicación)
from cryptography.fernet import Fernet

class EncryptionService:
    def __init__(self):
        kms_client = boto3.client('kms')
        response = kms_client.generate_data_key(
            KeyId=os.getenv('KMS_KEY_ARN'),
            KeySpec='AES_256'
        )
        self.cipher = Fernet(base64.b64encode(response['Plaintext'][:32]))
    
    def encrypt_pii(self, pii_value: str) -> str:
        """Encriptar PII antes guardar en BD"""
        encrypted = self.cipher.encrypt(pii_value.encode())
        return base64.b64encode(encrypted).decode()
    
    def decrypt_pii(self, encrypted_value: str) -> str:
        """Desencriptar PII desde BD"""
        encrypted = base64.b64decode(encrypted_value.encode())
        return self.cipher.decrypt(encrypted).decode()

# Uso en modelo
class Usuario(Base):
    email_encrypted = Column(String, nullable=False)
    phone_encrypted = Column(String, nullable=False)
    
    def set_email(self, email: str):
        self.email_encrypted = EncryptionService().encrypt_pii(email)
    
    def get_email(self) -> str:
        return EncryptionService().decrypt_pii(self.email_encrypted)
```

---

## 🎯 ADR-UNIT6-002: Auditoría Logging (Structured Logs en CloudWatch vs ELK vs Splunk)

**Título**: Elegir sistema auditoría centralizado para compliance

**Estado**: ✅ ACEPTADA

### Contexto

Necesita auditar 100% eventos:
- Búsqueda rápida <2s
- Retención 7 años
- Compliance LGPD
- Bajo costo

### Opciones

**Opción 1: CloudWatch Logs + CloudWatch Insights** ✅ ELEGIDA
- ✅ Integrado AWS (sin overhead)
- ✅ Búsqueda <2s (CloudWatch Insights)
- ✅ Retención configurable
- ✅ Bajo costo (~$0.50/GB)

**Opción 2: ELK (Elasticsearch, Logstash, Kibana)**
- ✅ Open source, control total
- ❌ Infraestructura compleja (3+ nodos)
- ❌ Costo ~$500/mes mínimo

**Opción 3: Splunk**
- ✅ Powerful search, compliance features
- ❌ Costo muy alto (~$2000+/mes)

### Decisión

**✅ CloudWatch Logs (structured JSON) + CloudWatch Insights + Athena (reporting)**

### Consecuencias

```python
# Structured logging con structlog
import structlog
import json

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

@app.post("/api/consent")
async def create_consent(user_id: UUID, consent_data: ConsentSchema):
    logger.info(
        "consent_created",
        user_id=str(user_id),
        consent_type=consent_data.type,
        granted_at=datetime.utcnow().isoformat(),
        ip_address_hash=hashlib.sha256(request.client.host.encode()).hexdigest(),
        user_agent_hash=hashlib.sha256(request.headers['user-agent'].encode()).hexdigest(),
        purpose="SCREENING"
    )

# CloudWatch Insights query
# fields @timestamp, @message, user_id, consent_type
# | filter event_type = "consent_created"
# | stats count() by consent_type
# | sort count desc
```

---

## 🎯 ADR-UNIT6-003: Flujo Consentimiento Dinámico (Checkbox vs Modal vs Two-Step)

**Título**: Elegir UX consentimiento LGPD para candidatos

**Estado**: ✅ ACEPTADA

### Contexto

Consentimiento debe ser:
- Explícito (no pre-checked)
- Informado (usuario entiende qué consiente)
- Documentado (prueba de consentimiento)

### Opciones

**Opción 1: Modal dialog + checkbox + sign** ✅ ELEGIDA
- ✅ Explícito (usuario debe hacer click)
- ✅ Documentado (screenshot + hash)
- ✅ Informado (full policy visible)

**Opción 2: Checkbox solo**
- ❌ No documenta términos vistos
- ❌ Menos evidencia legal

**Opción 3: Two-Step (read + confirm)**
- ✅ Muy riguroso (usuario lee antes confirmar)
- ❌ Mayor friction (UX negativa)

### Decisión

**✅ Modal dialog con scroll-to-bottom + checkbox + screenshot/hash documentación**

---

## 🎯 ADR-UNIT6-004: Solicitud Derecho Olvido (Sincrónico vs Asincrónico + SLA)

**Título**: Elegir ejecución hard delete para solicitudes RTB

**Estado**: ✅ ACEPTADA

### Contexto

Derecho olvido requiere <24h. Opciones:
- Sincrónico (bloquear hasta completar)
- Asincrónico (Celery task)

### Opciones

**Opción 1: Asincrónico (Celery)** ✅ ELEGIDA
- ✅ No bloquea API (<1s respuesta)
- ✅ Reversible hasta ejecutar
- ✅ Retries automáticos si falla
- ✅ Tracking status de job

**Opción 2: Sincrónico**
- ❌ Bloquea API (~5-10 min)
- ❌ Risk timeout/network failure
- ❌ No reversible

### Decisión

**✅ Celery async task + Flower monitoring + <24h SLA**

---

## 📊 Matriz ADRs

| ADR | Decisión | Alternativa | Razón |
|---|---|---|---|
| ADR-UNIT6-001 | AWS KMS | Customer Keys | Compliance, auditoría automática |
| ADR-UNIT6-002 | CloudWatch Logs | ELK | Bajo costo, búsqueda <2s |
| ADR-UNIT6-003 | Modal + Checkbox | Plain checkbox | Documentación explícita |
| ADR-UNIT6-004 | Celery async | Sincrónico | No bloquea API, reversible <24h |

---

## ✅ Criterios de Aceptación (Actividad 3)

- [x] 4 ADRs documentados (formato CODC)
- [x] Opciones evaluadas objetivamente
- [x] Decisiones con consecuencias documentadas
- [x] Compliance LGPD embebido
- [x] Integración observabilidad

---

**Generado**: 2026-05-27  
**Unit**: 6 - Cumplimiento (LGPD/Compliance)  
**Actividad**: 3 - Decisiones Arquitectura  
**Estado**: ✅ COMPLETADA
