#!/usr/bin/env bash
# ==============================================================================
# Teardown / Cleanup Script (Protected with confirmation)
# ==============================================================================

set -euo pipefail

ENV_DIR="terraform/environments/dev"

echo "WARNING: This script will DESTROY all resources managed by Terraform in dev."
read -p "Type 'destroy-dev-environment' to proceed: " -r CONFIRM

if [[ "$CONFIRM" == "destroy-dev-environment" ]]; then
  echo "Emptying S3 buckets before teardown..."
  FRONTEND_BUCKET=$(terraform -chdir="$ENV_DIR" output -raw frontend_bucket 2>/dev/null || true)
  ANALYTICS_BUCKET=$(terraform -chdir="$ENV_DIR" output -raw analytics_bucket 2>/dev/null || true)

  if [[ -n "$FRONTEND_BUCKET" ]]; then
    aws s3 rm "s3://$FRONTEND_BUCKET" --recursive || true
  fi

  if [[ -n "$ANALYTICS_BUCKET" ]]; then
    aws s3 rm "s3://$ANALYTICS_BUCKET" --recursive || true
  fi

  echo "Executing terraform destroy..."
  terraform -chdir="$ENV_DIR" destroy -auto-approve
  echo "Cleanup complete."
else
  echo "Cleanup cancelled."
  exit 0
fi
