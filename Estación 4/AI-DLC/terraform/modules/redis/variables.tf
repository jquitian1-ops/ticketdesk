# Redis Module - Input Variables

variable "cache_subnet_ids" {
  description = "List of cache subnet IDs for Multi-AZ deployment"
  type        = list(string)

  validation {
    condition     = length(var.cache_subnet_ids) >= 2
    error_message = "Must provide at least 2 cache subnets for Multi-AZ."
  }
}

variable "redis_security_group_id" {
  description = "Security group ID for Redis cluster"
  type        = string

  validation {
    condition     = startswith(var.redis_security_group_id, "sg-")
    error_message = "Security group ID must start with 'sg-'."
  }
}

variable "redis_node_type" {
  description = "ElastiCache Redis node type (e.g., cache.t4g.small, cache.r6g.large)"
  type        = string
  default     = "cache.t4g.small"

  validation {
    condition     = can(regex("^cache\\.[a-z0-9]+\\.(micro|small|medium|large|xlarge|[0-9]*xlarge)$", var.redis_node_type))
    error_message = "Must be a valid ElastiCache node type."
  }
}

variable "redis_version" {
  description = "Redis version (e.g., 7.0, 7.1)"
  type        = string
  default     = "7.1"

  validation {
    condition     = can(regex("^7\\.[0-1]$", var.redis_version))
    error_message = "Redis version must be 7.0 or 7.1."
  }
}

variable "redis_auth_token" {
  description = "Redis auth token for secure authentication"
  type        = string
  sensitive   = true

  validation {
    condition     = length(var.redis_auth_token) >= 16 && length(var.redis_auth_token) <= 128
    error_message = "Redis auth token must be 16-128 characters."
  }
}

variable "kms_key_id" {
  description = "KMS key ARN for Redis encryption at rest"
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
