# ==============================================================================
# S3 Storage Module (Analytics Data Bucket + Frontend Static Hosting Bucket)
# ==============================================================================

# --- Analytics Bucket ---
resource "aws_s3_bucket" "analytics" {
  bucket        = var.analytics_bucket_name
  force_destroy = var.force_destroy

  tags = merge(var.tags, {
    Name        = var.analytics_bucket_name
    Description = "Storage for partitioned JSONL click analytics data"
  })
}

resource "aws_s3_bucket_server_side_encryption_configuration" "analytics" {
  bucket = aws_s3_bucket.analytics.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "analytics" {
  bucket = aws_s3_bucket.analytics.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "analytics" {
  bucket = aws_s3_bucket.analytics.id

  # Transition raw click logs to Standard-IA after 30 days to save cost
  rule {
    id     = "transition-old-logs-to-ia"
    status = "Enabled"

    filter {
      prefix = "clicks/"
    }

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }
  }

  # Expire Athena temporary query results after 7 days
  rule {
    id     = "expire-athena-results"
    status = "Enabled"

    filter {
      prefix = "athena-results/"
    }

    expiration {
      days = 7
    }
  }
}

# --- Frontend Website Static Bucket ---
resource "aws_s3_bucket" "frontend" {
  bucket        = var.frontend_bucket_name
  force_destroy = var.force_destroy

  tags = merge(var.tags, {
    Name        = var.frontend_bucket_name
    Description = "Static hosting origin for CloudFront distribution"
  })
}

resource "aws_s3_bucket_server_side_encryption_configuration" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
