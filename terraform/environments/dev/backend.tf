# ==============================================================================
# Terraform Remote State Backend (S3 + DynamoDB Lock)
# ==============================================================================

terraform {
  backend "s3" {
    bucket         = "dev-tfstate-197550036081"
    key            = "dev/terraform.tfstate"
    region         = "ap-south-1"
    dynamodb_table = "dev-tfstate-locks"
    encrypt        = true
  }
}
