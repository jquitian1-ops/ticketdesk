# Unit 2: Fundamentos Backend — Actividad 2: Requisitos No-Funcionales (NFR)

**Proyecto**: TicketDesk Enterprise v1.0  
**Fase**: Construcción  
**Unit**: 2 - Fundamentos Backend  
**Actividad**: 2 - Requisitos No-Funcionales (NFR)  
**Fecha**: 2026-05-27  

---

## 📋 Descripción General

**6 Requisitos No-Funcionales** con métricas cuantificadas, umbrales de aceptación y estrategias de medición.

---

## 🎯 NFR 1: Rendimiento (Performance)

**Categoría**: Eficiencia, Experiencia de Usuario

### Descripción
El sistema backend debe responder a solicitudes dentro de latencias específicas para garantizar experiencia fluida del candidato y reclutador.

### Requisitos Cuantificados

| Métrica | Objetivo | Umbral Crítico | Medición |
|---------|----------|---|---|
| Latencia endpoint p50 | <100ms | <200ms | CloudWatch latency percentiles |
| Latencia endpoint p95 | <500ms | <1000ms | CloudWatch latency percentiles |
| Latencia endpoint p99 | <1000ms | <2000ms | CloudWatch latency percentiles |
| Tiempo respuesta streaming mensaje | <100ms por token | <200ms por token | WebSocket/SSE event timing |
| Tiempo respuesta búsqueda caché | <10ms | <50ms | Redis timing metrics |
| Tiempo procesamiento mensaje completo | <500ms | <1000ms | Aplicación de logs de duración |

### Criterios de Aceptación

- [ ] 95% de solicitudes completan en <500ms (p95)
- [ ] 99% de solicitudes completan en <1000ms (p99)
- [ ] Streaming de tokens entrega <100ms latencia por token
- [ ] Caché Redis <10ms latencia típica
- [ ] Sin solicitudes >2000ms bajo carga normal (p99.9)

### Estrategia de Medición

```python
# CloudWatch Metrics (Backend)
- aws:endpoint:latency (p50, p95, p99)
- aws:endpoint:duration
- aws:redis:latency
- aws:database:query:duration

# Aplicación Instrumentación (APM)
- @app.middleware("timing")
  - Registrar inicio: request.start_time = time.now()
  - Registrar fin: duration = time.now() - request.start_time
  - Emitir métrica CloudWatch (latency_ms)

# Frontend Real User Monitoring (RUM)
- window.performance.timing
- Enviar a Datadog/New Relic: page_load, api_response_time
```

### Actividades para Garantizar

- Identificar endpoints críticos (mensaje, evaluación)
- Perfilar bajo carga (Apache JMeter, Locust)
- Optimizar índices de BD (clustering por session_id, screening_id)
- Caché estratégico (rúbricas, preguntas de campaña)
- Monitoreo continuo (dashboards CloudWatch)

### Impacto Negocio

**Métrica**: Cada 100ms de latencia extra = +3% tasa abandono (según estudios UX)
- Latencia actual estimada: 150ms
- Target: 500ms p95 mantiene abandono <5%
- Crítico: >2000ms = conversión a 0

---

## 🎯 NFR 2: Escalabilidad

**Categoría**: Disponibilidad, Crecimiento

### Descripción
El sistema debe soportar crecimiento de carga sin degradación significativa de rendimiento.

### Requisitos Cuantificados

| Métrica | Objetivo | Medición |
|---------|----------|----------|
| Sesiones concurrentes | 1,000 simultáneas | Contador Sesión.estado=ACTIVA |
| Screenings activos | 500 simultáneos | Contador Screening.estado=EN_PROGRESO |
| Evaluaciones procesando | 200 simultáneas | Contador Evaluación.estado=EN_PROGRESO |
| RPS (Requests Per Second) | 5,000 RPS pico | CloudWatch RequestCount/60s |
| Auto-escalado ECS | +0 a +8 tareas en <5min | ECS TargetTrackingScaling event lag |
| Crecimiento BD | Soportar 10M registros sin degradación | RDS Multi-AZ replication lag <1s |
| Throughput Redis | 10,000 ops/sec | ElastiCache Operations/sec metric |

### Criterios de Aceptación

- [ ] Sistema maneja 1,000 sesiones concurrentes sin error
- [ ] Latencia p95 bajo pico carga (<500ms)
- [ ] Auto-escalado ECS dispara en <5min ante spike
- [ ] RDS replication lag <1s (Multi-AZ sync)
- [ ] Redis eviction rate <1% (buena caching)
- [ ] Sin timeout en API under pico load

### Estrategia de Medición

```python
# Pruebas de Carga (Load Testing)
- Herramienta: Locust (Python) o Apache JMeter
- Escenario: 1,000 usuarios concurrentes
- Duración: 15 minutos ramp-up
- Métricas: response_time, error_rate, throughput

# Monitoreo Producción
- CloudWatch: RequestCount, TargetResponseTime, HTTPCode_Target_5XX
- RDS: DatabaseConnections, ReplicaLag
- ElastiCache: CPUUtilization, EvictionRate, CacheHits
- ECS: TaskCount, CPUUtilization, MemoryUtilization

# Dashboard (Real-time)
- Sesiones activas: min-max-current
- RPS: actual vs límite (5,000)
- Error rate: <0.1%
- Latencia p95: <500ms
```

### Actividades para Garantizar

- Diseñar con stateless (horizontalmente escalable)
- Connection pooling BD (max 20 conexiones por instancia)
- Caché distribuido (Redis Cluster optional, pero preparado)
- Load balancer (ALB con target groups health check)
- Pruebas carga mensual (regresión automática)

### Impacto Negocio

**Capacidad actual estimada**: 500 sesiones simultáneas (1 instancia ECS)
**Target**: 1,000 sesiones (2 instancias ECS auto-escaladas)
**Costo**: ~$50/mes por instancia extra
**Beneficio**: Soportar x10 campaña sin infra overhaul

---

## 🎯 NFR 3: Fiabilidad (Reliability)

**Categoría**: Disponibilidad, Resiliencia

### Descripción
El sistema debe mantener servicio confiable incluso ante fallos parciales.

### Requisitos Cuantificados

| Métrica | Objetivo | Umbral Crítico |
|---------|----------|---|
| Uptime (disponibilidad) | 99.5% anual | 99.0% |
| MTTR (Mean Time To Repair) | <2 minutos | <5 minutos |
| MTTF (Mean Time To Failure) | >720 horas | >168 horas |
| Tasa error API | <0.1% | <1% |
| Recuperación de fallo BD | <30s failover | <60s |
| Recuperación de fallo Redis | <10s reconexión | <30s |
| Idempotencia mensajes | 100% | - |

### Criterios de Aceptación

- [ ] 99.5% uptime (máx 21.6 horas downtime/año)
- [ ] 0% data loss (BD Multi-AZ sync)
- [ ] Recuperación automática BD failover <30s
- [ ] Circuit breaker previene cascading failures
- [ ] Todos endpoints idempotentes (safe retries)
- [ ] Graceful degradation (fallback responses)

### Estrategia de Medición

```python
# Uptime Tracking
- CloudWatch Events → SNS → Pagerduty
- Alertas por: HTTP 5xx, TimeoutError, DB connection lost

# Health Checks
- GET /health → { status: "healthy", timestamp, version }
  - Verificar: BD conectada, Redis conectada, API Claude disponible
  - Respuesta <100ms
- Ejecutado por: ECS health check (cada 30s), ALB (cada 5s)

# Circuit Breaker Métricas
- Evento: CircuitBreakerOpened
- Métrica: Contador (cuántas veces se abre)
- Dashboard: estado actual (CLOSED, OPEN, HALF_OPEN)

# Alertas
- Error rate >0.1% → Pagerduty
- Latencia p95 >1s → Warning (no page)
- Database CPU >80% → Page
- Redis eviction >10% → Page
```

### Actividades para Garantizar

- Implementar circuit breaker (pybreaker o tenacity)
- Health check endpoint (/health)
- Retry logic con exponential backoff
- Graceful shutdown (SIGTERM handler)
- Backup BD automático (daily, 30-day retention)
- Disaster recovery plan (RTO <1h, RPO <15min)

### Impacto Negocio

**SLA con clientes**: 99.5% uptime
**Costo downtime**: ~$5,000 por hora (estimado 50 campañas activas)
**Prioridad**: CRÍTICA

---

## 🎯 NFR 4: Seguridad (Security)

**Categoría**: Integridad, Confidencialidad, Autenticación

### Descripción
El sistema debe proteger datos candidato y prevenir acceso no autorizado.

### Requisitos Cuantificados

| Métrica | Objetivo | Medición |
|---------|----------|----------|
| Autenticación JWT | RS256 (asymmetric) | Algoritmo configurado |
| Token TTL acceso | 1 hora | Claim `exp` |
| Token TTL refresco | 30 días | Claim `exp` |
| Rotación refresh token | Post-uso | Revoke anterior token |
| Encriptación datos en tránsito | TLS 1.2+ | CloudFront HTTPS only |
| Encriptación datos en reposo | AES-256 KMS | RDS encryption enabled |
| Validación entrada | 100% endpoints | Input validation rules |
| Rate limiting | 100 req/min por IP | Middleware enforcement |
| SQL Injection prevention | 0 vulnerabilidades | Parametrized queries (SQLAlchemy) |
| XSS prevention | 0 vulnerabilidades | Output escaping (Jinja2) |
| CSRF tokens | Validación POST/PUT/DELETE | Session-bound tokens |

### Criterios de Aceptación

- [ ] JWT RS256 configurado (private key en AWS Secrets Manager)
- [ ] Todos endpoints requieren Authorization header
- [ ] Token refresh rotado (old token revocado)
- [ ] HTTPS forzado (HTTP → 301 redirect)
- [ ] KMS key rotation anual
- [ ] SQLAlchemy ORM elimina SQL injection
- [ ] CORS configurado (whitelist dominios)
- [ ] Security headers: CSP, X-Frame-Options, X-XSS-Protection
- [ ] OWASP Top 10 scan pasando (0 críticas)
- [ ] Penetration testing anual

### Estrategia de Medición

```python
# Autenticación
- JWT validation: PyJWT.decode(token, key, algorithms=["RS256"])
- Endpoint middleware: @app.middleware("http") verificar Authorization
- Token refresh: POST /auth/refresh → nueva pareja tokens

# Validación Entrada
- Pydantic schemas (automatic validation)
- Zod en frontend (adicional validation)
- Rate limiting: slowapi middleware

# Pruebas Seguridad
- OWASP ZAP scan (automated)
- Manual penetration testing (trimestral)
- Dependency scanning (Snyk, cada push)

# Audit Logging
- Todos cambios sensibles registrados
- Evento: AdminUserCreated, PermissionGranted, DataExported
- Almacenado: AuditoríaEvento tabla (append-only)
```

### Actividades para Garantizar

- Implementar JWT con RS256 (public/private key pair)
- AWS Secrets Manager para credenciales
- HTTPS con TLS 1.2+ (CloudFront)
- WAF (Web Application Firewall) en ALB
- Scanning de dependencias (Snyk pre-commit)
- Pruebas seguridad regular (OWASP ZAP)
- Cumplimiento LGPD (encryption, audit trail, right-to-delete)

### Impacto Negocio

**Riesgo**: Breach de datos candidato → litigio + multa LGPD
**Multa LGPD**: Hasta 2% revenue o R$50M
**Prioridad**: CRÍTICA

---

## 🎯 NFR 5: Cumplimiento (Compliance)

**Categoría**: Datos, Auditoría, Privacidad

### Descripción
El sistema debe cumplir con regulaciones LGPD y estar auditado.

### Requisitos Cuantificados

| Métrica | Objetivo | Medición |
|---------|----------|----------|
| Retención auditoria | 7 años | AuditoríaEvento.created_at retention policy |
| Derecho al olvido | <24 horas hard delete | Celery task SLA |
| Consentimiento documentado | 100% | Consentimiento.dado_en + ip + user_agent |
| Revocación consentimiento | <5 minutos procesamiento | Suspender operaciones relacionadas |
| PII redacción | Logs y backups | Hash/mask email/teléfono en no-prod |
| Documentación cambios datos | 100% de mutaciones | AuditoríaEvento para todos INSERT/UPDATE/DELETE |
| Cumplimiento políticas | Revisión anual | Legal review + audit trail analysis |

### Criterios de Aceptación

- [ ] Registro auditoría 100% de mutaciones (CREATE, UPDATE, DELETE, READ sensible)
- [ ] Derecho al olvido: <24h desde solicitud hasta hard delete
- [ ] Consentimiento: 3 tipos requeridos (DATA_PROCESSING, RECORDING, ANALYTICS)
- [ ] Revocación: Celery task cancela operaciones dentro 5min
- [ ] Retención: 7 años auditoría, 30 días transcripción (default)
- [ ] PII: No aparecer en logs de non-prod (redactado)
- [ ] Documentación: Política privacidad + términos servicio actualizados

### Estrategia de Medición

```python
# Auditoría Logging
- Tabla: AuditoríaEvento
- Campos: id, tipo_entidad, id_entidad, acción, usuario_id, fecha, cambios_json, dirección_ip
- Append-only: NO UPDATE/DELETE en registros auditoría

# Derecho al Olvido
- POST /api/candidatos/{id}/solicitar-eliminación
  - Crear DatosEnLimpieza(id_candidato, solicitado_en, eliminar_en=now+24h)
  - Celery task: hard_delete_after_24h(id_candidato)
  - Ejecuta: BD hard delete, S3 delete, caché clear

# Consentimiento Tracking
- Tabla: Consentimiento(id, id_candidato, id_campaña, tipo, estado, dado_en, revocado_en, ip, user_agent)
- Validación: Consentimiento.PROCESAMIENTO requerido antes screening

# Reportes Cumplimiento
- Dashboard: Cantidad solicitudes olvido, latencia promedio eliminación
- Auditoria: Export JSON registros auditoría para Legal (anual)
```

### Actividades para Garantizar

- Implementar AuditoríaEvento append-only
- Celery task para derecho al olvido (<24h SLA)
- Políticas de retención datos (7 años auditoría, 30 días transcripción)
- PII masking en logs (hash emails, mask teléfonos)
- Documentación consentimiento (legal review)
- LGPD compliance checklist (anual)
- Backup encriptado con restore testing (trimestral)

### Impacto Negocio

**Regulación**: LGPD (ley brasileña, aplicable a empresa)
**Multa máxima**: 2% revenue anual o R$50M
**Prioridad**: CRÍTICA

---

## 🎯 NFR 6: Observabilidad (Observability)

**Categoría**: Monitoreo, Debugging, Análisis

### Descripción
El sistema debe generar visibilidad suficiente para debugging rápido y análisis de tendencias.

### Requisitos Cuantificados

| Métrica | Objetivo | Herramienta |
|---------|----------|----------|
| Log coverage | 100% de eventos significativos | CloudWatch Logs |
| Trace coverage | 95% de request flows | X-Ray tracing |
| Métrica custom | >50 métricas negocio | CloudWatch custom metrics |
| Alerta cobertura | >90% de fallos detectados | Pagerduty integration |
| MTTR (Mean Time To Resolve) | <5 minutos | Logs + trace diagnostics |
| Dashboard actualización | <1 minuto | CloudWatch dashboard refresh |
| Retención logs | 30 días (producción) | CloudWatch log retention |
| Costo observabilidad | <5% de costo total AWS | Baseline ~$500-1000/mes |

### Criterios de Aceptación

- [ ] Logs contienen: timestamp, nivel (DEBUG/INFO/WARN/ERROR), servicio, mensaje, contexto
- [ ] Traces muestran: request_id, latencia por servicio, database query time
- [ ] Métricas registran: request count, error rate, latencia (p50/p95/p99), token usage
- [ ] Alertas disparan: error rate >0.1%, latencia p95 >1s, database CPU >80%
- [ ] Dashboard muestra: uptime, RPS, latencia, errores, sesiones activas (live)
- [ ] Búsqueda logs <2s (CloudWatch Insights query performance)

### Estrategia de Medición

```python
# Logging (CloudWatch Logs)
import logging
logger = logging.getLogger(__name__)
logger.info("SessionStarted", extra={
    "session_id": str(session.id),
    "candidate_id": str(session.candidate_id),
    "timestamp": session.created_at.isoformat(),
    "duration_ms": 100
})

# Tracing (AWS X-Ray)
from aws_xray_sdk.core import xray_recorder

@xray_recorder.capture('exchange_message')
def exchange_message(conversation_id, message):
    # Subsegment automático para cada función
    return bot_engine.process(message)

# Métricas Custom (CloudWatch PutMetricData)
cloudwatch.put_metric_data(
    Namespace='TicketDesk',
    MetricData=[
        {
            'MetricName': 'SessionCount',
            'Value': active_sessions,
            'Unit': 'Count'
        },
        {
            'MetricName': 'TokensUsed',
            'Value': tokens_in_evaluation,
            'Unit': 'Count'
        }
    ]
)

# Alertas (CloudWatch Alarms)
cloudwatch.put_metric_alarm(
    AlarmName='ErrorRateHigh',
    MetricName='HTTPCode_Target_5XX',
    Threshold=5,  # 5 errores en 5 minutos
    ComparisonOperator='GreaterThanThreshold',
    AlarmActions=['arn:aws:sns:...']
)
```

### Actividades para Garantizar

- Configurar CloudWatch Logs (30d retention)
- Habilitar X-Ray tracing (sampling: 10% normal, 100% errors)
- Crear métricas custom (negocio + técnicas)
- Dashboard centralizado (Grafana o CloudWatch dashboard)
- Alertas setup (Pagerduty integration)
- Runbook para escaladas (error rates, latency, database)
- Log analysis regularmente (CloudWatch Insights)

### Impacto Negocio

**MTTR actual sin observabilidad**: 30+ minutos (investigación manual)
**MTTR target con observabilidad**: <5 minutos (logs + traces)
**Impacto**: -$2,500/año (downtime reducido)

---

## 📊 Matriz de Trazabilidad NFR

| NFR | Agregado | Componente | Métrica Clave | SLA |
|---|---|---|---|---|
| Rendimiento | Mensaje | BotEngine | Latencia p95 <500ms | 99% cumplimiento |
| Escalabilidad | Sesión | ECS Auto-scaling | 1,000 sesiones concurrentes | 100% under load |
| Fiabilidad | Sistema | Health Check | Uptime 99.5% | <2min MTTR |
| Seguridad | Autenticación | JWT RS256 | 0 vulnerabilidades | OWASP ZAP pass |
| Cumplimiento | Auditoría | AuditoríaEvento | <24h derecho olvido | LGPD compliant |
| Observabilidad | Logs | CloudWatch | <2s query latencia | 95% trace coverage |

---

## ✅ Criterios de Aceptación (Actividad 2)

- [x] 6 NFRs documentados con métricas cuantificadas
- [x] Umbrales aceptación claros (objetivo + crítico)
- [x] Estrategias medición definidas (herramientas específicas)
- [x] Actividades para garantizar listos
- [x] Impacto negocio articulado
- [x] Matriz trazabilidad con SLAs

---

**Generado**: 2026-05-27  
**Unit**: 2 - Fundamentos Backend  
**Actividad**: 2 - Requisitos No-Funcionales  
**Estado**: ✅ COMPLETADA
