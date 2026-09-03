output "api_id" {
  description = "ID of the HTTP API Gateway"
  value       = aws_apigatewayv2_api.http_api.id
}

output "api_endpoint" {
  description = "Default invoke URL endpoint of the HTTP API Gateway"
  value       = aws_apigatewayv2_api.http_api.api_endpoint
}

output "api_arn" {
  description = "ARN of the HTTP API Gateway"
  value       = aws_apigatewayv2_api.http_api.arn
}
