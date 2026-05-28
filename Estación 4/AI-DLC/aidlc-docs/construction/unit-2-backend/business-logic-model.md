# Unit 2: Backend Fundamentals — Business Logic Model

**Proyecto**: TicketDesk Enterprise v1.0  
**Fase**: Construction  
**Unit**: 2 - Backend Fundamentals  
**Actividad**: 1 - Diseño Funcional: Business Logic Model (E2E Flows)  
**Fecha**: 2026-05-27  

---

## 📋 Overview

**5 End-to-End Flows** describing complete business processes with state transitions, error handling, and event publishing.

---

## 🎯 Flow 1: Create Session & Obtain Consent

**Duration**: 3-5 minutes  
**Actors**: Candidate, Backend API, ConsentService  
**Trigger**: Candidate clicks "Start Screening" from campaign page  

### Pre-conditions
- Campaign is PUBLISHED
- Candidate is REGISTERED in system
- Network connection active

### Steps

1. **POST /api/campaigns/{campaign_id}/sessions**
   - Request: `{ candidate_id, metadata: { device, ip, location } }`
   - Backend creates Session aggregate
   - Session.status = CREATED
   - Session.created_at = now (immutable)
   - Return: `{ session_id, consent_form_url }`

2. **Load Consent Form (GET /api/sessions/{session_id}/consent)**
   - Return: ConsentDocument (3 consent types: DATA_PROCESSING, RECORDING, ANALYTICS)
   - Frontend displays form with legal text
   - Checkboxes required for all 3

3. **Candidate Reviews & Agrees**
   - Frontend shows:
     - "I agree to data processing" (required)
     - "I agree to be recorded" (required)
     - "I agree to analytics" (optional, but recommended)
   - Candidate must check all
   - Click "I Agree" button

4. **POST /api/sessions/{session_id}/consent**
   - Request: `{ consent_types: [DATA_PROCESSING, RECORDING, ANALYTICS], ip_address, user_agent }`
   - ConsentService creates 3 Consent aggregates (one per type)
   - Consent.status = GIVEN
   - Consent.given_at = now
   - Capture metadata (ip_address, user_agent)
   - Publish event: **ConsentGiven** (topic: consent.given)
   - Return: `{ consent_ids, consent_given_at }`

5. **Transition Session to ACTIVE**
   - POST /api/sessions/{session_id}/start
   - Session.status = CREATED → ACTIVE
   - Session.started_at = now
   - Publish event: **SessionStarted** (topic: session.started)
   - Return: `{ session_id, screening_ready }`

### Success Path
- Candidate sees chat window
- Session.status = ACTIVE
- Inactivity timer starts

### Error Paths

**Error 1: Campaign Not Found**
```
Step 1: Campaign lookup fails
→ Return 404 Not Found
→ Frontend shows: "Campaign not available"
```

**Error 2: Consent Not Complete**
```
Step 3: Candidate unchecks checkbox
→ "I Agree" button disabled
→ Frontend shows: "Please agree to all required items"
```

**Error 3: Network Failure During Consent**
```
Step 4: POST fails (timeout)
→ Frontend shows: "Connection error, please try again"
→ Retry button enabled (idempotent POST)
```

### Post-conditions
- Session.status = ACTIVE
- 3 Consent records exist (DATA_PROCESSING, RECORDING, ANALYTICS all GIVEN)
- Events published: SessionStarted, ConsentGiven
- Candidate can now start screening

---

## 🎯 Flow 2: Screening Exchange Message

**Duration**: 2-8 hours (campaign-dependent)  
**Actors**: Candidate, BotEngine, ScreeningService, EvaluationService  
**Trigger**: Candidate types message in chat  

### Pre-conditions
- Session is ACTIVE
- Screening started (has opening message from bot)
- Candidate has valid Consent (DATA_PROCESSING = GIVEN)

### Steps

1. **Candidate Types Message**
   - Frontend: User enters text in chat input
   - Sends: POST /api/conversations/{conversation_id}/messages
   - Request: `{ role: "user", content, timestamp }`

2. **Backend Validation**
   - Parse message (UTF-8 validation)
   - Check message length (max 5000 chars)
   - Sanitize (no HTML/script tags)
   - Detect language (textblob)
   - If non-English: translate to English for Claude (keep original for display)

3. **Jailbreak Detection**
   - BotEngine.scan_jailbreak(content)
   - Check against 20+ regex patterns:
     - Prompt injection markers ("Ignore previous", "You are now", etc.)
     - Encoding tricks (base64, hex escapes)
     - Token manipulation ("system prompt", "instructions override")
     - Excessive punctuation/symbols (anomaly detection)
   - Return: risk_level (LOW, MEDIUM, HIGH, CRITICAL)

4. **Risk Assessment**
   ```
   IF risk_level == CRITICAL:
       → Block response, terminate screening
       → Screening.status = FAILED
       → Publish event: ScreeningFailed
       → Return to candidate: "Your session ended due to suspicious activity"
   
   ELSE IF risk_level == HIGH:
       → Increment Screening.jailbreak_attempts
       → Block response, show warning
       → Return to candidate: "That request violates our policies"
   
   ELSE IF risk_level == MEDIUM:
       → Increment Screening.jailbreak_attempts
       → Log attempt (audit)
       → Continue (with warning)
   
   ELSE:
       → Continue normally
   ```

5. **Token Budget Check**
   ```
   estimated_tokens = estimate_tokens(message_content)
   IF Screening.tokens_used + estimated_tokens > Screening.token_budget:
       → Truncate conversation (oldest messages removed, summarized)
       → Retry estimation
       IF still exceeds budget:
           → Return degraded response: "I'm experiencing limits, please try later"
           → Publish event: TokenBudgetExceeded
   ```

6. **Call Claude API (Streaming)**
   - BotEngine constructs system_prompt (role, job context, rubric, instructions)
   - system_prompt includes: "If candidate asks off-topic, redirect..."
   - messages = [... conversation history ..., { role: "user", content }]
   - Call: client.messages.create(model="claude-3-5-sonnet", stream=True, messages, system=system_prompt)
   - Collect tokens stream (real-time SSE/WebSocket to frontend)
   - Stop reason: end_turn or max_tokens or stop_sequence

7. **Detect Out-of-Scope (Instruction-Based)**
   - Monitor response for redirect markers:
     - "Let's get back to...", "That's outside my scope...", "I'm here to help with..."
   - If detected: increment Screening.out_of_scope_count
   - After 3 violations: auto-terminate (Screening.status = FAILED)

8. **Store Message Pair**
   - Create Message aggregate (user + assistant, both immutable)
   - Message.role = "user" | "assistant"
   - Message.content = (original language)
   - Message.tokens_used = estimated + actual from API
   - Message.timestamp = now (immutable)
   - Screening.tokens_used += message.tokens_used
   - Persist both messages (transactional)

9. **Check Continuation**
   ```
   IF Screening.jailbreak_attempts >= 3:
       → Screening.status = FAILED
       → Publish event: ScreeningCompleted
       → Return: "Your screening has ended"
   
   ELSE IF Screening.out_of_scope_count >= 3:
       → Screening.status = FAILED
       → Publish event: ScreeningCompleted
       → Return: "Your screening has ended"
   
   ELSE IF all_questions_answered_OR_timeout_reached:
       → Screening.status = COMPLETED
       → Publish event: ScreeningCompleted
       → Return: "Thank you! Your screening is complete. We'll review and get back to you."
   
   ELSE:
       → Continue (user can send next message)
   ```

10. **Publish Event**
    - Event: **MessageExchanged**
    - Payload: { session_id, message_id, role, tokens_used, timestamp, jailbreak_detected }

### Success Path
- Message stored (immutable)
- Assistant response streamed to frontend
- Tokens tracked
- Screening continues (or completes if all questions answered)

### Error Paths

**Error 1: Claude API Timeout**
```
Step 6: client.messages.create timeout (>10s)
→ Circuit breaker trips
→ Return degraded response: "I'm experiencing delays..."
→ Publish event: DegradedMode
→ Try again with cached response
```

**Error 2: Message Contains Jailbreak (HIGH)**
```
Step 4: Jailbreak detected
→ Increment jailbreak_attempts (now = 1)
→ Don't call Claude
→ Return: "That request violates our policies. Please stay on topic."
→ After 3 such attempts → Screening.status = FAILED
```

**Error 3: Token Budget Exceeded**
```
Step 5: tokens_used exceeds budget
→ Truncate conversation
→ Return degraded response
→ Candidate sees: "I'm experiencing limits, please try later"
→ Prompt them to submit what they have
```

**Error 4: Message Malformed**
```
Step 2: Sanitization fails
→ Return 400 Bad Request
→ Frontend shows: "Message format invalid"
```

### Post-conditions
- Message pair persisted (user + assistant, both immutable)
- Screening.tokens_used incremented
- Events published (MessageExchanged, possibly ScreeningCompleted)
- Session.last_activity_at = now (inactivity timer reset)

---

## 🎯 Flow 3: Complete Screening & Trigger Evaluation

**Duration**: <1 second  
**Actors**: ScreeningService, EvaluationService, EventBus  
**Trigger**: ScreeningCompleted event published  

### Pre-conditions
- Screening status = COMPLETED (or FAILED with 3 jailbreaks)
- All messages stored
- Transcript captured

### Steps

1. **Generate Transcript**
   - Collect all messages (user + assistant) from Screening
   - Convert to JSON structure:
     ```json
     {
       "session_id": "...",
       "screening_id": "...",
       "created_at": "...",
       "completed_at": "...",
       "duration_seconds": 3600,
       "message_count": 15,
       "messages": [
         { "role": "user", "content": "...", "timestamp": "..." },
         { "role": "assistant", "content": "...", "timestamp": "..." }
       ],
       "metadata": { "tokens_used": 1850, "language": "en", "jailbreak_attempts": 0 }
     }
     ```

2. **Upload to S3**
   - S3 key: `transcriptions/{session_id}/{screening_id}.json`
   - Encryption: KMS key (at-rest + in-transit)
   - Versioning: enabled
   - Lifecycle: 7-year retention (compliance), then delete
   - Create AuditLog: ACTION=TRANSCRIPT_UPLOADED

3. **Create Transcription Aggregate**
   - Generate signed URL (expires 24h)
   - Transcription.session_id = session_id
   - Transcription.audio_url = s3_url (for future audio recordings)
   - Transcription.text_url = s3_url (JSON transcript)
   - Transcription.created_at = now
   - Publish event: **TranscriptionCreated**

4. **Publish ScreeningCompleted Event**
   - Event: **ScreeningCompleted**
   - Topic: screening.completed
   - Payload:
     ```json
     {
       "screening_id": "...",
       "session_id": "...",
       "candidate_id": "...",
       "campaign_id": "...",
       "status": "COMPLETED",
       "message_count": 15,
       "tokens_used": 1850,
       "transcript_url": "s3://...",
       "completed_at": "2026-05-27T14:30:00Z"
     }
     ```

5. **Subscribers Consume Event**
   - EvaluationService subscribes to screening.completed
   - Receives ScreeningCompleted event
   - Triggers Evaluation start (see Flow 4)

### Success Path
- Screening marked COMPLETED (immutable)
- Transcript stored in S3
- Event published
- EvaluationService begins evaluation automatically

### Error Paths

**Error 1: S3 Upload Fails**
```
Step 2: S3.put_object times out
→ Retry (up to 3 times with exponential backoff)
→ If all fail: EventLog.status = FAILED, alert ops
→ Screening.status stays COMPLETED (don't block)
→ Manual recovery: ops can retry upload
```

**Error 2: Event Publish Fails**
```
Step 4: Redis Pub/Sub times out
→ EventLog.status = PENDING
→ Retry job runs (every 5 min)
→ After 5 failures: EventLog.status = FAILED
```

### Post-conditions
- Screening.status = COMPLETED (immutable)
- Transcript in S3 (encrypted, versioned, 7-year retention)
- ScreeningCompleted event published
- EvaluationService triggered (asynchronous)

---

## 🎯 Flow 4: Evaluate Screening & Generate Score

**Duration**: 5-10 seconds  
**Actors**: EvaluationService, Claude API, CitationExtractor, FairnessCalculator  
**Trigger**: ScreeningCompleted event  

### Pre-conditions
- Screening completed + transcript available
- Campaign published with rubric
- EvaluationService listening on screening.completed topic

### Steps

1. **Load Rubric (Cached)**
   - EvaluationService receives ScreeningCompleted event
   - Query: Rubric for campaign_id + rubric_version
   - Check Redis cache (TTL = 1h)
   - If cache hit: use cached rubric (no DB hit)
   - If cache miss: load from DB, cache in Redis
   - Rubric contains: dimensions[], scoring_criteria, weights

2. **Call Claude API for Scoring**
   - Construct prompt:
     ```
     You are an expert recruiter evaluating a candidate screening.
     
     Rubric Dimensions:
     - Technical Skills (weight: 40%)
     - Communication (weight: 30%)
     - Problem Solving (weight: 20%)
     - Leadership (weight: 10%)
     
     Scoring Criteria:
     - 90-100: Exceptional, exceeds expectations
     - 75-89: Strong, meets all requirements
     - 50-74: Adequate, some gaps
     - <50: Weak, significant gaps
     
     Transcript:
     [insert messages from screening]
     
     Provide JSON response:
     {
       "overall_score": 85,
       "dimension_scores": {
         "Technical Skills": { "score": 88, "evidence": "..." },
         "Communication": { "score": 82, "evidence": "..." },
         ...
       },
       "recommendation": "PASS",
       "feedback": {
         "strengths": [...],
         "improvements": [...],
         "rationale": "..."
       }
     }
     ```
   - Call: client.messages.create(model="claude-3-5-sonnet", response_format={"type": "json_object"}, ...)
   - Parse JSON response
   - Validate: score ∈ [0, 100], recommendation ∈ {PASS, FAIL, REVIEW}

3. **Extract Citations (Fuzzy Matching)**
   - CitationExtractor receives dimension_scores with evidence strings
   - For each evidence string: fuzzy match against transcript messages
   - RapidFuzz library: find best matching message (confidence >70%)
   - Citation aggregate:
     ```
     Citation {
       evaluation_id: UUID,
       text_snippet: str (max 200 chars),
       source_timestamp: datetime,
       confidence: float (0.7-1.0)
     }
     ```
   - Store all citations (immutable)

4. **Calculate Fairness Score**
   - FairnessCalculator analyzes feedback for bias signals
   - Check for patterns:
     - Gender bias: keywords like "assertive", "aggressive" (gendered language)
     - Age bias: "young", "energetic", "overqualified"
     - Demographic signals in feedback
   - FairnessScore aggregate:
     ```
     FairnessScore {
       evaluation_id: UUID,
       overall_bias_risk: float (0.0-1.0),
       per_dimension_risk: Map[dimension → float],
       flags: List[BiasFlag]
     }
     ```
   - If bias_risk > 0.3: flag for HITL review (override recommendation to REVIEW)

5. **Calculate Final Recommendation**
   ```
   score = dimension_scores weighted average
   
   IF fairness_score.bias_risk > 0.3:
       recommendation = REVIEW (force HITL)
   ELSE IF score >= 75:
       recommendation = PASS
   ELSE IF score < 50:
       recommendation = FAIL
   ELSE:
       recommendation = REVIEW
   ```

6. **Create Evaluation Aggregate**
   - Evaluation aggregate (immutable):
     ```
     Evaluation {
       id: UUID,
       session_id: UUID,
       screening_id: UUID,
       campaign_id: UUID,
       score: 85,
       recommendation: PASS,
       confidence: 0.92,
       dimension_scores: {...},
       citations: [Citation, Citation, ...],
       fairness_score: {...},
       status: COMPLETED,
       completed_at: now
     }
     ```
   - Persist to DB (transactional with citations)

7. **Publish EvaluationCompleted Event**
   - Event: **EvaluationCompleted**
   - Topic: evaluation.completed
   - Payload:
     ```json
     {
       "evaluation_id": "...",
       "session_id": "...",
       "candidate_id": "...",
       "score": 85,
       "recommendation": "PASS",
       "completed_at": "2026-05-27T14:35:00Z"
     }
     ```

### Success Path
- Evaluation created (COMPLETED, immutable)
- Citations extracted (>85% accuracy)
- Fairness calculated
- Event published

### Error Paths

**Error 1: Claude API Fails**
```
Step 2: API returns error
→ Retry up to 3 times
→ If all fail: Evaluation.status = FAILED
→ EventLog.status = FAILED
→ Publish EvaluationFailed event
→ Ops alert
```

**Error 2: Fairness Calculation Shows High Bias**
```
Step 4: bias_risk = 0.45
→ Force recommendation = REVIEW
→ Flag for HITL with bias alert
→ Auditor notified
```

**Error 3: Citation Extraction Fails**
```
Step 3: No matches found
→ confidence = 0.0
→ Still complete evaluation
→ Flag in fairness check (missing evidence)
→ Force REVIEW if confidence too low
```

### Post-conditions
- Evaluation.status = COMPLETED (immutable)
- Citations extracted and stored
- Fairness score calculated
- EvaluationCompleted event published
- Candidate status updated to EVALUATED
- If recommendation = REVIEW: triggers HITL queue (Unit 6)

---

## 🎯 Flow 5: Auto-Expire Inactive Sessions

**Duration**: < 1 second (per session)  
**Actors**: SessionExpiryJob, SessionService, EventBus  
**Trigger**: Background job (every 2 minutes)  

### Pre-conditions
- Background job scheduled (Celery task)
- Sessions in PAUSED or ACTIVE state exist

### Steps

1. **Query Inactive Sessions**
   ```sql
   SELECT * FROM sessions 
   WHERE status IN ('ACTIVE', 'PAUSED')
   AND last_activity_at < now() - INTERVAL '5 minutes'
   AND status != 'COMPLETED' AND status != 'ABANDONED'
   ```

2. **For Each Inactive Session**
   - Check: session.status and time since last_activity_at
   
   **If status = ACTIVE and inactive > 5 min:**
   ```
   → Session.status = PAUSED
   → Candidate notified (email + dashboard)
   → Message: "Your session has been paused due to inactivity"
   → Publish event: SessionPaused
   ```
   
   **If status = PAUSED and inactive > 24 hours:**
   ```
   → Session.status = ABANDONED
   → Publish event: SessionAbandoned
   → No more resumption allowed
   → Candidate can start new session
   ```

3. **Update Timestamps**
   - Session.paused_at or Session.abandoned_at = now (immutable)
   - Session.last_activity_at stays as-is (immutable)

4. **Publish Events**
   - Event: **SessionPaused** or **SessionAbandoned**
   - Topic: session.paused or session.abandoned
   - Payload: { session_id, candidate_id, status, paused_at/abandoned_at }

5. **Cleanup**
   - If abandoned: clear Redis session state (free memory)
   - Mark session for archival (audit only)
   - Update Candidate.status if all sessions abandoned (for reporting)

### Success Path
- Inactive sessions transitioned (ACTIVE → PAUSED → ABANDONED)
- Candidate notified
- Events published

### Error Paths

**Error 1: Job Crashes**
```
→ Retry on next cycle (2 min later)
→ Idempotent (same result if run twice)
```

**Error 2: Notification Fails**
```
→ Don't block session transition
→ Log failure for manual follow-up
→ Candidate sees status change on next login
```

### Post-conditions
- Inactive sessions transitioned (PAUSED or ABANDONED)
- Timestamps immutable
- Events published
- Resources freed (memory in Redis)

---

## 📊 Event Flow Diagram

```
Create Session & Consent
        ↓
    [SessionStarted]
    [ConsentGiven]
        ↓
Screening Exchange (Loop)
        ↓
    [MessageExchanged] × N
        ↓
Complete Screening
        ↓
    [ScreeningCompleted]
        ↓
Evaluate Screening
        ↓
    [EvaluationCompleted]
        ↓
    (If recommendation = REVIEW)
        ↓
HITL Queue (Unit 6)
        ↓
    [HITLDecisionMade]
        ↓
Inactivity Detection (Background)
        ↓
    [SessionPaused] → [SessionAbandoned]
```

---

## 🎯 Acceptance Criteria (Actividad 1)

- [x] 5 E2E flows documented with steps, error paths, post-conditions
- [x] Each flow includes state transitions (immutability enforced)
- [x] Events published clearly identified
- [x] Error handling for network, timeout, business logic failures
- [x] Pre/post-conditions for each flow
- [x] All business rules applied and traceable
- [x] Aggregate responsibilities clear in each flow

---

**Generated**: 2026-05-27  
**Unit**: 2 - Backend Fundamentals  
**Actividad**: 1 - Business Logic Model (E2E Flows)  
**Status**: ✅ COMPLETE
