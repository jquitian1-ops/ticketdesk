# ECS Module - Input Variables

variable "private_subnet_ids" {
  description = "List of private subnet IDs for ECS task placement"
  type        = list(string)

  validation {
    condition     = length(var.private_subnet_ids) >= 2
    error_message = "Must provide at least 2 private subnets."
  }
}

variable "ecs_security_group_id" {
  description = "Security group ID for ECS tasks"
  type        = string

  validation {
    condition     = startswith(var.ecs_security_group_id, "sg-")
    error_message = "Security group ID must start with 'sg-'."
  }
}

variable "backend_image" {
  description = "Docker image URI for backend service (ECR)"
  type        = string

  validation {
    condition     = can(regex("^[0-9]{12}\\.dkr\\.ecr\\.[a-z0-9-]+\\.amazonaws\\.com/.+:.+$", var.backend_image))
    error_message = "Backend image must be a valid ECR image URI (e.g., 123456789012.dkr.ecr.us-south-1.amazonaws.com/ticketdesk-backend:latest)"
  }
}

variable "frontend_image" {
  description = "Docker image URI for frontend service (ECR)"
  type        = string

  validation {
    condition     = can(regex("^[0-9]{12}\\.dkr\\.ecr\\.[a-z0-9-]+\\.amazonaws\\.com/.+:.+$", var.frontend_image))
    error_message = "Frontend image must be a valid ECR image URI (e.g., 123456789012.dkr.ecr.us-south-1.amazonaws.com/ticketdesk-frontend:latest)"
  }
}

variable "backend_cpu" {
  description = "CPU units for backend task (256=0.25vCPU, 512=0.5vCPU, 1024=1vCPU, 2048=2vCPU, 4096=4vCPU)"
  type        = number
  default     = 512

  validation {
    condition     = contains([256, 512, 1024, 2048, 4096], var.backend_cpu)
    error_message = "CPU must be 256, 512, 1024, 2048, or 4096."
  }
}

variable "backend_memory" {
  description = "Memory (MB) for backend task"
  type        = number
  default     = 1024

  validation {
    condition     = var.backend_memory >= 512 && var.backend_memory <= 30720
    error_message = "Memory must be 512-30720 MB."
  }
}

variable "frontend_cpu" {
  description = "CPU units for frontend task"
  type        = number
  default     = 256

  validation {
    condition     = contains([256, 512, 1024, 2048, 4096], var.frontend_cpu)
    error_message = "CPU must be 256, 512, 1024, 2048, or 4096."
  }
}

variable "frontend_memory" {
  description = "Memory (MB) for frontend task"
  type        = number
  default     = 512

  validation {
    condition     = var.frontend_memory >= 512 && var.frontend_memory <= 30720
    error_message = "Memory must be 512-30720 MB."
  }
}

variable "min_tasks" {
  description = "Minimum number of tasks (for auto-scaling)"
  type        = number
  default     = 2

  validation {
    condition     = var.min_tasks >= 1 && var.min_tasks <= 10
    error_message = "Min tasks must be 1-10."
  }
}

variable "max_tasks" {
  description = "Maximum number of tasks (for auto-scaling)"
  type        = number
  default     = 10

  validation {
    condition     = var.max_tasks >= 2 && var.max_tasks <= 20
    error_message = "Max tasks must be 2-20."
  }
}

variable "backend_target_group_arn" {
  description = "Backend ALB target group ARN"
  type        = string

  validation {
    condition     = startswith(var.backend_target_group_arn, "arn:aws:elasticloadbalancing:")
    error_message = "Target group ARN must start with 'arn:aws:elasticloadbalancing:'."
  }
}

variable "frontend_target_group_arn" {
  description = "Frontend ALB target group ARN"
  type        = string

  validation {
    condition     = startswith(var.frontend_target_group_arn, "arn:aws:elasticloadbalancing:")
    error_message = "Target group ARN must start with 'arn:aws:elasticloadbalancing:'."
  }
}

variable "redis_endpoint" {
  description = "Redis endpoint (host:port)"
  type        = string
  sensitive   = true

  validation {
    condition     = can(regex("^[a-z0-9.-]+:\\d+$", var.redis_endpoint))
    error_message = "Redis endpoint must be in format host:port."
  }
}

variable "database_endpoint" {
  description = "RDS database endpoint (host only, no port)"
  type        = string
  sensitive   = true
}

variable "database_username" {
  description = "RDS database username"
  type        = string
  sensitive   = true
}

variable "database_password_secret_arn" {
  description = "AWS Secrets Manager ARN for database password"
  type        = string

  validation {
    condition     = startswith(var.database_password_secret_arn, "arn:aws:secretsmanager:")
    error_message = "Secret ARN must start with 'arn:aws:secretsmanager:'."
  }
}

variable "s3_transcriptions_bucket_arn" {
  description = "S3 bucket ARN for transcriptions"
  type        = string

  validation {
    condition     = startswith(var.s3_transcriptions_bucket_arn, "arn:aws:s3:::")
    error_message = "S3 bucket ARN must start with 'arn:aws:s3:::'."
  }
}

variable "s3_uploads_bucket_arn" {
  description = "S3 bucket ARN for user uploads"
  type        = string

  validation {
    condition     = startswith(var.s3_uploads_bucket_arn, "arn:aws:s3:::")
    error_message = "S3 bucket ARN must start with 'arn:aws:s3:::'."
  }
}

variable "s3_reports_bucket_arn" {
  description = "S3 bucket ARN for generated reports"
  type        = string

  validation {
    condition     = startswith(var.s3_reports_bucket_arn, "arn:aws:s3:::")
    error_message = "S3 bucket ARN must start with 'arn:aws:s3:::'."
  }
}

variable "kms_key_id" {
  description = "KMS key ARN for encryption"
  type        = string

  validation {
    condition     = startswith(var.kms_key_id, "arn:aws:kms:")
    error_message = "KMS key ID must be an ARN starting with 'arn:aws:kms:'."
  }
}

variable "api_url" {
  description = "Public API URL (for frontend to call backend)"
  type        = string

  validation {
    condition     = can(regex("^https?://", var.api_url))
    error_message = "API URL must start with http:// or https://."
  }
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30

  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653], var.log_retention_days)
    error_message = "Log retention must be a valid CloudWatch value."
  }
}

variable "aws_region" {
  description = "AWS region"
  type        = string

  validation {
    condition     = can(regex("^[a-z]{2}-[a-z]+-[0-9]$", var.aws_region))
    error_message = "Invalid AWS region format."
  }
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string

  validation {
    condition     = length(var.project_name) > 0 && length(var.project_name) <= 32
    error_message = "Project name must be 1-32 characters."
  }
}

variable "environment" {
  description = "Environment name (development, staging, production)"
  type        = string

  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be one of: development, staging, production."
  }
}
