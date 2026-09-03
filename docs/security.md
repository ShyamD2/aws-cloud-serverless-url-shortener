# DevSecOps & Security Baseline

## 1. Security Architecture & Threat Model

The platform enforces **Defense-in-Depth** and **Least Privilege** across the edge, API, compute, storage, and CI/CD layers.

---

## 2. Least-Privilege IAM Model

Every Lambda function and deployment pipeline is bound to an isolated, purpose-built IAM role. **No component uses `AdministratorAccess` or wildcard full-service actions.**

| Component / Function | IAM Role Name | Allowed AWS Actions | Target Resource Scope |
| :--- | :--- | :--- | :--- |
| **Create URL Lambda** | `dev-create-url-lambda-role` | `dynamodb:PutItem`, `logs:PutLogEvents` | Specific Table: `arn:aws:dynamodb:ap-south-1:197550036081:table/dev-urls` |
| **Redirect Lambda** | `dev-redirect-lambda-role` | `dynamodb:GetItem`, `sqs:SendMessage`, `logs:PutLogEvents` | Table: `dev-urls`, Queue: `dev-click-events` |
| **Delete URL Lambda** | `dev-delete-url-lambda-role` | `dynamodb:UpdateItem`, `dynamodb:DeleteItem`, `logs:PutLogEvents` | Table: `dev-urls` |
| **Analytics Processor**| `dev-analytics-lambda-role` | `sqs:ReceiveMessage`, `sqs:DeleteMessage`, `s3:PutObject` | Queue: `dev-click-events`, S3: `arn:aws:s3:::dev-url-analytics-*/*` |
| **CI/CD Deployer** | `github-actions-deploy-role` | Scoped STS AssumeRole via GitHub OIDC federation | Only allows updating designated dev resources |

---

## 3. Data Protection (At Rest & In Transit)

### 3.1 Encryption at Rest
- **DynamoDB**: Encrypted at rest using AWS KMS managed customer master key (`aws/dynamodb`).
- **Amazon S3 (Analytics & Frontend)**: Default server-side encryption enabled with AES-256 (`aws:s3`). Public access blocked at the bucket and account level (`aws_s3_bucket_public_access_block`).
- **Amazon SQS & DLQ**: SQS-managed server-side encryption (`sqs_managed_sse_enabled = true`).

### 3.2 Encryption in Transit
- **CloudFront**: Enforces HTTPS (`viewer_protocol_policy = "redirect-to-https"`) with modern TLS 1.2/1.3 ciphers.
- **API Gateway (HTTP API v2)**: Rejects unencrypted HTTP; all requests terminate over HTTPS TLS.
- **Internal AWS SDK Calls**: Boto3 client communication with DynamoDB, SQS, and S3 executes over AWS SigV4 signed TLS 1.3 endpoints.

---

## 4. Application-Level Security Controls

1. **Input Sanitization & Validation**:
   - URL length strictly capped at 2,048 characters to prevent buffer and memory bloat.
   - Strictly restricted to `http://` and `https://` schemes (blocks `javascript:`, `data:`, `file:`, `ftp:` exploits).
   - Domain loop check blocks attempts to shorten links pointing back to the shortener host.
   - Custom aliases validated with strict regex: `^[a-zA-Z0-9_-]{3,30}$`.
2. **API Throttling & DDoS Protection**:
   - API Gateway throttles requests with a burst limit of 50 and steady-state limit of 100 req/sec, protecting downstream Lambdas and preventing bill spikes.
3. **Zero Secrets in Source Code**:
   - Zero API keys, passwords, or hard-coded credentials exist in any repository file.
   - CI/CD uses GitHub Actions OpenID Connect (OIDC) rather than permanent AWS Access Keys.
