# CloudWatch Observability, Metrics & Logging Guide

## 1. Observability Architecture

The observability stack utilizes native AWS CloudWatch features to provide full end-to-end visibility across:
1. Edge & Ingress (API Gateway access logs & status codes)
2. Serverless Compute (Lambda duration, error rate, invocations)
3. Asynchronous Messaging (SQS backlog depth, DLQ poison pill alerts)
4. Data Persistence (DynamoDB read/write units, throttles)

---

## 2. Structured Logging Guidelines

All Lambda services emit logs in structured format compatible with CloudWatch Logs Insights.

### Sample Redirect Log:
```json
{
  "timestamp": "2026-09-03T16:55:00.123Z",
  "level": "INFO",
  "operation": "redirect",
  "short_code": "aB72x9k",
  "destination": "https://example.com/target",
  "status": "success",
  "latency_ms": 14.85,
  "requestId": "c6b41c24-e902-46a4-9799-6e3e1505c8a2"
}
```

### Critical Security Rule for Logs:
- **Never log**: Authorization headers, passwords, session cookies, raw IP addresses, or customer secret parameters.

---

## 3. Useful CloudWatch Logs Insights Queries

### Query 1: Top Slowest Redirects
```sql
fields @timestamp, short_code, destination, latency_ms
| filter operation = "redirect"
| sort latency_ms desc
| limit 20
```

### Query 2: Error Rate by Short Code
```sql
fields @timestamp, short_code, error.code, error.message
| filter ispresent(error)
| stats count(*) as error_count by short_code, error.code
| sort error_count desc
```

### Query 3: Hourly Traffic Volume
```sql
stats count(*) by bin(1h)
```
