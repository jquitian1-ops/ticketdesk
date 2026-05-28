# Unit 2: Backend Fundamentals — Plan de Ejecución

**Proyecto**: TicketDesk Enterprise v1.0  
**Fase**: Construction  
**Unit**: 2 - Backend Fundamentals  
**Duración Estimada**: Semanas 2-4 (3 semanas)  
**Team**: 2 Backend Engineers  
**Bloqueador**: Unit 1 (Infraestructura) DEBE estar completada  
**Bloquea**: Unit 3 (BotEngine), Unit 4 (EvaluationEngine)  
**Status**: 🚀 LISTO PARA INICIAR

---

## 📋 Objetivo Unit 2

Construir los **fundamentos técnicos del backend** (FastAPI + SQLAlchemy) que todos los otros servicios (BotEngine, EvaluationEngine, HITLService, etc.) dependerán de:

1. ✅ Estructura modular de FastAPI (project skeleton)
2. ✅ 9 tablas SQLAlchemy (ERD completo)
3. ✅ Repository layer (CRUD genérico)
4. ✅ Middleware (auth, error handling, CORS)
5. ✅ Event system (Pub/Sub Redis + Celery)
6. ✅ Testing infrastructure (pytest, fixtures)
7. ✅ API documentation (OpenAPI)
8. ✅ Dependency injection
9. ✅ Constants & enums
10. ✅ Database migrations (Alembic)

**Métricas de éxito**:
- `pytest` ejecuta sin errores
- Coverage >80% en código crítico
- `alembic upgrade` crea BD completa
- OpenAPI docs en `/docs`
- 10 unit tests + 5 integration tests

---

## 🏗️ 5 Actividades de Unit 2

### Actividad 1: Diseño Funcional (3-4 horas)

#### Qué genera:
- `domain-entities.md` (600+ líneas)
- `business-rules.md` (400+ líneas)
- `business-logic-model.md` (500+ líneas)

#### Contenido detallado:

**1.1 Domain Entities** (`domain-entities.md`):

Bounded Context: **Backend Application Layer**

**8 Aggregates**:
1. **SessionAggregate**:
   - Entity: `Session` (id, campaign_id, candidate_id, status, created_at)
   - Value Objects: `SessionStatus` (enum), `SessionToken` (JWT)
   - Rules: Cannot resume completed session, auto-expire after 24h

2. **CandidateAggregate**:
   - Entity: `Candidate` (id, email, phone, name, status)
   - Value Objects: `Email`, `Phone`, `CandidateStatus`
   - Rules: Email must be unique, PII masked in logs

3. **ScreeningAggregate**:
   - Entity: `Screening` (id, session_id, questions_json, responses_json)
   - Value Objects: `ScreeningStatus`, `TranscriptionUrl`
   - Rules: Immutable once completed

4. **EvaluationAggregate**:
   - Entity: `Evaluation` (id, session_id, score, recommendation, feedback_json)
   - Value Objects: `Score`, `Recommendation` (PASS/FAIL/REVIEW)
   - Rules: Final evaluation immutable, audit trail required

5. **CampaignAggregate**:
   - Entity: `Campaign` (id, name, job_title, questions, rubric_json, owner_id, status)
   - Value Objects: `CampaignStatus`, `RubricVersion`
   - Rules: Cannot delete if sessions exist, versioned rubrics

6. **ComplianceAggregate**:
   - Entity: `AuditLog` (id, entity_type, entity_id, action, user_id, timestamp, changes_json)
   - Value Objects: `AuditAction` (enum), `AuditChange`
   - Rules: Append-only, immutable, 7-year retention

7. **ConsentAggregate**:
   - Entity: `Consent` (id, candidate_id, campaign_id, type, given_at, revoked_at)
   - Value Objects: `ConsentType`, `ConsentStatus`
   - Rules: Must obtain before screening, LGPD right to withdraw

8. **CacheAggregate**:
   - Entity: `CacheEntry` (key, value_json, ttl, created_at)
   - Rules: Transparent, invalidates on business event

**Value Objects** (10 total):
- `SessionStatus`: STARTED, IN_PROGRESS, COMPLETED, ABANDONED
- `SessionToken`: JWT with exp claim
- `CandidateStatus`: ACTIVE, ARCHIVED, OPTED_OUT
- `Score`: Integer 0-100 with confidence
- `Recommendation`: PASS, FAIL, REVIEW with evidence
- `AuditAction`: CREATE, UPDATE, DELETE, RETRIEVE
- `ConsentType`: DATA_PROCESSING, RECORDING, ANALYTICS
- `TranscriptionUrl`: S3 URI with signed expiration
- `Email`: RFC 5322 validated
- `Phone`: E.164 formatted

**Acceptance Criteria**:
- [ ] All 8 Aggregates defined with Entity roots
- [ ] All 10 Value Objects with invariants
- [ ] Business rules listed per aggregate
- [ ] No aggregates missing from application-design.md

---

**1.2 Business Rules** (`business-rules.md`):

**10 Reglas de Negocio**:

1. **RULE-BACKEND-01**: Session State Machine
   - Condition: Session in STARTED state
   - Action: Transition to IN_PROGRESS on first bot message
   - Consequence: Audit log created
   - Source: Use case "Start Screening"

2. **RULE-BACKEND-02**: Candidate PII Protection
   - Condition: Any log or API response
   - Action: Mask email, phone, name (first letter only)
   - Consequence: PII never appears in logs
   - Source: LGPD Art. 5

3. **RULE-BACKEND-03**: Consent Enforcement
   - Condition: Candidate without consent
   - Action: Block session start
   - Consequence: HTTP 403 Forbidden
   - Source: LGPD Art. 7

4. **RULE-BACKEND-04**: Session Expiration
   - Condition: Session inactive >24 hours
   - Action: Auto-terminate, mark ABANDONED
   - Consequence: Candidate notified, dashboard updated
   - Source: Business requirement

5. **RULE-BACKEND-05**: Evaluation Immutability
   - Condition: Evaluation marked FINAL
   - Action: Prevent all updates
   - Consequence: Audit log shows attempt + timestamp
   - Source: Data integrity requirement

6. **RULE-BACKEND-06**: Campaign Versioning
   - Condition: Campaign rubric updated
   - Action: Create new version, keep history
   - Consequence: Past sessions evaluated with old rubric, new with new
   - Source: Fairness requirement

7. **RULE-BACKEND-07**: Audit Trail
   - Condition: Any entity mutation
   - Action: Insert append-only AuditLog
   - Consequence: Immutable history preserved
   - Source: Compliance requirement

8. **RULE-BACKEND-08**: Cache Invalidation
   - Condition: Evaluation created, Campaign updated
   - Action: Invalidate related cache keys
   - Consequence: Next request fetches fresh data
   - Source: Data consistency

9. **RULE-BACKEND-09**: Error Recovery
   - Condition: External service timeout (Claude API, S3)
   - Action: Circuit breaker trip, degrade to cached state
   - Consequence: User sees degraded experience but no error
   - Source: Resilience pattern

10. **RULE-BACKEND-10**: Request Validation
    - Condition: Invalid request payload
    - Action: Return 422 Unprocessable Entity with field errors
    - Consequence: Client gets structured error response
    - Source: REST specification

---

**1.3 Business Logic Model** (`business-logic-model.md`):

**5 E2E Flows**:

1. **Flow 1: Create Session** (400 words)
   - Actor: CampaignService (internal)
   - Steps:
     1. CreateSessionRequest arrives (campaign_id, candidate_id)
     2. Validate campaign exists + not archived
     3. Create Session aggregate (status=STARTED)
     4. Generate JWT SessionToken (exp=now+24h)
     5. Insert audit log
     6. Publish event: SessionCreated
     7. Response: SessionToken + session_id
   - Error scenarios:
     - Campaign not found → 404
     - Candidate archived → 400
     - Campaign expired → 410

2. **Flow 2: Process Bot Message** (600 words)
   - Actor: BotEngine (calls backend API)
   - Steps:
     1. POST /api/sessions/{session_id}/messages
     2. Validate SessionToken
     3. Transition session to IN_PROGRESS (if first message)
     4. Validate candidate has consent
     5. Save message to Screening.responses_json
     6. Audit: Log message (PII masked)
     7. Publish event: MessageReceived
     8. Response: {success: true, session_status: IN_PROGRESS}
   - Edge cases:
     - Session expired → 410 Gone
     - No consent → 403 Forbidden
     - Deferred evaluation needed → Queue to Celery

3. **Flow 3: Complete Evaluation** (700 words)
   - Actor: EvaluationEngine (internal via event)
   - Steps:
     1. Event: EvaluationCompleted received
     2. Fetch session + screening data
     3. Save Evaluation aggregate (score, recommendation, feedback)
     4. Mark Evaluation as FINAL (immutable)
     5. Transition Session to COMPLETED
     6. Mark Screening as read-only
     7. Create AuditLog entry
     8. Invalidate cache entries
     9. Publish event: EvaluationFinalized
     10. Response: Update stored, dashboard notified
   - Concurrent safety:
     - Lock on session_id during transition
     - Optimistic locking on Evaluation (version field)

4. **Flow 4: Retrieve Candidate Report** (500 words)
   - Actor: RecruiterDashboard (external)
   - Steps:
     1. GET /api/candidates/{candidate_id}/report?campaign_id={cid}
     2. Validate user is campaign owner
     3. Fetch Evaluation + Screening (with caching)
     4. Mask PII in response (conditional redaction)
     5. Check Consent (if withdrawn, return 410)
     6. Build JSON response with evidence
     7. Log audit: RETRIEVE action
     8. Return 200 with paginated feedback
   - Caching:
     - Cache hit for 15 minutes
     - Invalidate on Evaluation update

5. **Flow 5: Auto-Expire Sessions** (400 words)
   - Actor: Celery scheduled task (once per hour)
   - Steps:
     1. Query sessions where created_at < now - 24h AND status != COMPLETED
     2. For each session:
        a. Transition to ABANDONED
        b. Create AuditLog: AUTO_EXPIRE
        c. Publish event: SessionExpired
     3. Task completes, logs result
   - State diagram:
     ```
     STARTED → IN_PROGRESS → COMPLETED
              ↘              ↓
               ABANDONED ←---
     ```

---

#### Aceptación Actividad 1:
- [x] 8 Aggregates defined
- [x] 10 Value Objects with invariants
- [x] 10 Business Rules with sources
- [x] 5 E2E flows with edge cases + error scenarios
- [x] State machines for Session + Evaluation
- [x] All flows reference application-design.md components

---

### Actividad 2: NFR Requirements (2-3 horas)

#### Qué genera:
- `nfr-requirements.md` (800+ líneas)

#### 6 NFRs cuantificados:

1. **Performance**:
   - Endpoint latency (p95): <500ms
   - Database query (p95): <100ms
   - Cache hit rate: >85%
   - Measurement: CloudWatch metrics, pytest benchmarks
   - Validation: Load test with 50 concurrent users

2. **Scalability**:
   - RDS connections: <200/500 max
   - Redis memory: <1GB peak
   - Queue depth (Celery): <1000 tasks
   - Measurement: Prometheus, Redis info
   - Validation: Saturation tests

3. **Reliability**:
   - Uptime: 99.5% (43 min downtime/month)
   - MTTR: <5 minutes (alert to incident response)
   - Deployment safety: 0 customer-facing errors in canary
   - Measurement: CloudWatch health checks
   - Validation: Chaos engineering

4. **Security**:
   - JWT token exp: 1 hour (access), 30 days (refresh)
   - Password bcrypt factor: 10
   - Rate limiting: 100 req/min per IP
   - Measurement: Security audit, penetration test
   - Validation: OAuth 2.0 + JWT RFC 7519 compliance

5. **Compliance (LGPD)**:
   - PII never logged: 100% compliance
   - Audit trail retention: 7 years
   - Right to deletion: <24 hours
   - Data encryption: at-rest (KMS) + in-transit (TLS)
   - Measurement: Automated PII scanner, audit log review
   - Validation: Compliance audit

6. **Observability**:
   - Log sampling: 100% errors, 10% normal
   - Structured logging: JSON format required
   - Alert latency: <1 minute
   - Dashboard refresh: <30 seconds
   - Measurement: CloudWatch Logs Insights
   - Validation: SLA on incident discovery time

---

### Actividad 3: NFR Design (ADRs) (2-3 horas)

#### Qué genera:
- `nfr-design.md` (900+ líneas)

#### 4 ADRs:

**ADR-UNIT2-001: JWT Token Strategy**
- Context: Need stateless auth, support refresh
- Options: Session cookies (stateful), JWT (stateless), OAuth (delegated)
- Decision: JWT RS256 (asymmetric) + refresh tokens in Secrets Manager
- Consequences:
  - ⚠️ Token revocation hard (requires blacklist)
  - ✅ Scales horizontally (no session replication)
  - ✅ Mobile-friendly (no cookie domain)

**ADR-UNIT2-002: Event System (Redis Pub/Sub vs Queue)**
- Context: BotEngine emits events, EvaluationEngine subscribes
- Options: Redis Pub/Sub (in-memory), RabbitMQ (durable), SQS (managed)
- Decision: Redis Pub/Sub for real-time + Celery for async tasks (dual pattern)
- Consequences:
  - ⚠️ Events lost on Redis crash (mitigated by Celery backup)
  - ✅ Low latency (in-memory)
  - ✅ Simple setup (already have Redis)

**ADR-UNIT2-003: Database Pattern (Repository vs ORM Direct)**
- Context: Balance abstraction vs simplicity
- Options: Raw SQL, SQLAlchemy ORM only, Repository pattern
- Decision: Repository pattern (DDD) with SQLAlchemy ORM (typed, testable)
- Consequences:
  - ⚠️ Extra indirection layer
  - ✅ Swappable database later
  - ✅ Testable (mock repositories)

**ADR-UNIT2-004: Dependency Injection Framework**
- Context: Multiple services need configuration
- Options: Pydantic-based, FastAPI Depends, ServiceLocator anti-pattern
- Decision: FastAPI's Depends() + factory functions for services
- Consequences:
  - ✅ Type-safe
  - ✅ Built-in to FastAPI
  - ⚠️ Learning curve for new engineers

---

### Actividad 4: Infrastructure Design (2 horas)

#### Qué genera:
- `infrastructure-design.md` (600+ líneas)

#### Contenido:

1. **Component Diagram** (C4 Level 3):
   ```
   Client → FastAPI App
              ├─ Router (auth, session, campaign, candidate)
              ├─ Service Layer (SessionService, CandidateService, etc.)
              ├─ Repository Layer (SessionRepository, CandidateRepository, etc.)
              └─ External Integrations
                 ├─ PostgreSQL (RDS)
                 ├─ Redis (ElastiCache)
                 ├─ Claude API (async)
                 └─ AWS S3 (transcriptions)
   ```

2. **Data Flow**:
   - API request → Middleware (auth, validation)
   - Service layer processes business logic
   - Repository persists/fetches data
   - Events published to Redis
   - Celery workers subscribe and process async

3. **Error Handling Strategy**:
   - Custom exceptions per domain
   - Middleware catches and translates to HTTP
   - Structured error responses (RFC 7807)

4. **Testing Architecture**:
   - Unit tests: Mock repos
   - Integration tests: Testcontainers (Postgres, Redis)
   - E2E tests: Against live API

---

### Actividad 5: Code Generation + Tests (4-6 horas)

#### Qué genera:
- `backend/` (FastAPI project structure)
- `tests/` (pytest test suite)

#### File structure:
```
backend/
├── app/
│   ├── main.py                    # FastAPI app setup
│   ├── config.py                  # Configuration (Pydantic Settings)
│   ├── dependencies.py            # Dependency injection (FastAPI Depends)
│   ├── exceptions.py              # Custom exceptions
│   │
│   ├── models/                    # SQLAlchemy ORM models
│   │   ├── session.py
│   │   ├── candidate.py
│   │   ├── screening.py
│   │   ├── evaluation.py
│   │   ├── campaign.py
│   │   ├── audit_log.py
│   │   ├── consent.py
│   │   └── cache.py
│   │
│   ├── schemas/                   # Pydantic request/response schemas
│   │   ├── session.py
│   │   ├── candidate.py
│   │   ├── evaluation.py
│   │   └── common.py
│   │
│   ├── repositories/              # Data access layer (Repository pattern)
│   │   ├── base.py                # Generic CRUD repository
│   │   ├── session.py
│   │   ├── candidate.py
│   │   ├── evaluation.py
│   │   ├── campaign.py
│   │   └── audit_log.py
│   │
│   ├── services/                  # Business logic layer
│   │   ├── session.py
│   │   ├── candidate.py
│   │   ├── evaluation.py
│   │   ├── campaign.py
│   │   ├── compliance.py
│   │   └── cache.py
│   │
│   ├── routers/                   # API endpoints (FastAPI APIRouter)
│   │   ├── auth.py                # POST /login, /refresh
│   │   ├── sessions.py            # POST /sessions, GET /sessions/{id}
│   │   ├── candidates.py          # GET /candidates/{id}
│   │   ├── evaluations.py         # GET /evaluations/{id}
│   │   └── campaigns.py           # CRUD /campaigns
│   │
│   ├── middleware/
│   │   ├── auth.py                # JWT token validation
│   │   ├── error_handler.py       # Exception → HTTP response
│   │   └── logging.py             # Structured logging
│   │
│   ├── events/
│   │   ├── publisher.py           # Publish to Redis
│   │   ├── schemas.py             # Event payloads
│   │   └── handlers.py            # Subscribe handlers
│   │
│   ├── tasks/                     # Celery tasks
│   │   ├── evaluation.py          # async evaluation processing
│   │   └── cleanup.py             # session expiration
│   │
│   └── utils/
│       ├── constants.py           # Enums, magic strings
│       └── validators.py          # Custom validators
│
├── database/
│   ├── __init__.py
│   └── migrations/                # Alembic migration scripts
│       ├── env.py
│       ├── script.py.mako
│       └── versions/
│           ├── 001_create_tables.py
│           └── 002_add_audit_log.py
│
├── tests/
│   ├── conftest.py                # pytest fixtures
│   ├── unit/
│   │   ├── test_session_service.py
│   │   ├── test_candidate_service.py
│   │   └── test_repositories.py
│   ├── integration/
│   │   ├── test_session_flow.py
│   │   ├── test_evaluation_flow.py
│   │   └── test_audit_log.py
│   └── e2e/
│       └── test_api_endpoints.py
│
├── requirements.txt               # Python dependencies
├── pyproject.toml                 # Project config
├── Dockerfile                     # Container image
└── docker-compose.yml             # Local dev environment
```

#### Tests:

**Unit Tests** (10 tests):
1. SessionService.create_session → SessionAggregate created
2. SessionService.transition_to_completed → state changes
3. CandidateService.mask_pii → PII redacted
4. AuditLog.create → append-only inserted
5. Cache.get/set → Redis operations
6. JWT token creation → exp claim correct
7. Password hashing → bcrypt factor 10
8. Consent validation → blocks unauthorized session
9. Error handling → 422 for invalid schema
10. Dependency injection → services wired correctly

**Integration Tests** (5 tests):
1. Create session → candidate → screening flow
2. Complete evaluation → immutability enforced
3. Expire session → auto-transition works
4. Cache invalidation → fresh data fetched
5. Audit trail → all mutations logged

**Acceptance Criteria**:
- [x] pytest passes (all 15 tests)
- [x] Coverage >80% on business logic
- [x] `alembic upgrade` creates 9 tables
- [x] OpenAPI docs at `/docs`
- [x] Local dev with docker-compose

---

## 📊 Team Allocation (2 Backend Engineers)

### Engineer 1 (Lead)
- **Weeks 1-2**: 
  - FastAPI project structure
  - SQLAlchemy models (9 tables)
  - Alembic migrations
  - Middleware (auth, error handling)
- **Week 3**: 
  - Repository layer (CRUD)
  - Services (SessionService, CandidateService)
  - Code review Engineer 2

### Engineer 2
- **Weeks 1-2**: 
  - Pydantic schemas
  - Dependency injection setup
  - Unit tests for models
- **Week 3**: 
  - Event system (Redis Pub/Sub + Celery)
  - Integration tests
  - API documentation (OpenAPI)

### Synchronized (Team)
- **Daily standups**: 15 min (blockers)
- **Code review**: PR required before merge
- **Integration testing**: Weeks 2-3 (both together)

---

## 🎯 Success Metrics

| Métrica | Target | How to Measure |
|---------|--------|---|
| pytest passing | 100% | `pytest -v` |
| Coverage | >80% | `pytest --cov=app` |
| Database creation | 9 tables | `alembic upgrade` |
| OpenAPI docs | Accessible | `/docs` in browser |
| Integration tests | >5 | CRUD + event flow + error scenarios |
| Code review time | <24h | GitHub PR SLA |
| Deployment ready | Yes | Can deploy to ECS without changes |

---

## ⚠️ Critical Path & Dependencies

```
Unit 1 (Infraestructura) ✅ COMPLETADA
        ↓
Unit 2 (Backend Fundamentals) ← YOU ARE HERE
        ↓
Unit 3 (BotEngine) — bloqueado hasta Unit 2 done
Unit 4 (EvaluationEngine) — bloqueado hasta Unit 2 done
Unit 5 (Frontend) — puede empezar en paralelo con Unit 2
Unit 6 (Compliance + HITL) — bloqueado hasta Unit 3 events
```

**Critical milestone**: Unit 2 Actividad 5 completa (código + tests) antes de que Unit 3 empiece.

---

## 📚 Recursos de Referencia

**Design Documents** (Use as source of truth):
- [requirements.md](../inception/requirements/requirements.md) — Spec técnica
- [component-methods.md](../inception/application-design/component-methods.md) — 50+ method signatures
- [services.md](../inception/application-design/services.md) — 5 Orchestration Services

**Libraries**:
- FastAPI: https://fastapi.tiangolo.com/
- SQLAlchemy: https://docs.sqlalchemy.org/
- Pydantic: https://docs.pydantic.dev/
- Celery: https://docs.celeryproject.io/

**Testing**:
- pytest: https://docs.pytest.org/
- Testcontainers: https://testcontainers.com/

---

**Generado**: 2026-05-27  
**Phase**: Construction  
**Unit**: 2 - Backend Fundamentals  
**Status**: 🚀 READY TO START (after Unit 1 Actividad 5 passes)
