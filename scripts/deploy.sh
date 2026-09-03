#!/usr/bin/env bash
# ==============================================================================
# Terraform Infrastructure Deployment Script
# ==============================================================================

set -euo pipefail

ENV_DIR="terraform/environments/dev"

echo "=== 1. Validating AWS Authentication ==="
aws sts get-caller-identity

echo "=== 2. Initializing Terraform ==="
terraform -chdir="$ENV_DIR" init

echo "=== 3. Planning Infrastructure Changes ==="
terraform -chdir="$ENV_DIR" plan -out=tfplan

echo "=== 4. Applying Plan ==="
read -p "Apply this plan to AWS? (y/N): " -r CONFIRM
if [[ "$CONFIRM" =~ ^[Yy]$ ]]; then
  terraform -chdir="$ENV_DIR" apply tfplan
  
  echo "=== 5. Syncing Frontend to S3 ==="
  FRONTEND_BUCKET=$(terraform -chdir="$ENV_DIR" output -raw frontend_bucket)
  aws s3 sync frontend/ "s3://$FRONTEND_BUCKET/" --delete
  
  echo "=== Deployment Completed Successfully ==="
else
  echo "Deployment aborted."
  exit 0
fi
