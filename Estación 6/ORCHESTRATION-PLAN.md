# 🎼 Plan de Orquestación — TicketDesk Enterprise

**Proyecto**: TicketDesk Enterprise v1.0  
**Propósito**: Especificar cómo coordinan agentes para implementar TicketDesk  
**Fecha**: 2026-05-27  
**Estado**: ✅ Listo para ejecución coordinada

---

## 📋 Resumen Ejecutivo

El **Plan de Orquestación** define cómo 4 agentes especializados (ORCHESTRATOR, ENGINEER, QA, ARCHITECT) trabajan en conjunto para implementar TicketDesk Enterprise usando Claude Code como arnés.

```
┌──────────────────────────────────────────────┐
│ CICLO DE ORQUESTACIÓN                        │
├──────────────────────────────────────────────┤
│                                              │
│ 1. ORCHESTRATOR lee requirements             │
│ 2. ORCHESTRATOR crea plan detallado          │
│ 3. ORCHESTRATOR delega tasks a agentes       │
│ 4. ENGINEER implementa código                │
│ 5. QA valida (tests, seguridad, perf)        │
│ 6. ARCHITECT revisa arquitectura             │
│ 7. ORCHESTRATOR sincroniza, valida, reporta │
│                                              │
└──────────────────────────────────────────────┘
```

---

## 1️⃣ Protocolos de Workflow

### 1.1 Inicio de Tarea

```
FASE: ORCHESTRATOR INITIALIZATION

Entrada:
  • Requirement/Issue description
  • Acceptance criteria
  • Constraints (time, resources, scope)

Acciones ORCHESTRATOR:
  1. Lee especificación (PRODUCT.md, DESIGN.md)
  2. Consulta MEMORY.md para contexto previo
  3. Ejecuta: git status, git log --oneline -5
  4. Crea plan.md con:
     ├─ Resumen ejecutivo (1 párrafo)
     ├─ Scope (qué se incluye/excluye)
     ├─ Subtasks (desglose en pasos atómicos)
     ├─ Dependencias entre tasks
     ├─ Archivos afectados
     ├─ Success criteria (testeable)
     └─ Riesgos y mitigaciones

Salida:
  • plan.md (guardar en .claude/plans/)
  • Confirmación al usuario (si es interactivo)
  • Delegación clara a ENGINEER/QA/ARCHITECT

Ejemplo de plan.md:
---
# Plan: Implementar Session Management (Unit 2)

## Resumen
Crear agregado Session con validación de candidatos, manejo de estado,
y scoring inicial. Integración con Compliance Unit para consentimiento.

## Scope
IN:  Session aggregate, repository, endpoints POST/GET/DELETE
OUT: Advanced features (versioning, branching)

## Subtasks
1. Define Session schema + validations (ARCHITECT)
2. Implement Session service (ENGINEER) [depends: 1]
3. Write unit tests (ENGINEER) [depends: 2]
4. Implement API endpoints (ENGINEER) [depends: 2]
5. Integration tests con BD (QA) [depends: 4]
6. Security validation LGPD (QA) [depends: 4]

## Success Criteria
- Session.create() validates candidate_email
- POST /api/sessions returns 201 with session_id
- LGPD: PII never logged
- Coverage > 90%
- Load test: <100ms per create

## Risks
- LGPD scope creep (mitigar: scope doc firmado)
- DB migration (mitigar: dry-run en staging primero)
---

COMUNICACIÓN:
  → Si es interactivo: mostrar plan, esperar aprobación
  → Si es autónomo: proceder sin aprobación explícita
```

### 1.2 Ejecución Paralela

```
PATRÓN: Agentes trabajan en paralelo cuando son independientes

Ejemplo (Unit 2 + Unit 3 paralelo):
├─ ENGINEER: Unit 2 backend (Session aggregate)
│            ├─ Service layer
│            ├─ Repository
│            ├─ Tests (unit + integration)
│            └─ API endpoints
│
└─ ENGINEER: Unit 3 backend (BotEngine)
             ├─ Claude API client
             ├─ Jailbreak detection
             ├─ Token budget logic
             └─ SSE streaming

Coordinación:
  • Ambos escriben a memoria.md cambios en interfaces públicas
  • Si Unit 2 cambia Session schema → aviso en MEMORY.md
  • Si Unit 3 necesita cambio en Unit 2 → pull MEMORY.md antes de proceder
  • Merges: ordenar por dependencia topológica (Unit 2 primero, luego Unit 3)

MCP CONTEXT SHARING:
  • Archivo: MEMORY.md (git tracked)
  • Actualizar antes de cambios interfaciales
  • Leer antes de implementar dependencias
  • Estructura:
    [agent-name]: cambio realizado (2026-05-27 14:30)
    - Impact: qué afecta
    - Interface changes: qué expone
    - Tests needed: qué validar
```

### 1.3 Sincronización de Agentes

```
SINCRONIZACIÓN EXPLÍCITA:

Cuando ENGINEER termina Unit 2:
  1. Commit todos los cambios
  2. Actualizar MEMORY.md:
     ENGINEER-UNIT2-COMPLETE: 2026-05-27 15:00
     - Session aggregate implementado
     - Endpoints: POST/GET/DELETE /api/sessions
     - Tests: 48 unit tests, 8 integration tests
     - Coverage: 92%
  3. Git push origin feature/unit2
  4. Esperar validación de QA/ARCHITECT

Cuando QA valida Unit 2:
  1. Ejecutar test suite completa
  2. Ejecutar security scan
  3. Ejecutar load test
  4. Actualizar MEMORY.md:
     QA-UNIT2-VALIDATED: 2026-05-27 15:45
     - Coverage: 92% ✓
     - Security: 0 critical issues ✓
     - Load: P95 80ms ✓
     - Status: APPROVED FOR MERGE

Cuando ORCHESTRATOR sincroniza:
  1. Verificar que todos los agentes reportan COMPLETE
  2. Ejecutar sanity checks
  3. Merge a main (si todo está listo)
  4. Actualizar CHANGELOG.md
  5. Tag release (v0.2.0)
  6. Reportar al usuario
```

---

## 2️⃣ Patrones de Orquestación

### 2.1 Patrón: Cascada (Pipeline lineal)

```
Caso: Dependencia fuerte entre fases (ej: DB migration primero, luego tests)

Flujo:
  PHASE 1: DB Schema
    → ENGINEER: crea migrations en Alembic
    → QA: valida schema contra requirements
    → ORCHESTRATOR: verifica migrations

  PHASE 2: Service Layer
    → ENGINEER: implementa ServiceLayer que usa schema
    → ENGINEER: escribe tests
    → QA: ejecuta coverage

  PHASE 3: API Endpoints
    → ENGINEER: expone endpoints
    → QA: E2E testing

Patrón git:
  main ← feature/migrations ← feature/services ← feature/endpoints
  (cada merge espera validación de anterior)

RIESGO: Si Phase 1 falla, whole pipeline bloqueado
MITIGACIÓN: Validar Phase 1 extensivamente antes de desbloquear Phase 2
```

### 2.2 Patrón: Fork-Join (Paralelo + merge)

```
Caso: Múltiples Units independientes (Unit 2 y Unit 3)

Flujo:
       main
       /  \
      /    \
   Unit2   Unit3
    |       |
   test    test
    |       |
   QA      QA
    \      /
     \ merge /
      \ /
      main

Patrón git:
  main ← feature/unit2 (paralelo)
       ← feature/unit3 (paralelo)
  
  Cuando ambas pasan QA:
    → git merge feature/unit2 origin/main
    → git merge feature/unit3 origin/main (puede tener conflictos)
    → Resolver conflictos si hay (namespace issues)
    → Ejecutar tests nuevamente
    → Deploy

COORDINACIÓN:
  • Antes de merging: leer MEMORY.md de rama hermana
  • Si hay conflictos: ORCHESTRATOR revisa ambas implementaciones
  • Resuelve: dialogo entre ENGINEER (unit2) e ENGINEER (unit3)
```

### 2.3 Patrón: Fan-In (Muchos agentes → 1 punto de merge)

```
Caso: Sprint con 10 tareas paralelas (módulos pequeños)

Flujo:
  feature/auth → \
  feature/core → |
  feature/api  → | → integrate & test → merge
  feature/db   → |
  ...          → /

Archivo de coordinación: INTEGRATION-BLOCKERS.md
  Contenido:
  ✗ feature/auth no puede mergearse hasta que feature/core esté merged
    (Razón: usa Core context)
  ✗ feature/api no puede mergearse hasta que feature/auth esté merged
    (Razón: depende de JWT validation)
  ✓ feature/db puede mergearse con cualquiera (independiente)

Acción de ORCHESTRATOR:
  1. Mantener INTEGRATION-BLOCKERS.md actualizado
  2. Ejecutar merge en orden topológico
  3. Re-run tests después de cada merge (para detectar regresiones)
  4. Si test falla: ROLLBACK última merge, notificar ENGINEER
```

---

## 3️⃣ Gestión de Dependencias

### 3.1 Matriz de Dependencias

```
STRUCTURE (cómo Units dependen entre sí):

Unit 1 (Account) ← autenticación
Unit 2 (Session) ← depende de Unit 1 (JWT validation)
Unit 3 (BotEngine) ← depende de Unit 2 (session_id context)
Unit 4 (Evaluation) ← depende de Unit 3 (bot_response)
Unit 5 (Frontend) ← depende de Unit 1,2,4 (API contracts)
Unit 6 (Compliance) ← depende de Unit 2 (audit trail)

Orden de implementación (topológico):
  1. Unit 1 (base)
  2. Unit 2, Unit 6 (pueden ir paralelo, ambos dependen de 1)
  3. Unit 3 (depende de 2)
  4. Unit 4 (depende de 3)
  5. Unit 5 (depende de 1,2,4)

PASOS:
  1. Deploy Unit 1 → staging
  2. Deploy Unit 2 + Unit 6 paralelo → staging (con Unit 1)
  3. Validate Unit 2 + Unit 6
  4. Deploy Unit 3 → staging
  5. Deploy Unit 4 → staging
  6. Deploy Unit 5 → staging
  7. Full E2E test
  8. Deploy prod
```

### 3.2 Interface Contracts

```
CONTRATO: Unit 2 ↔ Unit 3

Session aggregate expone:
  class Session:
    session_id: str
    candidate_email: str
    status: "pending" | "screening" | "evaluated"
    messages: List[Message]

    def get_context() -> dict:
      """Retorna contexto para BotEngine (Unit 3)"""
      return {
        "session_id": self.session_id,
        "candidate_email": self.candidate_email,  # MASKED en logs
        "message_history": self.messages,
      }

BotEngine (Unit 3) usa:
  @router.post("/api/evaluate")
  def evaluate(session: Session):
    context = session.get_context()
    response = claude_api.send_messages(
      system=SYSTEM_PROMPT,
      messages=context["message_history"]
    )
    return {
      "response": response,
      "jailbreak_detected": jailbreak_check(response)
    }

VALIDACIÓN:
  • Cualquier cambio en Session.get_context() → notificar BotEngine ENGINEER
  • Cambio en Unit 2 → actualizar MEMORY.md ANTES de merging
  • BotEngine valida AFTER Unit 2 merge

Archivo: INTERFACE-CONTRACTS.md (git tracked)
  Contenido:
  ```
  ## Unit 2 → Unit 3: Session Context
  
  Desde: Session.get_context()
  Para: BotEngine.evaluate(session)
  
  Campos:
    - session_id (str, ≤36 chars)
    - candidate_email (str, masked en logs)
    - message_history (List[Message])
  
  Validación:
    - session_id nunca nulo
    - message_history indexado por timestamp
    - masking: candidateEmail nunca en logs
  
  Cambios requeridos (backcompat):
    - Agregar campo: version mayor en schema
    - Remover campo: DEPRECATED para 1 release
    - Renombrar: dual export (old name → new name)
  ```
```

---

## 4️⃣ Recolección de Evidencia

### 4.1 Artefactos por Agente

```
ENGINEER produces:
  • Feature branch (origin/feature/unit2)
  • Commits (semánticos: feat: ..., fix: ..., test: ...)
  • Test suite (tests/unit/, tests/integration/)
  • Build artifacts (Docker image in ECR)
  • MEMORY.md entry:
    ENGINEER-UNIT2: 2026-05-27 15:00
    - Implementation: Session aggregate
    - Files: app/sessions/, tests/unit/test_sessions.py
    - Tests: 48 written (pytest)
    - Build: docker build passed
    - PR: github.com/org/repo/pull/123

QA produces:
  • Test execution report:
    pytest --cov=app tests/unit/ → 92% coverage
    npm test -- --coverage → 85% frontend
  • Security scan: bandit, npm audit
  • Performance report: Lighthouse, load test
  • Accessibility report: axe-core scan
  • MEMORY.md entry:
    QA-UNIT2: 2026-05-27 15:45
    - Tests: 48 unit passed (92% coverage)
    - Security: 0 critical, 1 medium (review required)
    - Performance: P95 80ms (target <100ms) ✓
    - Accessibility: 0 violations ✓
    - Status: APPROVED

ARCHITECT produces:
  • Design review document:
    - Pattern validation (aggregate correct? services right?)
    - ADR (Architecture Decision Record)
    - Trade-off analysis
  • MEMORY.md entry:
    ARCHITECT-UNIT2: 2026-05-27 16:00
    - Pattern: Aggregate, Service Layer (✓ correct)
    - ADR: Why soft-delete not hard (LGPD constraint)
    - Trade-offs: Performance vs LGPD compliance (reviewed)
    - Status: APPROVED

ORCHESTRATOR produces:
  • Master report:
    - All PRs merged ✓
    - All tests passing ✓
    - All QA checks ✓
    - All ARCH reviews ✓
    - Release notes (CHANGELOG.md)
  • Git tag: v0.2.0 (bump version)
  • Final MEMORY.md entry:
    ORCHESTRATOR-RELEASE-V0.2.0: 2026-05-27 17:00
    - Scope: Unit 2 (Session) + Unit 6 (Compliance)
    - Status: RELEASED TO STAGING
    - Next: Full E2E testing before prod
```

### 4.2 Estructura de MEMORY.md

```
MEMORY.md (en raíz de proyecto)

---
# CONTEXT SHARED BETWEEN AGENTS

## Current Work (por timestamp descendente)

### 2026-05-27 17:00
**ORCHESTRATOR-RELEASE-V0.2.0**
- Merged: feature/unit2, feature/unit6
- Tests: ALL PASSING (92% coverage, 0 violations)
- Build: docker image pushed to ECR
- Status: RELEASED TO STAGING
- Next: E2E testing + prod deployment

### 2026-05-27 16:00
**ARCHITECT-UNIT2-APPROVED**
- Session aggregate: pattern correct ✓
- Soft-delete justification: LGPD <24h hard delete requirement
- Service layer: appropriate (not God object)
- ADR #7: Why soft-delete + celery task for hard-delete at T+24h

### 2026-05-27 15:45
**QA-UNIT2-VALIDATED**
- pytest: 48 tests, 92% coverage, all passing
- Security: bandit clean, npm audit 0 critical
- Performance: P95 80ms < 100ms target ✓
- Accessibility: axe 0 violations
- Status: APPROVED FOR MERGE

### 2026-05-27 15:00
**ENGINEER-UNIT2-COMPLETE**
- Session aggregate: validation, state machine, events
- API endpoints: POST/GET/DELETE /api/sessions
- Tests: 48 unit + 8 integration written
- Files: app/sessions/ (service, repository, models)
- PR: github.com/org/repo/pull/123
- Build: docker build passed, image: ticketdesk-backend:abc123

## Blocked Issues (Si las hay)

### 2026-05-27 14:30
**BLOCKED: ENGINEER-UNIT3 waiting for UNIT2**
- Reason: Unit 3 needs Session.get_context() from Unit 2
- Unblocks: When Unit 2 merged to main
- Action: ENGINEER-UNIT3 to pull main and test integration

## Planned Work (próximas 24h)

### 2026-05-28 09:00
- ENGINEER-UNIT3: Implement BotEngine Claude client
- QA: Prepare E2E test suite for Unit 3
- ARCHITECT: Review API contract Unit 2→3

### 2026-05-28 16:00
- Merge Unit 3 to staging
- Full E2E test Unit 2→3 flow

---

ACTUALIZACIÓN: Cada agente actualiza su sección cuando termina
LECTURA: Cada agente lee antes de empezar
RESOLUCIÓN: Si hay conflicto (dos agentes escriben campo distinto), ORCHESTRATOR resuelve
```

---

## 5️⃣ Comunicación Inter-Agentes

### 5.1 Protocolo MCP (Model Context Protocol)

```
CANAL: MEMORY.md (git-tracked context file)

WRITE PROTOCOL:
  1. Agente lee MEMORY.md actual (git pull origin main)
  2. Agente hace cambios locales
  3. Agente escribe a MEMORY.md su entrada
  4. Agente commits: "chore: memory update [ENGINEER-UNIT2-COMPLETE]"
  5. Agente pushes: git push origin feature/unit2
  6. (ORCHESTRATOR sincroniza y merged si están listos)

READ PROTOCOL:
  1. Agente necesita saber estado de otros
  2. Agente ejecuta: git pull origin main
  3. Agente lee MEMORY.md sección relevante
  4. Agente continúa con información actualizada

CONFLICT RESOLUTION:
  Si 2 agentes escriben simultáneamente:
    → git merge conflict en MEMORY.md
    → ORCHESTRATOR resuelve (keep both entries, add timestamp)
    → Re-push con merge commit

Ejemplo conflicto:
  <<<<<<< HEAD (ENGINEER-UNIT2)
  ENGINEER-UNIT2: Session ready for QA
  =======
  QA-UNIT2: Ready to test
  >>>>>>> origin/main
  
  Resolución ORCHESTRATOR:
  ENGINEER-UNIT2: Session ready for QA (15:00)
  QA-UNIT2: Ready to test (15:01)
  (mantener ambos, ordenar por timestamp)
```

### 5.2 Lenguaje de Coordinación

```
ESTADOS DE TAREA:

[PLANNING]    → Agente está diseñando
[IN_PROGRESS] → Agente está codificando
[TESTING]     → Agente escribe tests o QA ejecuta tests
[BLOCKED]     → Esperando otro agente/recurso (describir por qué)
[READY]       → Listo para review (PR)
[APPROVED]    → Aprobado por reviewer (QA/ARCHITECT)
[DEPLOYED]    → Merged y en env destino

FORMATO MEMORIA:

AGENT-UNIT-STATE-TIMESTAMP
- Status: [STATE]
- Issue/PR: URL o branch name
- Blockers: descripción si BLOCKED
- Next: siguiente paso

Ejemplo:
  ENGINEER-UNIT3: [IN_PROGRESS]
  - Status: Coding BotEngine Claude client
  - Issue: github.com/org/repo/issues/42
  - Blockers: Waiting for Unit 2 merge (due 16:00)
  - Next: Integration test with Session.get_context()

  ORCHESTRATOR-SYNC: [APPROVING]
  - Merged: unit2, unit6
  - Testing: full E2E suite
  - Next: Prod deployment if E2E passes
```

---

## 6️⃣ Scheduling de Trabajo

### 6.1 Sprints y Milestones

```
SPRINT STRUCTURE:

SPRINT = 1 semana (5 días)
  Lunes-Viernes: Implementación
  Viernes PM: Retrospectiva + planning

MILESTONE = 1 Unit + Related features
  Ej: Unit 2 (Session Management)
  Tamaño: 2-3 sprints

ROADMAP:

Sprint 1 (Semana 1):
  - Unit 1: Account Management (auth, RBAC)
  - Unit 6: Compliance scaffolding (audit log)
  Output: v0.1.0 to staging

Sprint 2 (Semana 2):
  - Unit 2: Session Management (full flow)
  Output: v0.2.0 to staging

Sprint 3 (Semana 3):
  - Unit 3: BotEngine (Claude integration)
  - Unit 4: Evaluation (scoring)
  Output: v0.3.0 to staging

Sprint 4 (Semana 4):
  - Unit 5: Frontend (React components)
  - E2E: Full user flows
  Output: v1.0.0 to prod

SCHEDULE (Daily):

09:00 - ORCHESTRATOR: Daily standup
        ├─ Read MEMORY.md
        ├─ Check blockers
        ├─ Assign work
        └─ Update priority

09:30 - ENGINEER: Start coding
        ├─ Read MEMORY.md for blockers
        ├─ Pull latest main
        ├─ Implement feature
        └─ Write tests

14:00 - QA: Validate previous day work
        ├─ Run test suite
        ├─ Security scan
        ├─ Performance check
        ├─ Update MEMORY.md

15:00 - ARCHITECT: Review pull requests
        ├─ Pattern validation
        ├─ ADR if needed
        ├─ Approve/request changes

16:00 - ORCHESTRATOR: Sync & integrate
        ├─ Check all statuses in MEMORY.md
        ├─ Merge approved PRs
        ├─ Update CHANGELOG.md
        ├─ Report status
```

### 6.2 Manejo de Bloqueos

```
ESCENARIO: Unit 3 bloqueado esperando Unit 2

Acción inmediata:
  1. ENGINEER-UNIT3 notifica en MEMORY.md:
     ENGINEER-UNIT3: [BLOCKED]
     - Reason: Unit 2 PR #123 not merged
     - Impact: Can't code Session.get_context() integration
     - Estimated unblock: 2h (waiting for QA approval)
  
  2. ORCHESTRATOR lee MEMORY.md, ve BLOCKED
  
  3. ORCHESTRATOR prioriza:
     - Acelera QA testing de Unit 2
     - Si QA necesita help: asigna resources
     - Comunica ETA a ENGINEER-UNIT3
  
  4. Una vez Unit 2 merged:
     - ORCHESTRATOR actualiza MEMORY.md
     - ENGINEER-UNIT3 es notificado (si sistema automático)
     - ENGINEER-UNIT3 pueda proceder

PREVENCIÓN:
  • Overlap: Antes de esperar, calcular qué puede hacerse paralelo
  • Ej: Si Unit 3 espera Unit 2, Unit 3 ENGINEER puede:
    → Escribir tests (mocks de Session)
    → Diseñar API contract
    → Implementar Claude client (sin Session integration)
    → Rápidamente mergear cuando Unit 2 listo
```

---

## 7️⃣ Validación Post-Merge

### 7.1 Checklist Integración

```
Después de cada merge a main:

☐ ORCHESTRATOR ejecuta:
  1. git pull origin main
  2. pytest tests/ --cov=app -v
  3. npm test -- --coverage
  4. terraform validate
  5. npm run build

☐ ORCHESTRATOR verifica:
  ✓ Todos los tests pasan
  ✓ Coverage > 80%
  ✓ Terraform plan válido (sin unexpected changes)
  ✓ Build artifacts generados
  ✓ No new security issues

☐ ORCHESTRATOR reporta:
  • PR merged: feature/unit2 → main
  • Tests: 48 unit (pass), 92% coverage
  • Build: docker push successful
  • Version: v0.2.0 tagged
  • Status: Ready for staging deployment

Si algo falla:
  → ROLLBACK commit inmediatamente
  → Notificar ENGINEER del problema
  → ENGINEER diagnostica localmente
  → Re-prepare PR
```

### 7.2 Smoke Tests Post-Deploy

```
Después de desplegar a staging:

ORCHESTRATOR ejecuta:
  1. Health check: GET /health → 200
  2. Auth flow: POST /auth/login → JWT
  3. Core flow: POST /api/sessions → 201 session_id
  4. Query: GET /api/sessions/:id → 200 with data
  5. Delete: DELETE /api/sessions/:id → 204
  6. Audit log: SELECT audit_log WHERE session_id = ?
  
Si todo pasa:
  → Actualizar MEMORY.md: STAGING-DEPLOYMENT-OK
  → Unlock PROD deployment checklist

Si algo falla:
  → Rollback ECS task definition
  → Investigar en CloudWatch logs
  → Comunicar a ENGINEER
```

---

## 8️⃣ Escenarios de Coordinación

### Scenario 1: Implementación Simple (1 Unit)

```
Tarea: Implementar Unit 1 (Account Management)
Duración: 1-2 días

Timeline:

T+0h (09:00):
  ORCHESTRATOR:
    • Lee PRODUCT.md, DESIGN.md
    • Crea plan.md con subtasks
    • Delega a ENGINEER: "Implementar Session aggregate"

T+2h (11:00):
  ENGINEER:
    • Implementa User, Role, RBAC models
    • Escribe 40 unit tests
    • Opens PR #100

T+4h (13:00):
  QA:
    • Ejecuta test suite: 40/40 pass, 90% coverage
    • Ejecuta security scan: bandit clean
    • Aprueba PR

T+6h (15:00):
  ARCHITECT:
    • Revisa patrón: Aggregate + Repository OK
    • Aprueba PR

T+7h (16:00):
  ORCHESTRATOR:
    • Verifica: todas las approvals presentes
    • Merge PR a main
    • Tag v0.1.0
    • Reporta: "Unit 1 complete, deployed to staging"

Siguiente: Deploy a prod si smoke tests pasan
```

### Scenario 2: Implementación Compleja (Múltiples Units paralelo)

```
Tarea: Sprint 2 (Unit 2 + Unit 6 paralelo)
Duración: 3-4 días

Timeline:

T+0h (Lunes 09:00):
  ORCHESTRATOR:
    • Plan: Unit 2 + Unit 6 como fork-join
    • Asigna ENGINEER-1 → Unit 2
    • Asigna ENGINEER-2 → Unit 6

T+4h (Lunes 13:00):
  ENGINEER-1:
    • Código: Session aggregate, repository
    • Abre PR #101 (Unit 2)
    • MEMORY.md: [IN_PROGRESS]

T+4h (Lunes 13:00):
  ENGINEER-2:
    • Código: AuditLog aggregate, ComplianceService
    • Abre PR #102 (Unit 6)
    • MEMORY.md: [IN_PROGRESS]

T+16h (Martes 01:00 - overnight):
  QA:
    • Ejecuta tests de PR #101: 92% coverage, pass
    • Ejecuta tests de PR #102: 85% coverage, pass
    • Ambas aprobadas

T+20h (Martes 05:00):
  ARCHITECT:
    • Revisa PR #101: aggregate pattern OK
    • Revisa PR #102: service layer OK
    • Ambas aprobadas

T+24h (Martes 09:00):
  ORCHESTRATOR:
    • Ambas PRs listos
    • Merge #101 primero (Unit 2 base)
    • Smoke test: ✓
    • Merge #102 (Unit 6 depende de Unit 2)
    • Smoke test: ✓
    • Tag v0.2.0
    • Reporta: "Unit 2 + Unit 6 complete, ready for E2E"

T+28h (Martes 13:00):
  QA:
    • E2E test: Session creation → Audit logged
    • Valida: audit trail correcto
    • Aprueba: OK for staging

T+32h (Martes 17:00):
  ORCHESTRATOR:
    • Deploy v0.2.0 a staging
    • Smoke tests pass
    • Reporta a usuario: "Ready for manual testing"
```

---

## 9️⃣ Monitoreo y Alertas

### 9.1 Health Checks

```
ORCHESTRATOR monitored:

CADA 1 HORA:
  • git status: pending commits? (no debería haber)
  • PR queue: cuántos PRs abiertos?
  • Test status: últimos tests pasaron?
  • Build status: última imagen en ECR?

DIARIOS (09:00):
  • Coverage trend: ¿aumentó o disminuyó?
  • Performance trend: ¿latencia cambió?
  • Security scan: nuevas vulnerabilidades?
  • Code review lag: PRs esperando review > 4h?

ALERTAS:

🔴 CRITICAL:
  • Cualquier test falla en main
  • Cualquier merge rompe build
  → Acción: ROLLBACK inmediatamente, notificar equipo

🟡 WARNING:
  • PR abierta > 24h sin aprobación
  • Coverage disminuyó > 2%
  → Acción: Priorizar review, investigar

🟢 INFO:
  • PR merged
  • Test suite ejecutado
  → Log para MEMORY.md
```

---

## 🔟 Resumen de Roles

### ORCHESTRATOR:
- ✅ Lee requirements, crea plan
- ✅ Asigna work a agentes
- ✅ Sincroniza progreso vía MEMORY.md
- ✅ Merge PRs en orden topológico
- ✅ Tag releases, actualiza CHANGELOG.md
- ✅ Reporta status al usuario
- ❌ No codifica (asigna a ENGINEER)
- ❌ No valida tests (asigna a QA)

### ENGINEER:
- ✅ Codifica features (TDD)
- ✅ Escribe unit + integration tests
- ✅ Abre PR con descripción clara
- ✅ Responde code review feedback
- ✅ Actualiza MEMORY.md [IN_PROGRESS]
- ❌ No ejecuta QA tests (deja a QA)
- ❌ No mergea (ORCHESTRATOR)

### QA:
- ✅ Ejecuta test suite (pytest, jest)
- ✅ Verifica coverage > 80%
- ✅ Ejecuta security scan (bandit, npm audit)
- ✅ Valida perf (Lighthouse, load test)
- ✅ Aprueba PR si todo OK
- ✅ Actualiza MEMORY.md [APPROVED]
- ❌ No codifica features (codifica tests)

### ARCHITECT:
- ✅ Revisa patrón de código
- ✅ Valida contra DESIGN.md
- ✅ Escribe ADRs si es necesario
- ✅ Aprueba PR si arquitectura OK
- ✅ Actualiza MEMORY.md [APPROVED]
- ❌ No codifica features
- ❌ No mergea PRs

---

## 📊 Resumen

```
MATRIZ DE ORQUESTACIÓN:

┌───────────────────────────────────────┐
│ WORKFLOW COORDINADO                   │
├───────────────────────────────────────┤
│                                       │
│ 1. ORCHESTRATOR → Plan                │
│ 2. ENGINEER ↔ ARCHITECT → Code review │
│ 3. QA → Validación                    │
│ 4. ORCHESTRATOR → Integrate & release │
│                                       │
│ Context: MEMORY.md                    │
│ Sync: git pull/push                   │
│ State: [PLANNING→IN_PROGRESS→...      │
│        ...APPROVED→DEPLOYED]          │
│                                       │
│ Status: ✅ READY FOR EXECUTION        │
│                                       │
└───────────────────────────────────────┘
```

---

**Especificación creada**: 2026-05-27  
**Responsable**: ORCHESTRATOR Agent  
**Estación 6 Status**: ✅ **COMPLETADA** (4/4 artefactos)

Artefactos entregados:
1. ✅ HARNESS-SPECIFICATION.md (Claude Code, Opus 4.7, Anthropic API)
2. ✅ AGENTS.md (ORCHESTRATOR, ENGINEER, QA, ARCHITECT)
3. ✅ VALIDATION-FRAMEWORK.md (Testing, Security, Performance, Accessibility, Compliance)
4. ✅ ORCHESTRATION-PLAN.md (Workflows, scheduling, coordination)

**Próximo paso**: Estación 7 (Implementation execution)
