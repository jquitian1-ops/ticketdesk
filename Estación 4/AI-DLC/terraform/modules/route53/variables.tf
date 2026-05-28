# Route53 Module - Input Variables

variable "domain_name" {
  description = "Domain name for the application (e.g., ticketdesk.example.com)"
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-]*[a-z0-9]\\.[a-z]{2,}$", var.domain_name))
    error_message = "Domain name must be a valid FQDN."
  }
}

variable "alb_dns_name" {
  description = "ALB DNS name"
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9-]+\\.elb\\.[a-z0-9-]+\\.amazonaws\\.com$", var.alb_dns_name))
    error_message = "ALB DNS name must be a valid AWS ALB DNS name."
  }
}

variable "alb_zone_id" {
  description = "ALB zone ID (for Route53 alias)"
  type        = string

  validation {
    condition     = startswith(var.alb_zone_id, "Z")
    error_message = "ALB zone ID must start with 'Z'."
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
