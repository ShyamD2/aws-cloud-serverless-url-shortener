-- ==============================================================================
-- Athena DDL & Analytical Queries for URL Shortener Platform
-- Database: url_shortener_analytics
-- ==============================================================================

-- 1. Create Analytics Database
CREATE DATABASE IF NOT EXISTS url_shortener_analytics
COMMENT 'Serverless click telemetry and diagnostics database for URL shortener';

-- 2. Create Partitioned External Table
-- Uses Partition Projection to avoid running manual MSCK REPAIR TABLE commands
CREATE EXTERNAL TABLE IF NOT EXISTS url_shortener_analytics.clicks (
  event_id string,
  request_id string,
  correlation_id string,
  timestamp string,
  timestamp_epoch bigint,
  short_code string,
  destination_url string,
  referrer string,
  country string,
  browser string,
  os string,
  device_type string,
  http_status int,
  latency_ms double
)
PARTITIONED BY (
  year string,
  month string,
  day string,
  hour string
)
ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
WITH SERDEPROPERTIES (
  'ignore.malformed.json' = 'true',
  'mapping.event_id' = 'event_id',
  'mapping.request_id' = 'request_id',
  'mapping.correlation_id' = 'correlation_id'
)
LOCATION 's3://${analytics_bucket_name}/clicks/'
TBLPROPERTIES (
  'projection.enabled' = 'true',
  'projection.year.type' = 'date',
  'projection.year.range' = '2024,2030',
  'projection.year.format' = 'yyyy',
  'projection.month.type' = 'integer',
  'projection.month.range' = '01,12',
  'projection.month.digits' = '2',
  'projection.day.type' = 'integer',
  'projection.day.range' = '01,31',
  'projection.day.digits' = '2',
  'projection.hour.type' = 'integer',
  'projection.hour.range' = '00,23',
  'projection.hour.digits' = '2',
  'storage.location.template' = 's3://${analytics_bucket_name}/clicks/year=${year}/month=${month}/day=${day}/hour=${hour}'
);

-- ==============================================================================
-- Analytical Queries
-- ==============================================================================

-- Query 1: Total Overall Clicks
SELECT count(*) AS total_clicks
FROM url_shortener_analytics.clicks;

-- Query 2: Daily Click Volume (Last 30 Days)
SELECT
  substr(timestamp, 1, 10) AS click_date,
  count(*) AS total_clicks
FROM url_shortener_analytics.clicks
GROUP BY substr(timestamp, 1, 10)
ORDER BY click_date DESC;

-- Query 3: Top Performing Short URLs
SELECT
  short_code,
  destination_url,
  count(*) AS total_clicks
FROM url_shortener_analytics.clicks
GROUP BY short_code, destination_url
ORDER BY total_clicks DESC
LIMIT 10;

-- Query 4: Device Type Distribution
SELECT
  device_type,
  count(*) AS click_count,
  round(100.0 * count(*) / sum(count(*)) over (), 2) AS percentage
FROM url_shortener_analytics.clicks
GROUP BY device_type
ORDER BY click_count DESC;

-- Query 5: Browser Distribution
SELECT
  browser,
  count(*) AS click_count,
  round(100.0 * count(*) / sum(count(*)) over (), 2) AS percentage
FROM url_shortener_analytics.clicks
GROUP BY browser
ORDER BY click_count DESC;

-- Query 6: Top Referrer Traffic Sources
SELECT
  referrer,
  count(*) AS click_count,
  round(100.0 * count(*) / sum(count(*)) over (), 2) AS percentage
FROM url_shortener_analytics.clicks
GROUP BY referrer
ORDER BY click_count DESC
LIMIT 10;

-- Query 7: Geolocation Breakdown (Top Countries)
SELECT
  country,
  count(*) AS click_count
FROM url_shortener_analytics.clicks
GROUP BY country
ORDER BY click_count DESC
LIMIT 10;

-- ==============================================================================
-- Diagnostics & Observability Queries
-- ==============================================================================

-- Query 8: End-to-End Latency Performance (p50, p95, p99 in milliseconds)
SELECT
  approx_percentile(latency_ms, 0.50) AS p50_latency_ms,
  approx_percentile(latency_ms, 0.95) AS p95_latency_ms,
  approx_percentile(latency_ms, 0.99) AS p99_latency_ms,
  round(avg(latency_ms), 2) AS avg_latency_ms,
  round(max(latency_ms), 2) AS max_latency_ms
FROM url_shortener_analytics.clicks;

-- Query 9: Diagnostics - Request Context & Distributed Correlation Tracing
-- Correlates an individual request trace across API Gateway, Lambda, and SNS/SQS
SELECT
  timestamp,
  short_code,
  request_id,
  correlation_id,
  http_status,
  latency_ms,
  browser,
  country
FROM url_shortener_analytics.clicks
WHERE correlation_id = 'YOUR_CORRELATION_ID_HERE'
ORDER BY timestamp DESC;

-- Query 10: Diagnostics - HTTP Status Anomaly & Failure Rate Detection
-- Audits non-302 redirect responses or elevated latency spikes
SELECT
  short_code,
  http_status,
  count(*) AS occurrence_count,
  round(avg(latency_ms), 2) AS avg_latency_ms,
  round(max(latency_ms), 2) AS max_latency_ms
FROM url_shortener_analytics.clicks
WHERE http_status != 302 OR latency_ms > 100.0
GROUP BY short_code, http_status
ORDER BY occurrence_count DESC;

-- Query 11: Diagnostics - Event Deduplication & SQS Delivery Audit
-- Detects potential at-least-once duplicate deliveries by unique event_id
SELECT
  event_id,
  count(*) AS delivery_count,
  min(timestamp) AS first_seen,
  max(timestamp) AS last_seen
FROM url_shortener_analytics.clicks
GROUP BY event_id
HAVING count(*) > 1
ORDER BY delivery_count DESC;
