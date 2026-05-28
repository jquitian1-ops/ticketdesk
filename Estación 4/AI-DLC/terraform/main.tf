# Root Module - TicketDesk Enterprise Infrastructure
# Orchestrates all 11 infrastructure modules

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
    }
  }
}

# KMS Key (encryption at rest) - MUST be first
module "kms" {
  source = "./modules/kms"

  aws_account_id                 = data.aws_caller_identity.current.account_id
  aws_region                     = var.aws_region
  project_name                   = var.project_name
  environment                    = var.environment
  ecs_task_execution_role_name   = module.ecs.ecs_task_execution_role_name
  ecs_task_role_name             = module.ecs.ecs_task_role_name
  sns_topic_arn                  = module.cloudwatch.sns_topic_arn

  depends_on = [module.cloudwatch]
}

# VPC & Networking
module "vpc" {
  source = "./modules/vpc"

  project_name          = var.project_name
  vpc_cidr              = var.vpc_cidr
  availability_zones    = var.availability_zones
  environment           = var.environment
  enable_nat_gateway    = true
  enable_vpn_gateway    = false
  enable_flow_logs      = true
}

# CloudWatch (for SNS topic) - Deploy early
module "cloudwatch" {
  source = "./modules/cloudwatch"

  alert_email         = var.alert_email
  log_retention_days  = var.log_retention_days
  aws_region          = var.aws_region
  project_name        = var.project_name
  environment         = var.environment
}

# Security Groups
module "security_groups" {
  source = "./modules/security_groups"

  vpc_id       = module.vpc.vpc_id
  vpc_cidr     = var.vpc_cidr
  project_name = var.project_name
  environment  = var.environment
}

# RDS Database (Multi-AZ PostgreSQL)
module "rds" {
  source = "./modules/rds"

  database_subnet_ids      = module.vpc.database_subnet_ids
  rds_security_group_id    = module.security_groups.rds_security_group_id
  db_instance_class        = var.db_instance_class
  postgres_version         = var.postgres_version
  allocated_storage        = var.rds_allocated_storage
  database_name            = var.database_name
  database_username        = var.database_username
  database_password        = var.database_password
  kms_key_id               = module.kms.key_arn
  log_retention_days       = var.log_retention_days
  sns_topic_arn            = module.cloudwatch.sns_topic_arn
  project_name             = var.project_name
  environment              = var.environment
}

# ElastiCache Redis (Multi-AZ with failover)
module "redis" {
  source = "./modules/redis"

  cache_subnet_ids        = module.vpc.private_subnet_ids
  redis_security_group_id = module.security_groups.redis_security_group_id
  redis_node_type         = var.redis_node_type
  redis_version           = var.redis_version
  redis_auth_token        = var.redis_auth_token
  kms_key_id              = module.kms.key_arn
  log_retention_days      = var.log_retention_days
  sns_topic_arn           = module.cloudwatch.sns_topic_arn
  project_name            = var.project_name
  environment             = var.environment
}

# S3 Buckets (Transcriptions, Uploads, Reports)
module "s3" {
  source = "./modules/s3"

  kms_key_id    = module.kms.key_arn
  sns_topic_arn = module.cloudwatch.sns_topic_arn
  project_name  = var.project_name
  environment   = var.environment
}

# ECR Repositories (Backend & Frontend)
module "ecr" {
  source = "./modules/ecr"

  kms_key_id         = module.kms.key_arn
  log_retention_days = var.log_retention_days
  project_name       = var.project_name
  environment        = var.environment
}

# Application Load Balancer (with health checks)
module "alb" {
  source = "./modules/alb"

  vpc_id                  = module.vpc.vpc_id
  public_subnet_ids       = module.vpc.public_subnet_ids
  alb_security_group_id   = module.security_groups.alb_security_group_id
  certificate_arn         = var.certificate_arn
  sns_topic_arn           = module.cloudwatch.sns_topic_arn
  project_name            = var.project_name
  environment             = var.environment
}

# ECS Cluster & Services (Backend + Frontend with auto-scaling)
module "ecs" {
  source = "./modules/ecs"

  private_subnet_ids              = module.vpc.private_subnet_ids
  ecs_security_group_id           = module.security_groups.ecs_security_group_id
  backend_image                   = var.backend_image
  frontend_image                  = var.frontend_image
  backend_cpu                     = var.backend_cpu
  backend_memory                  = var.backend_memory
  frontend_cpu                    = var.frontend_cpu
  frontend_memory                 = var.frontend_memory
  min_tasks                       = var.min_tasks
  max_tasks                       = var.max_tasks
  backend_target_group_arn        = module.alb.backend_target_group_arn
  frontend_target_group_arn       = module.alb.frontend_target_group_arn
  redis_endpoint                  = "${module.redis.redis_endpoint}"
  database_endpoint               = module.rds.rds_address
  database_username               = var.database_username
  database_password_secret_arn    = aws_secretsmanager_secret.db_password.arn
  s3_transcriptions_bucket_arn    = module.s3.transcriptions_bucket_arn
  s3_uploads_bucket_arn           = module.s3.uploads_bucket_arn
  s3_reports_bucket_arn           = module.s3.reports_bucket_arn
  kms_key_id                      = module.kms.key_arn
  api_url                         = "https://${var.domain_name}"
  log_retention_days              = var.log_retention_days
  aws_region                      = var.aws_region
  project_name                    = var.project_name
  environment                     = var.environment
}

# Route53 DNS
module "route53" {
  source = "./modules/route53"

  domain_name   = var.domain_name
  alb_dns_name  = module.alb.alb_dns_name
  alb_zone_id   = module.alb.alb_zone_id
  sns_topic_arn = module.cloudwatch.sns_topic_arn
  project_name  = var.project_name
  environment   = var.environment
}

# Secrets Manager - Database Password
resource "aws_secretsmanager_secret" "db_password" {
  name_prefix             = "${var.project_name}-db-password-"
  description             = "RDS database master password for ${var.project_name}"
  recovery_window_in_days = 7
  kms_key_id              = module.kms.key_id

  tags = {
    Name        = "${var.project_name}-db-password"
    Environment = var.environment
  }
}

resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id     = aws_secretsmanager_secret.db_password.id
  secret_string = var.database_password
}

# Get current AWS account ID
data "aws_caller_identity" "current" {}
