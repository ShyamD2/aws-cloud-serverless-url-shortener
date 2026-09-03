provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "ServerlessURLShortener"
      Environment = var.environment
      ManagedBy   = "Terraform"
      Owner       = "DevOpsTeam"
    }
  }
}
