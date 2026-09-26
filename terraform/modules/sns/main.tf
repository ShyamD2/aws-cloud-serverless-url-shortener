# ==============================================================================
# Amazon SNS Module: Asynchronous Messaging Fabric & Alerting
# ==============================================================================

# 1. Click Events SNS Topic (Decoupled Fanout Fabric)
resource "aws_sns_topic" "click_events" {
  name              = "${var.environment}-click-events-topic"
  kms_master_key_id = "alias/aws/sns" # Default AWS-managed KMS key for encryption

  tags = merge(var.tags, {
    Name        = "${var.environment}-click-events-topic"
    Description = "Asynchronous messaging fabric for click telemetry event fanout"
  })
}

# 2. SNS to SQS Subscription (Fanout Integration)
resource "aws_sns_topic_subscription" "sqs_subscription" {
  topic_arn            = aws_sns_topic.click_events.arn
  protocol             = "sqs"
  endpoint             = var.sqs_queue_arn
  raw_message_delivery = true # Delivers raw JSON without SNS envelope for optimal consumer ingestion
}

# 3. SQS Queue Policy granting SNS permissions to deliver messages
resource "aws_sqs_queue_policy" "sns_to_sqs" {
  queue_url = var.sqs_queue_url

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowSNSPublishToSQS"
        Effect    = "Allow"
        Principal = {
          Service = "sns.amazonaws.com"
        }
        Action    = "sqs:SendMessage"
        Resource  = var.sqs_queue_arn
        Condition = {
          ArnEquals = {
            "aws:SourceArn" = aws_sns_topic.click_events.arn
          }
        }
      }
    ]
  })
}

# 4. System Alarms & Observability SNS Topic
resource "aws_sns_topic" "alarms" {
  name              = "${var.environment}-system-alarms-topic"
  kms_master_key_id = "alias/aws/sns"

  tags = merge(var.tags, {
    Name        = "${var.environment}-system-alarms-topic"
    Description = "Target SNS topic for CloudWatch metric alarms and DLQ alerts"
  })
}
