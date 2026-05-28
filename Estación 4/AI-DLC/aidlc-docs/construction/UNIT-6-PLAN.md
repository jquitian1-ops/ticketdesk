# Unit 6: Compliance + HITL — Plan de Ejecución

**Proyecto**: TicketDesk Enterprise v1.0  
**Fase**: Construction  
**Unit**: 6 - Compliance + Human-in-the-Loop + Re-engagement  
**Duración Estimada**: Semanas 4-6 (2-3 semanas)  
**Team**: 2 Backend Engineers  
**Bloqueador**: Unit 1 ✅, Unit 2 ✅, Unit 3 (depends on events)  
**Bloquea**: None (final unit)  
**Status**: ⏳ Pending Units 2-3 completion

---

## 📋 Objetivo Unit 6

Construir **3 servicios críticos**:

1. ✅ **ComplianceService**: Audit logs + LGPD right-to-delete
2. ✅ **HITLService**: Human review queue + decision recording
3. ✅ **ReEngagementService**: Auto-send emails for inactive candidates

**Métricas de éxito**:
- Audit trail: 100% of mutations logged
- LGPD deletion: <24h execution
- HITL flow: Full workflow end-to-end
- Re-engagement: Email sending working
- 15+ integration tests

---

## 🎯 5 Actividades de Unit 6

### Actividad 1: Diseño Funcional (4 horas)

**5 Aggregates**:

1. **AuditLogAggregate**:
   - Entity: `AuditLog` (id, entity_type, entity_id, action, user_id, timestamp, changes_json, ip_address)
   - Value Objects: `AuditAction` (CREATE, UPDATE, DELETE, RETRIEVE), `EntityType`, `Changes`
   - Rules: Append-only, immutable, 7-year retention, indexed by entity_id

2. **ConsentAggregate**:
   - Entity: `Consent` (id, candidate_id, campaign_id, type, given_at, revoked_at)
   - Value Objects: `ConsentType` (DATA_PROCESSING, RECORDING, ANALYTICS), `ConsentStatus`
   - Rules: Must obtain before screening, can revoke anytime, audit on revocation

3. **HITLQueueAggregate**:
   - Entity: `HITLQueue` (id, evaluation_id, status, assigned_to, created_at, completed_at)
   - Value Objects: `HITLStatus` (PENDING, IN_REVIEW, DECIDED, ARCHIVED), `Decision` (PASS/FAIL/APPEAL)
   - Rules: Move to queue if evaluation marked REVIEW, recruiter must decide, decision immutable

4. **DataRetentionAggregate**:
   - Entity: `DataRetention` (id, candidate_id, data_type, retention_until, deleted_at)
   - Value Objects: `DataType` (SCREENING, EVALUATION, TRANSCRIPTION), `RetentionPolicy`
   - Rules: Auto-delete after retention period, LGPD right-to-be-forgotten overrides

5. **ReEngagementAggregate**:
   - Entity: `ReEngagementCampaign` (id, session_id, last_contacted_at, email_sent_count, status)
   - Value Objects: `ReEngagementStatus` (PENDING, EMAILED, REACTIVATED, FAILED), `EmailTemplate`
   - Rules: Send 24h/48h after inactivity, max 2 emails, stop after reactivation

**15 Business Rules**:
1. **RULE-COMPLIANCE-01**: Append-only audit log
2. **RULE-COMPLIANCE-02**: No direct data deletion (soft delete only)
3. **RULE-COMPLIANCE-03**: LGPD right-to-be-forgotten (24h hard delete)
4. **RULE-COMPLIANCE-04**: Consent before processing
5. **RULE-COMPLIANCE-05**: Consent revocation instant
6. **RULE-COMPLIANCE-06**: Audit trail for consent changes
7. **RULE-COMPLIANCE-07**: HITL queue escalation (evaluation = REVIEW)
8. **RULE-COMPLIANCE-08**: Recruiter decision immutable
9. **RULE-COMPLIANCE-09**: Decision audit logged
10. **RULE-COMPLIANCE-10**: Re-engagement eligibility (24h inactivity)
11. **RULE-COMPLIANCE-11**: Email rate limiting (max 2/candidate)
12. **RULE-COMPLIANCE-12**: Candidate notification on action
13. **RULE-COMPLIANCE-13**: Data retention auto-cleanup
14. **RULE-COMPLIANCE-14**: Archive old HITL records (30d+)
15. **RULE-COMPLIANCE-15**: Compliance reporting (PDF export)

**5 E2E Flows**:

1. **Flow 1: LGPD Right-to-Forget** (600 words)
   - Pre-condition: Candidate requests deletion
   - Steps:
     1. Receive DELETE /api/candidates/{id}/data request
     2. Validate consent (must have given consent to delete)
     3. Create AuditLog: ACTION=DELETE_REQUESTED
     4. Mark all related data for deletion (soft delete)
     5. Queue Celery task: hard_delete_after_24h()
     6. Send candidate confirmation email
     7. After 24h: hard delete (irreversible)
     8. Create AuditLog: ACTION=DELETE_COMPLETED
   - Immutable: After deletion, no recovery

2. **Flow 2: Consent Management** (400 words)
   - Pre-condition: Candidate takes action (withdraw consent)
   - Steps:
     1. POST /api/candidates/{id}/consent/revoke
     2. Validate current consent status
     3. Transition Consent.status to REVOKED
     4. Create AuditLog: ACTION=CONSENT_REVOKED
     5. Stop any pending re-engagement emails
     6. Mark session as PII-redacted
     7. Send revocation confirmation
   - Instant: No 24h delay

3. **Flow 3: HITL Queue Escalation** (500 words)
   - Trigger: Evaluation completed with recommendation = REVIEW
   - Steps:
     1. Event: EvaluationCompleted received
     2. Check recommendation == REVIEW
     3. Create HITLQueue entry (status=PENDING)
     4. Assign to recruiter (round-robin or load-based)
     5. Notify recruiter (email + dashboard)
     6. Track queue wait time (metric)
     7. Recruiter reviews evaluation + transcript
     8. Recruiter clicks PASS/FAIL/APPEAL
     9. Create HITLDecision aggregate
     10. Create AuditLog: ACTION=HITL_DECIDED
     11. Publish event: HITLDecisionMade
     12. Archive HITL record after 30d
   - SLA: Decision within 24h

4. **Flow 4: Re-engagement Campaign** (500 words)
   - Trigger: Celery task (every 6h)
   - Steps:
     1. Query sessions where created_at < now - 24h AND status != COMPLETED
     2. For each inactive session:
        a. Check consent (if revoked, skip)
        b. Check email count (if >=2, skip)
        c. Load email template (HTML)
        d. Personalize (candidate name, job title)
        e. Send via SES (Amazon Simple Email Service)
        f. Create ReEngagementCampaign record
        g. Increment email_sent_count
        h. Create AuditLog: ACTION=REENGAGEMENT_EMAIL_SENT
     3. If candidate reactivates (new message):
        a. Transition to REACTIVATED
        b. Create AuditLog: ACTION=REENGAGEMENT_SUCCESS
     4. Task completes, logs summary
   - Email templates: 24h reminder, 48h final reminder

5. **Flow 5: Data Retention Cleanup** (400 words)
   - Trigger: Celery task (once daily, midnight UTC)
   - Steps:
     1. Query DataRetention where retention_until < now AND deleted_at IS NULL
     2. For each expired record:
        a. Soft delete related data (set deleted_at = now)
        b. Mark transcriptions/evaluations as archived
        c. Create AuditLog: ACTION=AUTO_CLEANUP
        d. Delete from S3 (transcriptions older than 7y)
     3. Cleanup HITL records >30d old
     4. Task logs count + duration
   - Safety: Audit trail before deletion

---

### Actividad 2: NFR Requirements (2 horas)

**6 NFRs**:
1. **Compliance**: LGPD 24h deletion, 7-year audit retention
2. **Audit Trail**: 100% mutation coverage
3. **HITL Latency**: Queue processing <1s
4. **Email Reliability**: >99% delivery (SES bounce handling)
5. **Data Retention**: Auto-cleanup no manual intervention
6. **Observability**: Compliance metrics tracked (deletion count, consent revocations)

---

### Actividad 3: NFR Design (2 horas)

**4 ADRs**:
1. **ADR-UNIT6-001**: Soft Delete vs Hard Delete Strategy
2. **ADR-UNIT6-002**: Email Service (SES vs third-party like SendGrid)
3. **ADR-UNIT6-003**: HITL Queue Assignment (round-robin vs load-based)
4. **ADR-UNIT6-004**: Audit Log Storage (RDS vs separate data warehouse)

---

### Actividad 4: Infrastructure Design (2 horas)

**3 Services**:

```
1. ComplianceService
   ├─ Audit log repository
   ├─ Consent manager
   └─ Data retention scheduler

2. HITLService
   ├─ Queue manager
   ├─ Decision recorder
   └─ Notification handler

3. ReEngagementService
   ├─ Email scheduler (Celery)
   ├─ Template engine (Jinja2)
   └─ Delivery tracker

External:
   ├─ Amazon SES (email)
   ├─ Redis (job queue)
   └─ PostgreSQL (audit logs)
```

---

### Actividad 5: Code Generation + Tests (4 horas)

**Structure**:
```
backend/app/services/
├── compliance.py           (300+ lines) — Audit + consent + retention
├── hitl.py                 (250+ lines) — Queue + decisions
└── reengagement.py         (200+ lines) — Email scheduling

backend/app/routers/
├── compliance.py           (100+ lines) — DELETE, GET audit logs
├── hitl.py                 (150+ lines) — Queue, decisions, assignment
└── reengagement.py         (50+ lines)  — Re-engagement status

backend/app/tasks/
├── retention_cleanup.py    (100+ lines) — Auto-delete scheduler
├── hitl_assignment.py      (80+ lines)  — Assign HITL to recruiter
└── reengagement_email.py   (120+ lines) — Send emails

backend/app/models/
├── audit_log.py
├── consent.py
├── hitl_queue.py
├── data_retention.py
└── reengagement.py

tests/integration/
├── test_lgpd_flow.py           (200+ lines)
├── test_hitl_queue.py          (150+ lines)
├── test_reengagement.py        (150+ lines)
├── test_audit_trail.py         (100+ lines)
└── test_compliance_flow.py     (200+ lines)
```

**Key Implementation**:

**ComplianceService.request_data_deletion()**:
```python
async def request_data_deletion(self, candidate_id: str, token: str) -> Dict:
    # 1. Validate consent (must have consented to processing)
    # 2. Create audit log: DELETE_REQUESTED
    # 3. Soft delete candidate data
    # 4. Queue Celery task: hard_delete_after_24h(candidate_id)
    # 5. Send confirmation email
    # 6. Return: deletion_scheduled_for=now+24h
```

**HITLService.create_hitl_record()**:
```python
async def create_hitl_record(self, evaluation_id: str) -> Dict:
    # 1. Fetch evaluation + recommendations
    # 2. If recommendation != REVIEW, return early
    # 3. Create HITLQueue record (status=PENDING)
    # 4. Assign to recruiter (round-robin)
    # 5. Send notification
    # 6. Create audit log: HITL_CREATED
```

**ReEngagementService.send_reengagement_emails()**:
```python
async def send_reengagement_emails(self) -> Dict:
    # 1. Query inactive sessions (24h+)
    # 2. For each: check consent, email count, template
    # 3. Render email (Jinja2 template)
    # 4. Send via SES (with bounce/complaint handling)
    # 5. Create ReEngagementCampaign record
    # 6. Log audit: REENGAGEMENT_EMAIL_SENT
    # 7. Return: sent_count, failed_count
```

**Tests** (15+ total):
1. LGPD deletion flow (end-to-end)
2. Consent revocation (stops re-engagement)
3. HITL queue creation + assignment
4. Recruiter decision recording
5. Audit trail completeness
6. Email sending (SES mock)
7. Data retention auto-cleanup
8. Soft delete + hard delete after 24h
9. Concurrent decision submissions (locking)
10. Celery task scheduling
11. Email template rendering
12. Bounce handling (SES delivery)
13. HITL archive (30d+)
14. Compliance reporting (PDF export)
15. Integration: all units together

---

## 📊 Team (2 Backend Engineers)

**Split**:
- **Engineer 1**: ComplianceService + audit logs
- **Engineer 2**: HITLService + ReEngagementService
- **Sync**: Events, testing, integration

**Timeline**:
- **Week 4 (4d)**: Design + ADRs
- **Week 5 (3d)**: Core implementation
- **Week 6 (3d)**: Tests + integration with Units 2-5

---

## 🎯 Success Metrics

| Métrica | Target |
|---------|--------|
| Audit trail coverage | 100% |
| LGPD deletion latency | <24h |
| HITL decision SLA | <24h |
| Email delivery rate | >99% |
| pytest passing | 100% |
| Coverage | >80% |

---

## 🔄 Event Dependencies

Unit 6 **subscribes to** events from:
- Unit 2: SessionCompleted, SessionAbandoned
- Unit 3: ConversationCompleted
- Unit 4: EvaluationCompleted

Unit 6 **publishes** events for:
- Unit 5: HITLQueueUpdated (for dashboard refresh)
- All units: ComplianceAuditLogged

---

**Generado**: 2026-05-27  
**Unit**: 6 - Compliance + HITL  
**Status**: ⏳ Final unit, depends on Unit 2-3 event system

