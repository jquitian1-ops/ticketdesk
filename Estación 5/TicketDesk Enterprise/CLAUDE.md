# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## 📋 Project Overview

**TicketDesk Enterprise v1.0** — Plataforma de screening y evaluación de candidatos impulsada por Claude API

**Stack Tech**:
- Backend: FastAPI (Python 3.12), 6 bounded contexts (DDD)
- Frontend: Next.js 14 (TypeScript), Zustand state management
- AI Engine: Claude API via Anthropic SDK
- Database: PostgreSQL 15 (RDS Multi-AZ in production)
- Cache/Pub-Sub: Redis 7 (ElastiCache in production)
- Storage: S3 (transcriptions, reports)
- Task Queue: Celery workers + Redis
- Infrastructure: AWS ECS Fargate, Terraform IaC
- CI/CD: GitHub Actions (6-stage pipeline: lint→test→build→e2e→deploy-staging→deploy-prod)
- Monitoring: CloudWatch (logs, metrics, alarms, dashboards)
- Security: JWT RS256, KMS encryption, RBAC, LGPD compliance

**Project Status**: ✅ **ESTACIÓN 5 COMPLETADA** (All 5 phases: Inception→Construction→Testing→Deployment→Operations)

---

## 🏗️ Architecture (Domain-Driven Design)

**6 Bounded Contexts (Units)**:
1. **Unit 1 - Account Management**: Users, authentication, RBAC
2. **Unit 2 - Session Management**: Candidate screening, flow control, scoring
3. **Unit 3 - BotEngine**: Claude API integration, jailbreak detection, token budget
4. **Unit 4 - Evaluation Engine**: Decision scoring (HIRE/REJECT/MAYBE), rubric validation, citation extraction
5. **Unit 5 - Frontend**: Next.js UI, Zustand store, accessibility (WCAG 2.1 AA)
6. **Unit 6 - Compliance**: LGPD audit logging, hard delete <24h SLA, consent management, PII masking

**Communication Patterns**:
- Synchronous: REST APIs between services
- Asynchronous: Redis Pub/Sub (event streaming) + Celery (background tasks)

**Key Patterns**: Aggregate, Service Layer, Repository, Event-Driven, Circuit Breaker

---

## 📂 Directory Structure

```
backend/          # FastAPI, Unit 2 (Session Management)
├── app/main.py, api/, db/, schemas/, services/
├── tests/unit/, integration/, fixtures/
└── requirements.txt

botengine/        # Claude API integration, Unit 3
evaluation/       # Scoring engine, Unit 4
compliance/       # LGPD compliance, Unit 6
celery/           # Async tasks

frontend/         # Next.js UI, Unit 5
├── app/          # App router (candidate/, recruiter/, admin/)
├── components/   # CandidateChat, RecruiterQueue, EvaluationModal
├── hooks/        # useAuth, useStore (Zustand)
└── tests/        # Jest unit + integration tests

terraform/        # Infrastructure as Code
├── main.tf       # Root composition (11 modules)
├── modules/      # vpc, ecs_cluster, rds, elasticache, s3, kms, iam, alb, cloudwatch, route53
└── environments/ # prod/, staging/ terraform.tfvars

docker-compose.yml    # Local dev (8 services)
.github/workflows/
└── deploy.yml        # 6-stage CI/CD pipeline

aidlc-docs/           # Comprehensive documentation
├── product/          # PRODUCT.md, DESIGN.md
├── testing/          # 8 test specification files
├── deployment/       # DEPLOYMENT-PHASE-PLAN.md, TERRAFORM-PRODUCTION.md
└── operations/       # OPERATIONS-PHASE-PLAN.md
```

---

## 🚀 Quick Commands

**Local Development**:
```bash
docker-compose up -d                          # Start 8 services
docker-compose logs -f backend                # View logs
docker-compose down -v                        # Stop + clean volumes
```

**Backend (FastAPI)**:
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload       # Dev server (port 8000)
pytest tests/unit/ -v                         # Unit tests
pytest tests/integration/ -v                  # Integration tests
pytest --cov=app --cov-report=html            # Coverage
black . && pylint src/ && mypy src/           # Lint
```

**Frontend (Next.js)**:
```bash
cd frontend
npm install
npm run dev                                   # Dev server (port 3000)
npm test                                      # Jest tests
npm test -- --coverage                        # Coverage
npm run lint                                  # Lint + type check
```

**BotEngine, Evaluation, Compliance**:
```bash
cd [service]
pytest tests/unit/ -v
pytest tests/unit/[specific_test].py::test_name -v
```

**Terraform**:
```bash
cd terraform
terraform init -backend-config="key=prod/terraform.tfstate"
terraform validate && terraform fmt -recursive
terraform plan -var-file="environments/prod/terraform.tfvars" -out=tfplan
terraform apply tfplan
```

**Load Testing (Locust)**:
```bash
cd tests/load
pip install locust
locust -f locustfile.py --host=http://localhost:8000
```

---

## 📋 Standards & Requirements

**Python**:
- Lint: black, pylint 8.0+, mypy
- Test: pytest >80% coverage, pytest-asyncio, pytest-cov
- Style: PEP 8, type hints on all functions

**TypeScript/Next.js**:
- Lint: prettier, eslint airbnb-config, tsc strict mode
- Test: Jest >80% coverage, @testing-library for UI
- Style: camelCase functions, PascalCase components

**Database**:
- Always use parameterized queries (SQLAlchemy ORM)
- Alembic migrations for schema changes
- Index foreign keys + frequently filtered columns

**Security**:
- JWT RS256 only (asymmetric)
- HTTPS/TLS 1.3 minimum
- Pydantic validation on all API endpoints
- AWS Secrets Manager for secrets (prod), .env files (local)
- LGPD compliance: Hard delete <24h, 7-year log retention

---

## 🔐 Security Architecture

**Authentication & Authorization**:
- JWT RS256 (asymmetric): Private key signs, public key verifies
- RBAC: Candidate, Recruiter, Admin roles
- Token Storage: Secure HTTP-only cookies (backend), localStorage (frontend)
- Token Rotation: Refresh token sliding window

**API Security**:
- Rate Limiting: 100 req/min per user
- CORS: Restricted to frontend domains
- Input Validation: Pydantic schemas + custom validators
- XSS Prevention: HTML escaping, CSP headers
- SQL Injection: Parameterized queries via SQLAlchemy

**Data Protection (LGPD)**:
- PII Hashing: SHA-256(email + salt)
- Encryption: KMS keys at rest, TLS 1.3 in transit
- Hard Delete SLA: <24h mandatory
- Audit Logging: 100% event capture
- Data Retention: 7 years for compliance

---

## 📊 Performance SLAs

**Production Targets**:
- Uptime: 99.5% (~3.6h downtime/month)
- API Latency P95: <1s, P99: <2s
- Bot Response P95: <3s
- Cache Hit Rate: >85%
- Error Rate: <0.5%
- Hard Delete SLA: <24h (LGPD)

---

## 🧪 Testing Strategy (130+ Tests)

**Unit Tests** (80+ tests):
- backend: 48+ tests (aggregates, RBAC, audit logging)
- botengine: 25+ tests (jailbreak >95%, token budget, SSE <100ms)
- evaluation: 20+ tests (scorer >95%, citation extraction >90%)
- compliance: 15+ tests (LGPD, hard delete, consent integrity)
- frontend: 29 tests (components, hooks, utilities)

**Integration Tests** (20+ tests): With PostgreSQL + Redis

**E2E Tests** (25+ scenarios): Playwright on staging

**Load Tests** (3 scenarios): 200 concurrent users via Locust

**Security Tests** (18+ scenarios): OWASP Top 10 validation

**Run Tests**:
```bash
pytest --cov=app --cov-report=term-missing
npm test -- --coverage
```

---

## 🔄 CI/CD Pipeline

**6-Stage Automated Workflow** (GitHub Actions):
1. **Lint**: Python + TypeScript linters
2. **Test**: pytest + Jest with DB/Redis services
3. **Build**: Docker images → ECR with git SHA tag
4. **E2E Tests**: Playwright (non-blocking)
5. **Deploy-Staging**: ECS update on staging cluster
6. **Deploy-Production**: Blue/Green deployment on prod (main branch only)

**Deployment Flow**:
- staging branch → deploy-staging
- main branch → full 6-stage pipeline + prod deployment
- PRs → lint + test only

**Rollback**: Automatic on failure, manual via `aws ecs update-service --task-definition <previous>`

---

## 📈 Monitoring & Operations

**CloudWatch Dashboards** (5 main):
1. System Health: Uptime, ECS tasks, RDS, ALB
2. Application Performance: Latency (P50/P95/P99), error rate, cache hits
3. Database: Connections, slow queries, replication, storage
4. Security & Compliance: Login failures, hard delete, audit logs
5. Cost: Daily spend, cost by service, forecast

**Alert Routing**:
- P0 (Critical): PagerDuty SMS (5min response)
- P1 (High): Slack + email (15min)
- P2 (Medium): Slack (1hr)
- P3 (Low): Slack metrics

**On-Call Rotation**:
- 4-person weekly rotation (handoff Mondays 9am PT)
- Escalation: Oncall → Tech Lead → Eng Manager → VP Eng

**Incident Runbooks**:
- API Down (all 502/503)
- High Error Rate (>2%)
- API Slow (P95 >5s)
- See OPERATIONS-PHASE-PLAN.md for details

---

## 📚 Key Documentation

**Product** (`aidlc-docs/product/`):
- PRODUCT.md: Vision, personas, features, metrics, costs, roadmap
- DESIGN.md: Principles, bounded contexts, patterns, ADRs

**Testing** (`aidlc-docs/testing/`):
- UNIT-2 to UNIT-6 test specs
- LOAD-TESTS-LOCUST.md, E2E-TESTS-PLAYWRIGHT.md, SECURITY-TESTS-OWASP.md

**Deployment** (`aidlc-docs/deployment/`):
- DEPLOYMENT-PHASE-PLAN.md: 7-day timeline, phases, security
- TERRAFORM-PRODUCTION.md: IaC, commands, cost, security

**Operations** (`aidlc-docs/operations/`):
- OPERATIONS-PHASE-PLAN.md: SLAs, on-call, alerts, dashboards, runbooks, compliance

---

## 🎯 Key ADRs

1. **JWT RS256**: Service-to-service auth without key sharing
2. **Jailbreak Detection Regex**: Fast (<100ms), >95% accuracy
3. **Token Budget 2000/session**: Limits costs (~$0.30 per screening)
4. **Redis Pub/Sub**: Real-time events at scale
5. **Hard Delete Atomic**: Single Celery job <24h SLA
6. **CloudWatch Logs 7 years**: LGPD compliance requirement

---

## 🔍 Debugging Tips

**DB Connection**:
```bash
docker-compose ps postgres
docker-compose logs postgres
docker-compose exec backend env | grep DATABASE_URL
```

**Claude API 401**:
```bash
echo $CLAUDE_API_KEY
curl -H "Authorization: Bearer $CLAUDE_API_KEY" https://api.anthropic.com/v1/messages
```

**Frontend→Backend**:
```bash
curl http://localhost:8000/health
cat frontend/.env.local | grep NEXT_PUBLIC_API_URL
```

**Redis**:
```bash
docker-compose exec redis redis-cli ping
docker-compose exec redis redis-cli -a redis_dev_pass_123 ping
```

**Terraform Lock**:
```bash
terraform force-unlock <lock-id>
terraform state list | head -5
```

---

## 📞 Common Tasks

**Local Iteration**: Code → Tests → Verify → Commit

**Staging Deploy**: Push to staging → GitHub Actions → CloudWatch

**Production Deploy**: PR → Review → Merge main → Full pipeline → CloudWatch

**Add Feature**: Create branch → TDD → Tests → PR → Update docs

---

**Generado**: 2026-05-27  
**Estación 5 Status**: ✅ **COMPLETADA**  
**Fases**: 5/5 (Inception→Construction→Testing→Deployment→Operations)
