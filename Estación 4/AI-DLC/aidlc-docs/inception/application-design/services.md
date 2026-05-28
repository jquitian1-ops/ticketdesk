# Capa de Servicios y Orquestación — TicketDesk Enterprise

**Definición de servicios de orquestación y patrones de coordinación**  
**Fecha**: 2026-05-27  
**Patrón**: Event-Driven + Message Queue para loose coupling

---

## VISIÓN GENERAL

La capa de servicios orquesta interacciones entre componentes usando:
- **Event-Driven Architecture** (asincrónico, loose coupling)
- **Message Queues** (Celery + Redis) para tasks pesadas
- **API Calls** (sincrónico) para consultas rápidas
- **Database Events** (opcional) para auditoria

### Flujo Principal: Screening → Evaluación → HITL → Compliance

```
1. Candidato envía respuesta
   ↓
2. BotEngine procesa vía Claude API
   ↓
3. BotEngine emite evento "ResponseProcessed"
   ↓
4. EvaluationEngine subscribe a evento, evalúa respuesta
   ↓
5. EvaluationEngine emite "EvaluationComplete"
   ↓
6. HITLService subscribe, agrega a cola si necesario
   ↓
7. ComplianceService subscribe, registra auditoría
   ↓
8. Reclutador ve nueva entrada en cola (via polling/SSE)
```

---

## SERVICIOS DE ORQUESTACIÓN

### 1. ScreeningOrchestrationService

**Responsabilidad**: Coordina flujo screening candidato

**Patrón**: Request-Reply (sincrónico desde cliente, pero internamente event-driven)

```python
class ScreeningOrchestrationService:
    """
    Orquesta sesión screening completa.
    
    Flujo:
    1. Cliente (frontend) llama start_screening()
    2. Service crea sesión en SessionManager
    3. Service invoca BotEngine.start_session()
    4. Service retorna primera pregunta al cliente
    
    5. Cliente envía respuesta via process_response()
    6. Service invoca BotEngine.process_response()
    7. Service emite evento "CandidateResponseSubmitted"
    8. Otros servicios reaccionan asincronicamente
    9. Service retorna siguiente pregunta
    """
    
    async def start_screening(
        campaign_id: str,
        candidate_id: str
    ) -> ScreeningStartResponse:
        """
        Inicia screening candidato.
        
        Steps:
        1. Validate campaign + candidate
        2. Create session (SessionManager)
        3. Register consent (ComplianceService)
        4. Call BotEngine.start_session()
        5. Return first question + session_id
        """
    
    async def process_response(
        session_id: str,
        response_text: str
    ) -> ProcessResponseResponse:
        """
        Procesa respuesta candidato, retorna siguiente pregunta.
        
        Steps:
        1. Validate session activa
        2. Call BotEngine.process_response()
        3. If jailbreak detected: log + escalate
        4. If out-of-scope detected: log + create ticket
        5. If screening completed:
           a. Call EvaluationEngine.evaluate_all()
           b. Emit "ScreeningCompleted" event
           c. Return final feedback
        6. Else: return next question
        """
    
    async def complete_screening(
        session_id: str
    ) -> ScreeningCompletionResult:
        """
        Finaliza screening, dispara evaluación.
        
        Steps:
        1. Save transcription (BotEngine)
        2. Evaluate all responses (EvaluationEngine)
        3. Calculate final score
        4. Emit "ScreeningCompleted" + score
        """
```

**Event Topics**:
- `screening.started` → consumed by: ComplianceService
- `candidate.response.submitted` → consumed by: EvaluationEngine
- `screening.completed` → consumed by: HITLService, ComplianceService, EmailService

---

### 2. EvaluationOrchestrationService

**Responsabilidad**: Coordina flujo evaluación

**Patrón**: Event-Driven (subscribe a "candidate.response.submitted")

```python
class EvaluationOrchestrationService:
    """
    Consume eventos de respuesta candidato, evalúa, emite resultado.
    
    Architecture:
    - Listens for: candidate.response.submitted
    - For each response:
      1. Call EvaluationEngine.evaluate_response()
      2. Extract citations
      3. Validate fairness
      4. Emit "EvaluationComplete"
    - On screening complete:
      1. Calculate final score
      2. Generate recommendation
      3. Emit "ScreeningEvaluationComplete"
    """
    
    async def on_candidate_response(
        event: CandidateResponseSubmittedEvent
    ) -> None:
        """
        Event handler para respuesta candidato.
        
        Steps:
        1. Extract session_id, question_id, response_text
        2. Load rubric from cache/DB
        3. Call EvaluationEngine.evaluate_response()
        4. Call EvaluationEngine.extract_citation()
        5. Call EvaluationEngine.validate_fairness()
        6. Save EvaluationResult to DB
        7. Emit "EvaluationComplete" event
        """
    
    async def on_screening_complete(
        event: ScreeningCompletedEvent
    ) -> None:
        """
        Event handler para screening completado.
        
        Steps:
        1. Fetch all evaluations para session
        2. Call EvaluationEngine.calculate_final_score()
        3. Call EvaluationEngine.generate_recommendation()
        4. Save final result to DB
        5. Emit "ScreeningEvaluationComplete" event
        """
    
    async def evaluate_all_responses(
        session_id: str
    ) -> EvaluationSummary:
        """
        Evalúa todas respuestas sesión.
        
        Used by: ScreeningOrchestrationService
        """
```

**Event Topics**:
- `candidate.response.submitted` (consumed by this service)
- `screening.completed` (consumed by this service)
- `evaluation.complete` → emitted to: HITLService, ComplianceService
- `screening.evaluation.complete` → emitted to: HITLService, EmailService

---

### 3. HITLOrchestrationService

**Responsabilidad**: Coordina flujo HITL (cola, decisión, notificación)

**Patrón**: Event-Driven + Real-time updates

```python
class HITLOrchestrationService:
    """
    Consume eventos evaluación, gestiona cola HITL, procesa decisiones.
    
    Architecture:
    - Listens for: evaluation.complete, screening.evaluation.complete
    - Adds to queue if score 50-80
    - Notifies recruiter queue update (SSE/WebSocket)
    - Process recruiter decisions, triggers notifications
    """
    
    async def on_evaluation_complete(
        event: EvaluationCompleteEvent
    ) -> None:
        """
        Event handler evaluación completa.
        
        Steps:
        1. Check if score 50-80 (HITL required)
        2. If yes: Call HITLService.add_to_queue()
        3. Emit "QueueItemAdded" event
        4. Notify recruiters (SSE/WebSocket update)
        """
    
    async def on_recruiter_decision(
        event: RecruiterDecisionEvent
    ) -> None:
        """
        Event handler decisión reclutador.
        
        Steps:
        1. Validate decision + reviewer_id
        2. Call HITLService.process_decision()
        3. Save to DB with audit
        4. Emit "DecisionRecorded" event
        5. Notify other systems
        """
    
    async def get_live_queue(
        campaign_id: str,
        recruiter_id: str
    ) -> LiveQueueResponse:
        """
        Retorna cola en tiempo real (para SSE/WebSocket).
        
        Used by: Frontend (polling/subscribe)
        """
```

**Event Topics**:
- `evaluation.complete` (consumed)
- `screening.evaluation.complete` (consumed)
- `queue.item.added` (emitted) → notifies frontend
- `recruiter.decision.made` (emitted)

---

### 4. ComplianceOrchestrationService

**Responsabilidad**: Coordina auditoría, LGPD, compliance

**Patrón**: Event-Driven (subscribe a múltiples eventos)

```python
class ComplianceOrchestrationService:
    """
    Consume eventos de todo sistema, registra auditoría inmutable.
    
    Architecture:
    - Listens for: screening.started, candidate.response.submitted,
                    evaluation.complete, recruiter.decision.made
    - Logs everything to append-only audit table
    - Handles LGPD: consentimiento, derecho olvido, retención
    """
    
    async def on_screening_started(
        event: ScreeningStartedEvent
    ) -> None:
        """
        Steps:
        1. Verify consent LGPD registered
        2. Log screening start
        """
    
    async def on_evaluation_complete(
        event: EvaluationCompleteEvent
    ) -> None:
        """
        Steps:
        1. Log evaluation with all details
        2. Verify citations present
        3. Check for bias flags
        """
    
    async def on_recruiter_decision(
        event: RecruiterDecisionEvent
    ) -> None:
        """
        Steps:
        1. Log decision + reviewer
        2. Create immutable record
        3. Schedule notification
        """
    
    async def cleanup_old_data(
        days_retention: int = 90
    ) -> None:
        """
        Background job: ejecuta hard-delete para datos >90 días.
        
        Scheduled: daily at 2 AM
        """
```

**Event Topics**: Subscribe a todos eventos principales

---

### 5. ReEngagementOrchestrationService

**Responsabilidad**: Maneja abandonment detection y re-engagement

**Patrón**: Scheduled + Event-Driven

```python
class ReEngagementOrchestrationService:
    """
    Detecta sesiones abandonadas, envía re-engagement emails.
    
    Architecture:
    - Background job cada 1 minuto: detectar inactividad
    - Emit eventos 24h/48h después inicio abandonment
    - Send emails, allow session resume
    """
    
    async def detect_abandoned_sessions(
    ) -> List[AbandonedSession]:
        """
        Background job (ejecuta cada 1 min).
        
        Steps:
        1. Query Redis: sesiones activas
        2. For each sesión: check last activity timestamp
        3. If >5 min inactivo: mark as inactivo, emit evento
        """
    
    async def on_session_abandoned(
        event: SessionAbandonedEvent
    ) -> None:
        """
        Event handler sesión abandonada.
        
        Steps:
        1. Schedule email #1 para 24h después
        2. Schedule email #2 para 48h después
        3. Log abandonment
        """
    
    async def send_reengagement_24h(
        session_id: str
    ) -> None:
        """
        Background job (ejecuta 24h después abandonment).
        
        Steps:
        1. Check if sesión still abandoned
        2. Load candidate + campaign details
        3. Send email con enlace resume
        4. Update tracking
        """
    
    async def on_session_resumed(
        event: SessionResumedEvent
    ) -> None:
        """
        Event handler: sesión reanudada.
        
        Steps:
        1. Restore exact context
        2. Log resumption
        3. Cancel pending re-engagement emails
        """
```

**Background Jobs**:
- `detect_abandoned_sessions` → every 1 minute
- `send_reengagement_24h` → scheduled per session
- `send_reengagement_48h` → scheduled per session

---

## PATRONES DE COMUNICACIÓN

### Pattern 1: Event-Driven (Async)

**Usado para**: Loose coupling entre servicios

```
Service A emits event → Message Queue (Redis Pub/Sub)
                      ↓
                Service B (subscriber) processes
```

**Ventajas**: Scalable, non-blocking, easy to add new subscribers

**Ejemplos**:
- Evaluation emits "EvaluationComplete" → HITL + Compliance subscribe
- Recruiter decision emits "DecisionRecorded" → Compliance + Email subscribe

**Implementation**: Celery (task queue) + Redis (message broker)

```python
from celery import shared_task

@shared_task
def on_evaluation_complete(evaluation_id: str):
    """Celery task: ejecuta cuando evaluation completa"""
    # HITLService reacciona
    # ComplianceService reacciona
```

---

### Pattern 2: Request-Reply (Sync)

**Usado para**: Respuestas inmediatas necesarias

```
Client calls Service API → Service ejecuta → retorna respuesta → Client
```

**Ejemplos**:
- Frontend calls `process_response()` → bloquea hasta siguiente pregunta
- Recruiter fetches queue → debe ser rápido (<3s)

**Implementation**: FastAPI endpoints

```python
@router.post("/screening/response")
async def process_response_endpoint(
    session_id: str,
    response_text: str
) -> ProcessResponseResponse:
    """Sincrónico: retorna siguiente pregunta inmediatamente"""
    return await orchestration_service.process_response(...)
```

---

### Pattern 3: Database Polling

**Usado para**: Real-time updates cuando WebSocket no disponible

```
Frontend polls every 5s → get_live_queue() → retorna cola actualizada
```

**Fallback**: Si WebSocket no soportado o cliente overhead bajo

---

## FLUJOS DE DATOS CRÍTICOS

### Flujo 1: Screening Completo

```
Frontend: Candidato envía respuesta
    ↓
API: POST /screening/{session_id}/response
    ↓
ScreeningOrchestrationService.process_response()
    ├─ BotEngine.process_response() → siguiente pregunta
    ├─ If completed:
    │   ├─ EvaluationOrchestrationService.evaluate_all_responses()
    │   │   ├─ For each response: EvaluationEngine.evaluate_response()
    │   │   ├─ EvaluationEngine.calculate_final_score()
    │   │   ├─ Emit "ScreeningEvaluationComplete"
    │   │   └─ Event hits HITL + Compliance
    │   ├─ HITLOrchestrationService.on_evaluation_complete()
    │   │   └─ If score 50-80: add_to_queue()
    │   └─ ComplianceOrchestrationService.on_evaluation_complete()
    │       └─ Log evaluation immutable
    └─ Return to Frontend (siguiente pregunta o final feedback)
```

---

### Flujo 2: Recruiter Decision

```
Frontend: Reclutador click "Aprobar"
    ↓
API: POST /hitl/decision
    ↓
HITLOrchestrationService.on_recruiter_decision()
    ├─ HITLService.process_decision() → save to DB
    ├─ Emit "DecisionRecorded" event
    ├─ ComplianceOrchestrationService.on_recruiter_decision()
    │   └─ Log decision immutable
    └─ EmailService.on_recruiter_decision()
        └─ Send notification to candidate
```

---

### Flujo 3: Session Abandonment + Re-engagement

```
Background Job (every 1 min):
    ├─ ReEngagementOrchestrationService.detect_abandoned_sessions()
    └─ If session >5 min inactivo:
        ├─ Emit "SessionAbandoned" event
        └─ Schedule re-engagement emails 24h/48h

24h después:
    └─ ReEngagementOrchestrationService.send_reengagement_24h()
        └─ Send email #1 + resume link

If Candidato click resume link:
    ├─ Emit "SessionResumed" event
    └─ ReEngagementOrchestrationService.on_session_resumed()
        ├─ CandidateSessionManager.resume_session()
        │   └─ Restore exact context
        └─ Cancel pending re-engagement emails
```

---

## MANEJO DE ERRORES Y FALLBACK

### Error: Claude API Timeout

```
BotEngine.process_response() → timeout
    ↓
Emit "BotEngineError" event
    ↓
Frontend: Show "Service momentarily unavailable, please retry"
    ↓
Retry logic: exponential backoff (1s, 2s, 4s, max 3 intentos)
```

### Error: Database Down

```
ComplianceService.log_evaluation() → DB connection error
    ↓
Fallback: Buffer event in Redis (temporary queue)
    ↓
Retry job: attempt to flush queue every 30s
    ↓
Alert: Page on-call if DB down >5 min
```

---

## MONITOREO DE ORQUESTACIÓN

**Métricas clave**:
- Event publishing latency (target <100ms)
- Event processing latency (target <500ms)
- Queue depth (HITL queue size)
- Error rate por servicio
- Message loss (if any)

---

**Estado**: ✅ Servicios definidos  
**Próxima**: component-dependency.md (matriz dependencias)
