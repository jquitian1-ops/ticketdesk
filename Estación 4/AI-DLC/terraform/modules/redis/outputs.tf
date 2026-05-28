# Redis Module - Outputs

output "redis_endpoint" {
  description = "Redis cluster endpoint (host:port)"
  value       = aws_elasticache_cluster.redis.cache_nodes[0].address
  sensitive   = true
}

output "redis_port" {
  description = "Redis cluster port"
  value       = aws_elasticache_cluster.redis.port
}

output "redis_cluster_id" {
  description = "Redis cluster ID"
  value       = aws_elasticache_cluster.redis.id
}

output "redis_engine_version" {
  description = "Redis engine version"
  value       = aws_elasticache_cluster.redis.engine_version
}

output "redis_parameter_group_name" {
  description = "Redis parameter group name"
  value       = aws_elasticache_parameter_group.redis.name
}

output "redis_subnet_group_name" {
  description = "Redis subnet group name"
  value       = aws_elasticache_subnet_group.default.name
}

output "slow_log_group_name" {
  description = "CloudWatch log group name for Redis slow log"
  value       = aws_cloudwatch_log_group.redis_slow.name
}

output "engine_log_group_name" {
  description = "CloudWatch log group name for Redis engine log"
  value       = aws_cloudwatch_log_group.redis_engine.name
}

output "primary_endpoint_address" {
  description = "Primary endpoint address (hostname only)"
  value       = aws_elasticache_cluster.redis.cache_nodes[0].address
  sensitive   = true
}
