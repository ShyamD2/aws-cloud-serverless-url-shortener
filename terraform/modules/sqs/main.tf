# ==============================================================================
# SQS Queue Module (Click Events Queue + Dead-Letter Queue)
# ==============================================================================

resource "aws_sqs_queue" "click_events_dlq" {
  name                      = "${var.queue_name}-dlq"
  message_retention_seconds = 1209600 # 14 days retention for poison messages
  sqs_managed_sse_enabled   = true

  tags = merge(var.tags, {
    Name        = "${var.queue_name}-dlq"
    Description = "Dead-letter queue for failed analytics processing"
  })
}

resource "aws_sqs_queue" "click_events" {
  name                       = var.queue_name
  visibility_timeout_seconds = var.visibility_timeout_seconds # e.g. 30s
  message_retention_seconds  = 345600                         # 4 days
  sqs_managed_sse_enabled    = true

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.click_events_dlq.arn
    maxReceiveCount     = 3
  })

  tags = merge(var.tags, {
    Name        = var.queue_name
    Description = "Decoupled buffer for click telemetry events"
  })
}
