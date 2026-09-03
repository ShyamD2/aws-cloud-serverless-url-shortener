variable "environment" {
  description = "Deployment environment name"
  type        = string
}

variable "create_url_function_name" {
  description = "Name of the Create URL Lambda function"
  type        = string
}

variable "create_url_function_arn" {
  description = "ARN of the Create URL Lambda function"
  type        = string
}

variable "redirect_function_name" {
  description = "Name of the Redirect Lambda function"
  type        = string
}

variable "redirect_function_arn" {
  description = "ARN of the Redirect Lambda function"
  type        = string
}

variable "delete_url_function_name" {
  description = "Name of the Delete URL Lambda function"
  type        = string
}

variable "delete_url_function_arn" {
  description = "ARN of the Delete URL Lambda function"
  type        = string
}

variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default     = {}
}
