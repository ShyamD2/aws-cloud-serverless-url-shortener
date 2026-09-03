variable "environment" {
  description = "Deployment environment name (e.g. dev, prod)"
  type        = string
}

variable "dynamodb_table_arn" {
  description = "ARN of the DynamoDB URLs table"
  type        = string
}

variable "sqs_queue_arn" {
  description = "ARN of the SQS click events queue"
  type        = string
}

variable "analytics_bucket_arn" {
  description = "ARN of the S3 analytics bucket"
  type        = string
}

variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default     = {}
}
