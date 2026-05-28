# Dependencias de Componentes y Flujos de Datos — TicketDesk Enterprise

**Matriz de dependencias, patrones comunicación, flujos datos**  
**Fecha**: 2026-05-27

---

## MATRIZ DE DEPENDENCIAS

### Componentes Backend

```
                   BotEngine  EvalEngine  HITLService  ComplianceService  CampaignService  SessionManager
BotEngine              -        --          N/A            Calls            Calls           Calls
EvalEngine            N/A        -          --             Calls            N/A             N/A
HITLService           N/A        --          -              Calls            N/A             Calls
ComplianceService     N/A        N/A         N/A            -                N/A             N/A
CampaignService       Calls      Calls       N/A            N/A              -               N/A
SessionManager        Calls      N/A         N/A            Calls            N/A             -

Legend:
  - = Self
  N/A = No dependency
  Calls = Llamada síncrona directa
  -- = Pub/Sub event (asincrónico)
  Calls (sin --) = Sincrónico
```

### Dependencias Externas

```
Backend Components
├─ Claude API (BotEngine)
├─ PostgreSQL (todos)
├─ Redis (caché + sesiones)
├─ S3 (transcripciones, Knowledge Base)
├─ EmailService (notificaciones)
└─ KnowledgeBaseService (RAG)

Frontend Components
├─ Next.js 14 runtime
├─ TailwindCSS (UI styling)
├─ React Query (API calls)
├─ Zustand (state management)
└─ Backend APIs (all components)
```

---

## FLUJO DE DATOS PRINCIPAL

### Screening Candidato → Evaluación → HITL

```
┌─────────────────────────────────────────────────────────────┐
│                     CANDIDATO INTERFACE                      │
│  (Frontend: Next.js - Chat UI, consentimiento, feedback)    │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP POST /screening/response
                         ▼
┌─────────────────────────────────────────────────────────────┐
│         SCREENING ORCHESTRATION SERVICE                      │
│  (Coordina flujo screening, maneja estado)                  │
└────────────────────────┬────────────────────────────────────┘
                         │
          ┌──────────────┼──────────────┐
          │              │              │
          ▼              ▼              ▼
    ┌──────────┐  ┌──────────┐  ┌───────────────┐
    │ BotEngine│  │ Session  │  │ Compliance    │
    │          │  │ Manager  │  │ Service       │
    │ • Process│  │          │  │               │
    │   response│  │ • Save   │  │ • Register    │
    │ • Generate│  │   progress│  │   consent     │
    │   question│  │ • Detect │  │ • Log         │
    │ • Detect  │  │   abandon│  │   screening   │
    │   jailbreak│  │          │  │               │
    └──────────┘  └──────────┘  └───────────────┘
          │              │
          └──────────┬───┘
                     │
          ┌──────────▼─────────────┐
          │ If screening completed │
          └──────────┬─────────────┘
                     │
                     ▼
    ┌────────────────────────────────────────┐
    │   EVALUATION ORCHESTRATION SERVICE     │
    │   (Evalúa todas respuestas)           │
    └────────────────────────────────────────┘
                     │
          ┌──────────┴──────────┐
          │                     │
          ▼                     ▼
    ┌──────────────┐    ┌──────────────────┐
    │EvaluationEngine│   │ Compliance Service│
    │               │    │                  │
    │ • Score response│  │ • Log evaluation │
    │ • Extract cites│   │ • Validate fairness
    │ • Calculate final│  │ • Save auditoría │
    │   score        │    │                  │
    │ • Recommend    │    │                  │
    └──────────────┘    └──────────────────┘
          │
          │ Emit "EvaluationComplete"
          │
          ▼
    ┌───────────────────────────────────┐
    │   HITL ORCHESTRATION SERVICE      │
    │   (Si score 50-80: add to queue)  │
    └───────────────────────────────────┘
          │
          ▼
    ┌───────────────────────────────────┐
    │   RECRUITER DASHBOARD (Frontend)  │
    │   (Cola filtrada, panel decisión) │
    └───────────────────────────────────┘
```

---

## MATRIZ COMUNICACIÓN INTER-COMPONENTES

### BotEngine ↔ EvaluationEngine

**Tipo**: Event-Driven (asincrónico)

```
BotEngine emits: "CandidateResponseSubmitted"
                    ├─ session_id
                    ├─ question_id
                    ├─ response_text
                    └─ timestamp

EvaluationEngine subscribes (Celery task)
                    ├─ Receive event
                    ├─ Load rubric
                    ├─ Evaluate
                    └─ Emit "EvaluationComplete"
```

### EvaluationEngine ↔ HITLService

**Tipo**: Event-Driven (asincrónico)

```
EvaluationEngine emits: "EvaluationComplete"
                        ├─ evaluation_id
                        ├─ session_id
                        ├─ final_score
                        ├─ recommendation
                        └─ timestamp

HITLService subscribes (Celery task)
                        ├─ Check score
                        ├─ If 50-80: add_to_queue()
                        └─ Emit "QueueItemAdded"
```

### HITLService ↔ EmailService

**Tipo**: Event-Driven (asincrónico)

```
HITLService emits: "RecruiterDecision"
                   ├─ decision (approve/reject)
                   ├─ candidate_id
                   └─ timestamp

EmailService subscribes
                   ├─ Load candidate email
                   ├─ Render template
                   └─ Send email
```

### CandidateSessionManager ↔ BotEngine

**Tipo**: Sincrónico (REST API call)

```
SessionManager calls: BotEngine.get_session_context()
                      ├─ session_id
                      └─ returns: {questions, responses, current_question}
```

---

## ALMACENAMIENTO DE DATOS POR COMPONENTE

### PostgreSQL (Principal Datastore)

```
Tables:
├── campaigns
├── candidates
├── sessions
├── screening_responses
├── evaluations
├── citations
├── decisions
├── audit_logs (append-only)
├── consent_records
└── rubrics
```

### Redis (Cache + Sessions)

```
Keys:
├── session:{session_id} → SessionData (TTL: 24h)
├── rubric:{rubric_id} → RubricData (TTL: 7 días)
├── queue:pending → Cola HITL (real-time)
└── reengagement:scheduled → Re-engagement jobs
```

### S3 (Object Storage)

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

## FLUJOS DE DATOS ESPECÍFICOS

### Flujo 1: Almacenamiento Transcripción

```
BotEngine
    └─ Tras cada respuesta:
       1. Append a sesión contexto (Redis)
       2. On screening complete:
          a. Serialize transcripción (JSON)
          b. Upload a S3 (transcriptions bucket)
          c. Save metadata a PostgreSQL (sessions tabla)
          d. Emit "TranscriptionSaved" event
```

### Flujo 2: Caché Rúbricas

```
CampaignService
    └─ on rubric upload/update:
       1. Save a PostgreSQL (rubrics table)
       2. Serialize y upload a Redis (TTL 7 días)

EvaluationEngine
    └─ on evaluate request:
       1. Try Redis cache
       2. If miss: query PostgreSQL
       3. Update Redis cache
```

### Flujo 3: Session Context Recovery

```
CandidateSessionManager
    └─ on session resume:
       1. Check Redis session (if exists)
       2. Load last 10 responses
       3. Load current question index
       4. Call BotEngine.get_session_context()
       5. Restore exact state to frontend
```

### Flujo 4: Re-engagement Workflow

```
Background Job (every 1 min)
    └─ Detect inactivity:
       1. Scan Redis: sesiones activas
       2. Check last_activity timestamp
       3. If >5 min: emit "SessionAbandoned"
          
ComplianceService
    └─ on SessionAbandoned:
       1. Log event immutable
       2. Schedule re-engagement jobs

ReEngagementService
    └─ on 24h/48h triggers:
       1. Load candidate email
       2. Render email template
       3. Send via EmailService
       4. Update tracking DB
```

---

## ACOPLAMIENTO Y MODULARIDAD

### Bajo Acoplamiento (Event-Driven)

Componentes que **NO** dependen directamente:
- BotEngine → EvaluationEngine (via events)
- EvaluationEngine → HITLService (via events)
- HITLService → EmailService (via events)

**Ventaja**: Fácil add/remove subscribers, escalable

---

### Alto Acoplamiento (Justificado)

- ScreeningOrchestrationService → BotEngine (sincrónico, necesario para UX)
- SessionManager → BotEngine (sincrónico, para restore context)

**Justificación**: Respuestas inmediatas necesarias para candidato

---

## VALIDACIÓN CONSISTENCIA

### ✅ Verificaciones Pasadas

| Check | Resultado | Nota |
|-------|-----------|------|
| Dependencias circulares | ✅ No hay ciclos | BotEngine → Eval → HITL → Compliance (DAG correcto) |
| Responsabilidades segregadas | ✅ Cada servicio clara | BotEngine: conversación, Eval: scoring, HITL: cola, Compliance: auditoría |
| Loose coupling | ✅ Event-driven | Servicios descoplados via message queue |
| Data consistency | ✅ Múltiples checks | PostgreSQL ACID + audit logs |
| Immutability LGPD | ✅ Append-only logs | Audit table no permite UPDATE/DELETE |

---

## DIAGRAMA ARQUITECTURA GENERAL

```
┌────────────────────────────────────────────────────────────┐
│                    CLIENTE (Browser)                        │
│     CandidateInterface / RecruiterDashboard (React)        │
└────────────┬─────────────────────────────────┬─────────────┘
             │ HTTP/REST API                  │ Polling/SSE
             │                                 │
┌────────────▼──────────────────────────────────▼─────────────┐
│                  API GATEWAY (FastAPI)                       │
│     ScreeningOrchestration, HITLOrchestration, etc.        │
└────────────┬──────────────────────────────────┬─────────────┘
             │                                  │
┌────────────▼────────────┐    ┌────────────────▼──────────────┐
│   BACKEND COMPONENTS    │    │  MESSAGE QUEUE & CACHE        │
│                         │    │                               │
│ • BotEngine             │    │ • Celery (task queue)        │
│ • EvaluationEngine      │    │ • Redis (pub/sub, cache)     │
│ • HITLService           │    │                               │
│ • ComplianceService     │    └────────────────┬──────────────┘
│ • CampaignService       │                     │
│ • SessionManager        │                     │
└────────────┬────────────┘                     │
             │                                  │
             └──────────────────┬───────────────┘
                                │
┌───────────────────────────────▼───────────────────────────────┐
│                      DATA LAYER                               │
│                                                               │
│  ┌──────────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │   PostgreSQL     │  │    Redis     │  │       S3       │  │
│  │  (relational)    │  │   (cache)    │  │   (objects)    │  │
│  │                  │  │              │  │                │  │
│  │ • campaigns      │  │ • sessions   │  │ • transcriptions│ │
│  │ • evaluations    │  │ • rubrics    │  │ • knowledge_base│ │
│  │ • decisions      │  │ • queue      │  │ • reports      │  │
│  │ • audit_logs     │  │              │  │                │  │
│  └──────────────────┘  └──────────────┘  └────────────────┘  │
└───────────────────────────────────────────────────────────────┘
```

---

**Estado**: ✅ Dependencias mapeadas  
**Próxima**: application-design.md (consolidación final)
