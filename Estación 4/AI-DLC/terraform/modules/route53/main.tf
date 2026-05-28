# Route53 Module - DNS Management
# Maps domain names to ALB, includes health checks, failover records

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Retrieve hosted zone (assumes it exists)
data "aws_route53_zone" "main" {
  name = var.domain_name
}

# DNS Record - Main Application (A record pointing to ALB)
resource "aws_route53_record" "app" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = var.domain_name
  type    = "A"

  alias {
    name                   = var.alb_dns_name
    zone_id                = var.alb_zone_id
    evaluate_target_health = true
  }
}

# DNS Record - WWW subdomain (CNAME)
resource "aws_route53_record" "www" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = "www.${var.domain_name}"
  type    = "CNAME"
  ttl     = 300
  records = [aws_route53_record.app.fqdn]
}

# DNS Record - API subdomain
resource "aws_route53_record" "api" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = "api.${var.domain_name}"
  type    = "A"

  alias {
    name                   = var.alb_dns_name
    zone_id                = var.alb_zone_id
    evaluate_target_health = true
  }
}

# Health Check - Primary Application
resource "aws_route53_health_check" "app" {
  fqdn              = aws_route53_record.app.fqdn
  port              = 443
  type              = "HTTPS"
  resource_path     = "/health"
  failure_threshold = 3
  request_interval  = 30

  tags = {
    Name = "${var.project_name}-app-health-check"
  }
}

# Health Check - API Endpoint
resource "aws_route53_health_check" "api" {
  fqdn              = aws_route53_record.api.fqdn
  port              = 443
  type              = "HTTPS"
  resource_path     = "/api/health"
  failure_threshold = 3
  request_interval  = 30

  tags = {
    Name = "${var.project_name}-api-health-check"
  }
}

# CloudWatch Alarm - Health Check Failure (App)
resource "aws_cloudwatch_metric_alarm" "health_check_app" {
  alarm_name          = "${var.project_name}-app-health-check-failed"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = "HealthCheckStatus"
  namespace           = "AWS/Route53"
  period              = "60"
  statistic           = "Minimum"
  threshold           = "1"  # 0 = healthy, 1 = unhealthy
  alarm_description   = "Alert when application health check fails"
  alarm_actions       = [var.sns_topic_arn]

  dimensions = {
    HealthCheckId = aws_route53_health_check.app.id
  }

  tags = {
    Environment = var.environment
  }
}

# CloudWatch Alarm - Health Check Failure (API)
resource "aws_cloudwatch_metric_alarm" "health_check_api" {
  alarm_name          = "${var.project_name}-api-health-check-failed"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = "HealthCheckStatus"
  namespace           = "AWS/Route53"
  period              = "60"
  statistic           = "Minimum"
  threshold           = "1"
  alarm_description   = "Alert when API health check fails"
  alarm_actions       = [var.sns_topic_arn]

  dimensions = {
    HealthCheckId = aws_route53_health_check.api.id
  }

  tags = {
    Environment = var.environment
  }
}

# TXT Record - Domain Verification (for future email, etc.)
resource "aws_route53_record" "verification" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = "_verification.${var.domain_name}"
  type    = "TXT"
  ttl     = 300
  records = ["v=${var.project_name}-${var.environment}"]
}
