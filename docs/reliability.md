# System Reliability & Resilience Architecture

## 1. Overview & Philosophy

The platform achieves high reliability without enterprise complexity by combining native AWS serverless primitives with defensive application engineering.

---

## 2. Reliability Mechanisms Across the Stack

```
[ Incoming Request ]
        │
        ▼
[ API Gateway Throttling ]  ── (50 burst / 100 steady) protects Lambda from saturation
        │
        ▼
[ Redirect Lambda ]
   ├── DynamoDB Lookup
   │      └── Conditional evaluation: Status active? Expired? (Returns 302, 404, or 410)
   └── SQS Publish (Non-Blocking)
          ├── Success: Click buffered
          └── SQS Failure: Logged to CloudWatch, 302 redirect STILL returned to user!
                  │
                  ▼
          [ SQS Click Buffer ]
                  │
                  ▼ (Batch size: 10, window: 5s)
          [ Analytics Processor Lambda ]
                  │
                  ├── Success: Writes JSONL batch to S3
                  └── Failure: Retries up to 3 times
                          │
                          └── After 3 retries: Diverts to Dead-Letter Queue (DLQ) + CloudWatch Alarm
```

---

## 3. Key Fault-Tolerance Patterns

### 3.1 Non-Blocking Read Path
User redirects must **never fail** due to background telemetry issues. In `src/handlers/redirect.py`:
```python
try:
    analytics_service.publish_click_event(click_event)
except Exception:
    logger.exception("Failed to dispatch telemetry for short code %s", short_code)
# HTTP 302 is still returned to the user
return redirect_response(location=destination_url, status_code=302)
```

### 3.2 Race-Condition Prevention (DynamoDB Conditional Writes)
When registering custom aliases or generated short codes, DynamoDB evaluates:
```python
ConditionExpression="attribute_not_exists(short_code)"
```
This guarantees atomic uniqueness without requiring distributed locks.

### 3.3 Poison-Pill Quarantine (SQS DLQ)
If a malformed event (e.g. invalid encoding, schema corruption) triggers an exception in `Analytics Processor Lambda`, SQS retries twice more before sending the message to `dev-click-events-dlq`. This isolates bad payloads and prevents them from blocking subsequent events.

### 3.4 Idempotency in Analytics Storage
Analytics batches written to S3 are named with UUIDs (`<uuid>.jsonl`). In the event of a message retry, duplicate records are harmlessly isolated or reconciled by event ID during Athena queries (`SELECT DISTINCT event_id`).
