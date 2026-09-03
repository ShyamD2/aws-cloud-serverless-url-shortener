variable "environment" {
  description = "Deployment environment name"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-south-1"
}

variable "api_id" {
  description = "API Gateway ID"
  type        = string
}

variable "queue_name" {
  description = "Name of the SQS click queue"
  type        = string
}

variable "dynamodb_table_name" {
  description = "Name of the DynamoDB table"
  type        = string
}

variable "redirect_function_name" {
  description = "Name of the Redirect Lambda function"
  type        = string
}

variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default     = {}
}
