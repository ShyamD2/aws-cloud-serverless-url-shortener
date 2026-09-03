# ==============================================================================
# Amazon API Gateway (HTTP API v2) Module
# ==============================================================================

resource "aws_apigatewayv2_api" "http_api" {
  name          = "${var.environment}-url-shortener-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["GET", "POST", "DELETE", "OPTIONS"]
    allow_headers = ["content-type", "authorization", "x-forwarded-proto", "x-forwarded-host"]
    max_age       = 300
  }

  tags = merge(var.tags, {
    Name = "${var.environment}-url-shortener-api"
  })
}

# CloudWatch Log Group for HTTP API Access Logs
resource "aws_cloudwatch_log_group" "api_access_logs" {
  name              = "/aws/apigateway/${var.environment}-url-shortener-api"
  retention_in_days = 7

  tags = var.tags
}

# Default Stage with rate limiting and logging
resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.http_api.id
  name        = "$default"
  auto_deploy = true

  default_route_settings {
    detailed_metrics_enabled = true
    throttling_burst_limit   = 50
    throttling_rate_limit    = 100
  }

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_access_logs.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      routeKey       = "$context.routeKey"
      status         = "$context.status"
      protocol       = "$context.protocol"
      responseLength = "$context.responseLength"
      latency        = "$context.responseLatency"
    })
  }

  tags = var.tags
}

# --- Lambda Integrations ---

# 1. Create URL Integration & Routes
resource "aws_apigatewayv2_integration" "create_url" {
  api_id                 = aws_apigatewayv2_api.http_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = var.create_url_function_arn
  integration_method     = "POST"
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "post_urls" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "POST /urls"
  target    = "integrations/${aws_apigatewayv2_integration.create_url.id}"
}

resource "aws_apigatewayv2_route" "post_api_urls" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "POST /api/urls"
  target    = "integrations/${aws_apigatewayv2_integration.create_url.id}"
}

resource "aws_lambda_permission" "apigw_create_url" {
  statement_id  = "AllowAPIGatewayInvokeCreateUrl"
  action        = "lambda:InvokeFunction"
  function_name = var.create_url_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http_api.arn}/*/*"
}

# 2. Redirect Integration & Route
resource "aws_apigatewayv2_integration" "redirect" {
  api_id                 = aws_apigatewayv2_api.http_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = var.redirect_function_arn
  integration_method     = "POST"
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "get_redirect" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "GET /{short_code}"
  target    = "integrations/${aws_apigatewayv2_integration.redirect.id}"
}

resource "aws_lambda_permission" "apigw_redirect" {
  statement_id  = "AllowAPIGatewayInvokeRedirect"
  action        = "lambda:InvokeFunction"
  function_name = var.redirect_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http_api.arn}/*/*"
}

# 3. Delete URL Integration & Routes
resource "aws_apigatewayv2_integration" "delete_url" {
  api_id                 = aws_apigatewayv2_api.http_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = var.delete_url_function_arn
  integration_method     = "POST"
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "delete_urls" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "DELETE /urls/{short_code}"
  target    = "integrations/${aws_apigatewayv2_integration.delete_url.id}"
}

resource "aws_apigatewayv2_route" "delete_api_urls" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "DELETE /api/urls/{short_code}"
  target    = "integrations/${aws_apigatewayv2_integration.delete_url.id}"
}

resource "aws_lambda_permission" "apigw_delete_url" {
  statement_id  = "AllowAPIGatewayInvokeDeleteUrl"
  action        = "lambda:InvokeFunction"
  function_name = var.delete_url_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http_api.arn}/*/*"
}
