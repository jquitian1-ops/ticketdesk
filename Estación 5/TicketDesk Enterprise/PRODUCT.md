# PRODUCT.md — TicketDesk Enterprise v1.0

**Memo del Producto**: Especificación ejecutiva de qué es TicketDesk y por qué existe.

---

## 🎯 Visión del Producto

**TicketDesk Enterprise** es una plataforma de screening conversacional con IA que automatiza la evaluación inicial de candidatos mediante entrevistas agénticas con Claude, reduciendo el tiempo de reclutamiento en un 70% mientras mejora la calidad de las contrataciones.

---

## 👥 Usuarios

### 1. **Candidato** (Flujo Screening)
- Accede a URL de screening personalizada
- Participa en entrevista conversacional con bot (Claude)
- Completa screening sin interacción humana
- **SLA**: Screening completado en <30 minutos

### 2. **Reclutador** (Flujo Evaluación)
- Accede dashboard de candidatos "listos para evaluar"
- Revisa transcripción + puntuación automática del bot
- Completa evaluación manual (rúbrica de 3 criterios)
- Toma decisión final: HIRE / REJECT / MAYBE
- **SLA**: Evaluación completa en <10 minutos por candidato

### 3. **Administrador** (Gestión)
- Crea campañas de reclutamiento
- Configura rúbricas de evaluación
- Monitorea SLAs, auditoría, compliance LGPD
- Gestiona usuarios y permisos

---

## 🔑 Features Principales

### Screening Candidato (Unit 5 + Unit 3)
```
1. Acceso a screening por URL personalizada
2. Aceptación de consentimiento LGPD
3. Lectura de instrucciones + briefing del rol
4. Chat interactivo con bot (Claude API)
   - Jailbreak detection en tiempo real
   - Token budget enforcement (2000 tokens/sesión)
   - SSE streaming (<100ms latencia primer token)
5. Conversación completada automáticamente
6. Reporte de sesión guardado en DB
```

### Evaluación Reclutador (Unit 4)
```
1. Dashboard con cola de candidatos
2. Filtrado por estado/campaña
3. Modal de evaluación:
   - Revisión de transcripción
   - Rúbrica de 3 criterios (Comunicación, Técnica, Cultural)
   - Puntuación automática (0-100)
   - Extracción de citas relevantes
4. Decisión final: HIRE / REJECT / MAYBE
5. Guardar evaluación con auditoría LGPD
```

### Gestión de Campañas (Unit 2)
```
1. CRUD campañas de reclutamiento
2. Asignar rúbricas por campaña
3. Invitar candidatos (genera URLs personalizadas)
4. Cola de evaluación en tiempo real
5. Reporte de resultados
```

### Compliance LGPD (Unit 6)
```
1. Consentimiento requerido antes de screening
2. Hash de integridad de documento de consentimiento
3. Auditoría 100% de eventos (7 años retención)
4. PII hasheado en CloudWatch Logs
5. Right to be Forgotten: hard delete <24h SLA
6. Exportación de datos personal (LGPD art. 20)
```

---

## 📊 Métricas de Éxito

### Engagement
- **Screening completion rate**: >85% (candidatos completan)
- **Time to complete screening**: <30 min (SLA)
- **Jailbreak attempt rate**: <2% (intentos de inyección)

### Calidad Evaluación
- **Scoring accuracy**: >95% (matches manual scoring)
- **Citation extraction**: >90% recall
- **Reclutador confidence**: >4.0/5.0 (survey)

### Operacional
- **Evaluación latencia**: <10 min (reclutador)
- **Bot response time**: <3s P95
- **System uptime**: 99.5% (SLA)
- **Hard delete SLA**: <24h (100% cumplimiento)

### Compliance
- **Audit trail**: 100% eventos
- **PII leak incidents**: 0
- **LGPD violations**: 0
- **Data retention policy**: 7 años

---

## 🏗️ Arquitectura de Alto Nivel

```
Internet
    │
    ▼
┌─ CloudFront (CDN) ────────┐
│ Static assets (Next.js 14) │
└──────────────┬─────────────┘
               │
               ▼
    ┌─ ALB (Application Load Balancer) ─┐
    │  Port 80 → 443 (HTTPS redirect)    │
    │  Path routing → servicios          │
    └──────────────┬──────────────────────┘
                   │
     ┌─────────────┼─────────────┬──────────┐
     ▼             ▼             ▼          ▼
┌─ ECS Fargate ─────────────────────────────────────┐
│  Backend (8000)     → FastAPI + Python            │
│  BotEngine (8001)   → Claude API + Jailbreak det. │
│  Evaluation (8002)  → Scoring engine              │
│  Compliance (8003)  → Auditoría LGPD              │
│  Celery Workers (2) → Async jobs (hard delete)    │
└────────────────────┬────────────────────────────┘
                     │
     ┌───────────────┼───────────┬──────────┐
     ▼               ▼           ▼          ▼
┌─ RDS ──────┐ ┌─ Redis ──┐ ┌─ S3 ──┐ ┌─ KMS ─┐
│PostgreSQL  │ │ElastiCache│ │Buckets│ │Encrypt│
│Multi-AZ    │ │3 nodes    │ │       │ │Rotate │
└────────────┘ └───────────┘ └───────┘ └───────┘
```

**Tecnología**:
- **Frontend**: Next.js 14 + React 19 + TypeScript + Zustand
- **Backend**: FastAPI + Python 3.12 + PostgreSQL + Redis
- **Infrastructure**: AWS (ECS Fargate, RDS, ElastiCache, S3, KMS)
- **External**: Claude API (AI screening)
- **Observability**: CloudWatch Logs + Alarms

---

## 💰 Modelo de Negocio

### Costo Infrastructure (Mensual)
```
ECS Fargate (compute)    ... $1,200
RDS PostgreSQL (DB)      ... $800
ElastiCache (cache)      ... $600
S3 + ALB + NAT           ... $300
CloudWatch + otros       ... $100
─────────────────────────────────
Total                    ... ~$3,000/mes
```

### Pricing (Estimado para customers)
```
Per-screening: $2-5 USD
Per-evaluation: $1-2 USD
Platform fee: $500/mes (base)

Ej: 1000 screenings/mes = ~$3,000 + overhead
```

---

## 📅 Fases de Desarrollo

| Fase | Duración | Status |
|---|---|---|
| **Inception** | 1 semana | ✅ COMPLETA |
| **Construction** | 1 semana | ✅ COMPLETA |
| **Testing** | 1 semana | ✅ COMPLETA |
| **Deployment** | 3-5 días | 🟨 EN CURSO |
| **Operations** | Ongoing | ⏳ PENDIENTE |

---

## 🔐 Seguridad & Compliance

### Security
- **JWT RS256** para autenticación
- **RBAC** roles (CANDIDATE, RECRUITER, ADMIN)
- **Rate limiting** contra brute force
- **XSS prevention** (DOMPurify)
- **SQL injection prevention** (parameterized queries)
- **Jailbreak detection** >95% accuracy

### Compliance
- **LGPD** (Lei Geral de Proteção de Dados)
  - Consentimiento explícito
  - Right to be Forgotten <24h
  - Auditoría 100%
  - PII encryption + hashing
- **Data retention**: 7 años (compliance)
- **Encryption**: AES-256 KMS at-rest, TLS 1.3 in-transit

---

## 📈 Roadmap Futuro

### V1.1 (Q3 2026)
- [ ] Integración con ATS (Applicant Tracking System)
- [ ] Bulk candidate import
- [ ] Advanced analytics dashboard

### V2.0 (Q4 2026)
- [ ] Multi-language screening (ES, EN, PT)
- [ ] Video interview option (opcional)
- [ ] ML-powered skill assessment

### V3.0 (2027)
- [ ] Candidate marketplace
- [ ] API para clientes SaaS
- [ ] Mobile app (iOS/Android)

---

## 👨‍💼 Stakeholders

| Rol | Responsabilidad |
|---|---|
| **Product Owner** | Visión, roadmap, prioridades |
| **Engineering Lead** | Arquitectura, technical decisions |
| **Compliance Officer** | LGPD, auditoría, regulaciones |
| **Customer Success** | Onboarding, support, feedback |
| **Data Analyst** | Metrics, reporting, insights |

---

## 📞 Contacto & Escalations

- **Product Questions**: PO
- **Technical Issues**: Engineering Lead
- **Compliance/Legal**: Compliance Officer
- **Customer Concerns**: Customer Success
- **Emergency (production down)**: Engineering On-call

---

**Última actualización**: 2026-05-27  
**Versión**: v1.0  
**Status**: Production Ready ✅
