# Unit 6: Cumplimiento (LGPD/Compliance) — Actividad 1: Entidades del Dominio

**Proyecto**: TicketDesk Enterprise v1.0  
**Fase**: Construcción  
**Unit**: 6 - Cumplimiento (LGPD/Compliance)  
**Actividad**: 1 - Diseño Funcional: Entidades del Dominio  
**Fecha**: 2026-05-27  

---

## 📋 Contexto Acotado: Cumplimiento LGPD + Auditoría

**Alcance**: Auditoría completa de todas las operaciones, registro consentimiento dinámico, solicitudes derecho olvido, hard delete asincrónico, reportes compliance.

**Patrón**: Domain-Driven Design con Agregados append-only, Objetos de Valor inmutables

---

## 🎯 4 Agregados del Dominio

### 1. AgregadoEntradaAuditoría

**Entidad Raíz**: `EntradaAuditoría`

```
EntradaAuditoría (Raíz, Append-Only)
├── id: UUID
├── timestamp: DateTime (IMMUTABLE, UTC)
├── tipo_evento: TipoEvento (CREATE, UPDATE, DELETE, EXPORT, CONSENT, JAILBREAK, EVALUATION, etc.)
├── entidad_tipo: String (Usuario, Sesión, Screening, Evaluación, etc.)
├── entidad_id: UUID
├── usuario_id: UUID (quien realizó acción)
├── dirección_ip: IPAddress (hashed SHA256)
├── user_agent: String (navigator.userAgent, hashed)
├── acción: AcciónAuditoria (INSERT, UPDATE, DELETE, READ, EXPORT)
├── cambios: JSON (before/after, solo datos sensibles hashed)
│   ├── campo_modificado: String
│   ├── valor_anterior: String (hashed si PII)
│   └── valor_nuevo: String (hashed si PII)
├── resultado: ResultadoAcción (EXITOSO, FALLIDO, BLOQUEADO)
├── razón_fallo: String | NULL (si fallido)
├── contexto: JSON
│   ├── session_id: UUID
│   ├── app_version: String
│   ├── feature_flag: String
│   └── request_id: String (para correlación)
├── pii_campos_accedidos: Lista[String] (email, phone, etc.)
├── propósito_acceso: PropósitoAcceso (SCREENING, EVALUATION, COMPLIANCE, INTERNAL)
└── estado: EstadoAuditoría (ACTIVA, RETENIDA, ELIMINADA)

Invariantes:
- EntradaAuditoría IMMUTABLE (append-only, nunca UPDATE/DELETE)
- timestamp ≤ ahora (no futuros)
- usuario_id siempre presente (quién hizo)
- Si PII accedido: propósito documentado
- Retención: 7 años (automático)
- Una entrada por evento (unicidad lógica)
```

**Objetos de Valor**:
- `TipoEvento` enum
- `AcciónAuditoria` enum
- `ResultadoAcción` enum
- `PropósitoAcceso` enum
- `IPAddress` (hashed, nunca plain text)
- `UserAgent` (hashed)
- `PiiCamposAccedidos` (lista inmutable)

**Reglas Aplicadas**: REGLA-LGPD-01, REGLA-LGPD-02, REGLA-LGPD-03

---

### 2. AgregadoConsentimiento

**Entidad Raíz**: `Consentimiento`

```
Consentimiento (Raíz)
├── id: UUID
├── id_usuario: UUID (candidato Unit 2)
├── id_campaña: UUID (de qué campaña)
├── tipo_consentimiento: TipoConsentimiento (SCREENING, EVALUATION, DATA_STORAGE, MARKETING)
├── otorgado_en: DateTime (when user consented)
├── otorgado_por: MedioOtorgamiento (CHECKBOX, VERBAL, API_CALL, DOCUMENT_SIGN)
├── estado: EstadoConsentimiento (ACTIVO, REVOCADO, EXPIRADO)
├── revocado_en: DateTime | NULL
├── razón_revocación: String | NULL
├── válido_hasta: DateTime (expiry, e.g., 24 months)
├── metadata_otorgamiento: JSON
│   ├── ip_address: IPAddress (hashed)
│   ├── user_agent: String (hashed)
│   ├── país_origen: String (ISO 3166)
│   ├── geolocalización: Coordinates (hashed lat/lon)
│   ├── idioma_presentación: String (idioma consentimiento mostrado)
│   └── version_política: String (v2.0, etc.)
├── documento_consentimiento: URLEmpresa | NULL (S3 signed URL)
├── copia_local_texto: Text (backup copia consentimiento)
├── confirmar_lectura: Boolean (verificó checkbox)
├── firma_digital: String | NULL (para contracts)
├── auditoría: AuditoríaEntry
└── integridad_hash: String (SHA256 documento, para validación)

Invariantes:
- Consentimiento.estado: ACTIVO → REVOCADO (una dirección)
- otorgado_en ≤ ahora
- revocado_en > otorgado_en (si presente)
- válido_hasta > otorgado_en (futuro)
- Un consentimiento por usuario+tipo (unicidad lógica)
- Si REVOCADO: razón documentada
- Inmutable después REVOCADO
```

**Objetos de Valor**:
- `TipoConsentimiento` enum
- `MedioOtorgamiento` enum
- `EstadoConsentimiento` enum
- `MetadataOtorgamiento` (JSON estructurado, GPS hashed)
- `IntegridadDocumento` (SHA256 hash)

**Reglas Aplicadas**: REGLA-LGPD-04, REGLA-LGPD-05, REGLA-LGPD-06

---

### 3. AgregadoSolicitudEliminación

**Entidad Raíz**: `SolicitudEliminación`

```
SolicitudEliminación (Raíz, RTB "Right To Be Forgotten")
├── id: UUID
├── id_usuario: UUID (candidato solicitante)
├── id_campaña: UUID | NULL (específica o todas)
├── solicitada_en: DateTime
├── solicitada_por: MedioSolicitud (WHATSAPP, EMAIL, FORM, API, LEGAL)
├── estado: EstadoSolicitud (PENDIENTE, APROBADA, RECHAZADA, EN_PROCESO, COMPLETADA)
├── razón_solicitud: String (explicación usuario)
├── evidencia_identidad: URLEmpresa (documento verificación)
├── datos_a_eliminar: JSON
│   ├── eliminar_sesiones: Boolean
│   ├── eliminar_screenings: Boolean
│   ├── eliminar_evaluaciones: Boolean
│   ├── eliminar_consentimientos: Boolean
│   └── mantener_legal: Boolean (datos retención legal)
├── aprobada_por: UUID | NULL (admin que aprobó)
├── aprobada_en: DateTime | NULL
├── rechazada_por: UUID | NULL
├── rechazada_en: DateTime | NULL
├── razón_rechazo: String | NULL (si RECHAZADA)
├── hard_delete_iniciado_en: DateTime | NULL
├── hard_delete_completado_en: DateTime | NULL
├── tarea_celery_id: String (async job tracking)
├── registros_eliminados: JSON
│   ├── count_sesiones: Int
│   ├── count_screenings: Int
│   ├── count_evaluaciones: Int
│   ├── bytes_liberados: Int
│   └── timestamp_completado: DateTime
├── notificación_usuario_en: DateTime | NULL
├── auditoría: AuditoríaEntry (quién qué cuándo)
└── metadata: JSON

Invariantes:
- Estado: PENDIENTE → APROBADA/RECHAZADA → EN_PROCESO → COMPLETADA
- solicitada_en ≤ ahora
- SLA hard delete: <24 horas (REGLA-LGPD-07)
- Si RECHAZADA: razón_rechazo siempre presente
- Datos marcados para hard delete antes de completar (reversible hasta último momento)
- Notificación usuario post-completada
- Solicitud IMMUTABLE después COMPLETADA
```

**Objetos de Valor**:
- `MedioSolicitud` enum
- `EstadoSolicitud` enum
- `DatosAEliminar` (JSON boolean flags)
- `RegistrosEliminados` (audit trail de qué se borró)

**Reglas Aplicadas**: REGLA-LGPD-07, REGLA-LGPD-08, REGLA-LGPD-09

---

### 4. AgregadoReporteCompliance

**Entidad Raíz**: `ReporteCompliance`

```
ReporteCompliance (Raíz)
├── id: UUID
├── período: PeríodoReporte (MENSUAL, TRIMESTRAL, ANUAL)
├── año_mes: String (e.g., "2026-05")
├── generada_en: DateTime
├── aprobada_en: DateTime | NULL
├── aprobada_por: UUID | NULL (DPO Data Protection Officer)
├── estado: EstadoReporte (BORRADOR, APROBADA, PUBLICADA, ARCHIVADA)
├── métricas_lgpd: JSON
│   ├── total_usuarios_registrados: Int
│   ├── total_consentimientos: Int
│   ├── consentimientos_revocados: Int
│   ├── solicitudes_derecho_olvido: Int
│   ├── solicitudes_olvido_completadas: Int
│   ├── tiempo_promedio_olvido: Int (horas)
│   ├── violations_detected: Int
│   └── violations_resueltas: Int
├── auditoría_resumida: JSON
│   ├── total_eventos_auditados: Int
│   ├── eventos_fallidos: Int
│   ├── acceso_pii_eventos: Int
│   ├── cambios_pii: Int
│   └── exports_datos_realizados: Int
├── incidentes_seguridad: Lista[String] (descriptions)
├── violaciones_detectadas: Lista[Violación]
│   ├── tipo: String (CONSENT_MISSING, RETENTION_EXCEEDED, UNAUTHORIZED_ACCESS)
│   ├── count: Int
│   ├── acción_correctiva: String
│   ├── estado_resolución: String (ABIERTA, CERRADA)
│   └── fecha_cierre: DateTime | NULL
├── recomendaciones: Lista[String] (mejoras compliance)
├── firma_dpo: String | NULL (DPO nombre/iniciales)
├── documento_export: URLEmpresa (S3 PDF signed URL, expira 90 días)
├── sensibilidad: Sensibilidad (PÚBLICO, CONFIDENCIAL, RESTRINGIDO)
├── hash_integridad: String (SHA256 documento)
└── auditoría: AuditoríaEntry

Invariantes:
- período + año_mes = único key
- Estado: BORRADOR → APROBADA → PUBLICADA
- Si APROBADA: aprobada_por (DPO) requerido
- métricas.violations_resueltas ≤ violations_detectadas
- Reporte IMMUTABLE después PUBLICADA
- Retención: 10 años (legal requirement)
```

**Objetos de Valor**:
- `PeríodoReporte` enum
- `EstadoReporte` enum
- `MétricasLGPD` (JSON estructurado)
- `Violación` (tipo, count, acción)
- `Sensibilidad` enum

**Reglas Aplicadas**: REGLA-LGPD-10

---

## 💡 8 Objetos de Valor (Resumen)

| Objeto de Valor | Propósito | Invariante |
|---|---|---|
| `TipoEvento` | Tipo de evento auditado | CREATE, UPDATE, DELETE, CONSENT, EVALUATION |
| `AcciónAuditoria` | Acción realizada | INSERT, UPDATE, DELETE, READ, EXPORT |
| `TipoConsentimiento` | Tipo consentimiento | SCREENING, EVALUATION, DATA_STORAGE |
| `EstadoConsentimiento` | Estado consentimiento | ACTIVO, REVOCADO, EXPIRADO |
| `MedioSolicitud` | Cómo solicitud RTB | WHATSAPP, EMAIL, FORM, API |
| `EstadoSolicitud` | Estado del derecho olvido | PENDIENTE, APROBADA, EN_PROCESO, COMPLETADA |
| `MétricasLGPD` | Métricas compliance | totales, revocaciones, violations |
| `Violación` | Incidente compliance | tipo, acción correctiva |

---

## 🔄 Máquinas de Estados

### Ciclo de Vida de Consentimiento

```
┌────────┐
│ ACTIVO │
└────┬───┘
     │ revocar_consentimiento()
     ▼
┌──────────┐     ┌─────────┐
│ REVOCADO │     │ EXPIRADO│  (automático después válido_hasta)
└──────────┘     └─────────┘
```

### Ciclo de Vida de SolicitudEliminación

```
┌──────────┐
│ PENDIENTE│
└────┬─────┘
     │ revisar_solicitud()
     ├─────────────┬──────────────┐
     ▼             ▼              ▼
┌─────────┐  ┌──────────┐  ┌──────────────┐
│ APROBADA│  │ RECHAZADA│  │  EN_PROCESO  │ (async hard delete)
└────┬────┘  └──────────┘  └──────┬───────┘
     │                            │
     └────────────┬───────────────┘
                  │
                  ▼
           ┌──────────────┐
           │  COMPLETADA  │ (immutable, notificación user)
           └──────────────┘
```

---

## ✅ Relaciones Entre Agregados

```
EntradaAuditoría (Unit 6)
  ├── referencia: Cualquier entidad (usuario, sesión, screening, evaluación)
  └── usuario: Usuario (Unit 2, quién realizó)

Consentimiento (Unit 6)
  ├── pertenece_a: Usuario (Unit 2, candidato)
  ├── pertenece_a: Campaña (Unit 2)
  └── documento: S3 storage (signed URL)

SolicitudEliminación (Unit 6)
  ├── solicitada_por: Usuario (Unit 2)
  ├── pertenece_a: Campaña (Unit 2, opcional)
  ├── aprobada_por: Usuario (Unit 2, admin)
  ├── marca_para_delete: Sesiones, Screenings, Evaluaciones
  └── celery_task: Async job tracking

ReporteCompliance (Unit 6)
  ├── referencias: EntradaAuditoría (agregaciones)
  ├── referencias: Consentimiento (estadísticas)
  ├── referencias: SolicitudEliminación (métricas)
  └── aprobada_por: Usuario (Unit 2, DPO)
```

---

## 📊 Tamaños de Datos Estimados

| Agregado | Típico | Máximo | Ejemplo |
|----------|--------|--------|---------|
| EntradaAuditoría | 1KB | 5KB | evento + cambios hashed |
| Consentimiento | 2KB | 8KB | metadata + documento |
| SolicitudEliminación | 3KB | 15KB | datos_eliminar + audit trail |
| ReporteCompliance | 50KB | 200KB | métricas + violations + documento PDF |

---

## 🎯 Eventos Publicados por Unit 6

| Evento | Trigger | Consumidor |
|--------|---------|-----------|
| **ConsentimientoOtorgado** | User consent | Unit 2 (auditoría) |
| **ConsentimientoRevocado** | User revoke | Unit 2 (compliance flag) |
| **DerechoOlvidoSolicitado** | RTB request | Unit 2 (queue revisión DPO) |
| **DerechoOlvidoAprobado** | Admin approval | Celery (async hard delete) |
| **HardDeleteIniciado** | Async job start | Unit 2 (data removal) |
| **HardDeleteCompletado** | All data removed | Unit 2 (notification user) |
| **ViolacionDetectada** | Policy breach | Unit 2 (alert admin) |
| **ReporteComplianceGenerado** | Monthly/yearly | Unit 2 (export) |

---

## ✅ Criterios de Aceptación (Actividad 1)

- [x] 4 Agregados definidos (append-only para auditoría)
- [x] 8 Objetos de Valor con invariantes
- [x] Máquinas de estado (Consentimiento, SolicitudEliminación)
- [x] Relaciones hacia Unit 2
- [x] Eventos publicados identificados
- [x] Tamaños estimados documentados
- [x] LGPD requirements embebidos en agregados

---

**Generado**: 2026-05-27  
**Unit**: 6 - Cumplimiento (LGPD/Compliance)  
**Actividad**: 1 - Entidades del Dominio  
**Estado**: ✅ COMPLETADA
