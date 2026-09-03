# Failure Mode & Resilience Testing Matrix

This runbook documents the failure scenarios tested in the development environment, detailing the detection mechanism, system behavior, recovery path, and end-user impact.

---

## Failure Testing Summary Matrix

| Failure Mode | How Detected | What Happened | How System Recovered | User Experience |
| :--- | :--- | :--- | :--- | :--- |
| **1. Invalid URL Scheme** (e.g. `ftp://`, `javascript:`) | In-code validation in `validation.py` | Request rejected before reaching database | Stateless; no state changed | HTTP `400 Bad Request` with clear explanation |
| **2. Expired URL Requested** | In-code epoch check (`expires_at < now`) | Redirect Lambda identified expired item | Item marked for background TTL cleanup | HTTP `410 Gone` with message `Short code expired` |
| **3. Missing URL Requested** | DynamoDB `GetItem` returned empty item | Lookup returned empty dict | Fast exit; no downstream calls | HTTP `404 Not Found` |
| **4. Duplicate Custom Alias** | DynamoDB `ConditionalCheckFailedException` | Write blocked by conditional expression | Request aborted; existing record preserved | HTTP `409 Conflict` (`Alias already in use`) |
| **5. Lambda Unhandled Error** | CloudWatch Lambda `Errors` metric & Logs | Exception logged with stack trace | Lambda container resets; error captured in log group | HTTP `500 Internal Server Error` (generic error, no trace leaked) |
| **6. Malformed Analytics Event** | JSON parse exception in Analytics Lambda | Event rejected from batch | SQS retries message up to `maxReceiveCount = 3` | Zero impact on end-user redirect (isolated async worker) |
| **7. SQS Consumer Backlog** | CloudWatch metric `ApproximateNumberOfMessagesVisible` | Events buffer safely in SQS queue | Lambda auto-scales concurrent batch invocations | No message loss; redirect latency completely unaffected |
| **8. Poison Pill Message in SQS** | CloudWatch DLQ alarm `dev-sqs-dlq-messages` | Message fails 3 times | SQS routes poison message to `dev-click-events-dlq` | Queue unblocks; operator investigates DLQ payloads |
| **9. DynamoDB Throttling** | CloudWatch alarm `dev-dynamodb-throttling` | Traffic exceeds burst capacity | On-Demand mode auto-scales up to 4,000 WCU / 12,000 RCU | Temporary slight latency increase; retry with exponential backoff |
| **10. Failed Smoke Test on Deploy** | `scripts/validate.sh` non-zero exit code | Post-deployment smoke test failed | GitHub Actions halts pipeline; triggers rollback runbook | Production traffic untouched; bad release blocked |
