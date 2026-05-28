# RDS Module - Input Variables

variable "database_subnet_ids" {
  description = "List of database subnet IDs for Multi-AZ deployment"
  type        = list(string)

  validation {
    condition     = length(var.database_subnet_ids) >= 2
    error_message = "Must provide at least 2 database subnets for Multi-AZ."
  }
}

variable "rds_security_group_id" {
  description = "Security group ID for RDS instance"
  type        = string

  validation {
    condition     = startswith(var.rds_security_group_id, "sg-")
    error_message = "Security group ID must start with 'sg-'."
  }
}

variable "db_instance_class" {
  description = "RDS instance class (e.g., db.t4g.medium, db.r6g.large)"
  type        = string
  default     = "db.t4g.medium"

  validation {
    condition     = can(regex("^db\\.[a-z0-9]+\\.(micro|small|medium|large|xlarge|[0-9]*xlarge)$", var.db_instance_class))
    error_message = "Must be a valid RDS instance class."
  }
}

variable "postgres_version" {
  description = "PostgreSQL version (e.g., 15.3, 14.8)"
  type        = string
  default     = "15.3"

  validation {
    condition     = can(regex("^(14|15|16)\\.[0-9]+$", var.postgres_version))
    error_message = "PostgreSQL version must be 14.x, 15.x, or 16.x"
  }
}

variable "allocated_storage" {
  description = "Initial allocated storage in GB"
  type        = number
  default     = 100

  validation {
    condition     = var.allocated_storage >= 20 && var.allocated_storage <= 1000
    error_message = "Allocated storage must be between 20 and 1000 GB."
  }
}

variable "database_name" {
  description = "Initial database name"
  type        = string
  default     = "ticketdesk"

  validation {
    condition     = can(regex("^[a-zA-Z][a-zA-Z0-9_]*$", var.database_name))
    error_message = "Database name must start with a letter and contain only alphanumeric characters and underscores."
  }
}

variable "database_username" {
  description = "Master database username"
  type        = string
  sensitive   = true

  validation {
    condition     = length(var.database_username) >= 1 && length(var.database_username) <= 63
    error_message = "Database username must be 1-63 characters."
  }
}

variable "database_password" {
  description = "Master database password"
  type        = string
  sensitive   = true

  validation {
    condition     = length(var.database_password) >= 8
    error_message = "Database password must be at least 8 characters."
  }
}

variable "kms_key_id" {
  description = "KMS key ARN for RDS encryption at rest"
  type        = string

  validation {
    condition     = startswith(var.kms_key_id, "arn:aws:kms:")
    error_message = "KMS key ID must be an ARN starting with 'arn:aws:kms:'."
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

variable "sns_topic_arn" {
  description = "SNS topic ARN for CloudWatch alarm notifications"
  type        = string

  validation {
    condition     = startswith(var.sns_topic_arn, "arn:aws:sns:")
    error_message = "SNS topic ARN must start with 'arn:aws:sns:'."
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
