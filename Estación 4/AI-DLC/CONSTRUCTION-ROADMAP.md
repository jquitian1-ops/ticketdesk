# TicketDesk Enterprise v1.0 — Construction Roadmap (Semanas 1-6)

**Proyecto**: TicketDesk Enterprise — AI-powered candidate screening  
**Fase**: Construction (AI-DLC)  
**Total Duration**: 6 weeks (Weeks 1-2: Unit 1, Weeks 2-5: Units 2-6 mixed, Week 6: Integration & UAT)  
**Team Size**: 6-7 developers  
**Start Date**: 2026-05-27  
**Target MVP Completion**: 2026-07-08  

---

## 📊 6 Units Overview

| Unit | Tema | Duration | Team | Status | Bloqueador | Bloquea |
|------|------|----------|------|--------|-----------|---------|
| **1** | Infraestructura (AWS) | Semanas 1-2 | 1 DevOps | ✅ DONE | - | 2,3,4,5,6 |
| **2** | Backend Fundamentals | Semanas 2-4 | 2 Backend | 🚀 READY | Unit 1 | 3,4,6 |
| **3** | BotEngine (Claude) | Semanas 3-5 | 1 Backend | ⏳ WAITING | Unit 1,2 | 6 |
| **4** | EvaluationEngine | Semanas 3-5 | 1 Backend | ⏳ WAITING | Unit 1,2 | 6 |
| **5** | Frontend (Next.js) | Semanas 3-5 | 2 Frontend | ⏳ WAITING | Unit 1 | 6 |
| **6** | Compliance + HITL | Semanas 4-6 | 2 Backend | ⏳ WAITING | Unit 1,2,3 | - |

---

## 🗓️ Week-by-Week Timeline

### **Week 1-2: Unit 1 (Infraestructura)**
**Responsible**: 1 DevOps Engineer  
**Status**: ✅ COMPLETED  

**Deliverables**:
- ✅ Actividad 1: Domain modeling (entities, rules, flows)
- ✅ Actividad 2: 6 NFRs + 6 ADRs
- ✅ Actividad 3: Deployment architecture
- ✅ Actividad 4: Terraform code (11 modules, 4,500+ lines)
- ✅ Actividad 5: Testing plan + automation script

**Success Criteria**:
- `terraform validate` passes
- `terraform apply` provisions infrastructure
- All health checks green
- Load test: p99 <2s latency
- CloudWatch monitoring active

**Artifacts**:
- `aidlc-docs/construction/unit-1-infrastructure/` (5 Actividades)
- `terraform/` (50+ files, 11 modules)
- `.github/workflows/terraform.yml` (CI/CD)

---

### **Week 2-4: Unit 2 (Backend Fundamentals)** [OVERLAPS WEEK 2]
**Responsible**: 2 Backend Engineers  
**Status**: 🚀 READY TO START  

**Actividades** (same 5-activity pattern):
1. **Actividad 1** (3-4h): Domain entities + business rules + E2E flows
2. **Actividad 2** (2-3h): 6 NFRs (performance, security, scalability, etc.)
3. **Actividad 3** (2-3h): 4 ADRs (JWT, event system, repository pattern, DI)
4. **Actividad 4** (2h): FastAPI architecture + database schema
5. **Actividad 5** (4-6h): Code generation + tests (15+ tests, >80% coverage)

**Deliverables**:
- `backend/` — FastAPI project (main.py, models, schemas, repos, services, routers)
- `app/database/` — SQLAlchemy models (9 tables) + Alembic migrations
- `tests/` — pytest suite (unit + integration + e2e)
- `requirements.txt` — Python dependencies
- `docker-compose.yml` — Local dev environment

**Success Criteria**:
- `pytest` passes (15+ tests, >80% coverage)
- `alembic upgrade` creates 9 tables
- FastAPI `/docs` accessible (OpenAPI)
- JWT auth middleware working
- Event system (Redis Pub/Sub) integrated with Celery
- All repositories CRUD-able

**Artifacts**:
- `aidlc-docs/construction/unit-2-backend/` (5 Actividades + code)
- `backend/app/` (FastAPI skeleton + models + services + tests)

---

### **Week 3-5: Units 3, 4, 5 (PARALLEL)**

#### **Unit 3: BotEngine** (Semanas 3-5)
**Responsible**: 1 Backend Engineer  
**Bloqueado por**: Unit 1 ✅, Unit 2  
**Status**: ⏳ Pending Unit 2

**Scope**: 
- Claude API integration (streaming responses)
- Jailbreak detection (prompt filtering)
- Out-of-scope detection (off-topic handling)
- Session state management (Redis)
- Transcription management (S3)
- Question branching logic
- 10 unit tests + 5 integration tests

**Key Component**: `BotEngine` service (from application-design.md)

**Deliverables**:
- `backend/app/services/bot_engine.py` (300+ lines)
- `backend/app/routers/screening.py` (POST /api/screening/start)
- `tests/integration/test_bot_engine.py`
- Event handlers for BotEngine events

---

#### **Unit 4: EvaluationEngine** (Semanas 3-5)
**Responsible**: 1 Backend Engineer  
**Bloqueado por**: Unit 1 ✅, Unit 2  
**Status**: ⏳ Pending Unit 2

**Scope**:
- Claude API for scoring (structured output)
- Rubric loading + caching (Redis)
- Citation extraction (fuzzy matching)
- Fairness validation (confidence scores)
- Final score calculation
- Recommendation generation
- 10 unit tests + 5 integration tests

**Key Component**: `EvaluationEngine` service

**Deliverables**:
- `backend/app/services/evaluation_engine.py` (400+ lines)
- `backend/app/services/citation_extractor.py`
- `tests/integration/test_evaluation_engine.py`
- Event handlers for evaluation workflow

---

#### **Unit 5: Frontend** (Semanas 3-5)
**Responsible**: 2 Frontend Engineers  
**Bloqueado por**: Unit 1 ✅ (infrastructure)  
**Status**: ⏳ Can start in parallel with Unit 2

**Scope**:
- Next.js 14 project setup + routing
- State management (Zustand)
- HTTP client (React Query + Axios)
- CandidateInterface (chat UI) — streaming responses
- Consent form + session flow
- RecruiterDashboard (evaluation queue)
- Candidate detail panel
- Real-time updates (polling)
- CampaignManager CRUD
- Authentication & authorization
- Styling (Tailwind)
- 10+ integration tests

**Key Components**: 
- `CandidateInterface` (from application-design.md)
- `RecruiterDashboard`
- `CampaignManager`

**Deliverables**:
- `frontend/app/` (Next.js pages + components)
- `frontend/components/` (Candidate chat, dashboard, etc.)
- `frontend/hooks/` (Custom React hooks)
- `frontend/services/` (API client)
- `tests/` (Jest + React Testing Library)

---

### **Week 4-6: Unit 6 (Compliance + HITL)**
**Responsible**: 2 Backend Engineers  
**Bloqueado por**: Unit 1 ✅, Unit 2, Unit 3 (events)  
**Status**: ⏳ Pending Units 2-3

**Scope**:
- ComplianceService (audit logs, append-only)
- Consent management (LGPD right-to-withdraw)
- Data retention & soft-delete (30-day auto-purge)
- LGPD right-to-be-forgotten (24h execution)
- Compliance reporting (PDF generation)
- ReEngagementService (inactivity detection)
- Email scheduling (24h/48h re-engagement)
- Email templates (Jinja2)
- HITLService (queue management, human review)
- Decision recording (recruiter action tracking)
- Candidate notifications (email + in-app)
- API endpoints (compliance, queue, decision)
- 10+ integration tests

**Key Components**:
- `ComplianceService`
- `ReEngagementService`
- `HITLService`

**Deliverables**:
- `backend/app/services/compliance.py` (300+ lines)
- `backend/app/services/hitl.py` (250+ lines)
- `backend/app/services/reengagement.py` (200+ lines)
- `backend/app/routers/compliance.py` (endpoints)
- `tests/integration/test_compliance_flow.py`
- Email templates + Celery tasks

---

## 🔀 Dependency Graph

```
Unit 1 (Infraestructura) ✅ DONE
    │
    ├──→ Unit 2 (Backend Fundamentals) 🚀 STARTS
    │        │
    │        ├──→ Unit 3 (BotEngine) ⏳
    │        │
    │        ├──→ Unit 4 (EvaluationEngine) ⏳
    │        │
    │        └──→ Unit 6 (Compliance + HITL) ⏳
    │
    └──→ Unit 5 (Frontend) ⏳ (can start in parallel)

All Units 3,4,5,6 RUN IN PARALLEL (Weeks 3-5+)
Integration Phase (Week 6): All units tested together
```

---

## 📦 Integration Checklist (Week 6)

### System-Level Tests:
- [ ] Full screening flow: Create session → Bot chat → Evaluation → Dashboard
- [ ] Event propagation: BotEngine event → EvaluationEngine processes
- [ ] Compliance auditing: All mutations logged + retrievable
- [ ] LGPD flow: Consent → Withdraw → Data deleted within 24h
- [ ] Re-engagement: Inactivity detection → Email sent → Candidate reactivates
- [ ] HITL workflow: Evaluation completed → Recruiter reviews → Decision recorded

### Cross-Unit Tests:
- [ ] Backend + Frontend: API responses match frontend expectations
- [ ] Frontend + Infrastructure: React Query handles ECS health issues
- [ ] Infrastructure + Backend: Database failover triggers circuit breaker
- [ ] All Units: End-to-end candidate screening (no errors)

### Performance Validation:
- [ ] Load test: 50 concurrent candidates, p99 <2s
- [ ] Database: No slow queries (>100ms)
- [ ] Cache: >85% hit rate during peak load
- [ ] Celery: Queue depth <100, processing time <10s per task

### Security & Compliance:
- [ ] PII: Never appears in logs, masked in responses
- [ ] Audit trail: 100% coverage of mutations
- [ ] Encryption: KMS keys rotating, TLS 1.3 enforced
- [ ] LGPD: Data deletion tests passing

---

## 🎯 Success Criteria (MVP Ready)

### Functional:
- [x] Unit 1: Infra deployed, monitoring active ✅
- [ ] Unit 2: Backend services CRUD-able
- [ ] Unit 3: BotEngine streams responses from Claude
- [ ] Unit 4: EvaluationEngine scores + provides evidence
- [ ] Unit 5: Frontend displays chat + dashboard + recruiting queue
- [ ] Unit 6: Compliance logs all actions, HITL queue operational

### Non-Functional:
- [ ] Performance: p99 <2s (all endpoints)
- [ ] Availability: 99.5% uptime (7-day baseline)
- [ ] Security: JWT + RBAC working
- [ ] Compliance: LGPD right-to-delete working
- [ ] Test coverage: >80% across all units

### Operational:
- [ ] CI/CD: All PRs validated, automated tests pass
- [ ] Monitoring: CloudWatch dashboards + alarms
- [ ] Documentation: API docs + runbooks
- [ ] Deployment: ECS deployment <5 minutes

---

## 🚀 Post-MVP Roadmap (v1.1)

After Unit 1-6 complete:

**Week 7: UAT + Staging Validation**
- Conduct user acceptance testing
- Fix bugs from UAT
- Finalize SLAs

**Week 8: Production Deployment**
- DNS cutover
- Data migration (if legacy system)
- Smoke tests
- Go-live preparation

**v1.1 Future Enhancements** (post-MVP):
- Microservices architecture (Unit 3, 4, 6 separate services)
- Additional evaluation models (beyond Claude)
- Custom NLP rules (jailbreak detection)
- Webhook integrations (ATS systems)
- Advanced scheduling (bulk campaigns)
- Analytics dashboard

---

## 📞 Team Communication

### Daily:
- **15-min standup**: Blockers + progress
- **Slack #construction**: Async updates

### Weekly:
- **Monday planning**: Weekly goals
- **Friday retrospective**: Lessons learned
- **Code review SLA**: <24h turnaround

### Critical Paths:
- Unit 1 → Unit 2 gate: All Actividad 5 tests passing
- Unit 2 → Unit 3,4,6 gate: Core services deployed
- All units → UAT gate: E2E smoke tests passing

---

## 📊 Cost Tracking

| Unit | Infrastructure Cost | Team Cost (2 weeks) | Total |
|------|------|------|------|
| Unit 1 | $250/month ✅ | $8,000 | $8,250 |
| Unit 2 | $250/month | $16,000 (2 eng × 2 weeks) | $16,250 |
| Unit 3 | $250/month | $8,000 (1 eng × 2 weeks) | $8,250 |
| Unit 4 | $250/month | $8,000 (1 eng × 2 weeks) | $8,250 |
| Unit 5 | $250/month | $16,000 (2 eng × 2 weeks) | $16,250 |
| Unit 6 | $250/month | $16,000 (2 eng × 2 weeks) | $16,250 |
| **Total** | **$1,500/month** | **$72,000** | **$73,500** |

---

## ✅ Approval Gates

### Unit 1 → Unit 2:
- [ ] All Terraform tests passing
- [ ] Infrastructure health checks green
- [ ] Load test baseline captured
- [ ] CloudWatch monitoring active

### Unit 2 → Units 3,4,6:
- [ ] pytest passing (>80% coverage)
- [ ] Database schema created
- [ ] Event system working (Redis + Celery)
- [ ] API endpoints documented

### Units 3,4,5,6 → UAT:
- [ ] All integration tests passing
- [ ] No critical bugs
- [ ] Performance baseline met (p99 <2s)
- [ ] Security audit passed

### UAT → Production:
- [ ] Zero critical issues
- [ ] Incident response plan approved
- [ ] Runbooks documented
- [ ] Stakeholder approval

---

## 📚 Key Reference Docs

**Keep handy while building**:
- [CONSTRUCTION-HANDOFF.md](../CONSTRUCTION-HANDOFF.md) — How to use artifacts
- [Unit 1 Summary](./unit-1-infrastructure/UNIT-1-RESUMEN-FINAL.md) — Completed unit
- [Unit 2 Plan](./UNIT-2-PLAN.md) — Next unit (in progress)
- [application-design.md](../inception/application-design/application-design.md) — Source of truth for components
- [functional-design.md](../inception/design/functional-design.md) — Business logic reference

---

## 🏁 Final Notes

**TicketDesk Enterprise v1.0 is 6 weeks from MVP completion.**

- Unit 1 ✅ complete (infrastructure tested)
- Unit 2 🚀 ready to start (plan documented)
- Units 3-6 ⏳ queued (will parallelize weeks 3-5)

**Next action**: Assign Unit 2 to 2 backend engineers, execute Actividad 1.

---

**Generated**: 2026-05-27  
**AI-DLC Phase**: Inception ✅ + Construction (Unit 1 ✅, Unit 2+ pending)  
**Status**: 🚀 MVP Roadmap Complete

