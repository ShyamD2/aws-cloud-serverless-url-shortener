# Disaster Recovery & Infrastructure Recreation Plan

## 1. Disaster Recovery Objectives

| Metric | Target Objective | Strategy |
| :--- | :---: | :--- |
| **RTO (Recovery Time Objective)** | **< 15 minutes** | Full automated infrastructure recreation from cold source code using Terraform. |
| **RPO (Recovery Point Objective)** | **< 1 hour** | DynamoDB on-demand daily backups; S3 versioned analytics data. |

---

## 2. Infrastructure as Code Cold Rebuild Procedure

Because 100% of the platform architecture is codified in Terraform, the entire fleet can be re-provisioned from scratch in any supported AWS region in under 15 minutes.

### Step 1: Re-authenticate to AWS
```bash
aws sts get-caller-identity
```

### Step 2: Initialize & Apply Terraform Configuration
```bash
cd terraform/environments/dev

# 1. Initialize modules and remote backend
terraform init

# 2. Review recreation execution plan
terraform plan -out=dr-plan.tfplan

# 3. Apply infrastructure
terraform apply dr-plan.tfplan
```

### Step 3: Deploy Frontend Assets to S3
```bash
FRONTEND_BUCKET=$(terraform output -raw frontend_bucket)
aws s3 sync ../../../frontend/ s3://$FRONTEND_BUCKET/ --delete
```

### Step 4: Validate Health via Smoke Tests
```bash
API_URL=$(terraform output -raw api_endpoint)
export API_BASE_URL=$API_URL
../../../scripts/validate.sh
```

---

## 3. Data Restoration Runbooks

### 3.1 DynamoDB On-Demand Table Restoration
To restore a point-in-time snapshot to the active table:
```bash
# List available backups
aws dynamodb list-backups --table-name dev-urls

# Restore snapshot into new table
aws dynamodb restore-table-from-backup \
  --target-table-name dev-urls-restored \
  --backup-arn <backup-arn>
```

### 3.2 Analytics S3 Bucket Recovery
The Analytics bucket utilizes S3 versioning and lifecycle policies. Accidentally deleted or corrupted partitions can be recovered by removing Delete Markers:
```bash
aws s3api list-object-versions \
  --bucket dev-url-analytics-197550036081 \
  --prefix clicks/
```
