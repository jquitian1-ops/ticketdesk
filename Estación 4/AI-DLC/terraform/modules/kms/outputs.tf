# KMS Module - Outputs

output "key_id" {
  description = "KMS key ID"
  value       = aws_kms_key.main.id
}

output "key_arn" {
  description = "KMS key ARN"
  value       = aws_kms_key.main.arn
}

output "alias_name" {
  description = "KMS key alias name"
  value       = aws_kms_alias.main.name
}

output "alias_arn" {
  description = "KMS key alias ARN"
  value       = aws_kms_alias.main.arn
}

output "key_rotation_enabled" {
  description = "Whether key rotation is enabled"
  value       = aws_kms_key.main.enable_key_rotation
}
