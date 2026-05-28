# S3 Module - Input Variables

variable "kms_key_id" {
  description = "KMS key ARN for S3 encryption at rest"
  type        = string

  validation {
    condition     = startswith(var.kms_key_id, "arn:aws:kms:")
    error_message = "KMS key ID must be an ARN starting with 'arn:aws:kms:'."
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
