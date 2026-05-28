output "api_gateway_url" {
  description = "Invoke URL of the API Gateway HTTP API"
  value       = aws_apigatewayv2_stage.default.invoke_url
}

output "api_gateway_id" {
  description = "API Gateway HTTP API ID"
  value       = aws_apigatewayv2_api.api.id
}

output "lambda_function_name" {
  description = "Lambda function name (used by backend deploy script)"
  value       = aws_lambda_function.api.function_name
}

output "lambda_function_arn" {
  description = "Lambda function ARN"
  value       = aws_lambda_function.api.arn
}

output "dynamodb_table_name" {
  description = "DynamoDB table name"
  value       = aws_dynamodb_table.participants.name
}

output "dynamodb_table_arn" {
  description = "DynamodB table ARN"
  value       = aws_dynamodb_table.participants.arn
}

output "s3_bucket_name" {
  description = "S3 bucket name for participant photos"
  value       = aws_s3_bucket.photos.id
}

output "s3_bucket_arn" {
  description = "S3 bucket ARN"
  value       = aws_s3_bucket.photos.arn
}
