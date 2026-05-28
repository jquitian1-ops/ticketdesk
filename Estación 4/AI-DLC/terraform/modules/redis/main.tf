# Redis Module - ElastiCache for Caching and Session Management
# TicketDesk Enterprise requires:
# - Encryption at rest (KMS) and in transit (TLS)
# - Auth token for access control
# - Multi-AZ for high availability
# - Automatic failover
# - CloudWatch monitoring

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# ElastiCache Subnet Group - required for Multi-AZ
resource "aws_elasticache_subnet_group" "default" {
  name_prefix = "${var.project_name}-"
  description = "Subnet group for ${var.project_name} Redis"
  subnet_ids  = var.cache_subnet_ids

  tags = {
    Name        = "${var.project_name}-redis-subnet-group"
    Environment = var.environment
  }
}

# ElastiCache Parameter Group - optimized for TicketDesk
resource "aws_elasticache_parameter_group" "redis" {
  name_prefix = "${var.project_name}-"
  family      = "redis7"
  description = "Parameter group for ${var.project_name}"

  # Memory management
  parameter {
    name  = "maxmemory-policy"
    value = "allkeys-lru"  # Evict any key using LRU when maxmemory reached
  }

  # Enable auth
  parameter {
    name  = "requirepass"
    value = var.redis_auth_token
  }

  # Database eviction policy
  parameter {
    name  = "timeout"
    value = "300"  # Close connections idle >5min
  }

  # Replication lag
  parameter {
    name  = "repl-diskless-sync"
    value = "yes"  # Faster failover
  }

  tags = {
    Name        = "${var.project_name}-redis-param-group"
    Environment = var.environment
  }

  lifecycle {
    create_before_destroy = true
  }
}

# ElastiCache Redis Cluster - Multi-AZ with automatic failover
resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "${var.project_name}-redis"
  engine               = "redis"
  engine_version       = var.redis_version
  node_type            = var.redis_node_type
  num_cache_nodes      = 1  # Primary node; standby created automatically with Multi-AZ
  parameter_group_name = aws_elasticache_parameter_group.redis.name
  engine_version_actual = var.redis_version

  # Security and encryption
  auth_token = var.redis_auth_token
  auth_token_enabled = true
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  transit_encryption_mode = "preferred"
  security_group_ids = [var.redis_security_group_id]
  kms_key_id = var.kms_key_id

  # Availability
  automatic_failover_enabled = true
  multi_az_enabled           = true

  # Subnet and maintenance
  subnet_group_name = aws_elasticache_subnet_group.default.name
  maintenance_window = "sun:03:00-sun:04:00"  # UTC
  notification_topic_arn = var.sns_topic_arn

  # Logging
  log_delivery_configuration {
    destination      = aws_cloudwatch_log_group.redis_slow.name
    destination_type = "cloudwatch-logs"
    log_format       = "json"
    log_type         = "slow-log"
    enabled          = true
  }

  log_delivery_configuration {
    destination      = aws_cloudwatch_log_group.redis_engine.name
    destination_type = "cloudwatch-logs"
    log_format       = "json"
    log_type         = "engine-log"
    enabled          = true
  }

  # Backup (for recovery, not persistence)
  snapshot_retention_limit = 5  # Keep 5 latest snapshots
  snapshot_window          = "02:00-03:00"  # UTC

  tags = {
    Name        = "${var.project_name}-redis"
    Environment = var.environment
  }

  depends_on = [
    aws_elasticache_subnet_group.default,
    aws_elasticache_parameter_group.redis,
    aws_cloudwatch_log_group.redis_slow,
    aws_cloudwatch_log_group.redis_engine
  ]
}

# CloudWatch Log Groups for Redis
resource "aws_cloudwatch_log_group" "redis_slow" {
  name              = "/aws/elasticache/${var.project_name}-redis/slow-log"
  retention_in_days = var.log_retention_days

  tags = {
    Name        = "${var.project_name}-redis-slow-log"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_log_group" "redis_engine" {
  name              = "/aws/elasticache/${var.project_name}-redis/engine-log"
  retention_in_days = var.log_retention_days

  tags = {
    Name        = "${var.project_name}-redis-engine-log"
    Environment = var.environment
  }
}

# CloudWatch Alarms for Redis

# Alarm: CPU Utilization
resource "aws_cloudwatch_metric_alarm" "redis_cpu" {
  alarm_name          = "${var.project_name}-redis-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ElastiCache"
  period              = "300"
  statistic           = "Average"
  threshold           = "75"
  alarm_description   = "Alert when Redis CPU exceeds 75%"
  alarm_actions       = [var.sns_topic_arn]

  dimensions = {
    CacheClusterId = aws_elasticache_cluster.redis.id
  }

  tags = {
    Environment = var.environment
  }
}

# Alarm: Memory Utilization
resource "aws_cloudwatch_metric_alarm" "redis_memory" {
  alarm_name          = "${var.project_name}-redis-high-memory"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "DatabaseMemoryUsagePercentage"
  namespace           = "AWS/ElastiCache"
  period              = "300"
  statistic           = "Average"
  threshold           = "85"
  alarm_description   = "Alert when Redis memory exceeds 85%"
  alarm_actions       = [var.sns_topic_arn]

  dimensions = {
    CacheClusterId = aws_elasticache_cluster.redis.id
  }

  tags = {
    Environment = var.environment
  }
}

# Alarm: Evictions
resource "aws_cloudwatch_metric_alarm" "redis_evictions" {
  alarm_name          = "${var.project_name}-redis-evictions"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "Evictions"
  namespace           = "AWS/ElastiCache"
  period              = "300"
  statistic           = "Sum"
  threshold           = "100"  # Alert on sustained evictions
  alarm_description   = "Alert when Redis evictions exceed threshold (capacity issue)"
  alarm_actions       = [var.sns_topic_arn]

  dimensions = {
    CacheClusterId = aws_elasticache_cluster.redis.id
  }

  tags = {
    Environment = var.environment
  }
}

# Alarm: Replication Lag
resource "aws_cloudwatch_metric_alarm" "redis_replication_lag" {
  alarm_name          = "${var.project_name}-redis-replication-lag"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "ReplicationLag"
  namespace           = "AWS/ElastiCache"
  period              = "60"
  statistic           = "Average"
  threshold           = "10"  # 10 seconds
  alarm_description   = "Alert when Redis replication lag exceeds 10 seconds"
  alarm_actions       = [var.sns_topic_arn]

  dimensions = {
    CacheClusterId = aws_elasticache_cluster.redis.id
  }

  tags = {
    Environment = var.environment
  }
}

# Alarm: Connection Count
resource "aws_cloudwatch_metric_alarm" "redis_connections" {
  alarm_name          = "${var.project_name}-redis-connections"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "CurrConnections"
  namespace           = "AWS/ElastiCache"
  period              = "300"
  statistic           = "Average"
  threshold           = "1000"  # Alert on high connection count
  alarm_description   = "Alert when Redis connections exceed 1000"
  alarm_actions       = [var.sns_topic_arn]

  dimensions = {
    CacheClusterId = aws_elasticache_cluster.redis.id
  }

  tags = {
    Environment = var.environment
  }
}
