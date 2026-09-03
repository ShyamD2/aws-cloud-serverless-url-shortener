# Deployment Pipeline & Release Guide

## 1. Overview & CI/CD Strategy

The platform utilizes GitHub Actions for continuous integration and automated deployment with zero permanent AWS access keys.

```
Push to branch ──> CI (Lint, Test, TF Validate, Checkov)
                         │
Pull Request ────────────┴──> Terraform Plan (OIDC)
                         │
Merge to main ───────────┴──> Pre-Deploy Tests
                                   │
                              Manual Approval Gate (dev/prod)
                                   │
                              Terraform Apply
                                   │
                              Post-Deploy Smoke Tests (scripts/validate.sh)
                                   ├── Success: Deployment Complete
                                   └── Failure: Alert & Halt (Rollback Triggered)
```

---

## 2. GitHub Actions OIDC Authentication

Instead of storing long-lived `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` in GitHub repository secrets, the pipeline assumes an IAM role via OpenID Connect (OIDC).

### Trust Relationship Policy for `github-actions-deploy`
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::197550036081:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:<your-org>/url-shortener-cloud:*"
        }
      }
    }
  ]
}
```

---

## 3. Rollback Strategy on Smoke-Test Failure

If the post-deployment smoke test fails:
1. **Immediate Pipeline Halt**: The workflow terminates with code 1, marking the release failed and sending notifications.
2. **Standard Git Revert**:
   ```bash
   git revert HEAD
   git push origin main
   ```
   This immediately re-triggers the deployment pipeline with the last known stable state.
3. **Emergency Lambda Rollback (Sub-minute)**:
   If code needs immediate recovery without waiting for a full pipeline run:
   ```bash
   aws lambda update-function-code \
     --function-name dev-redirect \
     --s3-bucket <backup-bucket> \
     --s3-key builds/stable-lambda-package.zip \
     --region ap-south-1
   ```
