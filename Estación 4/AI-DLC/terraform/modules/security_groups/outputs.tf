# Security Groups Module - Outputs

output "alb_security_group_id" {
  description = "ALB Security Group ID"
  value       = aws_security_group.alb.id
}

output "ecs_security_group_id" {
  description = "ECS Security Group ID"
  value       = aws_security_group.ecs.id
}

output "rds_security_group_id" {
  description = "RDS Security Group ID"
  value       = aws_security_group.rds.id
}

output "redis_security_group_id" {
  description = "Redis Security Group ID"
  value       = aws_security_group.redis.id
}

output "alb_security_group_name" {
  description = "ALB Security Group Name"
  value       = aws_security_group.alb.name
}

output "ecs_security_group_name" {
  description = "ECS Security Group Name"
  value       = aws_security_group.ecs.name
}

output "rds_security_group_name" {
  description = "RDS Security Group Name"
  value       = aws_security_group.rds.name
}

output "redis_security_group_name" {
  description = "Redis Security Group Name"
  value       = aws_security_group.redis.name
}
