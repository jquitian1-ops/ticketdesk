# Diseño de Requisitos No-Funcionales — TicketDesk Enterprise v1.0

**Patrones para Seguridad, Performance, Escalabilidad, Confiabilidad**  
**Fecha**: 2026-05-27  
**Fase**: Inception - NFR Design  
**Estado**: En Desarrollo

---

## 1. SEGURIDAD

### 1.1 Autenticación y Autorización

#### JWT Token Security
```yaml
Token Configuration:
  Algorithm: HS256 (HMAC SHA-256)
  Secret Key: 
    ├─ Stored in: AWS Secrets Manager (NOT in code)
    ├─ Rotation: Quarterly (Q1, Q2, Q3, Q4)
    └─ Backup keys: Keep 3 previous keys for rotation grace period

  Token Structure:
    ├─ Header: {alg: "HS256", typ: "JWT"}
    ├─ Payload: {sub: user_id, email, role, iat, exp, aud: "ticketdesk"}
    └─ Signature: HMAC(Header.Payload, secret)

  Expiration:
    ├─ Access Token: 1 hora
    ├─ Refresh Token: 7 días
    └─ Session: 24 horas inactividad → re-login

Token Storage (Frontend):
  ├─ Access Token: Memory (vulnerable to XSS but NOT persisted if page reload)
  ├─ Refresh Token: httpOnly cookie (secure against XSS, NOT accessible to JS)
  └─ Token Refresh: Auto-refresh 5 min before expiration (background)

Validation:
  ├─ Verify signature (secret key)
  ├─ Check expiration (exp > now)
  ├─ Check audience (aud == "ticketdesk")
  └─ IF any invalid → 401 Unauthorized, clear cookies
```

#### Password Security
```yaml
Hashing:
  Algorithm: bcrypt (cost=12)
  Process:
    ├─ 1. Generate salt: bcrypt.gensalt(rounds=12)
    ├─ 2. Hash password: bcrypt.hashpw(password.encode(), salt)
    ├─ 3. Store hash in DB (NEVER store plaintext)
    └─ On login: bcrypt.checkpw(provided_password, stored_hash)

  Cost=12:
    ├─ ~100ms per hash on modern hardware
    ├─ Acceptable for login flow (no timeout)
    └─ Resistant to GPU brute force

Password Requirements (Optional enforced in login form):
  ├─ Min 8 characters (enforzar en frontend validation)
  ├─ Suggested: 1 uppercase + 1 number + 1 special char
  └─ NOTE: Enforce server-side if multi-tenant later
```

#### Role-Based Access Control (RBAC)
```yaml
Roles Definidos:
  ├─ CANDIDATE: Puede iniciar screening, responder, pausar
  ├─ RECRUITER: Puede ver queue, tomar decisiones, analytics
  ├─ ADMIN: Puede crear campaigns, manage users, ver todos reports
  └─ SYSTEM: Reserved para automated tasks (re-engagement emails, etc.)

Permission Matrix:
  ├─ CANDIDATE:
  │  ├─ POST /api/screening/start ✓
  │  ├─ POST /api/screening/{session_id}/response ✓
  │  ├─ GET /api/recruiter/queue ✗
  │  └─ DELETE /api/campaign ✗
  │
  ├─ RECRUITER:
  │  ├─ POST /api/screening/start ✗
  │  ├─ GET /api/recruiter/queue ✓
  │  ├─ POST /api/recruiter/decision ✓
  │  └─ DELETE /api/campaign ✗
  │
  └─ ADMIN:
     ├─ ALL endpoints ✓
     ├─ POST /api/campaign ✓
     └─ DELETE /api/campaign ✓

Enforcement:
  ├─ FastAPI guard decorator: @require_role('RECRUITER')
  ├─ Middleware: Extract user role from JWT token
  ├─ On unauthorized: Return 403 Forbidden
  └─ Log: Every authorization failure (audit trail)
```

### 1.2 Encriptación de Datos

#### Datos en Tránsito (TLS/HTTPS)
```yaml
Protocol: TLS 1.3 (mínimo 1.2)
Ciphers:
  ├─ TLS_AES_256_GCM_SHA384
  ├─ TLS_CHACHA20_POLY1305_SHA256
  └─ Exclude weak ciphers (< 128 bits)

Certificates:
  ├─ Issuer: AWS ACM (Let's Encrypt o DigiCert)
  ├─ Domain: *.ticketdesk.com (wildcard)
  ├─ Renewal: Automatic before expiration (90 days AWS default)
  └─ HSTS: Enabled (max-age=31536000, includeSubDomains)

Endpoints:
  ├─ API: api.ticketdesk.com (HTTPS only)
  ├─ App: app.ticketdesk.com (HTTPS only)
  └─ Admin: admin.ticketdesk.com (HTTPS only)

HTTP Redirect:
  ├─ ALL HTTP (port 80) traffic → HTTPS (port 443)
  ├─ Code: 301 Permanent Redirect
  └─ Enforce in ALB listener
```

#### Datos en Reposo (Storage Encryption)
```yaml
PostgreSQL RDS:
  ├─ Encryption: AWS KMS (customer-managed key)
  ├─ Key Rotation: Annual (AWS automated)
  ├─ Backup Encryption: Inherited from DB
  └─ Snapshot Encryption: Enforced

Redis ElastiCache:
  ├─ Encryption at rest: Enabled (AWS managed keys)
  ├─ Encryption in transit: TLS (auth token required)
  └─ Authentication: Redis token (strong password, 32+ chars)

S3 Object Encryption:
  ├─ Default: SSE-S3 (AES-256)
  ├─ Alternative: SSE-KMS (customer-managed key) para compliance extra
  ├─ Versioning: Enabled (protect against accidental deletion)
  └─ Lifecycle: Automatic transition to Glacier after 90d (transcriptions)
```

### 1.3 API Security

#### Rate Limiting
```yaml
Global Rate Limit:
  ├─ Per IP: 100 requests/minute
  ├─ Per authenticated user: 1000 requests/minute
  └─ Implementation: FastAPI + slowapi (Redis-backed)

Endpoint-specific:
  ├─ POST /api/screening/start: 5/min per IP (prevent abuse)
  ├─ POST /api/auth/login: 5/min per IP (prevent brute force)
  ├─ POST /api/recruiter/decision: 100/min per user (normal load)
  └─ GET /api/recruiter/queue: 1000/min per user (polling/WebSocket)

Response:
  ├─ Return: 429 Too Many Requests
  ├─ Headers:
  │  ├─ Retry-After: 60 (seconds until can retry)
  │  └─ X-RateLimit-Remaining: 3
  └─ Body: {error: "Rate limit exceeded. Retry after 60 seconds"}
```

#### Input Validation & Sanitization
```yaml
All POST/PUT requests:
  ├─ 1. Validate schema (Pydantic models)
  │  └─ {response_text: str (max 5000 chars), session_id: UUID}
  │
  ├─ 2. Sanitize input:
  │  ├─ Trim whitespace: response_text.strip()
  │  ├─ Remove null bytes: response_text.replace('\x00', '')
  │  ├─ HTML escape if displaying: html.escape(response_text)
  │  └─ NO regex blacklist (positive allow-list instead)
  │
  ├─ 3. Validate business logic:
  │  ├─ session_id must exist in DB
  │  ├─ session.status must == "SCREENING"
  │  └─ candidate must have consent
  │
  └─ 4. IF validation fails:
     ├─ Return 400 Bad Request
     ├─ Body: {error: "Invalid input", details: [...]}
     └─ Log: "Invalid input from IP X for endpoint Y"

SQL Injection Prevention:
  ├─ ALWAYS use parameterized queries (SQLAlchemy ORM)
  ├─ NEVER concatenate strings in SQL
  ├─ Example CORRECT:
  │  └─ session = db.query(Session).filter_by(id=session_id).first()
  │
  └─ Example WRONG (NEVER):
     └─ session = db.execute(f"SELECT * FROM sessions WHERE id={session_id}")

XSS Prevention:
  ├─ Frontend: React automatically escapes JSX variables
  ├─ API: Return JSON (not HTML templates)
  └─ Special case: If returning HTML (e.g., PDF), sanitize con BeautifulSoup
```

### 1.4 LGPD Compliance

#### Consentimiento
```yaml
Consent Collection:
  ├─ 1. Before screening starts:
  │  └─ Show disclosure checkbox (in Portuguese):
  │     "I consent to my data being processed for recruitment evaluation"
  │
  ├─ 2. Candidate must EXPLICITLY check before proceeding
  │  └─ No pre-checked boxes
  │
  ├─ 3. Save to DB:
  │  └─ consent_records table:
  │     ├─ {candidate_id, consent_type: "SCREENING", given: true, timestamp}
  │     └─ IMMUTABLE (can't change past consent)
  │
  └─ 4. Certificate:
     ├─ Generate PDF: "Consent Certificate {timestamp}"
     ├─ Provide download link to candidate
     └─ Save PDF a S3 for audit

Withdrawal:
  ├─ Candidate can request withdrawal anytime
  ├─ POST /api/candidate/withdraw-consent {session_id}
  ├─ Backend:
  │  ├─ Update consent_records: withdrawn=true, withdrawn_at=now()
  │  ├─ Soft-delete all personal data for this session
  │  └─ Log to audit_logs: "CONSENT_WITHDRAWN"
  │
  └─ Cannot undo withdrawal (legal requirement)
```

#### Right to Forgotten (Right to Erasure)
```yaml
Data Export (Right to Access):
  ├─ Candidate: POST /api/candidate/data-export {candidate_id}
  ├─ Backend:
  │  ├─ Collect all data:
  │  │  ├─ Personal info: candidates table row
  │  │  ├─ Consent records: all records for candidate
  │  │  ├─ Screening responses: all responses
  │  │  ├─ Evaluations: all evaluation scores/citas
  │  │  └─ Decisions: final decision (if made)
  │  │
  │  ├─ Compile ZIP file with JSON files
  │  ├─ Encrypt with AES-256 (password-protected ZIP)
  │  ├─ Store temporarily (1 hora) a S3
  │  └─ Email download link (auto-delete after 24h)
  │
  └─ Frontend shows: "Data export requested. Check email in 5 min."

Deletion (Right to be Forgotten):
  ├─ Candidate: POST /api/candidate/request-deletion {candidate_id}
  ├─ Backend:
  │  ├─ Mark for soft-delete:
  │  │  ├─ candidates.deleted = true
  │  │  ├─ sessions.deleted = true
  │  │  └─ Update all FKs to handle soft-delete
  │  │
  │  ├─ Log to audit_logs: "DELETION_REQUESTED" with timestamp
  │  ├─ Schedule hard-delete (90 days later):
  │  │  └─ Celery task: hard_delete_candidate(candidate_id, scheduled_for: now + 90d)
  │  │
  │  └─ Email confirmation: "Your account will be permanently deleted in 90 days"
  │
  └─ Exceptions (NOT deleted):
     ├─ audit_logs (immutable for legal compliance)
     ├─ consent_records (proof of data processing)
     └─ decisions (recruiter decision record)

Retention Policy:
  ├─ Personal data (candidates, responses): 90 days after last activity
  ├─ Evaluations: 2 años (compliance retention)
  ├─ Audit logs: 7 años (legal requirement)
  └─ Backups: 30 días (then deleted from RDS)
```

---

## 2. PERFORMANCE

### 2.1 Latencia de Endpoint

#### SLAs (Service Level Agreements)
```yaml
Target Latencies (p99 = 99th percentile):

REST Endpoints:
  ├─ POST /api/screening/start: <500ms (inicio screening, primo consulta BD)
  ├─ POST /api/screening/{session_id}/response: <2000ms (Claude API + guardrails)
  ├─ GET /api/recruiter/queue: <300ms (solo lectura, cached)
  ├─ POST /api/recruiter/decision: <500ms (decisión registro)
  └─ GET /api/compliance/report: <5000ms (PDF generation)

WebSocket (Polling alternative):
  ├─ Queue update push: <2000ms (from evaluation complete to recruiter sees)
  └─ NOTE: MVP usa polling 5s, WebSocket v1.1

Health Check:
  └─ GET /health: <50ms (always fast)
```

#### Database Optimization
```yaml
Índices:
  ├─ PRIMARY KEY: id (auto-indexed)
  ├─ FOREIGN KEYS: auto-indexed (campaign_id, candidate_id, etc.)
  │
  ├─ Business queries:
  │  ├─ idx_sessions_candidate_id (retrieve candidate sessions)
  │  ├─ idx_sessions_status (find SCREENING/COMPLETED sessions)
  │  ├─ idx_screening_responses_session_id (retrieve responses)
  │  ├─ idx_evaluations_response_id (retrieve evaluations per response)
  │  ├─ idx_decisions_session_id (find decision for session)
  │  ├─ idx_audit_logs_timestamp (range queries for compliance reports)
  │  └─ idx_audit_logs_event_type (filter audit events)
  │
  └─ Query analysis:
     ├─ Use EXPLAIN ANALYZE for new queries
     ├─ Watch out for N+1 queries (use eager loading in ORM)
     └─ Profile with slow_query_log (log queries >1000ms)

Connection Pooling:
  ├─ FastAPI + SQLAlchemy:
  │  ├─ Pool size: 20 (max concurrent connections to RDS)
  │  ├─ Max overflow: 20 (wait up to 40 before error)
  │  └─ Pool recycle: 3600s (recycle stale connections)
  │
  └─ Redis:
     ├─ Pool size: 20
     └─ Connection timeout: 2s

Query Optimization:
  ├─ Select only needed columns (NOT SELECT *)
  ├─ Filter early (WHERE clause in query, NOT in application)
  ├─ Batch operations when possible (bulk insert, bulk update)
  └─ Pagination for large result sets (LIMIT 100 OFFSET 0)
```

#### Caching Strategy
```yaml
Redis Cache Layers:

L1 - Session Cache:
  ├─ Key: session:{session_id}
  ├─ Value: {candidate_id, current_question_index, responses, last_activity}
  ├─ TTL: 24 horas
  ├─ Hit rate target: >95% (casi todos screening activos cached)
  └─ Invalidation: On session complete or abandon

L2 - Rubric Cache:
  ├─ Key: rubric:{rubric_id}
  ├─ Value: {questions, criteria, weights}
  ├─ TTL: 7 días
  ├─ Hit rate target: >90% (rúbricas raramente cambian)
  └─ Invalidation: ON campaign update (manual cache bust)

L3 - Queue Cache:
  ├─ Key: queue:pending
  ├─ Value: ZSET of {queue_item_id, score: candidate_score, timestamp}
  ├─ TTL: No TTL (persistent, updated on each evaluation)
  ├─ Hit rate target: 99%+ (queue is real-time)
  └─ Invalidation: Auto-updated on decision, manual purge daily

Cache Invalidation:
  ├─ Time-based: TTL expiration (session: 24h, rubric: 7d)
  ├─ Event-based: ON campaign update, manual endpoint: DELETE /cache/{key}
  ├─ Passive: Stale-while-revalidate pattern (serve stale, fetch fresh async)
  └─ Monitoring: Track cache hit ratio in CloudWatch (target: >85%)
```

### 2.2 API Response Compression

```yaml
Compression (gzip):
  ├─ Enabled for responses >1KB
  ├─ Compression level: 6 (balance speed/ratio)
  ├─ Excluded: images, already compressed (video, zip)
  ├─ Header: Content-Encoding: gzip
  └─ Reduces JSON response by ~70-80%
```

### 2.3 Frontend Performance

```yaml
Next.js Optimization:
  ├─ Bundle size:
  │  ├─ Initial JS: <100KB (after gzip)
  │  ├─ CSS: <50KB
  │  └─ Monitoring: Vercel Analytics (auto-tracked)
  │
  ├─ Code splitting:
  │  ├─ Automatic per route (/recruiter vs /screening)
  │  ├─ Dynamic imports for heavy components
  │  └─ Lazy load images (lazy="true" attribute)
  │
  ├─ Image optimization:
  │  ├─ Use Next.js <Image /> component (auto-optimization)
  │  ├─ WebP format (auto-served if browser supports)
  │  └─ Responsive images (srcset generation)
  │
  └─ Rendering:
     ├─ SSR disabled (SPA for screening interactions)
     ├─ ISR (Incremental Static Regeneration) for campaigns
     └─ Prefetch on route hover (improve perceived speed)

Metrics (Web Vitals):
  ├─ Largest Contentful Paint (LCP): <2.5s
  ├─ First Input Delay (FID): <100ms
  ├─ Cumulative Layout Shift (CLS): <0.1
  └─ Monitoring via NextJS Analytics or Vercel
```

---

## 3. ESCALABILIDAD

### 3.1 Horizontal Scaling

#### Backend (FastAPI)
```yaml
ECS Auto Scaling:

Task Definition:
  ├─ FastAPI tasks: CPU 512, Memory 1024
  ├─ Desired count: 2 (start)
  ├─ Min count: 2
  └─ Max count: 10 (during peak load)

Auto Scaling Policy:
  ├─ Metric: CPU utilization
  ├─ Scale up: IF avg CPU > 70% for 2 min → add 1 task
  ├─ Scale down: IF avg CPU < 30% for 5 min → remove 1 task
  └─ Cooldown: 60s (avoid thrashing)

Alternative metric (future):
  ├─ Request count: IF >100 req/sec → scale up
  └─ Memory utilization: IF >80% → scale up

Load Balancer (ALB):
  ├─ Distributes traffic across healthy tasks
  ├─ Health check: GET /health (200 OK = healthy)
  ├─ Interval: 30s
  └─ Unhealthy task: Removed from rotation in 30s
```

#### Frontend (Next.js)
```yaml
ECS Auto Scaling:

Task Definition:
  ├─ Next.js tasks: CPU 256, Memory 512
  ├─ Desired count: 2
  ├─ Min count: 2
  └─ Max count: 8

Auto Scaling Policy:
  ├─ Scale up: IF CPU > 70% → add task
  ├─ Scale down: IF CPU < 30% → remove task
  └─ Most of the load is on client (React), server mainly serves HTML + API calls
```

#### Database Scaling
```yaml
PostgreSQL RDS (Single instance → Multi-read replicas v2.0):

MVP (Single instance):
  ├─ db.t3.small (2 vCPU, 2GB RAM)
  ├─ Multi-AZ enabled (automatic failover)
  ├─ Read replicas: Optional (1 replica for read-heavy queries)
  └─ Estimated capacity: ~1000 concurrent connections

Monitoring:
  ├─ CPU: Alert if >80%
  ├─ Storage: Auto-scale when >80% (configured in RDS)
  ├─ Connections: Alert if >1000
  └─ Replication lag (if replicas added): <1s

Future (v1.1):
  ├─ Read replicas in different AZ
  ├─ Query routing: Read queries → replicas, write → primary
  └─ Connection pooling: PgBouncer or AWS RDS Proxy
```

#### Redis Scaling
```yaml
ElastiCache Redis (Single node → Cluster v2.0):

MVP (Single node):
  ├─ cache.t3.micro (0.5GB)
  ├─ Single primary (no replicas)
  ├─ Max concurrent connections: ~500
  └─ Memory: 500MB

Monitoring:
  ├─ CPU: Alert if >80%
  ├─ Memory evictions: Alert if >1000 evictions/min
  ├─ Connections: Alert if >400
  └─ Latency: <1ms p99

Scaling Plan:
  ├─ If memory pressure > threshold:
  │  └─ Scale up: t3.small (1.55GB)
  │
  ├─ If throughput > threshold (v2.0):
  │  └─ Switch to cluster mode (16 shards, 3 replicas = 48 nodes)
  │
  └─ Data persistence:
     ├─ RDB snapshot: Every 5 min (for recovery)
     └─ AOF: Optional (performance cost vs durability tradeoff)
```

### 3.2 Colas de Trabajo (Job Queue)

```yaml
Celery + Redis:

Tasks:
  ├─ evaluate_response: Evaluate candidate response (async, <5s)
  ├─ send_reengagement_email: Send email (async, <2s)
  ├─ generate_compliance_report: Generate PDF (async, <30s)
  ├─ cleanup_old_data: Delete 90d+ old data (scheduled, nightly)
  └─ detect_abandoned_sessions: Check inactivity (scheduled, every 1 min)

Queue Configuration:
  ├─ Worker count: 4 (start), scale up if queue depth > 1000
  ├─ Task timeout: 300s (5 min, tasks should finish sooner)
  ├─ Retry: 3 attempts (exponential backoff: 2s, 4s, 8s)
  ├─ Dead letter: Failed tasks after 3 retries → manual review queue
  └─ Monitoring: Redis queue depth, task latency (CloudWatch)
```

---

## 4. CONFIABILIDAD Y DISASTER RECOVERY

### 4.1 Backup & Restore

```yaml
PostgreSQL RDS Backups:
  ├─ Automatic backups: Enabled, retention 30 días
  ├─ Frequency: Daily (incremental), takes snapshot for recovery
  ├─ Backup window: 2-3 AM UTC (low traffic)
  ├─ Recovery time objective (RTO): <15 min (restore from latest backup)
  ├─ Recovery point objective (RPO): <5 min (latest backup + WAL replay)
  └─ Manual snapshots: Before major releases

S3 Backups:
  ├─ Versioning: Enabled (protect against accidental deletion)
  ├─ Cross-region replication: (Optional v2.0, S3 → S3 another region)
  ├─ Lifecycle: Transition old versions to GLACIER after 90 días
  └─ Retention: Latest 30 versions + GLACIER archive

Redis Backups:
  ├─ RDB snapshots: Every 5 min (via Celery scheduled task)
  ├─ Location: S3 bucket (ticketdesk-redis-backups)
  ├─ Retention: 7 días (rolling)
  ├─ Recovery: <10 sec (load RDB, reconstruct memory)
  └─ Acceptable data loss: Last 5 min of sessions (acceptable, user can resume)
```

### 4.2 High Availability

```yaml
Multi-AZ Deployment:

RDS:
  ├─ Primary instance: us-south-1a
  ├─ Standby instance: us-south-1b (synchronous replication)
  ├─ Failover: <2 min (automatic if primary down)
  └─ DNS CNAME: Points to active instance

Redis:
  ├─ MVP: Single node (single AZ)
  ├─ Future (v1.1): Multi-AZ with automatic failover
  └─ Current acceptable: <5 min downtime, data loss <5 min

ALB (Load Balancer):
  ├─ Primary: us-south-1a
  ├─ Secondary: us-south-1b (cross-AZ)
  ├─ Failover: Automatic (if primary AZ down, routes to secondary)
  └─ Health checks: Every 30s

ECS Cluster:
  ├─ Distributed across 2 AZs (2 instances each)
  ├─ Tasks auto-placed on healthy instances
  ├─ If instance down: Tasks reschedule on other instances
  └─ Auto Scaling: Maintains desired count across AZs
```

### 4.3 Error Handling & Retries

```yaml
Claude API Timeout:
  ├─ Timeout: 15s
  ├─ Retry strategy:
  │  ├─ Attempt 1: Fail, wait 1s
  │  ├─ Attempt 2: Fail, wait 2s
  │  ├─ Attempt 3: Fail, wait 4s
  │  └─ All fail: Return 503 Service Unavailable to frontend
  │
  └─ Frontend: Show "Service temporarily unavailable. Retry in 30s?"

Database Connection Error:
  ├─ Connection pool exhausted:
  │  ├─ Wait for connection (timeout 5s)
  │  ├─ If timeout: Return 503, increment error counter
  │  └─ If error rate high: PagerDuty alert
  │
  └─ Connection lost:
     ├─ Retry immediately (connection pool will reconnect)
     └─ If >3 consecutive failures: Alert ops

Event Publishing Failure:
  ├─ Redis Pub/Sub down:
  │  ├─ Buffer event in in-memory queue (max 1000 events)
  │  ├─ Retry publish every 5s
  │  └─ If buffer full: Drop oldest event, alert ops
  │
  └─ After Redis recovery:
     ├─ Flush all buffered events to Redis
     └─ Celery subscribers catch up asynchronously

Email Sending Failure:
  ├─ AWS SES rate limit:
  │  ├─ Queue email, retry later (exponential backoff)
  │  └─ Keep trying for 24h, then give up + log
  │
  └─ Email validation failure:
     ├─ Skip this email, alert ops (manual review)
     └─ Continue with other emails
```

### 4.4 Circuit Breaker Pattern

```yaml
Claude API Circuit Breaker:
  ├─ State 1 (Closed):
  │  ├─ Normal operation, requests flow through
  │  ├─ Count failures
  │  └─ If failure_count > 5 in 1 min → State 2
  │
  ├─ State 2 (Open):
  │  ├─ Stop sending requests (fail fast)
  │  ├─ Return error immediately: "Service unavailable"
  │  └─ After 30s → State 3
  │
  └─ State 3 (Half-Open):
     ├─ Allow 1 test request
     ├─ If succeeds → reset to State 1 (Closed)
     └─ If fails → back to State 2 (Open)

Implementation (FastAPI):
  └─ Use pybreaker library or custom decorator
```

---

## 5. MONITOREO Y ALERTAS

### 5.1 Métricas Clave

```yaml
Application Metrics:
  ├─ Request latency (p50, p95, p99)
  ├─ Request error rate (5xx, 4xx)
  ├─ Claude API latency + error rate
  ├─ Event publishing latency
  ├─ Event processing latency (por servicio)
  ├─ Queue depth (pending evaluations, re-engagement emails)
  └─ Cache hit ratio (Redis)

Infrastructure Metrics:
  ├─ ECS CPU/Memory utilization
  ├─ RDS CPU/Memory/Connections/Storage
  ├─ Redis CPU/Memory/Evictions
  ├─ ALB request count + latency
  ├─ Network bandwidth (in/out)
  └─ Disk I/O (if applicable)

Business Metrics:
  ├─ Active screening sessions
  ├─ Screenings completed (daily/weekly)
  ├─ Average final score
  ├─ Decision distribution (Approve/Reject/HITL)
  ├─ Abandonment rate (%)
  └─ Re-engagement conversion (% resumed after email)
```

### 5.2 Alertas CloudWatch

```yaml
Critical Alerts (Page on-call):
  ├─ RDS CPU > 90% for 5 min
  ├─ RDS storage > 90% free
  ├─ RDS unavailable (failover or down)
  ├─ API error rate > 5% (5xx errors)
  ├─ Claude API error rate > 10%
  └─ Redis memory evictions > 1000/min

Warning Alerts (Slack notification):
  ├─ API latency p99 > 3s (for 2 consecutive min)
  ├─ Queue depth > 1000 (pending tasks)
  ├─ Cache hit ratio < 80%
  ├─ ECS tasks unhealthy (>0)
  ├─ Celery task timeout > 3 times (dead letter queue)
  └─ CloudWatch logs errors > 100/hour

Dashboard (Real-time):
  ├─ API latency (p50, p95, p99) → trending
  ├─ Error rate (5xx, 4xx) → trending
  ├─ Queue depth → trending
  ├─ ECS scaling activity
  ├─ RDS connection count → trending
  ├─ Cache hit ratio
  └─ Active screenings (real-time counter)
```

---

**Estado**: 🔄 NFR Design En Progreso  
**Siguiente**: Infrastructure Design (AWS specifics, Terraform, CI/CD)

