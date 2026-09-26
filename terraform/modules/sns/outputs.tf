output "click_events_topic_arn" {
  description = "ARN of the SNS click events topic"
  value       = aws_sns_topic.click_events.arn
}

output "click_events_topic_name" {
  description = "Name of the SNS click events topic"
  value       = aws_sns_topic.click_events.name
}

output "alarms_topic_arn" {
  description = "ARN of the SNS system alarms topic"
  value       = aws_sns_topic.alarms.arn
}

output "alarms_topic_name" {
  description = "Name of the SNS system alarms topic"
  value       = aws_sns_topic.alarms.name
}
