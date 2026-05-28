variable "aws_region" {
  type        = string
  default     = "us-south-1"
  description = "AWS region for deployment"
}

variable "environment" {
  type        = string
  description = "Environment name (development, staging, production)"

  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be development, staging, or production."
  }
}

variable "project_name" {
  type        = string
  default     = "ticketdesk"
  description = "Project name for resource naming"
}

variable "vpc_cidr" {
  type        = string
  default     = "10.0.0.0/16"
  description = "VPC CIDR block"
}

variable "availability_zones" {
  type        = list(string)
  default     = ["us-south-1a", "us-south-1b"]
  description = "Availability zones for multi-AZ setup"
}

variable "db_instance_class" {
  type        = string
  default     = "db.t3.small"
  description = "RDS instance class"
}

variable "rds_allocated_storage" {
  type        = number
  default     = 100
  description = "RDS allocated storage in GB"
}

variable "database_name" {
  type        = string
  default     = "ticketdesk"
  description = "RDS database name"
}

variable "database_username" {
  type        = string
  description = "RDS database master username"
  sensitive   = true
}

variable "redis_node_type" {
  type        = string
  default     = "cache.t3.micro"
  description = "ElastiCache node type"
}

variable "certificate_arn" {
  type        = string
  description = "ACM certificate ARN for HTTPS"
}

variable "backend_image" {
  type        = string
  description = "Docker image URI for backend (ECR)"
}

variable "frontend_image" {
  type        = string
  description = "Docker image URI for frontend (ECR)"
}

variable "log_retention_days" {
  type        = number
  default     = 30
  description = "CloudWatch log retention in days"
}

variable "domain_name" {
  type        = string
  description = "Domain name for Route53 (e.g., ticketdesk.example.com)"
}

variable "database_password" {
  type        = string
  sensitive   = true
  description = "RDS database master password (min 8 characters)"

  validation {
    condition     = length(var.database_password) >= 8
    error_message = "Database password must be at least 8 characters."
  }
}

variable "postgres_version" {
  type        = string
  default     = "15.3"
  description = "PostgreSQL version (14.x, 15.x, or 16.x)"
}

variable "redis_version" {
  type        = string
  default     = "7.1"
  description = "Redis version (7.0 or 7.1)"
}

variable "redis_auth_token" {
  type        = string
  sensitive   = true
  description = "Redis auth token for secure authentication (16-128 characters)"

  validation {
    condition     = length(var.redis_auth_token) >= 16 && length(var.redis_auth_token) <= 128
    error_message = "Redis auth token must be 16-128 characters."
  }
}

variable "backend_cpu" {
  type        = number
  default     = 512
  description = "CPU units for backend task (256, 512, 1024, 2048, 4096)"
}

variable "backend_memory" {
  type        = number
  default     = 1024
  description = "Memory (MB) for backend task"
}

variable "frontend_cpu" {
  type        = number
  default     = 256
  description = "CPU units for frontend task"
}

variable "frontend_memory" {
  type        = number
  default     = 512
  description = "Memory (MB) for frontend task"
}

variable "min_tasks" {
  type        = number
  default     = 2
  description = "Minimum number of ECS tasks (auto-scaling)"
}

variable "max_tasks" {
  type        = number
  default     = 10
  description = "Maximum number of ECS tasks (auto-scaling)"
}

variable "alert_email" {
  type        = string
  description = "Email address for SNS alert notifications"
}
