# Diseño de Aplicación Consolidado — TicketDesk Enterprise v1.0

**Documento de Consolidación de Diseño de Aplicación**  
**Fecha**: 2026-05-27  
**Fase**: Inception - Application Design  
**Estado**: ✅ COMPLETADO

---

## RESUMEN EJECUTIVO

TicketDesk Enterprise es una plataforma de screening automatizado de candidatos usando Inteligencia Artificial conversacional, dirigida a empresas de recursos humanos que buscan reducir el costo por candidato evaluado de $16.67 a $4.17 (75% de ahorro).

**Arquitectura de Alto Nivel**:
- **Frontend**: Next.js 14 (React) con Zustand para estado y Tailwind para estilos
- **Backend**: Python FastAPI con arquitectura monolítica modular (6 componentes discretos)
- **Comunicación**: Event-Driven (asincrónico via Redis Pub/Sub + Celery) + Request-Reply (sincrónico via REST)
- **Data Layer**: PostgreSQL (relacional + auditoría) + Redis (cache + sesiones + cola) + S3 (objetos)
- **IA**: Claude API para conversación adaptativa de screening
- **Infraestructura**: AWS (São Paulo region para LGPD) con Docker + ECS

**Duración Estimada**: 10 semanas (6 Units of Work parallelizables), 4-6 desarrolladores

---

## PRINCIPIOS DE DISEÑO

### 1. Modularidad Alta Cohesión, Bajo Acoplamiento
- **Componentes discretos**: BotEngine, EvaluationEngine, HITLService, ComplianceService, CampaignService, SessionManager
- **Comunicación asincrónica**: Servicios NO llaman directamente, emiten eventos
- **Beneficio**: Fácil testing unitario, escalable, permite iteración independiente

### 2. Auditoría Inmutable (LGPD-First)
- Tabla `audit_logs` append-only: NO UPDATE/DELETE
- ComplianceService suscrito a TODOS los eventos
- Cumplimiento legal garantizado desde arquitectura

### 3. Responsabilidad Segregada
- **BotEngine**: Conversación (nada más)
- **EvaluationEngine**: Scoring (nada más)
- **HITLService**: Decisión reclutador (nada más)
- **ComplianceService**: Auditoría (nada más)
- **CampaignService**: Configuración (nada más)
- **SessionManager**: Estado candidato (nada más)

### 4. Fallos Graceful (Degradación Elegante)
- Claude API timeout → retry con exponencial backoff, fallback a respuesta temporal
- BD down → buffer en Redis, reintentar cada 30s, alert si >5 min
- WebSocket no disponible → fallback a polling cada 5s

### 5. Data Residency Local (LGPD)
- PostgreSQL en AWS São Paulo
- Redis en AWS São Paulo
- S3 en AWS São Paulo (todas transacciones locales)

---

## ARQUITECTURA DE COMPONENTES

### 6 Componentes Backend

| Componente | Responsabilidad | Métodos Clave | Llamadas Salientes |
|-----------|-----------------|---------------|-------------------|
| **BotEngine** | Orquestación Claude API, flujo conversacional, guardrails | `start_session()`, `process_response()`, `detect_jailbreak()` | ComplianceService, SessionManager, EvaluationEngine (evento) |
| **EvaluationEngine** | Evaluación por rúbrica, scoring, extracción citas, fairness | `evaluate_response()`, `extract_citation()`, `calculate_final_score()` | ComplianceService, HITLService (evento) |
| **HITLService** | Cola HITL, decisión reclutador, notificaciones | `add_to_queue()`, `get_queue()`, `process_decision()` | EvaluationEngine (evento), ComplianceService, EmailService |
| **ComplianceService** | Auditoría inmutable, consentimiento LGPD, retención | `log_evaluation()`, `register_consent()`, `soft_delete_candidate()` | (Suscrito a eventos) |
| **CampaignService** | CRUD campañas, rúbricas, Knowledge Base | `create_campaign()`, `update_rubric()`, `upload_knowledge_base()` | Todos servicios |
| **SessionManager** | Gestión estado sesión, inactividad, re-engagement | `create_session()`, `detect_inactivity()`, `send_reengagement_email()` | BotEngine, ComplianceService |

### 4 Componentes Frontend (Next.js)

| Componente | Responsabilidad |
|-----------|-----------------|
| **CandidateInterface** | Chat conversacional, divulgación consentimiento, feedback final |
| **RecruiterDashboard** | Cola HITL filtrada, panel decisión, analytics por campaña |
| **CampaignManager** | CRUD campañas, upload rúbricas, generar enlaces |
| **CommonUI** | Componentes compartidos (layouts, navbars, modales, estilos) |

---

## CAPA DE SERVICIOS Y ORQUESTACIÓN

### 5 Servicios de Orquestación (Patrones de Coordinación)

#### 1. **ScreeningOrchestrationService**
- **Patrón**: Request-Reply (sincrónico)
- **Flujo**: Frontend → start_screening() → BotEngine.start_session() → primera pregunta
- **Responsabilidad**: Coordina todo flujo screening candidato de inicio a fin
- **Métodos**: `start_screening()`, `process_response()`, `complete_screening()`

#### 2. **EvaluationOrchestrationService**
- **Patrón**: Event-Driven (asincrónico)
- **Escucha**: evento `candidate.response.submitted` (emitido por BotEngine)
- **Flujo**: recibe evento → evalúa respuesta → extrae citas → emite `evaluation.complete`
- **Métodos**: `on_candidate_response()`, `on_screening_complete()`, `evaluate_all_responses()`

#### 3. **HITLOrchestrationService**
- **Patrón**: Event-Driven (asincrónico) + Real-time updates
- **Escucha**: evento `evaluation.complete` (emitido por EvaluationEngine)
- **Flujo**: recibe evento → si score 50-80 → agrega a cola → notifica recruiter (SSE/polling)
- **Métodos**: `on_evaluation_complete()`, `on_recruiter_decision()`, `get_live_queue()`

#### 4. **ComplianceOrchestrationService**
- **Patrón**: Event-Driven (asincrónico)
- **Escucha**: TODOS los eventos (screening.started, response.submitted, evaluation.complete, decision.made)
- **Flujo**: recibe evento → registra en audit_logs append-only
- **Métodos**: `on_screening_started()`, `on_evaluation_complete()`, `on_recruiter_decision()`, `cleanup_old_data()`

#### 5. **ReEngagementOrchestrationService**
- **Patrón**: Scheduled (Background Job) + Event-Driven
- **Flujo**: Job cada 1 min → detecta sesiones >5 min inactivas → emite `session.abandoned` → programa emails 24h/48h
- **Métodos**: `detect_abandoned_sessions()`, `on_session_abandoned()`, `send_reengagement_24h()`, `on_session_resumed()`

### Patrones de Comunicación Inter-Componentes

#### Patrón 1: Event-Driven (Asincrónico)
```
BotEngine emite "CandidateResponseSubmitted"
    ↓ (Redis Pub/Sub + Celery task)
EvaluationEngine recibe y procesa
    ↓ emite "EvaluationComplete"
HITLService recibe y agrega a cola
    ↓ notifica recruiter
```
**Ventaja**: Loose coupling, escalable, easy agregar/remover subscribers

#### Patrón 2: Request-Reply (Sincrónico)
```
Frontend calls POST /screening/{session_id}/response
    ↓ (HTTP REST API)
ScreeningOrchestrationService ejecuta bloqueando
    ↓
Retorna siguiente pregunta (o feedback final)
```
**Ventaja**: Respuesta inmediata, UX consistente

#### Patrón 3: Database Polling (Fallback)
```
Frontend cada 5 segundos: GET /hitl/queue
    ↓ (HTTP REST API)
Backend retorna cola actualizada
```
**Ventaja**: Fallback si WebSocket no disponible

---

## FLUJOS DE DATOS CRÍTICOS

### Flujo 1: Screening Completo (Del Candidato a Evaluación)

```
┌─────────────────────────────────────┐
│ CANDIDATO INTERFACE (Frontend)      │
│ POST /screening/{session_id}/response
└────────────────────┬────────────────┘
                     │ response_text + session_id
                     ▼
    ┌────────────────────────────────────────┐
    │ ScreeningOrchestrationService          │
    │ .process_response()                    │
    └────────────────┬───────────────────────┘
                     │
          ┌──────────┼──────────┐
          │          │          │
          ▼          ▼          ▼
    ┌──────────┐ ┌─────────┐ ┌──────────────┐
    │BotEngine │ │Session  │ │ComplianceServ│
    │          │ │Manager  │ │              │
    │Process   │ │         │ │Register      │
    │response  │ │Save     │ │consent       │
    │Generate  │ │progress │ │              │
    │next Q    │ │Detect   │ │              │
    │Detect JB │ │abandon  │ │              │
    └──────────┘ └─────────┘ └──────────────┘
          │          │
          └────┬─────┘
               │
          ¿Screening completado?
               │
          Sí  ▼
    ┌──────────────────────────┐
    │EvaluationOrchestrationServ│
    │.evaluate_all_responses()  │
    │                           │
    │1. For each response:      │
    │   - evaluate_response()   │
    │   - extract_citation()    │
    │   - validate_fairness()   │
    │                           │
    │2. calculate_final_score() │
    │3. generate_recommendation()
    │4. emit "ScreeningEval.Cmplt" event
    └──────────────┬────────────┘
                   │
          ┌────────┴────────┐
          │                 │
          ▼                 ▼
    ┌──────────┐    ┌──────────────┐
    │HITLOrch. │    │ComplianceServ│
    │If 50-80: │    │Log immutable │
    │add_queue │    │              │
    └──────────┘    └──────────────┘
          │
          ▼
    ┌──────────────────────────┐
    │Frontend notificado:      │
    │Cola actualizada          │
    └──────────────────────────┘
```

### Flujo 2: Decisión Reclutador (HITL)

```
RECRUITER DASHBOARD
    │ Click "Aprobar" / "Rechazar"
    ▼
POST /hitl/decision
    │ decision + recruiter_id
    ▼
HITLOrchestrationService.on_recruiter_decision()
    │
    ├─ HITLService.process_decision() → guardar BD
    │
    ├─ emit "recruiter.decision.made" event
    │
    ├─ ComplianceService.on_recruiter_decision() → log immutable
    │
    └─ EmailService.on_recruiter_decision() → enviar notificación candidato
```

### Flujo 3: Abandonment + Re-engagement

```
Background Job (cada 1 minuto)
    │ ReEngagementOrchestrationService
    ▼
Scan Redis sesiones activas
    │ Check last_activity timestamp
    ▼
Si >5 min inactivo
    │ emit "session.abandoned"
    ▼
Schedule email #1 para 24h después
Schedule email #2 para 48h después
    │
Después 24 horas
    ▼
send_reengagement_24h()
    │ Send email + resume link
    ▼
Si candidato click resume
    │ emit "session.resumed"
    ▼
Restore exact context
Cancel pending emails
```

---

## ALMACENAMIENTO DE DATOS

### PostgreSQL (Relacional + Auditoría)
```
Tablas:
├── campaigns (ID, nombre, rubrica_id, knowledge_base_ids, link, creado)
├── candidates (ID, email, nombre, campaña_id)
├── sessions (ID, candidato_id, campaña_id, estado, created_at, completed_at)
├── screening_responses (ID, sesión_id, pregunta_id, respuesta_texto, timestamp)
├── evaluations (ID, respuesta_id, rúbrica_id, score, citas_json, timestamp)
├── decisions (ID, evaluación_id, reclutador_id, decisión, timestamp)
├── audit_logs (ID, evento, detalles_json, timestamp) [APPEND-ONLY]
├── consent_records (ID, candidato_id, timestamp, consentimiento_tipo)
└── rubrics (ID, campaña_id, criteria_json, version)
```

### Redis (Cache + Sesiones + Cola)
```
Keys:
├── session:{session_id} → {estado, respuestas, pregunta_actual} (TTL: 24h)
├── rubric:{rubric_id} → {criteria} (TTL: 7 días)
├── queue:pending → {lista candidatos score 50-80} (real-time)
└── reengagement:scheduled → {lista trabajos 24h/48h}
```

### S3 (Almacenamiento Objetos)
```
Buckets/Paths:
├── ticketdesk-transcriptions/
│   └── {campaign_id}/{session_id}/transcript.json
├── ticketdesk-knowledge-base/
│   └── {campaign_id}/{doc_id}/content.txt
└── ticketdesk-compliance-reports/
    └── {campaign_id}/{date}/report.pdf
```

---

## MATRIZ DE DEPENDENCIAS

### Llamadas Directas (Síncronas)
- ScreeningOrchestrationService → BotEngine (necesario para UX responsiva)
- ScreeningOrchestrationService → ComplianceService (necesario para registro consentimiento)
- SessionManager → BotEngine (necesario para restaurar contexto)

### Eventos (Asincrónicas)
- BotEngine → EvaluationEngine (evento `candidate.response.submitted`)
- EvaluationEngine → HITLService (evento `evaluation.complete`)
- EvaluationEngine → ComplianceService (evento `evaluation.complete`)
- Recruiter Decision → ComplianceService (evento `recruiter.decision.made`)
- Recruiter Decision → EmailService (evento `recruiter.decision.made`)
- SessionManager → ReEngagementService (evento `session.abandoned`)

### Validaciones
✅ **Sin dependencias circulares** — DAG correcto (Screening → Bot → Eval → HITL → Compliance)  
✅ **Responsabilidades segregadas** — Cada servicio tiene UN propósito claro  
✅ **Loose coupling** — Comunicación vía eventos, no llamadas directas  
✅ **Data consistency** — PostgreSQL ACID + audit logs inmutables

---

## DECISIONES TECNOLÓGICAS FINALES

| Decisión | Seleccionado | Justificación |
|----------|-------------|--------------|
| Frontend Framework | Next.js 14 | React moderna, SSR, Full-stack, routing integrado |
| Backend Language | Python + FastAPI | Prototipado rápido, excelente para API async, ecosistema ML/AI |
| Database Relacional | PostgreSQL | ACID, jurado, LGPD-friendly, auditoría sólida |
| Cache + Sesiones | Redis | In-memory rápido, Pub/Sub nativo, TTL automático |
| Object Storage | S3 | Escalable, barato, integración AWS nativa |
| LLM | Claude API (Anthropic) | Mejor para razonamiento complejo, excelentes guardrails |
| Message Queue | Celery + Redis | Integración FastAPI, workers escalables, eventos broadcast |
| State Management Frontend | Zustand | Ligero, API simple, perfecto para pequeños a medianos apps |
| Styling Frontend | Tailwind CSS | Utilidad-first, excelente compatibilidad con componentes |
| HTTP Client Frontend | React Query | Caching automático, sincronización estado servidor |
| Infraestructura | AWS ECS + Docker | Escalable, serverless-ready, LGPD zona São Paulo |
| Arquitectura Backend | Monolítica Modular | MVP rápido, migración a microservicios en v1.1 |
| Comunicación Real-time | Polling MVP → WebSocket v1.1 | MVP simple, upgrade a verdadero tiempo real después |

---

## PRÓXIMAS FASES

### Fase: Units Generation
**Objetivo**: Descomponer 6 Units of Work en work items específicos (stories, tasks)

**6 Units**:
1. **Unit 1**: Infraestructura (AWS, Docker, CI/CD) — Semanas 1-2
2. **Unit 2**: Fundamentos Backend (models, repos, middleware) — Semanas 2-4 [CRÍTICO]
3. **Unit 3**: BotEngine (conversación, guardrails) — Semanas 3-5
4. **Unit 4**: EvaluationEngine (scoring, auditoría) — Semanas 3-5
5. **Unit 5**: Frontend + Integración (Chat UI, Dashboard) — Semanas 3-5
6. **Unit 6**: Compliance + Re-engagement (auditoría, emails) — Semanas 4-5 [CRÍTICO]

**Crítica Path**: Unit 1 → Unit 2 → (Unit 3 || Unit 4 || Unit 5) → Unit 6

### Fase: Functional Design
**Objetivo**: Por cada Unit, definir flujos de negocio detallados, lógica por módulo

### Fase: NFR Design
**Objetivo**: Patrones para seguridad, performance, escalabilidad

### Fase: Infrastructure Design
**Objetivo**: CloudFormation/Terraform para AWS, CI/CD pipeline

### Fase: Construction
**Objetivo**: Implementación del código fuente

---

## CHECKLIST DE COMPLETITUD

### ✅ Artefactos de Diseño Completados

- [x] **components.md** — 6 componentes backend + 4 frontend definidos, 50+ métodos
- [x] **component-methods.md** — Firmas de métodos con tipos, pre/post-condiciones
- [x] **services.md** — 5 servicios de orquestación, patrones de comunicación
- [x] **component-dependency.md** — Matriz de dependencias, flujos de datos críticos
- [x] **application-design.md** — Consolidación (este documento)

### ✅ Decisiones de Diseño Confirmadas

- [x] Componentes organizados por característica (BotEngine, EvaluationEngine, etc.)
- [x] Patrón Event-Driven para loose coupling (BotEngine → Eval → HITL → Compliance)
- [x] Request-Reply para respuestas inmediatas (ScreeningOrchestration)
- [x] Database Polling como fallback si WebSocket no disponible
- [x] PostgreSQL + Redis + S3 como data layer
- [x] Auditoría inmutable con ComplianceService
- [x] Sin dependencias circulares (DAG validado)

### ✅ Validaciones Arquitectónicas

- [x] No hay ciclos de dependencia
- [x] Responsabilidades segregadas
- [x] Loose coupling via eventos
- [x] Data consistency ACID + audit
- [x] Immutability LGPD (append-only logs)
- [x] LGPD compliance (consentimiento, derecho olvido, retención 90d)

---

## APROBACIÓN FINAL

**Estado**: ✅ APLICACIÓN DISEÑADA COMPLETAMENTE

**Próximo paso**: User approves design artifacts → Procede a Units Generation phase

**Responsables**: Equipo de desarrollo (4-6 developers) puede ahora iniciar construcción basada en diseño establecido

---

**Artefactos Relacionados**:
- [components.md](./components.md) — Definiciones detalladas de componentes
- [component-methods.md](./component-methods.md) — Firmas de métodos
- [services.md](./services.md) — Servicios y orquestación
- [component-dependency.md](./component-dependency.md) — Matriz de dependencias y flujos

**Versión**: 1.0  
**Fecha**: 2026-05-27  
**Fase**: Inception - Application Design ✅ COMPLETADA
