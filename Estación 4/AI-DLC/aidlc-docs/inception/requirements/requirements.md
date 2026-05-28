# Requisitos Técnicos — TicketDesk Enterprise v1.0

**Documento generado mediante AI-DLC Requirements Analysis**  
**Fecha**: 2026-05-27  
**Estado**: Aprobado — Listo para Workflow Planning

---

## ANÁLISIS INICIAL

### Resumen de Solicitud
- **Tipo**: Nuevo Producto (Greenfield)
- **Complejidad**: Moderada-Alta (IA conversacional + cumplimiento LGPD + auditoría legal)
- **Scope**: Plataforma web + Bot + Dashboard HITL
- **Timeline**: MVP 8-10 semanas (30/60/90 días)
- **Equipo**: 4-6 desarrolladores

### Contexto Funcional
El PRD define una plataforma de screening automatizado para hiring que:
- Reduce costo-per-hire 75% ($16.67 → $4.17 USD)
- Acelera screening 3x (45 min → 15 min)
- Proporciona auditoría legal 100% (citas textuales para cada puntuación)
- Cumple LGPD nativo (Brasil) con derecho olvido, consentimiento explícito

---

## DECISIONES TÉCNICAS APROBADAS

### Stack Tecnológico

#### Frontend
- **Framework**: Next.js 14+ con TypeScript
- **Razonamiento**: SSR/SSG para SEO, API routes, excelente UX para candidatos async
- **Componentes UI**: React 18+, TailwindCSS, Shadcn/UI
- **Internacionalización**: next-i18n (i18n desde MVP para facilitar portugués v1.2)
- **State Management**: Zustand (ligero) + React Query (data fetching)

#### Backend
- **Runtime**: Python 3.11+ con FastAPI
- **Razonamiento**: Excelente para integraciones LLM, procesamiento evaluación, async/await nativo
- **ORM**: SQLAlchemy 2.0 con async support
- **Validación**: Pydantic v2
- **Task Queue**: Celery + Redis (evaluación async, emails, re-engagement)
- **API**: RESTful JSON + future WebSocket support

#### Base de Datos
- **Primary**: PostgreSQL 15+ (AWS RDS managed)
  - ACID compliance (crítico para auditoría LGPD)
  - Soporte JSON (flexible schemas para evaluaciones)
  - Full-text search (búsqueda en transcripciones)
  
- **Cache**: Redis 7+ (AWS ElastiCache)
  - Sesiones candidato en progreso
  - Caché rúbricas por campaña
  - Rate limiting (anti-abuse bot)
  - Pub/Sub para updates HITL real-time

#### LLM & IA
- **Proveedor**: Claude API (Anthropic) v3.5 Sonnet
- **Razonamiento**: 
  - Conversación española superior, bajo hallucination risk (<2%)
  - Context window 200k (completa transcripciones largas)
  - Vision capability (future: analizar documentos)
  - Consistent API for production use

#### Infraestructura
- **Cloud**: AWS
  - Región: sa-east-1 (São Paulo, LGPD Brasil)
  - Backup: sa-east-2 (São Paulo secundario) v1.1
  
- **Compute**: ECS (Elastic Container Service)
  - Docker containers, auto-scaling
  - Load balancer: ALB (Application Load Balancer)
  - Task definition: 2 vCPU, 4GB RAM por instancia
  
- **Storage**: 
  - S3: Transcripciones audio (encrypted)
  - RDS PostgreSQL: Datos relacionales, logs auditoría
  - ElastiCache Redis: Sesiones, caché
  
- **CI/CD**: GitHub Actions → ECR (Elastic Container Registry) → ECS

#### Tiempo Real
- **MVP**: HTTP Polling (2-3s bot updates, 5s HITL cola)
- **Ventajas**: Stateless, fácil testear, cero infraestructura nueva
- **Upgrade v1.1**: WebSocket si latencia crítica

#### Containerización
- **Tecnología**: Docker
- **Orquestación**: AWS ECS (Fargate pricing model)
- **Ventajas**: Managed scaling, sin Kubernetes ops, integración AWS nativa

---

## REQUISITOS FUNCIONALES

### RF-1: Motor Screening Conversacional (ÉPICA-02)

#### RF-1.1: Conversación Candidato-Bot
- Bot debe conduct 5-6 preguntas STAR-based en tiempo real
- Cada pregunta debe soportar follow-ups adaptativos basados en respuesta previa
- Bot debe detectar incompletitud de respuesta y solicitar aclaración
- Tiempo máximo respuesta pregunta: 15 minutos (default abandonment)
- Transcripción en tiempo real (grabada en S3)

**Aceptación**: Candidato completa 5 preguntas en 12-18 minutos, transcripción exacta en S3

#### RF-1.2: Evaluación en Tiempo Real
- Sistema debe evaluar cada respuesta contra rúbrica candidata
- Scoring: 1-100 (escala continua)
- Scoring desglosado por competencia (ej: "Comunicación 8/10, Liderazgo 7/10")
- Cada puntuación debe tener cita textual de respuesta (verbatim del candidato)

**Aceptación**: Score final ≥ 98% match entre evaluación IA y revisión humana spot-check

#### RF-1.3: Guardrails & Escalación
- Bot debe detectar preguntas fuera de alcance (no en Knowledge Base)
- Preguntas OOB deben escalarse a ticket automático para reclutador
- Bot responde honestamente: "No tengo esa información. Equipo de [empresa] te dirá."

**Aceptación**: 100% de preguntas OOB detectadas y escaladas

### RF-2: Dashboard HITL (ÉPICA-04)

#### RF-2.1: Cola de Revisión Filtrada
- Reclutador ve candidatos Score 50-80 (requieren decisión humana)
- Ordenamiento: por score (descendente), fecha (más recientes primero)
- Filtrado: por campaña, estado (pendiente, aprobado, rechazado)

**Aceptación**: <5s carga cola 1000 candidatos

#### RF-2.2: Panel Decisión
- Reclutador ver: resumen ejecutivo + citas + transcripción completa
- Acciones: "Aprobar", "Rechazar", "Revisar" (requiere nota)
- Timestamp automático de decisión + usuario

**Aceptación**: Decisión HITL toma ≤5 minutos (vs. 45 min hoy)

### RF-3: Cumplimiento & Auditoría (ÉPICA-06)

#### RF-3.1: Registro Inmutable de Evaluación
- BD: Cada evaluación genera entry inmutable en auditoría
- Fields: campaña_id, candidato_id, pregunta, respuesta, puntuación, cita_textual, timestamp, evaluador
- No permite overwrite histórico (append-only log)

**Aceptación**: 100% de evaluaciones tienen cita textual en auditoría

#### RF-3.2: Consentimiento LGPD Explícito
- Candidato DEBE confirmar checkbox: "Entiendo que soy evaluado por IA y mis datos procesados conforme LGPD"
- No proceed a screening sin checkbox
- Consentimiento registrado en BD con timestamp

**Aceptación**: Cumple 100% LGPD en auditoría interna

#### RF-3.3: Derecho al Olvido (Right to Erasure)
- Candidato solicita borrado vía UI → sistema marca como "borrado"
- Datos borrados post 90 días automáticamente
- Logs auditoría mantenidos 90 días para compliance, luego borrados

**Aceptacion**: Fulfills LGPD dentro 30 días solicitud

### RF-4: Abandono & Re-engagement (ÉPICA-07)

#### RF-4.1: Detección Inactividad
- Sistema detecta candidato inactivo >5 minutos en pregunta
- Pausa suave: "Veo que no respondiste. Tómate tu tiempo, aquí estaré cuando quieras continuar."
- Sesión guardada en Redis (contexto íntegro)

**Aceptación**: Contexto restaurado exactamente al reanudar

#### RF-4.2: Re-engagement Automático
- 24h después inactividad: Email soft reminder
- 48h después: Email final "Última oportunidad, quedan N preguntas"
- Candidato clica enlace → sessionresume, contexto íntegro

**Aceptación**: +15-20% completion rate (vs baseline 50-70%)

### RF-5: Campañas & Knowledge Base (ÉPICA-05)

#### RF-5.1: Crear Campaña
- Director RH crea campaña: rol, rúbrica, KB, preguntas
- Generador de enlace único: https://ticketdesk.com/campaign/UUID
- Tiempo setup: 30 min (vs. 2h hoy)

**Aceptación**: Director RH crea campaña en 30 min sin técnico

#### RF-5.2: Knowledge Base
- Upload documentos PDF: job description, beneficios, políticas
- Bot accede KB para responder Q fuera de scope (RAG)
- Búsqueda: full-text search en PostgreSQL

**Aceptación**: Bot responde 90% preguntas KB sin escalación

---

## REQUISITOS NO-FUNCIONALES

### NFR-1: Rendimiento

#### NFR-1.1: Latencia Bot
- Tiempo respuesta bot question: <2 segundos (p95)
- Evaluación en tiempo real: <5 segundos post-respuesta
- Tiempo carga HITL dashboard: <3 segundos

#### NFR-1.2: Throughput
- Capacidad: 100+ candidatos concurrentes screening simultáneamente
- Escalado automático ECS: +instances si CPU >70%

#### NFR-1.3: Database
- Query P99 auditoría: <500ms
- Connection pool: 20-50 conexiones

### NFR-2: Seguridad

#### NFR-2.1: Encriptación
- En tránsito: TLS 1.3 (HTTPS, WSS)
- En reposo: AWS KMS encryption (RDS, S3)
- Sensitive fields en BD: encrypted (API keys, etc.)

#### NFR-2.2: Autenticación & Autorización
- Reclutador: OAuth2 + JWT (short-lived tokens)
- Candidato: Session-based (no auth, solo session UUID)
- RBAC: Director RH, Reclutador, Admin roles

#### NFR-2.3: API Security
- Rate limiting: 1000 req/min por IP
- CORS: whitelist dominios permitidos
- Input validation: Pydantic + sanitización
- SQL injection prevention: ORM parameterized queries

#### NFR-2.4: Jailbreak Prevention
- Bot system prompt no expuesto a candidato
- Attempts to reveal prompt → bot declines + escalación
- Red-teaming testing fase pre-launch (65 casos adversariales)

### NFR-3: Cumplimiento & Regulatorio

#### NFR-3.1: LGPD Brasil
- Residencia datos: São Paulo (sa-east-1) 100%
- DPA (Data Processing Agreement) with customers
- Auditoría de accesos: log todos queries a datos PII
- Right to erasure: hard delete <90 días

#### NFR-3.2: Fairness & Transparency
- Rúbrica explícita, visible candidato durante screening
- Explicación scorecard: "Comunicación 8/10 porque respondiste con ejemplo STAR claro"
- Bias monitoring: log comparativa puntuaciones por género/edad/etc (opcional, segregado)

### NFR-4: Disponibilidad & Reliability

#### NFR-4.1: Uptime
- Target: 99.5% (4.4 horas downtime/mes)
- SLA: guaranteed para clientes pagos
- Monitoring: CloudWatch alarms automático

#### NFR-4.2: Disaster Recovery
- RTO (Recovery Time Objective): <1 hora
- RPO (Recovery Point Objective): <15 minutos
- Multi-AZ deployment: primary + standby
- Backup diario: incremental S3 cross-region

#### NFR-4.3: Graceful Degradation
- Si Claude API está down: bot pausa, candidato informed
- Si Redis está down: HTTP session fallback (más lento pero funciona)
- Si S3 está down: transcripciones buffered en BD temporalmente

### NFR-5: Mantenibilidad

#### NFR-5.1: Code Quality
- Testing: 80%+ coverage (unit + integration)
- Static analysis: Ruff (linting), MyPy (type checking)
- Pre-commit hooks: auto-format, linting

#### NFR-5.2: Documentation
- API documentation: OpenAPI/Swagger (auto from code)
- Architecture decision records (ADRs)
- Runbook de operaciones, troubleshooting

#### NFR-5.3: Logging & Observability
- Logs estructurados JSON (timestamp, level, context)
- Distributed tracing preparado (OpenTelemetry, upgrade v1.1)
- Métricas: latency, throughput, errors (Prometheus-compatible)

### NFR-6: Escalabilidad

#### NFR-6.1: Horizontal Scaling
- Backend stateless → add/remove instancias ECS libremente
- Redis cluster-ready (pero single node MVP, cluster v1.1)
- RDS: parametrized, plan para read replicas v1.1

#### NFR-6.2: Data Growth
- Proyección year 1: 50k candidatos × 6 preguntas = 300k registros evaluación
- Partitioning: monthly tables para auditoría (optimiza queries antiguas)

---

## REQUISITOS DE DATOS

### RD-1: Modelo de Datos Principales

#### Entidades Clave
1. **Campaign**: campaña_id, empresa_id, rol, rúbrica_id, fecha_inicio, fecha_fin, status
2. **Candidate**: candidato_id, email, nombre, campaña_id, estado (iniciado, completado, abandonado)
3. **Screening**: sesión_id, candidato_id, pregunta#, respuesta_texto, timestamp
4. **Evaluation**: evaluación_id, sesión_id, pregunta#, score, cita_textual, competencia_id
5. **AuditLog**: log_id, entidad, acción, usuario, timestamp, cambios

### RD-2: Volúmenes de Datos
- Campañas activas: 10-100 simultáneamente
- Candidatos/campaña: 100-500
- Sesiones/mes: 5k-50k (escala con clientes)
- Retención: 90 días (LGPD), entonces borrado automático

---

## INTEGRACIÓN & DEPENDENCIAS

### DEP-1: APIs Externas
- **Claude API** (Anthropic): screening bot, fallback graceful si down
- **AWS services**: RDS, ElastiCache, S3, ECS, ALB, KMS

### DEP-2: Futuros (Out of Scope MVP)
- ATS integration (Workday, BambooHR) — v1.1
- Twilio/SendGrid email — MVP usará SES básico AWS
- Sentry error tracking — v1.1 (logs a CloudWatch MVP)

---

## CRITERIOS DE ACEPTACIÓN GENERALES

### CA-1: Funcionalidad
✅ Todas 11 features Must-Have del PRD implementadas  
✅ 5-6 preguntas screening completadas en ≤18 min  
✅ 100% citas textuales para evaluaciones  
✅ Tasa completitud ≥85% (vs. baseline 50-70%)  

### CA-2: Cumplimiento
✅ LGPD audit completo sin hallazgos críticos  
✅ DPA firmado (customer template disponible)  
✅ Transparencia IA explícita en UI  
✅ Consentimiento LGPD 100% de candidatos  

### CA-3: Calidad
✅ Test coverage 80%+  
✅ Factualidad IA ≥98% (red-teaming 65 casos, ≥95% pase)  
✅ Zero critical security vulnerabilities (OWASP top 10)  
✅ Uptime 99.5% en staging 2 semanas pre-launch  

### CA-4: Performance
✅ Bot latency <2s p95  
✅ HITL dashboard <3s carga  
✅ Soportar 100+ candidatos concurrentes  

---

## HITOS PRINCIPALES

| Fase | Entregables | Timeline |
|---|---|---|
| **Fase 1** | MVP staging-ready, 30 synthetic tests passed | Días 1-30 |
| **Fase 2** | Piloto validado, ≥100 candidatos reales, NPS ≥3.5 | Días 31-60 |
| **Fase 3** | GA launch, 5+ clientes adquiridos, KPIs validados | Días 61-90 |

---

## PRÓXIMOS PASOS

1. ✅ Requirements Analysis — **COMPLETE**
2. → **Workflow Planning** — Descomponer en units of work, estimar esfuerzo
3. → **Application Design** — Arquitectura detallada, diagramas componentes
4. → **Code Generation** — Implementación backend + frontend por unit
5. → **Build & Test** — Integration, security scanning, deployment staging

---

**Estado**: ✅ Requisitos Técnicos Aprobados  
**Fecha**: 2026-05-27  
**Siguiente Fase**: Workflow Planning
