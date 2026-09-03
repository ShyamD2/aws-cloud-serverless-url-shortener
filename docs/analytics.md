# Analytics Pipeline Design & Telemetry Specifications

## 1. Overview & Architecture

The analytics pipeline captures real-time click telemetry for shortened URLs without introducing latency penalties to user redirects.

```mermaid
sequenceDiagram
    autonumber
    actor User as User Browser
    participant Redirect as Redirect Lambda
    participant DDB as DynamoDB Table
    participant SQS as SQS Click Queue
    participant SQS_DLQ as SQS Dead-Letter Queue
    participant Analytics as Analytics Processor Lambda
    participant S3 as Analytics S3 Bucket

    User->>Redirect: GET /{short_code}
    Redirect->>DDB: GetItem(short_code)
    DDB-->>Redirect: Return destination_url
    Redirect->>User: HTTP 302 Found (Location: destination_url)
    Note over User: User navigation completes in < 30ms

    par Async Dispatch
        Redirect->>SQS: SendMessage(click_event)
    end

    Note over SQS,Analytics: SQS buffers events; triggers Lambda in batches (10 msgs or 5s window)
    SQS->>Analytics: Batch Event [Record 1 .. N]
    alt Batch processing succeeds
        Analytics->>S3: PutObject (Hive partitioned JSONL)
        Analytics-->>SQS: Delete batch messages from queue
    else Retry limit exceeded (maxReceiveCount = 3)
        SQS->>SQS_DLQ: Route poison message to DLQ
    end
```

---

## 2. Telemetry Event Schema

Telemetry events capture operational and statistical metrics strictly for performance and aggregate analytics:

```json
{
  "event_id": "4b5d6a89-21b4-4e78-9e6b-07b1b601f7a0",
  "timestamp": "2026-09-03T16:50:12.345678+00:00",
  "timestamp_epoch": 1788454212,
  "short_code": "my-promo",
  "destination_url": "https://example.com/products/deals",
  "referrer": "https://news.ycombinator.com",
  "country": "US",
  "browser": "Chrome",
  "os": "macOS",
  "device_type": "Desktop",
  "http_status": 302,
  "latency_ms": 14.85
}
```

### 2.1 Privacy & Compliance Principles
- **No IP Addresses**: Client IP addresses are never persisted in SQS or S3, adhering to GDPR/CCPA telemetry minimization guidelines.
- **Referrer Sanitization**: Query strings (e.g. `?auth_token=...`, `?user_id=...`) are stripped from `Referer` headers prior to storage.
- **Coarse Geolocation**: Only 2-letter ISO country codes derived from CloudFront edge headers (`CloudFront-Viewer-Country`) are recorded.

---

## 3. Ingestion & Storage Architecture

### 3.1 SQS Buffering Parameters
- **Queue Type**: Standard SQS Queue (high throughput, virtually unlimited TPS).
- **Batch Size**: 10 messages per invocation.
- **Maximum Batching Window**: 5 seconds (allows Lambda to collect multiple events into one write, saving S3 PUT costs).
- **Visibility Timeout**: 30 seconds (6x Lambda execution timeout of 5 seconds).
- **Message Retention**: 4 days.
- **Dead-Letter Queue (DLQ)**: `maxReceiveCount = 3`. Unprocessable messages divert to the DLQ to prevent blocking the queue.

### 3.2 S3 Storage Partitioning
Data is written in **Newline-Delimited JSON (NDJSON / JSONL)** format using standard Hive-style partitioning:

```
s3://<analytics-bucket>/clicks/year=YYYY/month=MM/day=DD/hour=HH/<uuid>.jsonl
```

**Benefits**:
1. **Athena Partition Pruning**: Queries filtering by date or hour only scan files in the requested partitions, drastically reducing data scanned and query latency.
2. **Cost Minimization**: Athena pricing is \$5.00 per TB scanned. By scanning only targeted partitions, queries cost fractions of a cent.
