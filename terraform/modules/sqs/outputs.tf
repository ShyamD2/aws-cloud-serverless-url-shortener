output "queue_url" {
  description = "URL of the primary click events queue"
  value       = aws_sqs_queue.click_events.url
}

output "queue_arn" {
  description = "ARN of the primary click events queue"
  value       = aws_sqs_queue.click_events.arn
}

output "dlq_url" {
  description = "URL of the dead-letter queue"
  value       = aws_sqs_queue.click_events_dlq.url
}

output "dlq_arn" {
  description = "ARN of the dead-letter queue"
  value       = aws_sqs_queue.click_events_dlq.arn
}
