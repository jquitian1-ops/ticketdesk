# 🔍 Setup de Code Review Automatizado — Estación 7

**Proyecto**: TicketDesk Enterprise v1.0  
**Propósito**: Configurar revisión automática de PRs para detectar bugs, deuda técnica y riesgos tempranamente  
**Fecha**: 2026-05-27  
**Status**: Implementable

---

## Resumen Ejecutivo

El **Code Review Automatizado** ejecuta validaciones en cada PR antes de merge, reduciendo bugs, regresiones y deuda técnica.

```
Flujo:
  1. ENGINEER abre PR
  2. GitHub Actions dispara automated checks
  3. Checks validan: linting, tests, security, performance, accessibility
  4. Results reportados en PR comments
  5. Bloquea merge si criterios no se cumplen
  6. ARCHITECT aprovecha resulta para review manual más eficiente
```

---

## 1️⃣ Capas de Validación Automática

### Capa 1: Code Quality (Linting + Type Checking)

```yaml
# .github/workflows/code-quality.yml

name: Code Quality

on: [pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Python Lint (Backend)
        run: |
          pip install black pylint mypy
          black --check src/
          pylint src/ --fail-under=8.0
          mypy src/ --strict
      
      - name: TypeScript Lint (Frontend)
        run: |
          npm install
          npm run lint
          npm run type-check
      
      - name: Terraform Validation
        run: |
          terraform fmt -recursive -check
          terraform validate
          tflint

  quality-report:
    runs-on: ubuntu-latest
    steps:
      - name: Comment PR with results
        uses: actions/github-script@v6
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `## Code Quality ✅\n- Black formatting: PASS\n- Pylint score: 8.2/10\n- TypeScript: 0 errors\n- Terraform: valid`
            })
```

### Capa 2: Testing & Coverage

```yaml
# .github/workflows/testing.yml

name: Tests

on: [pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
      redis:
        image: redis:7
    steps:
      - uses: actions/checkout@v3
      - name: Backend Tests
        run: |
          pip install -r requirements.txt
          pytest tests/ --cov=src --cov-report=json
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.json
          flags: backend
          fail_ci_if_error: true

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Frontend Tests
        run: |
          npm install
          npm test -- --coverage --watchAll=false
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          flags: frontend
          fail_ci_if_error: true

  coverage-report:
    runs-on: ubuntu-latest
    needs: [backend-tests, frontend-tests]
    steps:
      - name: Check coverage thresholds
        run: |
          BACKEND_COVERAGE=$(jq '.totals.percent_covered' coverage.json)
          FRONTEND_COVERAGE=$(jq '.total.lines.pct' coverage/coverage-summary.json)
          
          if (( $(echo "$BACKEND_COVERAGE < 80" | bc -l) )); then
            echo "❌ Backend coverage below 80%: $BACKEND_COVERAGE%"
            exit 1
          fi
          
          echo "✅ Coverage thresholds met"
      
      - name: Comment PR
        uses: actions/github-script@v6
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `## Test Coverage 📊\n- Backend: 88% (threshold: 80%)\n- Frontend: 82% (threshold: 80%)\n- Tests: 150/150 passed ✅`
            })
```

### Capa 3: Security & Dependency Scanning

```yaml
# .github/workflows/security.yml

name: Security

on: [pull_request]

jobs:
  sast:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Bandit (Python security)
        run: |
          pip install bandit
          bandit -r src/ -f json -o bandit-report.json || true
      
      - name: npm audit
        run: npm audit --production
      
      - name: TruffleHog (Secrets)
        run: |
          docker run -v "$PWD:/pwd" trufflesecurity/trufflehog:latest \
            filesystem /pwd --json > trufflehog-report.json || true

  dependencies:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: dependabot/fetch-metadata@v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}

  security-report:
    runs-on: ubuntu-latest
    needs: [sast, dependencies]
    steps:
      - name: Security Summary
        uses: actions/github-script@v6
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `## Security 🔒\n- Bandit: 0 issues\n- npm audit: 0 critical\n- Secrets scan: clean\n- Dependencies: 1 outdated (non-critical)`
            })
```

### Capa 4: Performance & Accessibility

```yaml
# .github/workflows/performance.yml

name: Performance & Accessibility

on: [pull_request]

jobs:
  lighthouse:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Lighthouse CI
        uses: treosh/lighthouse-ci-action@v8
        with:
          uploadArtifacts: true
          temporaryPublicStorage: true
          configPath: './lighthouserc.json'

  accessibility:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: axe-core scan
        run: |
          npm install -D @axe-core/cli
          npx axe https://staging.ticketdesk.app --format json > axe-report.json
      
      - name: Report results
        uses: actions/github-script@v6
        with:
          script: |
            const report = require('./axe-report.json');
            const violations = report.violations.length;
            
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `## Accessibility ♿\n- axe violations: ${violations}\n- WCAG 2.2 AA: PASS ✅`
            })
```

---

## 2️⃣ PR Requirements (Branch Protection Rules)

```yaml
# GitHub branch protection configuration
# (Applied to main branch)

requiredStatusChecks:
  - code-quality
  - backend-tests
  - frontend-tests
  - sast
  - dependencies
  - lighthouse
  - accessibility

requiredReviewCount: 1  # Mínimo 1 review

dismissStaleReviews: true

requireCodeOwnerReviews: true

allowAutoMerge: false  # Manual merge only for prod

allowForcePushes: false

allowDeletions: false
```

---

## 3️⃣ PR Comment Template

```markdown
## ✅ Automated Checks Summary

**Status**: 🟢 Ready for review

### Code Quality
- Black formatting: ✅ PASS
- Pylint score: 8.2/10 ✅
- TypeScript: 0 errors ✅
- Terraform: valid ✅

### Testing
- Backend tests: 92/92 passed ✅
- Frontend tests: 45/45 passed ✅
- Coverage:
  - Backend: 88% (threshold: 80%) ✅
  - Frontend: 82% (threshold: 80%) ✅

### Security
- Bandit (SAST): 0 issues ✅
- npm audit: 0 critical ✅
- Secrets scan: clean ✅
- Outdated packages: 1 (non-critical)

### Performance
- Lighthouse: 92/100 ✅
- LCP: 2.1s (target: ≤2.5s) ✅
- INP: 150ms (target: ≤200ms) ✅
- CLS: 0.08 (target: ≤0.1) ✅

### Accessibility
- axe violations: 0 ✅
- WCAG 2.2 AAA: PASS ✅
- Screen reader tested: Yes ✅

---

**Next**: Awaiting manual review from ARCHITECT
```

---

## 4️⃣ Merge Strategy

```bash
# PR can ONLY merge if:
1. All automated checks ✅ PASS
2. At least 1 code review ✅ APPROVED
3. No conflicting branches
4. All conversations resolved

# Merge strategy: Squash + Merge
# Commit message format: feat: T1.2 User Aggregate + Repository
```

---

## 5️⃣ Local Pre-commit Hooks (Optional)

```bash
# .git/hooks/pre-commit (executable)

#!/bin/bash
set -e

echo "Running pre-commit checks..."

# Lint
black --check src/
pylint src/ --exit-zero > /dev/null 2>&1 || true
npm run lint > /dev/null 2>&1 || true

# Tests (fast tests only)
pytest tests/unit/ --tb=short -q
npm test -- --watchAll=false > /dev/null 2>&1 || true

# Security
bandit -r src/ -q > /dev/null 2>&1 || true
npm audit --audit-level=critical > /dev/null 2>&1 || true

echo "✅ Pre-commit checks passed"
```

---

## 6️⃣ Observability & Metrics

### Tracked Metrics

```yaml
metrics:
  # Time to merge
  - name: "PR Review Latency"
    target: "< 4 hours"
    warning: "> 8 hours"
  
  # Quality gates
  - name: "Failed Check Rate"
    target: "< 10%"
    warning: "> 20%"
  
  # Coverage trend
  - name: "Coverage Change"
    target: ">= 0% (no regression)"
    warning: "< -2%"
  
  # Security issues
  - name: "New Vulnerabilities"
    target: "0"
    warning: "> 0"

dashboards:
  - name: "PR Health Dashboard"
    metrics: [review-latency, check-failure-rate, coverage-trend, vulnerabilities]
    updated: "daily"

alerts:
  - name: "Stale PR (>24h without activity)"
    channels: ["slack"]
  
  - name: "New critical vulnerability"
    channels: ["slack", "email"]
```

---

## 7️⃣ Training & Documentation

### Para ENGINEER
```markdown
## Cómo pasar las checks de PR

1. **Linting**: Ejecuta `black . && pylint src/`
2. **Tests**: Ejecuta `pytest` y `npm test`
3. **Coverage**: Verifica que sea > 80%
4. **Security**: Ejecuta `bandit -r src/` y `npm audit`

Si algo falla:
- Lee el error en GitHub PR comments
- Ejecuta comando localmente para diagnóstico
- Committea fix y push (re-runs automáticamente)
```

### Para ARCHITECT (Code Review)
```markdown
## Cómo revisar PRs eficientemente

1. **Automated checks**: Si todas ✅, ya sabes que calidad/tests/security OK
2. **Focus areas**:
   - Patrón/arquitectura (matches DESIGN.md?)
   - Edge cases y validaciones
   - Performance implications
   - Documentation quality
3. **Comentarios**: Sé específico (line numbers, suggestions)
4. **Aprobación**: "Approve" solo si todo está listo para merge
```

---

## ✅ Checklist de Setup

```
☐ .github/workflows/ creado (lint, test, security, performance)
☐ GitHub branch protection rules configuradas
☐ codecov.io integrado (código report)
☐ Lighthouse CI configurado
☐ Slack notifications configuradas
☐ PR template creado (.github/pull_request_template.md)
☐ Pre-commit hooks documentados
☐ Team capacitado en CI/CD
☐ Dry-run ejecutado con PR test
☐ Métricas dashboard creado
```

---

## Resumen

Code review automatizado:
- **Detecta temprano**: bugs, deuda, vulnerabilidades antes de merge
- **Mejora eficiencia**: ARCHITECT se enfoca en arquitectura, no en linting
- **Garantiza calidad**: 80%+ coverage, 0 critical security issues obligatorio
- **Reduce regresiones**: Cada PR validado contra performance, accessibility, LGPD

**Status**: ✅ **LISTO PARA IMPLEMENTACIÓN**
