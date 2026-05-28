# CloudWatch Module - Outputs

output "sns_topic_arn" {
  description = "SNS topic ARN for alerts"
  value       = aws_sns_topic.alerts.arn
}

output "sns_topic_name" {
  description = "SNS topic name for alerts"
  value       = aws_sns_topic.alerts.name
}

output "infrastructure_dashboard_url" {
  description = "URL to infrastructure CloudWatch dashboard"
  value       = "https://console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${aws_cloudwatch_dashboard.infrastructure.dashboard_name}"
}

output "application_dashboard_url" {
  description = "URL to application CloudWatch dashboard"
  value       = "https://console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${aws_cloudwatch_dashboard.application.dashboard_name}"
}

output "log_group_name" {
  description = "Application log group name"
  value       = aws_cloudwatch_log_group.application.name
}

output "error_metric_filter_name" {
  description = "Error count metric filter name"
  value       = aws_cloudwatch_log_metric_filter.error_count.name
}

output "latency_metric_filter_name" {
  description = "Latency metric filter name"
  value       = aws_cloudwatch_log_metric_filter.latency.name
}
