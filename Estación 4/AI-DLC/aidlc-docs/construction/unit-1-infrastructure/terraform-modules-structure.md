# Terraform Modules Structure — Unit 1: Infraestructura

**Propósito**: Especificar cómo se organiza el código Terraform en módulos reutilizables. Cada módulo es responsable de un área (VPC, RDS, ECS, etc.) y puede ser testeado y versionado independientemente.

---

## 1. ESTRUCTURA DE DIRECTORIOS

```
ticketdesk-infrastructure/
├── terraform/
│   ├── main.tf                          # Root module entry point
│   ├── variables.tf                     # Input variables
│   ├── outputs.tf                       # Output values
│   ├── backend.tf                       # Terraform state backend (S3 + DynamoDB lock)
│   ├── terraform.tfvars                 # Environment-specific values (GITIGNORED)
│   ├── terraform.tfvars.example         # Example (check in)
│   ├── .terraform/                      # Cache (GITIGNORED)
│   │
│   ├── modules/                         # Reusable modules
│   │   ├── vpc/
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   ├── outputs.tf
│   │   │   └── README.md
│   │   │
│   │   ├── security_groups/
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   ├── outputs.tf
│   │   │   └── README.md
│   │   │
│   │   ├── rds/
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   ├── outputs.tf
│   │   │   ├── password_rotation.tf
│   │   │   └── README.md
│   │   │
│   │   ├── redis/
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   ├── outputs.tf
│   │   │   └── README.md
│   │   │
│   │   ├── ecs/
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   ├── outputs.tf
│   │   │   ├── auto_scaling.tf
│   │   │   ├── services.tf
│   │   │   └── README.md
│   │   │
│   │   ├── alb/
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   ├── outputs.tf
│   │   │   └── README.md
│   │   │
│   │   ├── s3/
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   ├── outputs.tf
│   │   │   └── README.md
│   │   │
│   │   ├── ecr/
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   ├── outputs.tf
│   │   │   └── README.md
│   │   │
│   │   ├── cloudwatch/
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   ├── outputs.tf
│   │   │   ├── alarms.tf
│   │   │   └── README.md
│   │   │
│   │   ├── kms/
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   ├── outputs.tf
│   │   │   └── README.md
│   │   │
│   │   └── route53/
│   │       ├── main.tf
│   │       ├── variables.tf
│   │       ├── outputs.tf
│   │       └── README.md
│   │
│   ├── environments/                   # Environment-specific configs
│   │   ├── dev/
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   ├── terraform.tfvars
│   │   │   └── backend.tf
│   │   │
│   │   ├── staging/
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   ├── terraform.tfvars
│   │   │   └── backend.tf
│   │   │
│   │   └── production/
│   │       ├── main.tf
│   │       ├── variables.tf
│   │       ├── terraform.tfvars
│   │       └── backend.tf
│   │
│   └── tests/                          # Terratest tests
│       ├── go.mod
│       ├── go.sum
│       ├── vpc_test.go
│       ├── rds_test.go
│       ├── ecs_test.go
│       └── README.md
│
├── .gitignore
├── .github/
│   └── workflows/
│       └── terraform.yml
│
└── README.md
```

---

## 2. MÓDULOS DESCRITOS

### Módulo: VPC

**Responsabilidad**: Crear VPC, subnets (públicas/privadas), Internet Gateway, NAT Gateway, route tables.

**Inputs**:
```hcl
variable "vpc_cidr" {
  type        = string
  default     = "10.0.0.0/16"
  description = "VPC CIDR block"
}

variable "enable_nat_gateway" {
  type        = bool
  default     = true
  description = "Enable NAT Gateway for private subnets"
}

variable "availability_zones" {
  type        = list(string)
  default     = ["us-south-1a", "us-south-1b"]
  description = "AZs for multi-AZ setup"
}
```

**Outputs**:
```hcl
output "vpc_id" {
  value = aws_vpc.main.id
}

output "public_subnet_ids" {
  value = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  value = aws_subnet.private[*].id
}
```

### Módulo: Security Groups

**Responsabilidad**: Crear 4 security groups (ALB, ECS, RDS, Redis) con reglas de entrada/salida.

**Inputs**:
```hcl
variable "vpc_id" {
  type        = string
  description = "VPC ID"
}

variable "enable_alb_sg" {
  type        = bool
  default     = true
}

variable "alb_ingress_ports" {
  type        = list(number)
  default     = [80, 443]
}
```

**Outputs**:
```hcl
output "alb_sg_id" {
  value = aws_security_group.alb.id
}

output "ecs_sg_id" {
  value = aws_security_group.ecs.id
}

output "rds_sg_id" {
  value = aws_security_group.rds.id
}

output "redis_sg_id" {
  value = aws_security_group.redis.id
}
```

### Módulo: RDS

**Responsabilidad**: Crear RDS PostgreSQL Multi-AZ con backups, encryption, monitoring.

**Inputs**:
```hcl
variable "db_instance_class" {
  type        = string
  default     = "db.t3.small"
  description = "RDS instance type"
}

variable "allocated_storage" {
  type        = number
  default     = 100
  description = "Allocated storage in GB"
}

variable "backup_retention_period" {
  type        = number
  default     = 30
  description = "Backup retention days"
}

variable "multi_az" {
  type        = bool
  default     = true
  description = "Enable Multi-AZ"
}

variable "kms_key_id" {
  type        = string
  description = "KMS key for encryption"
}
```

**Outputs**:
```hcl
output "rds_endpoint" {
  value = aws_db_instance.postgres.endpoint
}

output "rds_arn" {
  value = aws_db_instance.postgres.arn
}
```

### Módulo: Redis (ElastiCache)

**Responsabilidad**: Crear ElastiCache Redis con encryption, auth token, monitoring.

**Inputs**:
```hcl
variable "node_type" {
  type        = string
  default     = "cache.t3.micro"
}

variable "engine_version" {
  type        = string
  default     = "7.0"
}

variable "auth_token_length" {
  type        = number
  default     = 32
  description = "Auth token length (min 32)"
}
```

**Outputs**:
```hcl
output "redis_endpoint" {
  value = aws_elasticache_cluster.redis.cache_nodes[0].address
}

output "redis_port" {
  value = aws_elasticache_cluster.redis.port
}

output "auth_token" {
  value     = aws_elasticache_cluster.redis.auth_token
  sensitive = true
}
```

### Módulo: ECS

**Responsabilidad**: Crear ECS cluster, task definitions (backend, frontend), services, auto-scaling.

**Sub-modules**:
- `ecs/main.tf`: Cluster definition
- `ecs/services.tf`: Service definitions for backend + frontend
- `ecs/auto_scaling.tf`: Target tracking auto-scaling policies

**Inputs**:
```hcl
variable "cluster_name" {
  type        = string
  default     = "ticketdesk-prod"
}

variable "desired_count" {
  type        = number
  default     = 2
  description = "Desired number of tasks"
}

variable "min_capacity" {
  type        = number
  default     = 2
}

variable "max_capacity" {
  type        = number
  default     = 10
}

variable "backend_image" {
  type        = string
  description = "ECR image URI for backend"
}

variable "frontend_image" {
  type        = string
  description = "ECR image URI for frontend"
}
```

**Outputs**:
```hcl
output "cluster_name" {
  value = aws_ecs_cluster.main.name
}

output "cluster_arn" {
  value = aws_ecs_cluster.main.arn
}

output "backend_service_name" {
  value = aws_ecs_service.backend.name
}

output "frontend_service_name" {
  value = aws_ecs_service.frontend.name
}
```

### Módulo: ALB

**Responsabilidad**: Crear Application Load Balancer con listeners, target groups, TLS certificate.

**Inputs**:
```hcl
variable "vpc_id" {
  type        = string
}

variable "subnet_ids" {
  type        = list(string)
  description = "Public subnet IDs for ALB"
}

variable "certificate_arn" {
  type        = string
  description = "ACM certificate ARN"
}

variable "backend_target_group_arn" {
  type        = string
}

variable "frontend_target_group_arn" {
  type        = string
}
```

**Outputs**:
```hcl
output "alb_dns_name" {
  value = aws_lb.main.dns_name
}

output "alb_arn" {
  value = aws_lb.main.arn
}

output "backend_target_group_arn" {
  value = aws_lb_target_group.backend.arn
}

output "frontend_target_group_arn" {
  value = aws_lb_target_group.frontend.arn
}
```

### Módulo: S3

**Responsabilidad**: Crear 3 buckets (transcriptions, audit-logs, knowledge-base) con versioning, encryption, lifecycle policies.

**Inputs**:
```hcl
variable "project_name" {
  type        = string
  default     = "ticketdesk"
}

variable "environment" {
  type        = string
  default     = "prod"
}

variable "kms_key_id" {
  type        = string
}

variable "enable_versioning" {
  type        = bool
  default     = true
}

variable "lifecycle_rules" {
  type = list(object({
    prefix              = string
    days_to_archive     = number
    days_to_expire      = number
  }))
  default = [
    {
      prefix          = "transcriptions/"
      days_to_archive = 90
      days_to_expire  = 365
    },
    {
      prefix          = "audit-logs/"
      days_to_archive = 2557  # 7 years
      days_to_expire  = 2557
    }
  ]
}
```

**Outputs**:
```hcl
output "transcriptions_bucket_name" {
  value = aws_s3_bucket.transcriptions.id
}

output "audit_logs_bucket_name" {
  value = aws_s3_bucket.audit_logs.id
}

output "knowledge_base_bucket_name" {
  value = aws_s3_bucket.knowledge_base.id
}
```

### Módulo: CloudWatch

**Responsabilidad**: Crear log groups, metric filters, alarms (SNS notifications).

**Inputs**:
```hcl
variable "log_retention_days" {
  type        = number
  default     = 30
}

variable "sns_topic_arn" {
  type        = string
  description = "SNS topic for critical alerts"
}

variable "alarm_actions" {
  type        = list(string)
  default     = []
}
```

**Outputs**:
```hcl
output "log_group_backend" {
  value = aws_cloudwatch_log_group.backend.name
}

output "log_group_rds" {
  value = aws_cloudwatch_log_group.rds.name
}
```

### Módulo: KMS

**Responsabilidad**: Crear KMS key con policy (access for RDS, Redis, S3, logs).

**Inputs**:
```hcl
variable "key_description" {
  type        = string
  default     = "KMS key for TicketDesk encryption"
}

variable "enable_rotation" {
  type        = bool
  default     = true
}

variable "rotation_period_days" {
  type        = number
  default     = 90
}
```

**Outputs**:
```hcl
output "kms_key_id" {
  value = aws_kms_key.primary.id
}

output "kms_key_arn" {
  value = aws_kms_key.primary.arn
}
```

### Módulo: Route53

**Responsabilidad**: Crear hosted zone, DNS records (api.ticketdesk.com, www.ticketdesk.com), health checks.

**Inputs**:
```hcl
variable "hosted_zone_name" {
  type        = string
  default     = "ticketdesk.com"
}

variable "alb_dns_name" {
  type        = string
}

variable "alb_zone_id" {
  type        = string
}
```

**Outputs**:
```hcl
output "hosted_zone_id" {
  value = aws_route53_zone.main.zone_id
}

output "api_record_fqdn" {
  value = aws_route53_record.api.fqdn
}
```

---

## 3. ROOT MODULE (main.tf)

```hcl
# Root module: orchestrates all modules

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "TicketDesk"
      Environment = var.environment
      ManagedBy   = "Terraform"
      CreatedAt   = timestamp()
    }
  }
}

# KMS key (must come first for encryption)
module "kms" {
  source = "./modules/kms"
  key_description = "KMS key for TicketDesk ${var.environment}"
}

# VPC & Networking
module "vpc" {
  source = "./modules/vpc"
  vpc_cidr = var.vpc_cidr
  availability_zones = var.availability_zones
}

# Security Groups
module "security_groups" {
  source = "./modules/security_groups"
  vpc_id = module.vpc.vpc_id
}

# RDS Database
module "rds" {
  source = "./modules/rds"
  subnet_ids = module.vpc.database_subnet_ids
  security_group_id = module.security_groups.rds_sg_id
  kms_key_id = module.kms.kms_key_id
  allocated_storage = var.rds_allocated_storage
}

# Redis Cache
module "redis" {
  source = "./modules/redis"
  subnet_group_name = aws_elasticache_subnet_group.default.name
  security_group_id = module.security_groups.redis_sg_id
  kms_key_id = module.kms.kms_key_id
}

# S3 Buckets
module "s3" {
  source = "./modules/s3"
  project_name = var.project_name
  environment = var.environment
  kms_key_id = module.kms.kms_key_id
}

# ECR Repositories
module "ecr" {
  source = "./modules/ecr"
  repository_names = ["backend", "frontend"]
}

# ALB & Networking
module "alb" {
  source = "./modules/alb"
  vpc_id = module.vpc.vpc_id
  subnet_ids = module.vpc.public_subnet_ids
  security_group_id = module.security_groups.alb_sg_id
  certificate_arn = var.certificate_arn
}

# ECS Cluster & Services
module "ecs" {
  source = "./modules/ecs"
  cluster_name = var.cluster_name
  vpc_id = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  security_group_id = module.security_groups.ecs_sg_id
  backend_image = var.backend_image
  frontend_image = var.frontend_image
  rds_endpoint = module.rds.rds_endpoint
  redis_endpoint = module.redis.redis_endpoint
}

# CloudWatch Monitoring
module "cloudwatch" {
  source = "./modules/cloudwatch"
  log_retention_days = var.log_retention_days
  sns_topic_arn = aws_sns_topic.critical_alerts.arn
}

# Route53 DNS
module "route53" {
  source = "./modules/route53"
  hosted_zone_name = var.hosted_zone_name
  alb_dns_name = module.alb.alb_dns_name
  alb_zone_id = module.alb.alb_zone_id
}
```

---

## 4. VARIABLES & OUTPUTS

### Root variables.tf

```hcl
variable "aws_region" {
  type        = string
  default     = "us-south-1"
}

variable "environment" {
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "project_name" {
  type    = string
  default = "ticketdesk"
}

variable "vpc_cidr" {
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  type        = list(string)
  default     = ["us-south-1a", "us-south-1b"]
}

variable "cluster_name" {
  type        = string
  default     = "ticketdesk-prod"
}

variable "rds_allocated_storage" {
  type        = number
  default     = 100
  description = "RDS allocated storage in GB"
}

variable "certificate_arn" {
  type        = string
  description = "ACM certificate ARN for HTTPS"
}

variable "backend_image" {
  type        = string
  description = "ECR image URI for backend"
}

variable "frontend_image" {
  type        = string
  description = "ECR image URI for frontend"
}

variable "log_retention_days" {
  type        = number
  default     = 30
}

variable "hosted_zone_name" {
  type        = string
  default     = "ticketdesk.com"
}
```

### Root outputs.tf

```hcl
output "vpc_id" {
  value = module.vpc.vpc_id
}

output "alb_dns_name" {
  value = module.alb.alb_dns_name
}

output "rds_endpoint" {
  value = module.rds.rds_endpoint
  sensitive = true
}

output "redis_endpoint" {
  value = module.redis.redis_endpoint
  sensitive = true
}

output "ecs_cluster_name" {
  value = module.ecs.cluster_name
}

output "ecr_backend_url" {
  value = module.ecr.backend_repository_url
}

output "ecr_frontend_url" {
  value = module.ecr.frontend_repository_url
}
```

---

## 5. BACKEND CONFIGURATION

### backend.tf

```hcl
# Terraform state stored in S3 with DynamoDB lock

terraform {
  backend "s3" {
    bucket           = "ticketdesk-terraform-state"
    key              = "prod/terraform.tfstate"
    region           = "us-south-1"
    encrypt          = true
    dynamodb_table   = "terraform-lock"
    skip_credentials_validation = false
  }
}
```

**Pre-requisites** (one-time setup):
```bash
# Create S3 bucket for state
aws s3api create-bucket \
  --bucket ticketdesk-terraform-state \
  --region us-south-1 \
  --create-bucket-configuration LocationConstraint=us-south-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket ticketdesk-terraform-state \
  --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption \
  --bucket ticketdesk-terraform-state \
  --server-side-encryption-configuration '{...}'

# Create DynamoDB table for locks
aws dynamodb create-table \
  --table-name terraform-lock \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

---

## 6. TESTING (Terratest)

### Example test: vpc_test.go

```go
package test

import (
    "testing"
    "github.com/gruntwork-io/terratest/modules/terraform"
    "github.com/stretchr/testify/assert"
)

func TestVPCCreation(t *testing.T) {
    terraformOptions := &terraform.Options{
        TerraformDir: "../",
        Vars: map[string]interface{}{
            "environment": "test",
        },
    }

    defer terraform.Destroy(t, terraformOptions)
    terraform.InitAndApply(t, terraformOptions)

    vpcId := terraform.Output(t, terraformOptions, "vpc_id")
    assert.NotEmpty(t, vpcId)
}
```

---

## 7. DEPLOYMENT WORKFLOW

### Plan & Apply

```bash
# Initialize (downloads providers, modules)
terraform init

# Plan (preview changes)
terraform plan -out=tfplan

# Review tfplan (human approval)
cat tfplan

# Apply (create/modify resources)
terraform apply tfplan

# Verify
terraform state list
terraform show
```

### Destroy (cleanup)

```bash
terraform destroy -auto-approve  # Only for dev/test, never for prod
```

---

**Artefacto para**: Unit 1 - Infraestructura  
**Fecha**: 2026-05-27  
**Proyecto**: TicketDesk Enterprise v1.0  
**Fase**: Construction - Estación 5, Actividad 3
