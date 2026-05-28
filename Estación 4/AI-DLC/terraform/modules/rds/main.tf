# RDS Module - PostgreSQL Multi-AZ Database
# TicketDesk Enterprise requires:
# - Multi-AZ for 99.5% availability (RTO <2min, RPO=0 with sync replication)
# - Encryption at rest (AWS KMS)
# - Automated backups (30 days retention)
# - Performance Insights enabled
# - Enhanced monitoring via CloudWatch

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# DB Subnet Group - required for Multi-AZ RDS
resource "aws_db_subnet_group" "default" {
  name_prefix            = "${var.project_name}-"
  description            = "DB subnet group for ${var.project_name} RDS"
  subnet_ids             = var.database_subnet_ids
  skip_final_snapshot    = false

  tags = {
    Name        = "${var.project_name}-db-subnet-group"
    Environment = var.environment
  }
}

# RDS PostgreSQL Instance - Multi-AZ for high availability
resource "aws_db_instance" "postgres" {
  identifier            = "${var.project_name}-postgres"
  engine                = "postgres"
  engine_version        = var.postgres_version
  instance_class        = var.db_instance_class
  allocated_storage     = var.allocated_storage
  storage_type          = "gp3"
  storage_encrypted     = true
  kms_key_id            = var.kms_key_id

  # Multi-AZ configuration - CRITICAL for 99.5% SLA
  multi_az              = true
  publicly_accessible   = false

  # Database configuration
  db_name               = var.database_name
  username              = var.database_username
  password              = var.database_password
  parameter_group_name  = aws_db_parameter_group.postgres.name
  db_subnet_group_name  = aws_db_subnet_group.default.name
  vpc_security_group_ids = [var.rds_security_group_id]

  # Backup and recovery configuration
  backup_retention_period = 30  # 30 days for compliance
  backup_window          = "03:00-04:00"  # UTC
  maintenance_window     = "sun:04:00-sun:05:00"  # UTC
  copy_tags_to_snapshot  = true
  final_snapshot_identifier = "${var.project_name}-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}"

  # Performance and monitoring
  performance_insights_enabled = true
  performance_insights_retention_period = 7
  performance_insights_kms_key_id = var.kms_key_id

  # Enhanced monitoring (1 minute granularity)
  monitoring_interval    = 60
  monitoring_role_arn    = aws_iam_role.rds_monitoring.arn
  enable_cloudwatch_logs_exports = ["postgresql"]

  # Connection pooling optimization
  max_allocated_storage  = 1000  # Auto-scaling up to 1TB

  skip_final_snapshot    = false
  deletion_protection    = var.environment == "production" ? true : false

  tags = {
    Name        = "${var.project_name}-postgres"
    Environment = var.environment
  }

  depends_on = [
    aws_db_subnet_group.default,
    aws_db_parameter_group.postgres,
    aws_iam_role.rds_monitoring
  ]
}

# DB Parameter Group - optimized for TicketDesk workload
resource "aws_db_parameter_group" "postgres" {
  name_prefix = "${var.project_name}-"
  family      = "postgres${floor(tonumber(var.postgres_version))}"
  description = "Custom parameter group for ${var.project_name}"

  # Connection pooling parameters
  parameter {
    name  = "max_connections"
    value = "500"
  }

  # Query performance parameters
  parameter {
    name  = "shared_preload_libraries"
    value = "pg_stat_statements,pgaudit"
  }

  parameter {
    name  = "log_statement"
    value = "all"
  }

  parameter {
    name  = "log_duration"
    value = "1"
  }

  # Lock management
  parameter {
    name  = "deadlock_timeout"
    value = "1000"  # 1 second
  }

  # Search path for migrations
  parameter {
    name  = "search_path"
    value = "\"$user\",public"
  }

  skip_invalid_parameter_group_config = false

  tags = {
    Name        = "${var.project_name}-db-param-group"
    Environment = var.environment
  }

  lifecycle {
    create_before_destroy = true
  }
}

# CloudWatch Log Group for RDS PostgreSQL logs
resource "aws_cloudwatch_log_group" "postgres" {
  name              = "/aws/rds/${var.project_name}-postgres"
  retention_in_days = var.log_retention_days

  tags = {
    Name        = "${var.project_name}-rds-logs"
    Environment = var.environment
  }
}

# IAM Role for RDS Enhanced Monitoring
resource "aws_iam_role" "rds_monitoring" {
  name_prefix = "${var.project_name}-rds-monitoring-"
  description = "Role for RDS enhanced monitoring"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "monitoring.rds.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-rds-monitoring-role"
    Environment = var.environment
  }
}

# IAM Role Policy - attach AWS managed policy for RDS monitoring
resource "aws_iam_role_policy_attachment" "rds_monitoring" {
  role       = aws_iam_role.rds_monitoring.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

# CloudWatch Alarms for RDS

# Alarm: CPU Utilization
resource "aws_cloudwatch_metric_alarm" "rds_cpu" {
  alarm_name          = "${var.project_name}-rds-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "Alert when RDS CPU exceeds 80%"
  alarm_actions       = [var.sns_topic_arn]

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.postgres.id
  }

  tags = {
    Environment = var.environment
  }
}

# Alarm: Database Connections
resource "aws_cloudwatch_metric_alarm" "rds_connections" {
  alarm_name          = "${var.project_name}-rds-high-connections"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "DatabaseConnections"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "400"  # Max 500 connections, alert at 400
  alarm_description   = "Alert when database connections exceed 400"
  alarm_actions       = [var.sns_topic_arn]

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.postgres.id
  }

  tags = {
    Environment = var.environment
  }
}

# Alarm: Free Storage Space
resource "aws_cloudwatch_metric_alarm" "rds_storage" {
  alarm_name          = "${var.project_name}-rds-low-storage"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "FreeStorageSpace"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "10737418240"  # 10GB in bytes
  alarm_description   = "Alert when free storage drops below 10GB"
  alarm_actions       = [var.sns_topic_arn]

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.postgres.id
  }

  tags = {
    Environment = var.environment
  }
}

# Replication Lag Alarm (for standby monitoring)
resource "aws_cloudwatch_metric_alarm" "rds_replication_lag" {
  alarm_name          = "${var.project_name}-rds-replication-lag"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "ReplicationLag"
  namespace           = "AWS/RDS"
  period              = "60"
  statistic           = "Average"
  threshold           = "1"  # 1 second - RPO requirement
  alarm_description   = "Alert when replication lag exceeds 1 second (RPO violation)"
  alarm_actions       = [var.sns_topic_arn]

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.postgres.id
  }

  tags = {
    Environment = var.environment
  }
}
