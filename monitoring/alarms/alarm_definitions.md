# CloudWatch Alarm Specifications & Alert Thresholds

| Alarm Name | Metric | Namespace | Evaluation / Period | Threshold | Severity | Immediate Action |
| :--- | :--- | :--- | :--- | :---: | :---: | :--- |
| **`dev-api-5xx-errors`** | `5xx` | `AWS/ApiGateway` | 1 datapoint / 60s | $> 0$ | P1 - High | Check API Gateway execution logs and Lambda function logs for unhandled exceptions. |
| **`dev-sqs-dlq-messages-detected`**| `ApproximateNumberOfMessagesVisible` | `AWS/SQS` | 1 datapoint / 60s | $> 0$ | P1 - High | Inspect messages in DLQ to diagnose poison pill payloads; check Analytics Lambda logs. |
| **`dev-dynamodb-throttling`** | `ThrottledRequests` | `AWS/DynamoDB` | 1 datapoint / 60s | $> 0$ | P2 - Medium | Evaluate table partition keys for hot key patterns or burst capacity limits. |
| **`dev-lambda-errors`** | `Errors` | `AWS/Lambda` | 1 datapoint / 300s | $> 2$ | P2 - Medium | Review CloudWatch Logs Insights queries for tracebacks and timeout triggers. |
