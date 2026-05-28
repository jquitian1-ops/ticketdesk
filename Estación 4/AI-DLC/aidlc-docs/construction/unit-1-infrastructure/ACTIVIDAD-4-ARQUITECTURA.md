# Unit 1: Infraestructura (Terraform) — Actividad 4: Infraestructura Detallada

**Proyecto**: TicketDesk Enterprise v1.0  
**Fase**: Construcción  
**Unit**: 1 - Infraestructura (Terraform)  
**Actividad**: 4 - Infraestructura  
**Fecha**: 2026-05-27  

---

## 🏗️ AWS Architecture Diagram (C4 Level 3)

```
Internet
    │
    ▼
┌─ Route 53 (DNS) ─────────────────────────────┐
│  api.ticketdesk.com → ALB                    │
│  app.ticketdesk.com → CloudFront (Next.js)   │
└──────────────┬───────────────────────────────┘
               │
               ▼
    ┌─ CloudFront (CDN) ──┐
    │ Static assets (Next)│
    │ Cache 1 year        │
    └─────────┬───────────┘
              │
              ▼
┌─ Application Load Balancer ────────────────────────────┐
│  Port 80 → 443 (HTTPS redirect)                        │
│  Target Groups:                                         │
│  • /api → Backend (8000)                               │
│  • /botengine → BotEngine (8001)                       │
│  • /evaluation → Evaluation (8002)                      │
│  • /compliance → Compliance (8003)                      │
└──────────────┬──────────────────────────────────────────┘
               │
     ┌─────────┴─────────┬─────────────┬──────────┐
     ▼                   ▼             ▼          ▼
┌─ ECS Cluster (Fargate) ────────────────────────────────┐
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────┐    │
│  │ Backend      │  │ BotEngine    │  │Evaluation│    │
│  │ Service (3)  │  │ Service (3)  │  │Service(2)│    │
│  │ Port 8000    │  │ Port 8001    │  │Port 8002 │    │
│  └──────────────┘  └──────────────┘  └──────────┘    │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐                   │
│  │ Compliance   │  │ Celery       │                   │
│  │ Service (2)  │  │ Worker (2)   │                   │
│  │ Port 8003    │  │ (Async jobs) │                   │
│  └──────────────┘  └──────────────┘                   │
│                                                         │
│  Auto Scaling: 2-10 tasks per service                  │
│  Logging: CloudWatch (30d)                             │
│  Monitoring: CloudWatch metrics (1m)                   │
└────────────────────┬─────────────────────────────────┘
                     │
     ┌───────────────┼───────────────┬──────────┐
     ▼               ▼               ▼          ▼
┌─ RDS ──────┐ ┌─ ElastiCache ┐ ┌─ S3 ──┐ ┌─ KMS ─┐
│PostgreSQL  │ │ Redis 7      │ │Buckets│ │Encrypt│
│Multi-AZ    │ │ 3 nodes      │ │Encrypt│ │Rotate │
│Encrypted   │ │ Replication  │ │KMS    │ │yearly │
│30d backup  │ │ 6379 cached  │ │Versio │ │       │
└────────────┘ └──────────────┘ └───────┘ └───────┘
```

## 🗂️ Estructura Directorios Terraform

```
terraform/
├── main.tf                  # Configuración root
├── variables.tf             # Variables de input
├── outputs.tf               # Outputs (IPs, URLs)
├── terraform.tfvars         # Valores (no commited)
├── backend.tf               # Remote state config
│
├── modules/
│   ├── vpc/                 # Networking
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   │
│   ├── alb/                 # Load balancer
│   ├── ecs_cluster/         # ECS cluster
│   ├── ecs_services/        # Services (backend, botengine, etc.)
│   ├── rds/                 # PostgreSQL
│   ├── elasticache/         # Redis
│   ├── s3/                  # Storage buckets
│   ├── kms/                 # Encryption keys
│   ├── iam/                 # IAM roles/policies
│   ├── cloudwatch/          # Monitoring
│   ├── route53/             # DNS
│   └── backup/              # Disaster recovery
│
├── environments/
│   ├── dev/
│   │   ├── terraform.tfvars
│   │   └── backend.tf
│   ├── staging/
│   │   ├── terraform.tfvars
│   │   └── backend.tf
│   └── prod/
│       ├── terraform.tfvars
│       └── backend.tf
│
└── tests/
    ├── main_test.go         # Terratest
    ├── vpc_test.go
    └── ecs_test.go
```

## 🔑 Terraform Backend Configuration

```hcl
# backend.tf
terraform {
  backend "s3" {
    bucket         = "ticketdesk-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
```

## 📊 Costo Estimado (Monthly)

| Recurso | Tipo | Cantidad | Costo |
|---------|------|----------|-------|
| ECS Fargate | vCPU-hora | 2,000 | $800 |
| ECS Fargate | Memory-hour | 4,000 GB | $400 |
| RDS r6i.xlarge | Multi-AZ | 1 | $800 |
| ElastiCache r6g.xlarge | 3 nodes | 1 | $600 |
| S3 Storage | 500 GB | 1 | $15 |
| ALB | hora | 730 | $150 |
| Data transfer | Out | 100 GB | $100 |
| CloudWatch | logs + metrics | 1 | $50 |
| **TOTAL** | - | - | **~$2,915** |

---

**Generado**: 2026-05-27  
**Unit**: 1 - Infraestructura (Terraform)  
**Actividad**: 4 - Infraestructura  
**Estado**: ✅ COMPLETADA
