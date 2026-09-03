# ==============================================================================
# Terraform Remote State Backend Module (S3 Bucket + DynamoDB Lock Table)
# ==============================================================================

resource "aws_s3_bucket" "terraform_state" {
  bucket        = var.bucket_name
  force_destroy = false

  tags = merge(var.tags, {
    Name        = var.bucket_name
    Description = "Encrypted S3 bucket for Terraform remote state storage"
  })
}

resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    id     = "expire-old-state-versions"
    status = "Enabled"

    filter {}

    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }
}

resource "aws_dynamodb_table" "terraform_locks" {
  name         = var.lock_table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  point_in_time_recovery {
    enabled = false
  }

  server_side_encryption {
    enabled = true
  }

  tags = merge(var.tags, {
    Name        = var.lock_table_name
    Description = "DynamoDB lock table for Terraform state concurrency control"
  })
}
