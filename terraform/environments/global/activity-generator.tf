# SQS Dead Letter Queue for failed activity generation
resource "aws_sqs_queue" "activity_generator_dlq" {
  name = "curriculum-activity-generator-dlq"
  
  # Retain failed messages for 14 days
  message_retention_seconds = 1209600
  
  tags = {
    Name        = "curriculum-activity-generator-dlq"
    Environment = "global"
    Project     = "curriculum-designer"
  }
}

# DynamoDB Table for Activity Storage
resource "aws_dynamodb_table" "curriculum_activities" {
  name         = "curriculum-activities"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "activity_id"

  attribute {
    name = "activity_id"
    type = "S"
  }

  attribute {
    name = "topic"
    type = "S"
  }

  attribute {
    name = "esl_level"
    type = "S"
  }

  attribute {
    name = "activity_type"
    type = "S"
  }

  global_secondary_index {
    name            = "topic-index"
    hash_key        = "topic"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "esl-level-index"
    hash_key        = "esl_level"
    range_key       = "topic"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "activity-type-index"
    hash_key        = "activity_type"
    range_key       = "topic"
    projection_type = "ALL"
  }

  # TTL attribute for automatic cleanup (e.g., remove activities after 1 year)
  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  # Enable point-in-time recovery for data protection
  point_in_time_recovery {
    enabled = true
  }

  tags = {
    Name        = "curriculum-activities"
    Environment = "global"
    Project     = "curriculum-designer"
  }
}

# Lambda Function for Activity Generation
resource "aws_lambda_function" "activity_generator" {
  filename      = "${path.module}/../../../lambda-deployments/activity-generator/deployment.zip"
  function_name = "curriculum-activity-generator"
  role         = aws_iam_role.activity_generator_role.arn
  handler      = "lambda_function.handler"
  runtime      = "python3.11"
  timeout      = 90  # Allow more time for complex activities
  memory_size  = 1024  # Increased memory for better performance with AI prompts

  layers = [
    data.aws_lambda_layer_version.httpx_dependencies.arn
  ]

  # Enable tracing for performance monitoring
  tracing_config {
    mode = "Active"
  }

  # Dead letter queue for failed invocations
  dead_letter_config {
    target_arn = aws_sqs_queue.activity_generator_dlq.arn
  }

  # Reserved concurrency to prevent cost overrun
  reserved_concurrency = 5

  environment {
    variables = {
      TABLE_NAME      = aws_dynamodb_table.curriculum_activities.name
      ANTHROPIC_API_KEY_PARAM = "/curriculum-designer/anthropic-api-key"
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.activity_generator_basic,
    aws_iam_role_policy.activity_generator_policy
  ]

  tags = {
    Name        = "curriculum-activity-generator"
    Environment = "global"
    Project     = "curriculum-designer"
  }
}

# IAM Role for Activity Generator Lambda
resource "aws_iam_role" "activity_generator_role" {
  name = "curriculum-activity-generator-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# IAM Policy for Activity Generator Lambda
resource "aws_iam_role_policy" "activity_generator_policy" {
  name = "activity-generator-policy"
  role = aws_iam_role.activity_generator_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:UpdateItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          aws_dynamodb_table.curriculum_activities.arn,
          "${aws_dynamodb_table.curriculum_activities.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters"
        ]
        Resource = [
          "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter/curriculum-designer/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "xray:PutTraceSegments",
          "xray:PutTelemetryRecords"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage"
        ]
        Resource = aws_sqs_queue.activity_generator_dlq.arn
      }
    ]
  })
}

# Attach basic Lambda execution role
resource "aws_iam_role_policy_attachment" "activity_generator_basic" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.activity_generator_role.name
}

# Lambda permission for webhook handler to invoke activity generator
resource "aws_lambda_permission" "allow_webhook_invoke_activity" {
  statement_id  = "AllowWebhookInvokeActivity"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.activity_generator.function_name
  principal     = "lambda.amazonaws.com"
  source_arn    = "arn:aws:lambda:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:function:curriculum-designer-webhook-dev"
}

# Grant permission for the webhook handler Lambda to invoke this function
# The webhook handler's role is created by the multi-env Terraform
# So we'll use a data source to reference it and attach a policy
data "aws_iam_role" "webhook_lambda_role" {
  name = "curriculum-designer-webhook-lambda-dev"
}

# Policy attachment for webhook to invoke activity generator
resource "aws_iam_role_policy" "webhook_invoke_activity" {
  name = "webhook-invoke-activity-policy"
  role = data.aws_iam_role.webhook_lambda_role.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = aws_lambda_function.activity_generator.arn
      }
    ]
  })
}

# Data sources for existing resources
data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

# Reference to existing HTTPX dependencies layer (latest version)
data "aws_lambda_layer_version" "httpx_dependencies" {
  layer_name = "curriculum-httpx-dependencies"
}

# Output the Lambda function details
output "activity_generator_function_name" {
  value = aws_lambda_function.activity_generator.function_name
}

output "activity_generator_function_arn" {
  value = aws_lambda_function.activity_generator.arn
}

output "activities_table_name" {
  value = aws_dynamodb_table.curriculum_activities.name
}

# CloudWatch Alarms for monitoring
resource "aws_cloudwatch_metric_alarm" "activity_generator_errors" {
  alarm_name          = "curriculum-activity-generator-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "60"
  statistic           = "Sum"
  threshold           = "5"
  alarm_description   = "This metric monitors activity generator errors"
  alarm_actions       = []  # Add SNS topic ARN for notifications if needed

  dimensions = {
    FunctionName = aws_lambda_function.activity_generator.function_name
  }

  tags = {
    Name        = "curriculum-activity-generator-errors"
    Environment = "global"
    Project     = "curriculum-designer"
  }
}

resource "aws_cloudwatch_metric_alarm" "activity_generator_duration" {
  alarm_name          = "curriculum-activity-generator-duration"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = "60"
  statistic           = "Average"
  threshold           = "75000"  # 75 seconds (close to timeout)
  alarm_description   = "This metric monitors activity generator duration"
  alarm_actions       = []

  dimensions = {
    FunctionName = aws_lambda_function.activity_generator.function_name
  }

  tags = {
    Name        = "curriculum-activity-generator-duration"
    Environment = "global"
    Project     = "curriculum-designer"
  }
}