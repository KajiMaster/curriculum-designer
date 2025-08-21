terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Keep only essential Parameter Store references
data "aws_ssm_parameter" "github_org" {
  name = "/global/curriculum-designer/github-org"
}

data "aws_ssm_parameter" "github_repo" {
  name = "/global/curriculum-designer/github-repo"
}

data "aws_ssm_parameter" "openai_api_key" {
  name = "/global/curriculum-designer/openai-api-key"
}

data "aws_ssm_parameter" "trello_api_key" {
  name = "/global/curriculum-designer/trello-api-key"
}

data "aws_ssm_parameter" "trello_token" {
  name = "/global/curriculum-designer/trello-token"
}

data "aws_ssm_parameter" "trello_webhook_secret" {
  name = "/global/curriculum-designer/trello-webhook-secret"
}

data "aws_ssm_parameter" "google_drive_api_key" {
  name = "/global/curriculum-designer/google-drive-api-key"
}

data "aws_ssm_parameter" "google_drive_folder_id" {
  name = "/global/curriculum-designer/google-drive-folder-id"
}

# Optional Canva parameters - check if they exist
data "aws_ssm_parameter" "canva_access_token" {
  count = 1
  name = "/global/curriculum-designer/canva-access-token"
}

# Reference Lambda layers from global infrastructure
data "aws_lambda_layer_version" "webhook_dependencies" {
  layer_name = "curriculum-designer-webhook-dependencies"
}

data "aws_lambda_layer_version" "mcp_dependencies" {
  layer_name = "curriculum-designer-mcp-dependencies"
}

# Reference GitHub Actions role from global state
data "terraform_remote_state" "global" {
  backend = "s3"
  config = {
    bucket = "terraform-state-curriculum-designer"
    key    = "global/terraform.tfstate"
    region = "us-east-1"
  }
}

# ============================================
# LAMBDA WEBHOOK HANDLER
# ============================================

# IAM role for Lambda
resource "aws_iam_role" "webhook_lambda_role" {
  name = "${var.project_name}-webhook-lambda-${var.environment}"

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

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# IAM policy for Lambda execution and Parameter Store access
resource "aws_iam_role_policy" "webhook_lambda_policy" {
  name = "${var.project_name}-webhook-lambda-policy-${var.environment}"
  role = aws_iam_role.webhook_lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream", 
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters"
        ]
        Resource = [
          "arn:aws:ssm:${var.aws_region}:*:parameter/global/${var.project_name}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          "arn:aws:dynamodb:${var.aws_region}:*:table/${var.project_name}-mcp-storage-${var.environment}",
          "arn:aws:dynamodb:${var.aws_region}:*:table/${var.project_name}-mcp-storage-${var.environment}/index/*",
          "arn:aws:dynamodb:${var.aws_region}:*:table/${var.project_name}-mcp-feedback-${var.environment}",
          "arn:aws:dynamodb:${var.aws_region}:*:table/${var.project_name}-mcp-feedback-${var.environment}/index/*"
        ]
      }
    ]
  })
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "webhook_lambda_logs" {
  name              = "/aws/lambda/${var.project_name}-webhook-${var.environment}"
  retention_in_days = 14

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# Lambda function (code will be deployed via CI/CD)
resource "aws_lambda_function" "webhook_handler" {
  function_name = "${var.project_name}-webhook-${var.environment}"
  role         = aws_iam_role.webhook_lambda_role.arn
  handler      = "lambda_main.handler"
  runtime      = "python3.11"
  timeout      = 30

  # Use Lambda layer for dependencies
  layers = [data.aws_lambda_layer_version.webhook_dependencies.arn]

  # Initial deployment with current working code (CI/CD will update)
  filename         = "${path.module}/../../../webhook-handler/lambda_package/placeholder.zip"
  source_code_hash = filebase64sha256("${path.module}/../../../webhook-handler/lambda_package/placeholder.zip")

  environment {
    variables = {
      ENVIRONMENT = var.environment
      TRELLO_API_KEY_PARAM = "/global/curriculum-designer/trello-api-key"
      TRELLO_TOKEN_PARAM = "/global/curriculum-designer/trello-token"
      OPENAI_API_KEY_PARAM = "/global/curriculum-designer/openai-api-key"
      TRELLO_WEBHOOK_SECRET_PARAM = "/global/curriculum-designer/trello-webhook-secret"
    }
  }

  depends_on = [
    aws_iam_role_policy.webhook_lambda_policy,
    aws_cloudwatch_log_group.webhook_lambda_logs,
  ]

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }
  
  # Allow CI/CD to update the function code
  lifecycle {
    ignore_changes = [
      filename,
      source_code_hash,
      last_modified
    ]
  }
}

# ============================================
# DYNAMODB TABLE FOR MCP STORAGE
# ============================================

# DynamoDB table for storing lesson plans and generated content
resource "aws_dynamodb_table" "mcp_storage" {
  name           = "${var.project_name}-mcp-storage-${var.environment}"
  billing_mode   = "PAY_PER_REQUEST"  # Serverless pricing
  hash_key       = "id"
  range_key      = "type"

  attribute {
    name = "id"
    type = "S"
  }

  attribute {
    name = "type"
    type = "S"
  }

  attribute {
    name = "created_at"
    type = "S"
  }

  # Global Secondary Index for querying by type and creation date
  global_secondary_index {
    name            = "type-created_at-index"
    hash_key        = "type"
    range_key       = "created_at"
    projection_type = "ALL"
  }

  # Point-in-time recovery for data protection
  point_in_time_recovery {
    enabled = true
  }

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
    Purpose     = "MCP lesson plan storage"
  }
}

# DynamoDB table for storing MCP feedback and training data
resource "aws_dynamodb_table" "mcp_feedback" {
  name           = "${var.project_name}-mcp-feedback-${var.environment}"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "feedback_id"
  range_key      = "created_at"

  attribute {
    name = "feedback_id"
    type = "S"
  }

  attribute {
    name = "created_at"
    type = "S"
  }

  attribute {
    name = "lesson_plan_id"
    type = "S"
  }

  attribute {
    name = "feedback_type"
    type = "S"
  }

  # GSI for querying by lesson plan
  global_secondary_index {
    name            = "lesson-plan-feedback-index"
    hash_key        = "lesson_plan_id"
    range_key       = "created_at"
    projection_type = "ALL"
  }

  # GSI for querying by feedback type
  global_secondary_index {
    name            = "feedback-type-index"
    hash_key        = "feedback_type"
    range_key       = "created_at"
    projection_type = "ALL"
  }

  # Point-in-time recovery
  point_in_time_recovery {
    enabled = true
  }

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
    Purpose     = "MCP feedback and training data"
  }
}

# ============================================
# MCP LAMBDA FUNCTION
# ============================================

# CloudWatch Log Group for MCP
resource "aws_cloudwatch_log_group" "mcp_lambda_logs" {
  name              = "/aws/lambda/${var.project_name}-mcp-${var.environment}"
  retention_in_days = 14

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# MCP Lambda function (code will be deployed via CI/CD)
resource "aws_lambda_function" "mcp_server" {
  function_name = "${var.project_name}-mcp-${var.environment}"
  role         = aws_iam_role.webhook_lambda_role.arn  # Reuse same role
  handler      = "lambda_handler.lambda_handler"
  runtime      = "python3.11"
  timeout      = 30

  # Use MCP Lambda layer for dependencies
  layers = [data.aws_lambda_layer_version.mcp_dependencies.arn]

  # Initial deployment with placeholder (CI/CD will update)
  filename         = "${path.module}/../../../mcp-server/mcp_deployment.zip"
  source_code_hash = fileexists("${path.module}/../../../mcp-server/mcp_deployment.zip") ? filebase64sha256("${path.module}/../../../mcp-server/mcp_deployment.zip") : null

  environment {
    variables = {
      ENVIRONMENT = var.environment
      TRELLO_API_KEY = data.aws_ssm_parameter.trello_api_key.value
      TRELLO_TOKEN = data.aws_ssm_parameter.trello_token.value
      TRELLO_BOARD_ID = "68a5fba51647caf78fc40866"
      TRELLO_LESSON_PLANS_BOARD_ID = "68a646dba9f202dbd275b7e8"
      TRELLO_ACTIVE_LIST_ID = "68a646f0094db25caba22dca"
      GOOGLE_DRIVE_API_KEY = data.aws_ssm_parameter.google_drive_api_key.value
      GOOGLE_DRIVE_FOLDER_ID = data.aws_ssm_parameter.google_drive_folder_id.value
      DYNAMODB_TABLE_NAME = aws_dynamodb_table.mcp_storage.name
      DYNAMODB_FEEDBACK_TABLE_NAME = aws_dynamodb_table.mcp_feedback.name
      CANVA_ACCESS_TOKEN = length(data.aws_ssm_parameter.canva_access_token) > 0 ? data.aws_ssm_parameter.canva_access_token[0].value : ""
    }
  }

  depends_on = [
    aws_iam_role_policy.webhook_lambda_policy,
    aws_cloudwatch_log_group.mcp_lambda_logs,
  ]

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }
  
  # Allow CI/CD to update the function code
  lifecycle {
    ignore_changes = [
      filename,
      source_code_hash
    ]
  }
}

# ============================================
# API GATEWAY
# ============================================

# API Gateway REST API
resource "aws_api_gateway_rest_api" "webhook_api" {
  name        = "${var.project_name}-webhook-${var.environment}"
  description = "Trello webhook API for ${var.environment} environment"
  
  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# API Gateway resource (catch-all proxy)
resource "aws_api_gateway_resource" "webhook_proxy" {
  rest_api_id = aws_api_gateway_rest_api.webhook_api.id
  parent_id   = aws_api_gateway_rest_api.webhook_api.root_resource_id
  path_part   = "{proxy+}"
}

# API Gateway method (ANY for proxy)
resource "aws_api_gateway_method" "webhook_proxy" {
  rest_api_id   = aws_api_gateway_rest_api.webhook_api.id
  resource_id   = aws_api_gateway_resource.webhook_proxy.id
  http_method   = "ANY"
  authorization = "NONE"
}

# API Gateway method (ANY for root)
resource "aws_api_gateway_method" "webhook_proxy_root" {
  rest_api_id   = aws_api_gateway_rest_api.webhook_api.id
  resource_id   = aws_api_gateway_rest_api.webhook_api.root_resource_id
  http_method   = "ANY"
  authorization = "NONE"
}

# API Gateway integration
resource "aws_api_gateway_integration" "webhook_lambda_integration" {
  rest_api_id = aws_api_gateway_rest_api.webhook_api.id
  resource_id = aws_api_gateway_method.webhook_proxy.resource_id
  http_method = aws_api_gateway_method.webhook_proxy.http_method

  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = aws_lambda_function.webhook_handler.invoke_arn
}

# API Gateway integration for root
resource "aws_api_gateway_integration" "webhook_lambda_integration_root" {
  rest_api_id = aws_api_gateway_rest_api.webhook_api.id
  resource_id = aws_api_gateway_method.webhook_proxy_root.resource_id
  http_method = aws_api_gateway_method.webhook_proxy_root.http_method

  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = aws_lambda_function.webhook_handler.invoke_arn
}

# API Gateway deployment
resource "aws_api_gateway_deployment" "webhook_deployment" {
  depends_on = [
    aws_api_gateway_integration.webhook_lambda_integration,
    aws_api_gateway_integration.webhook_lambda_integration_root,
  ]

  rest_api_id = aws_api_gateway_rest_api.webhook_api.id
  stage_name  = var.environment
}

# Lambda permission for API Gateway
resource "aws_lambda_permission" "webhook_api_gw_permission" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.webhook_handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.webhook_api.execution_arn}/*/*"
}

# ============================================
# MCP API GATEWAY
# ============================================

# API Gateway REST API for MCP
resource "aws_api_gateway_rest_api" "mcp_api" {
  name        = "${var.project_name}-mcp-${var.environment}"
  description = "MCP server API for ${var.environment} environment"
  
  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# API Gateway resource (catch-all proxy for MCP)
resource "aws_api_gateway_resource" "mcp_proxy" {
  rest_api_id = aws_api_gateway_rest_api.mcp_api.id
  parent_id   = aws_api_gateway_rest_api.mcp_api.root_resource_id
  path_part   = "{proxy+}"
}

# API Gateway method (ANY for MCP proxy)
resource "aws_api_gateway_method" "mcp_proxy" {
  rest_api_id   = aws_api_gateway_rest_api.mcp_api.id
  resource_id   = aws_api_gateway_resource.mcp_proxy.id
  http_method   = "ANY"
  authorization = "NONE"
}

# API Gateway method (ANY for MCP root)
resource "aws_api_gateway_method" "mcp_proxy_root" {
  rest_api_id   = aws_api_gateway_rest_api.mcp_api.id
  resource_id   = aws_api_gateway_rest_api.mcp_api.root_resource_id
  http_method   = "ANY"
  authorization = "NONE"
}

# API Gateway integration for MCP
resource "aws_api_gateway_integration" "mcp_lambda_integration" {
  rest_api_id = aws_api_gateway_rest_api.mcp_api.id
  resource_id = aws_api_gateway_method.mcp_proxy.resource_id
  http_method = aws_api_gateway_method.mcp_proxy.http_method

  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = aws_lambda_function.mcp_server.invoke_arn
}

# API Gateway integration for MCP root
resource "aws_api_gateway_integration" "mcp_lambda_integration_root" {
  rest_api_id = aws_api_gateway_rest_api.mcp_api.id
  resource_id = aws_api_gateway_method.mcp_proxy_root.resource_id
  http_method = aws_api_gateway_method.mcp_proxy_root.http_method

  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = aws_lambda_function.mcp_server.invoke_arn
}

# API Gateway deployment for MCP
resource "aws_api_gateway_deployment" "mcp_deployment" {
  depends_on = [
    aws_api_gateway_integration.mcp_lambda_integration,
    aws_api_gateway_integration.mcp_lambda_integration_root,
  ]

  rest_api_id = aws_api_gateway_rest_api.mcp_api.id
  stage_name  = var.environment
}

# Lambda permission for MCP API Gateway
resource "aws_lambda_permission" "mcp_api_gw_permission" {
  statement_id  = "AllowExecutionFromMCPAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.mcp_server.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.mcp_api.execution_arn}/*/*"
}

# Outputs
output "github_repo" {
  value = "${data.aws_ssm_parameter.github_org.value}/${data.aws_ssm_parameter.github_repo.value}"
  description = "GitHub repository"
  sensitive = true
}

output "openai_configured" {
  value = "OpenAI API key stored in Parameter Store"
  description = "AI integration ready"
}

output "webhook_api_url" {
  value = aws_api_gateway_deployment.webhook_deployment.invoke_url
  description = "Base URL for webhook API"
}

output "webhook_endpoint" {
  value = "${aws_api_gateway_deployment.webhook_deployment.invoke_url}/webhook"
  description = "Full webhook URL to register with Trello"
}

output "lambda_function_name" {
  value = aws_lambda_function.webhook_handler.function_name
  description = "Lambda function name for monitoring"
}

output "github_actions_role_arn" {
  value = data.terraform_remote_state.global.outputs.github_actions_role_arn
  description = "ARN of the GitHub Actions role for CI/CD"
}

output "mcp_api_url" {
  value = aws_api_gateway_deployment.mcp_deployment.invoke_url
  description = "Base URL for MCP API"
}

output "mcp_health_endpoint" {
  value = "${aws_api_gateway_deployment.mcp_deployment.invoke_url}/health"
  description = "MCP server health check endpoint"
}

output "mcp_function_name" {
  value = aws_lambda_function.mcp_server.function_name
  description = "MCP Lambda function name for monitoring"
}

output "dynamodb_table_name" {
  value = aws_dynamodb_table.mcp_storage.name
  description = "DynamoDB table name for MCP storage"
}

output "dynamodb_feedback_table_name" {
  value = aws_dynamodb_table.mcp_feedback.name
  description = "DynamoDB table name for MCP feedback storage"
}