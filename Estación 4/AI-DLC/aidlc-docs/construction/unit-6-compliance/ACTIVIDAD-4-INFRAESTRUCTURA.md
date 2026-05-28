# Unit 6: Cumplimiento (LGPD/Compliance) — Actividad 4: Infraestructura

**Proyecto**: TicketDesk Enterprise v1.0  
**Fase**: Construcción  
**Unit**: 6 - Cumplimiento (LGPD/Compliance)  
**Actividad**: 4 - Infraestructura: Componentes, Flujos, Despliegue  
**Fecha**: 2026-05-27  

---

## 🏗️ C4 Level 3: Compliance Pipeline

```
┌─ Compliance Engine ────────────────────────────────────┐
│                                                         │
│  ┌──────────────────────────────────────────────────┐ │
│  │    Audit Logger (todas operaciones)             │ │
│  │  • EntradaAuditoría append-only                  │ │
│  │  • Structured JSON logging CloudWatch           │ │
│  │  • PII hashing (nunca plain text)                │ │
│  └──────────────────────────────────────────────────┘ │
│         │                                              │
│         ▼                                              │
│  ┌──────────────────────────────────────────────────┐ │
│  │    Consent Manager                              │ │
│  │  • Crear consentimiento (LGPD compliance)        │ │
│  │  • Documentar con hash integridad                │ │
│  │  • Revocar (auditable)                           │ │
│  │  • Validar antes operaciones                     │ │
│  └──────────────────────────────────────────────────┘ │
│         │                                              │
│         ▼                                              │
│  ┌──────────────────────────────────────────────────┐ │
│  │    Right To Be Forgotten Handler                │ │
│  │  • Procesar solicitudes derecho olvido           │ │
│  │  • Hard delete asincrónico (Celery)              │ │
│  │  • <24h SLA con tracking                         │ │
│  │  • Notificación usuario post-completada          │ │
│  └──────────────────────────────────────────────────┘ │
│         │                                              │
│         ▼                                              │
│  ┌──────────────────────────────────────────────────┐ │
│  │    Compliance Reporting                         │ │
│  │  • Generación monthly ReporteCompliance          │ │
│  │  • Métricas LGPD agregadas                       │ │
│  │  • Violations detected + alertas                 │ │
│  │  • Export PDF DPO approval                       │ │
│  └──────────────────────────────────────────────────┘ │
│                                                         │
└──────────────────────────────────────────────────────┘
        │                    │                    │
        ▼                    ▼                    ▼
   ┌─────────┐       ┌──────────────┐      ┌──────────┐
   │PostgreSQL       │CloudWatch    │      │S3 Bucket │
   │(AuditLogs,      │Logs (JSON    │      │(Consent- │
   │Consentimiento)  │structured)   │      │imientos) │
   └─────────┘       └──────────────┘      └──────────┘
```

## 🗄️ Base de Datos (PostgreSQL)

```sql
CREATE TABLE EntradaAuditoría (
    id UUID PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    tipo_evento VARCHAR(50) NOT NULL,
    entidad_tipo VARCHAR(50) NOT NULL,
    entidad_id UUID NOT NULL,
    usuario_id UUID NOT NULL,
    dirección_ip_hash VARCHAR(64) NOT NULL,
    acción VARCHAR(20) NOT NULL,
    cambios JSONB,
    resultado VARCHAR(20) NOT NULL,
    estado VARCHAR(20) DEFAULT 'ACTIVA',
    
    INDEX idx_timestamp ON EntradaAuditoría(timestamp),
    INDEX idx_usuario ON EntradaAuditoría(usuario_id),
    INDEX idx_tipo ON EntradaAuditoría(tipo_evento)
);

CREATE TABLE Consentimiento (
    id UUID PRIMARY KEY,
    id_usuario UUID NOT NULL REFERENCES Usuario(id),
    id_campaña UUID NOT NULL REFERENCES Campaña(id),
    tipo_consentimiento VARCHAR(50) NOT NULL,
    otorgado_en TIMESTAMP NOT NULL,
    estado VARCHAR(20) DEFAULT 'ACTIVO',
    revocado_en TIMESTAMP,
    válido_hasta TIMESTAMP NOT NULL,
    copia_local_texto TEXT NOT NULL,
    integridad_hash VARCHAR(64) NOT NULL,
    url_s3_documento VARCHAR(512),
    
    UNIQUE(id_usuario, tipo_consentimiento, id_campaña)
);

CREATE TABLE SolicitudEliminación (
    id UUID PRIMARY KEY,
    id_usuario UUID NOT NULL REFERENCES Usuario(id),
    id_campaña UUID,
    solicitada_en TIMESTAMP NOT NULL,
    estado VARCHAR(20) DEFAULT 'PENDIENTE',
    aprobada_en TIMESTAMP,
    hard_delete_completado_en TIMESTAMP,
    tarea_celery_id VARCHAR(255),
    
    INDEX idx_usuario ON SolicitudEliminación(id_usuario),
    INDEX idx_estado ON SolicitudEliminación(estado)
);
```

## ☁️ Despliegue Terraform

```hcl
# CloudWatch Logs grupo
resource "aws_cloudwatch_log_group" "compliance" {
  name              = "/aws/compliance/ticketdesk"
  retention_in_days = 2555  # 7 años
}

# KMS key para encriptación
resource "aws_kms_key" "compliance" {
  description             = "KMS key para encriptación compliance"
  deletion_window_in_days = 30
  enable_key_rotation     = true
}

# Celery workers para hard delete
resource "aws_ecs_task_definition" "rtb_worker" {
  family      = "rtb-worker"
  cpu         = "512"
  memory      = "1024"
  
  container_definitions = jsonencode([{
    name      = "celery-worker"
    image     = "celery-rtb:latest"
    
    environment = [
      { name = "CELERY_BROKER_URL", value = var.redis_url },
      { name = "DATABASE_URL", value = var.postgres_url }
    ]
  }])
}
```

## ✅ Criterios de Aceptación (Actividad 4)

- [x] C4 Level 3 compliance pipeline
- [x] Esquema BD append-only para auditoría
- [x] Terraform para CloudWatch + KMS
- [x] Celery workers para hard delete async

---

**Generado**: 2026-05-27  
**Unit**: 6 - Cumplimiento (LGPD/Compliance)  
**Actividad**: 4 - Infraestructura  
**Estado**: ✅ COMPLETADA
