# S3 Module - Object Storage
# TicketDesk Enterprise requires 3 S3 buckets:
# 1. Transcriptions: Audio files from screening interviews
# 2. Uploads: User-uploaded files (resumes, etc.)
# 3. Reports: Generated evaluation reports
#
# All buckets have:
# - Encryption at rest (KMS)
# - Versioning enabled
# - Public access blocked
# - Lifecycle policies

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Bucket 1: Transcriptions
resource "aws_s3_bucket" "transcriptions" {
  bucket_prefix = "${var.project_name}-transcriptions-"

  tags = {
    Name        = "${var.project_name}-transcriptions"
    Environment = var.environment
    Purpose     = "Audio transcriptions from screening"
  }
}

# Block Public Access - Transcriptions
resource "aws_s3_bucket_public_access_block" "transcriptions" {
  bucket = aws_s3_bucket.transcriptions.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Versioning - Transcriptions
resource "aws_s3_bucket_versioning" "transcriptions" {
  bucket = aws_s3_bucket.transcriptions.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Encryption - Transcriptions
resource "aws_s3_bucket_server_side_encryption_configuration" "transcriptions" {
  bucket = aws_s3_bucket.transcriptions.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = var.kms_key_id
    }
  }
}

# Lifecycle Policy - Transcriptions (transition to cheaper storage after 90 days)
resource "aws_s3_bucket_lifecycle_configuration" "transcriptions" {
  bucket = aws_s3_bucket.transcriptions.id

  rule {
    id     = "archive-old-transcriptions"
    status = "Enabled"

    noncurrent_version_transition {
      noncurrent_days = 30
      storage_class   = "GLACIER"
    }

    noncurrent_version_expiration {
      noncurrent_days = 365  # Delete versions older than 1 year
    }

    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    expiration {
      days = 2555  # 7 years for compliance (LGPD)
    }
  }
}

# Bucket 2: Uploads
resource "aws_s3_bucket" "uploads" {
  bucket_prefix = "${var.project_name}-uploads-"

  tags = {
    Name        = "${var.project_name}-uploads"
    Environment = var.environment
    Purpose     = "User-uploaded files"
  }
}

# Block Public Access - Uploads
resource "aws_s3_bucket_public_access_block" "uploads" {
  bucket = aws_s3_bucket.uploads.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Versioning - Uploads
resource "aws_s3_bucket_versioning" "uploads" {
  bucket = aws_s3_bucket.uploads.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Encryption - Uploads
resource "aws_s3_bucket_server_side_encryption_configuration" "uploads" {
  bucket = aws_s3_bucket.uploads.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = var.kms_key_id
    }
  }
}

# Lifecycle Policy - Uploads (delete after 30 days per LGPD data retention)
resource "aws_s3_bucket_lifecycle_configuration" "uploads" {
  bucket = aws_s3_bucket.uploads.id

  rule {
    id     = "delete-old-uploads"
    status = "Enabled"

    noncurrent_version_expiration {
      noncurrent_days = 30
    }

    expiration {
      days = 30  # LGPD: delete user data after retention period
    }
  }
}

# Bucket 3: Reports
resource "aws_s3_bucket" "reports" {
  bucket_prefix = "${var.project_name}-reports-"

  tags = {
    Name        = "${var.project_name}-reports"
    Environment = var.environment
    Purpose     = "Generated evaluation reports"
  }
}

# Block Public Access - Reports
resource "aws_s3_bucket_public_access_block" "reports" {
  bucket = aws_s3_bucket.reports.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Versioning - Reports
resource "aws_s3_bucket_versioning" "reports" {
  bucket = aws_s3_bucket.reports.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Encryption - Reports
resource "aws_s3_bucket_server_side_encryption_configuration" "reports" {
  bucket = aws_s3_bucket.reports.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = var.kms_key_id
    }
  }
}

# Lifecycle Policy - Reports (archive to Glacier after 1 year, keep for 7 years)
resource "aws_s3_bucket_lifecycle_configuration" "reports" {
  bucket = aws_s3_bucket.reports.id

  rule {
    id     = "archive-old-reports"
    status = "Enabled"

    noncurrent_version_transition {
      noncurrent_days = 90
      storage_class   = "GLACIER"
    }

    noncurrent_version_expiration {
      noncurrent_days = 2555  # 7 years
    }

    transition {
      days          = 365
      storage_class = "GLACIER"
    }

    expiration {
      days = 2555  # 7 years for compliance
    }
  }
}

# CloudWatch Alarms for S3

# Alarm: Bucket size (Transcriptions)
resource "aws_cloudwatch_metric_alarm" "transcriptions_bucket_size" {
  alarm_name          = "${var.project_name}-transcriptions-large-bucket"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "BucketSizeBytes"
  namespace           = "AWS/S3"
  period              = "86400"  # 1 day
  statistic           = "Average"
  threshold           = 107374182400  # 100 GB
  alarm_description   = "Alert when transcriptions bucket exceeds 100GB"
  alarm_actions       = [var.sns_topic_arn]

  dimensions = {
    BucketName = aws_s3_bucket.transcriptions.id
    StorageType = "StandardStorageSize"
  }

  tags = {
    Environment = var.environment
  }
}

# Alarm: Number of objects (Uploads)
resource "aws_cloudwatch_metric_alarm" "uploads_object_count" {
  alarm_name          = "${var.project_name}-uploads-many-objects"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "NumberOfObjects"
  namespace           = "AWS/S3"
  period              = "86400"  # 1 day
  statistic           = "Average"
  threshold           = 1000000  # 1 million objects
  alarm_description   = "Alert when uploads bucket exceeds 1M objects"
  alarm_actions       = [var.sns_topic_arn]

  dimensions = {
    BucketName = aws_s3_bucket.uploads.id
    StorageType = "AllStorageTypes"
  }

  tags = {
    Environment = var.environment
  }
}
