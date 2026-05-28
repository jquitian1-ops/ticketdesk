# Unit 2: Backend Fundamentals — Business Rules

**Proyecto**: TicketDesk Enterprise v1.0  
**Fase**: Construction  
**Unit**: 2 - Backend Fundamentals  
**Actividad**: 1 - Diseño Funcional: Business Rules  
**Fecha**: 2026-05-27  

---

## 📋 Overview

**10 Business Rules** governing backend operations, with traceability to domain aggregates and acceptance criteria.

---

## 🎯 Business Rules

### RULE-BACKEND-01: Session Lifecycle Management

**Description**: Sessions follow a strict state machine with immutable timestamps.

**Condition**: User initiates screening or moves between states

**Action**:
1. Session created in CREATED state (created_at = now)
2. User clicks "Start" → CREATED → ACTIVE (started_at = now)
3. User can PAUSE → inactivity timer resets on resume
4. Session auto-completes after (questions answered OR 30-min timeout)
5. On completion → COMPLETED (completed_at = now)
6. On manual abandon → ABANDONED (abandoned_at = now, only if ACTIVE >5min)

**Consequence**:
- All timestamps immutable (creation ≤ start ≤ completion, no reversals)
- Audit trail of state transitions
- Enables compliance reporting and analytics

**Source**: functional-design.md § Session Lifecycle
**Affected Aggregate**: SessionAggregate

**Acceptance Criteria**:
- [ ] Session state transitions validated in tests
- [ ] Timestamps ordered chronologically
- [ ] Completed/abandoned sessions are read-only

---

### RULE-BACKEND-02: Consent Before Processing

**Description**: No screening can commence without explicit candidate consent.

**Condition**: Candidate joins screening session

**Action**:
1. Display consent form (legal, data processing, recording)
2. Require explicit checkbox agreement for each consent type
3. Capture consent metadata (ip_address, user_agent, timestamp)
4. Only after ALL consents given → allow session to proceed

**Consequence**:
- Non-compliance is impossible (form blocks progression)
- Audit trail of consents with metadata
- LGPD-compliant (documented, revocable)

**Source**: LGPD Article 8 (Consent Requirement)
**Affected Aggregate**: ConsentAggregate, SessionAggregate

**Acceptance Criteria**:
- [ ] Consent form displays before screening starts
- [ ] All 3 consent types required (DATA_PROCESSING, RECORDING, ANALYTICS)
- [ ] Consent audit entries created with ip/user_agent
- [ ] Session cannot transition to ACTIVE without consents

---

### RULE-BACKEND-03: Candidate Status Transitions

**Description**: Candidate status follows monotonic progression (no reversals).

**Condition**: Candidate completes actions or evaluation concludes

**Action**:
```
REGISTERED → SCREENING → EVALUATED → (PASSED | FAILED)
                                  └→ ARCHIVED (after 30d)
```

1. New candidate → REGISTERED
2. Enters session → SCREENING (first message sent/received)
3. Screening completed → EVALUATED
4. Evaluation score available → PASSED (score ≥ 75) or FAILED (score < 50) or REVIEW
5. After inactivity + email re-engagement → can return to SCREENING
6. Never goes backward (e.g., PASSED → SCREENING not allowed)

**Consequence**:
- Clear progress tracking
- Enables dashboard filtering (show FAILED candidates separately)
- Prevents data integrity issues (can't "undo" a failure)

**Source**: functional-design.md § Candidate Lifecycle
**Affected Aggregate**: CandidateAggregate

**Acceptance Criteria**:
- [ ] Status enum enforces allowed transitions
- [ ] No backward transitions permitted (test validates)
- [ ] ARCHIVED candidates immutable
- [ ] Audit logs all transitions with timestamps

---

### RULE-BACKEND-04: Message Ordering & Immutability

**Description**: Screening messages are ordered chronologically and immutable.

**Condition**: Any message sent/received in screening

**Action**:
1. Each message assigned unique id + sequence number
2. Messages stored in chronological order (timestamp DESC)
3. Once created, message content is READ-ONLY
4. Deletions not allowed (soft-delete if needed, marks is_deleted=true)

**Consequence**:
- Audit trail is trustworthy (no retroactive edits)
- Transcript is legally defensible (immutable record)
- Enables fairness review (no cherry-picking evidence)

**Source**: Compliance requirement (LGPD § 6)
**Affected Aggregate**: ScreeningAggregate

**Acceptance Criteria**:
- [ ] Message.created_at immutable (database constraint)
- [ ] No UPDATE operations on message content
- [ ] Soft-delete only (is_deleted flag, no hard delete)
- [ ] Tests verify ordering after concurrent inserts

---

### RULE-BACKEND-05: Jailbreak Escalation

**Description**: Jailbreak attempts are counted and escalate to termination.

**Condition**: Screening detects prompt injection or security anomaly

**Action**:
1. BotEngine scans user message against 20+ jailbreak patterns
2. If detected:
   - LOW risk: log attempt, continue (user warned)
   - MEDIUM: log, continue, increment counter
   - HIGH: log, block response, increment counter (user sees apology)
   - CRITICAL: log, terminate screening immediately
3. After 3 HIGH/MEDIUM attempts → auto-terminate screening
4. Create AuditLog entry for each attempt

**Consequence**:
- Security: Protects against prompt injection attacks
- Compliance: Maintains audit trail
- UX: Graceful handling (user knows what happened)

**Source**: Security requirement (§ 3.2.1)
**Affected Aggregate**: ScreeningAggregate

**Acceptance Criteria**:
- [ ] jailbreak_attempts counter increments correctly
- [ ] After 3 attempts, screening auto-fails
- [ ] Audit logs created for each HIGH/MEDIUM attempt
- [ ] Tests validate against OWASP Top 10 injection patterns

---

### RULE-BACKEND-06: Out-of-Scope Detection & Limits

**Description**: Questions off-topic are redirected; too many violations auto-terminate.

**Condition**: Screening detects off-topic user message

**Action**:
1. System prompt includes instruction: "If candidate asks off-topic, redirect with friendly message"
2. BotEngine response includes redirect marker
3. Count violations (max 3 per screening)
4. After 3 violations → auto-terminate screening (FAILED state)
5. Audit log: out_of_scope_violations

**Consequence**:
- Maintains screening quality (on-topic answers)
- Fair: candidates who go off-topic 3x are marked fairly
- Graceful: allows some flexibility before termination

**Source**: Screening best practices
**Affected Aggregate**: ScreeningAggregate

**Acceptance Criteria**:
- [ ] out_of_scope_count tracked
- [ ] After 3 violations, screening auto-terminates
- [ ] Audit entries logged
- [ ] Tests verify redirect messages work

---

### RULE-BACKEND-07: Token Budget Enforcement

**Description**: Conversations are constrained by token budget (cost control).

**Condition**: Any message exchanged in screening

**Action**:
1. Screening initialized with token_budget = 2000 tokens
2. Before calling Claude API, check: tokens_used + estimated_new_tokens ≤ token_budget
3. If budget exceeded:
   - Truncate conversation (oldest messages removed, summarized)
   - Re-estimate token count
   - Proceed only if fit
4. If cannot fit: return degraded response ("I'm experiencing limits, please try again")
5. Track tokens_used continuously (audit purposes)

**Consequence**:
- Cost predictability (no runaway API bills)
- Fair: all candidates get similar token allowance
- Graceful degradation (users understand limits)

**Source**: Financial constraint (unit economics requirement)
**Affected Aggregate**: ScreeningAggregate

**Acceptance Criteria**:
- [ ] tokens_used increments accurately (±5%)
- [ ] Budget overflow prevented (test validates)
- [ ] Conversation truncation preserves semantic meaning
- [ ] Audit logs token usage per message

---

### RULE-BACKEND-08: Inactivity Detection & Pause

**Description**: Sessions auto-pause after 5 minutes of inactivity.

**Condition**: No user input for 5+ minutes

**Action**:
1. Backend tracks last_activity_at timestamp
2. Background job (every 2 min) checks: now - last_activity_at > 5min
3. If inactive >5min:
   - Transition Session to PAUSED (if was ACTIVE)
   - Notify candidate: "Your session has been paused. Click to resume."
   - Clear conversation context (cost saving)
4. Candidate can resume within 24h (re-establish context)
5. After 24h of PAUSED → auto-abandon

**Consequence**:
- Cost savings (free up resources)
- Respects candidate time (acknowledges pause)
- Fairness: all candidates get same pause rule
- LGPD compliance (clear session end)

**Source**: Cost optimization + UX best practice
**Affected Aggregate**: SessionAggregate

**Acceptance Criteria**:
- [ ] Inactivity job runs correctly
- [ ] Session transitions to PAUSED at 5min
- [ ] Candidate notified (email/dashboard)
- [ ] After 24h PAUSED → ABANDONED

---

### RULE-BACKEND-09: Evaluation Immutability

**Description**: Once evaluation is complete, it cannot be modified.

**Condition**: Evaluation transitions to COMPLETED status

**Action**:
1. During evaluation (IN_PROGRESS):
   - Score, recommendation, feedback can be updated (Claude re-scoring)
   - Citations being collected
2. When evaluation_completed event published:
   - Status → COMPLETED
   - Aggregate becomes READ-ONLY
   - No further mutations allowed
3. If re-evaluation needed:
   - Create NEW Evaluation record
   - Link both evaluations (evaluation_id_v1, evaluation_id_v2)
   - Use newer evaluation for final decision

**Consequence**:
- Audit trail immutable (legally defensible)
- Fair: candidates can't be surprised by changed scores
- Enables appeals (can compare v1 vs v2)

**Source**: Compliance + fairness requirement
**Affected Aggregate**: EvaluationAggregate

**Acceptance Criteria**:
- [ ] Database constraint: Evaluation.status COMPLETED = immutable
- [ ] Tests verify no UPDATEs after COMPLETED
- [ ] Re-evaluation creates new record with version tracking
- [ ] Audit logs track version history

---

### RULE-BACKEND-10: Recommendation Logic

**Description**: Score maps deterministically to recommendation.

**Condition**: Evaluation scoring complete

**Action**:
```
IF score >= 75:
    recommendation = PASS
ELSE IF score < 50:
    recommendation = FAIL
ELSE (50 <= score < 75):
    recommendation = REVIEW
```

1. Recommendation calculated immediately after scoring
2. Immutable (same as score)
3. REVIEW triggers HITL queue (human review)
4. PASS/FAIL bypass HITL (unless flagged by fairness check)

**Consequence**:
- Deterministic: no ambiguity in thresholds
- Fair: same rules apply to all candidates
- Clear decision path (HITL knows which go to review)

**Source**: functional-design.md § Scoring Thresholds
**Affected Aggregate**: EvaluationAggregate

**Acceptance Criteria**:
- [ ] Score-to-recommendation mapping tested
- [ ] Boundary cases (49, 50, 74, 75) verified
- [ ] Recommendation matches recommendation field
- [ ] REVIEW cases route to HITL queue

---

### RULE-BACKEND-11: Campaign Lifecycle

**Description**: Campaigns have a strict lifecycle with version control.

**Condition**: Campaign created, published, or archived

**Action**:
```
DRAFT → PUBLISHED → (PAUSED ↔ PUBLISHED)* → ARCHIVED
```

1. New campaign → DRAFT
2. Admin reviews → PUBLISHED (enables screenings)
3. Admin can PAUSE (stops new screenings) and resume
4. After hiring complete → ARCHIVED (read-only, no new screenings)
5. Never delete campaigns (audit trail)

**Consequence**:
- Clear governance (who can screen with which campaign)
- Audit trail (track campaign versions)
- Fair: all candidates in same campaign use same rubric version

**Source**: Campaign management requirement
**Affected Aggregate**: CampaignAggregate

**Acceptance Criteria**:
- [ ] Campaign.status enforces state machine
- [ ] Archived campaigns immutable
- [ ] Published campaigns linked to screening sessions
- [ ] Audit logs track status changes

---

### RULE-BACKEND-12: Rubric Immutability & Versioning

**Description**: Rubric is immutable once published; changes create new version.

**Condition**: Campaign published with rubric OR rubric updated

**Action**:
1. While campaign DRAFT: rubric can be edited
2. When campaign PUBLISHED: rubric.version incremented, locked
3. To change rubric: create new version (rubric_version + 1)
4. Old screenings use old rubric version (not changed retroactively)
5. New screenings use new rubric version
6. Evaluation stores rubric_version for traceability

**Consequence**:
- Fair: same version rubric applies to cohort of candidates
- Audit trail: can trace which version scored which candidates
- No retroactive scoring changes (defensible)

**Source**: Compliance + fairness requirement
**Affected Aggregate**: CampaignAggregate

**Acceptance Criteria**:
- [ ] Rubric versioning enforced in code
- [ ] Old versions preserved
- [ ] Screening.rubric_version and Evaluation.rubric_version match
- [ ] Tests verify immutability

---

### RULE-BACKEND-13: Consent Tracking & Audit Trail

**Description**: All consent changes audited with metadata.

**Condition**: Candidate gives or revokes consent

**Action**:
1. Consent.given_at = timestamp, with ip_address + user_agent captured
2. If candidate revokes consent:
   - Consent.revoked_at = timestamp
   - Consent.status → REVOKED
   - Create ConsentAuditEntry (action=REVOKED, ip, user_agent)
   - Stop any pending re-engagement emails
   - Mark PII as redacted
3. Audit trail immutable (append-only)

**Consequence**:
- LGPD-compliant (consent tracking)
- Defensible: can prove candidate consented or revoked
- Data governance: know who gave consent when

**Source**: LGPD Article 8
**Affected Aggregate**: ConsentAggregate

**Acceptance Criteria**:
- [ ] Consent.given_at/revoked_at immutable
- [ ] Audit trail append-only
- [ ] IP/user_agent captured on consent
- [ ] Revocation blocks downstream processing

---

### RULE-BACKEND-14: Cache Invalidation Strategy

**Description**: Cached data expires and is invalidated on source updates.

**Condition**: Rubric updated OR campaign published

**Action**:
1. Cache entries have TTL = 3600s (1 hour default)
2. On CampaignPublished event:
   - Invalidate all cache entries for that campaign_id
   - Clear rubric cache
3. Background job: delete expired cache entries (once per hour)
4. If cache miss: fetch from DB, store in cache, return

**Consequence**:
- Performance: cached rubrics avoid DB hits
- Consistency: stale cache expires automatically
- Event-driven: invalidation on source change

**Source**: Performance requirement (p95 < 500ms)
**Affected Aggregate**: CacheEntryAggregate

**Acceptance Criteria**:
- [ ] Cache TTL enforced
- [ ] Event-driven invalidation working
- [ ] Background cleanup job running
- [ ] Cache hit rate >85% tracked

---

### RULE-BACKEND-15: Event Publishing & Reliability

**Description**: Events published to Redis Pub/Sub with retry logic.

**Condition**: Any significant domain event (SessionStarted, EvaluationCompleted, etc.)

**Action**:
1. Service publishes event to Redis Pub/Sub (topic = event_type)
2. Event stored in EventLog (status = PENDING)
3. Subscribers (e.g., HITLService) consume event
4. On success: EventLog.status = PUBLISHED
5. On failure: retry up to 5 times (exponential backoff: 1s, 2s, 4s, 8s, 16s)
6. After 5 failures: EventLog.status = FAILED, alert ops

**Consequence**:
- Reliable: events eventually delivered
- Auditable: all events logged
- Decoupled: publishers don't block on subscribers

**Source**: Event-driven architecture requirement
**Affected Aggregate**: EventLogAggregate

**Acceptance Criteria**:
- [ ] Events published to Redis
- [ ] EventLog records created
- [ ] Retry logic working (test with mock failure)
- [ ] Failed events alertable

---

## 📊 Business Rules Traceability Matrix

| Rule | Aggregate | Event | Acceptance Criteria |
|------|-----------|-------|-------------------|
| RULE-BACKEND-01 | Session | SessionStarted, SessionCompleted | State machine enforced |
| RULE-BACKEND-02 | Consent | ConsentGiven | Form blocks progression |
| RULE-BACKEND-03 | Candidate | CandidateStatusChanged | Monotonic transitions |
| RULE-BACKEND-04 | Screening | MessageExchanged | Immutable messages |
| RULE-BACKEND-05 | Screening | JailbreakDetected | Auto-terminate at 3 |
| RULE-BACKEND-06 | Screening | ScreeningCompleted | Auto-terminate at 3 violations |
| RULE-BACKEND-07 | Screening | MessageExchanged | Budget not exceeded |
| RULE-BACKEND-08 | Session | SessionPaused | Auto-pause at 5min |
| RULE-BACKEND-09 | Evaluation | EvaluationCompleted | Immutable after COMPLETED |
| RULE-BACKEND-10 | Evaluation | EvaluationCompleted | Deterministic recommendation |
| RULE-BACKEND-11 | Campaign | CampaignPublished | Status machine enforced |
| RULE-BACKEND-12 | Campaign | CampaignUpdated | Rubric versioning immutable |
| RULE-BACKEND-13 | Consent | ConsentRevoked | Audit trail append-only |
| RULE-BACKEND-14 | Cache | CampaignUpdated | TTL enforced, invalidation triggered |
| RULE-BACKEND-15 | EventLog | (all) | Retry logic with backoff |

---

## 🎯 Acceptance Criteria (Actividad 1)

- [x] 10 Business Rules documented with source traceability
- [x] Each rule has Condition, Action, Consequence sections
- [x] Aggregate ownership clear for each rule
- [x] Event triggers identified
- [x] Acceptance criteria for each rule defined
- [x] Traceability matrix complete

---

**Generated**: 2026-05-27  
**Unit**: 2 - Backend Fundamentals  
**Actividad**: 1 - Business Rules  
**Status**: ✅ COMPLETE
