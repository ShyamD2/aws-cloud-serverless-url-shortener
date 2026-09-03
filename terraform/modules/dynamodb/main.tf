# ==============================================================================
# DynamoDB URLs Table Module
# ==============================================================================

resource "aws_dynamodb_table" "urls" {
  name         = var.table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "short_code"

  attribute {
    name = "short_code"
    type = "S"
  }

  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  server_side_encryption {
    enabled = true
  }

  point_in_time_recovery {
    enabled = var.enable_pitr
  }

  tags = merge(var.tags, {
    Name        = var.table_name
    Description = "Primary short URL registry table with TTL"
  })
}
