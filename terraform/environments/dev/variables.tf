variable "environment" {
  description = "Deployment environment name"
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "AWS deployment region (pinned from PROJECT_ENVIRONMENT.md)"
  type        = string
  default     = "ap-south-1"
}

variable "base_url" {
  description = "Optional base URL override for short URLs (defaults to API Gateway or CloudFront endpoint)"
  type        = string
  default     = ""
}
