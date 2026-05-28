# KMS Module - Key Management Service
# Encryption key for RDS, Redis, S3, ECR, CloudWatch Logs
# Implements key rotation, access controls

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# KMS Encryption Key
resource "aws_kms_key" "main" {
  description             = "KMS key for ${var.project_name} encryption at rest"
  deletion_window_in_days = 10  # Allow recovery
  enable_key_rotation     = true

  tags = {
    Name        = "${var.project_name}-key"
    Environment = var.environment
  }
}

# KMS Key Alias
resource "aws_kms_alias" "main" {
  name_prefix   = "${var.project_name}-"
  target_key_id = aws_kms_key.main.key_id
}

# Key Policy - Allow AWS services and account principals to use the key
resource "aws_kms_key_policy" "main" {
  key_id = aws_kms_key.main.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM Root Account"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${var.aws_account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "Allow RDS Encryption"
        Effect = "Allow"
        Principal = {
          Service = "rds.amazonaws.com"
        }
        Action = [
          "kms:Decrypt",
          "kms:GenerateDataKey",
          "kms:CreateGrant"
        ]
        Resource = "*"
      },
      {
        Sid    = "Allow ElastiCache Encryption"
        Effect = "Allow"
        Principal = {
          Service = "elasticache.amazonaws.com"
        }
        Action = [
          "kms:Decrypt",
          "kms:GenerateDataKey",
          "kms:CreateGrant"
        ]
        Resource = "*"
      },
      {
        Sid    = "Allow S3 Encryption"
        Effect = "Allow"
        Principal = {
          Service = "s3.amazonaws.com"
        }
        Action = [
          "kms:Decrypt",
          "kms:GenerateDataKey"
        ]
        Resource = "*"
      },
      {
        Sid    = "Allow ECR Encryption"
        Effect = "Allow"
        Principal = {
          Service = "ecr.amazonaws.com"
        }
        Action = [
          "kms:Decrypt",
          "kms:GenerateDataKey"
        ]
        Resource = "*"
      },
      {
        Sid    = "Allow CloudWatch Logs Encryption"
        Effect = "Allow"
        Principal = {
          Service = "logs.${var.aws_region}.amazonaws.com"
        }
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:CreateGrant",
          "kms:DescribeKey"
        ]
        Resource = "*"
        Condition = {
          ArnLike = {
            "kms:EncryptionContext:aws:logs:arn" = "arn:aws:logs:${var.aws_region}:${var.aws_account_id}:*"
          }
        }
      },
      {
        Sid    = "Allow ECS Task Execution Role"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${var.aws_account_id}:role/${var.ecs_task_execution_role_name}"
        }
        Action = [
          "kms:Decrypt",
          "kms:DescribeKey"
        ]
        Resource = "*"
      },
      {
        Sid    = "Allow Application to Decrypt Secrets"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${var.aws_account_id}:role/${var.ecs_task_role_name}"
        }
        Action = [
          "kms:Decrypt",
          "kms:DescribeKey"
        ]
        Resource = "*"
      }
    ]
  })
}

# CloudWatch Alarm - Key Pending Deletion
resource "aws_cloudwatch_metric_alarm" "kms_key_pending_deletion" {
  alarm_name          = "${var.project_name}-kms-key-pending-deletion"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = "KeyDisabled"
  namespace           = "AWS/KMS"
  period              = "3600"
  statistic           = "Maximum"
  threshold           = "1"
  alarm_description   = "Alert if KMS key is pending deletion"
  alarm_actions       = [var.sns_topic_arn]

  dimensions = {
    KeyId = aws_kms_key.main.id
  }

  tags = {
    Environment = var.environment
  }
}
