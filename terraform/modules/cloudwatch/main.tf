# ==============================================================================
# Amazon CloudWatch Observability Module (Alarms & Dashboard)
# ==============================================================================

# 1. API Gateway 5XX Errors Alarm
resource "aws_cloudwatch_metric_alarm" "api_5xx_errors" {
  alarm_name          = "${var.environment}-api-5xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "5xx"
  namespace           = "AWS/ApiGateway"
  period              = 60
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "Triggered when API Gateway returns 5XX server errors"
  treat_missing_data  = "notBreaching"

  dimensions = {
    ApiId = var.api_id
  }

  tags = var.tags
}

# 2. SQS Dead-Letter Queue (DLQ) Message Alarm
resource "aws_cloudwatch_metric_alarm" "sqs_dlq_messages" {
  alarm_name          = "${var.environment}-sqs-dlq-messages-detected"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 60
  statistic           = "Maximum"
  threshold           = 0
  alarm_description   = "CRITICAL: Poison messages detected in analytics Dead-Letter Queue"
  treat_missing_data  = "notBreaching"

  dimensions = {
    QueueName = "${var.queue_name}-dlq"
  }

  tags = var.tags
}

# 3. DynamoDB System Errors / Throttles Alarm
resource "aws_cloudwatch_metric_alarm" "dynamodb_throttles" {
  alarm_name          = "${var.environment}-dynamodb-throttling"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ThrottledRequests"
  namespace           = "AWS/DynamoDB"
  period              = 60
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "Triggered if DynamoDB read/write requests are throttled"
  treat_missing_data  = "notBreaching"

  dimensions = {
    TableName = var.dynamodb_table_name
  }

  tags = var.tags
}

# 4. Consolidated CloudWatch Operations Dashboard
resource "aws_cloudwatch_dashboard" "operations" {
  dashboard_name = "${var.environment}-url-shortener-operations"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/ApiGateway", "Count", "ApiId", var.api_id, { label = "API Requests", stat = "Sum", period = 60 }],
            [".", "4xx", ".", ".", { label = "4XX Errors", stat = "Sum", period = 60, color = "#ff7f0e" }],
            [".", "5xx", ".", ".", { label = "5XX Errors", stat = "Sum", period = 60, color = "#d62728" }]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "API Gateway Traffic & Errors"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/SQS", "ApproximateNumberOfMessagesVisible", "QueueName", var.queue_name, { label = "Click Queue Depth", stat = "Maximum", period = 60 }],
            [".", "ApproximateNumberOfMessagesVisible", "QueueName", "${var.queue_name}-dlq", { label = "DLQ Message Count", stat = "Maximum", period = 60, color = "#d62728" }]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "SQS Queue Telemetry & Poison Pill Monitor"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/Lambda", "Duration", "FunctionName", var.redirect_function_name, { label = "Redirect Duration (Avg)", stat = "Average", period = 60 }],
            ["...", { label = "Redirect Duration (p95)", stat = "p95", period = 60, color = "#2ca02c" }]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Redirect Lambda Latency (ms)"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 6
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/DynamoDB", "ConsumedReadCapacityUnits", "TableName", var.dynamodb_table_name, { label = "Consumed RCU", stat = "Sum", period = 60 }],
            [".", "ConsumedWriteCapacityUnits", ".", ".", { label = "Consumed WCU", stat = "Sum", period = 60 }]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "DynamoDB Consumed Capacity"
        }
      }
    ]
  })
}
