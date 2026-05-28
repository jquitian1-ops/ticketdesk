# RDS Module - Outputs

output "rds_endpoint" {
  description = "RDS instance endpoint (host:port)"
  value       = aws_db_instance.postgres.endpoint
  sensitive   = true
}

output "rds_address" {
  description = "RDS instance address (hostname only)"
  value       = aws_db_instance.postgres.address
  sensitive   = true
}

output "rds_port" {
  description = "RDS instance port"
  value       = aws_db_instance.postgres.port
}

output "rds_resource_id" {
  description = "RDS instance resource ID"
  value       = aws_db_instance.postgres.resource_id
}

output "rds_instance_id" {
  description = "RDS instance identifier"
  value       = aws_db_instance.postgres.id
}

output "db_name" {
  description = "Name of the initial database"
  value       = aws_db_instance.postgres.db_name
}

output "db_subnet_group_id" {
  description = "DB subnet group ID"
  value       = aws_db_subnet_group.default.id
}

output "parameter_group_id" {
  description = "DB parameter group ID"
  value       = aws_db_parameter_group.postgres.id
}

output "log_group_name" {
  description = "CloudWatch log group name for PostgreSQL logs"
  value       = aws_cloudwatch_log_group.postgres.name
}

output "monitoring_role_arn" {
  description = "IAM role ARN for RDS enhanced monitoring"
  value       = aws_iam_role.rds_monitoring.arn
}
