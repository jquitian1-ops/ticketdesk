# 📅 Estación 7 — Guía de Ejecución Detallada

**Proyecto**: TicketDesk Enterprise v1.0  
**Propósito**: Plan ejecutivo de 4 semanas para implementar TicketDesk usando agentes  
**Fecha**: 2026-05-27  
**Estado**: ✅ Listo para ejecución inmediata

---

## 📋 Resumen Ejecutivo

**Estación 7** ejecuta la implementación de TicketDesk en **4 sprints (4 semanas)**, usando 4 agentes especializados coordinados por ORCHESTRATOR.

```
TIMELINE EJECUTIVO:

Semana 1 (May 27 - Jun 02): Unit 1 + Unit 6 (Base + Compliance)
  → Deploy v0.1.0 a staging

Semana 2 (Jun 03 - Jun 09): Unit 2 (Session Management)
  → Deploy v0.2.0 a staging

Semana 3 (Jun 10 - Jun 16): Unit 3 + Unit 4 (BotEngine + Evaluation)
  → Deploy v0.3.0 a staging

Semana 4 (Jun 17 - Jun 23): Unit 5 (Frontend) + E2E + Prod
  → Deploy v1.0.0 a producción

ENTREGA FINAL: Viernes 23 de Junio 2026
```

---

## 📊 Matriz de Agentes × Tareas

```
AGENTES ASIGNADOS:

ORCHESTRATOR:   Planificación, sincronización, integración
ENGINEER-1:     Backend (Unit 1, 2, 3, 4)
ENGINEER-2:     Frontend (Unit 5) + DevOps
QA:             Testing, validación, security
ARCHITECT:      Review, ADRs, design validation

CAPACIDAD:
- ENGINEER-1: 40 horas/semana
- ENGINEER-2: 40 horas/semana
- QA:         30 horas/semana (validación + integración)
- ARCHITECT:  15 horas/semana (review + decisions)
- ORCHESTRATOR: 20 horas/semana (planning + sync)
```

---

## 🔴 SEMANA 1 (27 May - 2 June)

### Sprint 1: Fundación (Unit 1 + Unit 6)

**Objetivo**: Implementar autenticación, RBAC, y framework de compliance

#### Tarea 1.1: Database Schema (Unit 1)

```
ASIGNADO: ENGINEER-1
DURACIÓN: 8 horas (Lunes-Martes)
DEPENDENCIA: Ninguna

DESCRIPCIÓN:
  Crear esquema PostgreSQL con:
  - users (id, email, password_hash, role, created_at)
  - roles (id, name, permissions[])
  - sessions (id, user_id, token, expires_at)
  - audit_logs (id, user_id, action, resource, timestamp)

ENTREGABLES:
  ✓ backend/migrations/001_initial_schema.py (Alembic)
  ✓ SQL validado en psql
  ✓ Indexes creados (user.email, sessions.user_id, audit_logs.timestamp)
  ✓ Tests: test_db_schema_creates_tables.py

VALIDACIÓN (QA):
  ✓ Migration ejecuta sin errores
  ✓ Schema matches DESIGN.md requirements
  ✓ Indexes presentes y efectivos

ARTEFACTOS ENTREGADOS:
  - PR #1: "feat: initial database schema"
  - Tests: 8 tests (schema validation)
  - MEMORY.md: ENGINEER-1-TASK-1.1-COMPLETE
```

#### Tarea 1.2: User Aggregate + Repository

```
ASIGNADO: ENGINEER-1
DURACIÓN: 12 horas (Martes-Miércoles)
DEPENDENCIA: Task 1.1 (schema)

DESCRIPCIÓN:
  Implementar agregado User (DDD):
  - User class (id, email, password, role, created_at)
  - password_hash() con bcrypt (rounds=12)
  - validate_email() regex
  - UserRepository (CRUD)

CÓDIGO:
  backend/app/users/models.py:
    class User(Base):
      id: UUID
      email: str
      password_hash: str
      role: str
      created_at: datetime

  backend/app/users/repository.py:
    class UserRepository:
      def create(user: User) → User
      def get_by_id(id: UUID) → User | None
      def get_by_email(email: str) → User | None
      def update(id: UUID, updates: dict) → User
      def delete(id: UUID) → None

ENTREGABLES:
  ✓ User aggregate (models.py)
  ✓ UserRepository con SQLAlchemy ORM
  ✓ Unit tests: 15 tests (validations, CRUD)
  ✓ Integration tests: 5 tests (DB)

VALIDACIÓN (QA):
  ✓ pytest tests/unit/test_user_model.py -v (15/15 pass)
  ✓ pytest tests/integration/test_user_repository.py -v (5/5 pass)
  ✓ Coverage: 92%
  ✓ mypy: 0 errors
  ✓ pylint: score > 8.0

ARTEFACTOS:
  - PR #2: "feat: user aggregate and repository"
  - Tests: 20 tests (unit + integration)
  - MEMORY.md: ENGINEER-1-TASK-1.2-COMPLETE
```

#### Tarea 1.3: Authentication Service (JWT RS256)

```
ASIGNADO: ENGINEER-1
DURACIÓN: 10 horas (Miércoles-Jueves)
DEPENDENCIA: Task 1.2 (User)

DESCRIPCIÓN:
  Implementar JWT RS256 authentication:
  - Generate keypair (private/public)
  - Token creation (exp: 15min)
  - Token validation
  - Refresh token rotation

CÓDIGO:
  backend/app/auth/service.py:
    class AuthService:
      def create_token(user_id: str, exp_minutes: int = 15) → str
      def validate_token(token: str) → dict | None
      def refresh_token(refresh_token: str) → str

  API endpoints:
    POST /auth/login (email, password) → {access_token, refresh_token}
    POST /auth/refresh (refresh_token) → {access_token}
    POST /auth/logout (token) → 200

ENTREGABLES:
  ✓ AuthService (JWT RS256)
  ✓ API endpoints (3: login, refresh, logout)
  ✓ Unit tests: 10 tests
  ✓ Integration tests: 5 tests

VALIDACIÓN (QA):
  ✓ Tokens válidos verifican correctamente
  ✓ Tokens expirados son rechazados
  ✓ Coverage: 88%
  ✓ Integración con User: correcta

ARTEFACTOS:
  - PR #3: "feat: jwt rs256 authentication"
  - Tests: 15 tests
  - MEMORY.md: ENGINEER-1-TASK-1.3-COMPLETE
```

#### Tarea 1.4: RBAC (Role-Based Access Control)

```
ASIGNADO: ENGINEER-1
DURACIÓN: 8 horas (Jueves)
DEPENDENCIA: Task 1.2 (User with roles)

DESCRIPCIÓN:
  Implementar RBAC con 3 roles:
  - admin: manage users, view all data
  - recruiter: create/edit sessions, view candidates
  - candidate: view own session, answer questions

CÓDIGO:
  backend/app/auth/rbac.py:
    def require_role(required_role: str):
      """Decorator para validar rol en endpoints"""
      def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
          user = get_current_user()
          if user.role != required_role:
            raise PermissionError(...)
          return func(*args, **kwargs)
        return wrapper
      return decorator

  Uso:
    @router.post("/api/users")
    @require_role("admin")
    def create_user(user_data: UserCreate):
      ...

ENTREGABLES:
  ✓ RBAC decorator
  ✓ 3 roles definidos (admin, recruiter, candidate)
  ✓ Unit tests: 8 tests (role validation)

VALIDACIÓN (QA):
  ✓ Non-admin no puede crear users
  ✓ Non-recruiter no puede crear sessions
  ✓ Coverage: 90%

ARTEFACTOS:
  - PR #4: "feat: role-based access control"
  - Tests: 8 tests
  - MEMORY.md: ENGINEER-1-TASK-1.4-COMPLETE
```

#### Tarea 1.5: Unit 6 - Audit Logging Framework

```
ASIGNADO: ENGINEER-1
DURACIÓN: 10 horas (Lunes-Jueves paralelo)
DEPENDENCIA: Task 1.1 (audit_logs table)

DESCRIPCIÓN:
  Implementar audit trail para LGPD compliance:
  - AuditLog aggregate (timestamp, user_id, action, resource_id, changes)
  - Middleware para capturar todos los cambios
  - Soft-delete handler (lógica para LGPD <24h)

CÓDIGO:
  backend/app/compliance/audit.py:
    class AuditLog(Base):
      id: UUID
      timestamp: datetime
      user_id: UUID
      action: str  # create, update, delete
      resource: str  # users, sessions, evaluations
      resource_id: UUID
      changes: dict  # {before: {field: old}, after: {field: new}}
      ip_address: str

    async def log_audit(
      user_id: UUID,
      action: str,
      resource: str,
      resource_id: UUID,
      changes: dict = None
    ) → AuditLog

  Middleware:
    @app.middleware("http")
    async def audit_middleware(request, call_next):
      response = await call_next(request)
      if response.status_code in [200, 201]:
        await log_audit(...)
      return response

ENTREGABLES:
  ✓ AuditLog aggregate
  ✓ Audit middleware
  ✓ Unit tests: 12 tests

VALIDACIÓN (QA):
  ✓ Todos los cambios logeados
  ✓ PII no aparece en logs (masked)
  ✓ Coverage: 90%

ARTEFACTOS:
  - PR #5: "feat: audit logging for lgpd compliance"
  - Tests: 12 tests
  - MEMORY.md: ENGINEER-1-TASK-1.5-COMPLETE
```

#### Tarea 1.6: Docker Setup + CI/CD Pipeline

```
ASIGNADO: ENGINEER-2 (DevOps)
DURACIÓN: 12 horas (Lunes-Martes)
DEPENDENCIA: Ninguna

DESCRIPCIÓN:
  Configurar stack Docker + GitHub Actions:
  - Dockerfile para backend (multi-stage)
  - docker-compose.yml (postgres, redis)
  - .github/workflows/deploy.yml (6 stages)

ENTREGABLES:
  ✓ Dockerfile optimizado (< 800MB image)
  ✓ docker-compose.yml con health checks
  ✓ GitHub Actions workflow (lint → test → build → deploy-staging)
  ✓ ECR registry setup

VALIDACIÓN (QA):
  ✓ Docker build completa sin errores
  ✓ docker-compose up funciona
  ✓ CI/CD pipeline ejecuta sin errores

ARTEFACTOS:
  - PR #6: "chore: docker and ci/cd setup"
  - Files: Dockerfile, docker-compose.yml, .github/workflows/deploy.yml
  - MEMORY.md: ENGINEER-2-TASK-1.6-COMPLETE
```

#### Checklist Semana 1

```
☐ LUNES (27 May):
  ☐ 09:00 ORCHESTRATOR: Sprint 1 planning
  ☐ 10:00 ENGINEER-1: Comienza Task 1.1 (schema)
  ☐ 10:00 ENGINEER-2: Comienza Task 1.6 (Docker)

☐ MARTES (28 May):
  ☐ 09:00 ENGINEER-1: Task 1.1 completado, PR review
  ☐ 09:00 QA: Valida schema (Tarea 1.1)
  ☐ 10:00 ENGINEER-1: Comienza Task 1.2 (User aggregate)

☐ MIÉRCOLES (29 May):
  ☐ 09:00 QA: Valida User + Repo (Task 1.2)
  ☐ 10:00 ENGINEER-1: Comienza Task 1.3 (Auth)
  ☐ 14:00 ARCHITECT: Review Task 1.2 (aggregate pattern)

☐ JUEVES (30 May):
  ☐ 09:00 QA: Valida Auth (Task 1.3)
  ☐ 10:00 ENGINEER-1: Comienza Task 1.4 (RBAC)
  ☐ 14:00 ARCHITECT: Review Task 1.3
  ☐ 15:00 ORCHESTRATOR: Sync progress

☐ VIERNES (31 May):
  ☐ 09:00 QA: Valida RBAC + Audit (Task 1.4, 1.5)
  ☐ 10:00 ENGINEER-2: Task 1.6 completado
  ☐ 14:00 ARCHITECT: Review Tasks 1.4, 1.5, 1.6
  ☐ 15:00 ORCHESTRATOR: Merge PRs 1-6 → main
  ☐ 16:00 ORCHESTRATOR: Tag v0.1.0
  ☐ 17:00 ORCHESTRATOR: Deploy v0.1.0 a staging

☐ SÁBADO (1 June):
  ☐ 09:00 QA: Smoke tests en staging
  ☐ 10:00 ORCHESTRATOR: Valida deployment

ENTREGA SEMANA 1:
  ✓ v0.1.0 deployed a staging
  ✓ 70+ tests creados y pasando
  ✓ Coverage: 88%
  ✓ Smoke tests: passing
```

---

## 🟠 SEMANA 2 (3 June - 9 June)

### Sprint 2: Session Management (Unit 2)

**Objetivo**: Implementar agregado Session, repositorio, endpoints y scoring básico

#### Tarea 2.1: Session Schema + Migration

```
ASIGNADO: ENGINEER-1
DURACIÓN: 6 horas (Lunes)
DEPENDENCIA: v0.1.0 (Unit 1)

DESCRIPCIÓN:
  Crear tabla sessions:
  - id (UUID)
  - account_id (FK users)
  - candidate_email (VARCHAR, masked en logs)
  - status (enum: pending, screening, evaluated, rejected, hired)
  - created_at, updated_at, deleted_at (soft-delete)
  - initial_score, final_score
  - message_history (JSONB)

ENTREGABLES:
  ✓ Alembic migration
  ✓ Validada en DB
  ✓ Indexes: (account_id, status), (candidate_email), (deleted_at)

VALIDACIÓN (QA):
  ✓ Migration ejecuta sin errores
  ✓ Indexes presentes

ARTEFACTOS:
  - PR #7: "feat: session schema migration"
```

#### Tarea 2.2: Session Aggregate

```
ASIGNADO: ENGINEER-1
DURACIÓN: 12 horas (Lunes-Martes)
DEPENDENCIA: Task 2.1

DESCRIPCIÓN:
  Implementar agregado Session:
  - Session (id, account_id, candidate_email, status, messages, scores)
  - Validación: email debe ser válido
  - State machine: pending → screening → evaluated
  - add_message(role: str, content: str)
  - score() → initial_score

CÓDIGO:
  backend/app/sessions/models.py:
    class Session(Base):
      id: UUID
      account_id: UUID  # FK users
      candidate_email: str
      status: str  # state machine
      messages: list  # [{role, content, timestamp}]
      initial_score: float = None
      final_score: float = None
      deleted_at: datetime = None

      def add_message(role: str, content: str) → Message
      def validate_candidate_email() → bool
      def score() → float

ENTREGABLES:
  ✓ Session aggregate (models.py)
  ✓ State machine validation (pending → screening → evaluated)
  ✓ Message validation
  ✓ Unit tests: 16 tests

VALIDACIÓN (QA):
  ✓ pytest tests/unit/test_session_model.py (16/16 pass)
  ✓ Coverage: 90%
  ✓ mypy: 0 errors

ARTEFACTOS:
  - PR #8: "feat: session aggregate"
  - Tests: 16 tests
```

#### Tarea 2.3: SessionRepository + Service Layer

```
ASIGNADO: ENGINEER-1
DURACIÓN: 10 horas (Martes-Miércoles)
DEPENDENCIA: Task 2.2

DESCRIPCIÓN:
  Implementar repository pattern + service layer:
  - SessionRepository (CRUD, query by account_id, status)
  - SessionService (business logic)
  - Soft-delete con cleanup Celery task

CÓDIGO:
  backend/app/sessions/repository.py:
    class SessionRepository:
      def create(account_id: UUID, candidate_email: str) → Session
      def get_by_id(id: UUID) → Session
      def list_by_account(account_id: UUID, status: str = None) → List[Session]
      def update(id: UUID, updates: dict) → Session
      def soft_delete(id: UUID) → Session  # sets deleted_at

  backend/app/sessions/service.py:
    class SessionService:
      def create_session(account_id: UUID, email: str) → Session
      def add_message_and_score(session_id: UUID, role: str, content: str) → Session
      def get_session_with_audit() → Session

ENTREGABLES:
  ✓ SessionRepository
  ✓ SessionService
  ✓ Unit tests: 12 tests
  ✓ Integration tests: 8 tests

VALIDACIÓN (QA):
  ✓ CRUD operations funciona
  ✓ Soft-delete implementado
  ✓ Coverage: 92%

ARTEFACTOS:
  - PR #9: "feat: session repository and service"
  - Tests: 20 tests
```

#### Tarea 2.4: Session API Endpoints

```
ASIGNADO: ENGINEER-1
DURACIÓN: 8 horas (Miércoles-Jueves)
DEPENDENCIA: Task 2.3

DESCRIPCIÓN:
  Implementar endpoints REST:
  - POST /api/sessions (create)
  - GET /api/sessions/:id (retrieve)
  - GET /api/sessions (list by account)
  - PUT /api/sessions/:id (update status)
  - DELETE /api/sessions/:id (soft-delete)

CÓDIGO:
  backend/app/sessions/api.py:
    @router.post("/api/sessions")
    @require_auth
    async def create_session(
      request: CreateSessionRequest,
      current_user: User = Depends(get_current_user)
    ) → Session:
      return await session_service.create_session(
        account_id=current_user.id,
        email=request.candidate_email
      )

    @router.get("/api/sessions/:id")
    @require_auth
    async def get_session(
      id: UUID,
      current_user: User = Depends(get_current_user)
    ) → Session:
      ...

ENTREGABLES:
  ✓ 5 endpoints implementados
  ✓ Request/Response DTOs
  ✓ Unit tests: 10 tests

VALIDACIÓN (QA):
  ✓ POST /api/sessions returns 201
  ✓ GET /api/sessions returns 200
  ✓ DELETE /api/sessions returns 204
  ✓ Unauthorized → 401
  ✓ Coverage: 85%

ARTEFACTOS:
  - PR #10: "feat: session api endpoints"
  - Tests: 10 tests
```

#### Tarea 2.5: Unit 2 - Session Testing Suite

```
ASIGNADO: QA (en paralelo con ENGINEER-1)
DURACIÓN: Ongoing (8 horas)
DEPENDENCIA: Tasks 2.1-2.4

DESCRIPCIÓN:
  Crear suite de tests para Unit 2:
  - Unit tests: modelo, validaciones
  - Integration tests: DB, service layer
  - E2E: crear session → agregar message → score
  - Security: PII masking en logs

ENTREGABLES:
  ✓ 48+ tests totales
  ✓ 92% coverage

VALIDACIÓN:
  ✓ pytest tests/ -v --cov=app (48/48 pass)
  ✓ No PII en logs

ARTEFACTOS:
  - PR #11: "test: unit 2 comprehensive test suite"
  - Tests: 48 tests
```

#### Checklist Semana 2

```
☐ LUNES (3 June):
  ☐ 09:00 ORCHESTRATOR: Sprint 2 planning
  ☐ 10:00 ENGINEER-1: Task 2.1 (schema)

☐ MARTES (4 June):
  ☐ 09:00 QA: Valida schema
  ☐ 10:00 ENGINEER-1: Task 2.2 (aggregate)
  ☐ 10:00 QA: Comienza tests (Task 2.5)

☐ MIÉRCOLES (5 June):
  ☐ 09:00 QA: Valida aggregate
  ☐ 10:00 ENGINEER-1: Task 2.3 (repo + service)

☐ JUEVES (6 June):
  ☐ 09:00 QA: Valida repo/service
  ☐ 10:00 ENGINEER-1: Task 2.4 (endpoints)
  ☐ 14:00 ARCHITECT: Review Tasks 2.2-2.3

☐ VIERNES (7 June):
  ☐ 09:00 QA: Valida endpoints
  ☐ 10:00 QA: Finaliza test suite (48 tests)
  ☐ 14:00 ARCHITECT: Review Task 2.4
  ☐ 15:00 ORCHESTRATOR: Merge PRs 7-11 → main
  ☐ 16:00 ORCHESTRATOR: Tag v0.2.0
  ☐ 17:00 ORCHESTRATOR: Deploy v0.2.0 a staging

ENTREGA SEMANA 2:
  ✓ v0.2.0 deployed
  ✓ 48+ tests Unit 2
  ✓ Coverage: 92%
```

---

## 🟡 SEMANA 3 (10 June - 16 June)

### Sprint 3: BotEngine + Evaluation (Unit 3 + Unit 4)

**Objetivo**: Integración con Claude API, jailbreak detection, scoring

#### Tarea 3.1: BotEngine - Claude API Client (Unit 3)

```
ASIGNADO: ENGINEER-1
DURACIÓN: 10 horas (Lunes-Martes)
DEPENDENCIA: v0.2.0 (Unit 2)

DESCRIPCIÓN:
  Implementar Claude API client:
  - Message sending (system + user messages)
  - SSE streaming (real-time responses)
  - Token budget tracking (max 2000/session)
  - Error handling + retries

CÓDIGO:
  backend/app/botengine/claude_client.py:
    class ClaudeClient:
      async def send_message(
        messages: List[Message],
        system_prompt: str,
        max_tokens: int = 1000
      ) → StreamingResponse:
        """Enviar a Claude API via SSE"""
        response = await anthropic.messages.stream(
          model="claude-opus-4-7-20250514",
          max_tokens=max_tokens,
          system=system_prompt,
          messages=messages
        )
        return response

      def track_token_budget(session_id: UUID) → int:
        """Retorna tokens restantes"""
        ...

ENTREGABLES:
  ✓ Claude API client
  ✓ SSE streaming
  ✓ Token budget tracking
  ✓ Unit tests: 12 tests

VALIDACIÓN (QA):
  ✓ API calls funcionan
  ✓ SSE streaming < 100ms
  ✓ Token budget correcto
  ✓ Coverage: 88%

ARTEFACTOS:
  - PR #12: "feat: botengine claude api client"
```

#### Tarea 3.2: Jailbreak Detection (Unit 3)

```
ASIGNADO: ENGINEER-1
DURACIÓN: 8 horas (Martes-Miércoles)
DEPENDENCIA: Task 3.1

DESCRIPCIÓN:
  Detectar intentos de jailbreak:
  - Regex patterns (prompt injection, role-play)
  - Accuracy > 95%
  - Latency < 100ms

CÓDIGO:
  backend/app/botengine/jailbreak_detector.py:
    class JailbreakDetector:
      PATTERNS = [
        r"(?i)(ignore|override|bypass|disregard).*instructions",
        r"(?i)(you are now|pretend|act as|roleplay).*\w+",
        r"(?i)(system|prompt|rule|constraint).*override",
        ...
      ]

      def detect(message: str) → bool:
        for pattern in self.PATTERNS:
          if re.search(pattern, message):
            return True
        return False

ENTREGABLES:
  ✓ Jailbreak detector
  ✓ 15+ regex patterns
  ✓ Unit tests: 15 tests (>95% accuracy)

VALIDACIÓN (QA):
  ✓ True positives: > 95%
  ✓ Latency: < 100ms
  ✓ False negatives: < 5%

ARTEFACTOS:
  - PR #13: "feat: jailbreak detection"
  - Tests: 15 tests
```

#### Tarea 3.3: Evaluation Engine (Unit 4)

```
ASIGNADO: ENGINEER-1
DURACIÓN: 12 horas (Miércoles-Jueves)
DEPENDENCIA: Task 3.1

DESCRIPCIÓN:
  Implementar scoring engine:
  - Evaluación de respuestas
  - Decisión: HIRE, REJECT, MAYBE
  - Rubric validation
  - Citation extraction (técnica mencionada)

CÓDIGO:
  backend/app/evaluation/scorer.py:
    class EvaluationScore:
      technical: float  # 0-100
      communication: float  # 0-100
      problem_solving: float  # 0-100
      
      @property
      def average(self) → float:
        return (self.technical + self.communication + self.problem_solving) / 3
      
      @property
      def decision(self) → str:
        if self.average >= 80:
          return "HIRE"
        elif self.average >= 60:
          return "MAYBE"
        else:
          return "REJECT"

    class EvaluationEngine:
      def score_interview(
        session: Session,
        rubric: dict  # {criteria: weight}
      ) → EvaluationScore:
        ...

      def extract_citations(response: str) → List[str]:
        """Extraer técnicas mencionadas"""
        citations = []
        for sentence in response.split("."):
          if any(tech in sentence for tech in TECHNIQUES):
            citations.append(sentence.strip())
        return citations

ENTREGABLES:
  ✓ EvaluationScore class
  ✓ EvaluationEngine
  ✓ Citation extraction
  ✓ Unit tests: 15 tests

VALIDACIÓN (QA):
  ✓ Scoring accuracy > 90% (vs manual review)
  ✓ Decision logic correcto
  ✓ Citation extraction > 85% recall
  ✓ Coverage: 90%

ARTEFACTOS:
  - PR #14: "feat: evaluation engine and scoring"
  - Tests: 15 tests
```

#### Tarea 3.4: Integration Unit 3 + Unit 2 + Unit 4

```
ASIGNADO: ENGINEER-1
DURACIÓN: 6 horas (Jueves)
DEPENDENCIA: Tasks 3.1-3.3

DESCRIPCIÓN:
  Integración end-to-end:
  - Session → BotEngine (Claude) → Evaluation
  - Message flow: User sends → Claude responds → Scored

ENDPOINTS:
  POST /api/sessions/:id/evaluate
    ├─ Read session messages
    ├─ Send to Claude
    ├─ Detect jailbreak
    ├─ Store response
    ├─ Score response
    └─ Update session.final_score

ENTREGABLES:
  ✓ Integrated endpoints
  ✓ E2E tests: 8 tests

VALIDACIÓN (QA):
  ✓ Full flow funciona
  ✓ Latency: < 3s (P95)
  ✓ Coverage: 85%

ARTEFACTOS:
  - PR #15: "feat: integrate botengine and evaluation"
```

#### Checklist Semana 3

```
☐ LUNES (10 June):
  ☐ 09:00 ORCHESTRATOR: Sprint 3 planning
  ☐ 10:00 ENGINEER-1: Task 3.1 (Claude client)

☐ MARTES (11 June):
  ☐ 09:00 QA: Valida Claude client
  ☐ 10:00 ENGINEER-1: Task 3.2 (jailbreak)

☐ MIÉRCOLES (12 June):
  ☐ 09:00 QA: Valida jailbreak
  ☐ 10:00 ENGINEER-1: Task 3.3 (evaluation)

☐ JUEVES (13 June):
  ☐ 09:00 QA: Valida evaluation
  ☐ 10:00 ENGINEER-1: Task 3.4 (integration)
  ☐ 14:00 ARCHITECT: Review all Unit 3+4

☐ VIERNES (14 June):
  ☐ 09:00 QA: Valida integration + E2E tests
  ☐ 14:00 ORCHESTRATOR: Merge PRs 12-15
  ☐ 16:00 ORCHESTRATOR: Tag v0.3.0
  ☐ 17:00 ORCHESTRATOR: Deploy v0.3.0 a staging

ENTREGA SEMANA 3:
  ✓ v0.3.0 deployed
  ✓ Claude integration working
  ✓ Full evaluation flow (session → eval → score)
  ✓ 50+ tests Unit 3+4
```

---

## 🟢 SEMANA 4 (17 June - 23 June)

### Sprint 4: Frontend + E2E + Production

**Objetivo**: Interfaz Next.js, tests E2E, deploy a producción

#### Tarea 4.1: Frontend Setup + Layout

```
ASIGNADO: ENGINEER-2
DURACIÓN: 8 horas (Lunes-Martes)
DEPENDENCIA: v0.3.0 (backend APIs)

DESCRIPCIÓN:
  Configurar Next.js 14 + TypeScript + Zustand:
  - App router structure (candidate/, recruiter/, admin/)
  - Global layout (navbar, sidebar)
  - Authentication context
  - Zustand store setup

ESTRUCTURA:
  frontend/
  ├── app/
  │   ├── layout.tsx (global)
  │   ├── candidate/
  │   │   ├── page.tsx (dashboard)
  │   │   ├── session/[id]/page.tsx
  │   │   └── layout.tsx
  │   ├── recruiter/
  │   │   ├── page.tsx (queue)
  │   │   └── evaluate/[id]/page.tsx
  │   └── admin/
  │       └── users/page.tsx
  ├── components/
  │   ├── CandidateChat.tsx
  │   ├── EvaluationModal.tsx
  │   └── ...
  └── hooks/
      ├── useAuth.ts
      └── useStore.ts

ENTREGABLES:
  ✓ Next.js app router configured
  ✓ Global layout + routing
  ✓ Zustand store
  ✓ Build: npm run build (< 10MB gzipped)

VALIDACIÓN (QA):
  ✓ Build completa sin errores
  ✓ Bundle size < 10MB gzipped

ARTEFACTOS:
  - PR #16: "feat: frontend setup and layout"
```

#### Tarea 4.2: Candidate Interview Component

```
ASIGNADO: ENGINEER-2
DURACIÓN: 10 horas (Martes-Miércoles)
DEPENDENCIA: Task 4.1 + v0.3.0

DESCRIPCIÓN:
  Interfaz de entrevista para candidatos:
  - Chat interface (SSE streaming from backend)
  - Message history display
  - Typing indicator
  - Score display
  - Accessibility (WCAG 2.2 AAA)

CÓDIGO:
  frontend/components/CandidateChat.tsx:
    export function CandidateChat({ sessionId }: { sessionId: string }) {
      const [messages, setMessages] = useState<Message[]>([])
      const [input, setInput] = useState("")
      const [streaming, setStreaming] = useState(false)

      async function sendMessage() {
        setStreaming(true)
        const response = await fetch(
          `/api/sessions/${sessionId}/evaluate`,
          { method: "POST", body: JSON.stringify({ message: input }) }
        )
        const reader = response.body.getReader()
        while (true) {
          const { value, done } = await reader.read()
          if (done) break
          const text = new TextDecoder().decode(value)
          setMessages(prev => [...prev, { role: "bot", content: text }])
        }
        setStreaming(false)
      }

      return (
        <div className="chat-container" role="log" aria-live="polite">
          {messages.map((msg, i) => (
            <div key={i} className="message" role="article">
              {msg.content}
            </div>
          ))}
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Your answer..."
            aria-label="Type your response"
          />
          <button
            onClick={sendMessage}
            disabled={streaming}
            aria-busy={streaming}
          >
            Send
          </button>
        </div>
      )
    }

ENTREGABLES:
  ✓ CandidateChat component
  ✓ SSE streaming integration
  ✓ Unit tests: 8 tests
  ✓ Accessibility: 0 violations

VALIDACIÓN (QA):
  ✓ Messages display correctly
  ✓ SSE streams properly
  ✓ axe: 0 violations
  ✓ Coverage: 85%

ARTEFACTOS:
  - PR #17: "feat: candidate chat component"
```

#### Tarea 4.3: Recruiter Dashboard

```
ASIGNADO: ENGINEER-2
DURACIÓN: 10 horas (Miércoles-Jueves)
DEPENDENCIA: Task 4.1 + v0.3.0

DESCRIPCIÓN:
  Dashboard para reclutadores:
  - Lista de sesiones (filtering, sorting)
  - Evaluation modal
  - Score visualization
  - Candidate details

ENTREGABLES:
  ✓ RecruiterQueue component (list + search)
  ✓ EvaluationModal component
  ✓ Unit tests: 10 tests
  ✓ Accessibility: 0 violations

VALIDACIÓN (QA):
  ✓ Lists render correctly
  ✓ Filtering works
  ✓ Modal opens/closes
  ✓ Coverage: 80%

ARTEFACTOS:
  - PR #18: "feat: recruiter dashboard"
```

#### Tarea 4.4: E2E Testing (Playwright)

```
ASIGNADO: QA
DURACIÓN: 12 horas (Lunes-Jueves)
DEPENDENCIA: Tasks 4.1-4.3

DESCRIPCIÓN:
  End-to-end tests de flujos críticos:
  - User registration → login → dashboard
  - Candidate assessment → scoring → decision
  - Recruiter queue → evaluate → decision

TESTS:
  25+ scenarios:
  ✓ Candidate flow: register → answer → view results
  ✓ Recruiter flow: login → queue → evaluate → view score
  ✓ Admin: manage users → assign roles
  ✓ Error handling: network errors, timeouts
  ✓ Accessibility: keyboard nav, screen reader

ENTREGABLES:
  ✓ 25+ Playwright scenarios
  ✓ Video recording on failure
  ✓ Screenshots for regression

VALIDACIÓN:
  ✓ All scenarios pass
  ✓ No flakiness (0 retries needed)

ARTEFACTOS:
  - PR #19: "test: e2e playwright scenarios"
```

#### Tarea 4.5: Production Deployment Preparation

```
ASIGNADO: ENGINEER-2 + ORCHESTRATOR
DURACIÓN: 6 horas (Viernes)
DEPENDENCIA: All Tasks complete

DESCRIPCIÓN:
  Preparación final para producción:
  - Data migration from staging
  - DNS / SSL certificates
  - Load balancer configuration
  - CloudWatch dashboards
  - On-call runbooks
  - Incident response plan

CHECKLIST PRE-PROD:
  ☐ Database: backup, migration tested
  ☐ Infrastructure: Terraform apply validated
  ☐ Security: TLS 1.3, CSP headers verified
  ☐ Monitoring: dashboards configured
  ☐ Runbooks: created and tested
  ☐ On-call: rotation scheduled
  ☐ Rollback: plan documented and tested

ENTREGABLES:
  ✓ Production infrastructure ready
  ✓ Runbooks written
  ✓ Team trained

ARTEFACTOS:
  - Infrastructure ready
  - OPERATIONS-RUNBOOKS.md updated
```

#### Tarea 4.6: Production Deployment + Smoke Tests

```
ASIGNADO: ORCHESTRATOR + QA
DURACIÓN: 2 horas (Viernes afternoon)
DEPENDENCIA: Task 4.5

DESCRIPCIÓN:
  Deploy a producción:
  1. terraform apply production
  2. ECS task update (blue/green)
  3. DNS switch (staging → prod)
  4. Smoke tests
  5. Post-deploy validation

SMOKE TESTS:
  ✓ Health check: GET /health → 200
  ✓ Auth: POST /auth/login → JWT
  ✓ User session: POST /api/sessions → 201
  ✓ Evaluation flow: full path works
  ✓ Audit log: entries recorded

ROLLBACK PLAN:
  Si algo falla:
  1. ECS: revert task definition
  2. DNS: switch back to staging
  3. Investigate en staging
  4. Plan fix + redeploy

ENTREGABLES:
  ✓ v1.0.0 deployed to production
  ✓ All smoke tests passing
  ✓ Monitoring active

ARTEFACTOS:
  - PR #20: "release: version 1.0.0 to production"
  - Tag: v1.0.0
  - CHANGELOG.md updated
```

#### Checklist Semana 4

```
☐ LUNES (17 June):
  ☐ 09:00 ORCHESTRATOR: Sprint 4 planning
  ☐ 10:00 ENGINEER-2: Task 4.1 (frontend setup)
  ☐ 10:00 QA: Task 4.4 (E2E test writing)

☐ MARTES (18 June):
  ☐ 09:00 QA: Valida Task 4.1
  ☐ 10:00 ENGINEER-2: Task 4.2 (candidate chat)

☐ MIÉRCOLES (19 June):
  ☐ 09:00 QA: Valida Task 4.2
  ☐ 10:00 ENGINEER-2: Task 4.3 (recruiter dashboard)
  ☐ 10:00 QA: Continuous E2E testing

☐ JUEVES (20 June):
  ☐ 09:00 QA: Valida Task 4.3 + all E2E scenarios
  ☐ 10:00 ENGINEER-2: Task 4.5 (prod prep)
  ☐ 14:00 ARCHITECT: Final review

☐ VIERNES (21 June):
  ☐ 09:00 ORCHESTRATOR: Pre-prod validation
  ☐ 10:00 QA: Smoke tests on staging (last validation)
  ☐ 14:00 ORCHESTRATOR: Merge PR #20
  ☐ 15:00 ORCHESTRATOR: Tag v1.0.0
  ☐ 16:00 ORCHESTRATOR: Deploy to production
  ☐ 17:00 QA: Smoke tests on production
  ☐ 18:00 ORCHESTRATOR: Verify monitoring active
  ☐ 19:00 ORCHESTRATOR: Notify stakeholders (DEPLOYMENT COMPLETE)

ENTREGA SEMANA 4:
  ✓ v1.0.0 deployed to production
  ✓ All E2E tests passing
  ✓ Monitoring & alerts active
  ✓ On-call rotation ready
  ✓ TicketDesk Enterprise LIVE 🚀
```

---

## 📊 Matriz RACI (Responsabilidad)

```
TAREA                    | ORCHESTRATOR | ENGINEER-1 | ENGINEER-2 | QA | ARCHITECT
─────────────────────────┼──────────────┼────────────┼────────────┼────┼───────────
1.1 DB Schema            | C            | R          | -          | A  | -
1.2 User Aggregate       | C            | R          | -          | A  | R
1.3 Auth Service         | C            | R          | -          | A  | -
1.4 RBAC                 | C            | R          | -          | A  | -
1.5 Audit Logging        | C            | R          | -          | A  | -
1.6 Docker + CI/CD       | C            | -          | R          | A  | -
2.1 Session Schema       | C            | R          | -          | A  | -
2.2 Session Aggregate    | C            | R          | -          | A  | R
2.3 Session Repo/Service | C            | R          | -          | A  | -
2.4 Session Endpoints    | C            | R          | -          | A  | -
2.5 Unit 2 Tests         | C            | -          | -          | R  | -
3.1 Claude Client        | C            | R          | -          | A  | -
3.2 Jailbreak Detection  | C            | R          | -          | A  | -
3.3 Evaluation Engine    | C            | R          | -          | A  | R
3.4 Integration          | C            | R          | -          | A  | -
4.1 Frontend Setup       | C            | -          | R          | A  | -
4.2 Candidate Chat       | C            | -          | R          | A  | -
4.3 Recruiter Dashboard  | C            | -          | R          | A  | -
4.4 E2E Tests            | C            | -          | -          | R  | -
4.5 Prod Prep            | R            | -          | I          | A  | I
4.6 Prod Deployment      | R            | -          | I          | A  | I

R = Responsible (hace el trabajo)
A = Accountable (aprueba/valida)
C = Consulted (retroalimenta)
I = Informed (notificado)
```

---

## 📈 Métricas de Éxito

```
CRITERIOS POR SEMANA:

SEMANA 1: v0.1.0 a staging
  ✓ 70+ tests creados
  ✓ Coverage: 88%
  ✓ 0 security vulnerabilities
  ✓ Smoke tests: PASS

SEMANA 2: v0.2.0 a staging
  ✓ 48+ tests Unit 2
  ✓ Coverage: 92%
  ✓ LGPD audit trail working
  ✓ E2E flow: session creation → scoring

SEMANA 3: v0.3.0 a staging
  ✓ 50+ tests Unit 3+4
  ✓ Claude integration verified
  ✓ Jailbreak detection: >95% accuracy
  ✓ Full eval flow working

SEMANA 4: v1.0.0 a producción
  ✓ 25+ E2E scenarios passing
  ✓ Frontend accessible (WCAG 2.2 AAA)
  ✓ Performance: LCP ≤ 2.5s, INP ≤ 200ms
  ✓ Uptime: 99.5% SLA configured

FINAL:
  ✓ TicketDesk Enterprise LIVE
  ✓ 150+ tests total (>80% coverage)
  ✓ Zero critical security issues
  ✓ LGPD compliant
  ✓ Accessible + fast
```

---

## 🛑 Mitigación de Riesgos

```
RIESGO 1: Bloqueo en Unit 2 → Unit 3 dependencia
MITIGACIÓN:
  • Unit 3 ENGINEER comienza tests con mocks de Unit 2
  • Rápido switch a integración real una vez Unit 2 merged

RIESGO 2: Claude API quota exceeded
MITIGACIÓN:
  • Token budget: max 2000/session (costo controlado)
  • Rate limiting: 100 req/min per user
  • Fallback: queue de espera si se excede

RIESGO 3: Frontend accesibilidad no cumple AAA
MITIGACIÓN:
  • axe-core automated testing en CI/CD
  • Manual testing con screen readers (NVDA, VoiceOver)
  • Accessibility specialist review en Week 4

RIESGO 4: Prod deployment falla
MITIGACIÓN:
  • Staging deployment primero (Week 3)
  • Blue/green strategy en prod
  • Rollback plan documented
  • Dry-run de rollback en staging antes de prod

RIESGO 5: Performance no alcanza Core Web Vitals
MITIGACIÓN:
  • Lighthouse testing semanal
  • Bundle size monitoring
  • Cache strategy validated
  • Load testing: 200 concurrent users
```

---

## 🎯 Resumen Ejecutivo Final

```
PROYECTO: TicketDesk Enterprise v1.0
METODOLOGÍA: 4 agentes + Orquestación centralizada
DURACIÓN: 4 semanas (27 May - 23 June 2026)
ENTREGA: v1.0.0 Production-Ready

TIMELINE:
  Semana 1: Unit 1 + Unit 6 → v0.1.0 (staging)
  Semana 2: Unit 2 → v0.2.0 (staging)
  Semana 3: Unit 3 + Unit 4 → v0.3.0 (staging)
  Semana 4: Unit 5 + E2E + Prod → v1.0.0 (production)

ENTREGABLES:
  ✓ 20 PRs (feature branches)
  ✓ 150+ tests (unit + integration + E2E)
  ✓ 6 releases (v0.1.0 - v1.0.0)
  ✓ 5 CLAUDE API integrations
  ✓ Full LGPD compliance
  ✓ WCAG 2.2 AAA accessibility
  ✓ Core Web Vitals performance
  ✓ 99.5% uptime SLA

ESTADO: ✅ LISTO PARA EJECUCIÓN INMEDIATA
```

---

**Guía de Ejecución creada**: 2026-05-27  
**Responsable**: ORCHESTRATOR Agent  
**Inicio de ejecución**: Lunes 27 de Mayo 2026, 09:00  
**Fin de ejecución**: Viernes 23 de Junio 2026, 19:00

🚀 **TicketDesk Enterprise — Del Diseño a Producción en 4 Semanas**
