# Unit 1: Infraestructura (Terraform) — Actividad 2: Requisitos No-Funcionales

**Proyecto**: TicketDesk Enterprise v1.0  
**Fase**: Construcción  
**Unit**: 1 - Infraestructura (Terraform)  
**Actividad**: 2 - Requisitos No-Funcionales (NFR)  
**Fecha**: 2026-05-27  

---

## 📋 Descripción General

**6 Requisitos No-Funcionales** para infraestructura AWS con métricas de SLA y disaster recovery.

---

## 🎯 NFR 1: Disponibilidad (Uptime 99.9%)

**Categoría**: Reliability, High Availability

### Requisitos Cuantificados

| Métrica | Objetivo | Crítico |
|---------|----------|---------|
| Uptime infraestructura | 99.9% | 99.5% |
| Downtime mensual máximo | 43 minutos | 7 horas |
| RTO (Recovery Time) | <1 hora | <2 horas |
| RPO (Recovery Point) | <15 minutos | <30 minutos |
| Latencia p99 | <200ms | <500ms |

### Criterios de Aceptación

- [ ] Multi-AZ deployment (mínimo 2 AZs)
- [ ] Auto-scaling para picos (min 2, max 10 tasks)
- [ ] RDS Multi-AZ failover <2 min
- [ ] ElastiCache replication 3+ nodes
- [ ] ALB health checks cada 10s
- [ ] Quarterly DR drill (restauración exitosa)

### Estrategia Medición

```hcl
# CloudWatch Availability metric
resource "aws_cloudwatch_metric_alarm" "uptime" {
  alarm_name = "uptime-alarm"
  
  metric_name = "CPUUtilization"
  namespace = "AWS/ECS"
  
  threshold = 0.0  # Si CPU = 0, servicio down
  evaluation_periods = 1
  period = 300
  
  alarm_actions = [aws_sns_topic.critical.arn]
}

# RTO test (quarterly)
# Terraform destroy + recreate en non-prod
# Medir tiempo restauración
```

---

## 🎯 NFR 2: Escalabilidad (Auto-Scaling)

**Categoría**: Performance, Capacity

### Requisitos Cuantificados

| Métrica | Objetivo | Medición |
|---------|----------|----------|
| Scaling time | <2 minutos | CloudWatch |
| Min tasks | 2 (HA) | Auto Scaling Group |
| Max tasks | 10 per service | Burst capacity |
| CPU target | 70% | Target tracking policy |
| Memory threshold | 80% | CloudWatch alarm |

### Criterios de Aceptación

- [ ] Auto-scaling grupo configurado (min 2, max 10)
- [ ] Target tracking CPU 70%
- [ ] Scaling cooldown 300s (evitar thrashing)
- [ ] FARGATE_SPOT para non-critical workloads
- [ ] Load test: 200 concurrent → scale to 8 tasks

---

## 🎯 NFR 3: Seguridad (Zero-Trust Network)

**Categoría**: Security, Compliance

### Requisitos Cuantificados

| Métrica | Objetivo | Crítico |
|---------|----------|---------|
| Public access | 0 buckets | 0 |
| Encryption at rest | AES-256 KMS | Requerido |
| Encryption in transit | TLS 1.3 | TLS 1.2 |
| Key rotation | Yearly | Yearly |
| IAM violations | 0 | 0 |

### Criterios de Aceptación

- [ ] S3 buckets privados (no public reads)
- [ ] KMS encryption en S3, RDS, ElastiCache
- [ ] HTTPS obligatorio (redirect HTTP)
- [ ] Security groups: least privilege
- [ ] No hardcoded secrets (use Secrets Manager)

---

## 🎯 NFR 4: Disaster Recovery (RPO <15min)

**Categoría**: Business Continuity, Resilience

### Requisitos Cuantificados

| Métrica | Objetivo | Crítico |
|---------|----------|---------|
| RTO (Recovery Time) | <1 hora | <2 horas |
| RPO (Recovery Point) | <15 minutos | <30 minutos |
| Backup frequency | Hourly | Daily |
| Retention | 30 días | 7 días |
| Cross-region replication | Active | N/A |

### Criterios de Aceptación

- [ ] RDS automated backups (daily, 30d retention)
- [ ] S3 cross-region replication (us-east-1 → us-west-2)
- [ ] EBS snapshots hourly (7d retention)
- [ ] Disaster recovery drill quarterly
- [ ] RDS read replica en otra región

---

## 🎯 NFR 5: Observabilidad (Centralized Monitoring)

**Categoría**: Monitoring, Logging

### Requisitos Cuantificados

| Métrica | Objetivo | Herramienta |
|---------|----------|----------|
| Log retention | 30-7 años (según tipo) | CloudWatch |
| Metric granularity | 1 minuto | CloudWatch |
| Alert latency | <1 minuto | SNS |
| Dashboard update | Real-time | CloudWatch |
| Cost visibility | <5% variance | Cost Explorer |

### Criterios de Aceptación

- [ ] CloudWatch logs para todos services (30d default)
- [ ] CloudWatch dashboards (CPU, Memory, Request count)
- [ ] CloudWatch alarms para thresholds críticos
- [ ] SNS notifications para eventos críticos
- [ ] CloudTrail auditing (API calls, quién hizo qué)

---

## 🎯 NFR 6: Costo & Optimización

**Categoría**: Financial, Efficiency

### Requisitos Cuantificados

| Métrica | Objetivo | Budget |
|---------|----------|--------|
| Monthly cost | <$3,000 | <$4,000 |
| Cost per evaluation | <$0.10 | <$0.15 |
| Reserved instances | 50% compute | Ahorro 40% |
| Spot instances | 30% workloads | Ahorro 70% |

### Criterios de Aceptación

- [ ] FARGATE_SPOT para batch jobs (30% savings)
- [ ] Reserved instances para baseline (50% commitment)
- [ ] S3 Intelligent-Tiering (auto archival)
- [ ] CloudWatch cost anomaly detection
- [ ] Monthly cost review vs budget

---

## 📊 Matriz NFR

| NFR | Métrica Clave | Target | Medición |
|---|---|---|---|
| Disponibilidad | Uptime | 99.9% | CloudWatch |
| Escalabilidad | Scaling time | <2 min | Auto Scaling |
| Seguridad | Encryption | 100% KMS | S3, RDS, cache |
| DR | RPO | <15 min | Backup frequency |
| Observabilidad | Log retention | 30-7 años | CloudWatch |
| Costo | Monthly | <$3K | Cost Explorer |

---

## ✅ Criterios de Aceptación (Actividad 2)

- [x] 6 NFRs documentados con métricas
- [x] Umbrales objetivo + crítico definidos
- [x] Estrategias medición con herramientas AWS
- [x] SLA 99.9% uptime documentado
- [x] DR/Backup plan con <15min RPO

---

**Generado**: 2026-05-27  
**Unit**: 1 - Infraestructura (Terraform)  
**Actividad**: 2 - Requisitos No-Funcionales  
**Estado**: ✅ COMPLETADA
