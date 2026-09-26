variable "environment" {
  description = "Deployment environment name (e.g. dev, prod)"
  type        = string
}

variable "sqs_queue_arn" {
  description = "ARN of the SQS click events queue to subscribe to the SNS topic"
  type        = string
}

variable "sqs_queue_url" {
  description = "URL of the SQS click events queue to attach subscription policy"
  type        = string
}

variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default     = {}
}
