output "create_url_role_arn" {
  description = "ARN of the Create URL Lambda execution role"
  value       = aws_iam_role.create_url.arn
}

output "redirect_role_arn" {
  description = "ARN of the Redirect Lambda execution role"
  value       = aws_iam_role.redirect.arn
}

output "delete_url_role_arn" {
  description = "ARN of the Delete URL Lambda execution role"
  value       = aws_iam_role.delete_url.arn
}

output "analytics_role_arn" {
  description = "ARN of the Analytics Lambda execution role"
  value       = aws_iam_role.analytics.arn
}
