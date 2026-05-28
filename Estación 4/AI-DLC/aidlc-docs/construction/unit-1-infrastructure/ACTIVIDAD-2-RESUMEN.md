# ✅ UNIT 1 — ACTIVIDAD 2: REQUERIMIENTOS NO-FUNCIONALES COMPLETADA

**Fecha**: 2026-05-27  
**Estación**: 5 - Construction  
**Actividad**: 2 - Requerimientos No-Funcionales  
**Unit**: 1 - Infraestructura  

---

## 📋 Artefactos Generados

### 1️⃣ nfr-requirements.md
**¿Qué?** Cómo se miden y validan los NFRs  
**Contiene**:
- **Disponibilidad (99.5% SLA)**: Monitoring, RTO <2min, RPO <1min
- **Seguridad (LGPD)**: Encryption at rest + in transit, audit logs, secrets management
- **Performance (<2s p99)**: Latency monitoring, cache hit rate, frontend bundle size
- **Escalabilidad (2-10 tasks)**: Auto-scaling verification, load test scenarios
- **Confiabilidad (MTTR <2min)**: RDS failover test, backup verification
- **Costo ($200/mes)**: AWS cost tracking, budget alerts

**Total**: 6 NFRs × 6 métricas = 36+ criterios de aceptación

### 2️⃣ nfr-design.md
**¿Qué?** ADRs y patrones de diseño que cumplen cada NFR  
**Contiene**:
- **ADR-UNIT1-001**: Multi-AZ Architecture (99.5% uptime)
- **ADR-UNIT1-002**: AWS KMS + TLS 1.3 (LGPD security)
- **ADR-UNIT1-003**: Circuit Breaker + Fallback (graceful degradation)
- **ADR-UNIT1-004**: CPU-based Auto-scaling (cost optimization)
- **ADR-UNIT1-005**: Terraform IaC (reproducibility)
- **ADR-UNIT1-006**: CloudWatch + SNS (observability)

**Total**: 6 ADRs con contexto, opciones evaluadas, decisión, consecuencias

---

## ✅ Criterios de Aceptación Cumplidos

- [x] 6 NFRs claramente medibles (no subjetivos)
- [x] Cada NFR tiene métricas concretas (uptime %, latency ms, cache hit %)
- [x] Criterios de validación con herramientas específicas (CloudWatch, pytest, load test)
- [x] 6 ADRs documentadas (contexto, opciones, decisión, consecuencias)
- [x] Cada ADR evalúa alternativas y explica por qué se eligió
- [x] ADRs mapeadas a NFRs específicos
- [x] Costo total estimado: $200/mes (calculado desde ADRs)
- [x] Frecuencia de validación documentada (daily, weekly, monthly)

---

## 🔗 Trazabilidad: Inception → Unit 1 → Operación

```
INCEPTION (QUÉ)           UNIT 1 ACTIVIDAD 1    UNIT 1 ACTIVIDAD 2
─────────────────────────  ──────────────────   ──────────────────
Req: 99.5% uptime    →     RULE-INFRA-01     →  ADR-001: Multi-AZ
                            (multi-AZ)           
Req: LGPD compliance  →     RULE-INFRA-02/03  →  ADR-002: KMS + TLS
                            (encryption)         
Req: <2s latency     →     RULE-CACHE-01/02  →  ADR-004: Auto-scaling
                            (caching)            
Req: High availability →   RULE-ECS-02/03    →  ADR-003: Circuit Breaker
                            (health checks)      
Req: Observability    →     RULE-MONITOR-01   →  ADR-006: CloudWatch
                            (monitoring)         
Req: IaC reproducible →     domain-entities   →  ADR-005: Terraform
                            (cloud entities)     
```

---

## 📊 NFRs vs Metrics vs Validación

| NFR | Métrica | Target | Herramienta | Validación |
|-----|---------|--------|-------------|-----------|
| Disponibilidad | Uptime % | ≥99.5% | CloudWatch | Daily/Weekly |
| Seguridad | Encryption 100% | KMS+TLS | AWS CLI | Weekly |
| Performance | p99 latency | <2s | Load test | Weekly |
| Escalabilidad | Auto-scale range | 2-10 tasks | ECS metrics | Weekly |
| Confiabilidad | RDS failover time | <2 min | Manual test | Weekly |
| Costo | Monthly bill | ≤$250 | AWS Billing | Monthly |

---

## 🎯 Decisiones Clave Documentadas

### 1. Multi-AZ (vs Single AZ)
- ✅ Decisión: ACEPTA multi-AZ
- Cost trade-off: +$30/mes para 99.5% uptime
- RPO = 0, RTO < 2 min (auto-failover)

### 2. KMS + TLS (vs no encryption / app-level encryption)
- ✅ Decisión: AWS KMS + TLS 1.3
- LGPD compliant, AWS manages keys, transparent to app
- Cost: +$10/mes

### 3. Circuit Breaker (vs direct Claude API calls)
- ✅ Decisión: Circuit Breaker con fallback
- Graceful degradation si Claude API falla
- Cost: 0 (pattrón, no servicio)

### 4. Auto-scaling (vs fixed tasks / manual scaling)
- ✅ Decisión: CPU-based Target Tracking
- Automatically scales 2-10 tasks based on load
- Cost optimization: scale down off-hours

### 5. Terraform (vs CloudFormation / Manual)
- ✅ Decisión: Terraform IaC
- Multi-cloud ready, code review, reproducible
- Community support, HCL readability

### 6. CloudWatch (vs DataDog / New Relic / no monitoring)
- ✅ Decisión: CloudWatch + SNS
- AWS-native, cost-effective ($50/mes)
- Sufficient para MVP (basic dashboards + alarms)

---

## 💰 Cost Breakdown (ADRs)

| ADR | Patrón | Costo Mensual |
|-----|--------|--------------|
| ADR-001 | Multi-AZ | +$30 |
| ADR-002 | KMS encryption | +$10 |
| ADR-003 | Circuit Breaker | $0 (patrón) |
| ADR-004 | Auto-scaling | $0 (AWS built-in) |
| ADR-005 | Terraform | $0 (open source) |
| ADR-006 | CloudWatch | +$50 |
| — | Base (2 tasks, RDS, Redis, S3) | $110 |
| **Total** | — | **~$200/mes** |

---

## 🚀 Próximo Paso

**Actividad 3**: Diseño de Infraestructura (Deployment Architecture)

Tomaremos los ADRs y traduciremos a:
- Diagrama de infraestructura (C4 Level 3)
- Terraform modules structure
- Network diagram (VPC, subnets, security groups)
- Deployment pipeline diagram

---

## ✨ Resumen Visual

```
UNIT 1: INFRAESTRUCTURA
├─ ACTIVIDAD 1: Diseño Funcional ✅
│  ├─ domain-entities.md (11 entities, 5 aggregates)
│  ├─ business-rules.md (21 reglas)
│  └─ business-logic-model.md (4 flujos E2E)
│
├─ ACTIVIDAD 2: Requerimientos No-Funcionales ✅
│  ├─ nfr-requirements.md (6 NFRs, 36+ métricas)
│  └─ nfr-design.md (6 ADRs, decisiones)
│
├─ ACTIVIDAD 3: Diseño de Infraestructura ⏳
├─ ACTIVIDAD 4: Generación de Código (Terraform) ⏳
├─ ACTIVIDAD 5: Pruebas e Integración ⏳
└─ ACTIVIDAD 6: Validación E2E ⏳
```

---

**Status**: ✅ ACTIVIDAD 2 COMPLETA  
**Siguiente**: Actividad 3 (Deployment Architecture)  
**Archivo**: aidlc-docs/construction/unit-1-infrastructure/
