# Lambda Best Practices Guide
*For consistent serverless development across all projects*

## 🎯 Purpose
This document establishes standardized practices for AWS Lambda development that can be used by development teams and AI agents to ensure consistency, maintainability, and scalability across all projects.

## 📁 Directory Structure

### Standard Project Layout
```
/lambda/                          # Source code only
  /{function-name}/
    - lambda_function.py          # Standard AWS handler (required)
    - requirements.txt            # Function-specific dependencies
    - config.py                   # Configuration constants (optional)
    - utils.py                    # Utility functions (optional)
    - tests/                      # Unit tests (optional)
      - test_lambda_function.py

/lambda-deployments/              # Build artifacts only (gitignored)
  /{function-name}/
    - deployment.zip              # Ready-to-deploy package
  - build.sh                      # Universal build script

/lambda-layers/                   # Layer source and artifacts
  /{layer-name}/
    - requirements.txt            # Layer dependencies
  /{layer-name}.zip              # Built layer artifact

/terraform/                       # Infrastructure as Code
  /environments/
    /{env}/
      - lambda-{function-name}.tf # Per-function Terraform
```

### Key Principles
1. **Function Isolation**: Each Lambda function has its own subdirectory
2. **Standard Naming**: Always use `lambda_function.py` with `lambda_function.handler`
3. **Source/Build Separation**: Source code and deployment artifacts are separate
4. **Consistent Paths**: Terraform references follow predictable patterns

## 🏗️ Function Structure

### Handler Standard
```python
# lambda_function.py
import json
import os
import logging
from typing import Dict, Any

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler function.
    
    Args:
        event: Lambda event data
        context: Lambda context object
        
    Returns:
        Response dictionary with statusCode and body
    """
    try:
        logger.info(f"Processing event: {json.dumps(event, default=str)}")
        
        # Main business logic here
        result = process_request(event, context)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'  # Adjust as needed
            },
            'body': json.dumps(result)
        }
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e) if os.environ.get('DEBUG') else 'An error occurred'
            })
        }

def process_request(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Main business logic - separate from handler for testability."""
    # Implementation here
    pass
```

## 🛠️ Development Standards

### Environment Variables
```python
# Always use environment variables for configuration
TABLE_NAME = os.environ.get('TABLE_NAME', 'default-table')
API_KEY_PARAM = os.environ.get('API_KEY_PARAM', '/default/api-key')
DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true'
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
```

### Error Handling
```python
# Structured error handling with proper logging
try:
    result = risky_operation()
except SpecificException as e:
    logger.warning(f"Expected error: {e}")
    # Handle gracefully
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    # Re-raise or handle as appropriate
    raise
```

### Secrets Management
```python
import boto3

class SecretsManager:
    """Centralized secrets management with caching."""
    _instance = None
    _secrets = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_secret(self, param_name: str, fallback_env: str = None) -> str:
        """Get secret from Parameter Store with fallback to env var."""
        if param_name in self._secrets:
            return self._secrets[param_name]

        if os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
            try:
                ssm = boto3.client('ssm')
                response = ssm.get_parameter(Name=param_name, WithDecryption=True)
                value = response['Parameter']['Value']
                self._secrets[param_name] = value
                return value
            except Exception as e:
                logger.warning(f"Failed to get parameter {param_name}: {e}")

        # Fallback to environment variable
        if fallback_env:
            return os.getenv(fallback_env, "")
        return ""
```

## 🚀 Deployment Standards

### Terraform Configuration
```hcl
# Standard Lambda function definition
resource "aws_lambda_function" "function_name" {
  filename      = "${path.module}/../../../lambda-deployments/{function-name}/deployment.zip"
  function_name = "{project-name}-{function-name}"
  role         = aws_iam_role.function_name_role.arn
  handler      = "lambda_function.handler"  # Always use this
  runtime      = "python3.11"              # Latest supported Python
  timeout      = 60                        # Reasonable default
  memory_size  = 512                       # Adjust based on needs

  layers = [
    data.aws_lambda_layer_version.dependencies.arn
  ]

  environment {
    variables = {
      LOG_LEVEL = var.environment == "prod" ? "WARN" : "INFO"
      TABLE_NAME = aws_dynamodb_table.table.name
      # Never put secrets directly in environment variables
      API_KEY_PARAM = "/project-name/api-key"
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic,
    aws_iam_role_policy.lambda_policy
  ]

  tags = {
    Name        = "{project-name}-{function-name}"
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "terraform"
  }
}
```

### GitHub Actions Workflow
```yaml
name: Deploy Lambda Function

on:
  push:
    branches: [develop, main]
    paths:
      - 'lambda/{function-name}/**'
      - '.github/workflows/deploy-{function-name}.yml'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Build deployment package
        run: |
          cd lambda/{function-name}
          mkdir -p ../../lambda-deployments/{function-name}
          zip -r ../../lambda-deployments/{function-name}/deployment.zip . -x "tests/*" "*.pyc" "__pycache__/*"

      - name: Deploy via Terraform
        run: |
          cd terraform/environments/global
          terraform init
          terraform apply -target=aws_lambda_function.{function_name} -auto-approve
```

## 🧪 Testing Standards

### Unit Tests
```python
# tests/test_lambda_function.py
import pytest
import json
from unittest.mock import patch, MagicMock
from lambda_function import handler, process_request

class TestLambdaFunction:
    
    @patch.dict('os.environ', {'TABLE_NAME': 'test-table'})
    def test_handler_success(self):
        """Test successful request handling."""
        event = {
            'httpMethod': 'POST',
            'body': json.dumps({'test': 'data'})
        }
        context = MagicMock()
        
        result = handler(event, context)
        
        assert result['statusCode'] == 200
        assert 'body' in result

    def test_handler_error(self):
        """Test error handling."""
        event = {}  # Invalid event
        context = MagicMock()
        
        result = handler(event, context)
        
        assert result['statusCode'] == 500
```

### Integration Testing
```python
# tests/test_integration.py
import boto3
import pytest
from moto import mock_dynamodb, mock_lambda

@mock_dynamodb
@mock_lambda
def test_full_integration():
    """Test function with mocked AWS services."""
    # Setup mocked services
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.create_table(
        TableName='test-table',
        KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}]
    )
    
    # Test function
    # Implementation here
```

## 🔐 Security Standards

### IAM Policies
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ssm:GetParameter"
      ],
      "Resource": [
        "arn:aws:ssm:*:*:parameter/project-name/*"
      ]
    }
  ]
}
```

### Security Checklist
- [ ] No secrets in environment variables (use Parameter Store)
- [ ] Least privilege IAM policies
- [ ] Input validation on all user data
- [ ] Proper error handling that doesn't expose internals
- [ ] VPC configuration if accessing private resources
- [ ] Resource-based policies where appropriate

## 📊 Monitoring Standards

### CloudWatch Metrics
```python
import boto3

cloudwatch = boto3.client('cloudwatch')

def put_custom_metric(metric_name: str, value: float, unit: str = 'Count'):
    """Put custom metric to CloudWatch."""
    try:
        cloudwatch.put_metric_data(
            Namespace=f'AWS/Lambda/{os.environ["AWS_LAMBDA_FUNCTION_NAME"]}',
            MetricData=[{
                'MetricName': metric_name,
                'Value': value,
                'Unit': unit
            }]
        )
    except Exception as e:
        logger.warning(f"Failed to put metric {metric_name}: {e}")
```

### Structured Logging
```python
import json
import logging

def log_event(event_type: str, data: dict):
    """Log structured event data."""
    log_data = {
        'timestamp': datetime.utcnow().isoformat(),
        'event_type': event_type,
        'function_name': os.environ.get('AWS_LAMBDA_FUNCTION_NAME'),
        'request_id': context.aws_request_id if context else None,
        'data': data
    }
    logger.info(json.dumps(log_data))
```

## 🔄 CI/CD Standards

### Build Process
1. **Lint**: Use `flake8` or `black` for code formatting
2. **Test**: Run unit tests with `pytest`
3. **Security**: Scan dependencies with `safety`
4. **Package**: Create deployment zip with dependencies
5. **Deploy**: Use Terraform for infrastructure updates

### Environments
- **Development**: Auto-deploy from `develop` branch
- **Staging**: Manual approval required
- **Production**: Manual approval + tagged releases only

## 📋 Checklist for New Lambda Functions

### Development Phase
- [ ] Create function directory in `/lambda/{function-name}/`
- [ ] Implement `lambda_function.py` with standard handler
- [ ] Add `requirements.txt` with dependencies
- [ ] Write unit tests in `tests/` directory
- [ ] Configure environment variables
- [ ] Implement proper error handling and logging

### Infrastructure Phase
- [ ] Create Terraform configuration
- [ ] Define IAM role with least privileges
- [ ] Configure Lambda layers if needed
- [ ] Set up CloudWatch log groups
- [ ] Configure VPC if required

### Deployment Phase
- [ ] Create GitHub Actions workflow
- [ ] Test deployment pipeline
- [ ] Configure monitoring and alerts
- [ ] Document function purpose and usage
- [ ] Add function to project README

## 🤖 AI Agent Instructions

When creating or modifying Lambda functions, always:

1. **Follow the directory structure** exactly as specified
2. **Use the standard handler template** with proper error handling
3. **Implement secrets management** via Parameter Store
4. **Create comprehensive tests** for all business logic
5. **Configure appropriate IAM permissions** with least privilege
6. **Set up monitoring and logging** with structured data
7. **Document all functions** with clear purpose and usage

### Common Patterns to Implement
- Database operations with connection pooling
- API integrations with retry logic
- File processing with chunked operations
- Event-driven architectures with SQS/SNS
- Scheduled tasks with EventBridge

### Code Quality Standards
- Type hints on all function parameters and returns
- Docstrings for all public functions
- Error handling for all external dependencies
- Proper resource cleanup (context managers)
- Performance optimization for cold starts

---

*This document should be updated as new patterns emerge and AWS services evolve. Use it as the foundation for all Lambda development across projects.*