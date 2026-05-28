# 🔍 Marco de Validación — TicketDesk Enterprise

**Proyecto**: TicketDesk Enterprise v1.0  
**Propósito**: Especificar framework de validación para garantizar calidad, seguridad y conformidad  
**Fecha**: 2026-05-27  
**Estado**: ✅ Listo para implementación

---

## 📋 Resumen Ejecutivo

El **Marco de Validación** define los mecanismos de control que garantizan que TicketDesk Enterprise cumple con:
- **Calidad de código**: Linting, type-checking, testing (unit, integration, E2E)
- **Seguridad**: OWASP Top 10, análisis de dependencias, penetration testing
- **Conformidad**: LGPD compliance, auditoría, trazabilidad
- **Rendimiento**: Core Web Vitals, latencia API, carga concurrente
- **Accesibilidad**: WCAG 2.2 AAA, screen reader compatibility

**Responsable de validación**: QA Agent (según AGENTS.md)

---

## 1️⃣ Validación de Código (Code Quality)

### 1.1 Linting y Formatting

```
BACKEND (Python):
  Tool:     black, pylint, isort, mypy
  Trigger:  Pre-commit hook, PR check, post-merge
  
  Comandos:
  $ black src/                          # Format Python code
  $ pylint src/ --exit-zero             # Check style (warnings only)
  $ mypy src/ --strict                  # Type checking strict mode
  $ isort src/                          # Organize imports
  
  Criterios de paso:
  ✓ No syntax errors (pylint score > 7.0)
  ✓ Type coverage > 95% (mypy)
  ✓ Formatting matches black standard
  ✓ No unused imports (isort)

FRONTEND (TypeScript/React):
  Tool:     ESLint, Prettier, TypeScript
  Trigger:  Pre-commit hook, PR check, CI/CD
  
  Comandos:
  $ npm run lint                        # ESLint check
  $ npm run format                      # Prettier format
  $ npm run type-check                  # TypeScript strict
  
  Criterios de paso:
  ✓ No eslint violations (error level)
  ✓ Code formatted per .prettierrc
  ✓ TypeScript strict mode passes
  ✓ No @ts-ignore comments (only with justification)

INFRAESTRUCTURA (Terraform):
  Tool:     terraform fmt, terraform validate, tflint
  Trigger:  Pre-commit, PR check
  
  Comandos:
  $ terraform fmt -recursive            # Format HCL
  $ terraform validate                  # Validate syntax
  $ tflint                              # Lint rules
  
  Criterios de paso:
  ✓ HCL properly formatted
  ✓ Valid Terraform syntax
  ✓ No security issues (tflint -format json)
```

### 1.2 Análisis Estático

```
SAST (Static Application Security Testing):
  Tool:     Bandit (Python), npm audit (Node.js)
  Trigger:  PR check, pre-deploy
  
  Comandos:
  $ bandit -r src/ -f json              # Python security scan
  $ npm audit --production              # Node.js dependencies
  $ npm audit fix --dry-run             # Check available fixes
  
  Criterios de paso:
  ✓ No critical/high vulnerabilities en dependencies
  ✓ Bandit findings reviewed y documentados
  ✓ API keys, secrets no presentes en código
  ✓ No SQL injection vectors (parameterized queries)

DEPENDENCY ANALYSIS:
  Tool:     Snyk, OWASP Dependency-Check
  Trigger:  Weekly scheduled, PR trigger
  
  Criterios de paso:
  ✓ Known vulnerabilities: 0 critical, max 2 high
  ✓ License compliance: no GPL/AGPL sin aprobación
  ✓ EOL dependencies: 0 (actualizar a versión soportada)
  ✓ Outdated packages: <3 meses atrás son aceptables
```

---

## 2️⃣ Validación de Tests

### 2.1 Coverage de Tests

```
BACKEND TESTS (pytest):
  Ubicación:  tests/unit/, tests/integration/
  Target:     > 80% line coverage
  
  Ejecución:
  $ pytest tests/ -v --cov=src --cov-report=html
  
  Por módulo:
  ├─ session/         > 90% (agregado crítico)
  ├─ botengine/       > 85% (detección jailbreak)
  ├─ evaluation/      > 85% (scoring)
  ├─ compliance/      > 90% (LGPD hard-delete)
  ├─ auth/            > 90% (RBAC)
  └─ shared/          > 75% (utilities)
  
  Métricas:
  ✓ Line coverage: >= 80%
  ✓ Branch coverage: >= 75%
  ✓ Mutation score: >= 70% (con mutmut)

FRONTEND TESTS (Jest):
  Ubicación:  src/__tests__/, src/components/__tests__/
  Target:     > 75% line coverage
  
  Ejecución:
  $ npm test -- --coverage
  
  Por categoría:
  ├─ Components       > 80%
  ├─ Hooks            > 85%
  ├─ Utils            > 70%
  └─ Integration      > 60%
  
  Casos especiales:
  ✓ XSS protection tests (sanitize HTML)
  ✓ CSRF token validation
  ✓ Session timeout behavior
  ✓ Error boundary recovery

E2E TESTS (Playwright):
  Ubicación:  tests/e2e/
  Target:     > 80% critical flows
  
  Ejecución:
  $ npx playwright test --headed
  
  Flows críticos (deben estar presentes):
  ✓ User registration → login → dashboard
  ✓ Create ticket → assign candidate → evaluate
  ✓ Candidate assessment → scoring → decision
  ✓ Compliance: consent acceptance → data deletion
  ✓ Admin: manage users → assign roles → audit log
  
  Criterios de paso:
  ✓ Todos los tests pasan (0 flakiness)
  ✓ Screenshots guardados en artifacts
  ✓ Video recording para failed tests
  ✓ Timeout: max 30s por test
```

### 2.2 Tipos de Tests

```
UNIT TESTS:
  Propósito:  Validar lógica aislada (funciones, métodos)
  Speed:      < 100ms por test
  Mock nivel: Sí, todas las dependencias externas
  Mínimo:     1 happy path + 2 edge cases por función
  
  Ejemplo (pytest):
  def test_session_candidate_validation_valid():
      session = Session(...)
      assert session.validate_candidate(...) == True
  
  def test_session_candidate_validation_invalid_email():
      session = Session(...)
      with pytest.raises(ValueError):
          session.validate_candidate(email="invalid")

INTEGRATION TESTS:
  Propósito:  Validar interacción entre componentes
  Speed:      < 1s por test
  Mock nivel: No mocks (DB real o testdb)
  Mínimo:     1 por agregado principal, 1 por dependencia
  
  Ejemplo:
  def test_session_to_evaluation_flow():
      db = setup_test_db()
      session = Session.create(...)
      db.save(session)
      evaluation = Evaluation.from_session(session.id)
      assert evaluation.status == "pending"

LOAD TESTS:
  Propósito:  Validar comportamiento bajo carga
  Speed:      Ejecutar con 200+ usuarios concurrentes
  Escenario:  Simulación de 8h pico (200 evaluaciones/hr)
  
  Herramienta: Locust
  Métricas:
  ✓ Response time P95: < 1000ms
  ✓ Response time P99: < 2000ms
  ✓ Error rate: < 0.5%
  ✓ Throughput: >= 100 req/s
  
  Ejecución:
  $ locust -f tests/load/locustfile.py \
      -u 200 -r 20 --run-time 10m
```

### 2.3 Test Failure Handling

```
FLAKY TESTS (intermitentes):
  Detección:  Ejecutar 5 veces localmente antes de mergear
  Máximo:     0 falsos positivos en CI
  Acción:     Si falla >1 vez: investigar, agregar retry, o skip con comentario
  
  Comandos:
  $ pytest tests/unit/test_session.py::test_async_flow -v --count=5

COVERAGE GAPS:
  Acción:     Si coverage < 80%:
    1. Identificar líneas no cubiertas
    2. Crear tests para cubrir (unit o integration)
    3. Si no es testeable: documentar por qué
  
  Reporte:
  $ pytest --cov=src --cov-report=term-missing
```

---

## 3️⃣ Validación de Build

### 3.1 Compilación y Bundling

```
BACKEND BUILD:
  Tool:      Docker, docker-compose
  Comando:   docker build -t ticketdesk-backend .
  
  Criterios:
  ✓ Imagen construida sin errores (exit code 0)
  ✓ Imagen < 800MB (usar .dockerignore)
  ✓ Todas las dependencias instaladas (requirements.txt)
  ✓ Healthcheck endpoint responde en 5s
  ✓ Startup < 10s desde image run

FRONTEND BUILD:
  Tool:      webpack, Next.js
  Comando:   npm run build
  
  Criterios:
  ✓ Build completa sin errores (exit code 0)
  ✓ Build output < 10MB gzipped
  ✓ JavaScript bundle < 300KB gzipped
  ✓ CSS bundle < 100KB gzipped
  ✓ Source maps generados (debug en prod)
  
  Análisis:
  $ npm run analyze                     # Bundle size analysis
  
  Máximos permitidos:
  ├─ Main chunk:        < 200KB
  ├─ Vendor chunks:     < 150KB cada
  └─ Total JS:          < 300KB gzipped

INFRASTRUCTURE BUILD:
  Tool:      terraform plan/apply
  Comando:   terraform plan -out=tfplan
  
  Criterios:
  ✓ Plan valida sin errores
  ✓ No resources elimina (a menos que intencional)
  ✓ No security group permite 0.0.0.0/0 (excepto CloudFront)
  ✓ Cost estimation < $5K/mes presupuesto
```

### 3.2 Artifact Management

```
VERSIONING:
  Backend:    v1.x.x (semver) en image tag
  Frontend:   v1.x.x en package.json
  IaC:        git tag v1.x.x
  Changelog:  CHANGELOG.md actualizado
  
  Artefact storage (CI/CD):
  ├─ Docker images:    ECR (Amazon)
  ├─ Build artifacts:  S3 versioned
  ├─ Releases:         GitHub Releases + CHANGELOG
  └─ Terraform plans:  .tfplan en artifact storage

ROLLBACK MECHANISM:
  Trigger:    Automatic si post-deploy validation falla
  Action:     ECS rolled back a previous image version
  Evidence:   CloudWatch logs + incident report
```

---

## 4️⃣ Validación de Seguridad (Security)

### 4.1 OWASP Top 10

```
OWASP-01: INJECTION ATTACKS
  Validación:
  ✓ SQL: parameterized queries (SQLAlchemy ORM)
  ✓ NoSQL: schema validation (Pydantic)
  ✓ LDAP: escaping automático
  ✓ OS: subprocess.run() sin shell=True
  
  Tests:
  def test_session_sql_injection_prevention():
      malicious = "'; DROP TABLE sessions; --"
      with pytest.raises(ValueError):
          Session.query_by_email(malicious)

OWASP-02: BROKEN AUTHENTICATION
  Validación:
  ✓ Passwords: bcrypt hash > 12 rounds
  ✓ Sessions: JWT con short-lived expiry (15min)
  ✓ Refresh tokens: stored in HTTP-only cookies
  ✓ MFA: TOTP con backup codes
  
  Tests:
  def test_password_hash_strength():
      assert bcrypt.checkpw(b"weak", hash) == False

OWASP-03: BROKEN OBJECT LEVEL ACCESS CONTROL
  Validación:
  ✓ RBAC: @require_role decorator en endpoints
  ✓ Session isolation: user_id en queries
  ✓ Tenant isolation: account_id en filters
  
  Tests:
  def test_user_cannot_access_other_session():
      user_a = create_user()
      session_b = create_session(user=user_b)
      with pytest.raises(PermissionError):
          session_b.get_by_user(user_a)

OWASP-04: BROKEN OBJECT PROPERTY LEVEL ACCESS CONTROL
  Validación:
  ✓ Serialization: @exclude_fields() en response DTOs
  ✓ PII protection: candidate_email no expose públicamente
  ✓ Sensitive fields: access_token never in logs
  
  Tests:
  def test_session_serialization_excludes_secrets():
      session = Session(access_token="secret123")
      data = session.model_dump()
      assert "access_token" not in data

OWASP-05: BROKEN ACCESS CONTROL (AUTHORIZATION)
  Validación:
  ✓ Token validation: JWT signature + expiry check
  ✓ Scope validation: token scope matches endpoint
  ✓ Rate limiting: per-user, per-IP
  
  Tests:
  def test_expired_token_rejected():
      token = create_token(exp=time.time()-3600)  # 1h ago
      with pytest.raises(UnauthorizedError):
          validate_token(token)

OWASP-06: SECURITY MISCONFIGURATION
  Validación:
  ✓ Headers: Security headers presentes (CSP, HSTS, X-Frame-Options)
  ✓ TLS: HTTPS only, TLS 1.2+
  ✓ Secrets: no hardcoded en código, en .env
  ✓ CORS: whitelist explícito, no "*"
  
  Tests:
  def test_security_headers_present():
      response = client.get("/api/health")
      assert "Strict-Transport-Security" in response.headers
      assert "Content-Security-Policy" in response.headers

OWASP-07: VULNERABLE AND OUTDATED COMPONENTS
  Validación:
  ✓ Dependencies: npm audit, pip safety
  ✓ Python: >= 3.11, no deprecated packages
  ✓ Node: >= 18, no end-of-life versions
  ✓ Security updates: applied within 30 days

OWASP-08: IDENTIFICATION AND AUTHENTICATION FAILURES
  Validación:
  ✓ Session timeout: 15min inactivity
  ✓ Password reset: 1h expiry, single-use token
  ✓ Logging: Auth failures en audit log (no passwords)
  
  Tests:
  def test_session_timeout_after_15min_inactivity():
      session = create_session()
      # Avanzar 15min
      with freeze_time("2026-05-27 13:15:00"):
          with pytest.raises(SessionExpiredError):
              validate_session(session)

OWASP-09: DATA INTEGRITY FAILURES
  Validación:
  ✓ Transactions: ACID en operations críticas
  ✓ Versioning: soft-delete + audit trail
  ✓ Consistency: constraints en DB (unique, FK)
  
  Tests:
  def test_session_delete_is_soft_delete():
      session = create_session()
      session.delete()
      assert session.deleted_at is not None
      # DB query debería excluir soft-deleted

OWASP-10: LOGGING AND MONITORING FAILURES
  Validación:
  ✓ Audit log: operaciones críticas registradas
  ✓ Sensitive data: nunca en logs (passwords, tokens)
  ✓ Alerting: anomalías detectadas en CloudWatch
  
  Logs no deben contener:
  ✗ Passwords, API keys, tokens
  ✗ PII directa (SSN, email sin masking)
  ✗ Credit card numbers
  
  Logs deben contener:
  ✓ Timestamp, user_id, action, status, latency
  ✓ Cambios de datos sensibles (masked): "email cambió de *** a ***"
```

### 4.2 Validación de Secrets

```
DETECCIÓN:
  Tool:      git-secrets, TruffleHog
  Trigger:   Pre-commit hook, post-commit scan
  
  Comando:
  $ git secrets --scan
  $ trufflehog filesystem . --json
  
  Acción:
  ✗ Si encuentra secreto: BLOQUEAR commit y fuerza rewrite history
  ✗ Rotación: regenerar API key en dashboard si fue expuesto
  
ALMACENAMIENTO:
  ✓ .env.local (gitignored)
  ✓ Secrets Manager (AWS Secrets Manager)
  ✓ .env.example con placeholder
```

---

## 5️⃣ Validación de Rendimiento

### 5.1 Core Web Vitals

```
LCP (Largest Contentful Paint): <= 2.5s
  Medición:   Lighthouse, WebPageTest, Real User Monitoring
  Optimización:
  ✓ Critical CSS inline en <head>
  ✓ LCP image preload (rel="preload")
  ✓ Server response time TTFB <= 600ms
  ✓ No render-blocking JavaScript
  
  Test:
  $ npx lighthouse https://ticketdesk.app --view

INP (Interaction to Next Paint): <= 200ms
  Medición:   Lighthouse, field testing
  Optimización:
  ✓ JavaScript debounce (click handlers)
  ✓ Web Worker para tasks pesadas
  ✓ React.memo para componentes costosos
  ✓ Lazy loading modales/dropdowns
  
  Test:
  def test_button_click_response_time():
      """Simular click, medir paint time"""
      start = performance.now()
      button.click()
      # Assert paint < 200ms

CLS (Cumulative Layout Shift): <= 0.1
  Medición:   Lighthouse, manual observation
  Validación:
  ✓ No ads/popups sin placeholder
  ✓ Imágenes tienen width/height explícito
  ✓ Fonts preload evita FOIT/FOUT
  ✓ Animations use transform/opacity (no layout)
  
  Test:
  def test_no_layout_shift_on_font_load():
      """Verificar que fonts se cargan sin shift"""
      # Medir CLS antes/después font-display: swap

PERFORMANCE BUDGET:
  JavaScript:    <= 300KB (gzipped)
  CSS:           <= 100KB (gzipped)
  Images:        <= 500KB (optimized)
  Total:         <= 1MB (initial load)
  
  Monitoreo:
  $ npm run build && npm run analyze
```

### 5.2 API Performance

```
LATENCY (P95):
  Target:     < 1000ms
  Medición:   CloudWatch metrics, custom APM
  
  Por endpoint:
  ├─ GET /api/sessions:      < 500ms (index)
  ├─ POST /api/sessions:     < 1000ms (create + save)
  ├─ GET /api/evaluate/:id:  < 2000ms (LLM call)
  └─ DELETE /api/sessions/:id: < 100ms (soft-delete)
  
  Monitoreo:
  $ curl -w "@curl-format.txt" \
      https://api.ticketdesk.app/api/health

THROUGHPUT:
  Target:     >= 100 req/s
  Escenario:  200 usuarios concurrentes
  
  Test:
  $ locust -f locustfile.py -u 200 -r 20 --run-time 10m
  
  Métricas esperadas:
  ✓ Average response time: < 500ms
  ✓ 95th percentile: < 1000ms
  ✓ 99th percentile: < 2000ms
  ✓ Error rate: < 0.5%

DATABASE PERFORMANCE:
  Query time: < 100ms (P95)
  Connection pool: > 20 concurrent
  Slow query log: enabled, monitored
  
  Queries to monitor:
  SELECT * FROM sessions WHERE account_id = ? (index en account_id)
  SELECT * FROM evaluations WHERE session_id = ? (index)
  
  Comando:
  $ mysql -u root -p'password' \
      -e "SET SESSION long_query_time=0.1; SET SESSION log_queries_not_using_indexes=ON;"
```

---

## 6️⃣ Validación de Accesibilidad (Accessibility)

### 6.1 WCAG 2.2 AAA Testing

```
AUTOMATED TESTING:
  Tool:      axe-core, WAVE, Lighthouse
  Trigger:   PR check, daily scheduled
  
  Comando:
  $ npx axe-core https://ticketdesk.app/dashboard --tags=wcag2aa
  $ npm test -- --coverage --a11y
  
  Criterios:
  ✓ No critical violations (axe)
  ✓ Color contrast: 7:1 para texto normal, 4.5:1 para grande
  ✓ Focus visible: outline claro en todos los interactive elements

MANUAL TESTING:
  Checklist:
  ✓ Keyboard-only navigation (Tab, Enter, Esc)
  ✓ Screen reader (NVDA on Windows, VoiceOver on Mac)
  ✓ Text zoom: 200% reflow sin horizontal scroll
  ✓ Color blindness: no depende solo del color
  ✓ Motion: respeta prefers-reduced-motion
  
  Tools:
  - NVDA (free, Windows)
  - VoiceOver (built-in, macOS)
  - axe DevTools browser extension
  - Chrome DevTools Lighthouse

SCREEN READER TESTING:
  Elementos críticos:
  ✓ Form labels: <label for="input"> o aria-label
  ✓ Buttons: aria-label si icon-only
  ✓ Links: aria-label descriptivo (no "click here")
  ✓ Tables: <caption>, <thead>, <scope> en <th>
  ✓ Modals: aria-modal="true", role="dialog"
  ✓ Lists: <ul>/<ol>/<li> para navegación
  ✓ Landmarks: <nav>, <main>, <footer> con roles
  
  Test NVDA:
  1. Iniciar NVDA (Ctrl+Alt+N)
  2. Tab a través de sitio
  3. Verificar que árbol de acceso semántico es correcto
  4. Verificar que form labels son anunciados

TESTING REPORT:
  Ubicación:  tests/a11y/
  Generador:  axe-core JSON report
  
  Criterios de paso:
  ✓ 0 violations críticas
  ✓ 0 violations graves
  ✓ Manual tests documentados
  ✓ Real user feedback recopilado
```

---

## 7️⃣ Validación de Conformidad (Compliance)

### 7.1 LGPD Compliance

```
HARD DELETE SLA: < 24h desde solicitud
  Validación:
  ✓ Endpoint DELETE /api/users/:id ejecuta immediately
  ✓ Backup retention: < 24h
  ✓ Audit log: user_id se registra
  
  Test:
  def test_user_hard_delete_within_24h():
      user = create_user(email="test@example.com")
      delete_response = client.delete(f"/api/users/{user.id}")
      assert delete_response.status_code == 204
      
      # Verificar en DB (hardcoded SQL, no ORM)
      with raw_db.cursor() as c:
          c.execute("SELECT * FROM users WHERE id = %s", [user.id])
          assert c.fetchone() is None
      
      # Verificar que PII fue eliminado
      # (no queda en caches, logs, backups)

CONSENT TRACKING:
  Validación:
  ✓ Consent version controlada (v1, v2, ...)
  ✓ Timestamp de aceptación registrado
  ✓ Consentimiento específico por categoría (marketing, analytics)
  
  Test:
  def test_consent_version_tracked():
      user = create_user()
      consent = user.consent_logs.latest()
      assert consent.version == "v1"
      assert consent.accepted_at is not None

PII PROTECTION:
  En logs:
  ✗ Email no debe ser logeado (usar hash o mask)
  ✗ SSN/Documento nunca
  ✓ user_id sí (para auditoría)
  
  En responses:
  ✓ candidate_email devuelto SOLO al propietario
  ✓ Interview notes pueden ser privados
  
  Validación:
  $ grep -r "candidate@" src/ logs/       # No debe encontrar PII en logs
  $ grep -r "email=" tests/               # Verificar masking en tests

DATA RETENTION:
  Validación:
  ✓ Session data: retiene 90 días, luego anonymize
  ✓ Audit logs: retiene 1 año
  ✓ Backups: retiene 30 días
  
  Comando:
  $ psql -c "SELECT COUNT(*) FROM sessions WHERE created_at < NOW() - INTERVAL '90 days';"
```

### 7.2 Audit Trail

```
AUDIT LOG REQUIREMENTS:
  Campos obligatorios:
  ├─ timestamp (UTC)
  ├─ user_id (quien hizo)
  ├─ action (qué: create, update, delete)
  ├─ resource (qué: session, evaluation)
  ├─ resource_id (cuál)
  ├─ changes (antes/después, si aplica)
  └─ ip_address (para detección de anomalías)
  
  Ejemplo:
  {
    "timestamp": "2026-05-27T10:30:00Z",
    "user_id": "u-123",
    "action": "evaluation_created",
    "resource": "evaluation",
    "resource_id": "e-456",
    "changes": {"status": {"before": null, "after": "pending"}},
    "ip_address": "203.0.113.45"
  }
  
  Test:
  def test_audit_log_on_session_create():
      session = Session.create(...)
      log = AuditLog.objects.latest()
      assert log.action == "session_created"
      assert log.user_id == session.created_by_id

IMMUTABILITY:
  ✓ Audit logs nunca se modifican (append-only)
  ✓ Stored en tabla separada de business data
  ✓ Indexed por timestamp + user_id para queries rápidas
  ✓ Replicado a immutable storage (S3 versioned, Glacier)
```

---

## 8️⃣ Validación de Regresión

### 8.1 Regression Detection

```
BASELINE COMPARISONS:
  Medición:   Antes/después de cambios
  Métricas:
  ├─ API latency (P95, P99)
  ├─ Error rate (%)
  ├─ Database query times
  ├─ JavaScript bundle size
  ├─ Test coverage (%)
  ├─ Accessibility violations count
  └─ Security scan findings
  
  Baseline almacenado en:
  .metrics/baseline.json (versionado en git)
  
  Comparación:
  $ npm run metrics:compare
  
  Criterios de paso:
  ✓ Latency: < 5% regression
  ✓ Bundle size: < 2% increase
  ✓ Coverage: no decrease
  ✓ Security findings: no increase

SCREENSHOT COMPARISON (Visual Regression):
  Tool:      Playwright visual comparisons
  Baseline:  guardado en tests/screenshots/
  
  Test:
  test('dashboard page renders correctly', async ({ page }) => {
    await page.goto('/dashboard')
    await expect(page).toHaveScreenshot('dashboard.png')
  })
  
  Ejecución:
  $ npx playwright test --update-snapshots    # Actualizar baselines
  $ npx playwright test                        # Comparar contra baselines
  
  Criterios:
  ✓ Píxeles diferentes: < 1%
  ✓ Layout no cambió
  ✓ Colors match expectations
```

### 8.2 Flakiness Detection

```
TRACKING:
  Métricas:   Tests que fallan intermitentemente
  Reporte:    En PR comments + Slack
  
  Test rerun strategy:
  def test_async_operation(self):
      for attempt in range(3):
          try:
              result = async_operation()
              break
          except TimeoutError:
              if attempt == 2:
                  raise
  
  O usar pytest-rerunfailures:
  $ pytest tests/integration/ --reruns 3 --reruns-delay 1

FLAKY TEST THRESHOLD:
  ✗ No tests pueden ser flaky (0 tolerance)
  ✓ Si falla >1 vez en 5 runs: investigar y fijar
  ✓ Si causa > 5 minutes de waste en CI: prioridad alta
```

---

## 9️⃣ Validación Pre-Deploy

### 9.1 Checklist

```
ANTES DE DESPLEGAR A STAGING:

Code Quality:
  ☐ black, pylint, mypy pasan sin errores
  ☐ eslint, typescript pasan
  ☐ terraform validate, tflint pasan
  ☐ git log --oneline muestra commits claros

Testing:
  ☐ Unit tests: > 80% coverage, todos pasan
  ☐ Integration tests: todos pasan, < 1s por test
  ☐ E2E tests: critical flows pasan
  ☐ Load tests: P95 < 1000ms, error rate < 0.5%
  ☐ Security tests: 0 OWASP critical vulnerabilities
  ☐ Accessibility tests: 0 critical violations

Security:
  ☐ No secrets en commit (git secrets scan)
  ☐ npm audit: 0 critical, < 2 high vulnerabilities
  ☐ bandit: no high/critical issues
  ☐ OWASP Top 10 coverage: 100%
  ☐ Dependency versions: supported (no EOL)

Performance:
  ☐ LCP: <= 2.5s (Lighthouse)
  ☐ INP: <= 200ms
  ☐ CLS: <= 0.1
  ☐ Bundle size: JS < 300KB gzipped, CSS < 100KB
  ☐ API latency: P95 < 1000ms

Compliance:
  ☐ LGPD hard delete test pasa
  ☐ Audit logs: todos los cambios trazables
  ☐ Data retention: configured per policy
  ☐ Consent tracking: implemented

Documentation:
  ☐ CHANGELOG.md actualizado
  ☐ API docs: generados y correctos
  ☐ Runbooks: actualizados para nuevo release
  ☐ Deployment notes: claramente documentados

ANTES DE DESPLEGAR A PROD:

Staging Validation:
  ☐ Smoke tests pasaron en staging
  ☐ Performance metrics: baseline met
  ☐ Real user testing: no issues críticos
  ☐ Security: vulnerability scan clean

Approval:
  ☐ Code review: 2+ approvals
  ☐ Security review: si hay cambios sensibles
  ☐ Product approval: feature completeness
  ☐ Operations: runbooks reviewed, on-call ready

Infrastructure:
  ☐ Terraform plan reviewed: no deletes unintended
  ☐ DNS/CDN: prewarmed
  ☐ Database: migration tested on staging replica
  ☐ Secrets rotated: new API keys deployed

Monitoring:
  ☐ CloudWatch dashboards: updated
  ☐ Alerts: configured para anomalías
  ☐ Logging: verified en staging
  ☐ APM (New Relic): agent version current

Rollback Plan:
  ☐ Previous image tagged: docker tag old-version
  ☐ Database rollback script: tested
  ☐ Feature flags: ability to disable feature via config
  ☐ On-call runbook: includes rollback steps

DEPLOYMENT EXECUTION:
  1. Execute: terraform apply (infrastructure)
  2. Verify: health checks passing
  3. Execute: data migrations (if any)
  4. Verify: post-migration validation
  5. Deploy: new image to ECS
  6. Monitor: metrics for 30 minutes
  7. Notify: stakeholders of success/rollback
```

### 9.2 Deployment Validation

```
POST-DEPLOYMENT (30 minutes):
  ☐ HTTP 200 responses en endpoints críticos
  ☐ Latency: no increase en baseline
  ☐ Error rate: < 0.5% (no errors)
  ☐ Database queries: executing normally
  ☐ Background jobs: processing queue
  ☐ Logs: no critical errors
  ☐ Alerts: no anomalies triggered
  
  Comando automatizado:
  $ ./scripts/post-deploy-validation.sh
  
  Si alguno falla:
  → ROLLBACK inmediatamente
  → Investigar en staging
  → Re-deploy solo si causa conocida y fixed
```

---

## 🔟 Orquestación de Validación

### Automatización en CI/CD

```
GITHUB ACTIONS WORKFLOW:

name: Validation Pipeline
on: [pull_request, push]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Black formatting
        run: black --check src/
      - name: ESLint
        run: npm run lint

  test:
    runs-on: ubuntu-latest
    services:
      postgres: image: postgres:15
      redis: image: redis:7
    steps:
      - uses: actions/checkout@v3
      - name: Backend tests
        run: pytest tests/ --cov=src
      - name: Frontend tests
        run: npm test -- --coverage
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: SAST (Bandit)
        run: bandit -r src/ -f json
      - name: Dependency check
        run: |
          npm audit
          pip-audit

  performance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build
        run: npm run build
      - name: Lighthouse
        run: npx lighthouse https://staging.ticketdesk.app --json
      - name: Compare metrics
        run: npm run metrics:compare

  deploy:
    needs: [lint, test, security, performance]
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to staging
        run: ./scripts/deploy.sh staging
      - name: Smoke tests
        run: ./scripts/smoke-test.sh
      - name: Deploy to prod (manual approval)
        environment: production
        run: ./scripts/deploy.sh prod
```

---

## 📊 Resumen

```
VALIDACIÓN COVERAGE:

┌──────────────────────────────────────────┐
│ FRAMEWORK DE VALIDACIÓN                  │
├──────────────────────────────────────────┤
│                                          │
│ Code Quality:     Linting + Type check  │
│ Testing:          Unit + Integration    │
│ Build:            Docker + Webpack      │
│ Security:         OWASP Top 10 + Deps   │
│ Performance:      Core Web Vitals + API │
│ Accessibility:    WCAG 2.2 AAA          │
│ Compliance:       LGPD + Audit trails   │
│ Regression:       Metrics + Screenshots │
│                                          │
│ STATE:            ✅ IMPLEMENTABLE       │
│                                          │
└──────────────────────────────────────────┘
```

---

**Especificación creada**: 2026-05-27  
**Responsable**: QA Agent  
**Próximo paso**: ORCHESTRATION-PLAN.md (4ª estación 6 artefacto)
