output "vpc_id" {
  value       = module.vpc.vpc_id
  description = "VPC ID"
}

output "alb_dns_name" {
  value       = module.alb.alb_dns_name
  description = "ALB DNS name"
}

output "alb_arn" {
  value       = module.alb.alb_arn
  description = "ALB ARN"
}

output "rds_endpoint" {
  value       = module.rds.rds_endpoint
  description = "RDS endpoint"
  sensitive   = true
}

output "redis_endpoint" {
  value       = module.redis.redis_endpoint
  description = "Redis endpoint"
  sensitive   = true
}

output "ecs_cluster_name" {
  value       = module.ecs.cluster_name
  description = "ECS cluster name"
}

output "ecr_backend_repository_url" {
  value       = module.ecr.backend_repository_url
  description = "ECR backend repository URL"
}

output "ecr_frontend_repository_url" {
  value       = module.ecr.frontend_repository_url
  description = "ECR frontend repository URL"
}

output "kms_key_id" {
  value       = module.kms.kms_key_id
  description = "KMS key ID"
  sensitive   = true
}

output "sns_topic_arn" {
  value       = aws_sns_topic.critical_alerts.arn
  description = "SNS topic ARN for critical alerts"
}
