# ALB Module - Application Load Balancer
# Distributes traffic to backend (FastAPI port 8000) and frontend (Next.js port 3000)
# HTTPS termination with ACM certificate
# Health checks every 30 seconds

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Application Load Balancer
resource "aws_lb" "main" {
  name_prefix        = "td"  # Limited to 6 chars
  internal           = false
  load_balancer_type = "application"
  security_groups    = [var.alb_security_group_id]
  subnets            = var.public_subnet_ids

  enable_deletion_protection = var.environment == "production" ? true : false
  enable_http2              = true
  enable_cross_zone_load_balancing = true

  tags = {
    Name        = "${var.project_name}-alb"
    Environment = var.environment
  }
}

# HTTP Listener - Redirect to HTTPS
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type = "redirect"

    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

# HTTPS Listener
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.main.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = var.certificate_arn

  default_action {
    type = "forward"
    forward {
      target_group {
        arn    = aws_lb_target_group.frontend.arn
        weight = 100
      }
    }
  }
}

# Target Group - Backend (FastAPI port 8000)
resource "aws_lb_target_group" "backend" {
  name_prefix = "bk"  # Limited to 6 chars
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"  # Fargate uses IP target type

  health_check {
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 30
    path                = "/health"
    matcher             = "200"
  }

  stickiness {
    type            = "lb_cookie"
    enabled         = true
    cookie_duration = 86400  # 1 day
  }

  tags = {
    Name = "${var.project_name}-backend-tg"
  }
}

# Target Group - Frontend (Next.js port 3000)
resource "aws_lb_target_group" "frontend" {
  name_prefix = "fr"  # Limited to 6 chars
  port        = 3000
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"  # Fargate uses IP target type

  health_check {
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 30
    path                = "/"
    matcher             = "200,404"  # Next.js may return 404 for some paths
  }

  tags = {
    Name = "${var.project_name}-frontend-tg"
  }
}

# Listener Rule - Route /api/* to Backend
resource "aws_lb_listener_rule" "backend_api" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 10

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend.arn
  }

  condition {
    path_pattern {
      values = ["/api/*"]
    }
  }
}

# Listener Rule - Route /health to Backend
resource "aws_lb_listener_rule" "backend_health" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 20

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend.arn
  }

  condition {
    path_pattern {
      values = ["/health"]
    }
  }
}

# CloudWatch Alarms for ALB

# Alarm: Unhealthy Host Count (Backend)
resource "aws_cloudwatch_metric_alarm" "backend_unhealthy_hosts" {
  alarm_name          = "${var.project_name}-backend-unhealthy-hosts"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = "UnHealthyHostCount"
  namespace           = "AWS/ApplicationELB"
  period              = "60"
  statistic           = "Average"
  threshold           = "1"
  alarm_description   = "Alert when backend has unhealthy hosts"
  alarm_actions       = [var.sns_topic_arn]

  dimensions = {
    LoadBalancer  = aws_lb.main.arn_suffix
    TargetGroup   = aws_lb_target_group.backend.arn_suffix
  }

  tags = {
    Environment = var.environment
  }
}

# Alarm: Unhealthy Host Count (Frontend)
resource "aws_cloudwatch_metric_alarm" "frontend_unhealthy_hosts" {
  alarm_name          = "${var.project_name}-frontend-unhealthy-hosts"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = "UnHealthyHostCount"
  namespace           = "AWS/ApplicationELB"
  period              = "60"
  statistic           = "Average"
  threshold           = "1"
  alarm_description   = "Alert when frontend has unhealthy hosts"
  alarm_actions       = [var.sns_topic_arn]

  dimensions = {
    LoadBalancer  = aws_lb.main.arn_suffix
    TargetGroup   = aws_lb_target_group.frontend.arn_suffix
  }

  tags = {
    Environment = var.environment
  }
}

# Alarm: Response Time (Backend)
resource "aws_cloudwatch_metric_alarm" "backend_response_time" {
  alarm_name          = "${var.project_name}-backend-slow-response"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "TargetResponseTime"
  namespace           = "AWS/ApplicationELB"
  period              = "300"
  statistic           = "Average"
  threshold           = "2"  # 2 seconds (SLA requirement)
  alarm_description   = "Alert when backend response time exceeds 2s"
  alarm_actions       = [var.sns_topic_arn]

  dimensions = {
    LoadBalancer  = aws_lb.main.arn_suffix
    TargetGroup   = aws_lb_target_group.backend.arn_suffix
  }

  tags = {
    Environment = var.environment
  }
}

# Alarm: Request Count (for scaling insights)
resource "aws_cloudwatch_metric_alarm" "alb_request_count" {
  alarm_name          = "${var.project_name}-alb-high-requests"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "RequestCount"
  namespace           = "AWS/ApplicationELB"
  period              = "300"
  statistic           = "Sum"
  threshold           = "10000"  # Alert on sustained high request count
  alarm_description   = "Alert when request count exceeds threshold"
  alarm_actions       = [var.sns_topic_arn]

  dimensions = {
    LoadBalancer = aws_lb.main.arn_suffix
  }

  tags = {
    Environment = var.environment
  }
}
