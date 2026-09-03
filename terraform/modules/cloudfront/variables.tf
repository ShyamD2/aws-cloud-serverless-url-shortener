variable "environment" {
  description = "Deployment environment name"
  type        = string
}

variable "frontend_bucket_id" {
  description = "ID/Name of the frontend S3 bucket"
  type        = string
}

variable "frontend_bucket_arn" {
  description = "ARN of the frontend S3 bucket"
  type        = string
}

variable "frontend_bucket_regional_domain_name" {
  description = "Regional domain name of the frontend S3 bucket"
  type        = string
}

variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default     = {}
}
