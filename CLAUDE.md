# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## TicketDesk Enterprise v1.0

**AI-Powered Candidate Screening Platform**

This repository implements a complete 4-week sprint to build TicketDesk Enterprise using:
- **Backend**: FastAPI + SQLAlchemy (Python)
- **Frontend**: Next.js 14 (TypeScript)
- **Database**: PostgreSQL 15
- **Infrastructure**: Docker, Terraform, AWS ECS
- **Agents**: Claude API with specialized agents (ORCHESTRATOR, ENGINEER-1, ENGINEER-2, QA, ARCHITECT)

---

## 📋 Execution Plan

**4 Sprints, 20 Tasks, 188 hours**

### Semana 1 (27-MAY to 31-MAY) — M1: Unit 1 + Unit 6
- **T1.1**: Database Schema (PostgreSQL)
- **T1.2**: User Aggregate + Repository
- **T1.3**: Authentication Service (JWT RS256)
- **T1.4**: RBAC (Role-Based Access Control)
- **T1.5**: Audit Logging Framework (LGPD compliance)
- **T1.6**: Docker Setup + CI/CD Pipeline
- **Deliverable**: v0.1.0 (70+ tests, 88% coverage)

### Semana 2 (3-JUNE to 7-JUNE) — M2: Unit 2
- T2.1 to T2.5: Session Management
- **Deliverable**: v0.2.0 (48+ tests, 92% coverage)

### Semana 3 (10-JUNE to 14-JUNE) — M3: Unit 3 + Unit 4
- T3.1 to T4.1: Interview Session + Jailbreak Detection
- **Deliverable**: v0.3.0 (50+ tests, jailbreak >95%)

### Semana 4 (17-JUNE to 23-JUNE) — M4: Unit 5 + E2E + Prod
- T4.1 to T4.5: Frontend + Testing + Production Deploy
- **Deliverable**: v1.0.0 Production Release (25+ E2E scenarios)

---

## 🔧 Development Setup

### Prerequisites
```bash
# Python 3.11+
python --version

# PostgreSQL 15
psql --version

# Node.js 20+
node --version

# Docker
docker --version
```

### Local Environment

1. **Create `.env` file** (NEVER commit):
```bash
# PostgreSQL (Development)
DATABASE_URL=postgresql://ticketdesk_user:dev_password@localhost:5432/ticketdesk_dev
DATABASE_SSL=false

# GitHub
GITHUB_TOKEN=ghp_xxxx...

# Vercel
VERCEL_TOKEN=xxxxx...

# Anthropic
ANTHROPIC_API_KEY=sk-ant-xxxxx
```

2. **Setup Python environment**:
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Setup PostgreSQL**:
```bash
createdb ticketdesk_dev
createuser ticketdesk_user
psql -d ticketdesk_dev -c "ALTER USER ticketdesk_user WITH PASSWORD 'dev_password';"
psql -d ticketdesk_dev -c "GRANT ALL PRIVILEGES ON DATABASE ticketdesk_dev TO ticketdesk_user;"
```

4. **Setup Node.js**:
```bash
cd frontend
npm install
```

---

## 📁 Project Structure

```
proyecto desde cero/
├── Estación 6/                      # Documentation & Specifications
│   ├── HARNESS-SPECIFICATION.md    # Claude Code + Opus setup
│   ├── AGENTS.md                   # Agent definitions
│   ├── VALIDATION-FRAMEWORK.md     # Quality gates
│   ├── ORCHESTRATION-PLAN.md       # Execution protocol
│   ├── ESTACION-7-EXECUTION-GUIDE.md
│   ├── docs/tasks/
│   │   ├── task-package.yaml       # 20 tasks in OpenSymphony format
│   │   ├── milestones.md
│   │   └── 001-T1.1-database-schema.md  # Task templates
│   └── MCP-*-SETUP.md              # Integration guides
│
├── backend/                         # FastAPI Application (Unit 1-4)
│   ├── src/
│   │   ├── main.py                 # FastAPI app
│   │   ├── config.py               # Settings
│   │   ├── models/                 # SQLAlchemy models
│   │   │   ├── user.py            # User aggregate (T1.2)
│   │   │   ├── session.py         # Session aggregate (T2.x)
│   │   │   ├── audit_log.py       # Audit logging (T1.5)
│   │   │   └── interview.py       # Interview session (T3.x)
│   │   ├── services/               # Business logic
│   │   │   ├── auth_service.py    # JWT + Auth (T1.3-T1.4)
│   │   │   ├── session_service.py # Session management (T2.x)
│   │   │   └── jailbreak_service.py # Jailbreak detection (T3.x)
│   │   ├── api/
│   │   │   ├── auth.py            # Auth endpoints
│   │   │   ├── users.py           # User CRUD
│   │   │   ├── sessions.py        # Session endpoints
│   │   │   └── interviews.py      # Interview endpoints
│   │   └── schemas/                # Pydantic models
│   ├── tests/
│   │   ├── unit/                  # Unit tests (>80% coverage)
│   │   ├── integration/           # Integration tests
│   │   └── conftest.py
│   ├── migrations/                 # Alembic migrations
│   │   └── 001_initial_schema.sql # T1.1 schema
│   ├── Dockerfile
│   ├── requirements.txt
│   └── pytest.ini
│
├── frontend/                        # Next.js Application (Unit 5)
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   │   ├── auth/              # Login, Register
│   │   │   ├── session/           # Interview session UI
│   │   │   └── dashboard/         # Admin dashboard
│   │   ├── lib/                   # Utilities
│   │   └── styles/
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── e2e/                   # Playwright tests (T4.4)
│   ├── package.json
│   ├── next.config.js
│   └── Dockerfile
│
├── infra/                           # Terraform Infrastructure
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── modules/
│   │   ├── vpc/
│   │   ├── rds/
│   │   ├── ecs/
│   │   └── ...
│   └── terraform.tfvars
│
├── .github/
│   ├── workflows/
│   │   ├── lint.yml               # Code quality
│   │   ├── test.yml               # Unit/Integration tests
│   │   ├── security.yml           # Security scans
│   │   ├── deploy-staging.yml     # Staging deployment
│   │   └── deploy-prod.yml        # Production deployment
│   └── pull_request_template.md
│
├── docs/                            # Documentation
│   ├── DESIGN.md                  # Architecture & Design
│   ├── SCHEMA.md                  # Database schema (auto-generated)
│   ├── API.md                     # API specification (auto-generated)
│   ├── CHANGELOG.md               # Release notes
│   ├── tasks/
│   │   ├── task-package.yaml      # 20 tasks
│   │   └── linear-publish.yaml    # Linear mapping
│   └── memory/                    # ADRs, learnings, patterns
│
├── scripts/
│   ├── publish-tasks-to-linear.py
│   ├── validate-task-package.py
│   ├── check-task-dependencies.py
│   └── analyze-timeline.py
│
├── .env.example
├── .gitignore
├── .github/CODEOWNERS
├── CLAUDE.md                        # This file
└── README.md
```

---

## 🎯 Semana 1 Tasks (CURRENT)

### T1.1: Database Schema
**Assignee**: ENGINEER-1  
**Estimate**: 8h  
**Due**: 2026-05-28

Create PostgreSQL schema with:
- `users` table (id, email, password_hash, role, created_at, updated_at)
- `sessions` table (id, account_id, candidate_email, status, deleted_at)
- `audit_logs` table (id, user_id, action, resource, resource_id, changes)
- 3 indexes for performance
- Soft-delete support (LGPD compliance)

**File**: `backend/migrations/001_initial_schema.sql`

**Evidence Required**:
- Migration runs without errors
- Schema matches DESIGN.md
- docs/SCHEMA.md generated and committed

---

### T1.2: User Aggregate + Repository
**Assignee**: ENGINEER-1  
**Estimate**: 12h  
**Blockers**: T1.1  
**Due**: 2026-05-29

Implement User aggregate:
- User entity with validation
- Password hashing (bcrypt 12 rounds)
- UserRepository pattern (CRUD)
- Unit tests (>80% coverage)

**Files**:
- `backend/src/models/user.py`
- `backend/src/services/user_service.py`
- `backend/tests/unit/test_user_aggregate.py`

**Evidence Required**:
- 20+ tests passing
- 92%+ coverage
- Security: bcrypt 12 rounds verified

---

### T1.3: Authentication Service
**Assignee**: ENGINEER-1  
**Estimate**: 10h  
**Blockers**: T1.2  
**Due**: 2026-05-30

JWT RS256 implementation:
- Token generation (access + refresh)
- Token validation
- Refresh token rotation
- Integration tests

**Files**:
- `backend/src/services/auth_service.py`
- `backend/src/api/auth.py`
- `backend/tests/integration/test_auth.py`

---

### T1.4: RBAC
**Assignee**: ENGINEER-1  
**Estimate**: 8h  
**Blockers**: T1.2, T1.3  
**Due**: 2026-05-31

Role-Based Access Control:
- `@require_role` decorator
- 3 roles: admin, recruiter, candidate
- Authorization checks on all endpoints

**Files**:
- `backend/src/api/rbac.py`
- `backend/tests/unit/test_rbac.py`

---

### T1.5: Audit Logging Framework
**Assignee**: ENGINEER-1  
**Estimate**: 10h  
**Blockers**: T1.1  
**Due**: 2026-05-31

LGPD Compliance:
- AuditLog aggregate
- Middleware to capture all actions
- Soft-delete handler (hard-delete after 24h)
- PII masking in logs

**Files**:
- `backend/src/models/audit_log.py`
- `backend/src/middleware/audit_middleware.py`
- `backend/src/tasks/hard_delete_worker.py`

---

### T1.6: Docker Setup + CI/CD
**Assignee**: ENGINEER-2  
**Estimate**: 8h  
**Due**: 2026-05-31

Infrastructure:
- Dockerfile (backend + frontend)
- docker-compose.yml (dev environment)
- GitHub Actions workflows (6-stage CI/CD)
- Branch protection rules

**Files**:
- `backend/Dockerfile`
- `frontend/Dockerfile`
- `docker-compose.yml`
- `.github/workflows/lint.yml`
- `.github/workflows/test.yml`
- `.github/workflows/deploy-staging.yml`

---

## 🔨 Common Commands

### Backend Development
```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start FastAPI dev server
uvicorn src.main:app --reload

# Run tests
pytest --cov=src

# Run specific test
pytest tests/unit/test_user_aggregate.py -v

# Lint and format
black src/
pylint src/
mypy src/
```

### Frontend Development
```bash
cd frontend

# Install dependencies
npm install

# Start Next.js dev server
npm run dev

# Run tests
npm test

# Run E2E tests
npm run e2e

# Build for production
npm run build
```

### Docker
```bash
# Build all services
docker-compose build

# Start development environment
docker-compose up -d

# View logs
docker-compose logs -f backend

# Run migrations in container
docker-compose exec backend alembic upgrade head

# Stop services
docker-compose down
```

### Git & GitHub
```bash
# Feature branch
git checkout -b feature/unit1-user-aggregate

# Commit with evidence
git commit -m "feat(T1.2) User Aggregate + Repository

## Evidence
- Tests: 20/20 passing (92% coverage)
- Security: bcrypt 12 rounds verified
- Performance: <100ms per operation

Closes #42"

# Push and create PR
git push origin feature/unit1-user-aggregate
```

---

## ✅ Validation & Quality Gates

### Pre-Commit Checks
```bash
# Code quality
black --check .
pylint src/
mypy src/

# Tests must pass
pytest --cov=src --cov-fail-under=80

# No security issues
bandit -r src/
```

### PR Requirements
- ✅ All tests passing
- ✅ >80% code coverage
- ✅ Security scan clean
- ✅ Acceptance criteria met
- ✅ Architecture review approved
- ✅ Evidence documented in PR

### Acceptance Criteria for Each Task
See `Estación 6/docs/tasks/` for detailed task files with:
- Definition of Ready
- Acceptance Criteria
- Test Plan
- Deliverables

---

## 📚 Key Documentation

| Document | Purpose | Location |
|----------|---------|----------|
| DESIGN.md | Architecture & Design Decisions | docs/ |
| SCHEMA.md | Database Schema | docs/ (auto-generated) |
| API.md | API Specification | docs/ (auto-generated) |
| CHANGELOG.md | Release Notes | docs/ |
| ADRs | Architecture Decisions | memory/decisions/ |
| Learnings | Captured Insights | memory/learnings/ |
| Patterns | Code Patterns | memory/patterns/ |

---

## 🔐 Secrets Management

**NEVER commit**:
- `.env` (local secrets)
- API keys, tokens
- Database credentials
- Private keys

**Always use**:
- `.env.example` (placeholders only)
- GitHub Secrets (for CI/CD)
- AWS Secrets Manager (for production)

---

## 🚀 Starting Semana 1

1. **Setup local environment** (see Development Setup above)
2. **Read Task Files** in `Estación 6/docs/tasks/`
3. **Implement T1.1**: Database Schema
4. **Create PR** with evidence
5. **Code Review** (ARCHITECT)
6. **Merge** and proceed to T1.2

Estimated completion: Friday 2026-05-31

---

## 📞 Support

- **Questions about tasks**: See task files in `Estación 6/docs/tasks/`
- **Architecture help**: See `Estación 6/DESIGN.md`
- **Testing help**: See `Estación 6/VALIDATION-FRAMEWORK.md`
- **Process questions**: See `Estación 6/ORCHESTRATION-PLAN.md`

---

**Status**: Semana 1 Ready  
**Last Updated**: 2026-05-27  
**Agent**: Claude Code (Haiku 4.5)
