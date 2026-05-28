# Unit 1: Infraestructura (Terraform) — Actividad 1: Entidades del Dominio

**Proyecto**: TicketDesk Enterprise v1.0  
**Fase**: Construcción  
**Unit**: 1 - Infraestructura (Terraform IaC)  
**Actividad**: 1 - Diseño Funcional: Recursos AWS  
**Fecha**: 2026-05-27  

---

## 📋 Contexto Acotado: Infrastructure as Code

**Alcance**: 11 módulos Terraform, multi-region AWS, auto-scaling, disaster recovery, observabilidad centralizada.

**Patrón**: Infrastructure as Code (IaC) con módulos reutilizables, versionados, tested

---

## 🎯 11 Agregados de Recursos AWS

### 1. Módulo VPC (Networking)

```
vpc
├── vpc: VPC principal (CIDR 10.0.0.0/16)
├── subnets_públicas: 2 AZs (10.0.1.0/24, 10.0.2.0/24)
├── subnets_privadas: 2 AZs (10.0.10.0/24, 10.0.11.0/24)
├── internet_gateway: Acceso exterior
├── nat_gateway: Salida privado (HA)
├── route_tables: Público + Privado
├── security_groups:
│   ├── alb_sg: Allow 80, 443 from anywhere
│   ├── ecs_sg: Allow 8000 from ALB
│   ├── rds_sg: Allow 5432 from ECS
│   └── redis_sg: Allow 6379 from ECS
└── network_acls: Estateful (default)

Invariantes:
- Subnets en mínimo 2 AZs (HA)
- NAT Gateway para salida privada
- SG restrictivo (least privilege)
```

### 2. Módulo ALB (Load Balancer)

```
alb
├── application_load_balancer: Port 80/443
├── target_groups:
│   ├── tg_backend: Port 8000 (Unit 2)
│   ├── tg_botengine: Port 8001 (Unit 3)
│   └── tg_compliance: Port 8002 (Unit 6)
├── listeners:
│   ├── HTTP → HTTPS redirect
│   └── HTTPS → TG routing
├── ssl_certificate: ACM (auto-renewed)
├── health_checks: /health endpoint, 30s interval
└── sticky_sessions: Cookie-based, 1d duration

Invariantes:
- HTTPS obligatorio
- Health check debe responder <5s
- Mínimo 2 targets por TG (HA)
```

### 3. Módulo ECS Cluster

```
ecs_cluster
├── cluster: Fargate launch type
├── capacity_provider: FARGATE_SPOT + FARGATE
├── services:
│   ├── backend_service (Unit 2): 3 tasks
│   ├── botengine_service (Unit 3): 3 tasks
│   ├── evaluation_service (Unit 4): 2 tasks
│   ├── compliance_service (Unit 6): 2 tasks
│   └── celery_worker: 2 tasks
├── task_definitions: (ver Módulo 5)
├── auto_scaling: Target tracking CPU 70%
└── logging: CloudWatch Logs (30d retention)

Invariantes:
- Desirable count ≥ 2 (HA)
- Service discovery via Route53
- Graceful shutdown (drain time 60s)
```

### 4. Módulo RDS (PostgreSQL)

```
rds
├── db_instance:
│   ├── engine: postgres 15
│   ├── instance_class: db.r6i.xlarge (production)
│   ├── multi_az: true (failover 2 min)
│   ├── storage: 100GB (gp3, 3000 IOPS)
│   └── backup_retention: 30 días
├── parameter_group: max_connections=200
├── option_group: encryption=on
├── subnet_group: Privadas (2 AZs)
├── security_group: Allow 5432 from ECS
├── enhanced_monitoring: CloudWatch (granular)
└── slow_query_log: <1s threshold

Invariantes:
- Multi-AZ obligatorio
- Backups automáticos 30d
- Encryption at rest (KMS)
- No acceso público (privado)
```

### 5. Módulo ElastiCache (Redis)

```
elasticache
├── cluster:
│   ├── engine: redis 7
│   ├── node_type: cache.r6g.xlarge
│   ├── num_cache_nodes: 3 (replication + sentinel)
│   ├── automatic_failover: true
│   ├── multi_az: true
│   └── engine_version: 7.0
├── parameter_group: maxmemory-policy=allkeys-lru
├── subnet_group: Privadas (2 AZs)
├── security_group: Allow 6379 from ECS
├── backup:
│   ├── snapshot_retention: 5
│   └── snapshot_window: 03:00-04:00 UTC
└── monitoring: CloudWatch metrics (1min granularity)

Invariantes:
- Cluster mode enabled (sharding)
- Replication 3+ nodes
- Encryption at transit (in-transit)
- Encryption at rest (at-rest)
```

### 6. Módulo S3 (Object Storage)

```
s3
├── bucket_transcriptions:
│   ├── versioning: enabled
│   ├── encryption: AES-256 + KMS
│   ├── public_access_block: all blocked
│   └── lifecycle:
│       ├── Intelligent-Tiering 30d
│       ├── Glacier 90d
│       └── Expiration 7 años
├── bucket_consentimientos:
│   ├── encryption: KMS
│   ├── versioning: enabled
│   └── lifecycle: 10 años (legal hold)
├── bucket_evaluations:
│   ├── encryption: KMS
│   ├── replication: cross-region
│   └── lifecycle: 7 años
├── bucket_logs:
│   ├── logging: server access logs
│   ├── retention: 1 año
│   └── encryption: AES-256
└── bucket_backups:
    ├── replication: multi-region
    ├── versioning: enabled
    └── lifecycle: 10 años

Invariantes:
- Versionado en buckets críticos
- Encryption KMS en datos sensibles
- Public access bloqueado
- Lifecycle policies automático
```

### 7. Módulo KMS (Encryption)

```
kms
├── master_key:
│   ├── rotation: yearly (automático)
│   ├── key_policy: least privilege
│   └── tags: compliance=lgpd
├── grants:
│   ├── Para S3: Encrypt/Decrypt
│   ├── Para RDS: Encrypt/Decrypt
│   ├── Para ElastiCache: Encrypt/Decrypt
│   └── Para CloudWatch: Encrypt/Decrypt
├── key_alias: alias/ticketdesk
└── audit: CloudTrail logging

Invariantes:
- Rotación yearly obligatoria
- Key policy auditable
- Grants auditados (CloudTrail)
```

### 8. Módulo IAM (Identity & Access)

```
iam
├── roles:
│   ├── ecs_task_role: Acceso S3, KMS, SQS
│   ├── ecs_task_execution_role: Acceso ECR, CloudWatch
│   ├── lambda_role: Si usamos Lambda (future)
│   └── ci_cd_role: GitHub Actions deploy
├── policies: Least privilege IAM
├── service_linked_roles: Para AWS services
└── mfa_enforcement: Requerido para humans

Invariantes:
- No root credentials en uso
- Roles con policy mínimo necesario
- Service linked roles para AWS
```

### 9. Módulo CloudWatch (Observabilidad)

```
cloudwatch
├── log_groups:
│   ├── /aws/ecs/backend: 30d retention
│   ├── /aws/ecs/botengine: 30d retention
│   ├── /aws/ecs/evaluation: 30d retention
│   ├── /aws/ecs/compliance: 7 años retention
│   └── /aws/rds/postgresql: 30d retention
├── metrics:
│   ├── CPU utilización
│   ├── Memory utilización
│   ├── RequestCount
│   └── ErrorRate
├── dashboards: Real-time monitoring
├── alarms:
│   ├── CPU > 80%: Warning
│   ├── CPU > 95%: Critical
│   ├── Error rate > 1%: Critical
│   └── RDS connections > 150: Warning
└── insights: Log query language

Invariantes:
- Retention según compliance (30d o 7 años)
- Alarms con SNS notifications
```

### 10. Módulo Route53 (DNS)

```
route53
├── hosted_zone: ticketdesk.com
├── records:
│   ├── api.ticketdesk.com: ALB ALIAS
│   ├── botengine.ticketdesk.com: ALB ALIAS
│   ├── app.ticketdesk.com: CloudFront (Next.js)
│   └── compliance.ticketdesk.com: ALB ALIAS
├── health_checks: Every 10s
└── routing_policy:
    ├── Simple para prod
    └── Weighted para canary deploys

Invariantes:
- DNS con health checks
- TTL 300s (5min) para agilidad
```

### 11. Módulo Backup & DR (Disaster Recovery)

```
backup
├── backup_vault: Encrypted
├── backup_plans:
│   ├── RDS: Daily, 30d retention
│   ├── S3: Replication cross-region
│   ├── EBS: Snapshots hourly, 7d retention
│   └── DynamoDB: (Future) On-demand backup
├── cross_region_replication:
│   ├── S3 to us-west-2
│   └── RDS standby (read replica)
└── rto_rpo:
    ├── RTO: <1 hora
    ├── RPO: <15 minutos
    └── Test quarterly

Invariantes:
- RTO <1h, RPO <15min
- Backups cifrados
- Cross-region redundancia
```

---

## 🔄 Máquinas de Estados (Deployment)

```
Code Push → GitHub Actions
     │
     ▼
ECR Build (Docker image)
     │
     ├─ Test stage
     ├─ Scan security
     └─ Push ECR
     │
     ▼
Terraform Plan (IaC)
     │
     ├─ Validate syntax
     ├─ Check policies
     └─ Show changes
     │
     ▼
Manual Approval (Prod)
     │
     ▼
Terraform Apply
     │
     ├─ Update resources
     ├─ Run smoke tests
     └─ Notify Slack
     │
     ▼
ECS Task Update
     │
     ├─ New task definition
     ├─ Rolling deployment
     └─ Health checks
     │
     ▼
DEPLOYED ✓
```

---

## ✅ Criterios de Aceptación (Actividad 1)

- [x] 11 módulos Terraform documentados
- [x] Recursos AWS especificados (VPC, ECS, RDS, S3, KMS, etc.)
- [x] Security groups y networking diseñado (HA)
- [x] Backup & DR documentado (RTO <1h, RPO <15m)
- [x] Observabilidad centralizada (CloudWatch)

---

**Generado**: 2026-05-27  
**Unit**: 1 - Infraestructura (Terraform)  
**Actividad**: 1 - Entidades del Dominio  
**Estado**: ✅ COMPLETADA
