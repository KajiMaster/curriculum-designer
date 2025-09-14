# ============================================
# LAMBDA LAYER FOR DEPENDENCIES
# ============================================

# Lambda layer for webhook handler dependencies
resource "aws_lambda_layer_version" "webhook_dependencies" {
  filename          = "${path.module}/../../../lambda-layers/webhook-dependencies.zip"
  layer_name        = "curriculum-designer-webhook-dependencies"
  description       = "Dependencies for curriculum designer webhook handler"
  
  compatible_runtimes = ["python3.11"]
  
  # Only create if the zip file exists
  source_code_hash = fileexists("${path.module}/../../../lambda-layers/webhook-dependencies.zip") ? filebase64sha256("${path.module}/../../../lambda-layers/webhook-dependencies.zip") : null
}

# Lambda layer for MCP server dependencies  
resource "aws_lambda_layer_version" "mcp_dependencies" {
  filename          = "${path.module}/../../../lambda-layers/mcp-dependencies.zip"
  layer_name        = "curriculum-designer-mcp-dependencies"
  description       = "Dependencies for curriculum designer MCP server"
  
  compatible_runtimes = ["python3.11"]
  
  # Only create if the zip file exists
  source_code_hash = fileexists("${path.module}/../../../lambda-layers/mcp-dependencies.zip") ? filebase64sha256("${path.module}/../../../lambda-layers/mcp-dependencies.zip") : null
}

# Lambda layer for HTTPX with asyncio support (for activity generator)
resource "aws_lambda_layer_version" "httpx_dependencies" {
  filename          = "${path.module}/../../../lambda-layers/httpx-dependencies.zip"
  layer_name        = "curriculum-httpx-dependencies"
  description       = "HTTPX with asyncio dependencies for activity generation"
  
  compatible_runtimes = ["python3.11"]
  
  # Only create if the zip file exists
  source_code_hash = fileexists("${path.module}/../../../lambda-layers/httpx-dependencies.zip") ? filebase64sha256("${path.module}/../../../lambda-layers/httpx-dependencies.zip") : null
}

# Note: unified dependencies layer managed separately - it already exists
# The multi-env configuration references it via data source

# Output layer ARNs for use in other environments
output "webhook_dependencies_layer_arn" {
  value = aws_lambda_layer_version.webhook_dependencies.arn
  description = "ARN of the webhook dependencies Lambda layer"
}

output "mcp_dependencies_layer_arn" {
  value = aws_lambda_layer_version.mcp_dependencies.arn
  description = "ARN of the MCP dependencies Lambda layer"
}

output "httpx_dependencies_layer_arn" {
  value = aws_lambda_layer_version.httpx_dependencies.arn
  description = "ARN of the HTTPX dependencies Lambda layer"
}

# unified_dependencies layer output removed - managed separately