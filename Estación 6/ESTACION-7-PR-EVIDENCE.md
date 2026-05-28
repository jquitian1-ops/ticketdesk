# 📋 PR con Evidence — Estación 7

**Proyecto**: TicketDesk Enterprise v1.0  
**Propósito**: Plantilla de PR que demuestre completitud, calidad y trazabilidad de tarea  
**Fecha**: 2026-05-27  
**Status**: Plantilla lista para usar

---

## Resumen Ejecutivo

Cada PR debe presentar **evidence** clara que la tarea está completa y validada:
- ✅ Task requirements met
- ✅ Tests passing (coverage, security, performance)
- ✅ Code review ready
- ✅ Commits trazables
- ✅ Documentación actualizada

```
PR TEMPLATE:

Title:      feat(T1.2) User Aggregate + Repository
Branch:     feature/unit1-user-aggregate
Task:       T1.2
Evidence:   Tests ✅ | Coverage 92% ✅ | Security clean ✅ | Docs ✅

This PR is ready for merge when:
  ☐ All checks pass (CI/CD)
  ☐ Code review approved (1x ARCHITECT)
  ☐ No conflicts
  ☐ All conversations resolved
```

---

## 1️⃣ PR Template (.github/pull_request_template.md)

```markdown
# [Task ID] Brief Description

## Task Information

**Task ID**: T1.2  
**Title**: User Aggregate + Repository (Unit 1)  
**Milestone**: M1 (Auth & Compliance)  
**Assignee**: ENGINEER-1  
**Related Issue**: #42 (link to GitHub issue)  

---

## Summary

What does this PR do? (1-2 sentences)

Implements User aggregate and UserRepository following DDD patterns. 
Provides CRUD operations and validation for user management (Unit 1).

---

## Scope

**In Scope**:
- User aggregate class with validation
- UserRepository with CRUD operations
- Password hashing (bcrypt, 12 rounds)
- 20+ unit + integration tests
- Database migrations (alembic)

**Out of Scope**:
- API endpoints (T1.3)
- Email verification (future work)
- User roles/permissions (T1.4)

---

## Changes Made

### Files Changed
- `backend/app/users/models.py` — User aggregate (+85 lines)
- `backend/app/users/repository.py` — UserRepository (+120 lines)
- `backend/migrations/002_user_aggregate.py` — Alembic migration (+40 lines)
- `tests/unit/test_user_model.py` — Unit tests (+150 lines)
- `tests/integration/test_user_repository.py` — Integration tests (+100 lines)

### Key Changes

#### User Aggregate (models.py)
```python
class User(Base):
    """User aggregate with validation and password hashing"""
    id: UUID = Field(primary_key=True, default_factory=uuid4)
    email: str = Field(unique=True, index=True)
    password_hash: str
    role: str = Field(default="candidate")
    created_at: datetime = Field(default_factory=utcnow)
    
    def set_password(self, password: str) -> None:
        """Hash password with bcrypt (12 rounds)"""
        self.password_hash = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt(rounds=12)
        ).decode('utf-8')
    
    def validate_email(self) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, self.email))
```

#### UserRepository (repository.py)
```python
class UserRepository:
    """Repository pattern for User persistence"""
    
    async def create(self, user: User) -> User:
        """Create and persist user"""
        self.session.add(user)
        self.session.commit()
        return user
    
    async def get_by_email(self, email: str) -> User | None:
        """Retrieve user by email (indexed query)"""
        return self.session.query(User)\
            .filter(User.email == email)\
            .first()
```

---

## Evidence of Completion

### ✅ Tests

**Test Results**:
- Unit tests: 15/15 ✅ PASS
- Integration tests: 5/5 ✅ PASS
- Total: 20 tests passing
- Coverage: 92% (target: >80%) ✅

**Test Command**:
```bash
pytest tests/unit/test_user_model.py -v
pytest tests/integration/test_user_repository.py -v
pytest --cov=app --cov-report=html
```

**Test Artifacts**:
- [Coverage report](https://codecov.io/org/repo/pull/123)
- [Test results log](https://github.com/org/repo/actions/runs/12345)

### ✅ Code Quality

**Linting Results**:
- black formatting: ✅ PASS (0 issues)
- pylint score: 8.2/10 ✅ (target: >8.0)
- mypy type checking: 0 errors ✅
- isort imports: ✅ PASS

**Commands**:
```bash
black --check backend/
pylint backend/app/users/
mypy backend/app/users/ --strict
isort backend/app/users/
```

### ✅ Security

**Security Scans**:
- bandit (SAST): 0 issues ✅
- Password hashing: bcrypt 12 rounds ✅ (verified)
- No hardcoded secrets ✅
- SQL injection protection: parameterized queries ✅

**Manual Verification**:
- Password hash not in logs ✅ (checked)
- Email validation prevents injection ✅ (tested)
- RBAC logic correct ✅ (reviewed against DESIGN.md)

**Bandit Output**:
```
bandit -r backend/app/users/ -f json > bandit-report.json

Result: No issues found
```

### ✅ Performance

**Database Queries**:
- Email lookup index: ✅ Created (email_idx)
- Query latency: <10ms (verified locally)
- N+1 queries: 0 detected ✅

**Metrics**:
- User.create(): <100ms ✅
- User.get_by_email(): <10ms (indexed) ✅

---

## Acceptance Criteria Met

- [x] User aggregate implemented with validation
- [x] UserRepository with CRUD operations
- [x] Password hashing (bcrypt, 12 rounds)
- [x] 20+ tests with >90% coverage
- [x] No security vulnerabilities
- [x] Code follows PEP 8 + type hints
- [x] Matches DESIGN.md Unit 1 requirements
- [x] Database migration working
- [x] Integration tests with real DB

---

## Related Documentation

- **Task**: docs/tasks/002-T1.2-user-aggregate.md
- **ADR**: decisions/ADR-002-password-hashing.md (bcrypt 12 rounds)
- **Pattern**: patterns/P001-aggregate-pattern.md
- **API**: Not yet (T1.3)

---

## Dependencies & Blocking

**Blocked by**:
- T1.1 (Database Schema) — ✅ Merged (no blocker)

**Blocks**:
- T1.3 (Authentication Service) — Waits on this
- T1.4 (RBAC) — Uses User model from this

---

## Deployment Impact

**Breaking Changes**: None

**Database Migrations**:
- Migration 002 creates users table
- Idempotent (safe to run multiple times)
- Rollback available via `alembic downgrade`

**Backwards Compatibility**: N/A (first release)

---

## Testing Performed

### Manual Testing
- [x] Created user with valid email
- [x] Created user with invalid email → rejected
- [x] Password hashing verified (bcrypt format)
- [x] get_by_email() returns correct user
- [x] Duplicate email rejected (unique constraint)

### Automated Testing
- [x] Unit tests: all green
- [x] Integration tests: all green
- [x] CI/CD pipeline: all checks pass

### Edge Cases
- [x] Empty password → validation error
- [x] Very long email → handled correctly
- [x] Special characters in email → validated
- [x] Concurrent user creation → handled (DB unique constraint)

---

## Checklist

- [x] Code follows project style guide (PEP 8, type hints)
- [x] All tests passing (local + CI)
- [x] Coverage threshold met (>80%)
- [x] No security issues (bandit, manual review)
- [x] No hardcoded secrets
- [x] Database migration tested
- [x] Related docs updated (or created tasks for updates)
- [x] Commits are atomic and well-described
- [x] No conflicts with main branch
- [x] Ready for code review

---

## Links & References

- **Milestone**: M1 — Auth & Compliance (due May 31)
- **Sprint**: Sprint 1 (Week 1)
- **GitHub Issue**: #42
- **Board**: [Linear issue](https://linear.app/org/issue/TICK-42)
- **Slack**: [Thread discussion](https://slack.com/archives/C123/p1234567890)

---

## Next Steps

**For QA**:
1. Review test results and coverage
2. Run integration tests against staging DB
3. Verify password hashing implementation
4. Check for any regressions

**For ARCHITECT**:
1. Review code patterns (aggregate + repository)
2. Verify against DESIGN.md requirements
3. Check for architectural issues
4. Approve if satisfied

**For Merge**:
- Wait for CI/CD ✅ (all green)
- Wait for 1x ARCHITECT approval 🟡 (pending)
- Squash merge to main
- Tag next version (v0.1.0-pre)

---

## Author Notes

This PR completes T1.2 (User Aggregate). 

Key decisions:
- bcrypt 12 rounds (security vs performance tradeoff)
- Repository pattern for persistence abstraction
- Email validation with regex (simple, <100ms)
- Type hints throughout (mypy strict mode)

Next task (T1.3) depends on this for authentication service.

---

## Questions?

Questions about this PR? Feel free to comment below or reach out in Slack.

🚀 Ready to merge!
```

---

## 2️⃣ Estructura de Evidence

```
TIPOS DE EVIDENCE:

1. Test Evidence
   ├─ Test results (stdout)
   ├─ Coverage reports (HTML)
   ├─ CI/CD logs (GitHub Actions)
   └─ Test artifacts (videos, screenshots)

2. Code Quality Evidence
   ├─ Linting results (bandit, pylint, mypy)
   ├─ Code coverage (% by file/function)
   ├─ Performance metrics (latency, memory)
   └─ Static analysis results

3. Security Evidence
   ├─ Bandit (SAST) report
   ├─ Dependency scan (npm audit, pip safety)
   ├─ Secret scan (no hardcoded keys)
   └─ Manual security review

4. Documentation Evidence
   ├─ Updated DESIGN.md (if schema changed)
   ├─ Updated API.md (if endpoints added)
   ├─ Updated patterns/decisions
   └─ Commit messages (clear, semantic)

5. Traceability Evidence
   ├─ Task ID in PR title (T1.2)
   ├─ Link to issue/task
   ├─ Commit hashes
   ├─ Code review comments
   └─ Approvals
```

---

## 3️⃣ CI/CD Artifacts (Auto-attached to PR)

```yaml
# GitHub Actions automatically comments on PR:

Artifact Type          | Where             | Format
-----------------------+-------------------+------------------
Test results           | PR comments       | Summary + link
Coverage report        | codecov.io        | % by file
Lighthouse report      | artifact storage  | HTML
axe a11y scan          | PR comments       | JSON → summary
Performance metrics    | PR comments       | Table
Security scan results  | PR comments       | Summary
Build log              | GitHub Actions    | Full output
Deploy preview         | Netlify/Vercel    | Live URL
```

---

## 4️⃣ Ejemplo Real: PR T1.2

```markdown
# feat(T1.2) User Aggregate + Repository (Unit 1)

## Summary
Implements User aggregate and UserRepository following DDD patterns.
Provides CRUD operations, validation, and password hashing.

## Evidence

✅ **Tests**: 20/20 passing (92% coverage)
✅ **Code Quality**: Pylint 8.2/10, mypy clean, black formatted
✅ **Security**: Bandit 0 issues, bcrypt 12 rounds, no secrets
✅ **Performance**: Email lookup <10ms (indexed)
✅ **Documentation**: DESIGN.md Unit 1 validated

### Test Results
pytest tests/unit/test_user_model.py tests/integration/test_user_repository.py -v

test_user_creation PASSED
test_user_email_validation PASSED
test_password_hashing_bcrypt PASSED
test_duplicate_email_rejected PASSED
test_get_by_email_indexed PASSED
... (15 more)

TOTAL: 20 passed in 2.34s
Coverage: 92% (app/users/)

### Code Quality
black --check backend/app/users/ ✅
pylint backend/app/users/ → 8.2/10 ✅
mypy backend/app/users/ --strict → 0 errors ✅

### Security
bandit -r backend/app/users/ → 0 issues ✅
Password hash verified: bcrypt.gensalt(rounds=12) ✅
No hardcoded secrets: ✅

### Deployability
- Migration: 002_user_aggregate.py (idempotent) ✅
- Backwards compatible: N/A ✅
- No breaking changes: ✅

## Task Completion

- [x] T1.2 scope: 100% complete
- [x] Acceptance criteria: all 8 met
- [x] Dependencies: T1.1 satisfied
- [x] Blocks: T1.3, T1.4 unblocked

## Ready for Merge

Awaiting 1x ARCHITECT review. All checks passing.
```

---

## ✅ Checklist: PR Evidence

```
ANTES DE ABRIR PR:
☐ Todas las pruebas pasan localmente
☐ Coverage > 80%
☐ Linting limpio (black, pylint, mypy)
☐ Seguridad validada (bandit, no secrets)
☐ Commits semánticos (feat, fix, test, docs)
☐ Task completado 100% (scope OK)

AL ABRIR PR:
☐ PR title: "feat(T1.2) Description"
☐ Task ID en descripción
☐ Summary claro (qué hace)
☐ Evidence section llenado
☐ Checklist completado
☐ Relacionada con issue/task
☐ Assigned a ARCHITECT (manual review)

DESPUÉS DE CI/CD:
☐ Todos los checks: ✅ GREEN
☐ No conflicts
☐ Coverage não regressed
☐ Security scan: clean
☐ Performance: acceptable

ANTES DE MERGE:
☐ 1x ARCHITECT approval: ✅ APPROVED
☐ All conversations resolved
☐ Branch updated (no merge conflicts)
☐ Squash merge to main
☐ Tag created (v0.1.0-pre)
```

---

## Beneficios de Evidence en PRs

| Aspecto | Sin Evidence | Con Evidence |
|---------|-------------|--------------|
| Review time | 30 min (leer código) | 5 min (confiar artifacts) |
| Merge confidence | 70% | 99% |
| Regressions post-merge | 15-20% | <2% |
| Code review quality | Variable | Consistent |
| Onboarding time | 2 weeks | 3-4 days |

---

**Status**: ✅ **TEMPLATE READY FOR USE**

**Next**: Use template for T1.1 PR (Database Schema) en Semana 1
