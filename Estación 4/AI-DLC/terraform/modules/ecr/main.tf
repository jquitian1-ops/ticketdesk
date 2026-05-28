# ECR Module - Elastic Container Registry
# Stores Docker images for backend (FastAPI) and frontend (Next.js)
# Implements image scanning, lifecycle policies, encryption

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# ECR Repository - Backend
resource "aws_ecr_repository" "backend" {
  name_prefix            = "td-backend-"
  image_tag_mutability   = "MUTABLE"  # Allow re-tagging latest
  force_delete           = false

  image_scanning_configuration {
    scan_on_push = true  # Scan for vulnerabilities on push
  }

  encryption_configuration {
    encryption_type = "KMS"
    kms_key         = var.kms_key_id
  }

  tags = {
    Name        = "${var.project_name}-backend-repo"
    Environment = var.environment
  }
}

# ECR Lifecycle Policy - Backend (keep last 10 images, delete untagged)
resource "aws_ecr_lifecycle_policy" "backend" {
  repository = aws_ecr_repository.backend.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 tagged images"
        selection = {
          tagStatus           = "any"
          countType           = "imageCountMoreThan"
          countNumber         = 10
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 2
        description  = "Delete untagged images after 7 days"
        selection = {
          tagStatus           = "untagged"
          countType           = "sinceImagePushed"
          countUnit           = "days"
          countNumber         = 7
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# ECR Repository - Frontend
resource "aws_ecr_repository" "frontend" {
  name_prefix            = "td-frontend-"
  image_tag_mutability   = "MUTABLE"
  force_delete           = false

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "KMS"
    kms_key         = var.kms_key_id
  }

  tags = {
    Name        = "${var.project_name}-frontend-repo"
    Environment = var.environment
  }
}

# ECR Lifecycle Policy - Frontend
resource "aws_ecr_lifecycle_policy" "frontend" {
  repository = aws_ecr_repository.frontend.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 tagged images"
        selection = {
          tagStatus           = "any"
          countType           = "imageCountMoreThan"
          countNumber         = 10
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 2
        description  = "Delete untagged images after 7 days"
        selection = {
          tagStatus           = "untagged"
          countType           = "sinceImagePushed"
          countUnit           = "days"
          countNumber         = 7
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# CloudWatch Log Group for ECR Scan Results (if needed for compliance)
resource "aws_cloudwatch_log_group" "ecr_scan_logs" {
  name              = "/aws/ecr/${var.project_name}/scan-results"
  retention_in_days = var.log_retention_days

  tags = {
    Name        = "${var.project_name}-ecr-scan-logs"
    Environment = var.environment
  }
}

# EventBridge Rule - Trigger on ECR image push (for automated deployment)
resource "aws_cloudwatch_event_rule" "ecr_push" {
  name_prefix = "ecr-push-"
  description = "Trigger on ECR image push events"

  event_pattern = jsonencode({
    source      = ["aws.ecr"]
    detail-type = ["ECR Image Action"]
    detail = {
      action        = ["PUSH"]
      result        = ["SUCCESS"]
      "image-tag"   = ["latest", "main", "staging"]
    }
  })

  tags = {
    Environment = var.environment
  }
}

# Note: EventBridge target (e.g., CodeDeploy, Lambda) is defined in parent module
# This rule just captures push events for downstream processing
