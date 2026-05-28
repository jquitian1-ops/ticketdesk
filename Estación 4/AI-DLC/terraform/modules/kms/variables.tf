# KMS Module - Input Variables

variable "aws_account_id" {
  description = "AWS account ID"
  type        = string

  validation {
    condition     = can(regex("^[0-9]{12}$", var.aws_account_id))
    error_message = "AWS account ID must be 12 digits."
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

variable "ecs_task_execution_role_name" {
  description = "Name of ECS task execution role (for KMS access)"
  type        = string

  validation {
    condition     = length(var.ecs_task_execution_role_name) > 0
    error_message = "ECS task execution role name cannot be empty."
  }
}

variable "ecs_task_role_name" {
  description = "Name of ECS task role (for application KMS access)"
  type        = string

  validation {
    condition     = length(var.ecs_task_role_name) > 0
    error_message = "ECS task role name cannot be empty."
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
