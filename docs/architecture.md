# Architecture Design: Serverless URL Shortener & Analytics Platform

## 1. Executive Summary & Philosophy

This document outlines the architecture for the **Production-Grade Serverless URL Shortener & Analytics Platform**. 

The architecture is built on five core principles:
1. **True Serverless & Pay-per-Use**: Zero idle compute costs; operates strictly within the AWS Free Tier during development/demo, with estimated costs under \$1.00/month.
2. **Ultra-Low Latency Redirects**: The read path (`GET /{short_code}`) must execute within 15–30 ms by decoupling analytics processing via asynchronous message queuing.
3. **Least Privilege & Defense-in-Depth**: Strict IAM policies scoped to resource ARNs, encrypted data at rest and in transit, and thorough input sanitization.
4. **Pragmatic Simplicity**: Deliberate avoidance of over-engineered components (no VPC overhead, no managed Kubernetes, no unnecessary microservice sprawl).
5. **Observability-First**: Structured JSON logging, real-time CloudWatch metrics, and Dead-Letter Queues (DLQ) for asynchronous workloads.

---

## 2. End-to-End Architecture Diagram

```mermaid
flowchart TD
    subgraph Clients["Clients & Browsers"]
        U["End User / Browser"]
        Admin["Developer / Admin Client"]
    end

    subgraph EdgeFrontend["Edge & Frontend Distribution"]
        CF["Amazon CloudFront<br/>(Static SPA Distribution & API Reverse Proxy)"]
        S3Web["Amazon S3<br/>(Frontend Web Assets Bucket)"]
        CF -->|Fetches Static Assets| S3Web
    end

    subgraph IngestionLayer["API & Ingestion Layer"]
        APIGW["Amazon API Gateway (HTTP API v2)<br/>Payload Compression & Throttling"]
        CF -->|Routes /api/* & /{short_code}| APIGW
    end

    subgraph ComputeLayer["Compute Layer (Serverless Functions)"]
        L_Create["Create URL Lambda<br/>(Python 3.13)"]
        L_Redirect["Redirect Lambda<br/>(Python 3.13)"]
        L_Analytics["Analytics Processor Lambda<br/>(Python 3.13)"]
    end

    subgraph StorageLayer["Data Storage & Async Queuing"]
        DDB[("Amazon DynamoDB<br/>(Single-Table, On-Demand, TTL)")]
        SQS["Amazon SQS Standard Queue<br/>(Decoupled Click Stream)"]
        SQS_DLQ["Amazon SQS Dead-Letter Queue<br/>(Poison Messages)"]
        S3_Data[("Amazon S3 Analytics Bucket<br/>(Partitioned Parquet / JSONL)")]
    end

    subgraph AnalyticsLayer["Query & Observability Layer"]
        Athena["Amazon Athena<br/>(Serverless SQL Analytics)"]
        CW["Amazon CloudWatch<br/>(Metrics, Alarms, Structured Logs)"]
    end

    %% Client Interactions
    U -->|1. Resolves short link| CF
    Admin -->|Interacts with Web UI| CF
    Admin -->|Calls REST API directly| APIGW

    %% Ingestion Routing
    APIGW -->|"POST /api/urls"| L_Create
    APIGW -->|"GET /:short_code"| L_Redirect

    %% URL Creation Flow
    L_Create -->|Writes item with TTL| DDB
    L_Create -.->|Logs & Metrics| CW

    %% Redirect Flow (Decoupled)
    L_Redirect -->|GetItem: Fetch URL| DDB
    L_Redirect -->|Sends 301/302 Location Header| U
    L_Redirect -->|Fire-and-forget: Push click event| SQS
    L_Redirect -.->|Logs & Metrics| CW

    %% Async Analytics Flow
    SQS -->|Batch triggers| L_Analytics
    SQS -.->|After 3 failed retries| SQS_DLQ
    L_Analytics -->|Buffers & writes batch| S3_Data
    L_Analytics -.->|Logs & Metrics| CW

    %% Querying
    Athena -->|Queries partitioned data| S3_Data
```

---

## 3. Request Flows

### 3.1 URL Creation Flow (`POST /api/urls`)
1. **Client Request**: The client sends a `POST` request with a JSON payload: `{"url": "https://example.com/target", "custom_alias": "custom", "ttl_days": 30}`.
2. **Validation**: The `Create URL Lambda` performs syntactic and security validations:
   - Must start with `http://` or `https://`.
   - Domain must not match the shortener domain (loop prevention).
   - URL length $\le$ 2048 characters.
   - Optional `custom_alias` must follow `^[a-zA-Z0-9_-]{3,30}$`.
3. **Short Code Generation**: If no custom alias is specified, a cryptographically secure 7-character Base62 identifier is generated.
4. **Conditional Put**: A DynamoDB `PutItem` operation is executed with a condition expression `attribute_not_exists(short_code)` to guarantee uniqueness and prevent race conditions.
5. **Response**: HTTP 201 Created returning `short_code`, `short_url`, `created_at`, and `expires_at`.

### 3.2 High-Performance Redirect Flow (`GET /{short_code}`)
1. **Client Request**: User clicks `https://domain/{short_code}`.
2. **Direct Lookup**: API Gateway routes to `Redirect Lambda`. The function executes a single, highly indexed DynamoDB `GetItem` query.
3. **Status & Expiration Evaluation**:
   - If item not found: returns HTTP 404 Not Found.
   - If item is marked `status = DISABLED`: returns HTTP 410 Gone.
   - If `expires_at` is set and `expires_at < current_timestamp`: returns HTTP 410 Gone.
4. **Immediate Redirect**: The Lambda immediately responds with HTTP 302 (or 301) and a `Location: <original_url>` header. The client is immediately forwarded without waiting for analytics.
5. **Asynchronous Telemetry Dispatch**: Simultaneously or via non-blocking execution, the click event (metadata: IP hash/country, user-agent parsed device/browser/OS, referrer, timestamp) is published to the `Amazon SQS` queue.

### 3.3 Asynchronous Analytics Pipeline
1. **Queueing**: SQS buffers incoming click events. If traffic spikes occur (e.g., viral link), the SQS queue absorbs the burst without throttling DynamoDB or degrading redirect response times.
2. **Batch Processing**: The `Analytics Processor Lambda` is triggered by SQS in batches (e.g., batch size: 10 items, batching window: 5 seconds).
3. **Partitioned Ingestion**: The processor aggregates events and flushes them to the Analytics S3 bucket using a temporal hive-style partition layout:
   ```
   s3://<analytics-bucket>/clicks/year=YYYY/month=MM/day=DD/hour=HH/<batch-id>.jsonl
   ```
4. **Poison-Pill Handling**: If the processor fails to parse or write a batch after 3 retries, SQS routes the message to the Dead-Letter Queue (`SQS_DLQ`) to prevent queue stalling.

---

## 4. Why Each AWS Service Was Chosen

| AWS Service | Practical Reason for Inclusion | Alternative Considered & Why Rejected |
| :--- | :--- | :--- |
| **Amazon API Gateway (HTTP API v2)** | Low latency, built-in CORS, native Lambda integration, 70% cheaper than REST APIs (\$1.00 vs \$3.50 per million requests). | **Application Load Balancer (ALB)**: Rejected due to \$16–22/month fixed baseline cost for idle instances. |
| **AWS Lambda (Python 3.13)** | True zero-idle cost, sub-second auto-scaling from 0 to thousands of concurrent requests, low operational burden. | **AWS Fargate / ECS**: Rejected due to minimum hourly task compute charges and container management overhead. |
| **Amazon DynamoDB (On-Demand)** | Single-digit millisecond reads at any scale, native automatic TTL expiration, zero baseline cost in On-Demand mode. | **Amazon Aurora Serverless**: Rejected due to high minimum ACU baseline cost (\$30–45+/month) and connection pool management complexity. |
| **Amazon SQS (Standard)** | Decouples read/redirect path from analytics writes; eliminates latency penalties on user redirects; provides backpressure buffer. | **Amazon Kinesis Data Streams**: Rejected due to persistent per-shard hourly costs (\$0.015/shard/hr $\approx$ \$11/month). |
| **Amazon S3** | Durable, virtually limitless, ultra-cheap storage for partitioned analytics events (\$0.023/GB/month). | **DynamoDB Click Table**: Rejected because high-volume analytical records rapidly inflate DynamoDB storage and scan costs. |
| **Amazon Athena** | Serverless interactive SQL analytics directly over raw S3 data without maintaining an always-on database (\$5.00 per TB scanned; < \$0.01 for small datasets). | **Amazon Redshift Serverless / OpenSearch**: Rejected due to steep hourly costs (\$100s/month) for an analytical workload that is queried occasionally. |
| **Amazon CloudWatch** | Unified logging, custom metrics, and alarm triggers native to all AWS services without third-party agents. | **Datadog / New Relic**: Rejected due to licensing costs and unnecessary complexity for a serverless AWS-focused project. |
| **Amazon CloudFront** | Low-latency CDN edge delivery for frontend single-page application assets with HTTPS by default. | **S3 Website Hosting (Direct HTTP)**: Direct S3 website endpoints do not support modern TLS/HTTPS without CloudFront. |

---

## 5. Deliberate Architectural Omissions (Simplicity & Cost Discipline)

In compliance with the project's strict budget target (< \$5.00/month) and junior-engineer clarity, the following services were **deliberately excluded**:

1. **Amazon Route 53 & AWS Certificate Manager (ACM) for Custom Domains**:
   - *Reason*: Avoids requiring the user to purchase a public top-level domain (\$12–15/year) and provision hosted zones (\$0.50/month per zone). The system uses CloudFront default `*.cloudfront.net` and API Gateway default `*.execute-api.{region}.amazonaws.com` URLs, which natively provide TLS 1.3 certificates for free.
2. **AWS WAF (Web Application Firewall)**:
   - *Reason*: AWS WAF charges \$5.00/month per WebACL + \$1.00/month per rule group. Adding 2 rules immediately breaches the \$10.00/month ceiling without traffic. In-code rate limiting, API Gateway throttling (burst and rate limits), and strict input validation achieve effective application protection for this tier.
3. **AWS VPC (Virtual Private Cloud) for Lambdas**:
   - *Reason*: Lambdas interact purely with AWS public endpoints (DynamoDB, SQS, S3) using AWS SigV4. Placing Lambdas in a private VPC would require NAT Gateways (\$32.00+/month) or VPC Endpoints (\$7.20/month per interface endpoint), incurring significant recurring costs with zero security benefit for this architecture.
4. **Amazon ElastiCache (Redis / Memcached)**:
   - *Reason*: Minimum node cost is ~\$12–15/month. DynamoDB single-item lookups consistently achieve single-digit millisecond latency (3–8 ms), which is more than sufficient without adding an expensive caching layer.

---

## 6. Failure Handling & Reliability Matrix

| Failure Scenario | Mitigation & System Behavior |
| :--- | :--- |
| **DynamoDB Read Outage / Throttling** | SDK exponential backoff and jitter. CloudWatch alarms monitor `ThrottledRequests`. In On-Demand mode, DynamoDB instantly adapts to traffic up to 4,000 WCU / 12,000 RCU. |
| **SQS Producer Failure during Redirect** | Non-blocking exception handling in `Redirect Lambda`: if SQS enqueue fails, the error is logged to CloudWatch, and the HTTP 302 redirect is **still fulfilled** to protect user experience. |
| **Analytics Processing Malformed Record** | Batch retry mechanism with `maxReceiveCount = 3`. Poison messages are diverted to `SQS Dead-Letter Queue (DLQ)`, emitting an alarm while healthy messages continue processing. |
| **Expired URL Request** | Evaluated via application logic (`expires_at < now`). Returns HTTP 410 Gone with informative JSON payload before DynamoDB background TTL sweeps the item. |
| **Duplicate Custom Alias Creation** | Handled gracefully via DynamoDB conditional writes. Returns HTTP 409 Conflict with message `"Alias already in use"`. |
