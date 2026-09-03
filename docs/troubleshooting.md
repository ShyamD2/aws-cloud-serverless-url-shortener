# Troubleshooting & Diagnostic Runbook

## 1. Common Issues & Resolutions

### Issue 1: Short URL Returns HTTP 404
- **Root Cause**: The requested `short_code` does not exist in the DynamoDB table.
- **Diagnostic Step**:
  ```bash
  aws dynamodb get-item \
    --table-name dev-urls \
    --key '{"short_code": {"S": "<requested_code>"}}' \
    --region ap-south-1
  ```
- **Resolution**: Verify that the creation request succeeded and that the client is not appending unintended slashes or query parameters.

---

### Issue 2: Short URL Returns HTTP 410 Gone
- **Root Cause**: The link was either soft-deleted (`status = "DISABLED"`) or its TTL has passed (`expires_at < current_epoch`).
- **Resolution**: Verify `expires_at` or recreate the link if it expired.

---

### Issue 3: Messages Appearing in SQS Dead-Letter Queue (DLQ)
- **Root Cause**: The `Analytics Processor Lambda` encountered 3 consecutive errors parsing or writing a batch of click telemetry events.
- **Diagnostic Steps**:
  1. Inspect message attributes and body in DLQ:
     ```bash
     aws sqs receive-message \
       --queue-url $(aws sqs get-queue-url --queue-name dev-click-events-dlq --query QueueUrl --output text) \
       --max-number-of-messages 5 \
       --region ap-south-1
     ```
  2. Query CloudWatch Logs for `dev-analytics-processor`:
     ```bash
     aws logs filter-log-events \
       --log-group-name /aws/lambda/dev-analytics-processor \
       --filter-pattern "ERROR" \
       --region ap-south-1
     ```

---

### Issue 4: S3 Access Denied when Accessing Frontend via CloudFront
- **Root Cause**: S3 Origin Access Control (OAC) policy missing on the bucket or incorrect regional domain name.
- **Resolution**: Confirm the S3 bucket policy in `terraform/modules/cloudfront/main.tf` allows `cloudfront.amazonaws.com` with condition matching the CloudFront distribution ARN.
