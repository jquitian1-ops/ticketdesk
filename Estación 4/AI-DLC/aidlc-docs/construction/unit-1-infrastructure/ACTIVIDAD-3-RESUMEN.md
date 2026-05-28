# ✅ UNIT 1 — ACTIVIDAD 3: DISEÑO DE INFRAESTRUCTURA COMPLETADA

**Fecha**: 2026-05-27  
**Estación**: 5 - Construction  
**Actividad**: 3 - Diseño de Infraestructura (Deployment Architecture)  
**Unit**: 1 - Infraestructura  

---

## 📋 Artefactos Generados

### 1️⃣ deployment-architecture.md
**¿Qué?** Diagrama completo de infraestructura, flujos de datos, security, replicación, failover.

**Contiene** (7 secciones):

1. **Topología de Red** (2 AZs, subnets públicas/privadas, NAT, IGW)
   - VPC CIDR: 10.0.0.0/16
   - Public subnets: 10.0.1.0/24, 10.0.2.0/24
   - Private subnets: 10.0.10.0/24, 10.0.11.0/24
   - Rutas de tráfico (entrada, salida, BD, cache)

2. **Security Groups & Firewall** (4 SGs, 14 reglas)
   - ALB-SG: 80 (HTTP), 443 (HTTPS) from 0.0.0.0/0
   - ECS-SG: 8000 (backend), 3000 (frontend) from ALB-SG only
   - RDS-SG: 5432 from ECS-SG only
   - Redis-SG: 6379 from ECS-SG only

3. **ECS Deployment** (2 services, 2-10 tasks per service)
   - Backend: CPU 512, Memory 1024 MB
   - Frontend: CPU 256, Memory 512 MB
   - Task definitions con health checks, logs, env vars

4. **Data Storage & Replication** (RDS + Redis + S3)
   - RDS: Primary (us-south-1a) ↔ Replica sync (us-south-1b)
   - RPO = 0, RTO < 2 min (auto failover)
   - S3: Auto geo-replicated, versioning enabled

5. **CI/CD Pipeline** (6 GitHub Actions jobs)
   - test-backend → test-frontend → build-docker → deploy-staging
   - Manual approval → deploy-production (blue-green)
   - Rollback automático si health check falla

6. **CloudWatch Dashboards** (real-time monitoring)
   - ECS status, ALB latency, RDS connections, Redis cache stats
   - 6 critical alarms (RDS down, ECS tasks, latency, error rate)

7. **Disaster Recovery** (RPO & RTO targets)
   - RDS failure: RPO 0, RTO < 2 min ✓
   - S3 delete: RPO 30 days (versioning) ✓
   - Audit logs: RPO 7 years (S3 archive) ✓

### 2️⃣ terraform-modules-structure.md
**¿Qué?** Cómo se organiza el código Terraform en módulos reutilizables.

**Contiene** (7 secciones):

1. **Estructura de Directorios** (10 módulos)
   - vpc/, security_groups/, rds/, redis/
   - ecs/, alb/, s3/, ecr/, cloudwatch/, kms/, route53/
   - Plus: environments/, tests/

2. **Módulos Descritos** (input, output para cada uno)
   - VPC: vpc_cidr, enable_nat_gateway, availability_zones
   - RDS: db_instance_class, allocated_storage, backup_retention_period, multi_az
   - ECS: cluster_name, desired_count, backend_image, frontend_image
   - ALB: vpc_id, subnet_ids, certificate_arn
   - S3: project_name, environment, lifecycle_rules
   - CloudWatch: log_retention_days, sns_topic_arn
   - Route53: hosted_zone_name, alb_dns_name

3. **Root Module** (orchestrates all modules, ~120 líneas)

4. **Variables & Outputs** (validated inputs, sensitive outputs)

5. **Backend Configuration** (S3 + DynamoDB lock for state)
   - State stored in S3 with versioning
   - DynamoDB table prevents concurrent applies

6. **Testing** (Terratest example)
   - Go-based infrastructure tests
   - Validate VPC creation, RDS multi-AZ, etc.

7. **Deployment Workflow** (plan, apply, destroy commands)

---

## ✅ Criterios de Aceptación Cumplidos

- [x] Topología de red dibujada (2 AZs, multi-AZ para HA)
- [x] Security groups definidas con least privilege
- [x] Flujos de datos documentados (entrada, salida, BD, cache)
- [x] Replicación de datos (sync RDS, S3 versioning, audit 7y)
- [x] Failover paths documentadas (RTO <2 min, RPO = 0)
- [x] CI/CD pipeline completo (6 jobs, blue-green, rollback)
- [x] CloudWatch monitoring (dashboards + alarms)
- [x] 10 módulos Terraform bien definidos
- [x] Cada módulo tiene inputs, outputs, README
- [x] Variables validadas (validation blocks)
- [x] Backend configurado (S3 + DynamoDB lock)
- [x] Testing framework (Terratest) especificado

---

## 🔗 Trazabilidad: ADR → Terraform

| ADR | Patrón | Módulos Terraform |
|-----|--------|-------------------|
| ADR-001 | Multi-AZ | vpc (2 AZs), rds (multi_az=true), ecs (2 subnets) |
| ADR-002 | KMS + TLS | kms, rds (encrypted), redis (at_rest_encryption) |
| ADR-003 | Circuit Breaker | N/A (código, no infra) |
| ADR-004 | Auto-scaling | ecs (auto_scaling.tf, target tracking) |
| ADR-005 | Terraform IaC | All modules, variables, outputs |
| ADR-006 | CloudWatch | cloudwatch (log groups, alarms, dashboards) |

---

## 📊 Infraestructura Resultante

### Costos Estimados

| Componente | Tipo | Costo/Mes |
|-----------|------|-----------|
| RDS db.t3.small | Database | $30 |
| ElastiCache t3.micro | Cache | $15 |
| ECS 2-10 tasks t3.medium | Compute | $60 |
| ALB | Load balancer | $20 |
| NAT Gateway (2x) | Networking | $32 |
| S3 + data transfer | Storage | $20 |
| CloudWatch logs | Monitoring | $15 |
| KMS | Encryption | $10 |
| Misc (Route53, etc) | Other | $6 |
| **Total** | — | **~$208/mes** |

### Performance Targets (from NFR Requirements)

| Métrica | Target | Status |
|---------|--------|--------|
| Uptime | 99.5% | ✓ Multi-AZ failover <2min |
| p99 latency | <2s | ✓ ALB + EC2 instances |
| Cache hit | >85% | ✓ Redis with TTLs |
| Auto-scale | 2-10 tasks | ✓ CPU-based target tracking |
| Data loss | RPO = 0 | ✓ Sync RDS replication |
| Encryption | 100% | ✓ KMS + TLS 1.3 |

---

## 🚀 Próximo Paso

**Actividad 4**: Generación de Código (Terraform Files)

Implementar los 10 módulos con código Terraform real:
- main.tf, variables.tf, outputs.tf para cada módulo
- backend.tf (S3 + DynamoDB lock)
- .github/workflows/terraform.yml (CI/CD)
- Terratest tests

---

## 📊 Unit 1 — Progreso Total

```
ESTACIÓN 5 - UNIT 1
├─ ✅ ACTIVIDAD 1: Diseño Funcional
│  └─ domain-entities.md + business-rules.md + business-logic-model.md
│
├─ ✅ ACTIVIDAD 2: Requerimientos No-Funcionales
│  └─ nfr-requirements.md + nfr-design.md (6 ADRs)
│
├─ ✅ ACTIVIDAD 3: Diseño de Infraestructura
│  └─ deployment-architecture.md + terraform-modules-structure.md
│
├─ ⏳ ACTIVIDAD 4: Generación de Código Terraform
│  └─ modules/, root, backend, tests/
│
└─ ⏳ ACTIVIDAD 5: Pruebas e Integración
   └─ Unit tests, integration tests, E2E validation
```

**Total completado**: 3 de 5 actividades (60%)

---

**Status**: ✅ ACTIVIDAD 3 COMPLETA  
**Siguiente**: Actividad 4 (Terraform Code Generation)  
**Archivo**: aidlc-docs/construction/unit-1-infrastructure/
