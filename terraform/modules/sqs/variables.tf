variable "queue_name" {
  description = "Base name for the SQS queue"
  type        = string
}

variable "visibility_timeout_seconds" {
  description = "Visibility timeout in seconds (should be >= 6x Lambda timeout)"
  type        = number
  default     = 30
}

variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default     = {}
}
