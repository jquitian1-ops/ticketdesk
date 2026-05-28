# Milestones — TicketDesk Enterprise v1.0

**Planning Wave**: `ticketdesk-enterprise-implementation`  
**Duration**: 4 weeks (27 May - 23 June 2026)  
**Status**: Ready for execution

---

## M1: Unit 1 + Unit 6 (Auth & Compliance)

**Target Date**: Friday, 31 May 2026  
**Week**: 1  
**Duration**: 5 days (Mon 27 - Fri 31)

### Objective
Implement authentication foundation (JWT RS256, RBAC) and compliance framework (audit logging) for LGPD requirements.

### Deliverables
- ✅ PostgreSQL schema with users, roles, sessions, audit_logs tables
- ✅ User aggregate with validation and password hashing
- ✅ JWT RS256 authentication service (15min token, refresh token rotation)
- ✅ RBAC decorator supporting 3 roles (admin, recruiter, candidate)
- ✅ AuditLog aggregate and middleware for compliance tracking
- ✅ Docker setup (multi-stage image < 800MB)
- ✅ GitHub Actions CI/CD pipeline (6 stages: lint → test → build → deploy)

### Success Criteria
- [ ] 70+ unit + integration tests created
- [ ] Coverage: 88% minimum
- [ ] 0 security vulnerabilities (bandit, npm audit clean)
- [ ] Build < 800MB, startup < 10s
- [ ] All tests green
- [ ] Smoke tests pass on staging

### Release
- **Version**: v0.1.0
- **Tag**: `v0.1.0`
- **Deploy Target**: Staging

### Tasks Included
| Task ID | Title | Assignee | Hours | Status |
|---------|-------|----------|-------|--------|
| T1.1 | Database Schema | ENGINEER-1 | 8 | pending |
| T1.2 | User Aggregate + Repository | ENGINEER-1 | 12 | pending |
| T1.3 | Authentication Service (JWT RS256) | ENGINEER-1 | 10 | pending |
| T1.4 | RBAC (Role-Based Access Control) | ENGINEER-1 | 8 | pending |
| T1.5 | Audit Logging Framework | ENGINEER-1 | 10 | pending |
| T1.6 | Docker Setup + CI/CD Pipeline | ENGINEER-2 | 12 | pending |

**Total Hours**: 60 hours (7.5 days of work distributed across 2 engineers)

---

## M2: Unit 2 (Session Management)

**Target Date**: Friday, 7 June 2026  
**Week**: 2  
**Duration**: 5 days (Mon 3 - Fri 7)

### Objective
Implement Session aggregate for candidate screening flow, including repository pattern, service layer, and REST API endpoints.

### Deliverables
- ✅ Session schema migration (with soft-delete for LGPD)
- ✅ Session aggregate (state machine: pending → screening → evaluated)
- ✅ SessionRepository with SQLAlchemy ORM
- ✅ SessionService with business logic
- ✅ REST API endpoints (POST/GET/DELETE /api/sessions)
- ✅ Comprehensive test suite (48+ tests, 92% coverage)

### Success Criteria
- [ ] 48+ unit + integration tests
- [ ] Coverage: 92% minimum
- [ ] POST /api/sessions returns 201 with session_id
- [ ] GET /api/sessions/:id returns 200 with full session data
- [ ] DELETE /api/sessions/:id soft-deletes (sets deleted_at)
- [ ] PII (candidate_email) never logged
- [ ] State machine validates correctly
- [ ] All tests green

### Release
- **Version**: v0.2.0
- **Tag**: `v0.2.0`
- **Deploy Target**: Staging

### Tasks Included
| Task ID | Title | Assignee | Hours | Status |
|---------|-------|----------|-------|--------|
| T2.1 | Session Schema + Migration | ENGINEER-1 | 6 | pending |
| T2.2 | Session Aggregate | ENGINEER-1 | 12 | pending |
| T2.3 | SessionRepository + Service Layer | ENGINEER-1 | 10 | pending |
| T2.4 | Session API Endpoints | ENGINEER-1 | 8 | pending |
| T2.5 | Comprehensive Test Suite | QA | 8 | pending |

**Total Hours**: 44 hours

---

## M3: Unit 3 + Unit 4 (BotEngine & Evaluation)

**Target Date**: Friday, 16 June 2026  
**Week**: 3  
**Duration**: 7 days (Mon 10 - Fri 14)

### Objective
Implement Claude API integration (BotEngine) with jailbreak detection and evaluation scoring engine.

### Deliverables
- ✅ Claude API client with SSE streaming
- ✅ Token budget tracking (max 2000/session)
- ✅ Jailbreak detection (>95% accuracy, <100ms latency)
- ✅ EvaluationScore class and EvaluationEngine
- ✅ Scoring algorithm (technical, communication, problem-solving)
- ✅ Decision logic (HIRE, MAYBE, REJECT)
- ✅ Citation extraction (>85% recall)
- ✅ End-to-end integration (Session → BotEngine → Evaluation)

### Success Criteria
- [ ] Claude API calls working (latency < 3s P95)
- [ ] SSE streaming < 100ms
- [ ] Jailbreak detection: >95% accuracy, <5% false negatives
- [ ] Token budget correctly tracked and enforced
- [ ] Scoring accuracy > 90% (vs manual review)
- [ ] Decision logic correct (edge cases handled)
- [ ] 50+ tests for Unit 3 + Unit 4
- [ ] Full E2E flow: session.add_message() → claude.evaluate() → score()

### Release
- **Version**: v0.3.0
- **Tag**: `v0.3.0`
- **Deploy Target**: Staging

### Tasks Included
| Task ID | Title | Assignee | Hours | Status |
|---------|-------|----------|-------|--------|
| T3.1 | BotEngine: Claude API Client | ENGINEER-1 | 10 | pending |
| T3.2 | Jailbreak Detection | ENGINEER-1 | 8 | pending |
| T3.3 | Evaluation Engine + Scoring | ENGINEER-1 | 12 | pending |
| T3.4 | Integration: Unit 2 + 3 + 4 | ENGINEER-1 | 6 | pending |

**Total Hours**: 36 hours

---

## M4: Unit 5 + E2E + Production (FINAL)

**Target Date**: Friday, 23 June 2026  
**Week**: 4  
**Duration**: 7 days (Mon 17 - Fri 23)

### Objective
Implement Next.js frontend, end-to-end testing, and deploy to production. Final release of TicketDesk Enterprise v1.0.

### Deliverables
- ✅ Next.js 14 app router with TypeScript
- ✅ Global layout and authentication context
- ✅ CandidateChat component (SSE streaming, message history)
- ✅ RecruiterQueue component (list, filtering, search)
- ✅ EvaluationModal component (score visualization)
- ✅ Zustand state management
- ✅ 25+ E2E Playwright scenarios
- ✅ Production infrastructure (Terraform, ECS, ALB, RDS)
- ✅ CloudWatch dashboards and alerts
- ✅ On-call runbooks and incident response

### Success Criteria
- [ ] Frontend builds without errors (< 10MB gzipped)
- [ ] JavaScript bundle < 300KB gzipped
- [ ] 25+ E2E scenarios passing
- [ ] No flakiness (0 retries needed)
- [ ] Lighthouse score: 90+
- [ ] Core Web Vitals:
  - LCP ≤ 2.5s
  - INP ≤ 200ms
  - CLS ≤ 0.1
- [ ] Accessibility: WCAG 2.2 AAA (0 axe violations)
- [ ] Production smoke tests: all pass
- [ ] Uptime monitoring: 99.5% SLA configured
- [ ] On-call ready: runbooks documented

### Release
- **Version**: v1.0.0
- **Tag**: `v1.0.0`
- **Deploy Target**: Production
- **Release Date**: Friday, 23 June 2026

### Tasks Included
| Task ID | Title | Assignee | Hours | Status |
|---------|-------|----------|-------|--------|
| T4.1 | Frontend Setup + Layout | ENGINEER-2 | 8 | pending |
| T4.2 | Candidate Interview Component | ENGINEER-2 | 10 | pending |
| T4.3 | Recruiter Dashboard | ENGINEER-2 | 10 | pending |
| T4.4 | E2E Testing (Playwright) | QA | 12 | pending |
| T4.5 | Production Deployment | ORCHESTRATOR | 8 | pending |

**Total Hours**: 48 hours

---

## Summary

```
PLANNING WAVE: ticketdesk-enterprise-implementation

Total Duration:    4 weeks
Total Tasks:       20
Total Hours:       188 hours
Team Size:         5 agents
Sprint Duration:   1 week per sprint

Milestone Timeline:
  M1 (Auth + Compliance)      → 31 May 2026    → v0.1.0
  M2 (Session Management)     → 7 June 2026    → v0.2.0
  M3 (BotEngine + Eval)       → 16 June 2026   → v0.3.0
  M4 (Frontend + E2E + Prod)  → 23 June 2026   → v1.0.0 ✨ FINAL

Success Path:
  M1: Auth foundation + LGPD framework ready
  M2: Session flow complete + audit trail working
  M3: Claude integration verified + scoring functional
  M4: User-facing product + production SLAs met

Deliverables:
  - 150+ automated tests (>80% coverage)
  - 0 security vulnerabilities
  - LGPD compliant hard-delete (<24h)
  - WCAG 2.2 AAA accessibility
  - Core Web Vitals performance targets
  - 99.5% uptime SLA
  - Production monitoring + incident response
```

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Claude API quota exceeded | Medium | High | Token budget 2000/session, rate limiting 100 req/min |
| Unit 2→3 dependency blocked | Medium | High | Unit 3 starts with mocks, fast switch to integration |
| Performance regression | Medium | High | Weekly Lighthouse testing, bundle size monitoring |
| Prod deployment fails | Low | Critical | Blue/green strategy, rollback tested on staging |
| Accessibility gaps | Medium | Medium | axe automated + manual NVDA testing, specialist review |

---

## Sign-off

| Role | Name | Signature | Date |
|------|------|-----------|------|
| ORCHESTRATOR | Planning Lead | - | - |
| ARCHITECT | Tech Lead | - | - |
| Product | Product Lead | - | - |

**Planning Wave Status**: 🟢 **READY FOR EXECUTION**

**Next Step**: Convert milestones to Linear issues. See `docs/tasks/linear-publish.yaml`.
