output "state_bucket_name" {
  description = "Name of the S3 state bucket"
  value       = aws_s3_bucket.terraform_state.id
}

output "state_bucket_arn" {
  description = "ARN of the S3 state bucket"
  value       = aws_s3_bucket.terraform_state.arn
}

output "lock_table_name" {
  description = "Name of the DynamoDB lock table"
  value       = aws_dynamodb_table.terraform_locks.name
}

output "lock_table_arn" {
  description = "ARN of the DynamoDB lock table"
  value       = aws_dynamodb_table.terraform_locks.arn
}
