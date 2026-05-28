# Diseño Funcional Detallado — TicketDesk Enterprise v1.0

**Lógica de Negocio por Unit de Work**  
**Fecha**: 2026-05-27  
**Fase**: Inception - Functional Design  
**Estado**: En Desarrollo

---

## PROPÓSITO

Este documento detalla la **lógica de negocio específica** para cada Unit, incluyendo:
- Flujos de ejecución paso a paso
- Decisiones lógicas (if/then)
- Edge cases y cómo manejarlos
- Secuencias de eventos
- Validaciones y constraints

---

## UNIT 1: INFRAESTRUCTURA — Lógica Funcional

### 1.1 Inicialización AWS

**Flujo**: Setup VPC, RDS, Redis, S3, ECS

```
1. Create VPC (10.0.0.0/16)
   ├─ Public subnet A: 10.0.1.0/24 (us-south-1a)
   ├─ Public subnet B: 10.0.2.0/24 (us-south-1b)
   ├─ Private subnet A: 10.0.11.0/24 (us-south-1a) → RDS, Redis
   └─ Private subnet B: 10.0.12.0/24 (us-south-1b) → RDS, Redis

2. Create Security Groups
   ├─ ALB-SG: ingress 80,443 from 0.0.0.0/0
   ├─ FastAPI-SG: ingress 8000 from ALB-SG
   ├─ Next.js-SG: ingress 3000 from ALB-SG
   ├─ PostgreSQL-SG: ingress 5432 from FastAPI-SG + Next.js-SG
   └─ Redis-SG: ingress 6379 from FastAPI-SG

3. Create RDS PostgreSQL
   ├─ Multi-AZ enabled
   ├─ Automated backups: 30 días
   ├─ Create database: ticketdesk_prod
   ├─ Create users:
   │  ├─ app_user: SELECT, INSERT, UPDATE (app connections)
   │  ├─ readonly_user: SELECT only (analytics)
   │  └─ admin_user: ALL PRIVILEGES
   └─ Enable Enhanced Monitoring

4. Create ElastiCache Redis
   ├─ Engine: 7.0
   ├─ Node type: cache.t3.micro (MVP, upgrade t3.small v1.1)
   ├─ Parameter groups:
   │  ├─ maxmemory-policy: allkeys-lru (evict oldest)
   │  ├─ timeout: 300
   │  └─ tcp-keepalive: 300
   └─ Enable automatic failover (Multi-AZ in future)

5. Create S3 Buckets
   ├─ ticketdesk-transcriptions
   │  ├─ Versioning: ON
   │  ├─ Lifecycle: transition to GLACIER after 90 días
   │  └─ Block Public Access: ON
   ├─ ticketdesk-knowledge-base
   │  ├─ Versioning: ON
   │  └─ Block Public Access: ON
   └─ ticketdesk-compliance-reports
       ├─ Versioning: ON
       ├─ Lifecycle: DELETE after 2 años
       └─ Block Public Access: ON
```

**Edge Cases**:
- ¿BD creación falla? → Retry con exponential backoff (1s, 2s, 4s)
- ¿Redis no responde? → Verificar security group, subnet routing
- ¿S3 bucket ya existe? → Error descriptivo (bucket names globally unique)

---

### 1.2 CI/CD Pipeline Logic

**Trigger**: Push a rama (feature, staging, main)

```
GitHub Actions Workflow Execution:

1. ON: push branch = feature/* OR staging OR main

2. FOR Backend:
   ├─ Checkout code
   ├─ Setup Python 3.11
   ├─ Install dependencies (pip install -r requirements.txt)
   ├─ Linting (pylint src/ --fail-under=8.0)
   ├─ Type checking (mypy src/ --strict)
   ├─ Unit tests (pytest tests/ --cov=src --cov-fail-under=80)
   │
   ├─ IF any check fails → POST comment en PR con error details
   ├─ IF all checks pass:
   │  ├─ Build Docker image: aws ecr get-login-password | docker login
   │  ├─ Tag image: {ECR_URL}/ticketdesk-backend:${GITHUB_SHA:0:7}
   │  └─ Push to ECR
   └─ IF push = main AND build success:
       ├─ Get latest image SHA
       └─ Trigger ECS deployment (rolling update)

3. FOR Frontend:
   ├─ Checkout code
   ├─ Setup Node.js 18
   ├─ Install dependencies (npm ci)
   ├─ Linting (npm run lint --fail-under=8.0)
   ├─ Unit tests (npm test -- --coverage --testPathIgnorePatterns=integration)
   │
   ├─ IF any check fails → POST comment en PR
   ├─ IF all checks pass:
   │  ├─ Build app (next build, next export)
   │  ├─ Build Docker image
   │  ├─ Tag and push to ECR
   └─ IF push = main AND build success:
       └─ Trigger ECS deployment

4. Deployment to ECS (ONLY if main branch)
   ├─ Get current task definition
   ├─ Create new task definition version (with new image SHA)
   ├─ Update ECS service
   ├─ Monitor task rollout (wait for healthy tasks)
   │
   ├─ IF all new tasks healthy (5 min timeout):
   │  └─ Success! Deployment complete
   └─ IF timeout or unhealthy:
       ├─ Rollback (redeploy previous task definition)
       └─ Alert on-call engineer
```

**Edge Cases**:
- ¿Test coverage <80%? → Block merge, mostrar rojo en PR
- ¿Lint/type check fallan? → Requiere fix en branch, re-push
- ¿Docker build falla? → ECR push skipped, PR marked failed
- ¿Deployment falla? → Auto-rollback a versión anterior
- ¿On-call paging? → CloudWatch alarm → SNS → PagerDuty

---

## UNIT 2: FUNDAMENTOS BACKEND — Lógica Funcional

### 2.1 Database Schema Logic

**Creación de Tablas via Alembic Migration**:

```
migrations/versions/001_create_initial_tables.py:

def upgrade():
    # Campaigns table
    op.create_table('campaigns',
        sa.Column('id', sa.String(36), primary_key=True),  # UUID
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('rubric_id', sa.String(36), nullable=False),  # FK
        sa.Column('knowledge_base_ids', sa.JSON),  # Array de IDs
        sa.Column('status', sa.Enum('ACTIVE', 'DRAFT', 'CLOSED'), default='DRAFT'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, onupdate=sa.func.now()),
    )
    op.create_index('idx_campaigns_status', 'campaigns', ['status'])

    # Candidates table
    op.create_table('candidates',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('campaign_id', sa.String(36), nullable=False, sa.ForeignKey('campaigns.id')),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('idx_candidates_campaign_id', 'candidates', ['campaign_id'])

    # Sessions table
    op.create_table('sessions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('candidate_id', sa.String(36), nullable=False, sa.ForeignKey('candidates.id')),
        sa.Column('campaign_id', sa.String(36), nullable=False, sa.ForeignKey('campaigns.id')),
        sa.Column('status', sa.Enum('SCREENING', 'COMPLETED', 'ABANDONED'), default='SCREENING'),
        sa.Column('current_question_index', sa.Integer, default=0),
        sa.Column('transcription_s3_url', sa.String(500)),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime),
    )
    op.create_index('idx_sessions_status', 'sessions', ['status'])

    # Screening_responses table
    op.create_table('screening_responses',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('session_id', sa.String(36), nullable=False, sa.ForeignKey('sessions.id')),
        sa.Column('question_id', sa.String(36), nullable=False),
        sa.Column('response_text', sa.Text, nullable=False),
        sa.Column('timestamp', sa.DateTime, server_default=sa.func.now()),
    )

    # Evaluations table
    op.create_table('evaluations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('response_id', sa.String(36), nullable=False, sa.ForeignKey('screening_responses.id')),
        sa.Column('rubric_criterion_id', sa.String(36), nullable=False),
        sa.Column('score', sa.Integer),  # 0-100
        sa.Column('justification', sa.Text),
        sa.Column('citations', sa.JSON),  # Array de citations
        sa.Column('timestamp', sa.DateTime, server_default=sa.func.now()),
    )

    # Decisions table
    op.create_table('decisions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('session_id', sa.String(36), nullable=False, sa.ForeignKey('sessions.id')),
        sa.Column('decision', sa.Enum('APPROVE', 'REJECT', 'PENDING'), default='PENDING'),
        sa.Column('recruiter_id', sa.String(36), nullable=False),
        sa.Column('decision_timestamp', sa.DateTime, server_default=sa.func.now()),
        sa.Column('notes', sa.Text),
    )

    # Audit_logs table (APPEND-ONLY)
    op.create_table('audit_logs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('actor_id', sa.String(36)),
        sa.Column('subject_id', sa.String(36)),
        sa.Column('details', sa.JSON),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('user_agent', sa.String(500)),
        sa.Column('timestamp', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('idx_audit_logs_timestamp', 'audit_logs', ['timestamp'])
    op.create_index('idx_audit_logs_event_type', 'audit_logs', ['event_type'])
    # CONSTRAINT: NO UPDATE/DELETE (enforce at application layer)

    # Consent_records table
    op.create_table('consent_records',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('candidate_id', sa.String(36), nullable=False, sa.ForeignKey('candidates.id')),
        sa.Column('consent_type', sa.String(100), nullable=False),  # SCREENING, DATA_PROCESSING, etc.
        sa.Column('given', sa.Boolean, default=False),
        sa.Column('withdrawn', sa.Boolean, default=False),
        sa.Column('timestamp', sa.DateTime, server_default=sa.func.now()),
        sa.Column('withdrawn_at', sa.DateTime),
    )
    op.create_index('idx_consent_records_candidate_id', 'consent_records', ['candidate_id'])

    # Rubrics table
    op.create_table('rubrics',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('campaign_id', sa.String(36), nullable=False, sa.ForeignKey('campaigns.id')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('criteria', sa.JSON, nullable=False),  # [{id, name, weight, description}]
        sa.Column('version', sa.Integer, default=1),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, onupdate=sa.func.now()),
    )
    op.create_index('idx_rubrics_campaign_id', 'rubrics', ['campaign_id'])
```

**Validations**:
- NOT NULL constraints en campos obligatorios
- Unique constraints en emails
- Foreign key constraints para referential integrity
- Check constraints (ej: score >= 0 AND score <= 100)

---

### 2.2 Authentication & Authorization Logic

**JWT Token Flow**:

```
Login Request (Email + Password):
  ├─ 1. POST /api/auth/login con {email, password}
  ├─ 2. Validar email existe en BD (SELECT * FROM users WHERE email=?)
  │
  ├─ SI email NO existe:
  │  └─ Return 401 Unauthorized ("Invalid credentials")
  │
  ├─ SI email existe:
  │  ├─ Retrieve password hash desde BD
  │  ├─ Compare password con hash (bcrypt.verify)
  │  │
  │  ├─ SI password NO match:
  │  │  └─ Return 401 Unauthorized
  │  │
  │  └─ SI password match:
  │     ├─ Create JWT token
  │     │  ├─ Payload: {user_id, email, role, iat, exp}
  │     │  ├─ Secret key: env variable AWS_SECRETS_MANAGER
  │     │  └─ Exp: 24 horas
  │     │
  │     ├─ Create refresh token (7 días)
  │     ├─ Return {access_token, refresh_token, user: {id, email, name}}
  │     └─ Frontend stores access_token (memory/session storage, NOT localStorage)
  │
Request con Autenticación (Protected Endpoint):
  ├─ Frontend envía: Authorization: Bearer {access_token}
  ├─ Backend middleware valida:
  │  ├─ Parse token header
  │  ├─ Verify signature (JWT secret)
  │  ├─ Check expiration (iat + 24h > now)
  │  │
  │  ├─ SI válido:
  │  │  ├─ Extract user_id, role
  │  │  ├─ Inject a request context
  │  │  └─ Allow proceeding
  │  │
  │  └─ SI inválido:
  │     ├─ Return 401 Unauthorized
  │     └─ Frontend debe redirectar a login
  │
Role-Based Access (RBAC):
  ├─ Roles: RECRUITER, ADMIN, CANDIDATE
  ├─ Guards en endpoints:
  │  ├─ @require_role('RECRUITER') en /api/recruiter/*
  │  ├─ @require_role('ADMIN') en /api/admin/*
  │  └─ Ninguno en /api/screening/* (público hasta completar)
  │
  └─ SI role insuficiente → 403 Forbidden
```

**Edge Cases**:
- ¿Token expirado? → Frontend debe usar refresh token para obtener nuevo token
- ¿Refresh token expirado? → Require login nuevamente
- ¿Token tampered (signature inválida)? → Immediate 401, log security event

---

### 2.3 Event System Logic

**Event Publishing & Subscription**:

```
Event Publishing (cuando algo importante ocurre):

1. Service code emits event:
   await event_bus.emit("candidate.response.submitted", {
       session_id: "abc123",
       response_text: "...",
       question_id: "q5",
       timestamp: now()
   })

2. event_bus.emit() logic:
   ├─ Serialize payload a JSON
   ├─ Publish a Redis Pub/Sub: PUBLISH "candidate.response.submitted" {payload}
   ├─ Async return (non-blocking)
   └─ Log event publication (para auditoría)

Event Subscription (Celery task listening):

1. @event.listen("candidate.response.submitted")
   @shared_task(bind=True, max_retries=3)
   async def on_candidate_response_submitted(self, payload):
       try:
           session_id = payload['session_id']
           response_text = payload['response_text']
           
           # EvaluationEngine react to event
           eval_engine = EvaluationEngine()
           result = await eval_engine.evaluate_response(session_id, response_text)
           
           # Log success
           logger.info(f"Evaluation complete for session {session_id}")
           
       except Exception as e:
           logger.error(f"Error evaluating response: {e}")
           # Retry with exponential backoff
           raise self.retry(exc=e, countdown=2 ** self.request.retries)

2. Celery worker process:
   ├─ Subscribe a Redis Pub/Sub "candidate.response.submitted"
   ├─ ON message received:
   │  ├─ Deserialize payload
   │  ├─ Execute task function
   │  └─ Log result
   │
   ├─ Error handling:
   │  ├─ 1st attempt fails → wait 2s, retry
   │  ├─ 2nd attempt fails → wait 4s, retry
   │  └─ 3rd attempt fails → move to dead-letter queue, alert ops
   │
   └─ Success: task complete, continue

Event Topics Defined:
  ├─ screening.started → ComplianceService (log inicio screening)
  ├─ candidate.response.submitted → EvaluationEngine (evaluar respuesta)
  ├─ evaluation.complete → HITLService (agregar a cola si 50-80)
  ├─ evaluation.complete → ComplianceService (log evaluación)
  ├─ recruiter.decision.made → ComplianceService (log decisión)
  ├─ recruiter.decision.made → EmailService (notificar candidato)
  └─ session.abandoned → ReEngagementService (schedule emails 24h/48h)
```

**Guarantees**:
- At-least-once delivery (si task falla, reintenta)
- Idempotent tasks (safe ejecutar múltiples veces)
- Dead-letter queue para fallos persistentes

---

## UNIT 3: BOTENGINE — Lógica Funcional

### 3.1 Flujo Screening Completo

**Inicio de Screening**:

```
Candidato accede a candidato.ticketdesk.com/screening/{campaign_id}
  │
  ├─ Frontend: GET /api/campaigns/{campaign_id}
  │  └─ Retorna: {campaign_name, rubric questions count, privacy policy}
  │
  ├─ Frontend: Display consent form (checkbox LGPD)
  │
  Candidato marca checkbox "Acepto"
  │
  ├─ Frontend: POST /api/screening/start
  │  ├─ Payload: {campaign_id, candidate_id/email}
  │  │
  │  └─ Backend ScreeningOrchestrationService.start_screening():
  │     ├─ 1. Validate campaign exists
  │     ├─ 2. Create candidate si no existe
  │     ├─ 3. Create session en PostgreSQL (status=SCREENING)
  │     ├─ 4. ComplianceService.register_consent(candidate_id, "SCREENING")
  │     ├─ 5. BotEngine.start_session(campaign_id, session_id)
  │     │  ├─ Load rubric preguntas
  │     │  ├─ Start with first question
  │     │  └─ Save session state to Redis: session:{session_id}
  │     │
  │     └─ Return {session_id, first_question, question_number: 1, total: 10}
  │
  └─ Frontend receives session_id, displays first question + input field
```

**Processing Response**:

```
Candidato escribe respuesta en textarea, presiona "Siguiente"
  │
  ├─ Frontend: POST /api/screening/{session_id}/response
  │  ├─ Payload: {session_id, response_text}
  │  │
  │  └─ Backend ScreeningOrchestrationService.process_response():
  │     │
  │     ├─ 1. Validate session exists y status=SCREENING
  │     │
  │     ├─ 2. BotEngine.process_response(session_id, response_text)
  │     │    ├─ Load session context from Redis
  │     │    ├─ Load current question from rubric
  │     │    │
  │     │    ├─ 3a. detect_jailbreak(response_text)
  │     │    │     ├─ Regex patterns check
  │     │    │     ├─ IF jailbreak detected:
  │     │    │     │  ├─ Emit event("bot.jailbreak_detected", {session_id, response})
  │     │    │     │  ├─ Return {is_jailbreak: true, generic_response: "Please follow instructions"}
  │     │    │     │  └─ Continuar al siguiente paso (no escalate, solo log)
  │     │    │     │
  │     │    │     └─ ELSE: is_jailbreak = false
  │     │    │
  │     │    ├─ 3b. detect_out_of_scope(response_text)
  │     │    │     ├─ Check patterns (preguntar about salary, location, etc.)
  │     │    │     ├─ IF OOB detected:
  │     │    │     │  ├─ Emit event("bot.out_of_scope_detected", {session_id, question})
  │     │    │     │  ├─ Return {is_out_of_scope: true, generic_response: "That's out of scope"}
  │     │    │     │  └─ Continuar
  │     │    │     │
  │     │    │     └─ ELSE: is_out_of_scope = false
  │     │    │
  │     │    ├─ 4. Save response a PostgreSQL screening_responses table
  │     │    │    └─ {session_id, question_id, response_text, timestamp}
  │     │    │
  │     │    ├─ 5. Append response a transcripción Redis (session:{session_id}:transcript)
  │     │    │
  │     │    ├─ 6. Emit event("candidate.response.submitted", {session_id, response_text, question_id})
  │     │    │    └─ EvaluationEngine recibe event y evalúa asincronicamente
  │     │    │
  │     │    ├─ 7. Check if screening completado (current_question_index >= total_questions)
  │     │    │    ├─ SI NO completado:
  │     │    │    │  ├─ BotEngine.generate_next_question(session_context, all_responses)
  │     │    │    │  │  ├─ Use Claude API con contexto:
  │     │    │    │    │  │    Prompt: "Based on responses so far: [responses], generate next clarifying question about [criterion]"
  │     │    │    │  │  └─ Return: {next_question, question_id: "q6"}
  │     │    │    │  │
  │     │    │    │  └─ Update session state Redis
  │     │    │    │     └─ current_question_index += 1
  │     │    │    │
  │     │    │    └─ SI completado:
  │     │    │       ├─ Emit event("screening.completed", {session_id})
  │     │    │       ├─ Upload transcription completa a S3
  │     │    │       ├─ Update session PostgreSQL: status=COMPLETED, completed_at=now()
  │     │    │       └─ Return final feedback message
  │     │
  │     └─ Return {
  │          session_id,
  │          response_processed: true,
  │          next_question: "...",
  │          question_number: 3,
  │          total_questions: 10,
  │          is_jailbreak: false,
  │          is_out_of_scope: false
  │        }
  │
  └─ Frontend receives next_question, displays it
```

**Edge Cases**:
- ¿Candidato deja browser abierto por 10 minutos sin respuesta? → ReEngagementService detecta inactividad, schedule emails
- ¿Candidato intenta jailbreak (SQL injection, prompt injection)? → Log, show generic response, continúa screening
- ¿Claude API timeout? → Retry logic, mostrar "Service momentarily unavailable, retry?"
- ¿Candidato completa en pregunta 5 de 10? → Screening completado, retorna early (no mandatory 10)

---

## UNIT 4: EVALUATIONENGINE — Lógica Funcional

### 4.1 Evaluación de Respuesta Individual

**Trigger**: Evento "candidate.response.submitted" (cuando BotEngine termina procesar respuesta)

```
EvaluationEngine.evaluate_response(response_text, rubric, session_id):

1. Load rubric from PostgreSQL / Redis cache
   ├─ Rubric = [{criterion_id, criterion_name, description, weight}, ...]
   └─ Si en Redis hit: use cached, senão query PostgreSQL y cache

2. For each criterion in rubric:
   ├─ Call Claude API con prompt:
   │  ├─ System: "You are an expert evaluator. Assess the response against this criterion."
   │  ├─ Criterion: "{criterion_name}: {description}"
   │  ├─ Response: "{response_text}"
   │  ├─ Task: "Score 0-100 and provide justification."
   │  │
   │  └─ Claude returns: {score: 85, justification: "..."}
   │
   ├─ 3. Call extract_citation(response_text, criterion_name)
   │  ├─ Use fuzzy matching (difflib)
   │  ├─ Find verbatim text from response that supports score
   │  ├─ Return {citation_text, start_index, end_index, confidence: 0.98}
   │  │
   │  └─ SI no citation found (confidence < 0.80):
   │     └─ citation = {text: "(no specific citation found)", confidence: 0}
   │
   └─ 4. Save evaluation to PostgreSQL
      ├─ evaluations table:
      │  ├─ response_id (FK)
      │  ├─ rubric_criterion_id
      │  ├─ score
      │  ├─ justification
      │  ├─ citations (JSON array)
      │  └─ timestamp
      │
      └─ Continue to next criterion

3. After all criteria evaluated:
   ├─ Emit event("evaluation.complete", {
   │    session_id,
   │    evaluation_id,
   │    individual_scores: [{criterion: "Leadership", score: 85}, ...],
   │    timestamp
   │  })
   │
   └─ Continue (HITLService / ComplianceService react asynchronously)
```

---

### 4.2 Cálculo de Score Final

**Trigger**: Evento "screening.completed" (cuando candidato termina todas preguntas)

```
EvaluationEngine.calculate_final_score(session_id):

1. Fetch ALL evaluations para session_id
   ├─ SELECT evaluations WHERE session_id = ? ORDER BY timestamp
   └─ Result: [eval1, eval2, eval3, ...]

2. Calculate weighted average:
   ├─ IF rubric has weights:
   │  └─ final_score = SUM(eval.score * criterion.weight) / SUM(weights)
   │  └─ Example: (85*0.3 + 90*0.3 + 75*0.4) / 1.0 = 82.5
   │
   └─ ELSE equal weights:
      └─ final_score = AVG(eval.score) = (85+90+75) / 3 = 83.3

3. Determine recommendation:
   ├─ IF final_score >= 80:
   │  └─ recommendation = "AUTO_APPROVE"
   │
   ├─ ELSE IF final_score >= 50 AND final_score < 80:
   │  └─ recommendation = "REQUIRES_HITL"
   │
   └─ ELSE:
      └─ recommendation = "AUTO_REJECT"

4. Save final score to PostgreSQL
   ├─ decisions table:
   │  ├─ session_id
   │  ├─ final_score
   │  ├─ recommendation
   │  ├─ decision_timestamp
   │  └─ recruiter_id = null (hasta que reclutador decide)

5. IF recommendation = "REQUIRES_HITL":
   ├─ Emit event("evaluation.complete", {
   │    session_id,
   │    final_score,
   │    recommendation: "REQUIRES_HITL"
   │  })
   │
   └─ HITLService reacts (add_to_queue)

6. ELSE IF recommendation = "AUTO_APPROVE" or "AUTO_REJECT":
   ├─ Skip HITL queue
   ├─ Auto-complete decision (recruiter_id = "SYSTEM")
   ├─ Send notification email directamente
   └─ Mark session como completada
```

---

## UNIT 5: FRONTEND — Lógica Funcional

### 5.1 Chat Session Flow (Candidato Perspective)

```
User Journey:

1. Open: https://app.ticketdesk.com/screening/campaign-abc123

2. Frontend loads:
   ├─ GET /api/campaigns/abc123
   └─ Display campaign info + consent form

3. Candidato marks consent checkbox + clicks "Start Screening"
   ├─ POST /api/screening/start {campaign_id}
   ├─ Receive {session_id, first_question, question_number: 1, total: 10}
   └─ Zustand store.setSession({session_id, current_question})

4. UI renders:
   ├─ <ChatMessage question="What is your strongest skill?" isQuestion={true} />
   ├─ <ChatInput onSubmit={handleResponse} disabled={isLoading} />
   └─ <ProgressBar current={1} total={10} />

5. Candidato types answer in textarea + presses "Enviar"
   ├─ Frontend validates: response_text.length >= 10
   │  ├─ SI < 10 chars: show error "Respuesta muy corta"
   │  └─ ELSE: continue
   │
   ├─ Frontend disables input (isLoading = true)
   ├─ POST /api/screening/{session_id}/response {response_text}
   │
   ├─ Receive response:
   │  ├─ IF success:
   │  │  ├─ Add response to chat history
   │  │  ├─ Display next_question
   │  │  ├─ Update progress bar (current = 2)
   │  │  └─ Clear input textarea
   │  │
   │  └─ IF error (e.g., session expired):
   │     ├─ Show error toast: "Session expired"
   │     └─ Redirect to /screening/new

6. Repeat steps 5-6 until question_number == total_questions

7. Final question submitted:
   ├─ Receive {screening_completed: true, final_feedback: "Thank you..."}
   ├─ Show <ScreeningCompleted /> modal
   ├─ Mostrar "Your screening has been submitted. Check email for updates."
   └─ Redirect a /screening/thank-you after 5 segundos
```

**Inactivity Handling**:

```
While candidato in screening (session active):

1. Frontend starts inactivity timer (4 minutos)
   ├─ ON user keystroke: reset timer
   ├─ ON mouse move: reset timer
   └─ ON response submit: reset timer

2. IF timer reaches 4 minutos:
   ├─ Show modal: "Are you still there? Click to continue or we'll save your progress."
   ├─ Buttons: "Yes, I'm here" | "Save & exit"
   │
   ├─ SI "Yes, I'm here": reset timer, close modal
   └─ SI "Save & exit":
      ├─ POST /api/screening/{session_id}/pause
      ├─ Backend: update session status = "PAUSED"
      ├─ Redirect a /screening/paused
      └─ Email sent: "You can resume here: [link with session_id]"

3. Backend (ReEngagementService) also detects abandonment:
   ├─ Every 1 min: check Redis session last_activity
   ├─ IF >5 min inactivo: emit "session.abandoned"
   └─ Schedule re-engagement emails 24h/48h
```

---

### 5.2 Recruiter Dashboard Queue Logic

```
Recruiter User Journey:

1. Open: https://app.ticketdesk.com/recruiter/queue

2. Frontend loads:
   ├─ GET /api/recruiter/queue (for current user's campaigns)
   │  ├─ Query param: ?campaign_id=abc123
   │  └─ Receive: [{candidate: {...}, score: 75, last_evaluated: "2 min ago"}, ...]
   │
   ├─ Zustand store.setQueue(items)
   └─ UI renders <QueueList>

3. Frontend setup polling (or WebSocket in v1.1):
   ├─ useEffect(() => {
   │    const interval = setInterval(() => {
   │      fetch('/api/recruiter/queue').then(data => store.setQueue(data))
   │    }, 5000)
   │  }, [])
   │
   └─ Update UI every 5 seconds (if new evaluations arrived)

4. Recruiter clicks on candidate in queue:
   ├─ GET /api/recruiter/queue/{queue_item_id}
   │  └─ Receive: {
   │       candidate: {id, name, email},
   │       scores: [{criterion: "Leadership", score: 85}, ...],
   │       final_score: 75,
   │       recommendation: "REQUIRES_HITL",
   │       citations: [{criterion: "...", citation_text: "...", confidence: 0.98}],
   │       transcription: [{q: "...", a: "..."}, ...]
   │     }
   │
   └─ UI renders <CandidateDetailPanel />

5. Recruiter reviews transcription + scores + recommendation

6. Recruiter makes decision: click "Aprobar" or "Rechazar"
   ├─ Frontend: POST /api/recruiter/decision
   │  ├─ Payload: {queue_item_id, decision: "APPROVE", notes: "Strong leadership potential"}
   │  │
   │  └─ Backend:
   │     ├─ HITLService.process_decision(queue_item_id, decision, recruiter_id, notes)
   │     ├─ Update decisions table
   │     ├─ Remove from queue (delete queue_item)
   │     ├─ Emit event("recruiter.decision.made", {decision, candidate_id})
   │     ├─ EmailService react: send notification email
   │     └─ ComplianceService react: log decision immutable
   │
   ├─ Frontend receives success
   ├─ Show toast: "Decision recorded"
   ├─ Remove from queue UI
   └─ Move to next item in queue

7. IF no items in queue:
   ├─ Show message: "No candidates pending review"
   └─ Suggest: "Check back later or configure new campaigns"
```

---

## UNIT 6: COMPLIANCE + HITL + RE-ENGAGEMENT — Lógica Funcional

### 6.1 Flujo Auditoría Inmutable

```
Cada evento importante genera registro append-only:

Event: "screening.started"
  │
  └─ ComplianceService.on_screening_started(event):
     ├─ Verify candidate consent exists (consent_records table)
     ├─ Insert to audit_logs:
     │  ├─ event_type: "SCREENING_STARTED"
     │  ├─ subject_id: candidate_id
     │  ├─ details: {campaign_id, candidate_email, consent_given: true}
     │  ├─ timestamp: now()
     │  └─ ip_address: request.remote_addr
     │
     └─ LOG entry: "2026-05-27 10:23:45 | SCREENING_STARTED | candidate@email.com | campaign-abc"

Event: "evaluation.complete"
  │
  └─ ComplianceService.on_evaluation_complete(event):
     ├─ Fetch evaluation details from DB
     ├─ Check for bias flags (age, gender, origin mentions)
     ├─ Insert to audit_logs:
     │  ├─ event_type: "EVALUATION_COMPLETE"
     │  ├─ details: {session_id, final_score, citations, bias_flags}
     │  └─ timestamp
     │
     └─ IF bias detected: emit warning event

Event: "recruiter.decision.made"
  │
  └─ ComplianceService.on_recruiter_decision(event):
     ├─ Insert to audit_logs:
     │  ├─ event_type: "DECISION_RECORDED"
     │  ├─ subject_id: candidate_id
     │  ├─ actor_id: recruiter_id
     │  ├─ details: {decision: "APPROVE", notes: "...", decision_timestamp}
     │  └─ timestamp
     │
     └─ 100% immutable record (NO UPDATE/DELETE)

Compliance Report Generation:
  └─ ComplianceService.generate_report(campaign_id, date_range):
     ├─ Query audit_logs WHERE event_type IN (...) AND timestamp BETWEEN date_range
     ├─ Compile PDF:
     │  ├─ Total screenings
     │  ├─ Decisions breakdown (APPROVE: 45%, REJECT: 35%, PENDING: 20%)
     │  ├─ Average score
     │  ├─ Bias flags detected count
     │  └─ Retention policy compliance
     │
     ├─ Sign PDF digitally (optional para compliance extra)
     └─ Upload a S3: ticketdesk-compliance-reports/{campaign_id}/2026-05-27-report.pdf
```

---

### 6.2 Flujo Re-engagement (Abandonment Detection + Emails)

```
Background Job (Celery, ejecuta cada 1 minuto):

1. ReEngagementService.detect_abandoned_sessions():
   ├─ Query Redis KEYS "session:*"
   ├─ For each session_id:
   │  ├─ GET Redis: session:{session_id}
   │  ├─ Check: last_activity timestamp
   │  │
   │  ├─ IF now() - last_activity > 5 minutos:
   │  │  ├─ Fetch session from PostgreSQL
   │  │  ├─ IF session.status != "COMPLETED":
   │  │  │  ├─ Emit event("session.abandoned", {session_id, candidate_id, abandon_time: now()})
   │  │  │  └─ Log: "Session abc123 abandoned by candidate@email.com"
   │  │  │
   │  │  └─ ReEngagementService.on_session_abandoned(event):
   │  │     ├─ 1. Schedule Celery task: send_reengagement_24h (run_at = now + 24h)
   │  │     │  └─ Task stores: {session_id, candidate_id, scheduled_for: tomorrow 10:00am}
   │  │     │
   │  │     ├─ 2. Schedule Celery task: send_reengagement_48h (run_at = now + 48h)
   │  │     └─ 3. Mark in Redis: reengagement:scheduled:{session_id} → {tasks: [task1, task2]}
   │  │
   │  └─ ELSE: session still active, do nothing

24 horas después de abandonment:

1. Scheduled task executes: send_reengagement_24h(session_id):
   ├─ Fetch session + candidate from PostgreSQL
   ├─ Check: IF session.status == "COMPLETED":
   │  └─ SKIP (candidato ya completó, abort task)
   │
   ├─ ELSE:
   │  ├─ Load email template #1
   │  ├─ Render template con variables: {candidate_name, campaign_name, resume_url}
   │  │  ├─ Subject: "¿Completamos tu screening de {campaign_name}?"
   │  │  ├─ Body: "Notamos que dejaste tu aplicación sin completar hace 24 horas..."
   │  │  └─ CTA Button: "Resumir Screening" → https://app.ticketdesk.com/screening/resume/{session_id}
   │  │
   │  ├─ Send email via AWS SES
   │  │  ├─ TO: candidate_email
   │  │  ├─ FROM: noreply@ticketdesk.com
   │  │  └─ REPLY-TO: support@ticketdesk.com
   │  │
   │  └─ Log event: "REENGAGEMENT_EMAIL_SENT_24H" to audit_logs

48 horas después:

1. Scheduled task executes: send_reengagement_48h(session_id):
   ├─ Same logic as 24h
   ├─ Load template #2
   │  ├─ Subject: "Última oportunidad para completar tu screening"
   │  ├─ Body: "Esta es la última oportunidad... Tienes hasta el viernes para completar"
   │  └─ CTA Button: "Completar Ahora"
   │
   └─ Send email

Candidato recibe email y clica resume link:

1. Candidato: clicks "Resumir Screening"
   ├─ Navigates to: https://app.ticketdesk.com/screening/resume/session-abc123
   ├─ Frontend: GET /api/screening/{session_id}/status
   │  └─ Receive: {session_id, current_question_index: 5, total: 10}
   │
   ├─ Frontend: Restore exact context
   │  ├─ Display all previous responses (read-only)
   │  ├─ Display current question (question 6)
   │  ├─ Show progress bar (5 of 10)
   │  └─ Candidate can continue answering
   │
   └─ Emit event("session.resumed", {session_id, candidate_id, resume_time: now()})

Backend reacts to resumed event:

1. ReEngagementService.on_session_resumed(event):
   ├─ Cancel pending re-engagement tasks:
   │  ├─ GET Redis: reengagement:scheduled:{session_id}
   │  ├─ For each pending task_id:
   │  │  └─ celery.revoke(task_id)  # Cancel scheduled task
   │  │
   │  └─ DELETE Redis key
   │
   ├─ Update session: last_activity = now() (restart inactivity timer)
   └─ Log event: "SESSION_RESUMED" to audit_logs
```

---

## VALIDACIONES Y CONSTRAINTS GLOBALES

### Data Integrity

```
1. Foreign Key Constraints:
   ├─ candidates.campaign_id → campaigns.id (CASCADE DELETE)
   ├─ sessions.candidate_id → candidates.id
   ├─ sessions.campaign_id → campaigns.id
   ├─ screening_responses.session_id → sessions.id
   ├─ evaluations.response_id → screening_responses.id
   └─ decisions.session_id → sessions.id

2. Unique Constraints:
   ├─ candidates.email (UNIQUE)
   └─ campaigns.name per organization (UNIQUE)

3. Check Constraints:
   ├─ evaluations.score BETWEEN 0 AND 100
   ├─ decisions.final_score BETWEEN 0 AND 100
   └─ consent_records.given IN (true, false)

4. Immutability Constraints (app level):
   ├─ audit_logs: NO UPDATE, NO DELETE
   ├─ consent_records: NO DELETE (mark withdrawn instead)
   └─ screening_responses: NO UPDATE (append-only transcription)
```

---

**Estado**: 🔄 Functional Design En Progreso  
**Siguiente**: NFR Design (seguridad, performance, escalabilidad)

