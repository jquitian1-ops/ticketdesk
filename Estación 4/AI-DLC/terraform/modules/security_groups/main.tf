# Security Groups Module - TicketDesk Enterprise
# Manages ingress/egress rules for all application components
# 4 Security Groups: ALB, ECS, RDS, Redis

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# ALB Security Group - public facing, allows HTTP/HTTPS from internet
resource "aws_security_group" "alb" {
  name_prefix = "${var.project_name}-alb-"
  description = "Security group for Application Load Balancer"
  vpc_id      = var.vpc_id

  tags = {
    Name        = "${var.project_name}-alb-sg"
    Environment = var.environment
  }

  lifecycle {
    create_before_destroy = true
  }
}

# ALB Ingress: HTTP from anywhere (redirect to HTTPS)
resource "aws_vpc_security_group_ingress_rule" "alb_http" {
  security_group_id = aws_security_group.alb.id
  description       = "HTTP from internet (redirect to HTTPS)"
  from_port         = 80
  to_port           = 80
  ip_protocol       = "tcp"
  cidr_ipv4         = "0.0.0.0/0"

  tags = {
    Name = "${var.project_name}-alb-http"
  }
}

# ALB Ingress: HTTPS from anywhere
resource "aws_vpc_security_group_ingress_rule" "alb_https" {
  security_group_id = aws_security_group.alb.id
  description       = "HTTPS from internet"
  from_port         = 443
  to_port           = 443
  ip_protocol       = "tcp"
  cidr_ipv4         = "0.0.0.0/0"

  tags = {
    Name = "${var.project_name}-alb-https"
  }
}

# ALB Egress: to ECS (port 8000 backend, 3000 frontend)
resource "aws_vpc_security_group_egress_rule" "alb_to_ecs_backend" {
  security_group_id = aws_security_group.alb.id
  description       = "ALB to ECS backend (FastAPI)"
  from_port         = 8000
  to_port           = 8000
  ip_protocol       = "tcp"
  cidr_ipv4         = var.vpc_cidr

  tags = {
    Name = "${var.project_name}-alb-to-backend"
  }
}

resource "aws_vpc_security_group_egress_rule" "alb_to_ecs_frontend" {
  security_group_id = aws_security_group.alb.id
  description       = "ALB to ECS frontend (Next.js)"
  from_port         = 3000
  to_port           = 3000
  ip_protocol       = "tcp"
  cidr_ipv4         = var.vpc_cidr

  tags = {
    Name = "${var.project_name}-alb-to-frontend"
  }
}

# ECS Security Group - accepts traffic from ALB, can reach RDS/Redis/S3
resource "aws_security_group" "ecs" {
  name_prefix = "${var.project_name}-ecs-"
  description = "Security group for ECS tasks"
  vpc_id      = var.vpc_id

  tags = {
    Name        = "${var.project_name}-ecs-sg"
    Environment = var.environment
  }

  lifecycle {
    create_before_destroy = true
  }
}

# ECS Ingress: from ALB (backend)
resource "aws_vpc_security_group_ingress_rule" "ecs_from_alb_backend" {
  security_group_id = aws_security_group.ecs.id
  description       = "ECS backend from ALB"
  from_port         = 8000
  to_port           = 8000
  ip_protocol       = "tcp"
  referenced_security_group_id = aws_security_group.alb.id

  tags = {
    Name = "${var.project_name}-ecs-from-alb-backend"
  }
}

# ECS Ingress: from ALB (frontend)
resource "aws_vpc_security_group_ingress_rule" "ecs_from_alb_frontend" {
  security_group_id = aws_security_group.ecs.id
  description       = "ECS frontend from ALB"
  from_port         = 3000
  to_port           = 3000
  ip_protocol       = "tcp"
  referenced_security_group_id = aws_security_group.alb.id

  tags = {
    Name = "${var.project_name}-ecs-from-alb-frontend"
  }
}

# ECS Ingress: task-to-task communication (for backend to frontend if needed)
resource "aws_vpc_security_group_ingress_rule" "ecs_self" {
  security_group_id = aws_security_group.ecs.id
  description       = "ECS task to task communication"
  from_port         = 3000
  to_port           = 8000
  ip_protocol       = "tcp"
  referenced_security_group_id = aws_security_group.ecs.id

  tags = {
    Name = "${var.project_name}-ecs-self"
  }
}

# ECS Egress: to RDS (port 5432)
resource "aws_vpc_security_group_egress_rule" "ecs_to_rds" {
  security_group_id = aws_security_group.ecs.id
  description       = "ECS to RDS PostgreSQL"
  from_port         = 5432
  to_port           = 5432
  ip_protocol       = "tcp"
  referenced_security_group_id = aws_security_group.rds

  tags = {
    Name = "${var.project_name}-ecs-to-rds"
  }
}

# ECS Egress: to Redis (port 6379)
resource "aws_vpc_security_group_egress_rule" "ecs_to_redis" {
  security_group_id = aws_security_group.ecs.id
  description       = "ECS to ElastiCache Redis"
  from_port         = 6379
  to_port           = 6379
  ip_protocol       = "tcp"
  referenced_security_group_id = aws_security_group.redis

  tags = {
    Name = "${var.project_name}-ecs-to-redis"
  }
}

# ECS Egress: to internet (for Claude API, S3, etc.)
resource "aws_vpc_security_group_egress_rule" "ecs_to_internet" {
  security_group_id = aws_security_group.ecs.id
  description       = "ECS to internet (Claude API, S3, etc.)"
  from_port         = 0
  to_port           = 65535
  ip_protocol       = "tcp"
  cidr_ipv4         = "0.0.0.0/0"

  tags = {
    Name = "${var.project_name}-ecs-to-internet"
  }
}

# RDS Security Group - accepts only from ECS, no public access
resource "aws_security_group" "rds" {
  name_prefix = "${var.project_name}-rds-"
  description = "Security group for RDS PostgreSQL (no public access)"
  vpc_id      = var.vpc_id

  tags = {
    Name        = "${var.project_name}-rds-sg"
    Environment = var.environment
  }

  lifecycle {
    create_before_destroy = true
  }
}

# RDS Ingress: only from ECS (port 5432)
resource "aws_vpc_security_group_ingress_rule" "rds_from_ecs" {
  security_group_id = aws_security_group.rds.id
  description       = "PostgreSQL access from ECS only"
  from_port         = 5432
  to_port           = 5432
  ip_protocol       = "tcp"
  referenced_security_group_id = aws_security_group.ecs

  tags = {
    Name = "${var.project_name}-rds-from-ecs"
  }
}

# RDS Egress: DENY all (RDS is a data store, no outbound traffic needed)
resource "aws_vpc_security_group_egress_rule" "rds_deny_all" {
  security_group_id = aws_security_group.rds.id
  description       = "Deny all outbound (data store only)"
  from_port         = 0
  to_port           = 65535
  ip_protocol       = "-1"
  cidr_ipv4         = "127.0.0.1/32"

  tags = {
    Name = "${var.project_name}-rds-deny-all"
  }
}

# Redis Security Group - accepts only from ECS, no public access
resource "aws_security_group" "redis" {
  name_prefix = "${var.project_name}-redis-"
  description = "Security group for ElastiCache Redis (no public access)"
  vpc_id      = var.vpc_id

  tags = {
    Name        = "${var.project_name}-redis-sg"
    Environment = var.environment
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Redis Ingress: only from ECS (port 6379)
resource "aws_vpc_security_group_ingress_rule" "redis_from_ecs" {
  security_group_id = aws_security_group.redis.id
  description       = "Redis access from ECS only"
  from_port         = 6379
  to_port           = 6379
  ip_protocol       = "tcp"
  referenced_security_group_id = aws_security_group.ecs

  tags = {
    Name = "${var.project_name}-redis-from-ecs"
  }
}

# Redis Egress: DENY all (cache, no outbound needed)
resource "aws_vpc_security_group_egress_rule" "redis_deny_all" {
  security_group_id = aws_security_group.redis.id
  description       = "Deny all outbound (cache only)"
  from_port         = 0
  to_port           = 65535
  ip_protocol       = "-1"
  cidr_ipv4         = "127.0.0.1/32"

  tags = {
    Name = "${var.project_name}-redis-deny-all"
  }
}
