-- ==============================================================================
-- Athena DDL & Analytical Queries for URL Shortener Platform
-- Database: url_shortener_analytics
-- ==============================================================================

-- 1. Create Analytics Database
CREATE DATABASE IF NOT EXISTS url_shortener_analytics
COMMENT 'Serverless click telemetry database for URL shortener';

-- 2. Create Partitioned External Table
-- Uses Partition Projection to avoid running manual MSCK REPAIR TABLE commands
CREATE EXTERNAL TABLE IF NOT EXISTS url_shortener_analytics.clicks (
  event_id string,
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
  'mapping.event_id' = 'event_id'
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

-- Query 8: End-to-End Latency Performance (p50, p95, p99 in milliseconds)
SELECT
  approx_percentile(latency_ms, 0.50) AS p50_latency_ms,
  approx_percentile(latency_ms, 0.95) AS p95_latency_ms,
  approx_percentile(latency_ms, 0.99) AS p99_latency_ms
FROM url_shortener_analytics.clicks;
