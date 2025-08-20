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

# Reference Lambda layer from global infrastructure
data "aws_lambda_layer_version" "webhook_dependencies" {
  layer_name = "curriculum-designer-webhook-dependencies"
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