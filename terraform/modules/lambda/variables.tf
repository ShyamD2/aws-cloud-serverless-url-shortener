variable "environment" {
  description = "Deployment environment name"
  type        = string
}

variable "source_code_path" {
  description = "Path to the application source directory"
  type        = string
}

variable "urls_table_name" {
  description = "Name of the DynamoDB URLs table"
  type        = string
}

variable "sqs_queue_url" {
  description = "URL of the SQS click events queue"
  type        = string
}

variable "sqs_queue_arn" {
  description = "ARN of the SQS click events queue"
  type        = string
}

variable "analytics_bucket_name" {
  description = "Name of the S3 analytics bucket"
  type        = string
}

variable "base_url" {
  description = "Base URL of the shortener platform"
  type        = string
  default     = ""
}

variable "create_url_role_arn" {
  description = "IAM role ARN for Create URL Lambda"
  type        = string
}

variable "redirect_role_arn" {
  description = "IAM role ARN for Redirect Lambda"
  type        = string
}

variable "delete_url_role_arn" {
  description = "IAM role ARN for Delete URL Lambda"
  type        = string
}

variable "analytics_role_arn" {
  description = "IAM role ARN for Analytics Lambda"
  type        = string
}

variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default     = {}
}
