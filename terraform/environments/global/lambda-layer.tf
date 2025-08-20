# ============================================
# LAMBDA LAYER FOR DEPENDENCIES
# ============================================

# Lambda layer for webhook handler dependencies
resource "aws_lambda_layer_version" "webhook_dependencies" {
  filename          = "${path.module}/../../../webhook-handler/dependencies-layer.zip"
  layer_name        = "curriculum-designer-webhook-dependencies"
  description       = "Dependencies for curriculum designer webhook handler"
  
  compatible_runtimes = ["python3.11"]
  
  # Only create if the zip file exists
  source_code_hash = fileexists("${path.module}/../../../webhook-handler/dependencies-layer.zip") ? filebase64sha256("${path.module}/../../../webhook-handler/dependencies-layer.zip") : null
}

# Output layer ARN for use in other environments
output "webhook_dependencies_layer_arn" {
  value = aws_lambda_layer_version.webhook_dependencies.arn
  description = "ARN of the webhook dependencies Lambda layer"
}