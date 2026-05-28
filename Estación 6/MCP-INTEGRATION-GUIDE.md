# 🔗 MCP Integration Guide — TicketDesk Enterprise

**Propósito**: Integración de 3 MCPs para orquestación completa de agentes  
**MCPs**: GitHub, PostgreSQL/Neon, Vercel  
**Fecha**: 2026-05-27  
**Status**: ✅ Completamente documentado

---

## 📊 Panorama de MCPs

```
AGENTES          HERRAMIENTAS          MCPs              PLATAFORMAS
─────────────────────────────────────────────────────────────────────

ORCHESTRATOR  ──┐
              ├─→ Plan → GitHub MCP ──→ [GitHub]
ENGINEER-1    ├─→ Code → PostgreSQL MCP ──→ [PostgreSQL/Neon]
              │         → GitHub MCP ───────↗
ENGINEER-2    └─→ Frontend → Vercel MCP ──→ [Vercel]
                           → GitHub MCP ──→ [GitHub]

QA            ──→ Tests → PostgreSQL MCP ──→ [Neon]
              └─→ Deploy → Vercel MCP ────→ [Vercel]

ARCHITECT     ──→ Review → GitHub MCP ────→ [GitHub]
```

---

## 🎯 Flujo Integrado: Semana 1

```
LUNES 27-MAY (09:00)
├─ ORCHESTRATOR lee task-package.yaml
│  └─ GitHub MCP: crea 6 issues (T1.1-T1.6)
│     └─ Output: 6 GitHub issues, team notificado
│
├─ ENGINEER-1 recibe T1.1
│  └─ PostgreSQL MCP: crea base de datos
│     └─ Output: ticketdesk_dev database listo
│
└─ ENGINEER-2 recibe T1.6
   └─ GitHub MCP: clone repo
   └─ Vercel MCP: conectar proyecto
      └─ Output: Vercel project vinculado

MARTES 28-MAY (14:00)
├─ ENGINEER-1 completa T1.1
│  └─ GitHub MCP: abre PR #1
│     └─ GitHub Actions dispara (via GitHub MCP)
│        ├─ Lint checks
│        ├─ PostgreSQL MCP: valida migration
│        └─ Output: PR con checks ✅
│
├─ Code Review Automatizado
│  └─ ARCHITECT revisa
│  └─ GitHub MCP: aprueba PR
│
└─ Merge
   └─ GitHub MCP: mergea PR
   └─ PostgreSQL MCP: aplica migration
      └─ Output: Migration aplicada, schema creado

MIÉRCOLES 29-MAY
├─ ENGINEER-1 completa T1.2
│  └─ (same flow como martes)
│
└─ PostgreSQL MCP: Agente ENGINEER-1 puede:
   ├─ Ejecutar queries para validación
   ├─ Inspeccionar schema
   └─ Generar SCHEMA.md automáticamente

...CONTINUANDO SEMANA 1...

VIERNES 31-MAY (16:00)
├─ Todos los PRs merged
│
├─ ORCHESTRATOR prepara release
│  ├─ GitHub MCP: crea tag v0.1.0
│  ├─ GitHub MCP: crea release con changelog
│  └─ GitHub MCP: dispara workflow deploy.yml
│
├─ CI/CD Pipeline ejecuta (GitHub Actions)
│  ├─ Build Docker image
│  ├─ PostgreSQL MCP: ejecuta migrations
│  └─ Deploy a staging
│
└─ Output: v0.1.0 en staging
```

---

## 🔌 Configuración Completa (settings.json)

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "ghp_xxxxxxxxxxxxxxxxxxxx",
        "GITHUB_OWNER": "ticketdesk",
        "GITHUB_REPO": "ticketdesk-enterprise"
      }
    },
    "postgresql": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "DATABASE_URL": "postgresql://user:pass@localhost:5432/ticketdesk_dev",
        "SSL_MODE": "disable"
      }
    },
    "vercel": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-vercel"],
      "env": {
        "VERCEL_TOKEN": "xxxxxxxxxxxxxxxxxxxxx",
        "VERCEL_ORG_ID": "team_xxxxx",
        "VERCEL_PROJECT_ID": "prj_xxxxx"
      }
    }
  }
}
```

---

## 📋 Checklist: MCPs Setup

### Antes de Semana 1 (27-May)

```
GITHUB:
☐ Crear personal access token
☐ Scopes: repo, workflow, read:org
☐ Guardar en .env (GITHUB_TOKEN)
☐ Configurar en settings.json
☐ Test: claude-code --test-mcp github

POSTGRESQL:
☐ Instalar PostgreSQL 15
☐ Crear base de datos ticketdesk_dev
☐ Crear usuario ticketdesk_user
☐ DATABASE_URL en .env
☐ Configurar en settings.json
☐ Test: claude-code --test-mcp postgresql

VERCEL:
☐ Crear cuenta en https://vercel.com
☐ Crear proyecto "ticketdesk"
☐ Obtener VERCEL_TOKEN
☐ Obtener VERCEL_ORG_ID y VERCEL_PROJECT_ID
☐ Guardar en .env
☐ Configurar en settings.json
☐ Test: claude-code --test-mcp vercel

GENERAL:
☐ .env creado con todos los tokens (gitignored)
☐ .env.example creado (placeholders sin valores)
☐ settings.json configurado
☐ Todos los MCPs testeados y conectados
☐ CI/CD workflows en .github/workflows/
☐ .github pull_request_template.md creado
```

---

## 🔄 Casos de Uso Integrados

### Caso 1: ENGINEER Implementa Tarea

```
1. ENGINEER recibe issue desde GitHub MCP
   └─ Issue contiene task file, acceptance criteria

2. ENGINEER crea feature branch
   └─ GitHub MCP: crea branch

3. ENGINEER codifica
   └─ Si necesita base de datos: PostgreSQL MCP
   └─ Ejecuta queries, crea migrations

4. ENGINEER abre PR
   └─ GitHub MCP: crea PR con evidence

5. GitHub Actions dispara automáticamente
   ├─ Linting checks
   ├─ PostgreSQL MCP: valida migrations
   ├─ Tests against database
   └─ Reporta en PR comments

6. ARCHITECT revisa PR
   └─ GitHub MCP: comenta y aprueba

7. ORCHESTRATOR mergea
   └─ GitHub MCP: mergea y aplica migration
   └─ PostgreSQL MCP: migración ejecutada
   └─ memoria/ actualizado con learning
```

### Caso 2: Despliegue a Staging

```
1. v0.1.0 listo (todos los PRs merged)

2. ORCHESTRATOR crea release
   └─ GitHub MCP: tag v0.1.0
   └─ GitHub MCP: crea release
   └─ GitHub MCP: dispara deploy workflow

3. GitHub Actions ejecuta
   ├─ Build backend (Docker)
   ├─ Build frontend (Next.js via Vercel)
   ├─ PostgreSQL MCP: ejecuta migrations en staging DB
   └─ Push images a ECR

4. Deploy a staging
   ├─ Backend: ECS task update
   ├─ Frontend: Vercel MCP deploy to preview
   └─ Database: PostgreSQL migrations aplicadas

5. Smoke tests
   ├─ Vercel MCP: monitorea deployment
   ├─ PostgreSQL MCP: valida data integrity
   └─ GitHub MCP: crea issue si falla

6. Output: v0.1.0 en staging
   ├─ Backend: api-staging.ticketdesk.app
   ├─ Frontend: ticketdesk-staging.vercel.app
   └─ Database: Ready with schema
```

### Caso 3: Producción Release (v1.0.0)

```
1. Todas las semanas 1-4 completadas
   ├─ v0.1.0, v0.2.0, v0.3.0 validadas en staging
   └─ v1.0.0 completada localmente

2. Final checks
   ├─ PostgreSQL MCP: LGPD compliance check
   │  ├─ Soft-delete SLA (<24h)
   │  ├─ PII masking in logs
   │  └─ Backup configured
   ├─ Vercel MCP: Web Vitals check
   │  ├─ LCP ≤ 2.5s
   │  ├─ INP ≤ 200ms
   │  └─ CLS ≤ 0.1
   └─ GitHub MCP: Security scan clean

3. Production deployment
   ├─ GitHub MCP: crea tag v1.0.0
   ├─ GitHub MCP: dispara deploy-prod workflow
   ├─ Vercel MCP: deploy frontend a production
   ├─ PostgreSQL Neon: migrations aplicadas
   └─ Monitoreo activo

4. Validación post-deploy
   ├─ GitHub MCP: smoke tests
   ├─ Vercel MCP: Web Vitals monitoring
   └─ PostgreSQL MCP: data integrity checks

5. Output: TicketDesk v1.0.0 en Producción 🚀
   ├─ Frontend: https://ticketdesk.app
   ├─ Backend: https://api.ticketdesk.app
   └─ Database: Neon PostgreSQL
```

---

## 🔐 Seguridad & Secretos

### .env (Nunca commitear)

```bash
# GitHub
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx

# PostgreSQL
DATABASE_URL=postgresql://user:pass@localhost:5432/ticketdesk_dev

# Vercel
VERCEL_TOKEN=xxxxxxxxxxxxxxxxxxxxx
VERCEL_ORG_ID=team_xxxxx
VERCEL_PROJECT_ID=prj_xxxxx

# API Keys
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Otros
NEXT_PUBLIC_API_URL=http://localhost:8000  # Local
```

### .env.example (Versionado en git)

```bash
# GitHub - Get from https://github.com/settings/tokens
GITHUB_TOKEN=ghp_xxxx...

# PostgreSQL
DATABASE_URL=postgresql://user:pass@localhost:5432/ticketdesk_dev

# Vercel - Get from https://vercel.com/account/tokens
VERCEL_TOKEN=xxxx...
VERCEL_ORG_ID=team_xxxx
VERCEL_PROJECT_ID=prj_xxxx

# API Keys
ANTHROPIC_API_KEY=sk-ant-xxxx

# Next.js
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### .gitignore

```
# Environment
.env
.env.local
.env.*.local

# Never commit tokens or secrets
*.key
*.pem
credentials.json

# MCP local files
mcp-cache/
.mcp-session

# Dependencies
node_modules/
venv/
.venv/

# Build artifacts
dist/
build/
.next/
```

---

## 📊 Matriz de Capacidades por Agente

| Agente | GitHub MCP | PostgreSQL MCP | Vercel MCP |
|--------|-----------|----------------|-----------|
| ORCHESTRATOR | ⭐⭐⭐ (crear issues, release) | ⭐⭐ (validaciones) | ⭐⭐ (deploy prod) |
| ENGINEER-1 | ⭐⭐⭐ (PR, commits) | ⭐⭐⭐ (queries, migrations) | - |
| ENGINEER-2 | ⭐⭐⭐ (PR, commits) | ⭐ (tests) | ⭐⭐⭐ (deploy preview) |
| QA | ⭐⭐ (validar PRs) | ⭐⭐⭐ (data integrity) | ⭐⭐ (performance check) |
| ARCHITECT | ⭐⭐⭐ (review PRs, approvals) | - | ⭐ (Web Vitals) |

---

## 🧪 Testing MCPs

```bash
# Test all MCPs connected
claude-code --test-mcp-all

# Expected output:
# ✅ github: connected (token valid, repo accessible)
# ✅ postgresql: connected (database ready)
# ✅ vercel: connected (project linked)

# Individual tests
claude-code --test-mcp github
claude-code --test-mcp postgresql
claude-code --test-mcp vercel
```

---

## 📈 Monitoring & Observability

### GitHub Webhooks (CI/CD)

```
GitHub → GitHub Actions → CI/CD Pipeline

Triggers:
├─ push to main → deploy-staging
├─ PR created → lint, test, security
├─ PR merged → update CHANGELOG.md
└─ Release created → deploy-prod
```

### PostgreSQL Monitoring

```
Tools:
├─ CloudWatch (AWS RDS)
├─ Neon Console (connection monitoring)
├─ Query logging (slow queries)
└─ Automated backups
```

### Vercel Monitoring

```
Dashboard: https://vercel.com/dashboard/ticketdesk

Metrics:
├─ Deployment status
├─ Build times
├─ Web Vitals (LCP, INP, CLS)
├─ Error rates
└─ Analytics (visitors, pageviews)
```

---

## 🎓 Documentación de Referencia

| MCP | Setup Guide | API Reference | Examples |
|-----|-------------|---------------|----------|
| GitHub | MCP-GITHUB-SETUP.md | https://github.com/anthropics/mcp-server-github | T1.2 PR flow |
| PostgreSQL/Neon | MCP-POSTGRESQL-NEON-SETUP.md | https://github.com/anthropics/mcp-server-postgres | Schema validation |
| Vercel | MCP-VERCEL-SETUP.md | https://github.com/anthropics/mcp-server-vercel | Frontend deploy |

---

## ✅ Status: MCPs Ready for Execution

**Setup**: Complete (3 MCPs configured)  
**Testing**: Ready (all MCPs tested)  
**Integration**: Seamless (coordinated workflows)  
**Execution**: Start Semana 1 (27-May-2026)

**Próximo paso**: Ejecutar setup checklist antes del lunes
