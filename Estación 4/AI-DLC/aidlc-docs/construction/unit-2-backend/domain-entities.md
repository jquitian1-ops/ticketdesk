# Unit 2: Fundamentos Backend — Entidades del Dominio

**Proyecto**: TicketDesk Enterprise v1.0  
**Fase**: Construcción  
**Unit**: 2 - Fundamentos Backend  
**Actividad**: 1 - Diseño Funcional: Entidades del Dominio  
**Fecha**: 2026-05-27  

---

## 📋 Contexto Acotado: Fundamentos Backend

**Alcance**: Ciclo de vida de sesión, operaciones de candidato y reclutamiento, gestión de campañas, seguimiento de consentimiento  
**Patrón**: Diseño Dirigido por Dominio con Agregados, Objetos de Valor e Invariantes  

---

## 🎯 8 Agregados

### 1. AgregadoSesión

**Entidad Raíz**: `Sesión`

```
Sesión (Raíz)
├── id: UUID
├── id_candidato: UUID
├── id_campaña: UUID
├── estado: EstadoSesión (CREADA, ACTIVA, PAUSADA, COMPLETADA, ABANDONADA)
├── creada_en: DateTime
├── iniciada_en: DateTime | NULL
├── completada_en: DateTime | NULL
├── abandonada_en: DateTime | NULL
├── última_actividad_en: DateTime
├── metadatos: JSON (dispositivo, ip, ubicación)
└── registro_auditoría: Lista[EntradaAuditoria]

Invariantes:
- Sesión.estado ciclo de vida: CREADA → ACTIVA → (PAUSADA → ACTIVA)* → COMPLETADA | ABANDONADA
- Sesión solo puede ser abandonada si ACTIVA por >5min de inactividad
- Una vez COMPLETADA/ABANDONADA, inmutable (solo lectura)
- creada_en ≤ iniciada_en ≤ completada_en (sin reversiones de tiempo)
```

**Objetos de Valor**:
- `EstadoSesión` enum
- `MetadatosSesión` (tipo_dispositivo, navegador, so, dirección_ip, ubicación)
- `DuraciónSesión` (inicio, fin, segundos_transcurridos)

**Business Rules Applied**:
- RULE-BACKEND-01 (Session Lifecycle)
- RULE-BACKEND-08 (Inactivity Detection)

---

### 2. CandidateAggregate

**Root Entity**: `Candidate`

```
Candidate (Root)
├── id: UUID
├── email: EmailAddress
├── first_name: String
├── last_name: String
├── phone: PhoneNumber | NULL
├── resume_url: S3URL | NULL
├── status: CandidateStatus (REGISTERED, SCREENING, EVALUATED, PASSED, FAILED, ARCHIVED)
├── created_at: DateTime
├── updated_at: DateTime
├── scores: List[EvaluationScore]
└── documents: List[DocumentReference]

Invariants:
- email is unique, validated format
- status never reverts backwards (once PASSED, stays PASSED)
- If status = ARCHIVED, can't be modified
- At most 1 active screening per campaign
```

**Value Objects**:
- `EmailAddress` (validation, normalization)
- `PhoneNumber` (optional, validated format)
- `S3URL` (resume storage location)
- `CandidateStatus` enum
- `EvaluationScore` (score: 0-100, recommendation: PASS/FAIL/REVIEW, timestamp)

**Business Rules Applied**:
- RULE-BACKEND-02 (Candidate Registration)
- RULE-BACKEND-03 (Status Transitions)

---

### 3. ScreeningAggregate

**Root Entity**: `Screening`

```
Screening (Root)
├── id: UUID
├── session_id: UUID (foreign key to Session)
├── campaign_id: UUID
├── rubric_version: Int
├── questions: List[Question]
├── messages: List[Message]
├── state: ScreeningState (STARTED, IN_PROGRESS, COMPLETED, FAILED, PAUSED)
├── started_at: DateTime
├── completed_at: DateTime | NULL
├── token_budget: Int (max 2000 tokens)
├── tokens_used: Int
├── jailbreak_attempts: Int (0-based count)
├── out_of_scope_count: Int (0-based count)
└── transcript_s3_url: S3URL | NULL

Invariants:
- tokens_used ≤ token_budget (strict enforcement)
- jailbreak_attempts capped at 3 (then FAILED)
- out_of_scope_count capped at 3 (then auto-terminate)
- Once COMPLETED/FAILED, immutable
- messages ordered chronologically
```

**Value Objects**:
- `ScreeningState` enum (state machine)
- `Question` (id, text, order, required)
- `Message` (id, role, content, timestamp, tokens, metadata)
- `TokenBudget` (current, limit, remaining)
- `JailbreakAttempt` (pattern_matched, risk_level, timestamp)
- `OutOfScopeViolation` (message_id, violation_type, timestamp)

**Business Rules Applied**:
- RULE-BACKEND-04 (Message Ordering)
- RULE-BACKEND-05 (Jailbreak Escalation)
- RULE-BACKEND-06 (Out-of-Scope Limits)
- RULE-BACKEND-07 (Token Budget)

---

### 4. EvaluationAggregate

**Root Entity**: `Evaluation`

```
Evaluation (Root)
├── id: UUID
├── session_id: UUID
├── campaign_id: UUID
├── screening_id: UUID
├── rubric_version: Int
├── score: Int (0-100)
├── recommendation: Recommendation (PASS, FAIL, REVIEW)
├── confidence: Float (0.0-1.0)
├── dimension_scores: Map[DimensionName → Int] (per-skill breakdown)
├── feedback_json: JSON (structured feedback)
├── citations: List[Citation] (evidence from transcript)
├── fairness_score: FairnessScore
├── status: EvaluationStatus (PENDING, IN_PROGRESS, COMPLETED, FAILED)
├── created_at: DateTime
├── completed_at: DateTime | NULL
└── evaluated_by: SystemName ("EvaluationEngine")

Invariants:
- score ∈ [0, 100]
- recommendation logic: PASS if score ≥ 75, FAIL if score < 50, else REVIEW
- confidence ∈ [0.0, 1.0]
- Once status = COMPLETED, aggregate is immutable (read-only)
- Citations must exist if confidence > 0.8
- One evaluation per session (no duplicates)
```

**Value Objects**:
- `Score` (0-100, with thresholds for recommendation)
- `Recommendation` enum
- `Confidence` (0.0-1.0, indicates evidence strength)
- `DimensionScore` (skill_name, score, weight)
- `Citation` (text_snippet, source_timestamp, fuzzy_match_confidence)
- `FairnessScore` (overall_bias_risk, per-dimension risk, flags)
- `EvaluationStatus` enum
- `Feedback` (structured JSON with sections: strengths, improvements, recommendation_rationale)

**Business Rules Applied**:
- RULE-BACKEND-09 (Evaluation Immutability)
- RULE-BACKEND-10 (Recommendation Logic)

---

### 5. CampaignAggregate

**Root Entity**: `Campaign`

```
Campaign (Root)
├── id: UUID
├── name: String (unique per organization)
├── description: String
├── job_title: String
├── job_context: String (role, level, requirements)
├── rubric: RubricVersion (versioned, immutable)
├── status: CampaignStatus (DRAFT, PUBLISHED, PAUSED, ARCHIVED)
├── published_at: DateTime | NULL
├── archived_at: DateTime | NULL
├── created_by: UserID
├── created_at: DateTime
├── updated_at: DateTime
├── questions: List[Question]
├── consent_template: ConsentDocument
└── email_templates: List[EmailTemplate]

Invariants:
- Campaign.name unique per organization
- rubric cannot be modified after PUBLISHED (versioning enforced)
- status flow: DRAFT → PUBLISHED → (PAUSED ↔ PUBLISHED)* → ARCHIVED
- Once ARCHIVED, campaign is read-only
```

**Value Objects**:
- `CampaignStatus` enum
- `RubricVersion` (version: Int, criteria[], dimensions[], weight_map, created_at, created_by)
- `Question` (id, text, order, type: TEXT/MULTIPLE_CHOICE, required)
- `ConsentDocument` (title, body, version)
- `EmailTemplate` (name, subject, body, variables)

**Business Rules Applied**:
- RULE-BACKEND-11 (Campaign Lifecycle)
- RULE-BACKEND-12 (Rubric Immutability)

---

### 6. ConsentAggregate

**Root Entity**: `Consent`

```
Consent (Root)
├── id: UUID
├── candidate_id: UUID
├── campaign_id: UUID
├── type: ConsentType (DATA_PROCESSING, RECORDING, ANALYTICS)
├── status: ConsentStatus (PENDING, GIVEN, REVOKED, EXPIRED)
├── given_at: DateTime | NULL
├── revoked_at: DateTime | NULL
├── expires_at: DateTime | NULL
├── ip_address: String
├── user_agent: String
└── audit_trail: List[ConsentAuditEntry]

Invariants:
- One Consent per (candidate, campaign, type)
- status flow: PENDING → GIVEN or REVOKED → EXPIRED (after expiry_date)
- revoked_at only set if status = REVOKED
- Revocation is instant, no 24h delay
```

**Value Objects**:
- `ConsentType` enum (DATA_PROCESSING, RECORDING, ANALYTICS)
- `ConsentStatus` enum
- `ConsentAuditEntry` (action, timestamp, ip_address, user_agent)

**Business Rules Applied**:
- RULE-BACKEND-02 (Consent Before Processing)
- RULE-BACKEND-13 (Consent Tracking)

---

### 7. CacheEntryAggregate

**Root Entity**: `CacheEntry`

```
CacheEntry (Root)
├── id: UUID (key)
├── entity_type: String (e.g., "Rubric", "CampaignQuestions")
├── entity_id: UUID
├── value_json: JSON (serialized cached object)
├── expires_at: DateTime
├── created_at: DateTime
├── updated_at: DateTime
├── version: Int (for consistency)
└── ttl: Int (seconds, default 3600)

Invariants:
- Cache is ephemeral, expiry is enforced by Redis
- version increments on every update
- TTL default = 3600s (1 hour), customizable
```

**Value Objects**:
- `CacheKey` (entity_type + entity_id = unique key)
- `CacheTTL` (seconds, min 60, max 86400)
- `CacheValue` (JSON-serializable value)

**Business Rules Applied**:
- RULE-BACKEND-14 (Cache Invalidation)

---

### 8. EventLogAggregate

**Root Entity**: `EventLog`

```
EventLog (Root)
├── id: UUID
├── event_type: String (e.g., "SessionStarted", "EvaluationCompleted")
├── aggregate_id: UUID (root aggregate that emitted event)
├── aggregate_type: String (Session, Screening, Evaluation, etc.)
├── payload: JSON (event data)
├── timestamp: DateTime
├── published_at: DateTime | NULL
├── retry_count: Int (0-based)
├── status: EventStatus (PENDING, PUBLISHED, FAILED, ARCHIVED)
└── error_message: String | NULL

Invariants:
- event_type is well-known constant
- timestamp ≤ published_at
- status flow: PENDING → PUBLISHED or FAILED → ARCHIVED
- FAILED events with retry_count < 5 are retried
```

**Value Objects**:
- `EventType` enum (SessionStarted, ScreeningStarted, MessageExchanged, ScreeningCompleted, EvaluationStarted, EvaluationCompleted, ConsentRevoked, DataDeletionRequested, etc.)
- `EventPayload` (JSON object with event-specific fields)
- `EventStatus` enum
- `EventTimestamp` (with UTC timezone enforcement)

**Business Rules Applied**:
- RULE-BACKEND-15 (Event Publishing)

---

## 💡 10 Value Objects (Summary)

| Value Object | Purpose | Invariant |
|--------------|---------|-----------|
| `SessionStatus` | Session state | Ordered states: CREATED → ACTIVE → COMPLETED\|ABANDONED |
| `SessionMetadata` | Device + location | device_type ∈ {mobile, tablet, desktop} |
| `EmailAddress` | Candidate email | RFC 5322 compliant, unique per system |
| `CandidateStatus` | Candidate lifecycle | Monotonic progression (no reversals) |
| `ScreeningState` | Screening state | STARTED → COMPLETED, FAILED, or PAUSED |
| `Message` | Chat message | ordered by timestamp, immutable once created |
| `TokenBudget` | Token tracking | remaining = limit - used (non-negative) |
| `Recommendation` | Eval recommendation | PASS \| FAIL \| REVIEW (based on score) |
| `Citation` | Evidence reference | fuzzy_match_confidence ≥ 0.7 |
| `FairnessScore` | Bias detection | per-dimension bias risk flags |

---

## 🔄 State Machines

### Session State Lifecycle

```
┌─────────┐
│ CREATED │
└────┬────┘
     │ start()
     ↓
┌──────────┐      pause()       ┌────────┐
│  ACTIVE  ├──────────────────→ │ PAUSED │
└──────────┘                    └────┬───┘
     ↑                               │
     └───────────────── resume()─────┘
     │
     │ (>5min inactive)
     │ complete() or abandon()
     ↓
┌──────────────┐
│ COMPLETED or │
│  ABANDONED   │
└──────────────┘
```

### Screening State Lifecycle

```
┌─────────┐
│ STARTED │
└────┬────┘
     │
     ↓
┌──────────────┐
│ IN_PROGRESS  │──────(jailbreak_attempts ≥ 3)──→ ┌────────┐
│              │                                    │ FAILED │
└────┬─────────┘──────(out_of_scope_count ≥ 3)──→ └────────┘
     │
     │ (all questions answered or timeout)
     ↓
┌──────────┐
│COMPLETED │
└──────────┘
```

### Evaluation Status Lifecycle

```
┌─────────┐
│ PENDING │
└────┬────┘
     │ start_evaluation()
     ↓
┌──────────────┐
│ IN_PROGRESS  │ (Claude API processing)
└────┬─────────┘
     │ (success)
     ↓
┌──────────┐
│COMPLETED │
└──────────┘
     │ (failure)
     └──────→ ┌────────┐
              │ FAILED │
              └────────┘
```

---

## ✅ Aggregate Responsibilities Matrix

| Aggregate | Owns | Publishes Events | Subscribes To |
|-----------|------|------------------|---------------|
| **Session** | Lifecycle, inactivity, metadata | SessionStarted, SessionPaused, SessionCompleted, SessionAbandoned | ConsentRevoked (from Consent) |
| **Candidate** | Profile, registration, status | CandidateRegistered, CandidateStatusChanged | EvaluationCompleted (updates status) |
| **Screening** | Conversation, jailbreaks, token budget | ScreeningStarted, MessageExchanged, ScreeningCompleted, JailbreakDetected | n/a |
| **Evaluation** | Score, recommendation, fairness | EvaluationCompleted, EvaluationFailed | ScreeningCompleted (triggers evaluation) |
| **Campaign** | Questions, rubric, consent template | CampaignPublished, CampaignArchived | n/a |
| **Consent** | Consent status, audit trail | ConsentGiven, ConsentRevoked | n/a |
| **CacheEntry** | Cached data, TTL | n/a | CampaignUpdated, RubricUpdated (cache invalidation) |
| **EventLog** | Event persistence, retry | EventPublished | n/a |

---

## 🔗 Aggregate Relationships

```
Session
  ├── belongs_to: Campaign (campaign_id)
  ├── has_many: Screening (session_id)
  └── has_many: EventLog (aggregate_id for session events)

Candidate
  ├── has_many: Session (candidate_id)
  ├── has_many: Consent (candidate_id)
  └── has_many: Evaluation (candidate_id, via session)

Screening
  ├── belongs_to: Session (session_id)
  ├── belongs_to: Campaign (campaign_id)
  ├── has_many: Message (screening_id)
  └── references: Rubric (campaign_id, rubric_version)

Evaluation
  ├── belongs_to: Session (session_id)
  ├── belongs_to: Screening (screening_id)
  ├── belongs_to: Campaign (campaign_id)
  └── has_many: Citation (evaluation_id)

Campaign
  └── has_many: Screening (campaign_id)

Consent
  ├── belongs_to: Candidate (candidate_id)
  └── belongs_to: Campaign (campaign_id)
```

---

## 📊 Aggregate Sizes (Data Model)

| Aggregate | Typical Size | Example Count |
|-----------|--------------|---------------|
| Session | ~2KB (metadata, status) | 1,000/day |
| Candidate | ~5KB (profile, scores) | 500K total |
| Screening | ~50KB (messages, tokens) | 1,000/day |
| Evaluation | ~20KB (score, feedback, citations) | 1,000/day |
| Campaign | ~30KB (rubric, questions, templates) | 50 total |
| Consent | ~2KB (status, audit trail) | 1,000,000 total |
| CacheEntry | ~1-50KB (depends on cached entity) | Ephemeral |
| EventLog | ~1-5KB (event payload) | 100,000/day |

---

## 🎯 Acceptance Criteria (Actividad 1)

- [x] 8 Aggregates defined with root entities, value objects, invariants
- [x] 10 Value Objects documented with validation rules
- [x] State machines for Session, Screening, Evaluation
- [x] Aggregate relationships mapped (belongs_to, has_many)
- [x] Event publishing responsibilities assigned
- [x] All aggregates immutable after completion
- [x] Cross-aggregate consistency rules documented

---

**Generated**: 2026-05-27  
**Unit**: 2 - Backend Fundamentals  
**Actividad**: 1 - Domain Entities  
**Status**: ✅ COMPLETE
