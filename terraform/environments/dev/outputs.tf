output "api_endpoint" {
  description = "HTTP API Gateway invoke URL"
  value       = module.api_gateway.api_endpoint
}

output "cloudfront_domain_name" {
  description = "CloudFront distribution domain name (Frontend URL)"
  value       = module.cloudfront.distribution_domain_name
}

output "dynamodb_table_name" {
  description = "Name of the DynamoDB URLs table"
  value       = module.dynamodb.table_name
}

output "sqs_queue_url" {
  description = "URL of the SQS click events queue"
  value       = module.sqs.queue_url
}

output "sqs_dlq_url" {
  description = "URL of the SQS dead-letter queue"
  value       = module.sqs.dlq_url
}

output "analytics_bucket" {
  description = "Name of the S3 analytics bucket"
  value       = module.s3.analytics_bucket_id
}

output "frontend_bucket" {
  description = "Name of the S3 frontend bucket"
  value       = module.s3.frontend_bucket_id
}

output "cloudwatch_dashboard" {
  description = "Name of the CloudWatch dashboard"
  value       = module.cloudwatch.dashboard_name
}
