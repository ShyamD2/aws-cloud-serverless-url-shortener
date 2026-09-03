output "analytics_bucket_id" {
  description = "Name/ID of the analytics S3 bucket"
  value       = aws_s3_bucket.analytics.id
}

output "analytics_bucket_arn" {
  description = "ARN of the analytics S3 bucket"
  value       = aws_s3_bucket.analytics.arn
}

output "frontend_bucket_id" {
  description = "Name/ID of the frontend S3 bucket"
  value       = aws_s3_bucket.frontend.id
}

output "frontend_bucket_arn" {
  description = "ARN of the frontend S3 bucket"
  value       = aws_s3_bucket.frontend.arn
}

output "frontend_bucket_regional_domain_name" {
  description = "Regional domain name of frontend S3 bucket (for CloudFront origin)"
  value       = aws_s3_bucket.frontend.bucket_regional_domain_name
}
