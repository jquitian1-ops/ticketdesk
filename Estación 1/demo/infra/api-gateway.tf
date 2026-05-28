###########################
# HTTP API
###########################

# Troubleshooting #20: API Gateway HTTP API v2 overrides Lambda CORS headers.
# CORS truth lives ONLY here. Do NOT replicate CORS headers in Lambda responses.
# Troubleshooting #21: allow_origins accepts multiple values via list(string).
resource "aws_apigatewayv2_api" "api" {
  name          = "skillwall-${var.environment}-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = var.cors_origins
    allow_methods = ["GET", "POST", "DELETE", "OPTIONS"]
    allow_headers = ["Content-Type", "Authorization", "traceparent", "tracestate"]
    max_age       = 3600
  }
}

###########################
# Lambda integration
###########################

resource "aws_apigatewayv2_integration" "lambda" {
  api_id                 = aws_apigatewayv2_api.api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.api.invoke_arn
  integration_method     = "POST"
  payload_format_version = "2.0"
  timeout_milliseconds   = 29000
}

###########################
# Routes (8 total)
###########################

locals {
  routes = {
    health       = "GET /health"
    upload_url   = "POST /upload-url"
    join         = "POST /join"
    wall         = "GET /wall"
    like         = "POST /like"
    leaderboard  = "GET /leaderboard"
    admin_create = "POST /admin/sessions"
    admin_delete = "DELETE /admin/sessions/{code}"
  }
}

resource "aws_apigatewayv2_route" "routes" {
  for_each = local.routes

  api_id    = aws_apigatewayv2_api.api.id
  route_key = each.value
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

###########################
# Stage with access logs + throttling
###########################

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.api.id
  name        = "$default"
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.apigw.arn
    format = jsonencode({
      requestId   = "$context.requestId"
      ip          = "$context.identity.sourceIp"
      method      = "$context.httpMethod"
      path        = "$context.path"
      status      = "$context.status"
      latency     = "$context.responseLatency"
      protocol    = "$context.protocol"
      requestTime = "$context.requestTime"
    })
  }

  default_route_settings {
    throttling_burst_limit = 50
    throttling_rate_limit  = 50
  }

  # Per-route throttling on write-heavy endpoints (5 TPS each)
  route_settings {
    route_key              = "POST /join"
    throttling_burst_limit = 5
    throttling_rate_limit  = 5
  }

  route_settings {
    route_key              = "POST /like"
    throttling_burst_limit = 5
    throttling_rate_limit  = 5
  }

  depends_on = [aws_api_gateway_account.this]
}
