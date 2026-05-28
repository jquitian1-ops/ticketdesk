# 🚀 MCP: Vercel Integration para TicketDesk Frontend

**Protocol**: Model Context Protocol  
**Platform**: Vercel (Serverless deployment)  
**Propósito**: Deploy automático del frontend Next.js desde agentes  
**Framework**: Next.js 14  
**Fecha**: 2026-05-27

---

## Resumen

El MCP de Vercel permite a los agentes:
- ✅ Deployer frontend a staging/production
- ✅ Monitorear build status y logs
- ✅ Crear preview deployments de PRs
- ✅ Gestionar environment variables
- ✅ Monitorear Core Web Vitals
- ✅ Configurar redirects y rewrites

---

## Setup: Vercel Project

### 1. Crear Proyecto Vercel

```bash
# Opción A: Via Vercel CLI
vercel login
vercel link

# Seleccionar:
# ✅ Link existing project? → No
# ✅ Project name: → ticketdesk
# ✅ Framework: → Next.js
# ✅ Root directory: → ./frontend

# Opción B: Via Vercel Dashboard (https://vercel.com)
# New Project → GitHub (ticketdesk-enterprise) → Select "frontend" folder
```

### 2. Obtener API Token

```bash
# Vercel Settings → Tokens → Create Token
# Scopes: 
#   ✅ Read Deployments
#   ✅ Write Deployments
#   ✅ Production Deployments
#   ✅ Read Environment Variables
#   ✅ Write Environment Variables

# Guardar en .env (nunca en git)
VERCEL_TOKEN=xxxxxxxxxxxxxxxxxxxxx
VERCEL_PROJECT_ID=prj_xxxxxxxxxxxxx
VERCEL_ORG_ID=team_xxxxxxxxxxxxx  # Si es team, sino user
```

---

## Configuración MCP (settings.json)

```json
{
  "mcpServers": {
    "vercel": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-vercel"
      ],
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

## Herramientas Disponibles

### 1. Deployer a Staging

```python
# Frontend completado, ENGINEER listo para desplegar

from mcp_vercel import create_deployment, monitor_deployment

deployment = create_deployment(
    environment="staging",
    ref="main",  # Branch
    version="0.4.0",
    env_vars={
        "NEXT_PUBLIC_API_URL": "https://api-staging.ticketdesk.app",
        "NEXT_PUBLIC_ENVIRONMENT": "staging"
    }
)

print(f"✅ Deployment created: {deployment.id}")
print(f"🔗 URL: {deployment.url}")

# Monitor until complete
status = monitor_deployment(
    deployment_id=deployment.id,
    timeout_seconds=600  # 10 minutes max
)

if status == "READY":
    print("✅ Deployment successful")
    print(f"Available at: {deployment.url}")
else:
    print(f"❌ Deployment failed: {status}")
```

### 2. Preview Deployment para PR

```python
# Cuando ENGINEER abre PR con frontend changes

from mcp_vercel import create_preview_deployment

pr_number = 123

preview = create_preview_deployment(
    ref=f"refs/pull/{pr_number}/merge",
    comment_on_pr=True,
    metadata={
        "pr_number": pr_number,
        "author": "ENGINEER-2",
        "feature": "Candidate Chat Component"
    }
)

# Output: Vercel crea preview URL y comenta en PR
# "Deployment preview ready: https://ticketdesk-pr-123.vercel.app"
```

### 3. Monitorear Web Vitals

```python
# Después de deployment

from mcp_vercel import get_web_vitals

vitals = get_web_vitals(
    deployment_id="deployment_id",
    time_period="last_7d"
)

print(f"LCP: {vitals.lcp}s (target: ≤2.5s)")
print(f"INP: {vitals.inp}ms (target: ≤200ms)")
print(f"CLS: {vitals.cls} (target: ≤0.1)")

# Validar contra Core Web Vitals target
if vitals.lcp > 2.5 or vitals.inp > 200 or vitals.cls > 0.1:
    print("⚠️ Web Vitals degraded, investigate")
    rollback_deployment(deployment_id)
else:
    print("✅ Web Vitals target met")
```

### 4. Gestionar Environment Variables

```python
# Setup variables para producción

from mcp_vercel import set_env_var, get_env_vars

# Set para staging
set_env_var(
    name="NEXT_PUBLIC_API_URL",
    value="https://api-staging.ticketdesk.app",
    environments=["preview", "development"]
)

# Set para producción
set_env_var(
    name="NEXT_PUBLIC_API_URL",
    value="https://api.ticketdesk.app",
    environments=["production"]
)

# Listar todas las variables
env_vars = get_env_vars()
for var in env_vars:
    print(f"{var.name} = {var.value_masked}")
```

### 5. Crear Production Deployment

```python
# Semana 4: Deploy v1.0.0 a producción

from mcp_vercel import create_deployment, create_release

# 1. Build y deploy
production_deployment = create_deployment(
    environment="production",
    ref="v1.0.0",  # Tagged release
    version="1.0.0",
    production=True
)

# 2. Wait for completion
monitor_deployment(
    deployment_id=production_deployment.id,
    timeout_seconds=900,
    auto_rollback=True  # Rollback si falla
)

# 3. Crear release record
release = create_release(
    version="1.0.0",
    deployment_id=production_deployment.id,
    notes="TicketDesk Enterprise v1.0.0 — Production Release"
)

print(f"✅ v1.0.0 deployed to production")
print(f"🌍 Available at: https://ticketdesk.app")
```

### 6. Rollback

```python
# Si algo sale mal post-deploy

from mcp_vercel import rollback_to_previous

rollback = rollback_to_previous(
    environment="production",
    reason="Critical bug detected in payment flow"
)

print(f"✅ Rolled back to: {rollback.previous_version}")
print(f"Deployment ID: {rollback.previous_deployment_id}")
```

---

## Flujo Integrado: Semana 4

### ENGINEER-2: T4.1-T4.3 (Frontend)

```python
# LUNES 17-JUNE
# ENGINEER-2 completa Unit 5 frontend

# Después de local testing:
# 1. Push a feature branch
git push origin feature/unit5-frontend

# 2. GitHub detecta PR → Vercel crea preview automáticamente
# (via webhook en .github/workflows/ o Vercel GitHub App)

# Output en PR:
# "Deployment preview ready: https://ticketdesk-pr-456.vercel.app"
```

### QA: T4.4 (E2E Testing)

```python
# QA ejecuta E2E tests contra preview deployment

from mcp_vercel import get_deployment_url

preview_url = get_deployment_url(pr_number=456)
# → https://ticketdesk-pr-456.vercel.app

# Playwright E2E tests apuntan a preview
# tests/e2e/candidate-flow.spec.ts
test('Candidate can answer interview questions', async ({ page }) => {
    await page.goto(preview_url + '/candidate/session/123')
    // ...
})

# Si todo pasa:
# ✅ E2E tests pass against preview
# → PR aprobado

# Si falla:
# ❌ E2E tests fail
# → Requer changes a ENGINEER-2
# → ENGINEER-2 fixea y push
# → Vercel redeploy automático
```

### ORCHESTRATOR: Release v1.0.0

```python
# VIERNES 23-JUNE (14:00)
# Todas las PRs merged, listo para producción

from mcp_vercel import create_deployment

# 1. Crear production deployment desde tag v1.0.0
prod = create_deployment(
    environment="production",
    ref="v1.0.0",
    production=True,
    env_vars={
        "NEXT_PUBLIC_API_URL": "https://api.ticketdesk.app",
        "NEXT_PUBLIC_ENVIRONMENT": "production"
    }
)

# 2. Monitor deployment
status = monitor_deployment(
    deployment_id=prod.id,
    auto_rollback=True  # Rollback automático si falla
)

# 3. Si success:
if status == "READY":
    # Validar Web Vitals
    vitals = get_web_vitals(deployment_id=prod.id)
    
    if vitals.lcp <= 2.5 and vitals.inp <= 200 and vitals.cls <= 0.1:
        print("✅ v1.0.0 deployed to production")
        print(f"LCP: {vitals.lcp}s, INP: {vitals.inp}ms, CLS: {vitals.cls}")
        
        # Update DNS si aplica
        update_dns_to_production()
    else:
        print("⚠️ Web Vitals degraded, rollback")
        rollback_to_previous(environment="production")
else:
    print("❌ Deployment failed, rollback")
```

---

## Configuración Avanzada

### vercel.json

```json
{
  "projectName": "ticketdesk",
  "framework": "nextjs",
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "env": [
    "NEXT_PUBLIC_API_URL",
    "NEXT_PUBLIC_ENVIRONMENT"
  ],
  "git": {
    "deploymentEnabled": {
      "main": true,
      "develop": true
    }
  },
  "headers": [
    {
      "source": "/:path*",
      "headers": [
        {
          "key": "Content-Security-Policy",
          "value": "default-src 'self'; script-src 'self' 'unsafe-inline' https://analytics.example.com"
        },
        {
          "key": "X-Frame-Options",
          "value": "DENY"
        },
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        }
      ]
    }
  ],
  "redirects": [
    {
      "source": "/old-path",
      "destination": "/new-path",
      "permanent": true
    }
  ],
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://api-staging.ticketdesk.app/:path*"
    }
  ]
}
```

### Performance Budget

```json
{
  "buildCommand": "npm run build && npm run analyze",
  "analysisReport": {
    "enabled": true,
    "outputPath": "analysis"
  }
}
```

---

## Monitoreo & Analytics

### Vercel Analytics Dashboard

```
https://vercel.com/dashboard/ticketdesk

Metrics:
├─ Deployments (history, status)
├─ Web Vitals (LCP, INP, CLS)
├─ Requests (latency, bandwidth)
├─ Build times (duration trends)
├─ Error rate (4xx, 5xx)
└─ Analytics (page views, visitors)

Alerts:
├─ Failed deployment
├─ Web Vitals degraded
├─ Error rate spike
└─ Build time >5 minutes
```

---

## Security & Compliance

### Production Checklist

```bash
☐ Domain con SSL/TLS (auto en Vercel)
☐ CORS configurado en API
☐ CSP headers presentes
☐ HTTPS redirect habilitado
☐ Environment variables mascaradas
☐ Rate limiting en API
☐ LGPD compliance (si datos)
☐ Backup strategy
☐ Incident response plan

# Validar configuración
curl -I https://ticketdesk.app

# Expected headers:
# Strict-Transport-Security: max-age=31536000
# Content-Security-Policy: ...
# X-Frame-Options: DENY
```

---

## Cost Estimation

```
VERCEL PRICING:

Pro Plan: $20/month

Included:
- Unlimited deployments
- Serverless Functions
- Edge Network
- Analytics
- 100 GB bandwidth/month

TICKETDESK EXPECTED:
- Builds: 20-30/month (cost: free tier)
- Bandwidth: 10-20 GB/month
- Serverless: minimal usage

MONTHLY COST: $20

Escalation (100K+ users):
- Additional bandwidth: $0.50/GB
- Edge Functions: $0.50/10M invocations
```

---

## Testing MCP Vercel

```bash
# Health check
claude-code --test-mcp vercel

# Expected:
# ✅ Vercel connected
# ✅ Token valid
# ✅ Project: ticketdesk
# ✅ Team/Org accessible

# List deployments
vercel deployments

# Get preview URL
vercel preview

# Manual deploy (test)
vercel deploy --prod
```

---

## Status: ✅ MCP Vercel Ready

**Staging**: Configurado para Week 2+  
**Production**: Configurado para Week 4  
**Preview**: Automático en cada PR (via GitHub App)
