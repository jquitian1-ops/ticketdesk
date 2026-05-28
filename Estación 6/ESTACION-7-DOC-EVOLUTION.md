# 📚 Propuesta de Documentación Evolutiva — Estación 7

**Proyecto**: TicketDesk Enterprise v1.0  
**Propósito**: Mantener documentación sincronizada con código mientras evoluciona  
**Fecha**: 2026-05-27  
**Status**: Plan de implementación

---

## Resumen Ejecutivo

**Documentación Evolutiva** es un sistema donde la documentación se actualiza automáticamente o se valida mientras el código cambia, evitando docs desincronizadas.

```
PROBLEMA ACTUAL:
  • PRODUCT.md y DESIGN.md son estáticas
  • Código cambia, docs no se actualizan
  • 2-3 meses después, docs están obsoletos
  • Nuevo team member lee docs antiguos → confusión

SOLUCIÓN:
  • Docs en 3 capas (stable, mutable, live)
  • Validación automática de docs vs código
  • Changelog que conecta docs con PRs/commits
  • Memoria que captura cambios en contexto
```

---

## 1️⃣ Capas de Documentación

### Capa 1: STABLE (No cambia frecuentemente)

```
Docs que cambian raramente:
- PRODUCT.md (vision, market, user personas)
- DESIGN.md (core principles, architecture decisions)
- ADRs (architecture decisions, immutable once accepted)

Update frequency: Semestral o cuando pivota el producto
Ownership: Product, ARCHITECT
Validation: Manual review
```

### Capa 2: MUTABLE (Cambia cada 1-2 semanas)

```
Docs que cambian con feature trabajo:
- API.md (endpoint documentation)
- SCHEMA.md (database schema)
- PATTERNS.md (common patterns)
- DEPLOYMENT.md (deployment procedures)

Update frequency: Con cada sprint
Ownership: ENGINEER (auto-update donde sea posible)
Validation: Automated linting + manual review
```

### Capa 3: LIVE (Actualiza en tiempo real)

```
Docs que reflejan estado actual:
- CHANGELOG.md (qué cambió y cuándo)
- memory/ (learnings, decisions, incidents)
- GLOSSARY.md (términos del proyecto)
- Test results (coverage, performance metrics)

Update frequency: Con cada PR/commit
Ownership: Automated (scripts + CI/CD)
Validation: Automated only (script verifies format)
```

---

## 2️⃣ Documentos Específicos a Evolucionar

### API.md (Capa MUTABLE)

**Current state**: No existe  
**Needed by**: Semana 1 onwards (cuando T1.3 complete)  
**Update strategy**: Auto-generate from OpenAPI spec + manual sections

```markdown
# API Reference — TicketDesk Enterprise

**Generated from**: backend/openapi.yaml  
**Last updated**: 2026-06-07  
**Version**: v0.2.0

## Authentication

POST /auth/login
POST /auth/refresh
POST /auth/logout

## Sessions

GET /api/sessions
POST /api/sessions
GET /api/sessions/:id
PUT /api/sessions/:id
DELETE /api/sessions/:id

...

**Manual sections**:
- Rate limiting (100 req/min per user)
- Error codes (400, 401, 403, 500)
- Examples and common patterns
```

**Generation script**:

```bash
# Generate API.md from FastAPI docstrings
fastapi-openapi-to-markdown backend/app/main.py > docs/API.md

# Validate: check that all endpoints documented
python scripts/validate_api_docs.py
```

### SCHEMA.md (Capa MUTABLE)

**Current state**: Schema en migrations/  
**Needed by**: Semana 1 onwards  
**Update strategy**: Auto-extract from SQLAlchemy models

```markdown
# Database Schema — TicketDesk Enterprise

**Last updated**: 2026-05-31 (auto-generated)

## users table

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PRIMARY KEY | auto-generated |
| email | VARCHAR(255) | UNIQUE, NOT NULL | hashed with SHA-256 |
| password_hash | VARCHAR(255) | NOT NULL | bcrypt, 12 rounds |
| role | VARCHAR(50) | NOT NULL | CHECK IN ('admin', 'recruiter', 'candidate') |
| created_at | TIMESTAMP | DEFAULT NOW() | UTC |
| updated_at | TIMESTAMP | DEFAULT NOW() | auto-update on change |

## sessions table

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PRIMARY KEY | |
| account_id | UUID | FOREIGN KEY users(id) | session owner |
| candidate_email | VARCHAR(255) | NOT NULL | PII, masked in logs |
| status | VARCHAR(50) | CHECK IN (...) | state machine |
| deleted_at | TIMESTAMP | | soft-delete (LGPD) |
...
```

**Generation script**:

```python
# scripts/generate_schema_docs.py
"""Generate SCHEMA.md from SQLAlchemy models"""

import sqlalchemy as sa
from app.models import User, Session, AuditLog

def model_to_markdown(model):
    """Convert SQLAlchemy model to markdown table"""
    table = model.__table__
    rows = []
    for col in table.columns:
        rows.append(f"| {col.name} | {col.type} | ... | {col.doc} |")
    return "\n".join(rows)

def generate_schema_docs():
    with open("docs/SCHEMA.md", "w") as f:
        f.write("# Database Schema\n\n")
        f.write("**Last updated**: " + datetime.now().isoformat() + "\n\n")
        
        for model in [User, Session, AuditLog]:
            f.write(f"## {model.__tablename__}\n\n")
            f.write(model_to_markdown(model))
            f.write("\n\n")
```

### PATTERNS.md (Capa MUTABLE)

**Current state**: Patrones en código + memory/  
**Needed by**: Semana 2 onwards  
**Update strategy**: Manual (con referencia a code examples)

```markdown
# Patterns — TicketDesk Enterprise

**Last updated**: 2026-06-16

## Aggregate Pattern

**Definition**: Entity with invariants and bounded context  
**Example**: Session aggregate (Unit 2)

```python
class Session(Base):
    # From: backend/app/sessions/models.py:42-105
    id: UUID
    account_id: UUID
    status: str  # state machine
    
    def add_message(...) -> Message:
        """Invariant: status must be 'screening'"""
        if self.status != "screening":
            raise InvalidStateError(...)
```

**When to use**: Modeling entities with complex logic  
**When not to**: Simple CRUD records  
**Lesson**: See L001-aggregate-pattern in memory/

## Repository Pattern

**Definition**: Abstraction over data persistence  
**Example**: SessionRepository

```python
# From: backend/app/sessions/repository.py:1-40
class SessionRepository:
    async def create(session: Session) -> Session: ...
    async def get_by_id(id: UUID) -> Session: ...
    async def list_by_account(...): ...
```

---

## 3️⃣ CHANGELOG Evolution

**Current state**: No existe  
**Needed by**: Semana 1, updated weekly  
**Update strategy**: Auto-generate from git commits + manual sections

```markdown
# Changelog — TicketDesk Enterprise

**Format**: Semantic Versioning (MAJOR.MINOR.PATCH)

## [v1.0.0] - 2026-06-23

**Release date**: Friday, June 23, 2026  
**Status**: Production Ready 🚀  

### Added
- Unit 5: Frontend (Next.js 14, React components)
- E2E testing suite (25+ Playwright scenarios)
- Production deployment (Terraform, CloudWatch, on-call)
- Core Web Vitals optimization (LCP ≤2.5s)
- WCAG 2.2 AAA accessibility

### Changed
- API error responses (more consistent)
- Token expiry logic (improved DX)
- Database query performance (10% improvement)

### Fixed
- Token refresh bug (T4.4)
- Accessibility violation in forms (T4.3)
- Performance regression in evaluations (T3.4)

### Security
- JWT token rotation implemented
- API rate limiting enforced
- OWASP Top 10 validation complete

### LGPD Compliance
- Hard delete SLA: <24h verified
- Audit trail: 100% event capture
- PII masking: in logs and backups

### Links
- GitHub Release: github.com/org/repo/releases/tag/v1.0.0
- Documentation: https://docs.ticketdesk.app/v1.0.0
- Deployment notes: docs/deployment/RELEASE-NOTES-v1.0.0.md

---

## [v0.3.0] - 2026-06-16

### Added
- Unit 3: BotEngine (Claude API integration)
- Unit 4: Evaluation (scoring engine)
- Jailbreak detection (>95% accuracy)
- Streaming responses (SSE)

...

---

## [v0.1.0] - 2026-05-31

### Added
- Unit 1: Account Management (auth, RBAC)
- Unit 6: Compliance (audit logging)
- Database schema with migrations
- CI/CD pipeline (6 stages)
- Docker setup (local development)

---

## Unreleased (main branch)

### In Progress
- Feature X (PR #123)
- Feature Y (PR #124)

### Planned
- Feature Z (scheduled for v1.1.0)
```

**Generation script**:

```bash
# Auto-generate CHANGELOG from git commits
git log --oneline --all > commits.txt
# Parse commits and group by semantic type (feat, fix, etc.)
# Generate markdown sections

# Manual sections (Added, Changed, Fixed, Security) edited by ORCHESTRATOR
```

---

## 4️⃣ Validación Automática de Docs

### Doctest (Validar ejemplos en docs)

```python
# docs/API.md contiene ejemplos executable

"""
Example: Create a session

>>> from app.sessions.service import SessionService
>>> service = SessionService()
>>> session = await service.create_session(account_id="123", email="candidate@example.com")
>>> assert session.status == "pending"
>>> print(f"Created: {session.id}")
Created: 550e8400-e29b-41d4-a716-446655440000
"""

# Validación:
# python -m doctest docs/API.md
```

### Lint docs (Validar formato)

```yaml
# .github/workflows/docs.yml

jobs:
  lint-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Markdown lint
        run: |
          npm install -D markdownlint-cli
          npx markdownlint "docs/**/*.md" --config .markdownlintrc
      
      - name: Link checker
        run: |
          npm install -D markdown-link-check
          find docs -name "*.md" -exec markdown-link-check {} \;
      
      - name: Validate API spec
        run: python scripts/validate_api_docs.py
      
      - name: Validate schema
        run: python scripts/validate_schema_docs.py
      
      - name: Sync check
        run: python scripts/check_docs_sync.py
          # Verifica que docs mencionen código actual
```

### Sincronización de docs y código

```python
# scripts/check_docs_sync.py
"""Verify docs match code reality"""

def check_api_endpoints():
    """Verify API.md lists all endpoints"""
    from app.main import app
    from markdown import parse_api_examples
    
    # Get endpoints from FastAPI
    endpoints = [route.path for route in app.routes]
    
    # Get endpoints from API.md
    documented_endpoints = parse_api_examples("docs/API.md")
    
    # Compare
    missing = set(endpoints) - set(documented_endpoints)
    if missing:
        print(f"❌ Undocumented endpoints: {missing}")
        return False
    
    extra = set(documented_endpoints) - set(endpoints)
    if extra:
        print(f"⚠️ Removed endpoints still documented: {extra}")
    
    return True

def check_schema_matches():
    """Verify SCHEMA.md matches models"""
    from app.models import Base
    from markdown import parse_schema_tables
    
    # Get columns from models
    actual_columns = {}
    for table in Base.metadata.tables.values():
        actual_columns[table.name] = [col.name for col in table.columns]
    
    # Get columns from SCHEMA.md
    documented_columns = parse_schema_tables("docs/SCHEMA.md")
    
    # Compare
    for table_name, cols in actual_columns.items():
        if table_name not in documented_columns:
            print(f"❌ Undocumented table: {table_name}")
            return False
        if set(cols) != set(documented_columns[table_name]):
            print(f"❌ Schema mismatch in {table_name}")
            return False
    
    return True

if __name__ == "__main__":
    assert check_api_endpoints(), "API docs out of sync"
    assert check_schema_matches(), "Schema docs out of sync"
    print("✅ All docs synchronized")
```

---

## 5️⃣ Propuesta: Documentación por Sprint

Después de cada sprint, crear:

```
docs/releases/RELEASE-v0.X.0.md

Contenido:
- Qué se implementó (lista de tareas)
- ADRs nuevos
- Learnings capturados
- Breaking changes (si hay)
- Migration guide (si necesario)
- New patterns documented
- Updated examples in API.md, SCHEMA.md, PATTERNS.md
```

**Ejemplo (v0.2.0 - después de semana 2)**:

```markdown
# Release Notes — v0.2.0 (Unit 2)

**Release date**: June 7, 2026  
**Focus**: Session Management

## What's New

### Unit 2: Session Management
- Session aggregate with state machine
- SessionRepository with CRUD operations
- 5 REST API endpoints
- 48+ tests (92% coverage)

### New ADRs
- ADR-003: Soft-delete strategy for LGPD compliance

### New Learnings
- L002: Soft-delete edge cases (see memory/learnings/L002-soft-delete-edge-cases.md)

### Documentation Updates
- API.md: Added Sessions endpoints section
- SCHEMA.md: Added sessions table documentation
- PATTERNS.md: Added Repository pattern example

### Breaking Changes
None

### Migration Guide
No database migrations needed (first release with sessions)

### Examples
```python
# Create a session
POST /api/sessions
{
  "candidate_email": "candidate@example.com"
}

# Response
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "created_at": "2026-06-07T14:30:00Z"
}
```

### Next (v0.3.0)
- Unit 3: BotEngine (Claude API)
- Unit 4: Evaluation (scoring)
```

---

## ✅ Checklist: Documentación Evolutiva

```
ANTES DE SPRINT 1:
☐ API.md template created (generará en T1.3)
☐ SCHEMA.md template created (generará en T1.1)
☐ PATTERNS.md template created
☐ CHANGELOG.md created (empty)
☐ Scripts de auto-generation preparados
☐ Doctest setup en CI/CD
☐ Markdown lint en CI/CD
☐ Sync checker (docs vs código) en CI/CD

POR CADA SPRINT:
☐ Docs auto-generados después de código
☐ Manual sections (patterns, examples) actualizados
☐ CHANGELOG.md actualizado
☐ memory/ learnings capturados
☐ Release notes creadas
☐ Docs validadas contra código

SEMANA 4 (PRODUCCIÓN):
☐ API.md completo y validado
☐ SCHEMA.md completo y validado
☐ PATTERNS.md con >10 patrones documentados
☐ CHANGELOG.md comprensivo (v0.1.0 → v1.0.0)
☐ memory/ con >20 learnings
☐ Link checker: 0 broken links
☐ Doctest: 100% pass
```

---

## Beneficios de Documentación Evolutiva

| Beneficio | Sin Doc Evo | Con Doc Evo |
|-----------|-----------|-----------|
| Docs accuracy | 60-70% | >95% |
| Onboarding time | 2-3 weeks | 3-4 days |
| Bug due to misunderstanding | 15-20% | <5% |
| "Outdated docs" complaints | Frequent | Rare |
| Team confidence | Low | High |

---

**Status**: ✅ **READY FOR IMPLEMENTATION**

**Next step**: Implement docs generation scripts at sprint start (Semana 1)
