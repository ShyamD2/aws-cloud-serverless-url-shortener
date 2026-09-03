variable "table_name" {
  description = "Name of the DynamoDB URLs table"
  type        = string
}

variable "enable_pitr" {
  description = "Enable Point-in-Time Recovery (recommend false in dev to minimize cost)"
  type        = bool
  default     = false
}

variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default     = {}
}
