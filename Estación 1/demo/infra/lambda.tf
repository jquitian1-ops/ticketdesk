###########################
# IAM: Lambda execution role
###########################

data "aws_iam_policy_document" "lambda_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    effect  = "Allow"
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda_exec" {
  name               = "skillwall-${var.environment}-lambda-exec"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}

# Troubleshooting #3: include DescribeTable, TransactWriteItems, BatchWriteItem,
# Query, Scan from start to avoid missing-IAM-perm runtime errors.
data "aws_iam_policy_document" "lambda_inline" {
  statement {
    sid    = "DynamoDB"
    effect = "Allow"
    actions = [
      "dynamodb:DescribeTable",
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:DeleteItem",
      "dynamodb:Query",
      "dynamodb:Scan",
      "dynamodb:BatchWriteItem",
      "dynamodb:BatchGetItem",
      "dynamodb:TransactWriteItems",
      "dynamodb:TransactGetItems"
    ]
    resources = [
      aws_dynamodb_table.participants.arn,
      "${aws_dynamodb_table.participants.arn}/index/*"
    ]
  }

  statement {
    sid    = "S3Objects"
    effect = "Allow"
    actions = [
      "s3:PutObject",
      "s3:GetObject",
      "s3:DeleteObject"
    ]
    resources = ["${aws_s3_bucket.photos.arn}/*"]
  }

  statement {
    sid    = "S3Bucket"
    effect = "Allow"
    actions = [
      "s3:ListBucket",
      "s3:GetBucketLocation"
    ]
    resources = [aws_s3_bucket.photos.arn]
  }

  statement {
    sid    = "Logs"
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]
    resources = ["arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/skillwall-${var.environment}-api:*"]
  }
}

resource "aws_iam_role_policy" "lambda_inline" {
  name   = "skillwall-${var.environment}-lambda-policy"
  role   = aws_iam_role.lambda_exec.id
  policy = data.aws_iam_policy_document.lambda_inline.json
}

###########################
# Lambda function
###########################

resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/skillwall-${var.environment}-api"
  retention_in_days = var.log_retention_days
}

resource "aws_lambda_function" "api" {
  function_name = "skillwall-${var.environment}-api"
  role          = aws_iam_role.lambda_exec.arn
  runtime       = "nodejs22.x"
  handler       = "index.handler"
  memory_size   = var.lambda_memory
  timeout       = var.lambda_timeout

  # Placeholder bundle; real code uploaded by backend/scripts/deploy.sh
  filename         = "${path.module}/dummy.zip"
  source_code_hash = filebase64sha256("${path.module}/dummy.zip")

  environment {
    variables = {
      DYNAMODB_TABLE_NAME   = aws_dynamodb_table.participants.name
      S3_BUCKET_NAME        = aws_s3_bucket.photos.id
      ADMIN_TOKEN           = var.admin_token
      NEW_RELIC_LICENSE_KEY = var.new_relic_license_key
      # Troubleshooting #21: serialize list to comma-separated for runtime parsing.
      CORS_ORIGINS = join(",", var.cors_origins)
      SESSION_CODE = var.session_code
      NODE_OPTIONS = "--enable-source-maps"
    }
  }

  depends_on = [
    aws_iam_role_policy.lambda_inline,
    aws_cloudwatch_log_group.lambda
  ]
}

resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.api.execution_arn}/*/*"
}
