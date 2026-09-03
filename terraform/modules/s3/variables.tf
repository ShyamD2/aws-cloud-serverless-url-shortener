variable "analytics_bucket_name" {
  description = "Name of the analytics S3 bucket"
  type        = string
}

variable "frontend_bucket_name" {
  description = "Name of the frontend S3 bucket"
  type        = string
}

variable "force_destroy" {
  description = "Whether to allow bucket deletion even if non-empty (useful in dev)"
  type        = bool
  default     = false
}

variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default     = {}
}
