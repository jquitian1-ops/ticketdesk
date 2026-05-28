# CloudWatch Module - Centralized Monitoring
# Dashboards, log groups, metric filters, custom metrics

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# SNS Topic for Alarms
resource "aws_sns_topic" "alerts" {
  name_prefix = "${var.project_name}-alerts-"
  display_name = "${var.project_name} Infrastructure Alerts"

  tags = {
    Name        = "${var.project_name}-alerts-topic"
    Environment = var.environment
  }
}

# SNS Topic Subscription (email)
resource "aws_sns_topic_subscription" "alerts_email" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email

  # Email confirmation required manually
}

# CloudWatch Dashboard - Infrastructure Overview
resource "aws_cloudwatch_dashboard" "infrastructure" {
  dashboard_name = "${var.project_name}-infrastructure"

  dashboard_body = jsonencode({
    widgets = [
      # ECS Services Status
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/ECS", "DesiredTaskCount", { stat = "Average" }],
            [".", "RunningCount", { stat = "Average" }]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "ECS Task Status"
        }
      },
      # RDS CPU and Connections
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/RDS", "CPUUtilization", { stat = "Average" }],
            [".", "DatabaseConnections", { stat = "Average" }]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "RDS Performance"
        }
      },
      # Redis Performance
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/ElastiCache", "CPUUtilization", { stat = "Average" }],
            [".", "DatabaseMemoryUsagePercentage", { stat = "Average" }],
            [".", "Evictions", { stat = "Sum" }]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "Redis Performance"
        }
      },
      # ALB Health
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/ApplicationELB", "HealthyHostCount", { stat = "Average" }],
            [".", "UnHealthyHostCount", { stat = "Average" }],
            [".", "TargetResponseTime", { stat = "Average" }]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "Load Balancer Health"
        }
      },
      # Network Performance
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/ApplicationELB", "RequestCount", { stat = "Sum" }],
            [".", "HTTPCode_Target_2XX_Count", { stat = "Sum" }],
            [".", "HTTPCode_Target_5XX_Count", { stat = "Sum" }]
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
          title  = "Request Distribution"
        }
      }
    ]
  })
}

# CloudWatch Dashboard - Application Performance
resource "aws_cloudwatch_dashboard" "application" {
  dashboard_name = "${var.project_name}-application"

  dashboard_body = jsonencode({
    widgets = [
      # API Response Times
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/ApplicationELB", "TargetResponseTime"]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "API Response Time (p50)"
        }
      },
      # Error Rates
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/ApplicationELB", "HTTPCode_Target_5XX_Count"],
            ["AWS/ApplicationELB", "HTTPCode_Target_4XX_Count"]
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
          title  = "HTTP Error Rates"
        }
      },
      # Throughput
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/ApplicationELB", "RequestCount"]
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
          title  = "Requests per 5min"
        }
      }
    ]
  })
}

# CloudWatch Log Group - Application Logs (aggregated)
resource "aws_cloudwatch_log_group" "application" {
  name              = "/app/${var.project_name}"
  retention_in_days = var.log_retention_days

  tags = {
    Name        = "${var.project_name}-app-logs"
    Environment = var.environment
  }
}

# Metric Filter - Error Rate from Application Logs
resource "aws_cloudwatch_log_metric_filter" "error_count" {
  name           = "${var.project_name}-error-count"
  log_group_name = aws_cloudwatch_log_group.application.name
  filter_pattern = "[time, request_id, level = ERROR*, ...]"

  metric_transformation {
    name      = "ApplicationErrors"
    namespace = "${var.project_name}/Application"
    value     = "1"
  }
}

# Alarm - High Error Rate
resource "aws_cloudwatch_metric_alarm" "error_rate_high" {
  alarm_name          = "${var.project_name}-error-rate-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "ApplicationErrors"
  namespace           = "${var.project_name}/Application"
  period              = "300"
  statistic           = "Sum"
  threshold           = "100"
  alarm_description   = "Alert when error count exceeds 100 in 5 minutes"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  tags = {
    Environment = var.environment
  }
}

# Metric Filter - Latency Analysis from Application Logs
resource "aws_cloudwatch_log_metric_filter" "latency" {
  name           = "${var.project_name}-latency-p99"
  log_group_name = aws_cloudwatch_log_group.application.name
  filter_pattern = "[time, request_id, level, msg, latency_ms]"

  metric_transformation {
    name      = "APILatencyP99"
    namespace = "${var.project_name}/Performance"
    value     = "$latency_ms"
  }
}

# Alarm - High Latency
resource "aws_cloudwatch_metric_alarm" "latency_high" {
  alarm_name          = "${var.project_name}-latency-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "3"
  metric_name         = "APILatencyP99"
  namespace           = "${var.project_name}/Performance"
  period              = "300"
  statistic           = "Maximum"
  threshold           = "2000"  # 2 seconds SLA
  alarm_description   = "Alert when p99 latency exceeds 2 seconds"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  tags = {
    Environment = var.environment
  }
}

# Alarm - Insufficient Data (detect missing metrics / dead services)
resource "aws_cloudwatch_metric_alarm" "data_availability" {
  alarm_name          = "${var.project_name}-insufficient-data"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "RequestCount"
  namespace           = "AWS/ApplicationELB"
  period              = "300"
  statistic           = "Sum"
  threshold           = "1"
  treat_missing_data  = "breaching"
  alarm_description   = "Alert when no requests detected (service may be down)"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  tags = {
    Environment = var.environment
  }
}
