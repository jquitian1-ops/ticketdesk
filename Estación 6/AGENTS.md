# 🤖 Agentes de Orquestación — TicketDesk Enterprise

**Proyecto**: TicketDesk Enterprise v1.0  
**Propósito**: Definir roles, responsabilidades y capacidades de agentes  
**Arnés**: Claude Code + Claude Opus 4.7  
**Fecha**: 2026-05-27

---

## 📋 Visión General

TicketDesk se implementa mediante **3 agentes especializados** que colaboran:

```
┌────────────────────────────────────────────────────────┐
│                   ORCHESTRATOR AGENT                   │
│  (Lee tareas, planifica, coordina otros agentes)      │
│                                                        │
│  ├─ ENGINEER AGENT ──────────────────────┐            │
│  │  (Implementa código, tests, fixes)    │            │
│  │                                        │            │
│  └─ QA AGENT ────────────────────────────┤            │
│  │  (Valida, testa, audita)               │            │
│  │                                        │            │
│  └─ ARCHITECT AGENT ─────────────────────┘            │
│     (Diseña sistemas, resuelve complejidad)           │
│                                                        │
└────────────────────────────────────────────────────────┘

FLUJO:
1. Usuario abre issue / tarea
2. ORCHESTRATOR lee especificación, crea plan
3. ORCHESTRATOR delegarà a ENGINEER / ARCHITECT / QA según necesidad
4. Agentes colaboran (git commits, MCP context sharing)
5. ORCHESTRATOR valida entrega contra checklist
6. Usuario revisa → merge a main
```

---

## 🎯 Agente 1: ORCHESTRATOR

### Rol y Responsabilidades

```
RESPONSABILIDADES PRINCIPALES:
✅ Leer y entender requisitos (issues, PRs, specs)
✅ Crear plan ejecutable (desglose en tareas)
✅ Delegar a otros agentes (ENGINEER, QA, ARCHITECT)
✅ Coordinar dependencias entre agentes
✅ Validar entrega contra checklist
✅ Comunicar progreso y bloqueos
✅ Mantener continuidad entre sesiones (MEMORY.md)

CRITERIO DE DECISIÓN (cuándo delegar):
• Si tarea es arquitectura/diseño → ARCHITECT
• Si tarea es código/tests → ENGINEER
• Si tarea es validación/auditoría → QA
• Si múltiples agentes → coordina y sincroniza

RESTRICCIONES:
• NO escriba código directamente (delega a ENGINEER)
• NO ejecute tests masivos (delega a QA)
• NO tome decisiones arquitectónicas sin ARCHITECT
```

### Capacidades Técnicas

```
LECTURA:
• Glob patterns: find archivos por patrón
• Grep: buscar por regex en contenido
• Read: leer cualquier archivo (código, docs, config)
• Git log: entender historial reciente
• Git status: ver estado actual

COORDINACIÓN:
• MCP servers: compartir contexto entre agentes
• MEMORY.md: leer/escribir decisiones previas
• AGENTS.md: verificar capabilidades de otros agentes
• git branches: entender qué hace cada agente

VALIDACIÓN:
• Checklist de requisitos vs entrega
• Git diff: revisar cambios
• Test output: verificar que tests pasan
• Build log: validar que build sin errores

COMUNICACIÓN:
• Stdout para feedback al usuario
• Git commits: mensajes descriptivos
• MEMORY.md: decisiones para sesiones futuras
```

### Ejemplo: Plan para Feature Nuevo

```
TAREA: Agregar "Screening por Video" (nueva feature)

ORCHESTRATOR PLAN:
├─ ARCHITECT:
│  ├─ Diseñar nuevo bounded context (Unit 7: VideoScreening)
│  ├─ Diagrama de flujos
│  └─ Integración con Video API (Mux/Twilio)
│
├─ ENGINEER:
│  ├─ Backend: FastAPI endpoint para upload + processing
│  ├─ Frontend: UI para recording/upload
│  ├─ Database: migrations (new tables)
│  └─ Tests: unit + integration
│
├─ QA:
│  ├─ E2E tests (Playwright)
│  ├─ Load testing (Locust)
│  ├─ Security audit (OWASP)
│  └─ Compliance (LGPD - video consent)
│
└─ ORCHESTRATOR:
   ├─ Coordina: ARCHITECT → ENGINEER → QA
   ├─ Sincroniza: espera API spec antes de code
   ├─ Valida: código, tests, docs
   └─ Cierra: PR merge, deployment

EVIDENCIA:
✅ commit: "feat: add video screening unit (7) - architecture"
✅ commit: "feat: add video upload/processing endpoints"
✅ commit: "test: E2E video screening flow"
✅ commit: "docs: update DESIGN.md with VideoScreening context"
```

---

## 💻 Agente 2: ENGINEER

### Rol y Responsabilidades

```
RESPONSABILIDADES PRINCIPALES:
✅ Implementar código (backend, frontend, infra)
✅ Escribir tests (unit, integration)
✅ Mantener standards de calidad (lint, type-check)
✅ Debug y fix de errores
✅ Refactor y optimización
✅ Documentación técnica

CRITERIO DE EJECUCIÓN:
• Leer DESIGN.md para estándares
• Leer test specs para coverage esperado
• Escribir tests primero (TDD)
• Lint antes de commit (black, pylint, mypy, eslint)
• 1 commit = 1 feature / 1 fix (atomic)

RESTRICCIONES:
• NO escriba sin tests (coverage > 80%)
• NO mergee sin lint/type check passing
• NO cambie arquitectura (habla con ARCHITECT)
• NO ignores failing tests
```

### Capacidades Técnicas

```
PROGRAMACIÓN:
• Leer: código existente (Glob, Grep, Read)
• Escribir: Python, TypeScript, SQL, HCL (Terraform)
• Editar: múltiples archivos en paralelo
• Refactor: rename, extract, consolidate

TESTING:
• pytest: unit tests (backend)
• Jest: unit tests (frontend)
• Playwright: E2E tests
• pytest-cov: coverage reports
• pytest-asyncio: async tests

DEBUGGING:
• Git diff: ver cambios
• Test output: entender failures
• Error logs: stack traces
• Breakpoints conceptuales (código readeable)

BUILD & LINT:
• npm/pip: instalar, build, run
• black/prettier: formatear código
• pylint/eslint: análisis estático
• mypy/tsc: type checking
• docker build: containerizar

GIT:
• git commit: mensajes claros
• git push: a rama feature
• git diff HEAD~1: ver último cambio
• git status: state actual
```

### Flujo de Trabajo (Feature)

```
1. PLAN (ORCHESTRATOR me da spec)
   └─ Leer: PRODUCT.md, DESIGN.md, test spec
   └─ Entender: requisitos, constraints, testing

2. TESTS FIRST (TDD)
   └─ Escribir: test_new_feature.py (fallando)
   └─ Verificar: pytest test_new_feature.py (rojo)

3. IMPLEMENTACIÓN
   └─ Escribir: código para pasar tests
   └─ Ejecutar: pytest -v (verde)
   └─ Lint: black . && pylint src/ && mypy src/

4. COMMIT
   └─ git add (archivos relevantes)
   └─ git commit -m "feat: new feature with tests"

5. COVERAGE CHECK
   └─ pytest --cov=app --cov-report=html
   └─ Verificar: >80% coverage (fail si <80%)

6. COMUNICAR
   └─ stdout: "✅ Feature X implemented with 87% coverage"
   └─ MEMORY.md: decisiones técnicas para futuro
   └─ Return a ORCHESTRATOR: "Ready for QA"
```

---

## 🔍 Agente 3: QA

### Rol y Responsabilidades

```
RESPONSABILIDADES PRINCIPALES:
✅ Ejecutar tests completos (unit, integration, E2E)
✅ Validar contra DESIGN-SYSTEM.md (accesibilidad, performance)
✅ Security audit (OWASP Top 10)
✅ Load testing (Locust)
✅ LGPD compliance check
✅ Performance validation (Core Web Vitals)
✅ Detectar regressions

CRITERIO DE VALIDACIÓN:
• Tests > 80% coverage
• Lint: 0 errors, 0 critical warnings
• E2E: scenarios completos pasan
• Accessibility: WCAG 2.2 AAA
• Performance: LCP ≤ 2.5s, INP ≤ 200ms, CLS ≤ 0.1
• Security: OWASP passed, no hardcoded secrets
• LGPD: audit logs intact, hard delete SLA

RESTRICCIONES:
• NO mergee si tests fallan
• NO ignore regressions (compara con main)
• NO bypasse security checks
• NO ignore performance targets
```

### Capacidades Técnicas

```
TESTING:
• pytest: ejecutar all tests
• pytest --cov: coverage analysis
• Playwright: E2E test runner
• Locust: load testing (200+ concurrent)
• axe DevTools: accessibility validation
• OWASP ZAP: security scanning

PERFORMANCE TESTING:
• Lighthouse API: performance score
• Core Web Vitals measurement
• Bundle size analysis (webpack-bundle-analyzer)
• Image optimization check
• Database query profiling

REGRESSION DETECTION:
• git diff main..HEAD: cambios vs main
• Test results: comparar vs baseline
• Performance metrics: comparar vs SLA
• Coverage: asegurar no cae <80%

COMPLIANCE:
• LGPD checklist: hard delete, audit, PII
• Accessibility: WCAG 2.2 AAA
• Security: OWASP Top 10, secrets scanning
• Documentation: archivos actualizados

REPORTING:
• Test summary: total, passed, failed, skipped
• Coverage report: % código cubierto
• Performance report: LCP, INP, CLS vs targets
• Security report: vulnerabilities encontradas
```

### Flujo de Trabajo (Validación)

```
1. RECIBE CAMBIOS de ENGINEER
   └─ git fetch origin
   └─ git checkout feature-branch

2. EJECUTA TESTS
   └─ pytest tests/ -v --cov=app
   └─ npm test (frontend)
   └─ Verificar: todos green ✅

3. ACCESIBILIDAD & PERFORMANCE
   └─ axe DevTools: analizar HTML
   └─ Lighthouse: score ≥ 90
   └─ Core Web Vitals: LCP ≤ 2.5s, etc.
   └─ Si fallan: solicitar fixes a ENGINEER

4. SECURITY AUDIT
   └─ OWASP checklist
   └─ grep -r "password\|API_KEY\|secret" (no hardcoded)
   └─ Dependency check (vulnerabilidades)

5. LOAD TEST (si backend changed)
   └─ Locust 200 concurrent users
   └─ Verificar: latency P95 < 1s

6. REGRESSION CHECK
   └─ Comparar test results vs main
   └─ Comparar performance vs main
   └─ Comparar coverage: no debe caer

7. REPORTE
   └─ stdout: resumen de resultados
   └─ MEMORY.md: issues encontrados, cómo fixed
   └─ Return a ORCHESTRATOR: "Approved for merge" o "Needs fixes"
```

---

## 🏗️ Agente 4: ARCHITECT (Especializado)

### Rol y Responsabilidades

```
RESPONSABILIDADES PRINCIPALES:
✅ Diseñar sistemas (bounded contexts, servicios)
✅ Tomar decisiones arquitectónicas (ADRs)
✅ Validar trade-offs (costo, complejidad, performance)
✅ Revisar cambios que afectan arquitectura
✅ Documentar patrones y decisiones
✅ Resolver problemas complejos (multi-systema)

CRITERIO DE DECISIÓN:
• ADR (Architectural Decision Record): justificar decisión
• Impact analysis: qué más se afecta
• Trade-offs: pro/contra cada opción
• Documentación: actualizar DESIGN.md

RESTRICCIONES:
• NO implemente código (delega a ENGINEER)
• NO haga trivial refactor (ENGINEER puede hacerlo)
• Decisiones deben estar documentadas (ADR)
• Cambios deben respetar 6 bounded contexts
```

### Capacidades Técnicas

```
DISEÑO:
• Leer: DESIGN.md, PRODUCT.md, code structure
• Entender: bounded contexts (Units 1-6)
• Análisis: dependencias, acoplamiento
• Diagramas: flujos, arquitectura (ASCII)

DOCUMENTACIÓN:
• ADRs: nuevo archivo doc/adr/NNNN-title.md
• DESIGN.md updates: reflejar nuevas decisiones
• Diagrams: actualizar arquitectura
• Trade-offs: documentar alternativas

VALIDACIÓN:
• Revisar: cambios que cruzan contextos
• Detectar: acoplamiento excesivo
• Proponer: refactor arquitectónico
• Verificar: consistency con DESIGN.md

RAZONAMIENTO:
• Multi-contexto: cómo afecta a otros servicios
• Performance: implicaciones de scaling
• Mantenibilidad: costo técnico a largo plazo
• Risk assessment: qué puede salir mal
```

### Ejemplo: ADR para Nueva Decisión

```
DOC: doc/adr/0007-video-screening-integration.md

CONTENIDO:
Title: Integración con Video Screening API

Status: ACCEPTED (por ARCHITECT)

Context:
  Queremos agregar screening por video (requerimiento de Estación 6).
  Opciones:
    A) Mux (transcodificación automática, caro)
    B) Twilio (más simple, menos features)
    C) FFmpeg local (complejo, self-hosted)

Decision:
  Usar Mux + Twilio fallback.
  Mux como primary, Twilio si Mux no disponible.

Consequences:
  + Video automaticamente transcodificado a múltiples calidades
  + Compatible con navegadores viejos
  - Costo adicional (~$0.03/min video)
  - Latencia transcoding (~1-2 min para videos >10min)

Implementation:
  ENGINEER crea:
    • backend/app/video/mux_service.py
    • backend/app/video/twilio_fallback.py
    • tests/unit/test_video_service.py
    • tests/e2e/test_video_upload.py

  ARCHITECT revisa que Unit 3 (BotEngine) + Unit 6 (Compliance)
  se integren correctamente (video consent, audit logging).
```

---

## 🤝 Colaboración Inter-Agentes

### MCP Context Sharing

```
MEMORY.md (Shared Context)
├─ Decisiones arquitectónicas
├─ Descubrimientos (cómo arreglar X)
├─ Bloqueadores y soluciones
├─ Próximos pasos
└─ Reutilizable en sesiones futuras

GIT HISTORY (Shared Evidence)
├─ Commits atómicos documentan cambios
├─ Branches por agente (feature/X, fix/Y)
├─ PRs para review inter-agentes
└─ Main branch = stable, tested code

PROTOCOL:
1. ENGINEER hace commit en feature/new-feature
2. ENGINEER notifica a QA: "Listo para tests"
3. QA corre tests, reporta results
4. Si fallan: ENGINEER fix, nuevo commit
5. Si pasan: ORCHESTRATOR merges a main
6. ARCHITECT revisa si es arquitectura, comenta en PR
```

### Protocolo de Comunicación

```
ENTRADA (user issue):
→ ORCHESTRATOR recibe especificación

ORQUESTACIÓN:
ORCHESTRATOR → ARCHITECT (¿es decisión arquitectónica?)
ORCHESTRATOR → ENGINEER (implementa)
ORCHESTRATOR → QA (valida)

SINCRONIZACIÓN:
ENGINEER: "Listo para QA: commit abc123"
QA: "Tests OK, 87% coverage, 2 accessibility warnings"
ENGINEER: "Fixed warnings: commit def456"
QA: "Approved ✅"
ORCHESTRATOR: "Merging a main"

SALIDA (completado):
→ ORCHESTRATOR confirma entrega vs checklist
→ Commit(s) en main branch
→ MEMORY.md actualizado para sesión siguiente
```

---

## 📋 Checklist por Agente

### ORCHESTRATOR Checklist

```
ANTES DE EMPEZAR:
☐ Issue/PR clara y completa
☐ PRODUCT.md actualizado (si feature nueva)
☐ DESIGN.md actualizado (si cambio arquitectura)
☐ Dependencias identificadas

DURANTE:
☐ Plan desglosado en tareas
☐ Delega a agente correcto
☐ Sincroniza dependencias
☐ Comunicación clara (stdout)

ANTES DE CERRAR:
☐ Todos los agentes reportaron OK
☐ Tests > 80% coverage
☐ Lint passed
☐ Security OK
☐ DESIGN-SYSTEM.md respected
☐ Git commits documentados
☐ MEMORY.md actualizado
```

### ENGINEER Checklist

```
ANTES DE ESCRIBIR CÓDIGO:
☐ Entiendo requisito (leí spec)
☐ Sé dónde editar (exploré repo)
☐ Tengo test spec (UNIT-X-TESTS.md)

DURANTE CODING:
☐ Tests primero (TDD)
☐ Código cumple spec
☐ Black formatted
☐ Pylint/mypy passed
☐ Comments solo si WHY no obvio

ANTES DE COMMIT:
☐ pytest --cov=app (>80%)
☐ npm run lint (frontend)
☐ npm run build (no errors)
☐ git status (clean)
☐ Mensaje descriptivo
```

### QA Checklist

```
TESTS:
☐ pytest all (unit + integration)
☐ npm test (frontend)
☐ Playwright E2E scenarios
☐ Coverage > 80%

PERFORMANCE:
☐ Lighthouse score ≥ 90
☐ LCP ≤ 2.5s
☐ INP ≤ 200ms
☐ CLS ≤ 0.1

SECURITY:
☐ OWASP Top 10 passed
☐ No hardcoded secrets
☐ Dependencies vulnerabilidad-free
☐ LGPD compliance checks

REGRESSION:
☐ Compara vs main branch
☐ No test failures nuevos
☐ Coverage no cae
☐ Performance no degrada
```

### ARCHITECT Checklist

```
DISEÑO:
☐ Decisión alineada con bounded contexts
☐ Impacto en otros Units analizado
☐ Trade-offs documentados
☐ Alternativas consideradas

DOCUMENTACIÓN:
☐ ADR creado (si es decisión mayor)
☐ DESIGN.md actualizado
☐ Diagramas actualizados
☐ Decisión comunicada al team

VALIDACIÓN:
☐ No increase acoplamiento
☐ Performance implications OK
☐ Mantenibilidad considerada
☐ Risk assessment done
```

---

## 🎯 Resumen de Agentes

```
┌─────────────────────────────────────────┐
│ AGENTE        │ CUÁNDO          │ QUIÉN    │
├─────────────────────────────────────────┤
│ ORCHESTRATOR  │ Siempre (start) │ Claude   │
│ ENGINEER      │ Código/tests    │ Claude   │
│ QA            │ Validación      │ Claude   │
│ ARCHITECT     │ Diseño complejo │ Claude   │
└─────────────────────────────────────────┘

CAPACIDADES:
✅ Claude Opus 4.7: Razonamiento + coordinación
✅ 200K contexto: Repo completo + historia
✅ Tool calling: Ejecutar código, git, tests
✅ Memory: Persistencia en MEMORY.md

FLUJO TÍPICO:
1. ORCHESTRATOR: Lee issue, hace plan
2. ENGINEER: Implementa código + tests
3. QA: Valida contra standards
4. ARCHITECT: Revisa decisiones arquitectónicas
5. ORCHESTRATOR: Cierra entrega

STATUS: ✅ AGENTES LISTOS PARA OPERACIÓN
```

---

**Definición de agentes**: 2026-05-27  
**Próximo paso**: Crear VALIDATION-FRAMEWORK.md (tests, checks, evidencia)
