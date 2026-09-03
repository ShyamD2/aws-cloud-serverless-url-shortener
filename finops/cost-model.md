# FinOps Cost Model: Serverless URL Shortener & Analytics

## 1. Official AWS Pricing Baseline (ap-south-1 / Asia Pacific Mumbai)

All calculations reflect official AWS public retail rates without enterprise discounts.

| Service | Pricing Metric / Unit | AWS Free Tier Allowance | Unit Cost |
| :--- | :--- | :--- | :--- |
| **API Gateway (HTTP API v2)** | Per 1,000,000 requests | None (HTTP API has no dedicated free tier) | **\$1.00** / 1M |
| **AWS Lambda** | Requests & Duration (256MB) | 1,000,000 requests + 3.2M GB-sec/month free | \$0.20 / 1M requests<br/>+\$0.0000041667/sec (256MB) |
| **Amazon DynamoDB (On-Demand)** | Read / Write Request Units | 25 GB storage free | \$0.25 / 1M RRUs (reads)<br/>\$1.25 / 1M WRUs (writes) |
| **Amazon SQS (Standard)** | Per 1,000,000 requests | 1,000,000 requests/month free | **\$0.40** / 1M requests |
| **Amazon S3 (Standard)** | Storage & Request Operations | 5 GB storage + 20,000 GETs + 2,000 PUTs free | \$0.023 / GB-month<br/>\$0.005 / 1,000 PUTs |
| **Amazon CloudFront** | Data Transfer Out & Requests | 1 TB data transfer + 10M requests free indefinitely | **\$0.00** (within free tier) |
| **Amazon Athena** | Per Terabyte (TB) scanned | None | **\$5.00** / TB scanned |
| **Amazon CloudWatch** | Metrics, Logs & Alarms | 10 alarms + 5 GB log ingestion free | **\$0.00** (within free tier) |

---

## 2. Workload Cost Projections

### Scenario A: Low / Portfolio Traffic (10,000 clicks/month)
- **API Gateway**: 10,000 requests = \$0.010
- **Lambda**: 10,000 invocations (25ms avg @ 256MB) = \$0.000 (Free Tier)
- **DynamoDB**: 10,000 reads = \$0.002
- **SQS**: 10,000 messages = \$0.000 (Free Tier)
- **S3**: < 100 MB = \$0.002
- **CloudFront**: Free Tier
- **CloudWatch**: Free Tier
- **Total Projected Monthly Cost**: **~\$0.02 / month** (Well within \$5.00 target)

---

### Scenario B: Moderate Production Traffic (1,000,000 clicks/month)
Assuming 90% redirects (900,000) and 10% URL creations (100,000):

| Service | Usage Calculation | Monthly Cost |
| :--- | :--- | :--- |
| **API Gateway** | 1,000,000 requests $\times$ \$1.00/1M | \$1.00 |
| **AWS Lambda** | 1,000,000 requests (\$0.20) + 25,000 GB-sec (\$0.10) after free tier | \$0.30 |
| **DynamoDB** | 900k reads (\$0.23) + 100k writes (\$0.13) | \$0.36 |
| **SQS** | 1M clicks published + 100k batch receives = 1.1M (\$0.04 after free tier) | \$0.04 |
| **S3** | 100,000 PUTs (batched 10:1 = 10,000 PUTs) $\times$ \$0.005/1k + 5GB storage | \$0.16 |
| **CloudFront** | 1M requests (Free Tier allows 10M) | \$0.00 |
| **Athena** | 20 analytical queries scanning ~200MB each (4GB total) | \$0.02 |
| **CloudWatch** | 1GB logs ingested + 4 alarms (within free tier) | \$0.00 |
| **Total Monthly Cost** | | **\$1.88 / month** |

---

## 3. Unit Economics
- **Cost per 1,000,000 Requests**: **\$1.88**
- **Marginal Cost per Redirect**: **\$0.00000188**
