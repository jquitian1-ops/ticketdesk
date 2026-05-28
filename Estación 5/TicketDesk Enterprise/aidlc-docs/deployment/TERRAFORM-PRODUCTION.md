# Terraform Production Deployment

**Proyecto**: TicketDesk Enterprise v1.0  
**Environment**: Production  
**Region**: us-east-1 (Virginia)  
**Backend**: S3 + DynamoDB (remote state)  
**Fecha**: 2026-05-27  

---

## 📋 Pre-Requisitos

```bash
# Instalar Terraform 1.5+
terraform version  # >= 1.5.0

# AWS credentials configuradas
export AWS_ACCESS_KEY_ID=xxx
export AWS_SECRET_ACCESS_KEY=xxx
export AWS_DEFAULT_REGION=us-east-1

# Crear S3 bucket para state (una sola vez)
aws s3 mb s3://ticketdesk-terraform-state-prod
aws s3api put-bucket-versioning \
  --bucket ticketdesk-terraform-state-prod \
  --versioning-configuration Status=Enabled
```

---

## 🗂️ Estructura Terraform

```
terraform/
├── main.tf                  # Configuración root
├── variables.tf             # Variables de input
├── outputs.tf               # Outputs (IPs, URLs)
├── terraform.tfvars         # Valores env-specific (NO commit)
├── backend.tf               # Remote state config
│
├── modules/
│   ├── vpc/                 # Networking
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── ecs_cluster/         # ECS cluster
│   ├── ecs_services/        # Backend, BotEngine, etc.
│   ├── rds/                 # PostgreSQL
│   ├── elasticache/         # Redis
│   ├── s3/                  # Storage buckets
│   ├── kms/                 # Encryption
│   ├── iam/                 # Roles/policies
│   ├── alb/                 # Load balancer
│   ├── cloudwatch/          # Monitoring
│   ├── route53/             # DNS
│   └── backup/              # Disaster recovery
│
├── environments/
│   ├── prod/
│   │   ├── terraform.tfvars
│   │   ├── backend.tf
│   │   └── vpc.tf
│   └── staging/
│       ├── terraform.tfvars
│       └── backend.tf
│
└── tests/
    ├── main_test.go
    ├── vpc_test.go
    └── ecs_test.go
```

---

## 🚀 Comandos Principales

### 1. Inicializar Terraform

```bash
cd terraform/

# Inicializar (descargar modules, configurar backend)
terraform init -backend-config="key=prod/terraform.tfstate"

# Output:
# Terraform has been successfully configured!
# Backend has been successfully initialized!
```

### 2. Validar Configuración

```bash
# Validar sintaxis
terraform validate

# Lint (opcional)
tflint

# Format
terraform fmt -recursive
```

### 3. Plan (Dry-run)

```bash
# Ver qué va a cambiar (sin aplicar)
terraform plan \
  -var-file="environments/prod/terraform.tfvars" \
  -out=tfplan

# Output:
# Plan: 47 to add, 0 to change, 0 to destroy.
```

### 4. Apply (Desplegar)

```bash
# Aplicar con aprobación manual
terraform apply tfplan

# O directamente (sin plan previo)
terraform apply \
  -var-file="environments/prod/terraform.tfvars" \
  -auto-approve  # NO USAR EN PROD SIN REVIEW
```

### 5. Outputs

```bash
# Ver outputs después de apply
terraform output

# Output:
# alb_dns_name = "ticketdesk-alb-1234567890.us-east-1.elb.amazonaws.com"
# rds_endpoint = "ticketdesk-prod.c9akciq32.us-east-1.rds.amazonaws.com:5432"
# ...
```

### 6. Destroy (Cuidado!)

```bash
# Solo para ambiente que queremos eliminar
terraform destroy \
  -var-file="environments/prod/terraform.tfvars" \
  -auto-approve  # NUNCA EN PROD
```

---

## 📋 Archivo: environments/prod/terraform.tfvars

```hcl
# TicketDesk Production Configuration

# Networking
vpc_cidr           = "10.0.0.0/16"
availability_zones = ["us-east-1a", "us-east-1b"]

# ECS Services
ecs_cluster_name = "ticketdesk-prod"

backend_desired_count      = 3
botengine_desired_count    = 3
evaluation_desired_count   = 2
compliance_desired_count   = 2
celery_desired_count       = 2

# Database
rds_instance_class = "db.r6i.xlarge"
rds_allocated_storage = 100
rds_engine_version = "15.2"
rds_backup_retention_days = 30
rds_multi_az = true

# Cache
elasticache_node_type = "cache.r6g.xlarge"
elasticache_num_cache_nodes = 3
elasticache_engine_version = "7.0"

# Storage
s3_transcriptions_bucket = "ticketdesk-prod-transcriptions"
s3_reports_bucket = "ticketdesk-prod-reports"

# Encryption
kms_key_rotation_enabled = true

# Monitoring
cloudwatch_log_retention_days = 2555  # 7 años para compliance

# Tags
environment = "production"
project     = "ticketdesk-enterprise"
cost_center = "engineering"
```

---

## 📄 Archivo: main.tf (Root)

```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  required_version = ">= 1.5"
}

provider "aws" {
  region = "us-east-1"

  default_tags {
    tags = {
      Environment = var.environment
      Project     = var.project
      ManagedBy   = "Terraform"
    }
  }
}

# VPC & Networking
module "vpc" {
  source = "./modules/vpc"
  
  vpc_cidr           = var.vpc_cidr
  availability_zones = var.availability_zones
}

# ECS Cluster
module "ecs_cluster" {
  source = "./modules/ecs_cluster"
  
  cluster_name = var.ecs_cluster_name
  vpc_id       = module.vpc.vpc_id
}

# ECS Services (Backend, BotEngine, etc.)
module "ecs_services" {
  source = "./modules/ecs_services"
  
  cluster_id = module.ecs_cluster.cluster_id
  vpc_id     = module.vpc.vpc_id
  
  backend_desired_count      = var.backend_desired_count
  botengine_desired_count    = var.botengine_desired_count
  evaluation_desired_count   = var.evaluation_desired_count
  compliance_desired_count   = var.compliance_desired_count
  celery_desired_count       = var.celery_desired_count
  
  depends_on = [
    module.rds,
    module.elasticache,
    module.iam,
  ]
}

# RDS PostgreSQL
module "rds" {
  source = "./modules/rds"
  
  instance_class       = var.rds_instance_class
  allocated_storage    = var.rds_allocated_storage
  engine_version       = var.rds_engine_version
  backup_retention     = var.rds_backup_retention_days
  multi_az             = var.rds_multi_az
  
  db_subnet_group_name = module.vpc.db_subnet_group_name
  security_group_id    = module.vpc.rds_security_group_id
  kms_key_id          = module.kms.rds_key_id
}

# ElastiCache Redis
module "elasticache" {
  source = "./modules/elasticache"
  
  node_type      = var.elasticache_node_type
  num_cache_nodes = var.elasticache_num_cache_nodes
  engine_version = var.elasticache_engine_version
  
  subnet_group_name = module.vpc.elasticache_subnet_group_name
  security_group_id = module.vpc.elasticache_security_group_id
}

# S3 Buckets
module "s3" {
  source = "./modules/s3"
  
  transcriptions_bucket = var.s3_transcriptions_bucket
  reports_bucket        = var.s3_reports_bucket
  
  kms_key_id = module.kms.s3_key_id
}

# KMS Encryption Keys
module "kms" {
  source = "./modules/kms"
  
  rotation_enabled = var.kms_key_rotation_enabled
}

# IAM Roles & Policies
module "iam" {
  source = "./modules/iam"
  
  ecs_task_role_name = "ticketdesk-ecs-task-role"
  
  # Permisos mínimos
  s3_buckets   = [module.s3.transcriptions_bucket_arn, module.s3.reports_bucket_arn]
  rds_arn      = module.rds.db_instance_arn
  kms_key_arns = [module.kms.rds_key_arn, module.kms.s3_key_arn]
}

# Application Load Balancer
module "alb" {
  source = "./modules/alb"
  
  vpc_id = module.vpc.vpc_id
  subnets = module.vpc.public_subnet_ids
  
  # Target groups para cada servicio
  backend_target_group_arn    = module.ecs_services.backend_target_group_arn
  botengine_target_group_arn  = module.ecs_services.botengine_target_group_arn
  evaluation_target_group_arn = module.ecs_services.evaluation_target_group_arn
  compliance_target_group_arn = module.ecs_services.compliance_target_group_arn
}

# CloudWatch Monitoring
module "cloudwatch" {
  source = "./modules/cloudwatch"
  
  log_retention_days = var.cloudwatch_log_retention_days
  
  # Alarms
  alarm_sns_topic_arn = aws_sns_topic.alerts.arn
  
  depends_on = [module.ecs_services, module.rds]
}

# Route53 DNS
module "route53" {
  source = "./modules/route53"
  
  domain_name       = "ticketdesk.com"
  alb_dns_name      = module.alb.dns_name
  alb_zone_id       = module.alb.zone_id
}

# SNS for Alerts
resource "aws_sns_topic" "alerts" {
  name = "ticketdesk-alerts"
}

resource "aws_sns_topic_subscription" "alerts_email" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = "oncall@ticketdesk.com"
}
```

---

## ✅ Validación Post-Deploy

```bash
# 1. Verificar recursos creados
terraform state list | wc -l
# Output: 47 resources

# 2. Obtener outputs
terraform output -json | jq .

# 3. Healthcheck manual
curl https://api.ticketdesk.com/health
curl https://api.ticketdesk.com/botengine/health

# 4. Database connectivity
psql -h $(terraform output -raw rds_endpoint | cut -d: -f1) \
     -U ticketdesk_user \
     -d ticketdesk \
     -c "SELECT version();"

# 5. Redis connectivity
redis-cli -h $(terraform output -raw elasticache_endpoint) ping
# Output: PONG

# 6. CloudWatch logs
aws logs tail /ticketdesk/backend --follow

# 7. ECS tasks running
aws ecs list-tasks --cluster ticketdesk-prod --launch-type FARGATE
```

---

## 🔄 State Management

```bash
# Backup state actual
terraform state pull > backup-$(date +%s).tfstate

# Ver recursos en state
terraform state list

# Mostrar recurso específico
terraform state show aws_rds_cluster_instance.main

# Remover de state (sin destruir en AWS)
terraform state rm aws_s3_bucket.old_bucket  # Usar con cuidado

# Restaurar desde backup
terraform state push backup-1234567890.tfstate
```

---

## 🚨 Troubleshooting

### Error: "Error acquiring the state lock"
```bash
# Alguien más está aplicando cambios
# Esperar a que terminen o force-unlock
terraform force-unlock <lock-id>
```

### Error: "Instance type not available"
```bash
# Cambiar instance type en variables.tf
rds_instance_class = "db.r6i.large"  # Más pequeño
terraform apply
```

### Error: "Insufficient capacity"
```bash
# AWS no tiene capacidad en esa AZ
# Cambiar availability_zones en variables.tf
availability_zones = ["us-east-1c", "us-east-1d"]
```

---

## 📊 Costo Estimado (Mensual)

| Recurso | Cantidad | Costo |
|---|---|---|
| ECS Fargate | 12 tasks | $1,200 |
| RDS r6i.xlarge | 1 Multi-AZ | $800 |
| ElastiCache r6g.xlarge | 3 nodes | $600 |
| ALB | 1 | $150 |
| S3 + NAT | - | $300 |
| CloudWatch | Logs + Metrics | $100 |
| **TOTAL** | | **~$3,150** |

---

## 🔒 Security Checklist

- [ ] Secrets en Secrets Manager (no en Terraform)
- [ ] RDS backup retenidos 30 días
- [ ] KMS key rotation enabled
- [ ] VPC security groups restrictivos (ingress only needed)
- [ ] RLS en PostgreSQL
- [ ] S3 versioning + encryption
- [ ] CloudWatch Logs 7 años retención (LGPD)
- [ ] ALB HTTPS/TLS 1.3
- [ ] No public IPs en RDS

---

## 📞 Support

- **Terraform docs**: https://registry.terraform.io/providers/hashicorp/aws/latest/docs
- **State issues**: https://www.terraform.io/docs/state/locking.html
- **AWS support**: AWS Console → Support Center

---

**Generado**: 2026-05-27  
**Ambiente**: Production  
**Status**: Ready to deploy ✅
