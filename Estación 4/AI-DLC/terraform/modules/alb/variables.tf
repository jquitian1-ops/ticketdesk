# ALB Module - Input Variables

variable "vpc_id" {
  description = "VPC ID where ALB will be created"
  type        = string

  validation {
    condition     = startswith(var.vpc_id, "vpc-")
    error_message = "VPC ID must start with 'vpc-'."
  }
}

variable "public_subnet_ids" {
  description = "List of public subnet IDs for ALB placement"
  type        = list(string)

  validation {
    condition     = length(var.public_subnet_ids) >= 2
    error_message = "Must provide at least 2 public subnets."
  }
}

variable "alb_security_group_id" {
  description = "Security group ID for ALB"
  type        = string

  validation {
    condition     = startswith(var.alb_security_group_id, "sg-")
    error_message = "Security group ID must start with 'sg-'."
  }
}

variable "certificate_arn" {
  description = "ACM certificate ARN for HTTPS"
  type        = string

  validation {
    condition     = startswith(var.certificate_arn, "arn:aws:acm:")
    error_message = "Certificate ARN must start with 'arn:aws:acm:'."
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
