# FinOps Cost Optimization & Budget Guardrails

## 1. Automated Guardrails

### 1.1 The \$10.00/Month Circuit Breaker (AWS Budget)
An AWS Budget is established with strict notification thresholds:
- **80% Actual Spend Alert (\$8.00)**: Warns the engineering team of unusual traffic surges.
- **100% Forecasted Spend Alert (\$10.00)**: Fires if AWS billing models predict that the current trajectory will breach \$10.00 before month-end.

```hcl
resource "aws_budgets_budget" "cost_ceiling" {
  name              = "monthly-cost-ceiling-10usd"
  budget_type       = "COST"
  limit_amount      = "10"
  limit_unit        = "USD"
  time_unit         = "MONTHLY"

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = ["devops-alerts@example.com"]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = ["devops-alerts@example.com"]
  }
}
```

---

## 2. Structural Cost Reductions

1. **API Gateway HTTP API v2 vs REST API**:
   - HTTP API v2 charges \$1.00 per million vs \$3.50 per million for REST API. **Savings: 71%**.
2. **DynamoDB On-Demand vs Provisioned**:
   - Provisioned tables incur minimum \$0.59/WCU and \$0.12/RCU monthly even when idle. On-demand costs **\$0.00** during idle periods.
3. **S3 Batching via SQS Windowing**:
   - SQS batching window of 5 seconds bundles up to 10 click events into a single S3 `PutObject` call. This cuts S3 API transaction costs by **up to 90%**.
4. **Log Retention Capping**:
   - All CloudWatch Log Groups are configured with `retention_in_days = 7` (dev) to eliminate perpetual log storage accumulation charges.
5. **Athena Query Result Expiration**:
   - S3 Lifecycle rules automatically purge temporary Athena query results in `s3://<bucket>/athena-results/` after 7 days.
