# Construction Phase Handoff — TicketDesk Enterprise v1.0

**Documento de Traspaso: Inception → Construction**  
**Fecha**: 2026-05-27  
**Estado**: ✅ LISTO PARA CONSTRUCCIÓN

---

## 🎯 OBJETIVO

Este documento guía al equipo de construcción (4-6 developers) en cómo usar los artefactos de diseño generados para construir TicketDesk Enterprise de forma ordenada y paralela.

---

## 📋 ARTEFACTOS DISPONIBLES

Todos los documentos están en `aidlc-docs/`:

### Requisitos & Planificación
- `inception/requirements/requirements.md` — Especificación técnica completa
- `inception/plans/execution-plan.md` — Timeline, Units, critical path
- `inception/plans/application-design-plan.md` — Decisiones de diseño

### Diseño de Aplicación
- `inception/application-design/components.md` — 6 backend + 4 frontend components
- `inception/application-design/component-methods.md` — 50+ method signatures
- `inception/application-design/services.md` — 5 services, orchestration patterns
- `inception/application-design/component-dependency.md` — Matriz de dependencias
- `inception/application-design/application-design.md` — Consolidación

### Diseño Detallado
- `inception/design/functional-design.md` — Flujos de negocio, edge cases
- `inception/design/nfr-design.md` — Seguridad, performance, escalabilidad
- `inception/design/infrastructure-design.md` — AWS, CI/CD, networking

### Planes de Trabajo
- `inception/plans/units-generation.md` — 68 work items con aceptación criteria

---

## 🚀 CÓMO COMENZAR

### Paso 1: Clonar Repositorio

```bash
# Asumiendo que el repo fue inicializado
git clone <ticketdesk-repo-url>
cd ticketdesk
git checkout -b unit-1-infrastructure
```

### Paso 2: Setup Local Development

```bash
# Install Docker
docker --version

# Clone + setup
git clone <repo>
cd ticketdesk
docker-compose up -d

# Verify stack is running
curl http://localhost:8000/health     # FastAPI
curl http://localhost:3000/api/health # Next.js
curl http://localhost:5432            # PostgreSQL
```

### Paso 3: Revisar Documentación

**TODOS deben leer:**
1. `README.md` (clonar desde repo)
2. `aidlc-docs/inception/application-design/application-design.md` (10 min read)
3. `aidlc-docs/inception/plans/execution-plan.md` (5 min read)

**Por rol:**
- **Backend Eng**: `functional-design.md` + `component-methods.md`
- **Frontend Eng**: `components.md` (CandidateInterface, RecruiterDashboard sections)
- **DevOps/Infra**: `infrastructure-design.md` + `nfr-design.md` (Infrastructure section)

### Paso 4: Asignar Teams a Units

```
Team A (2 DevOps + 1 Backend):  Unit 1 (Infraestructura) — Semanas 1-2
Team B (2 Backend):             Unit 2 (Backend Fundamentals) — Semanas 2-4
Team C (1 Backend):             Unit 3 (BotEngine) — Semanas 3-5 [Paralelo]
Team D (1 Backend):             Unit 4 (EvaluationEngine) — Semanas 3-5 [Paralelo]
Team E (2 Frontend):            Unit 5 (Frontend) — Semanas 3-5 [Paralelo]
Team F (2 Backend):             Unit 6 (Compliance + HITL) — Semanas 4-5 [Paralelo]
```

---

## 📊 UNITS BREAKDOWN

### Unit 1: Infraestructura (Semanas 1-2)
**Responsable**: 1 DevOps Engineer  
**Bloquea**: TODO el resto

**10 Work Items**:
1. AWS VPC + Security Groups
2. PostgreSQL RDS setup
3. Redis ElastiCache setup
4. S3 buckets
5. Docker + ECR
6. ECS cluster + task definitions
7. GitHub Actions CI/CD pipeline
8. CloudWatch monitoring + alarms
9. Route53 DNS + TLS certificates
10. Local development environment

**Aceptación**: `docker-compose up` levanta stack completo, CI/CD pipeline executa en PR

**Documentación**: `infrastructure-design.md`

---

### Unit 2: Backend Fundamentals (Semanas 2-4) [CRITICAL]
**Responsables**: 2 Backend Engineers  
**Bloqueado por**: Unit 1  
**Bloquea**: Unit 3, 4

**10 Work Items**:
1. FastAPI project structure
2. SQLAlchemy models (9 tablas)
3. Repository layer (CRUD)
4. Middleware (auth, error handling, CORS)
5. Database + Redis connections
6. Event system (Pub/Sub + Celery)
7. Testing infrastructure (pytest)
8. API documentation (OpenAPI)
9. Dependency injection
10. Constants & enums

**Aceptación**: `pytest` corre, >80% coverage, `alembic upgrade` crea BD

**Documentación**: `functional-design.md` (Unit 2 section) + `component-methods.md`

---

### Unit 3: BotEngine (Semanas 3-5)
**Responsable**: 1 Backend Engineer  
**Bloqueado por**: Unit 1, Unit 2  
**Paralelo con**: Unit 4, Unit 5

**10 Work Items**:
1. BotEngine core service
2. Claude API integration
3. Jailbreak detection
4. Out-of-scope detection
5. Session state management (Redis)
6. Transcription management (S3)
7. Question management (branching logic)
8. API endpoints
9. Unit tests
10. Documentation

**Aceptación**: `POST /api/screening/start` funciona, respuestas evaluadas

**Documentación**: `functional-design.md` (Unit 3 section)

---

### Unit 4: EvaluationEngine (Semanas 3-5)
**Responsable**: 1 Backend Engineer  
**Paralelo con**: Unit 3, Unit 5

**10 Work Items**:
1. EvaluationEngine core service
2. Rubric loading & caching
3. Scoring engine (Claude API)
4. Citation extraction (fuzzy matching)
5. Fairness validation
6. Final score calculation
7. Recommendation generation
8. Event handler
9. API endpoints
10. Unit tests

**Aceptación**: Evaluaciones calculadas correctamente, citas extraídas con confidence

**Documentación**: `functional-design.md` (Unit 4 section)

---

### Unit 5: Frontend + Integration (Semanas 3-5)
**Responsables**: 2 Frontend Engineers  
**Paralelo con**: Unit 3, Unit 4

**14 Work Items**:
1. Next.js setup
2. State management (Zustand)
3. HTTP client (React Query + Axios)
4. CandidateInterface (Chat UI)
5. Consent form
6. Session management
7. RecruiterDashboard (Queue)
8. Candidate detail panel
9. Real-time updates (polling)
10. CampaignManager (CRUD)
11. Authentication & routing
12. Styling (Tailwind)
13. Error handling & loading states
14. Integration tests

**Aceptación**: Chat screening completa funciona, queue muestra evaluaciones

**Documentación**: `functional-design.md` (Unit 5 section) + `components.md` (frontend section)

---

### Unit 6: Compliance + HITL + Re-engagement (Semanas 4-5) [CRITICAL]
**Responsables**: 2 Backend Engineers  
**Bloqueado por**: Unit 2, Unit 3 (eventos)

**14 Work Items**:
1. ComplianceService (auditoría append-only)
2. Consent management
3. Data retention & soft delete
4. LGPD right to forget
5. Compliance reporting (PDF)
6. ReEngagementService (inactivity detection)
7. Email scheduling (24h/48h)
8. Email templates
9. HITLService (queue management)
10. Decision recording
11. Candidate notifications
12. API endpoints (compliance, queue, decision)
13. Integration tests (full workflow)
14. Documentation

**Aceptación**: Full screening → evaluación → HITL → decision → email workflow funciona

**Documentación**: `functional-design.md` (Unit 6 section)

---

## ⚠️ CRITICAL PATH & DEPENDENCIAS

```
Week 1-2:
  └─ Unit 1 MUST complete (blocks everything)

Week 2-4:
  └─ Unit 2 MUST complete (blocks Units 3,4,5,6)

Week 3-5:
  ├─ Unit 3, Unit 4, Unit 5 PARALLEL (independent)
  └─ All should ~complete by week 5

Week 4-5:
  └─ Unit 6 (depends on Unit 2 + Unit 3 events)
```

**Red Flags** (escalate immediately):
- Unit 1 no completada en semana 2 ⚠️
- Unit 2 no completada en semana 4 ⚠️
- Unit 3 o 4 events no emitiendo ⚠️
- Unit 6 evento handler failing ⚠️

---

## 🔧 DEVELOPMENT STANDARDS

### Code Style
- Python: `black` formatter, `pylint` linter
- TypeScript: `ESLint`, `prettier`
- Pre-commit hooks configured (linting on commit)

### Testing Requirements
- Python: pytest, >80% coverage, integration tests for critical paths
- TypeScript: Jest, >80% coverage, integration tests

### Git Workflow
```bash
# Create feature branch per unit
git checkout -b unit-3-botengine

# Commit frequently (small, atomic commits)
git commit -m "BotEngine: implement jailbreak detection"

# Push and create PR
git push origin unit-3-botengine
# → GitHub Actions runs tests, linting, build

# After approval: merge to main
# → Automatic deployment to staging
# → Manual approval for production
```

### PR Review Checklist
- [ ] Code compiles/tests pass
- [ ] No security vulnerabilities (SQL injection, XSS, etc.)
- [ ] Follows design (component methods, service contracts)
- [ ] >80% test coverage
- [ ] Documentation updated

---

## 📚 REFERENCE QUICK LINKS

**Architecture Diagrams**:
- Component dependency matrix → `component-dependency.md`
- Data flow diagrams → `functional-design.md`
- Infrastructure → `infrastructure-design.md`

**API Contract**:
- All endpoint signatures → `component-methods.md`
- Request/response types → `component-methods.md`
- Error codes → `nfr-design.md` (error handling section)

**Security**:
- JWT implementation → `nfr-design.md` (section 1.1)
- LGPD compliance → `nfr-design.md` (section 1.4)
- Data encryption → `infrastructure-design.md`

**Performance**:
- Latency SLAs → `nfr-design.md` (section 2.1)
- Caching strategy → `nfr-design.md` (section 2.1)
- Database optimization → `nfr-design.md` (section 2.1)

**Scaling & Reliability**:
- Auto-scaling policy → `infrastructure-design.md`
- High availability setup → `nfr-design.md` (section 4.2)
- Disaster recovery → `nfr-design.md` (section 4.1)

---

## 📞 ESCALATION & SUPPORT

### Questions About Design?
- Check the relevant section in `functional-design.md`
- If still unclear: consult `component-methods.md` for exact signatures
- Escalate to tech lead if contradictions found

### CI/CD Pipeline Issues?
- Check `.github/workflows/` files
- Consult `infrastructure-design.md` section 5
- Contact DevOps lead

### Database/Infrastructure Questions?
- Check `infrastructure-design.md`
- Consult ERD diagram (in `functional-design.md` section 2.1)
- Contact DevOps/Infra lead

### Design Conflicts?
- Document in issue/PR
- Reference which design doc conflicts with which
- Tech lead decides resolution (may require design amendment)

---

## ✅ CONSTRUCTION CHECKLIST

**Week 0 (Planning)**:
- [ ] Teams assigned to Units
- [ ] Development environment setup locally
- [ ] All docs reviewed by respective teams
- [ ] GitHub repo + branches created
- [ ] CI/CD pipeline verified

**Week 1-2 (Unit 1)**:
- [ ] AWS infrastructure provisioned
- [ ] RDS + Redis operational
- [ ] S3 buckets created
- [ ] ECS cluster ready
- [ ] CI/CD pipeline functional

**Week 2-4 (Unit 2)**:
- [ ] FastAPI skeleton built
- [ ] SQLAlchemy models created
- [ ] Repositories implemented
- [ ] Middleware configured
- [ ] Event system working
- [ ] Testing infrastructure ready

**Week 3-5 (Units 3,4,5)**:
- [ ] BotEngine integrated with Claude API
- [ ] EvaluationEngine scoring functional
- [ ] Frontend chat UI responsive
- [ ] API integration tests passing

**Week 4-5 (Unit 6)**:
- [ ] Compliance service auditing
- [ ] HITL queue operational
- [ ] Re-engagement emails sending
- [ ] Full workflow E2E tested

**Week 5 (Validation)**:
- [ ] All units integrated
- [ ] Full screening flow works (candidate → bot → eval → HITL → decision)
- [ ] >80% test coverage across codebase
- [ ] Performance targets met (p99 latency <2s)
- [ ] MVP ready for QA/UAT

---

## 🎓 LEARNING RESOURCES

**For Backend Engineers**:
- FastAPI docs: https://fastapi.tiangolo.com/
- SQLAlchemy docs: https://docs.sqlalchemy.org/
- Celery docs: https://docs.celeryproject.io/
- Pydantic docs: https://docs.pydantic.dev/

**For Frontend Engineers**:
- Next.js 14 docs: https://nextjs.org/docs
- React Query docs: https://tanstack.com/query/latest
- Zustand docs: https://github.com/pmndrs/zustand
- Tailwind docs: https://tailwindcss.com/docs

**For DevOps/Infra**:
- AWS ECS: https://docs.aws.amazon.com/ecs/
- CloudFormation: https://docs.aws.amazon.com/cloudformation/
- Terraform: https://www.terraform.io/docs
- GitHub Actions: https://docs.github.com/en/actions

---

## 🎉 FINAL NOTES

- **Estimated MVP Completion**: 10 weeks from start (2026-07-29)
- **Parallel Execution**: Units 3, 4, 5 are independent, can be built simultaneously
- **Communication**: Daily standups (15 min), blockers surfaced immediately
- **Quality**: No shortcuts on testing, security, performance
- **Go-live**: After QA/UAT + stakeholder approval (v1.0)

**You have everything needed to build this product. Good luck! 🚀**

---

**Generated**: 2026-05-27  
**Phase**: Inception → Construction Handoff  
**Status**: ✅ READY TO BUILD

