###########################
# API Gateway access log group
###########################

resource "aws_cloudwatch_log_group" "apigw" {
  name              = "/aws/apigateway/skillwall-${var.environment}-api"
  retention_in_days = var.log_retention_days
}

###########################
# IAM role allowing API Gateway to write to CloudWatch
###########################

data "aws_iam_policy_document" "apigw_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    effect  = "Allow"
    principals {
      type        = "Service"
      identifiers = ["apigateway.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "apigw_cloudwatch" {
  name               = "skillwall-${var.environment}-apigw-cw"
  assume_role_policy = data.aws_iam_policy_document.apigw_assume.json
}

resource "aws_iam_role_policy_attachment" "apigw_cloudwatch" {
  role       = aws_iam_role.apigw_cloudwatch.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonAPIGatewayPushToCloudWatchLogs"
}

# Account-level setting: API Gateway → CloudWatch logging role
resource "aws_api_gateway_account" "this" {
  cloudwatch_role_arn = aws_iam_role.apigw_cloudwatch.arn
}
