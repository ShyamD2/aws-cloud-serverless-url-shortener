# ==============================================================================
# IAM Module: Least-Privilege Execution Roles for Lambda Functions
# ==============================================================================

data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    effect  = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

# --- 1. Create URL Lambda Role ---
resource "aws_iam_role" "create_url" {
  name               = "${var.environment}-create-url-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
  tags               = var.tags
}

resource "aws_iam_policy" "create_url" {
  name        = "${var.environment}-create-url-policy"
  description = "Least privilege policy for Create URL Lambda"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "CloudWatchLogging"
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:log-group:/aws/lambda/${var.environment}-*"
      },
      {
        Sid    = "DynamoDBPutItem"
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem"
        ]
        Resource = var.dynamodb_table_arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "create_url" {
  role       = aws_iam_role.create_url.name
  policy_arn = aws_iam_policy.create_url.arn
}

# --- 2. Redirect Lambda Role ---
resource "aws_iam_role" "redirect" {
  name               = "${var.environment}-redirect-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
  tags               = var.tags
}

resource "aws_iam_policy" "redirect" {
  name        = "${var.environment}-redirect-policy"
  description = "Least privilege policy for Redirect Lambda"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "CloudWatchLogging"
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:log-group:/aws/lambda/${var.environment}-*"
      },
      {
        Sid    = "DynamoDBGetItem"
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem"
        ]
        Resource = var.dynamodb_table_arn
      },
      {
        Sid    = "SQSSendTelemetry"
        Effect = "Allow"
        Action = [
          "sqs:SendMessage"
        ]
        Resource = var.sqs_queue_arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "redirect" {
  role       = aws_iam_role.redirect.name
  policy_arn = aws_iam_policy.redirect.arn
}

# --- 3. Delete URL Lambda Role ---
resource "aws_iam_role" "delete_url" {
  name               = "${var.environment}-delete-url-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
  tags               = var.tags
}

resource "aws_iam_policy" "delete_url" {
  name        = "${var.environment}-delete-url-policy"
  description = "Least privilege policy for Delete URL Lambda"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "CloudWatchLogging"
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:log-group:/aws/lambda/${var.environment}-*"
      },
      {
        Sid    = "DynamoDBUpdateItem"
        Effect = "Allow"
        Action = [
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem"
        ]
        Resource = var.dynamodb_table_arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "delete_url" {
  role       = aws_iam_role.delete_url.name
  policy_arn = aws_iam_policy.delete_url.arn
}

# --- 4. Analytics Processor Lambda Role ---
resource "aws_iam_role" "analytics" {
  name               = "${var.environment}-analytics-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
  tags               = var.tags
}

resource "aws_iam_policy" "analytics" {
  name        = "${var.environment}-analytics-policy"
  description = "Least privilege policy for Analytics Processor Lambda"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "CloudWatchLogging"
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:log-group:/aws/lambda/${var.environment}-*"
      },
      {
        Sid    = "SQSConsumeMessages"
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = var.sqs_queue_arn
      },
      {
        Sid    = "S3PutAnalyticsObjects"
        Effect = "Allow"
        Action = [
          "s3:PutObject"
        ]
        Resource = "${var.analytics_bucket_arn}/*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "analytics" {
  role       = aws_iam_role.analytics.name
  policy_arn = aws_iam_policy.analytics.arn
}
