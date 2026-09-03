# Security Guidelines & Checkov Scan Instructions

## 1. Static Code Analysis with Checkov

To audit Terraform configuration for security compliance:

```bash
# Run Checkov against Terraform code
checkov -d terraform/ --framework terraform
```

Key controls validated:
- `CKV_AWS_18`: Ensure S3 access logging or public access block is enabled.
- `CKV_AWS_19`: Ensure S3 buckets enforce encryption at rest.
- `CKV_AWS_27`: Ensure SQS queues have server-side encryption enabled.
- `CKV_AWS_119`: Ensure DynamoDB point-in-time recovery is evaluated.
- `CKV_AWS_116`: Ensure AWS Lambda functions have Dead Letter Queue / error handling configured.

---

## 2. Dependency Vulnerability Auditing

```bash
# Python dependency check
pip install pip-audit
pip-audit -r application/requirements.txt
```
