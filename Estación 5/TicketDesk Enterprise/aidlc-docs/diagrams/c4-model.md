# Diagrama C4 — TicketDesk Enterprise v1.0

**C4 Model: Context (Level 1) y Containers (Level 2)**  
**Fecha**: 2026-05-27  
**Formato**: Mermaid.js

---

## C4 NIVEL 1: CONTEXTO DEL SISTEMA

Muestra TicketDesk Enterprise en relación con actores externos y sistemas.

```mermaid
graph TB
    subgraph "Actores Externos"
        Candidate["👤 Candidato<br/>(Aplicante)"]
        Recruiter["👨‍💼 Reclutador<br/>(Empresa HR)"]
        Admin["🔐 Admin<br/>(Operaciones)"]
    end

    subgraph "TicketDesk Enterprise"
        TDE["🎯 TicketDesk Enterprise<br/>Plataforma de Screening<br/>Automatizado con IA"]
    end

    subgraph "Sistemas Externos"
        Claude["🤖 Claude API<br/>(Anthropic)<br/>LLM para conversación"]
        Email["✉️ AWS SES<br/>Servicio de Email"]
        AWS["☁️ AWS Services<br/>(S3, RDS, Redis,<br/>ECS, CloudWatch)"]
    end

    %% Relaciones
    Candidate -->|Ingresa screening<br/>Responde preguntas<br/>Recibe decisión| TDE
    Recruiter -->|Revisa candidatos<br/>Toma decisiones<br/>Crea campañas| TDE
    Admin -->|Monitorea sistema<br/>Configura alertas<br/>Gestiona infraestructura| TDE

    TDE -->|Llamadas API<br/>Conversación IA<br/>Evaluación respuestas| Claude
    TDE -->|Envía notificaciones<br/>Re-engagement emails| Email
    TDE -->|Almacena datos<br/>Ejecuta aplicación<br/>Cachea sesiones| AWS

    style TDE fill:#4A90E2,stroke:#2E5C8A,color:#fff,stroke-width:3px
    style Candidate fill:#52C41A,stroke:#3A8A13,color:#fff
    style Recruiter fill:#1890FF,stroke:#0D47A1,color:#fff
    style Admin fill:#FF4D4F,stroke:#B72C2C,color:#fff
    style Claude fill:#722ED1,stroke:#531BAC,color:#fff
    style Email fill:#FA8C16,stroke:#B56C00,color:#fff
    style AWS fill:#13C2C2,stroke:#0B6B6B,color:#fff
```

**Descripción**:
- **Candidato**: Accede a screening (web), responde preguntas, recibe decisión vía email
- **Reclutador**: Utiliza dashboard para ver cola HITL, revisar evaluaciones, tomar decisiones
- **Admin**: Monitorea sistema, configura alertas, gestiona infraestructura AWS
- **Claude API**: LLM externa para conversación adaptativa del screening
- **AWS SES**: Servicio de email para notificaciones y re-engagement
- **AWS Services**: Infraestructura: S3, RDS (PostgreSQL), Redis, ECS, CloudWatch

---

## C4 NIVEL 2: CONTENEDORES

Muestra componentes principales dentro de TicketDesk Enterprise y cómo se comunican.

```mermaid
graph TB
    subgraph "Clientes"
        WebBrowser["🌐 Web Browser<br/>(Candidato)")
        RecruiterBrowser["🌐 Web Browser<br/>(Reclutador)"]
    end

    subgraph "Tier 1: Presentación (CDN + Load Balancing)"
        ALB["⚙️ AWS ALB<br/>(Application Load Balancer)<br/>Port 443 HTTPS<br/>Health Checks"]
    end

    subgraph "Tier 2: Aplicación"
        Frontend["📱 Frontend Container<br/>(Next.js 14)<br/>React + Zustand<br/>Port 3000<br/>- CandidateInterface<br/>- RecruiterDashboard<br/>- CampaignManager<br/>- CommonUI"]
        
        Backend["🔧 Backend Container<br/>(FastAPI + Python)<br/>Port 8000<br/>- BotEngine<br/>- EvaluationEngine<br/>- HITLService<br/>- ComplianceService<br/>- CampaignService<br/>- SessionManager"]
    end

    subgraph "Tier 3: Servicios & Orquestación"
        EventBus["📢 Event Bus<br/>(Redis Pub/Sub)<br/>Async Events:<br/>- response.submitted<br/>- evaluation.complete<br/>- decision.made"]
        
        TaskQueue["⏳ Task Queue<br/>(Celery + Redis)<br/>Background Jobs:<br/>- evaluate_response<br/>- send_email<br/>- detect_abandoned<br/>- cleanup_data"]
    end

    subgraph "Tier 4: Data Persistence"
        PostgreSQL["🗄️ PostgreSQL RDS<br/>(Multi-AZ)<br/>- candidates<br/>- sessions<br/>- responses<br/>- evaluations<br/>- decisions<br/>- audit_logs<br/>- consent_records"]
        
        Redis["💾 Redis Cache<br/>(ElastiCache)<br/>- session:{id}<br/>- rubric:{id}<br/>- queue:pending<br/>- reengagement:scheduled"]
        
        S3["📦 S3 Buckets<br/>- transcriptions/<br/>- knowledge-base/<br/>- compliance-reports/<br/>- redis-backups/"]
    end

    subgraph "Tier 5: Integración Externa"
        ClaudeAPI["🤖 Claude API<br/>(Anthropic)<br/>- generate_question<br/>- evaluate_response"]
        
        EmailService["✉️ Email Service<br/>(AWS SES)<br/>- send_notification<br/>- send_reengagement"]
        
        Monitoring["📊 CloudWatch<br/>(Monitoring & Logging)<br/>- Metrics<br/>- Logs<br/>- Alarms"]
    end

    %% Comunicación Frontend
    WebBrowser -->|HTTPS| ALB
    RecruiterBrowser -->|HTTPS| ALB
    ALB -->|HTTP 3000| Frontend
    ALB -->|HTTP 8000| Backend

    %% Frontend ↔ Backend
    Frontend -->|REST API| Backend
    Backend -->|HTTP 200 JSON| Frontend

    %% Backend ↔ Data Layer
    Backend -->|SQL Queries<br/>ACID Transactions| PostgreSQL
    Backend -->|GET/SET<br/>Pub/Sub| Redis
    Backend -->|PUT/GET<br/>Objects| S3

    %% Backend → Event Bus & Task Queue
    Backend -->|emit event| EventBus
    EventBus -->|subscribe| TaskQueue
    TaskQueue -->|async process| Backend

    %% Backend → External APIs
    Backend -->|POST /messages<br/>Claude API Calls| ClaudeAPI
    Backend -->|send_email()| EmailService
    Backend -->|CloudWatch API| Monitoring

    %% Inter-Container Communication
    EventBus ↔️|pub/sub| Redis
    TaskQueue ↔️|enqueue/dequeue| Redis

    %% Styling
    style ALB fill:#FF9C6E,stroke:#D66236,color:#000,stroke-width:2px
    style Frontend fill:#1890FF,stroke:#0D47A1,color:#fff,stroke-width:2px
    style Backend fill:#52C41A,stroke:#3A8A13,color:#fff,stroke-width:2px
    style EventBus fill:#FA8C16,stroke:#B56C00,color:#000,stroke-width:2px
    style TaskQueue fill:#FA8C16,stroke:#B56C00,color:#000,stroke-width:2px
    style PostgreSQL fill:#13C2C2,stroke:#0B6B6B,color:#fff,stroke-width:2px
    style Redis fill:#EB2F96,stroke:#991A5E,color:#fff,stroke-width:2px
    style S3 fill:#722ED1,stroke:#531BAC,color:#fff,stroke-width:2px
    style ClaudeAPI fill:#9254DE,stroke:#6C3DB0,color:#fff,stroke-width:2px
    style EmailService fill:#FF85C0,stroke:#C41340,color:#fff,stroke-width:2px
    style Monitoring fill:#FAAD14,stroke:#B88600,color:#000,stroke-width:2px
    style WebBrowser fill:#BFBFBF,stroke:#595959,color:#000
    style RecruiterBrowser fill:#BFBFBF,stroke:#595959,color:#000
```

**Descripción de Contenedores**:

### Tier 1: Load Balancing
- **ALB (Application Load Balancer)**: Distribuye tráfico HTTPS (443) a frontend y backend

### Tier 2: Aplicación
- **Frontend (Next.js)**:
  - React 18 con TypeScript
  - State: Zustand
  - Componentes: CandidateInterface (chat), RecruiterDashboard (queue), CampaignManager
  
- **Backend (FastAPI)**:
  - 6 componentes principales
  - REST API endpoints
  - Integración con Claude API, servicios externos

### Tier 3: Orquestación
- **Event Bus (Redis Pub/Sub)**: Comunicación asincrónica entre servicios
- **Task Queue (Celery)**: Procesos background (evaluaciones, emails, limpieza)

### Tier 4: Persistencia
- **PostgreSQL RDS**: BD relacional principal (tablas: candidates, sessions, evaluations, decisions, audit_logs)
- **Redis ElastiCache**: Caché en-memory (sesiones, rúbricas, cola HITL)
- **S3 Buckets**: Almacenamiento objetos (transcripciones, KB, reportes, backups)

### Tier 5: Integraciones
- **Claude API**: LLM para conversación y evaluación
- **Email Service (SES)**: Notificaciones y re-engagement
- **CloudWatch**: Monitoreo, logging, alarmas

---

## C4 NIVEL 2 DETALLADO: COMPONENTES BACKEND

Zoom in en Backend container mostrando los 6 componentes principales:

```mermaid
graph LR
    subgraph "FastAPI Backend (Port 8000)"
        subgraph "API Gateway"
            Router["🔀 Router<br/>(FastAPI Routes)<br/>- /screening/*<br/>- /recruiter/*<br/>- /compliance/*<br/>- /admin/*"]
        end

        subgraph "Componentes de Negocio"
            BE["🤖 BotEngine<br/>- start_session<br/>- process_response<br/>- detect_jailbreak<br/>- save_transcription"]
            
            EE["📊 EvaluationEngine<br/>- evaluate_response<br/>- extract_citation<br/>- calculate_final_score<br/>- validate_fairness"]
            
            HITL["👨‍💼 HITLService<br/>- add_to_queue<br/>- get_queue<br/>- process_decision<br/>- notify_candidate"]
            
            Compliance["🔐 ComplianceService<br/>- log_evaluation<br/>- register_consent<br/>- soft_delete_candidate<br/>- generate_report"]
            
            Campaign["📋 CampaignService<br/>- create_campaign<br/>- update_rubric<br/>- upload_kb<br/>- get_statistics"]
            
            Session["⏱️ SessionManager<br/>- create_session<br/>- detect_inactivity<br/>- resume_session<br/>- soft_pause"]
        end

        subgraph "Servicios de Orquestación"
            ScreeningOrch["🎯 ScreeningOrchestrationService"]
            EvalOrch["📈 EvaluationOrchestrationService"]
            HITLOrch["🎪 HITLOrchestrationService"]
            CompOrch["✅ ComplianceOrchestrationService"]
            ReEngOrch["📧 ReEngagementOrchestrationService"]
        end

        subgraph "Infraestructura"
            Auth["🔑 Authentication<br/>(JWT Middleware)"]
            Validation["✔️ Validation<br/>(Pydantic Models)"]
            Logging["📝 Logging<br/>(CloudWatch)"]
            ErrorHandling["⚠️ Error Handling<br/>(Global Handlers)"]
        end
    end

    %% Flujo
    Router --> ScreeningOrch
    Router --> HITLOrch
    
    ScreeningOrch --> BE
    ScreeningOrch --> Session
    ScreeningOrch --> Compliance

    BE -->|emit event| EvalOrch
    EvalOrch --> EE
    EvalOrch --> Compliance

    EvalOrch -->|emit event| HITLOrch
    HITLOrch --> HITL
    HITL -->|emit event| Compliance

    Session --> ReEngOrch
    Campaign --> BE

    Auth -.->|validate| Router
    Validation -.->|validate| Router
    Logging -.->|log| BE
    Logging -.->|log| EE
    ErrorHandling -.->|catch| Router

    style BE fill:#52C41A,stroke:#3A8A13,color:#fff
    style EE fill:#1890FF,stroke:#0D47A1,color:#fff
    style HITL fill:#FA8C16,stroke:#B56C00,color:#000
    style Compliance fill:#FF4D4F,stroke:#B72C2C,color:#fff
    style Campaign fill:#722ED1,stroke:#531BAC,color:#fff
    style Session fill:#EB2F96,stroke:#991A5E,color:#fff
    style Router fill:#FAAD14,stroke:#B88600,color:#000
    style ScreeningOrch fill:#13C2C2,stroke:#0B6B6B,color:#fff
    style EvalOrch fill:#13C2C2,stroke:#0B6B6B,color:#fff
    style HITLOrch fill:#13C2C2,stroke:#0B6B6B,color:#fff
    style CompOrch fill:#13C2C2,stroke:#0B6B6B,color:#fff
    style ReEngOrch fill:#13C2C2,stroke:#0B6B6B,color:#fff
    style Auth fill:#8C8C8C,stroke:#595959,color:#fff
    style Validation fill:#8C8C8C,stroke:#595959,color:#fff
    style Logging fill:#8C8C8C,stroke:#595959,color:#fff
    style ErrorHandling fill:#8C8C8C,stroke:#595959,color:#fff
```

---

## C4 NIVEL 2 DETALLADO: COMPONENTES FRONTEND

Zoom in en Frontend container mostrando componentes principales:

```mermaid
graph TB
    subgraph "Next.js Frontend (Port 3000)"
        subgraph "Páginas"
            ScreeningPage["📄 /screening/[id]<br/>Candidato screering"]
            QueuePage["📄 /recruiter/queue<br/>Reclutador queue"]
            CampaignPage["📄 /recruiter/campaigns<br/>Gestión campañas"]
            LoginPage["📄 /login<br/>Autenticación"]
        end

        subgraph "Componentes Principales"
            CandidateInt["📱 CandidateInterface<br/>- ChatMessage<br/>- ChatInput<br/>- ProgressBar<br/>- ConsentForm<br/>- DisclosureText"]
            
            RecruiterDash["👨‍💼 RecruiterDashboard<br/>- QueueList<br/>- QueueItem<br/>- CandidateDetail<br/>- EvaluationSummary<br/>- CandidateActions"]
            
            CampaignMgr["📋 CampaignManager<br/>- CampaignForm<br/>- RubricUpload<br/>- KnowledgeBaseUpload<br/>- CampaignList"]
            
            CommonUI["🎨 CommonUI<br/>- Header/NavBar<br/>- Modals<br/>- Toast Notifications<br/>- Loading Skeletons<br/>- ErrorBoundary"]
        end

        subgraph "State Management"
            AuthStore["🔑 Auth Store<br/>(Zustand)<br/>- user<br/>- token<br/>- role"]
            
            ScreeningStore["🎯 Screening Store<br/>- session_id<br/>- current_question<br/>- responses<br/>- progress"]
            
            RecruiterStore["👨‍💼 Recruiter Store<br/>- queue_items<br/>- selected_candidate<br/>- filters"]
            
            UIStore["🎨 UI Store<br/>- modals<br/>- notifications<br/>- loading_states"]
        end

        subgraph "HTTP & Caching"
            ApiClient["🌐 API Client<br/>(Axios)<br/>- Base URL<br/>- Interceptors<br/>- Token injection"]
            
            ReactQuery["💾 React Query<br/>- Caching<br/>- Refetching<br/>- Mutations<br/>- Polling (5s)"]
        end

        subgraph "Hooks Personalizados"
            UseScreening["🪝 useScreening()<br/>- start_screening<br/>- submit_response<br/>- resume_session"]
            
            UseQueue["🪝 useQueue()<br/>- fetch_queue<br/>- submit_decision<br/>- filter_queue"]
            
            UseAuth["🪝 useAuth()<br/>- login<br/>- logout<br/>- refresh_token"]
        end

        subgraph "Estilos & Utils"
            Tailwind["🎨 Tailwind CSS<br/>- Responsive<br/>- Dark mode (future)<br/>- Accessible"]
            
            Utils["🔧 Utilities<br/>- API helpers<br/>- Date formatting<br/>- Validation"]
        end
    end

    %% Flujo de Datos
    ScreeningPage --> CandidateInt
    QueuePage --> RecruiterDash
    CampaignPage --> CampaignMgr
    LoginPage --> CommonUI

    CandidateInt --> ScreeningStore
    RecruiterDash --> RecruiterStore
    CampaignMgr --> UIStore

    UseScreening --> ApiClient
    UseQueue --> ApiClient
    UseAuth --> ApiClient

    ApiClient --> ReactQuery
    ReactQuery --> AuthStore

    CommonUI -.->|decorates| CandidateInt
    CommonUI -.->|decorates| RecruiterDash
    CommonUI -.->|decorates| CampaignMgr

    Tailwind -.->|styles| CommonUI
    Utils -.->|helpers| CandidateInt
    Utils -.->|helpers| RecruiterDash

    style CandidateInt fill:#1890FF,stroke:#0D47A1,color:#fff
    style RecruiterDash fill:#52C41A,stroke:#3A8A13,color:#fff
    style CampaignMgr fill:#722ED1,stroke:#531BAC,color:#fff
    style CommonUI fill:#FAAD14,stroke:#B88600,color:#000
    style AuthStore fill:#EB2F96,stroke:#991A5E,color:#fff
    style ScreeningStore fill:#13C2C2,stroke:#0B6B6B,color:#fff
    style RecruiterStore fill:#13C2C2,stroke:#0B6B6B,color:#fff
    style UIStore fill:#13C2C2,stroke:#0B6B6B,color:#fff
    style ApiClient fill:#FF9C6E,stroke:#D66236,color:#000
    style ReactQuery fill:#FF9C6E,stroke:#D66236,color:#000
    style UseScreening fill:#95DE64,stroke:#5B8C00,color:#000
    style UseQueue fill:#95DE64,stroke:#5B8C00,color:#000
    style UseAuth fill:#95DE64,stroke:#5B8C00,color:#000
    style Tailwind fill:#8C8C8C,stroke:#595959,color:#fff
    style Utils fill:#8C8C8C,stroke:#595959,color:#fff
```

---

## LEYENDA

### Colores por Tipo
- 🔵 **Azul**: Componentes Frontend / APIs HTTP
- 🟢 **Verde**: Componentes Backend / Lógica
- 🟠 **Naranja**: Servicios Externos / APIs
- 🟣 **Púrpura**: Integraciones / APIs
- 🟤 **Gris**: Infraestructura / Utilities
- 🔴 **Rojo**: Seguridad / Compliance

### Patrones de Comunicación
- **→** (Flecha sólida): Comunicación sincrónica / HTTP
- **→** (Flecha punteada): Inyección de dependencias / decoración
- **↔️** (Doble flecha): Pub/Sub o bidireccional

---

## FLUJOS DE DATOS CLAVE

### Flujo 1: Screening Candidato
```
WebBrowser → ALB → Frontend (Chat UI)
          ↓
Frontend → Backend (/api/screening/start)
          ↓
Backend → BotEngine → Claude API
        → SessionManager → Redis
        → ComplianceService → PostgreSQL (audit)
          ↓
Backend → Frontend (first_question)
          ↓
Candidato responde
          ↓
Frontend → Backend (/api/screening/{id}/response)
          ↓
Backend → EventBus (emit: candidate.response.submitted)
          ↓
EvaluationEngine (async) → EvaluationService → PostgreSQL
          ↓
EventBus (emit: evaluation.complete)
          ↓
HITLOrchestration → check score
  ├─ If 50-80: add_to_queue → Redis, notify recruiter
  ├─ If >80: auto_approve → notify candidate
  └─ If <50: auto_reject → notify candidate
```

### Flujo 2: Decisión Reclutador
```
RecruiterBrowser → ALB → Frontend (RecruiterDashboard)
                 ↓
Frontend (polling) → Backend (/api/recruiter/queue)
                   ↓
Backend → Redis (queue:pending) → Frontend (QueueList)
                   ↓
Reclutador selecciona candidato
                   ↓
Frontend → Backend (/api/recruiter/candidate/{id})
         ↓
Backend → PostgreSQL (fetch evaluations + citations)
        → Frontend (CandidateDetail)
                   ↓
Reclutador clicks "Aprobar" / "Rechazar"
                   ↓
Frontend → Backend (POST /api/recruiter/decision)
         ↓
Backend → HITLService (process_decision)
        → PostgreSQL (save decision)
        → EventBus (emit: recruiter.decision.made)
          ├─ ComplianceService → audit_logs
          └─ EmailService → send notification
        → Frontend (update queue, remove item)
```

### Flujo 3: Re-engagement (Background Job)
```
Celery Worker (every 1 min) → detect_abandoned_sessions
                           ↓
Check Redis: session:{id} last_activity
                           ↓
If >5 min inactivo:
  ├─ emit: session.abandoned
  ├─ Schedule: send_reengagement_24h (Celery task)
  └─ Schedule: send_reengagement_48h (Celery task)
                           ↓
24 horas después:
  ├─ Task executes
  ├─ Load candidate + session
  ├─ Render email template
  └─ Send via EmailService (SES)
                           ↓
Candidato clica resume link
  ├─ Frontend: resume_session endpoint
  ├─ Backend: restore context
  └─ Cancel pending re-engagement tasks (Celery.revoke)
```

---

## PERSPECTIVA TÉCNICA: COMUNICACIÓN ENTRE CONTENEDORES

| Origen | Destino | Protocolo | Tipo | Ejemplo |
|--------|---------|-----------|------|---------|
| Frontend | Backend | HTTPS/REST | Sincrónico | POST /api/screening/{id}/response |
| Backend | Claude API | HTTPS | Sincrónico | /v1/messages (Claude SDK) |
| Backend | PostgreSQL | TCP:5432 | Sincrónico | SELECT * FROM evaluations |
| Backend | Redis | TCP:6379 | Sincrónico + Async | PUBLISH, GET, SET |
| Backend | S3 | HTTPS | Sincrónico | PutObject, GetObject |
| Backend | Email Service | SMTP:587 | Asincrónico | SendEmail (Celery) |
| Backend | CloudWatch | HTTPS | Asincrónico | PutMetricData, PutLogEvents |
| Celery Worker | Redis | TCP:6379 | Sincrónico | Dequeue tasks, pub/sub |
| Frontend | HTTP Cache | Memory | Sincrónico | React Query (in-memory) |

---

**Generado**: 2026-05-27  
**Formato**: Mermaid.js (compatible con GitHub, GitLab, Notion, Confluence)  
**Nivel de Detalle**: C4 Models (Context + Containers)

