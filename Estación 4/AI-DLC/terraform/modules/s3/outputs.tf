# S3 Module - Outputs

output "transcriptions_bucket_id" {
  description = "Transcriptions bucket ID"
  value       = aws_s3_bucket.transcriptions.id
}

output "transcriptions_bucket_arn" {
  description = "Transcriptions bucket ARN"
  value       = aws_s3_bucket.transcriptions.arn
}

output "transcriptions_bucket_regional_domain_name" {
  description = "Transcriptions bucket regional domain name"
  value       = aws_s3_bucket.transcriptions.bucket_regional_domain_name
}

output "uploads_bucket_id" {
  description = "Uploads bucket ID"
  value       = aws_s3_bucket.uploads.id
}

output "uploads_bucket_arn" {
  description = "Uploads bucket ARN"
  value       = aws_s3_bucket.uploads.arn
}

output "uploads_bucket_regional_domain_name" {
  description = "Uploads bucket regional domain name"
  value       = aws_s3_bucket.uploads.bucket_regional_domain_name
}

output "reports_bucket_id" {
  description = "Reports bucket ID"
  value       = aws_s3_bucket.reports.id
}

output "reports_bucket_arn" {
  description = "Reports bucket ARN"
  value       = aws_s3_bucket.reports.arn
}

output "reports_bucket_regional_domain_name" {
  description = "Reports bucket regional domain name"
  value       = aws_s3_bucket.reports.bucket_regional_domain_name
}
