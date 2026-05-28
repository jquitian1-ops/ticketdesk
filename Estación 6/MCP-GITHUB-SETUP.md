# 🔌 MCP: GitHub Integration para TicketDesk

**Protocol**: Model Context Protocol  
**Propósito**: Acceso estructurado a GitHub desde agentes Claude  
**Herramientas**: Issues, PRs, Repos, Commits, Workflows  
**Plataforma**: TicketDesk Enterprise v1.0  
**Fecha**: 2026-05-27

---

## Resumen

El MCP de GitHub permite a los agentes:
- ✅ Crear issues (tareas de GitHub)
- ✅ Listar y actualizar PRs
- ✅ Ejecutar GitHub Actions workflows
- ✅ Acceder a commits y git history
- ✅ Crear/actualizar releases
- ✅ Validar PRs contra requirements

---

## Configuración Local (settings.json)

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-github"
      ],
      "env": {
        "GITHUB_TOKEN": "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "GITHUB_OWNER": "ticketdesk",
        "GITHUB_REPO": "ticketdesk-enterprise"
      }
    }
  }
}
```

### Obtener GITHUB_TOKEN

```bash
# 1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
# 2. Crear nuevo token con scopes:
#    - repo (full control of private repositories)
#    - workflow (actions)
#    - read:org (read organization data)

# 3. Copiar token y guardar en .env:
echo "GITHUB_TOKEN=ghp_xxxx" >> .env

# 4. Cargar en Claude settings.json
# IMPORTANT: Nunca commit GITHUB_TOKEN a git
echo ".env" >> .gitignore
```

---

## Herramientas Disponibles

### 1. Crear Issue

```python
# El agente puede hacer:
create_github_issue(
    title="T1.2 User Aggregate + Repository",
    body="""
    ## Task Details
    Implementar User aggregate y UserRepository
    
    ## Acceptance Criteria
    - [ ] User aggregate implementado
    - [ ] CRUD operations funciona
    - [ ] Tests: >90% coverage
    - [ ] Security: bcrypt 12 rounds
    
    ## Related
    - Milestone: M1 (Auth & Compliance)
    - Task: T1.2
    """,
    labels=["unit-1", "backend", "critical"],
    milestone="M1",
    assignee="ENGINEER-1"
)

# Resultado: GitHub issue creada automáticamente
# URL: github.com/ticketdesk/ticketdesk-enterprise/issues/42
```

### 2. Crear PR

```python
create_github_pr(
    title="feat(T1.2) User Aggregate + Repository",
    base="main",
    head="feature/unit1-user-aggregate",
    body="""
    # Task T1.2 Completion
    
    ## Evidence
    ✅ Tests: 20/20 passing (92% coverage)
    ✅ Security: bandit clean, bcrypt 12 rounds
    ✅ Performance: <100ms per operation
    
    ## Acceptance Criteria
    - [x] User aggregate implemented
    - [x] Repository pattern
    - [x] Tests complete
    
    Closes #42
    """,
    labels=["unit-1", "backend"],
    assignees=["ENGINEER-1"],
    reviewers=["ARCHITECT"]
)

# Resultado: PR creada, reviewers notificados
# URL: github.com/ticketdesk/ticketdesk-enterprise/pull/123
```

### 3. Actualizar PR Status

```python
# Después de aprobación:
update_github_pr(
    pr_number=123,
    state="merged",  # o "closed"
    comment="""
    ✅ Merged by ORCHESTRATOR
    
    Evidence verified:
    - Tests: 20/20 ✅
    - Coverage: 92% ✅
    - Security: clean ✅
    
    Releasing v0.1.0
    """
)
```

### 4. Ejecutar Workflow

```python
# Disparar CI/CD pipeline:
trigger_github_workflow(
    workflow_file=".github/workflows/deploy.yml",
    ref="main",
    inputs={
        "environment": "staging",
        "version": "v0.1.0"
    }
)

# Resultado: GitHub Actions ejecuta 6-stage pipeline
# Status reportado al agente en tiempo real
```

### 5. Crear Release

```python
create_github_release(
    tag="v0.1.0",
    name="TicketDesk Enterprise v0.1.0 — Auth & Compliance",
    body="""
    ## Release v0.1.0
    **Release Date**: 2026-05-31
    
    ### What's New
    - Unit 1: Account Management (User, RBAC)
    - Unit 6: Compliance (Audit Logging)
    - 70+ tests, 88% coverage
    
    ### Assets
    - [Docker image: ticketdesk:v0.1.0](...)
    - [Database schema](...)
    
    ### Next Release
    v0.2.0 (Unit 2: Session Management) — June 7
    """,
    draft=False,
    prerelease=False,
    target_commitish="main"
)

# Resultado: Release visible en GitHub releases page
# Assets adjuntados automáticamente
```

### 6. Leer Issue/PR

```python
# Agente lee requirements:
issue = read_github_issue(issue_number=42)

print(issue.title)           # "T1.2 User Aggregate..."
print(issue.body)            # Full requirement text
print(issue.labels)          # ["unit-1", "backend", "critical"]
print(issue.state)           # "open" o "closed"
print(issue.assignees)       # ["ENGINEER-1"]

# Usa para validar que task está completa:
if "Acceptance Criteria" in issue.body:
    criteria = parse_acceptance_criteria(issue.body)
    validate_against_criteria(code, criteria)
```

### 7. Listar PRs

```python
# Revisar progreso:
prs = list_github_prs(
    state="open",
    labels=["unit-1"],
    sort="updated"
)

for pr in prs:
    print(f"{pr.number}: {pr.title} ({pr.reviews_approved}/{pr.reviews_required})")
    
# Output:
# 123: feat(T1.2) User Aggregate (1/1) ✅ Ready to merge
# 124: feat(T1.3) Auth Service (0/1) 🟡 Pending review
```

---

## Flujo de Ejecución con MCP GitHub

### Semana 1 - ORCHESTRATOR

```python
# LUNES 27-MAY (09:00)
# ORCHESTRATOR publica tareas desde task-package.yaml

from mcp_github import create_github_issue

tasks = load_task_package("docs/tasks/task-package.yaml")

for task in tasks[:6]:  # T1.1 - T1.6
    issue = create_github_issue(
        title=f"[{task.id}] {task.title}",
        body=render_task_as_markdown(task),
        labels=task.labels,
        milestone=task.milestone,
        assignee=task.assignee
    )
    
    print(f"✅ Created issue #{issue.number}: {task.title}")
    
    # Actualizar task-package.yaml con issue number
    update_task_with_github_issue(task.id, issue.number)

# Resultado: 6 issues en GitHub, equipo recibe notificaciones
```

### Durante Semana 1 - ENGINEER

```python
# ENGINEER-1 implementa T1.2, abre PR

from mcp_github import create_github_pr, update_github_pr

# Después de completar la tarea:
pr = create_github_pr(
    title="feat(T1.2) User Aggregate + Repository",
    base="main",
    head="feature/unit1-user-aggregate",
    body=render_pr_evidence(
        tests_passed=20,
        coverage=92,
        security_scan_clean=True,
        performance_acceptable=True
    )
)

print(f"✅ PR created: #{pr.number}")

# ARCHITECT revisa y aprueba
# CODE-REVIEW-SETUP ejecuta checks automáticamente (via GitHub Actions)
# ARCHITECT comenta: "Looks good, merging"

# ORCHESTRATOR mergea:
update_github_pr(
    pr_number=pr.number,
    state="merged",
    comment="✅ Merged after validation"
)
```

### Viernes - ORCHESTRATOR

```python
# VIERNES 31-MAY (16:00)
# ORCHESTRATOR prepara v0.1.0

from mcp_github import create_github_release, trigger_github_workflow

# 1. Tag release
release = create_github_release(
    tag="v0.1.0",
    name="v0.1.0 — Unit 1 + Unit 6",
    body=generate_changelog_from_merged_prs(
        from_tag=None,  # Initial release
        to_ref="main"
    )
)

print(f"✅ Release {release.tag_name} created")

# 2. Trigger deploy workflow
workflow = trigger_github_workflow(
    workflow_file=".github/workflows/deploy.yml",
    inputs={"environment": "staging", "version": "v0.1.0"}
)

print(f"✅ Workflow triggered: {workflow.id}")
print(f"Monitor: github.com/ticketdesk/.../actions/{workflow.id}")
```

---

## GitHub Actions Integration

### Workflows Disparables desde MCP

```yaml
# .github/workflows/deploy.yml

name: Deploy

on:
  workflow_dispatch:
    inputs:
      environment:
        type: choice
        options: [staging, production]
      version:
        type: string
        description: "Version to deploy (v0.1.0, v0.2.0)"

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Lint
        run: black --check . && pylint src/

  test:
    runs-on: ubuntu-latest
    steps:
      - name: Tests
        run: pytest --cov=src

  build:
    runs-on: ubuntu-latest
    steps:
      - name: Build Docker image
        run: docker build -t ticketdesk:${{ inputs.version }} .

  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to ${{ inputs.environment }}
        run: |
          if [ "${{ inputs.environment }}" == "staging" ]; then
            aws ecs update-service --cluster staging --service ticketdesk-backend --force-new-deployment
          else
            aws ecs update-service --cluster prod --service ticketdesk-backend --force-new-deployment
          fi
```

### Agente Monitorea Workflow

```python
# ORCHESTRATOR espera a que workflow complete:

workflow_run = trigger_github_workflow(
    workflow_file=".github/workflows/deploy.yml",
    inputs={"environment": "staging", "version": "v0.1.0"}
)

# Poll hasta que complete
while True:
    status = get_workflow_run_status(workflow_run.id)
    
    if status == "completed":
        if status.conclusion == "success":
            print("✅ Deploy successful")
            break
        else:
            print(f"❌ Deploy failed: {status.failure_reason}")
            rollback()
            break
    
    print(f"⏳ Still running: {status.name}")
    time.sleep(30)
```

---

## Seguridad & Permisos

```
GITHUB TOKEN SCOPES REQUERIDOS:

✅ repo              — Acceso a private repos
✅ workflow          — Leer/escribir GitHub Actions
✅ read:org          — Leer organización data
✅ read:discussion   — Leer discussions
✅ write:discussion  — Escribir discussions (optional)

NO NECESARIO:
❌ admin:repo_hook
❌ delete_repo
❌ gist
```

---

## Validación & Testing

```bash
# Test MCP GitHub connection:
claude-code --test-mcp github

# Expected output:
# ✅ GitHub MCP connected
# ✅ Token valid
# ✅ Repo accessible
# ✅ Workflow available

# Create test issue:
gh issue create \
  --title "Test issue from MCP" \
  --body "Automated test" \
  --label "test"

# List issues:
gh issue list --limit 10
```

---

## Status: ✅ MCP GitHub Ready for Implementation

**Siguiente**: Configurar antes de Semana 1 (27-May-2026)
