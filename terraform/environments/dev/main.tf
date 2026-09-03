# ==============================================================================
# Root Infrastructure Composition: Dev Environment
# ==============================================================================

data "aws_caller_identity" "current" {}

# --- 1. Terraform Remote State Storage Bootstrap ---
module "state_backend" {
  source          = "../../modules/state_backend"
  bucket_name     = "${var.environment}-tfstate-${data.aws_caller_identity.current.account_id}"
  lock_table_name = "${var.environment}-tfstate-locks"
}

# --- 2. DynamoDB URLs Table ---
module "dynamodb" {
  source      = "../../modules/dynamodb"
  table_name  = "${var.environment}-urls"
  enable_pitr = false
}

# --- 3. SQS Telemetry Queue & DLQ ---
module "sqs" {
  source                     = "../../modules/sqs"
  queue_name                 = "${var.environment}-click-events"
  visibility_timeout_seconds = 30
}

# --- 4. S3 Storage Buckets ---
module "s3" {
  source                = "../../modules/s3"
  analytics_bucket_name = "${var.environment}-url-analytics-${data.aws_caller_identity.current.account_id}"
  frontend_bucket_name  = "${var.environment}-url-frontend-${data.aws_caller_identity.current.account_id}"
  force_destroy         = true
}

# --- 5. IAM Least-Privilege Roles ---
module "iam" {
  source               = "../../modules/iam"
  environment          = var.environment
  dynamodb_table_arn   = module.dynamodb.table_arn
  sqs_queue_arn        = module.sqs.queue_arn
  analytics_bucket_arn = module.s3.analytics_bucket_arn
}

# --- 6. AWS Lambda Functions ---
module "lambda" {
  source                = "../../modules/lambda"
  environment           = var.environment
  source_code_path      = "${path.module}/../../../application"
  urls_table_name       = module.dynamodb.table_name
  sqs_queue_url         = module.sqs.queue_url
  sqs_queue_arn         = module.sqs.queue_arn
  analytics_bucket_name = module.s3.analytics_bucket_id
  base_url              = var.base_url

  create_url_role_arn = module.iam.create_url_role_arn
  redirect_role_arn   = module.iam.redirect_role_arn
  delete_url_role_arn = module.iam.delete_url_role_arn
  analytics_role_arn  = module.iam.analytics_role_arn
}

# --- 7. API Gateway (HTTP API v2) ---
module "api_gateway" {
  source                   = "../../modules/api_gateway"
  environment              = var.environment
  create_url_function_name = module.lambda.create_url_function_name
  create_url_function_arn  = module.lambda.create_url_function_arn
  redirect_function_name   = module.lambda.redirect_function_name
  redirect_function_arn    = module.lambda.redirect_function_arn
  delete_url_function_name = module.lambda.delete_url_function_name
  delete_url_function_arn  = module.lambda.delete_url_function_arn
}

# --- 8. CloudFront Edge CDN ---
module "cloudfront" {
  source                               = "../../modules/cloudfront"
  environment                          = var.environment
  frontend_bucket_id                   = module.s3.frontend_bucket_id
  frontend_bucket_arn                  = module.s3.frontend_bucket_arn
  frontend_bucket_regional_domain_name = module.s3.frontend_bucket_regional_domain_name
}

# --- 9. CloudWatch Monitoring & Dashboard ---
module "cloudwatch" {
  source                 = "../../modules/cloudwatch"
  environment            = var.environment
  aws_region             = var.aws_region
  api_id                 = module.api_gateway.api_id
  queue_name             = "${var.environment}-click-events"
  dynamodb_table_name    = module.dynamodb.table_name
  redirect_function_name = module.lambda.redirect_function_name
}
