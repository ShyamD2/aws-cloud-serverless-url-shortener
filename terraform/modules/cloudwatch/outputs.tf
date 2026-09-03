output "dashboard_name" {
  value = aws_cloudwatch_dashboard.operations.dashboard_name
}

output "api_alarm_arn" {
  value = aws_cloudwatch_metric_alarm.api_5xx_errors.arn
}

output "dlq_alarm_arn" {
  value = aws_cloudwatch_metric_alarm.sqs_dlq_messages.arn
}
