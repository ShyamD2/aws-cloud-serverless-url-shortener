output "create_url_function_name" {
  value = aws_lambda_function.create_url.function_name
}

output "create_url_function_arn" {
  value = aws_lambda_function.create_url.arn
}

output "redirect_function_name" {
  value = aws_lambda_function.redirect.function_name
}

output "redirect_function_arn" {
  value = aws_lambda_function.redirect.arn
}

output "delete_url_function_name" {
  value = aws_lambda_function.delete_url.function_name
}

output "delete_url_function_arn" {
  value = aws_lambda_function.delete_url.arn
}

output "analytics_function_name" {
  value = aws_lambda_function.analytics.function_name
}

output "analytics_function_arn" {
  value = aws_lambda_function.analytics.arn
}
