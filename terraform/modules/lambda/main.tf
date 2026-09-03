# ==============================================================================
# Lambda Functions Module
# ==============================================================================

# Package the application source code into a deployable zip artifact
data "archive_file" "lambda_package" {
  type        = "zip"
  source_dir  = var.source_code_path
  output_path = "${path.module}/builds/lambda_package.zip"
  excludes    = ["tests", "__pycache__", ".pytest_cache", "venv", ".venv", "*.pyc"]
}

# --- 1. Create URL Function ---
resource "aws_lambda_function" "create_url" {
  function_name    = "${var.environment}-create-url"
  role             = var.create_url_role_arn
  runtime          = "python3.13"
  handler          = "src.handlers.create_url.lambda_handler"
  filename         = data.archive_file.lambda_package.output_path
  source_code_hash = data.archive_file.lambda_package.output_base64sha256
  timeout          = 5
  memory_size      = 256

  environment {
    variables = {
      URLS_TABLE_NAME = var.urls_table_name
      BASE_URL        = var.base_url
    }
  }

  tags = merge(var.tags, {
    Name = "${var.environment}-create-url"
  })
}

# --- 2. Redirect Function ---
resource "aws_lambda_function" "redirect" {
  function_name    = "${var.environment}-redirect"
  role             = var.redirect_role_arn
  runtime          = "python3.13"
  handler          = "src.handlers.redirect.lambda_handler"
  filename         = data.archive_file.lambda_package.output_path
  source_code_hash = data.archive_file.lambda_package.output_base64sha256
  timeout          = 5
  memory_size      = 256

  environment {
    variables = {
      URLS_TABLE_NAME        = var.urls_table_name
      CLICK_EVENTS_QUEUE_URL = var.sqs_queue_url
    }
  }

  tags = merge(var.tags, {
    Name = "${var.environment}-redirect"
  })
}

# --- 3. Delete URL Function ---
resource "aws_lambda_function" "delete_url" {
  function_name    = "${var.environment}-delete-url"
  role             = var.delete_url_role_arn
  runtime          = "python3.13"
  handler          = "src.handlers.delete_url.lambda_handler"
  filename         = data.archive_file.lambda_package.output_path
  source_code_hash = data.archive_file.lambda_package.output_base64sha256
  timeout          = 5
  memory_size      = 256

  environment {
    variables = {
      URLS_TABLE_NAME = var.urls_table_name
    }
  }

  tags = merge(var.tags, {
    Name = "${var.environment}-delete-url"
  })
}

# --- 4. Analytics Processor Function ---
resource "aws_lambda_function" "analytics" {
  function_name    = "${var.environment}-analytics-processor"
  role             = var.analytics_role_arn
  runtime          = "python3.13"
  handler          = "src.handlers.analytics.lambda_handler"
  filename         = data.archive_file.lambda_package.output_path
  source_code_hash = data.archive_file.lambda_package.output_base64sha256
  timeout          = 10
  memory_size      = 256

  environment {
    variables = {
      ANALYTICS_BUCKET_NAME = var.analytics_bucket_name
    }
  }

  tags = merge(var.tags, {
    Name = "${var.environment}-analytics-processor"
  })
}

# SQS Trigger for Analytics Processor
resource "aws_lambda_event_source_mapping" "sqs_to_analytics" {
  event_source_arn                   = var.sqs_queue_arn
  function_name                      = aws_lambda_function.analytics.arn
  batch_size                         = 10
  maximum_batching_window_in_seconds = 5
  enabled                            = true
}
