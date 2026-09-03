# DynamoDB Data Architecture & Design

## 1. Overview & Single-Table Principles

In accordance with AWS serverless best practices, the database layer for the URL Shortener is modeled around **specific access patterns** rather than relational entity models.

A single-table design is used for the URL registry:
- **Table Name**: `${environment}-urls` (e.g. `dev-urls`)
- **Billing Mode**: `PAY_PER_REQUEST` (On-Demand)
- **Encryption**: AWS Managed KMS Key (`aws/dynamodb`) by default
- **Point-in-Time Recovery (PITR)**: Configurable, disabled in `dev` to minimize unnecessary charges, enabled in production.

---

## 2. Key Schema & Attribute Definitions

### 2.1 Primary Key
- **Partition Key (HASH)**: `short_code` (Type: `String`)
- **Sort Key (RANGE)**: *None*. Every short code (or custom alias) is globally unique. Omitting the sort key optimizes query performance to a direct key-value lookup (`GetItem`), which executes in 3–6 ms.

### 2.2 Attribute Catalog

| Attribute Name | DynamoDB Type | Sample Value | Description |
| :--- | :---: | :--- | :--- |
| `short_code` | `S` | `"aB72x9k"` or `"my-resume"` | Primary key. Unique identifier. |
| `original_url` | `S` | `"https://example.com/deep/link"` | Destination target URL (max 2048 chars). |
| `created_at` | `S` | `"2026-09-03T16:45:00.000000+00:00"` | ISO-8601 UTC creation timestamp. |
| `created_at_epoch`| `N` | `1788453900` | Unix epoch timestamp (seconds). |
| `expires_at` | `N` | `1791045900` | Unix epoch timestamp for DynamoDB TTL. |
| `expires_at_iso` | `S` | `"2026-10-03T16:45:00.000000+00:00"` | Human-readable expiration timestamp. |
| `status` | `S` | `"ACTIVE"` / `"DISABLED"` | Soft-delete status flag. |
| `click_count` | `N` | `142` | Basic atomic click counter. |

---

## 3. Access Patterns & Query Execution

| ID | Access Pattern | Operation | Key Condition & Expression | Target Latency |
| :---: | :--- | :--- | :--- | :---: |
| **AP-01** | Resolve destination URL | `GetItem` | `Key = {"short_code": short_code}` | 3–8 ms |
| **AP-02** | Create new short URL | `PutItem` | `ConditionExpression = "attribute_not_exists(short_code)"` | 5–12 ms |
| **AP-03** | Disable/delete URL | `UpdateItem` | `SET #status = :disabled`, `ConditionExpression = "attribute_exists(short_code)"` | 5–10 ms |
| **AP-04** | Increment basic click count | `UpdateItem` | `ADD click_count :one` | 5–10 ms |

---

## 4. Architectural Decisions

### 4.1 Capacity Mode: On-Demand (`PAY_PER_REQUEST`)
- **Decision**: Use `PAY_PER_REQUEST` instead of provisioned capacity.
- **Justification**:
  1. *Cost Efficiency*: URL shorteners experience highly spiky traffic. On-demand charges strictly for requests made (\$0.25 per million write units, \$0.05 per million read units in `ap-south-1`). Idle cost is **\$0.00**.
  2. *Operational Simplicity*: Eliminates the need to monitor and tune Auto Scaling policies or handle `ProvisionedThroughputExceededException` during sudden traffic bursts.

### 4.2 Read Consistency: Eventually Consistent
- **Decision**: Use Eventually Consistent reads for `GetItem` redirects.
- **Justification**:
  1. Once written, short URL records are rarely mutated.
  2. Eventually consistent reads consume **0.5 RCU per 4 KB** (half the price of strongly consistent reads).
  3. DynamoDB replication lag across three availability zones is typically under 10 milliseconds, making eventual consistency effectively instantaneous for end-users.

### 4.3 Time-To-Live (TTL) Strategy
- **Attribute**: `expires_at` (epoch timestamp in seconds).
- **Behavior**:
  - DynamoDB evaluates TTL in the background and purges expired records within 24–48 hours at zero consumed write capacity.
  - **Application Safeguard (Dual-Check)**: To avoid serving expired links while awaiting DynamoDB's background sweep, `Redirect Lambda` immediately verifies:
    ```python
    if expires_at and int(expires_at) < int(time.time()):
        return error_response(410, "Short code expired")
    ```
    This guarantees strict real-time expiration compliance.

### 4.4 Soft Delete vs Hard Delete
- Disabling a URL sets `status = "DISABLED"`.
- This enables the API to return `410 Gone` rather than `404 Not Found`, providing clear feedback to users that the link was intentionally revoked rather than invalid.
