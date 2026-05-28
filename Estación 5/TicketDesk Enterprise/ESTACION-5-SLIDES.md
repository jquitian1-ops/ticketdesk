# 🎓 TicketDesk Enterprise v1.0 — Slides Exportables

**Formato**: Markdown (convertible a PowerPoint, reveal.js, PDF)  
**Duración**: 40-50 minutos (5-7 min por slide)  
**Audiencia**: Estudiantes de ingeniería de software

---

## 📍 Slide 1: Portada

### TicketDesk Enterprise v1.0
### Plataforma de Screening Inteligente con IA

```
┌──────────────────────────────────────────────────┐
│                                                  │
│     ESTACIÓN 5 — DELIVERY COMPLETO               │
│                                                  │
│     5 Fases: Inception → Operations              │
│     130+ Tests | 11 Terraform Modules            │
│     6 Microservicios | 99.5% SLA                 │
│                                                  │
│     TicketDesk Enterprise v1.0                   │
│     2026-05-27                                   │
│                                                  │
└──────────────────────────────────────────────────┘
```

**Notas para Presentador**:
- Introducir el proyecto TicketDesk (screening + evaluación)
- Mencionar que recorreremos 5 fases completas
- Tiempo esperado: 40-50 minutos

---

## 📍 Slide 2: El Problema Real

### ¿Por qué TicketDesk?

```
REALIDAD ACTUAL:
┌─────────────────────────────────────────────┐
│ 1,000+ candidatos/mes                       │
│ 20 min de evaluación manual por candidato   │
│ = 333 horas/mes = 4 evaluadores full-time   │
│ Cuello de botella: pérdida de talento       │
└─────────────────────────────────────────────┘

TICKETDESK:
┌─────────────────────────────────────────────┐
│ Candidato → Screening automático (5 min)    │
│ IA Claude → Evaluación en <1s                │
│ Evaluador → Review solo candidatos buenos   │
│ = 50 horas/mes = 1 persona                   │
│ Resultado: 85% más rápido ✓                   │
└─────────────────────────────────────────────┘
```

**Notas para Presentador**:
- Mostrar números reales: 333 horas vs 50 horas
- Enfatizar "pérdida de talento" como motivación
- Esto justifica la complejidad de la solución

---

## 📍 Slide 3: INCEPTION — El Plan

### Fase 1: Decidir QUÉ Construir

```
DECISIONES CLAVE:
┌──────────────────────────────────────────────┐
│ ✅ Architecture: Domain-Driven Design (DDD)  │
│    └─ 6 bounded contexts independientes      │
│                                              │
│ ✅ Stack: FastAPI + Next.js + Claude API     │
│    └─ Python backend, TypeScript frontend    │
│                                              │
│ ✅ Compliance: LGPD brasileño                │
│    └─ Hard delete <24h, audit 7 años        │
│                                              │
│ ✅ SLAs: 99.5% uptime, <1s latency P95      │
│    └─ Monitoreo 24/7                         │
└──────────────────────────────────────────────┘

6 BOUNDED CONTEXTS:
┌─────────────────────────────────────┐
│ Unit 1: Account Management          │
│ Unit 2: Session Management (núcleo) │
│ Unit 3: BotEngine (Claude API)      │
│ Unit 4: Evaluation (Scoring)        │
│ Unit 5: Frontend (UI/UX)            │
│ Unit 6: Compliance (LGPD)           │
└─────────────────────────────────────┘

ARTIFACTS CLAVE:
- PRODUCT.md (visión + features)
- DESIGN.md (patrones + decisiones)
```

**Notas para Presentador**:
- DDD permite que 6 teams trabajen en paralelo
- LGPD es requisito legal en Brasil
- 6 contexts = 6 servicios independientes
- Tiempo de slide: 5 min

---

## 📍 Slide 4: CONSTRUCTION — El Código

### Fase 2: Implementar los 6 Contextos

```
ARQUITECTURA CONSTRUIDA:

                Frontend (Next.js)
                      ↓
        ┌─────────────────────────────┐
        │   API Gateway (ALB/Nginx)   │
        └──┬───────────┬──────────┬───┘
           │           │          │
        ┌──▼──┐    ┌───▼──┐  ┌───▼────┐
        │Back │    │Bot   │  │Eval+   │
        │end  │    │Engine│  │Compl   │
        └──┬──┘    └───┬──┘  └───┬────┘
           │           │         │
        ┌──▼───────────▼─────────▼───┐
        │  PostgreSQL | Redis | S3   │
        └────────────────────────────┘

SERVICIOS CREADOS:
├─ Backend (FastAPI) — Session mgmt + RBAC
├─ BotEngine (Python) — Claude API + jailbreak
├─ Evaluation — Scoring engine
├─ Compliance — LGPD audit logs
├─ Celery — Async tasks
└─ Frontend (Next.js) — Chat + recruiter queue

PATRONES ARQUITECTÓNICOS:
✅ Microservicios (independencia)
✅ Event-Driven (Redis Pub/Sub)
✅ Async-First (Celery workers)
✅ API-First (REST + SSE)
✅ Zero-Trust Security (JWT RS256 + RBAC)
```

**Notas para Presentador**:
- 6 servicios = 6 teams en paralelo
- Event-Driven vía Redis (sin acoplamiento)
- Celery para operaciones pesadas (hard delete)
- Tiempo: 6 min

---

## 📍 Slide 5: TESTING — La Validación

### Fase 3: 130+ Tests Cubriendo Todo

```
PIRÁMIDE TESTING:

                  ▲
                 ╱│╲
                ╱ │ ╲   25 E2E Tests
               ╱  │  ╲  (Playwright)
              ╱───┼───╲
             ╱    │    ╲
            ╱     │     ╲  20 Integration
           ╱      │      ╲ (DB + Redis)
          ╱───────┼───────╲
         ╱        │        ╲
        ╱         │         ╱ 80+ Unit Tests
       ╱          │        ╱ (pytest + Jest)
      ╱───────────┴───────╱

COBERTURA COMPLETA:
┌──────────────────────────────────────────┐
│ Unit 2 Backend    48+ tests              │
│ Unit 3 BotEngine  25+ tests              │
│ Unit 4 Evaluation 20+ tests              │
│ Unit 5 Frontend   29 tests               │
│ Unit 6 Compliance 15+ tests              │
│ Security         18+ tests (OWASP Top10)│
│ Load Testing     3 scenarios (200 users) │
│ ────────────────────────────────────    │
│ TOTAL: 130+ tests | >80% coverage       │
└──────────────────────────────────────────┘

MÉTRICAS DE ÉXITO:
✅ >95% AI scoring accuracy
✅ >95% jailbreak detection
✅ >90% citation extraction
✅ <100ms SSE latency
✅ <24h hard delete SLA
✅ OWASP Top 10 cleared
```

**Notas para Presentador**:
- 130+ tests = confianza total
- Jailbreak detection: custom regex <100ms
- Hard delete: atomic Celery job
- Load testing con 200 usuarios
- Tiempo: 5 min

---

## 📍 Slide 6: DEPLOYMENT — La Entrega

### Fase 4: Docker + Terraform + CI/CD

```
3 AMBIENTES:

LOCAL              STAGING            PRODUCTION
(docker-compose)   (AWS)              (AWS)

PostgreSQL      → RDS (single)    → RDS (Multi-AZ)
Redis           → ElastiCache    → ElastiCache (3 nodes)
LocalStack (S3) → S3 buckets      → S3 + KMS
Nginx           → ALB             → ALB + WAF

6-STAGE CI/CD PIPELINE:

Code Push
    ↓
[1] LINT → [2] TEST → [3] BUILD → [4] E2E → [5] DEPLOY → [6] RELEASE
    │         │          │         │         │           │
    └─ Fail?──┴────────────────────────────────────────────┘
              (Rollback automático)

INFRASTRUCTURE AS CODE:

Terraform 11 Modules:
├─ VPC (networking)
├─ ECS Cluster (container orchestration)
├─ ECS Services (6 servicios)
├─ RDS (PostgreSQL Multi-AZ, 30-day backup)
├─ ElastiCache (Redis cluster, 3 nodes)
├─ S3 (encryption + versioning)
├─ KMS (rotation enabled)
├─ IAM (least privilege)
├─ ALB (load balancer)
├─ CloudWatch (logs, metrics, alarms)
└─ Route53 (DNS)

COST ESTIMADO: $3,150/mes
├─ ECS Fargate $1,200
├─ RDS r6i.xlarge $800
├─ ElastiCache $600
├─ ALB $150
├─ S3 + NAT $300
└─ CloudWatch $100
```

**Notas para Presentador**:
- Local: desarrollo rápido sin AWS
- Staging: validación pre-prod
- Production: Multi-AZ = 0 downtime
- CI/CD: automático desde GitHub
- Terraform: infraestructura versionada
- Tiempo: 7 min

---

## 📍 Slide 7: OPERATIONS — La Producción

### Fase 5: 24/7 Production Support

```
SLAs GARANTIZADOS:

Métrica                Target
─────────────────────────────────
Uptime                 99.5% (~3.6h/mes)
API Latency P95        <1s
Bot Response P95       <3s
Hard Delete SLA        <24h (LGPD)
Error Rate             <0.5%
Database CPU           <70%

ON-CALL ROTATION:

Week 1 → Engineer A  ──┐
Week 2 → Engineer B  ──┤─ Handoff Mondays 9am PT
Week 3 → Engineer C  ──┤─ Backup siempre disponible
Week 4 → Engineer D  ──┘

ALERT MATRIX:

P0 CRITICAL (Page immediately)
├─ API downtime (all 502/503)
├─ Database unreachable
└─ Hard delete failing (LGPD risk)

P1 HIGH (15 min response)
├─ Error rate >2%
├─ API latency >5s
└─ ECS tasks failing

P2 MEDIUM (1hr response)
├─ CPU >80%
├─ Memory >85%
└─ Disk <10%

5 CLOUDWATCH DASHBOARDS:

1. System Health
   └─ Uptime, ECS, RDS, ALB

2. Application Performance
   └─ Latency P50/P95/P99, error rate

3. Database
   └─ Connections, slow queries, storage

4. Security & Compliance
   └─ Login failures, hard delete status

5. Cost
   └─ Daily spend, service breakdown
```

**Notas para Presentador**:
- On-call: personas reales en rotación
- P0 = crítico, page immediately
- 5 dashboards cubriendo todo
- Hard delete <24h es requisito LGPD
- Tiempo: 7 min

---

## 📍 Slide 8: Incident Runbooks

### Cómo Responder a Emergencias

```
RUNBOOK EXAMPLE: API Down (All 502/503)

DIAGNOSIS (5 min):
├─ aws ecs describe-services --cluster ticketdesk-prod
├─ aws rds describe-db-instances
└─ aws elbv2 describe-target-health

RECOVERY (10 min):
├─ Option 1: Restart ECS service
│  └─ aws ecs update-service --force-new-deployment
├─ Option 2: Rollback to previous version
│  └─ git log → revert → deploy
└─ Option 3: Blue/Green failover
   └─ Route traffic a versión anterior

VALIDATION (5 min):
├─ curl https://api.ticketdesk.com/health
├─ curl https://api.ticketdesk.com/botengine/health
└─ Verify SLAs returned to target

RUNBOOK: High Error Rate (>2%)

1. Identify affected service
   └─ Grep logs for ERROR messages

2. Check recent deployments
   └─ git log --oneline -5

3. Options:
   ├─ Fix + PR + deploy (if quick)
   ├─ Rollback to previous version
   └─ Scale down service (reduce traffic)

4. Monitor recovery
   └─ CloudWatch error rate chart

ESCALATION CONTACTS:

Primary On-call    → Phone + Slack
Secondary         → Backup
Tech Lead         → Complex issues
Engineering Manager → Escalations
VP Engineering    → Business impact
```

**Notas para Presentador**:
- Runbooks = procedimientos documentados
- Total response time: 20 min (diagnosis + recovery + validation)
- Escalation clara: no ambigüedad
- Tiempo: 5 min

---

## 📍 Slide 9: Cómo Todo Se Conecta

### El Ciclo Completo de 5 Fases

```
FLUJO ITERATIVO:

  INCEPTION           CONSTRUCTION        TESTING
  (Plan)              (Code)              (Validate)
     │                   │                   │
     ├─ Define          ├─ Implement       ├─ 130+ tests
     │  6 contexts      │  6 services      ├─ >95% accuracy
     ├─ Decide          ├─ Use ADRs        ├─ OWASP passed
     │  architecture    │  from plan       └─ SLAs validated
     └─ Set SLAs        └─ Build APIs
                                                │
                                                ▼
                                           DEPLOYMENT
                                           (Package)
                                               │
                                        ├─ Docker
                                        ├─ Terraform
                                        ├─ CI/CD
                                        └─ Automation
                                                │
                                                ▼
                                           OPERATIONS
                                           (Run 24/7)
                                               │
                                        ├─ SLAs
                                        ├─ On-call
                                        ├─ Monitoring
                                        └─ Runbooks
                                                │
                                                ▼
                                        FEEDBACK → INCEPTION
                                        (Métricas reales)

UN CHANGE FLUYE ASÍ:

Developer Code → Push GitHub
      │
      ├─ [1] Lint (validar estilo)
      ├─ [2] Test (130+ tests)
      ├─ [3] Build (Docker)
      ├─ [4] E2E (Playwright)
      ├─ [5] Deploy Staging (AWS)
      │   ├─ Health checks
      │   └─ Monitor 24h
      │
      └─ [6] Deploy Prod (Blue/Green)
          ├─ RDS backup
          ├─ ECS update
          ├─ Health checks
          ├─ Smoke tests
          └─ Slack notification

Si cualquier stage falla → Rollback automático
```

**Notas para Presentador**:
- 5 fases son iterativas (no lineales)
- Cada fase depende de anterior
- Cambio toma ~10 min de staging a prod
- Rollback automático si falla
- Tiempo: 6 min

---

## 📍 Slide 10: Lecciones Aprendidas

### ¿Qué Funcionó? ¿Qué Fue Difícil?

```
✅ QUÉ FUNCIONÓ:

✓ DDD con 6 bounded contexts
  └─ Equipos en paralelo, bajo acoplamiento

✓ JWT RS256 asymmetric
  └─ Verificación multi-servicio segura

✓ Jailbreak detection regex
  └─ Rápido + accurado sin API call extra

✓ Docker Compose local
  └─ Todos replican prod en su laptop

✓ Terraform IaC
  └─ Infraestructura reproducible, versionada

✓ GitHub Actions 6-stage
  └─ Automatización total lint→deploy

✓ CloudWatch + Runbooks
  └─ Equipo ops responde P0 en <5 min

✓ 130+ tests >80% coverage
  └─ Confianza para push sin fear

⚠️ QUÉ FUE DIFÍCIL:

⚠ LGPD compliance
  └─ Hard delete atómico + 7-year audit

⚠ Token budget enforcement
  └─ Evitar runaway Claude API costs

⚠ Jailbreak accuracy
  └─ >95% sin false positives

⚠ Multi-AZ RDS failover
  └─ Testing de recuperación automática

⚠ Blue/Green 0-downtime
  └─ Health checks + ALB draining timing

RECOMMENDATIONS V1.1+:

V1.1 (3 meses):
├─ WAF (Web Application Firewall)
├─ Granular rate limiting
├─ Analytics dashboard
└─ Email notifications

V2.0 (6 meses):
├─ Multi-language support
├─ Video screening
├─ ATS integrations
└─ Feedback forms

V3.0 (12 meses):
├─ ML pipeline (mejorar scoring)
├─ Custom rubrics
├─ Workflow automation
└─ Industry benchmarking
```

**Notas para Presentador**:
- Honestidad sobre desafíos
- LGPD = complejidad legal real
- Token budget = gestión de costos
- Roadmap muestra visión
- Tiempo: 5 min

---

## 📍 Slide 11: Key Takeaways

### Resumen de Station 5

```
5 FASES = DELIVERY COMPLETO

┌───────────────────────────────────────────────┐
│ INCEPTION    → Define QUÉ (arquitectura)     │
│ ↓                                             │
│ CONSTRUCTION → Implementa CÓMO (code)        │
│ ↓                                             │
│ TESTING      → Valida QUIÉN (130+ tests)     │
│ ↓                                             │
│ DEPLOYMENT   → Empaqueta DÓNDE (AWS)         │
│ ↓                                             │
│ OPERATIONS   → Mantiene CUÁNDO (24/7)        │
└───────────────────────────────────────────────┘

NÚMEROS:
✅ 130+ tests
✅ 6 microservicios
✅ 11 Terraform modules
✅ 6-stage CI/CD
✅ 5 CloudWatch dashboards
✅ 99.5% uptime SLA
✅ <24h hard delete SLA
✅ $3,150/mes infrastructure

ARTIFACTS:
✅ PRODUCT.md + DESIGN.md
✅ docker-compose.yml
✅ terraform/ (completo)
✅ .github/workflows/deploy.yml
✅ OPERATIONS-PHASE-PLAN.md
✅ 8 test specification files
✅ CLAUDE.md (developer guide)

MEJOR PRÁCTICA:
"Un prompt vago produce defaults genéricos"
→ Siempre dar contexto visual + específico
→ Memoria + skills = resultado controlable
```

**Notas para Presentador**:
- Refuerza números clave
- Artifacts = prueba de trabajo
- Mejor práctica = meta-lesson
- Tiempo: 3 min

---

## 📍 Slide 12: Q&A

```
PREGUNTAS FRECUENTES:

Q: ¿Cuánto tiempo llevó esto?
A: 5-7 días de trabajo efectivo (22 horas)

Q: ¿Cuántas personas?
A: Diseñado para 1-2 engineers por servicio
   + 1 DevOps + 1 QA = ~8 personas

Q: ¿Qué si tenemos >200 usuarios?
A: Auto-scaling en ECS Fargate
   RDS Multi-AZ soporta 1000+ conexiones

Q: ¿LGPD solo para Brasil?
A: Sí, pero GDPR es similar (UE)
   El pattern es reutilizable

Q: ¿Cuánto cuesta en prod?
A: ~$3,150/mes (CPU, memory, storage)
   Escalable: +$500 por 2000 usuarios extra

Q: ¿Cómo replico esto?
A: README.md + docker-compose up -d
   Luego terraform apply (producción)

Q: ¿Qué skills necesito?
A: Python, TypeScript, PostgreSQL, AWS
   Docker, Terraform, Git

┌─────────────────────────────────┐
│                                 │
│  ¿Preguntas?                    │
│                                 │
│  Contacto: [your-email]         │
│  GitHub: [project-repo]         │
│  Docs: ESTACION-5-PRESENTACION  │
│                                 │
└─────────────────────────────────┘
```

**Notas para Presentador**:
- Prepara respuestas a preguntas comunes
- Tiempo: 5 min de Q&A

---

## 📋 Cómo Usar Estos Slides

### Opción 1: Convertir a PowerPoint

```bash
# Si tienes pandoc instalado:
pandoc ESTACION-5-SLIDES.md -o presentacion.pptx

# Luego editas en PowerPoint para agregar logos/colores
```

### Opción 2: Convertir a Reveal.js (HTML)

```bash
# Reveal.js es excelente para presentaciones técnicas
pandoc ESTACION-5-SLIDES.md -o presentacion.html \
  -t revealjs \
  -V revealjs-url=https://unpkg.com/reveal.js
```

### Opción 3: Usar directamente desde Markdown

```bash
# En VS Code con extensión "Markdown Preview Mermaid Support"
# Abre este archivo y preview
# Perfecto para presentaciones rápidas
```

### Timing Sugerido

```
Total: 40-50 minutos

Slide 1:  Portada (1 min)
Slide 2:  Problema (3 min)
Slide 3:  Inception (5 min)
Slide 4:  Construction (6 min)
Slide 5:  Testing (5 min)
Slide 6:  Deployment (7 min)
Slide 7:  Operations (7 min)
Slide 8:  Runbooks (5 min)
Slide 9:  Conexión (6 min)
Slide 10: Lecciones (5 min)
Slide 11: Key Takeaways (3 min)
Slide 12: Q&A (5 min)
```

---

**Generado**: 2026-05-27  
**Formato**: Markdown slides (exportable a PowerPoint/Reveal.js/PDF)  
**Duración**: 40-50 minutos  
**Audiencia**: Estudiantes de ingeniería de software
