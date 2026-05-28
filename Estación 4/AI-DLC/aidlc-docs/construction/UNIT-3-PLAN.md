# Unit 3: BotEngine — Plan de Ejecución

**Proyecto**: TicketDesk Enterprise v1.0  
**Fase**: Construction  
**Unit**: 3 - BotEngine (Claude API Integration + Screening Logic)  
**Duración Estimada**: Semanas 3-5 (2-3 semanas)  
**Team**: 1 Backend Engineer  
**Bloqueador**: Unit 1 ✅, Unit 2 (in progress)  
**Bloquea**: Unit 6 (depends on events)  
**Status**: ⏳ Pending Unit 2 completion

---

## 📋 Objetivo Unit 3

Construir el **motor de screening conversacional** que:

1. ✅ Se conecta con Claude API (Anthropic SDK)
2. ✅ Gestiona flujo de preguntas (branching logic)
3. ✅ Detecta jailbreaks (prompt injection protection)
4. ✅ Detecta out-of-scope (off-topic handling)
5. ✅ Almacena transcripciones (S3)
6. ✅ Maneja sesiones (Redis state)
7. ✅ Publica eventos (para EvaluationEngine)
8. ✅ Implementa fallback graceful (circuit breaker)

**Métricas de éxito**:
- Claude API integration working
- 10 unit tests + 5 integration tests
- Jailbreak detection >95% accuracy
- Response latency <3s (p99)
- Graceful degradation when Claude API down

---

## 🎯 5 Actividades de Unit 3

### Actividad 1: Diseño Funcional (3-4 horas)

#### Qué genera:
- `domain-entities.md` (500+ líneas)
- `business-rules.md` (400+ líneas)
- `business-logic-model.md` (600+ líneas)

#### 1.1 Domain Entities:

**Bounded Context**: Conversational Screening Engine

**4 Aggregates**:

1. **ConversationAggregate**:
   - Entity: `Conversation` (id, session_id, messages[], state, metadata)
   - Value Objects: `ConversationState` (STARTED, IN_PROGRESS, COMPLETED, FAILED)
   - Rules: Immutable after completion, messages ordered by timestamp

2. **MessageAggregate**:
   - Entity: `Message` (id, conversation_id, role, content, timestamp, tokens_used)
   - Value Objects: `Role` (USER, ASSISTANT, SYSTEM), `TokenCount`
   - Rules: Content immutable, timestamp immutable, token count auto-calculated

3. **JailbreakDetectionAggregate**:
   - Entity: `JailbreakAttempt` (id, message_id, detected_at, risk_level, pattern_matched)
   - Value Objects: `RiskLevel` (LOW, MEDIUM, HIGH, CRITICAL), `JailbreakPattern`
   - Rules: Logged for audit, may trigger session termination if CRITICAL

4. **TranscriptionAggregate**:
   - Entity: `Transcription` (id, session_id, audio_url, text_url, language, created_at)
   - Value Objects: `TranscriptionUrl` (S3 URI with expiration), `Language`
   - Rules: S3 URLs expire in 24h, audit trail on access

**Value Objects** (8 total):
- `ConversationState`: state machine values
- `Role`: actor in conversation
- `TokenCount`: usage tracking
- `RiskLevel`: severity classification
- `JailbreakPattern`: regex + ML patterns
- `TranscriptionUrl`: S3 signed URL
- `Language`: ISO 639-1 code
- `ClaudeResponse`: streaming tokens + stop reason

**Acceptance Criteria**:
- [ ] 4 Aggregates defined
- [ ] 8 Value Objects with invariants
- [ ] State machines for Conversation
- [ ] All entities immutable after completion

---

#### 1.2 Business Rules (10 rules):

1. **RULE-BOT-01**: Message Ordering
   - Condition: Message received
   - Action: Insert in chronological order, assign sequence number
   - Consequence: Ensures conversation coherence

2. **RULE-BOT-02**: Jailbreak Detection
   - Condition: User message contains suspicious patterns
   - Action: Scan against 20+ regex + ML model
   - Consequence: If HIGH/CRITICAL, flag for review, may block response

3. **RULE-BOT-03**: Out-of-Scope Detection
   - Condition: Message off-topic (not about job/skills)
   - Action: Claude detects via system prompt instruction
   - Consequence: Bot redirects to topic, counts as violation

4. **RULE-BOT-04**: Token Budget
   - Condition: Conversation total tokens > 2000
   - Action: Truncate context, summarize early messages
   - Consequence: Keeps API calls efficient

5. **RULE-BOT-05**: Response Timeout
   - Condition: Claude API takes >10s to respond
   - Action: Cancel request, return degraded response
   - Consequence: User sees apology + retry option, circuit breaker trips

6. **RULE-BOT-06**: Transcription Retention
   - Condition: Session completed
   - Action: Upload audio/text to S3, store URL + metadata
   - Consequence: Audit trail + evidence preserved

7. **RULE-BOT-07**: Graceful Degradation
   - Condition: Claude API down (circuit breaker open)
   - Action: Return cached responses or canned messages
   - Consequence: User experience degrades but doesn't fail

8. **RULE-BOT-08**: Session Pause
   - Condition: User inactive >5 minutes
   - Action: Pause conversation, require re-engagement
   - Consequence: Cost savings + respects candidate's time

9. **RULE-BOT-09**: Language Detection
   - Condition: User types in non-English
   - Action: Detect via textblob, translate to English for Claude
   - Consequence: Bot responds in original language

10. **RULE-BOT-10**: Context Injection Prevention
    - Condition: System prompt + conversation template
    - Action: Escape user input, validate no injection
    - Consequence: Prevents prompt injection attacks

---

#### 1.3 Business Logic Model (5 E2E flows):

1. **Flow 1: Start Conversation** (400 words)
   - Pre-conditions: Session created, consent given
   - Steps:
     1. POST /api/sessions/{id}/conversations
     2. Initialize Conversation aggregate
     3. Create system prompt (role, job context, rubric)
     4. Send opening message to Claude API
     5. Store response in messages array
     6. Publish event: ConversationStarted
   - Error handling: Claude API down → degrade to canned greeting
   - Output: First bot message

2. **Flow 2: Exchange Message** (600 words)
   - Pre-conditions: Conversation in progress
   - Steps:
     1. POST /api/conversations/{id}/messages
     2. Parse user message, validate UTF-8
     3. Detect language (if not English, translate)
     4. Scan jailbreak patterns (regex + ML)
     5. If jailbreak detected: audit log + maybe block
     6. Add to conversation history
     7. Call Claude API with streaming
     8. Collect tokens, detect out-of-scope
     9. Store assistant message
     10. Publish event: MessageExchanged
   - Streaming: Real-time token arrival via WebSocket
   - Error: Timeout → circuit breaker, degrade

3. **Flow 3: Detect Out-of-Scope** (400 words)
   - Trigger: Message content doesn't match job context
   - Steps:
     1. Claude system prompt includes: "If user asks off-topic, redirect"
     2. Monitor response for redirect markers
     3. Count violations (max 3 allowed)
     4. After 3 violations: auto-terminate conversation
     5. Audit log: out-of-scope count
   - State: out_of_scope_count in Conversation

4. **Flow 4: Complete Conversation** (500 words)
   - Pre-conditions: Candidate says they're done OR 30 min timeout OR 3 out-of-scope
   - Steps:
     1. Transition Conversation to COMPLETED
     2. Collect all messages + tokens + duration
     3. Send full transcript to S3 (S3 key: session_id/conversation.json)
     4. Generate signed URL (expires 24h)
     5. Create Transcription aggregate
     6. Publish event: ConversationCompleted
     7. Response: completion_timestamp + transcript_url
   - Immutability: Conversation now read-only

5. **Flow 5: Handle Claude API Failure** (400 words)
   - Trigger: Circuit breaker open (3 consecutive timeouts)
   - Steps:
     1. Stop calling Claude API
     2. Return canned responses from Redis cache
     3. Log degraded mode activation
     4. Publish event: DegradedMode
     5. Periodic health check (every 30s)
     6. When healthy: reset circuit breaker
   - User experience: "Service busy, please try again" (graceful)

---

### Actividad 2: NFR Requirements (2-3 horas)

#### 6 NFRs:

1. **Performance**:
   - First response: <3s (p95)
   - Streaming: <100ms per token
   - Message processing: <500ms
   - Measurement: CloudWatch metrics, APM

2. **Reliability**:
   - Uptime: 99.5% (Claude API down handled gracefully)
   - Message delivery: at-least-once (idempotent)
   - Jailbreak false positive: <5%
   - Measurement: Circuit breaker metrics, audit logs

3. **Security**:
   - Prompt injection: 0 successful attacks
   - XSS prevention: all user input escaped
   - Token exposure: 0 (never log tokens)
   - Measurement: Security audit, automated scanning

4. **Scalability**:
   - Concurrent conversations: 100+
   - Token buffer: <500MB per conversation
   - Graceful degradation under load
   - Measurement: Load testing

5. **Compliance (LGPD)**:
   - PII masked in logs: 100%
   - Transcriptions encrypted: at-rest + in-transit
   - Retention: 7 years (audit), 30 days (transcription)
   - Measurement: Automated PII scanner

6. **Observability**:
   - Token usage tracked: per message + per session
   - Latency buckets: <1s, <2s, <3s, >3s
   - Jailbreak attempts: all logged
   - Streaming errors: tracked per event

---

### Actividad 3: NFR Design (ADRs) (2 horas)

#### 4 ADRs:

**ADR-UNIT3-001: Claude API Integration Approach**
- Context: Need conversational AI, multiple LLM options
- Options: OpenAI (GPT-4), Anthropic (Claude), open-source (Llama)
- Decision: Claude API via Anthropic SDK (streaming support, safety features)
- Consequences:
  - ⚠️ API costs (~$0.01 per 1K tokens)
  - ✅ Streaming for real-time UX
  - ✅ Extended thinking for complex reasoning

**ADR-UNIT3-002: Jailbreak Detection Strategy**
- Context: Security risk from prompt injection
- Options: Regex patterns only, ML model, human review, combination
- Decision: Regex patterns (fast) + heuristics (content length, token count anomalies) + manual escalation
- Consequences:
  - ⚠️ False positives possible
  - ✅ Deterministic (no ML model drift)
  - ✅ Fast (<10ms overhead)

**ADR-UNIT3-003: Context Management (Sliding Window vs Summarization)**
- Context: Token budget constraint (keep conversations under 2000 tokens)
- Options: Discard old messages, summarize with LLM, compress with vectors
- Decision: Summarization (keep semantic meaning) + sliding window (discard oldest)
- Consequences:
  - ⚠️ Extra API call for summarization
  - ✅ Better conversation continuity
  - ✅ Auditability preserved

**ADR-UNIT3-004: Streaming Architecture**
- Context: User expects real-time token arrival (like ChatGPT)
- Options: Polling (CORS issues), WebSocket (complex), Server-Sent Events (simpler)
- Decision: Server-Sent Events (SSE) for streaming, WebSocket fallback
- Consequences:
  - ✅ Native browser support (EventSource)
  - ⚠️ Requires heartbeat (keep-alive)
  - ✅ Simpler than WebSocket

---

### Actividad 4: Infrastructure Design (2 horas)

#### Componentes:

**BotEngine Service Architecture**:
```
POST /api/sessions/{id}/conversations
    ↓
FastAPI Router (auth + validation)
    ↓
BotEngineService (business logic)
    ├─ JailbreakDetector (regex + heuristics)
    ├─ OutOfScopeDetector (Claude instruction-based)
    ├─ ContextManager (token budgeting)
    └─ ClaudeAPIClient (streaming)
    ↓
Database Repository (Message, Conversation)
    ↓
Redis (session state, cache)
    ↓
S3 (transcription storage)
    ↓
Event Publisher (SessionEvents)
```

**External Dependencies**:
- Anthropic SDK (`pip install anthropic`)
- Redis (for session state + cache)
- S3 (for transcription files)
- CloudWatch (for metrics + logging)

---

### Actividad 5: Code Generation + Tests (4-6 horas)

#### Estructura:

```
backend/app/services/
├── bot_engine.py           (400+ lines) — Main orchestrator
├── claude_client.py        (250+ lines) — API integration + streaming
├── jailbreak_detector.py   (200+ lines) — Security scanning
└── context_manager.py      (150+ lines) — Token budgeting

backend/app/routers/
├── screening.py            (200+ lines) — POST /api/sessions/{id}/conversations

backend/app/models/
├── message.py              — SQLAlchemy Message model
└── conversation.py         — SQLAlchemy Conversation model

tests/unit/
├── test_jailbreak_detector.py      (100+ lines)
├── test_context_manager.py         (100+ lines)
└── test_claude_client.py           (100+ lines)

tests/integration/
├── test_conversation_flow.py       (200+ lines)
└── test_claude_api_integration.py  (150+ lines)
```

#### Key Implementation Details:

**BotEngineService.start_conversation()**:
```python
async def start_conversation(self, session_id: str) -> Message:
    # 1. Load session + campaign context
    # 2. Build system prompt (role, job, rubric)
    # 3. Call Claude API (streaming)
    # 4. Collect tokens, detect stop reason
    # 5. Store Message aggregate
    # 6. Publish ConversationStarted event
    # 7. Return assistant message
```

**BotEngineService.exchange_message()**:
```python
async def exchange_message(self, conversation_id: str, user_message: str) -> AsyncIterator[str]:
    # 1. Validate + sanitize user_message
    # 2. Detect language (translate if needed)
    # 3. Scan jailbreak patterns
    # 4. Add to conversation history
    # 5. Call Claude API with streaming (yield tokens)
    # 6. Detect out-of-scope (instruction in system prompt)
    # 7. Store Message aggregate
    # 8. Publish MessageExchanged event
```

**Graceful Degradation**:
```python
async def send_to_claude(self, messages: List[Message]) -> AsyncIterator[str]:
    try:
        async with timeout(10):  # 10s timeout
            async for token in claude_api.stream(...):
                yield token
    except asyncio.TimeoutError:
        # Circuit breaker open
        yield "I apologize, I'm experiencing delays. Please try again shortly."
        log_circuit_breaker_event()
```

#### Tests (15+ total):

**Unit Tests**:
1. JailbreakDetector.scan() → detects 20+ patterns
2. ContextManager.truncate() → keeps semantic meaning
3. ClaudeClient.stream() → token collection correct
4. OutOfScopeCounter → counts violations
5. MessageAggregateCreation → immutable after completion
6. LanguageDetection → detects Spanish, Portuguese, etc.
7. TokenBudgetCalculation → prevents budget overflow
8. CircuitBreakerLogic → switches to degraded mode
9. JailbreakLogging → audit trail created
10. ConversationStateTransitions → correct state machine

**Integration Tests**:
1. Full conversation flow (start → exchange → complete)
2. Claude API integration (mock + real)
3. Session state persistence (Redis)
4. Transcription upload (S3)
5. Event publishing (verify events emitted)

#### Acceptance Criteria:
- [x] pytest passes (15+ tests)
- [x] Coverage >80%
- [x] OpenAPI docs include streaming endpoint
- [x] Jailbreak detector tested against OWASP prompts
- [x] Response latency <3s p95
- [x] Graceful degradation working

---

## 📊 Team (1 Backend Engineer)

**Timeline**:
- **Week 3 (4d)**: Actividades 1-3 (domain + design)
- **Week 4 (3d)**: Actividad 4 (infrastructure)
- **Week 5 (3d)**: Actividad 5 (code + tests)

**Milestones**:
- End Week 3: Design approved
- End Week 4: Architecture signed off
- End Week 5: Code passing tests

---

## 🎯 Success Metrics

| Métrica | Target |
|---------|--------|
| pytest passing | 100% |
| Coverage | >80% |
| Jailbreak detection accuracy | >95% |
| Response latency (p95) | <3s |
| Token tracking | ±5% accuracy |
| Graceful degradation | Functional |

---

**Generado**: 2026-05-27  
**Unit**: 3 - BotEngine  
**Status**: ⏳ Ready to document (awaiting Unit 2 start)

