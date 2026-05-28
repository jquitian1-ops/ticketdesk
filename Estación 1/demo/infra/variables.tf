variable "environment" {
  description = "Environment name (dev, demo, prod)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "demo", "prod"], var.environment)
    error_message = "environment must be one of: dev, demo, prod"
  }
}

variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

# Troubleshooting #21: cors_origins MUST be list(string) to support multiple
# environments (localhost dev + Vercel prod). Using a string forces manual
# AWS CLI fixes that the next terraform apply reverts.
variable "cors_origins" {
  description = "Allowed CORS origins for API Gateway and S3 bucket"
  type        = list(string)
  default     = ["http://localhost:3000"]
}

variable "admin_token" {
  description = "Admin API token for protected endpoints"
  type        = string
  sensitive   = true
}

variable "new_relic_license_key" {
  description = "New Relic license key for OTLP export"
  type        = string
  sensitive   = true
  default     = ""
}

variable "session_code" {
  description = "Default session code"
  type        = string
  default     = "LATAM2026"
}

variable "lambda_memory" {
  description = "Lambda function memory in MB"
  type        = number
  default     = 256
}

variable "lambda_timeout" {
  description = "Lambda function timeout in seconds"
  type        = number
  default     = 30
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 7
}
