# Serverless Analytics Queries via Amazon Athena

## 1. Overview & Strategy

Amazon Athena enables interactive SQL queries directly against raw, newline-delimited JSON click telemetry stored in Amazon S3.

### Why Athena?
- **Zero Idle Infrastructure**: No EC2, no clusters to patch, no always-on data warehouse (e.g. Redshift).
- **Extreme Cost Efficiency**: Costs \$5.00 per TB scanned (billed to the nearest MB, minimum 10MB per query). At demo/portfolio scale, scanning hundreds of kilobytes costs less than \$0.0001 per query.
- **Partition Projection**: Utilizes AWS Glue / Athena Partition Projection so new hour/day partitions in S3 are instantly queryable without running metadata repair commands (`MSCK REPAIR TABLE`).

---

## 2. Table Definition & Schema

The table `url_shortener_analytics.clicks` is partitioned by `year`, `month`, `day`, and `hour`:

```sql
PARTITIONED BY (
  year string,
  month string,
  day string,
  hour string
)
```

Partition Projection configuration automatically maps S3 directories matching `s3://<bucket>/clicks/year=YYYY/month=MM/day=DD/hour=HH/` to table partitions based on numeric ranges (2024–2030, months 01–12, days 01–31, hours 00–23).

---

## 3. Standard Production Analytics Queries

All queries are defined in [`application/src/services/athena_queries.sql`](../application/src/services/athena_queries.sql):

1. **Total Overall Click Volume**:
   ```sql
   SELECT count(*) AS total_clicks FROM url_shortener_analytics.clicks;
   ```
2. **Daily Trend (Last 30 Days)**:
   ```sql
   SELECT substr(timestamp, 1, 10) AS click_date, count(*) AS total_clicks
   FROM url_shortener_analytics.clicks
   GROUP BY substr(timestamp, 1, 10)
   ORDER BY click_date DESC;
   ```
3. **Top 10 Performing URLs**:
   ```sql
   SELECT short_code, destination_url, count(*) AS total_clicks
   FROM url_shortener_analytics.clicks
   GROUP BY short_code, destination_url
   ORDER BY total_clicks DESC LIMIT 10;
   ```
4. **Device Distribution Breakdown**:
   ```sql
   SELECT device_type, count(*) AS click_count,
          round(100.0 * count(*) / sum(count(*)) over (), 2) AS percentage
   FROM url_shortener_analytics.clicks
   GROUP BY device_type ORDER BY click_count DESC;
   ```
5. **Browser & OS Distribution**:
   ```sql
   SELECT browser, count(*) AS click_count,
          round(100.0 * count(*) / sum(count(*)) over (), 2) AS percentage
   FROM url_shortener_analytics.clicks
   GROUP BY browser ORDER BY click_count DESC;
   ```
6. **Traffic Referrers (Direct vs Social vs Search)**:
   ```sql
   SELECT referrer, count(*) AS click_count
   FROM url_shortener_analytics.clicks
   GROUP BY referrer ORDER BY click_count DESC LIMIT 10;
   ```
7. **Latency SLA Compliance (p50 / p95 / p99)**:
   ```sql
   SELECT
     approx_percentile(latency_ms, 0.50) AS p50_latency_ms,
     approx_percentile(latency_ms, 0.95) AS p95_latency_ms,
     approx_percentile(latency_ms, 0.99) AS p99_latency_ms
   FROM url_shortener_analytics.clicks;
   ```

---

## 4. Operational Diagnostics & Trace Queries

The telemetry schema includes `request_id` and `correlation_id` propagated across the API Gateway, Lambda, and SNS/SQS boundaries, enabling Athena to act as an operational diagnostic tool:

8. **Distributed Correlation Trace Lookup**:
   Locate the entire execution and click trajectory for a specific transaction or user session:
   ```sql
   SELECT timestamp, short_code, request_id, correlation_id, http_status, latency_ms, browser
   FROM url_shortener_analytics.clicks
   WHERE correlation_id = 'YOUR_CORRELATION_ID_HERE'
   ORDER BY timestamp DESC;
   ```

9. **HTTP Anomaly & Error Detection**:
   Isolate abnormal status codes or redirect latencies exceeding 100ms:
   ```sql
   SELECT short_code, http_status, count(*) AS failure_count, round(avg(latency_ms), 2) AS avg_latency_ms
   FROM url_shortener_analytics.clicks
   WHERE http_status != 302 OR latency_ms > 100.0
   GROUP BY short_code, http_status
   ORDER BY failure_count DESC;
   ```

10. **At-Least-Once SQS Delivery & Deduplication Audit**:
    Audit duplicate message deliveries via SQS retry by unique `event_id`:
    ```sql
    SELECT event_id, count(*) AS delivery_count, min(timestamp) AS first_seen, max(timestamp) AS last_seen
    FROM url_shortener_analytics.clicks
    GROUP BY event_id HAVING count(*) > 1;
    ```

---

## 5. Query Cost Optimization Best Practices
1. **Always filter by date partition** when querying specific time ranges:
   ```sql
   WHERE year = '2026' AND month = '09' AND day >= '01'
   ```
   This prevents Athena from scanning prior months/years of logs.
2. **Store analytical query results in dedicated S3 prefix** (`s3://<bucket>/athena-results/`) configured with an S3 Lifecycle expiration rule of 7 days to eliminate orphaned query result storage costs.
