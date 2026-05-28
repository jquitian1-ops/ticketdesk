# Generación de Units — TicketDesk Enterprise v1.0

**Descomposición de 6 Units of Work en Work Items**  
**Fecha**: 2026-05-27  
**Fase**: Inception - Units Generation  
**Estado**: En Generación

---

## VISIÓN GENERAL

6 Units of Work parallelizables (con dependencias críticas) se descomponen en **work items específicos** (user stories, tasks técnicas) que developers pueden ejecutar en sprints de 2 semanas.

**Timeline**: 10 semanas  
**Equipo**: 4-6 developers  
**Critical Path**: Unit1 → Unit2 → (Unit3 || Unit4 || Unit5) → Unit6

---

## UNIT 1: INFRAESTRUCTURA — Semanas 1-2

**Responsable**: 1 DevOps Engineer  
**Bloquea**: Unit 2, Unit 3, Unit 4, Unit 5, Unit 6 (todas dependen de infra lista)  
**Objetivo**: AWS ECS, Docker, CI/CD pipeline, bases de datos, monitoreo

### Work Items

#### 1.1 AWS Setup & VPC
- [x] Crear AWS Account / usar existente (São Paulo region)
- [x] VPC, subnets públicas/privadas (multi-AZ para HA)
- [x] Security Groups (PostgreSQL: 5432, Redis: 6379, FastAPI: 8000, Next.js: 3000)
- [x] NAT Gateway para egress privado
- [x] Certificados ACM para TLS

**Aceptación**: VPC operativo, security groups validados, ACM certificates activos

#### 1.2 PostgreSQL Setup
- [x] RDS PostgreSQL 15 (Multi-AZ, automated backups 30 días)
- [x] Database: `ticketdesk_prod`
- [x] Usuarios: app_user (read/write), readonly_user, admin_user
- [x] Parameter Groups configurados (max_connections=200, shared_buffers=256MB)
- [x] Monitoring CloudWatch (CPU, storage, connections)

**Aceptación**: BD operativa, backups confirmados, conexión desde app-server exitosa

#### 1.3 Redis Setup
- [x] ElastiCache Redis 7.0 (Single-node MVP, Multi-AZ en v1.1)
- [x] Parameter Groups (maxmemory-policy=allkeys-lru, timeout=300)
- [x] Subnet Group en VPC privada
- [x] Monitoring CloudWatch (CPU, evictions, connections)

**Aceptación**: Redis operativo, pub/sub testeable desde aplicación

#### 1.4 S3 Buckets
- [x] Bucket: `ticketdesk-transcriptions` (versioning ON, lifecycle 90 días → Glacier)
- [x] Bucket: `ticketdesk-knowledge-base` (versioning ON)
- [x] Bucket: `ticketdesk-compliance-reports` (versioning ON, lifecycle 2 años)
- [x] IAM role para ECS con acceso S3 (mínimo privilegio)
- [x] Encryption S3 (SSE-S3 o KMS)

**Aceptación**: 3 buckets operativos, uploads/downloads testables, lifecycle policies activos

#### 1.5 Docker & ECR
- [x] AWS ECR (Elastic Container Registry) setup
- [x] Dockerfile para FastAPI (Python 3.11, slim base image)
- [x] Dockerfile para Next.js (multi-stage build, optimizado producción)
- [x] docker-compose.yml local (PostgreSQL, Redis, FastAPI, Next.js)
- [x] GitHub Actions para build/push a ECR (trigger en push main)

**Aceptación**: Imágenes construidas y pusheadas a ECR, docker-compose levanta stack localmente

#### 1.6 ECS Cluster & Task Definitions
- [x] ECS Cluster `ticketdesk-prod` en EC2 (2 instances t3.medium como MVP)
- [x] Task Definition FastAPI (CPU: 512, Memory: 1024, image: ECR_URI)
- [x] Task Definition Next.js Frontend (CPU: 256, Memory: 512, image: ECR_URI)
- [x] Auto Scaling policies (scale up si CPU >70%, scale down si <30%)
- [x] Load Balancer ALB (health checks /health endpoint)

**Aceptación**: 2 task definitions operativas, ALB retorna 200 OK, escalado automático verificado

#### 1.7 CI/CD Pipeline (GitHub Actions)
- [x] `.github/workflows/build-backend.yml` (pytest, linting, build Docker)
- [x] `.github/workflows/build-frontend.yml` (npm lint, npm test, build Docker)
- [x] `.github/workflows/deploy-staging.yml` (deploy a ECS staging en merge PR)
- [x] `.github/workflows/deploy-production.yml` (deploy a ECS prod en merge main)
- [x] Environment secrets (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, etc.)

**Aceptación**: Pipeline ejecuta en cada push, deploys a staging/prod automatizados, rollback manual disponible

#### 1.8 Monitoring & Logging
- [x] CloudWatch Log Groups (`/ecs/ticketdesk-backend`, `/ecs/ticketdesk-frontend`)
- [x] CloudWatch Alarms (RDS CPU >80%, Redis evictions >1000, ECS task failures)
- [x] CloudWatch Dashboard (main metrics: ECS CPU, RDS CPU, Redis memory, ALB latency)
- [x] DataDog/New Relic opcional (MVP puede usar solo CloudWatch)

**Aceptación**: Logs centralizados, al menos 3 alarms configuradas, dashboard visible

#### 1.9 DNS & TLS
- [x] Route53 domain setup (ej: ticketdesk.com)
- [x] ALB hostname: api.ticketdesk.com → backend ECS
- [x] ALB hostname: app.ticketdesk.com → frontend ECS
- [x] ACM certificates (wildcard *.ticketdesk.com o individual)
- [x] HTTPS redirect (80 → 443)

**Aceptación**: app.ticketdesk.com carga frontend, api.ticketdesk.com retorna 200, HTTPS válido

#### 1.10 Local Development Environment
- [x] README.md con setup instructions (clone, docker-compose up, etc.)
- [x] `.env.example` file (DB_HOST, REDIS_URL, AWS_REGION, etc.)
- [x] Scripts útiles: `scripts/setup-db.sh`, `scripts/reset-db.sh`, `scripts/seed-data.sh`
- [x] Pre-commit hooks (linting, formatting)

**Aceptación**: Nuevo developer puede `docker-compose up` y tener stack operativo en 5 minutos

---

## UNIT 2: FUNDAMENTOS BACKEND — Semanas 2-4 [CRÍTICO]

**Responsables**: 2 Backend Engineers  
**Bloqueado por**: Unit 1  
**Bloquea**: Unit 3, Unit 4 (ambas necesitan models/repos establecidos)  
**Objetivo**: FastAPI skeleton, models, repositories, middleware, testing infrastructure

### Work Items

#### 2.1 FastAPI Project Setup
- [ ] `src/` directory structure
- [ ] `main.py` → FastAPI app initialization
- [ ] ASGI configuration (uvicorn, workers)
- [ ] Environment config (`config/settings.py`)
- [ ] Logging setup (Python logging, CloudWatch)

**Aceptación**: `python -m uvicorn src.main:app --reload` levanta servidor en 8000

#### 2.2 Database Models (SQLAlchemy)
- [ ] `src/models/campaign.py` (Campaign model)
- [ ] `src/models/candidate.py` (Candidate model)
- [ ] `src/models/session.py` (Session model)
- [ ] `src/models/response.py` (ScreeningResponse model)
- [ ] `src/models/evaluation.py` (Evaluation model)
- [ ] `src/models/decision.py` (Decision model)
- [ ] `src/models/audit_log.py` (AuditLog model — append-only)
- [ ] `src/models/consent.py` (ConsentRecord model)
- [ ] Migraciones Alembic

**Aceptación**: `alembic upgrade head` crea todas tablas en PostgreSQL, modelos testeables

#### 2.3 Repository Layer (Data Access)
- [ ] `src/repositories/base_repository.py` (CRUD base)
- [ ] `src/repositories/campaign_repository.py`
- [ ] `src/repositories/candidate_repository.py`
- [ ] `src/repositories/session_repository.py`
- [ ] `src/repositories/evaluation_repository.py`
- [ ] `src/repositories/audit_log_repository.py` (append-only logic)

**Aceptación**: Repos testeados, métodos CRUD funcionales, append-only constraint en audit_logs

#### 2.4 Middleware & Authentication
- [ ] `src/middleware/auth.py` (JWT token validation)
- [ ] `src/middleware/error_handling.py` (global exception handler)
- [ ] `src/middleware/logging.py` (request/response logging)
- [ ] `src/middleware/cors.py` (CORS configurado para frontend)
- [ ] Guard decorators (@require_auth, @require_recruiter_role)

**Aceptación**: Endpoints pueden usar @require_auth, CORS permite localhost:3000, errores retornan JSON

#### 2.5 Database Connection & Redis Integration
- [ ] `src/database.py` → PostgreSQL connection pool
- [ ] `src/cache.py` → Redis connection pool
- [ ] Health check endpoints: `/health`, `/health/db`, `/health/redis`
- [ ] Connection pooling configured (max_overflow=20)

**Aceptación**: Health checks retornan 200, puede conectar a BD y Redis

#### 2.6 Event System (Redis Pub/Sub + Celery)
- [ ] `src/events/event_bus.py` → Event publisher (wrapper Redis Pub/Sub)
- [ ] `src/events/event_types.py` → Enum de eventos (screening.started, candidate.response.submitted, etc.)
- [ ] `src/tasks/celery_app.py` → Celery app configuration
- [ ] `src/tasks/base_task.py` → Base task class con retry logic
- [ ] Event listener infrastructure (subscribers pueden decorar @event.listen("topic"))

**Aceptación**: Evento emitido en Redis es recibido por suscriptor Celery task

#### 2.7 Testing Infrastructure
- [ ] `tests/conftest.py` → pytest fixtures
- [ ] `tests/fixtures/database.py` → In-memory SQLite para tests
- [ ] `tests/fixtures/redis.py` → Mock Redis para tests
- [ ] `tests/fixtures/factories.py` → Factory Boy factories (CampaignFactory, CandidateFactory, etc.)
- [ ] GitHub Actions ejecuta pytest en cada push

**Aceptación**: `pytest` corre localmente sin BD/Redis real, >80% líneas cubiertas

#### 2.8 API Documentation & OpenAPI
- [ ] FastAPI auto-genera OpenAPI schema (`/docs`)
- [ ] Docstrings en endpoints
- [ ] Request/response Pydantic models documentados
- [ ] `docs/API.md` con ejemplos cURL/Python

**Aceptación**: `/docs` muestra todos endpoints, ejemplos ejecutables

#### 2.9 Dependency Injection Framework
- [ ] `src/di.py` → Simple DI container (inyecta repos, services, etc.)
- [ ] Services pueden inyectar repos sin tight coupling
- [ ] Fácil mockear dependencias en tests

**Aceptación**: Service constructor: `def __init__(self, campaign_repo: CampaignRepository)`

#### 2.10 Constants & Enums
- [ ] `src/constants.py` (scores: MIN_PASS=50, MAX_PASS=80, PASS>80, etc.)
- [ ] `src/enums.py` (DecisionType: APPROVE, REJECT, PENDING, CandidateStatus: SCREENING, COMPLETED, etc.)

**Aceptación**: Código usa enums en lugar de string literals

---

## UNIT 3: BOTENGINE — Semanas 3-5

**Responsable**: 1 Backend Engineer  
**Bloqueado por**: Unit 1 (infra), Unit 2 (models/repos)  
**Paralelo con**: Unit 4, Unit 5  
**Objetivo**: Conversación Claude API, guardrails (jailbreak, OOB detection)

### Work Items

#### 3.1 BotEngine Core Service
- [ ] `src/components/bot_engine/service.py` → BotEngine class
- [ ] `start_session(campaign_id, candidate_id) → SessionContext`
- [ ] `process_response(session_id, response_text) → ProcessResponseResult`
- [ ] Prompt templates sistema (base + rúbrica-specific)
- [ ] Adaptive follow-up logic (preguntas de clarificación basadas en respuesta)

**Aceptación**: start_session retorna primera pregunta, process_response retorna siguiente pregunta sin errores

#### 3.2 Claude API Integration
- [ ] `src/components/bot_engine/claude_client.py` → Wrapper Claude API
- [ ] Configuración: model="claude-3-5-sonnet-20241022", max_tokens=1000
- [ ] Retry logic con exponential backoff (1s, 2s, 4s, máx 3 intentos)
- [ ] Timeout handling (15 segundos por request)
- [ ] Logging de prompts/respuestas (para auditoría)
- [ ] Cost tracking (tokens usados)

**Aceptación**: Llamadas a Claude exitosas, retries funcionan, timeouts capturados

#### 3.3 Jailbreak Detection
- [ ] `src/components/bot_engine/guards/jailbreak_detector.py`
- [ ] Patrones regex para detectar: prompt injection, off-topic instructions, role-play requests
- [ ] Claude API system prompt con instrucciones de guardrail
- [ ] Respuesta estándar cuando jailbreak detectado ("Por favor, sigue las instrucciones...")
- [ ] Event: emit("bot.jailbreak_detected", {session_id, response_text})

**Aceptación**: Jailbreak attempts detectados y bloqueados, evento emitido

#### 3.4 Out-of-Scope Detection
- [ ] `src/components/bot_engine/guards/oob_detector.py`
- [ ] Regex patterns para OOB (preguntas sobre salary antes de eligibilidad, etc.)
- [ ] Optional: ML model para clasificación OOB (fine-tuned si presupuesto)
- [ ] Respuesta apropiada ("Esa pregunta está fuera del scope...")
- [ ] Event: emit("bot.out_of_scope_detected", {session_id, question})

**Aceptación**: OOB preguntas detectadas, evento emitido, respuesta apropiada

#### 3.5 Session State Management
- [ ] `src/components/bot_engine/session_manager.py` → save/load session context
- [ ] Save: {session_id, questions_asked, responses, current_question_index, metadata}
- [ ] Redis key: `session:{session_id}` (TTL: 24 horas)
- [ ] On resume: restaurar estado exacto
- [ ] Inactivity detection: check last_activity timestamp

**Aceptación**: Sessions persisten en Redis, resumen exacto al retomar, TTL funciona

#### 3.6 Transcription Management
- [ ] `src/components/bot_engine/transcription_service.py`
- [ ] Append respuesta a transcripción en Redis después cada response
- [ ] Estructura: {timestamp, question, response, evaluation_score (si aplica)}
- [ ] On screening complete: serialize a JSON
- [ ] Upload a S3: `s3://ticketdesk-transcriptions/{campaign_id}/{session_id}/transcript.json`
- [ ] Save metadata a PostgreSQL (sessions table: transcription_s3_url, transcription_size)

**Aceptación**: Transcripción completa en S3, metadata en BD, descargable para auditoría

#### 3.7 Question Management
- [ ] `src/components/bot_engine/question_service.py`
- [ ] Load rubric questions del PostgreSQL / Redis cache
- [ ] Generate next question basado en: current_index, campaign rubric, adaptive logic
- [ ] Handle branching logic (si respuesta A → preguntas 5-7, si respuesta B → preguntas 8-10)
- [ ] Max questions: 10 (configurable por campaña)

**Aceptación**: Preguntas cargadas correctamente, branching funciona, max respetado

#### 3.8 BotEngine API Endpoints
- [ ] `POST /api/screening/start` → ScreeningOrchestrationService
- [ ] `POST /api/screening/{session_id}/response` → ScreeningOrchestrationService
- [ ] `GET /api/screening/{session_id}/status` → estado sesión actual
- [ ] Request validation, error handling, logging

**Aceptación**: 3 endpoints testeados, request validation funciona, errores retornan JSON

#### 3.9 Testing BotEngine
- [ ] `tests/components/test_bot_engine.py` (unit tests)
- [ ] Mock Claude API (usar respuestas predefinidas)
- [ ] Test jailbreak detection (10+ patrones)
- [ ] Test OOB detection (10+ patrones)
- [ ] Test session persistence (Redis)
- [ ] >85% líneas cubiertas

**Aceptación**: pytest corre sin errores, coverage >85%

#### 3.10 Documentation
- [ ] BotEngine architecture doc (`docs/BotEngine.md`)
- [ ] Prompt templates documentados
- [ ] Guard rules documentadas
- [ ] API endpoint examples

**Aceptación**: Documentación legible, ejemplos ejecutables

---

## UNIT 4: EVALUATIONENGINE — Semanas 3-5

**Responsable**: 1 Backend Engineer  
**Bloqueado por**: Unit 1 (infra), Unit 2 (models/repos)  
**Paralelo con**: Unit 3, Unit 5  
**Objetivo**: Scoring, extracción citas, cálculo final score, recomendaciones

### Work Items

#### 4.1 EvaluationEngine Core Service
- [ ] `src/components/evaluation_engine/service.py` → EvaluationEngine class
- [ ] `evaluate_response(response_text, rubric) → EvaluationResult`
- [ ] `extract_citation(response_text, criterion) → CitationResult`
- [ ] `calculate_final_score(evaluations_list) → FinalScore`
- [ ] `generate_recommendation(final_score) → Recommendation`

**Aceptación**: Métodos ejecutables, tipos Pydantic definidos

#### 4.2 Rubric Loading & Caching
- [ ] `src/components/evaluation_engine/rubric_service.py`
- [ ] Load rubric desde PostgreSQL por campaign_id
- [ ] Cache en Redis: `rubric:{rubric_id}` (TTL: 7 días)
- [ ] Cache invalidation cuando rúbrica editada
- [ ] Fallback a DB si Redis miss

**Aceptación**: Rúbricas cargadas rápidamente, caché TTL respetado

#### 4.3 Scoring Engine
- [ ] `src/components/evaluation_engine/scoring_engine.py`
- [ ] Para cada criterion en rúbrica: score 0-100
- [ ] Scoring logic: Claude API evalúa respuesta contra criterion
- [ ] Output: {criterion_id, score, justification, citations}
- [ ] Aggregate score: promedio ponderado (weights definidos en rúbrica)

**Aceptación**: Scores calculados correctamente, justificaciones presentes

#### 4.4 Citation Extraction
- [ ] `src/components/evaluation_engine/citation_extractor.py`
- [ ] Dado response_text + criterion, extraer cita exacta (verbatim)
- [ ] Usar fuzzy matching (difflib, min_score=0.95)
- [ ] Si no match perfecto, buscar parafrase similar
- [ ] Retornar: {start_index, end_index, citation_text, confidence_score}

**Aceptación**: Citas extraídas correctamente, confidence score presente

#### 4.5 Fairness Validation
- [ ] `src/components/evaluation_engine/fairness_validator.py`
- [ ] Monitor bias indicators: mentions de edad, género, origen
- [ ] Flag si evaluación parece sesgada
- [ ] Opcional: trigger review reclutador si bias_score > threshold
- [ ] Event: emit("evaluation.bias_detected", {session_id, bias_score})

**Aceptación**: Bias flags generados, eventos emitidos

#### 4.6 Final Score Calculation
- [ ] `calculate_final_score(session_id)` → Promedia todos scores respuestas
- [ ] Decision logic:
  - Score >= 80: "AUTO_APPROVE"
  - Score 50-80: "REQUIRES_HITL"
  - Score < 50: "AUTO_REJECT"
- [ ] Save a PostgreSQL (evaluations table)

**Aceptación**: Score final calculado, decisión lógica correcta

#### 4.7 Recommendation Generation
- [ ] `generate_recommendation(final_score, citations, fairness_flags)` → Recommendation
- [ ] Recomendación textual para reclutador (puntos fuertes, débiles)
- [ ] Citas compiladas como soporte
- [ ] Avisos si bias detected

**Aceptación**: Recomendación útil, basada en datos

#### 4.8 EvaluationEngine Event Handler
- [ ] `src/components/evaluation_engine/event_handler.py`
- [ ] Suscrito a evento: `candidate.response.submitted` (emitido por BotEngine)
- [ ] Celery task: `evaluate_response_task(evaluation_id, response_text, rubric)`
- [ ] Emit evento: `evaluation.complete` (para HITLService)

**Aceptación**: Event handler recibe y procesa eventos correctamente

#### 4.9 Evaluation API Endpoints
- [ ] `POST /api/evaluation/submit` (trigger manual evaluation)
- [ ] `GET /api/evaluation/{evaluation_id}` (fetch resultado)
- [ ] `GET /api/evaluation/session/{session_id}/all` (todas evaluaciones sesión)

**Aceptación**: Endpoints testeados, retornan JSON correcto

#### 4.10 Testing EvaluationEngine
- [ ] `tests/components/test_evaluation_engine.py`
- [ ] Mock Claude API para scoring
- [ ] Test citation extraction (10+ samples)
- [ ] Test fairness detection (bias patterns)
- [ ] Test final score calculation
- [ ] >85% líneas cubiertas

**Aceptación**: pytest corre sin errores, coverage >85%

---

## UNIT 5: FRONTEND + INTEGRACIÓN — Semanas 3-5

**Responsable**: 2 Frontend Engineers  
**Bloqueado por**: Unit 1 (infra), Unit 2 (models/repos)  
**Paralelo con**: Unit 3, Unit 4  
**Objetivo**: Next.js application, CandidateInterface, RecruiterDashboard, integración API

### Work Items

#### 5.1 Next.js Project Setup
- [ ] `npx create-next-app@14 --typescript --tailwind`
- [ ] Directory structure: `src/pages`, `src/components`, `src/lib`, `src/hooks`, `src/store`
- [ ] Environment config (`.env.local` con NEXT_PUBLIC_API_URL=http://localhost:8000)
- [ ] Typescript strict mode enabled

**Aceptación**: `npm run dev` levanta servidor en 3000

#### 5.2 State Management (Zustand)
- [ ] `src/store/auth.ts` → User auth state (token, user info)
- [ ] `src/store/screening.ts` → Screening state (current_question, responses, session_id)
- [ ] `src/store/recruiter.ts` → Recruiter state (queue, selected_candidate)
- [ ] `src/store/ui.ts` → UI state (modals, notifications)

**Aceptación**: Stores funcionales, accesibles desde componentes

#### 5.3 HTTP Client (React Query + Axios)
- [ ] `src/lib/api-client.ts` → Axios instance (base URL, interceptores)
- [ ] `src/hooks/useApi.ts` → Custom hook para queries/mutations
- [ ] `src/hooks/useCandidateScreening.ts` → Hook específico screening
- [ ] `src/hooks/useRecruiterQueue.ts` → Hook específico HITL queue

**Aceptación**: API calls funcionan, caching/retries automáticos

#### 5.4 CandidateInterface - Chat UI
- [ ] `src/pages/screening/[session_id].tsx` → Chat layout
- [ ] `src/components/screening/ChatMessage.tsx` → Display pregunta/respuesta
- [ ] `src/components/screening/ChatInput.tsx` → Input textarea + enviar botón
- [ ] `src/components/screening/ProgressBar.tsx` → Muestra progreso (3 de 10)
- [ ] Styling Tailwind (modern, responsive, accesible)

**Aceptación**: Chat UI carga, preguntas muestran, input funciona

#### 5.5 CandidateInterface - Consent & Disclosure
- [ ] `src/pages/screening/start.tsx` → Pantalla inicial consent
- [ ] `src/components/screening/ConsentForm.tsx` → Checkbox LGPD consent
- [ ] `src/components/screening/DisclosureText.tsx` → Información candidato
- [ ] `src/lib/consent-service.ts` → Handle consent storage

**Aceptación**: Consent form muestra, puede marcar checklist

#### 5.6 CandidateInterface - Session Management
- [ ] Session start: POST /api/screening/start → recibe session_id + first_question
- [ ] Response submission: POST /api/screening/{session_id}/response → envía respuesta, recibe next_question
- [ ] Error handling: si API error, mostrar friendly message + retry button
- [ ] Inactivity warning: 4 min inactivo → mostrar "¿Aún aquí?" nudge

**Aceptación**: Full screening flow funciona, errores manejados gracefully

#### 5.7 RecruiterDashboard - Queue Display
- [ ] `src/pages/recruiter/queue.tsx` → Queue layout
- [ ] `src/components/recruiter/QueueList.tsx` → Listado candidatos (score 50-80)
- [ ] `src/components/recruiter/QueueItem.tsx` → Card per candidato (nombre, score, último update)
- [ ] Filtering: por campaña, por score range
- [ ] Sorting: por score, por fecha

**Aceptación**: Queue carga, items muestran, filtros funcionan

#### 5.8 RecruiterDashboard - Candidate Detail Panel
- [ ] `src/pages/recruiter/candidate/[candidate_id].tsx` → Detail view
- [ ] `src/components/recruiter/CandidateDetail.tsx` → Muestra transcripción completa
- [ ] `src/components/recruiter/EvaluationSummary.tsx` → Scores, citas, recomendación
- [ ] `src/components/recruiter/CandidateActions.tsx` → Approve/Reject botones

**Aceptación**: Detail panel carga, muestra transcripción + evaluación

#### 5.9 RecruiterDashboard - Real-time Updates
- [ ] Option A (MVP): Polling cada 5s en GET /api/recruiter/queue
- [ ] Option B (Future v1.1): WebSocket para updates verdadero real-time
- [ ] Para MVP, usar React Query refetchInterval: 5000
- [ ] Mostrar "last updated 2 minutos atrás"

**Aceptación**: Queue actualiza cada 5s sin full page reload

#### 5.10 CampaignManager - Campaign CRUD
- [ ] `src/pages/recruiter/campaigns.tsx` → Listado campañas
- [ ] `src/pages/recruiter/campaigns/[campaign_id]/edit.tsx` → Edit form
- [ ] `src/components/recruiter/CampaignForm.tsx` → Form (nombre, rúbrica, KB docs)
- [ ] Upload rúbrica: drag-drop JSON file
- [ ] Upload Knowledge Base: multi-file upload

**Aceptación**: CRUD campañas funciona, uploads funcionan

#### 5.11 Authentication & Layout
- [ ] `src/pages/login.tsx` → Login form (email/password)
- [ ] JWT token storage (localStorage, httpOnly cookie opcional)
- [ ] Protected routes (require login, role-based)
- [ ] `src/components/layout/Header.tsx` → Nav bar con user menu
- [ ] Logout button

**Aceptación**: Login funciona, sesión persiste, logout limpia token

#### 5.12 Styling & Theme
- [ ] Tailwind config: colors, spacing, fonts
- [ ] `src/styles/globals.css` → Global styles
- [ ] Dark mode support (opcional para MVP)
- [ ] Mobile responsive (media queries)

**Aceptación**: App se ve moderna, responsive en mobile

#### 5.13 Frontend API Integration Testing
- [ ] `tests/integration/screening.test.ts` → End-to-end screening flow
- [ ] Mock API responses usando MSW (Mock Service Worker)
- [ ] Test: start screening → responder preguntas → complete
- [ ] Test: recruiter queue → click candidato → see details

**Aceptación**: Integration tests pasan

#### 5.14 Error Handling & Loading States
- [ ] Loading skeletons en QueueList, CandidateDetail
- [ ] Error boundaries component
- [ ] Toast notifications para errores (usar react-toastify)
- [ ] Retry buttons en errores

**Aceptación**: UX graceful si errores, loading states presente

---

## UNIT 6: COMPLIANCE + RE-ENGAGEMENT — Semanas 4-5 [CRÍTICO]

**Responsables**: 2 Backend Engineers  
**Bloqueado por**: Unit 1, Unit 2, Unit 3 (depende de eventos Bot)  
**Objetivo**: Auditoría inmutable, LGPD compliance, re-engagement emails, HITL queue

### Work Items

#### 6.1 ComplianceService - Audit Logging
- [ ] `src/components/compliance_service/audit_logger.py`
- [ ] Suscrito a TODOS los eventos (screening.started, response.submitted, evaluation.complete, decision.made)
- [ ] Append-only insert a `audit_logs` PostgreSQL table
- [ ] Fields: {id, timestamp, event_type, actor_id, subject_id, details_json, ip_address, user_agent}
- [ ] NO UPDATE/DELETE constraints en tabla (immutable)

**Aceptación**: Audit logs creados inmutablemente, eventos correctamente registrados

#### 6.2 ComplianceService - Consent Management
- [ ] `src/components/compliance_service/consent_manager.py`
- [ ] `register_consent(candidate_id, consent_type, timestamp)` → insert a consent_records
- [ ] Handle consent withdrawal (soft delete con flag instead=true)
- [ ] Generate consent certificate (PDF, downloadable)

**Aceptación**: Consentimiento registrado, certificado generado

#### 6.3 ComplianceService - Data Retention & Deletion
- [ ] `src/components/compliance_service/retention_policy.py`
- [ ] Soft delete (flag deleted=true, no delete actual)
- [ ] Hard delete después 90 días (background job)
- [ ] `cleanup_old_data(days_retention=90)` scheduled nightly a 2 AM

**Aceptación**: Datos borrados después 90 días, soft delete funciona

#### 6.4 ComplianceService - LGPD Right to Forget
- [ ] `src/components/compliance_service/gdpr_service.py` (LGPD=GDPR equivalente)
- [ ] `request_data_export(candidate_id)` → Compilar ZIP con todos datos candidato
- [ ] `request_deletion(candidate_id)` → Soft delete inmediato
- [ ] Email confirmación al candidato

**Aceptación**: Data export genera ZIP, deletion funciona

#### 6.5 ComplianceService - Compliance Reporting
- [ ] `src/components/compliance_service/report_generator.py`
- [ ] `generate_compliance_report(campaign_id, date_range)` → PDF report
- [ ] Contenido: {total_screenings, total_evaluations, decisions_breakdown, avg_score, bias_flags}
- [ ] Upload a S3: `s3://ticketdesk-compliance-reports/{campaign_id}/{date}/report.pdf`

**Aceptación**: Reporte PDF generado, uploadado a S3

#### 6.6 ReEngagementService - Inactivity Detection
- [ ] `src/components/reengagement_service/inactivity_detector.py`
- [ ] Background job cada 1 minuto: scan Redis sesiones activas
- [ ] Check last_activity timestamp (desde session:{session_id})
- [ ] Si >5 min inactivo: emit evento "session.abandoned"
- [ ] Event: {session_id, candidate_id, abandon_timestamp}

**Aceptación**: Inactivity detectado, evento emitido correctamente

#### 6.7 ReEngagementService - Email Scheduling
- [ ] `src/components/reengagement_service/email_scheduler.py`
- [ ] On "session.abandoned" event: schedule 2 email tasks
- [ ] Task 1: send_reengagement_24h (24 horas después)
- [ ] Task 2: send_reengagement_48h (48 horas después)
- [ ] Use Celery tasks con delayed execution

**Aceptación**: Tasks scheduled, ejecutan en tiempos correctos

#### 6.8 ReEngagementService - Email Templates
- [ ] Email #1 (24h): "Hemos notado que dejaste tu screening sin completar. ¿Necesitas ayuda? [Resume Link]"
- [ ] Email #2 (48h): "Esta es la última oportunidad para completar tu screening. [Resume Link]"
- [ ] Template variables: {candidate_name, campaign_name, resume_url}
- [ ] Send via AWS SES o SendGrid

**Aceptación**: Emails generados con variables correctas

#### 6.9 HITLService - Queue Management
- [ ] `src/components/hitl_service/queue_manager.py`
- [ ] `add_to_queue(evaluation_id, candidate_id, score)` → insert a HITL queue
- [ ] `get_queue(campaign_id, recruiter_id)` → filtrar por campaña y permisos
- [ ] `remove_from_queue(queue_id)` (cuando reclutador toma decisión)

**Aceptación**: Queue operativa, filtros funcionan

#### 6.10 HITLService - Decision Recording
- [ ] `src/components/hitl_service/decision_recorder.py`
- [ ] `process_decision(queue_id, decision, recruiter_id, notes)` → insert a decisions table
- [ ] Fields: {id, queue_id, decision (APPROVE/REJECT), recruiter_id, decision_timestamp, notes}
- [ ] Emit evento: "recruiter.decision.made"

**Aceptación**: Decisión registrada, evento emitido

#### 6.11 HITLService - Candidate Notification
- [ ] `src/components/hitl_service/notification_service.py`
- [ ] On "recruiter.decision.made": send email a candidato
- [ ] Si APPROVE: "¡Felicitaciones! Tu aplicación fue aprobada. Nos contactaremos pronto."
- [ ] Si REJECT: "Gracias por tu interés. Desafortunadamente, no fue seleccionado."
- [ ] Include link a feedback (opcional)

**Aceptación**: Notificaciones enviadas, templates apropiados

#### 6.12 Compliance & HITL API Endpoints
- [ ] `POST /api/compliance/consent/register` → register consent
- [ ] `POST /api/compliance/data-export/request` → request data export
- [ ] `POST /api/compliance/deletion/request` → request deletion
- [ ] `GET /api/recruiter/queue` → get queue
- [ ] `POST /api/recruiter/decision` → submit decision
- [ ] `GET /api/compliance/report/{campaign_id}` → generate report

**Aceptación**: Todos endpoints testeados, retornan correctamente

#### 6.13 Testing Compliance & HITL
- [ ] `tests/components/test_compliance_service.py`
- [ ] `tests/components/test_reengagement_service.py`
- [ ] `tests/components/test_hitl_service.py`
- [ ] Test audit logging, consent, deletion, queue, decision
- [ ] Mock email service
- [ ] >85% líneas cubiertas

**Aceptación**: pytest corre sin errores, coverage >85%

#### 6.14 Integration Testing All Components
- [ ] `tests/integration/full_workflow.test.ts` (Python)
- [ ] End-to-end: candidato entra → responde → screening completa → evaluación → HITL queue → reclutador decide → notificación
- [ ] Verifica audit logs, consent records, emails scheduled

**Aceptación**: Full workflow test pasa

---

## RESUMEN FINAL: WORK ITEMS POR UNIT

| Unit | Work Items | Semanas | FTE | Critical |
|------|-----------|---------|-----|----------|
| **Unit 1** | 10 (AWS, Docker, CI/CD) | 1-2 | 1 | ✅ |
| **Unit 2** | 10 (FastAPI, Models, Repos) | 2-4 | 2 | ✅ |
| **Unit 3** | 10 (BotEngine) | 3-5 | 1 | ⏸️ |
| **Unit 4** | 10 (EvaluationEngine) | 3-5 | 1 | ⏸️ |
| **Unit 5** | 14 (Frontend) | 3-5 | 2 | ⏸️ |
| **Unit 6** | 14 (Compliance, HITL, Re-eng) | 4-5 | 2 | ✅ |
| **TOTAL** | **68 Work Items** | **10 weeks** | **4-6** | **3 critical** |

---

## DEPENDENCIAS CRÍTICAS

```
Week 1-2:
  ├─ Unit 1 MUST complete (blocks everything)
  
Week 2-4:
  ├─ Unit 2 MUST complete (blocks Units 3,4,5,6)
  
Week 3-5:
  ├─ Unit 3, 4, 5 PARALLEL (no dependencies between them)
  ├─ All 3 must ~complete by week 5
  
Week 4-5:
  └─ Unit 6 starts (depends on Units 2,3 events)
  └─ Unit 6 must complete by week 5
```

---

## CHECKLIST DE COMPLETITUD

- [x] All 6 Units decomposed
- [x] 68 work items defined
- [x] Acceptance criteria per item
- [x] Dependencies mapped
- [x] FTE allocation balanced
- [x] Ready for sprint planning

---

**Estado**: ✅ UNITS GENERATION COMPLETADA  
**Siguiente**: Functional Design (lógica negocio por Unit) + Construction (código)

**Versión**: 1.0  
**Fecha**: 2026-05-27  
**Fase**: Inception - Units Generation ✅ COMPLETADA
