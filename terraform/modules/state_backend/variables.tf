variable "bucket_name" {
  description = "Globally unique name for the Terraform state S3 bucket"
  type        = string
}

variable "lock_table_name" {
  description = "Name for the DynamoDB state lock table"
  type        = string
  default     = "terraform-locks"
}

variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default     = {}
}
