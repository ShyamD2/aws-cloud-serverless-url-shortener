output "distribution_id" {
  description = "ID of the CloudFront distribution"
  value       = aws_cloudfront_distribution.frontend.id
}

output "distribution_domain_name" {
  description = "Domain name of the CloudFront distribution"
  value       = aws_cloudfront_distribution.frontend.domain_name
}

output "distribution_arn" {
  description = "ARN of the CloudFront distribution"
  value       = aws_cloudfront_distribution.frontend.arn
}
