#!/bin/bash

# Enhanced build script for optimized webhook handler
# Supports the new modular architecture with src/ structure
# Usage: ./build-optimized-webhook.sh

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WEBHOOK_SOURCE_DIR="$PROJECT_ROOT/webhook-handler"
DEPLOY_DIR="$PROJECT_ROOT/lambda-deployments/webhook-handler"

echo "🔨 Building Optimized Webhook Handler..."
echo "📁 Source: $WEBHOOK_SOURCE_DIR"
echo "📁 Deploy: $DEPLOY_DIR"

# Verify source directory exists
if [[ ! -d "$WEBHOOK_SOURCE_DIR" ]]; then
    echo "❌ Webhook handler directory not found: $WEBHOOK_SOURCE_DIR"
    exit 1
fi

# Verify optimized structure exists
if [[ ! -d "$WEBHOOK_SOURCE_DIR/src" ]]; then
    echo "❌ Optimized src/ directory not found in: $WEBHOOK_SOURCE_DIR"
    echo "💡 This script is for the new optimized architecture"
    exit 1
fi

# Create clean deployment directory
echo "🧹 Cleaning deployment directory..."
rm -rf "$DEPLOY_DIR"
mkdir -p "$DEPLOY_DIR"

# Copy optimized source code structure
echo "📦 Copying optimized source code..."
cp -r "$WEBHOOK_SOURCE_DIR/src"/* "$DEPLOY_DIR/"

# Copy the optimized main entry point as lambda_main.py (for AWS Lambda)
if [[ -f "$WEBHOOK_SOURCE_DIR/lambda_main_optimized.py" ]]; then
    echo "📝 Using optimized lambda_main_optimized.py as entry point..."
    cp "$WEBHOOK_SOURCE_DIR/lambda_main_optimized.py" "$DEPLOY_DIR/lambda_main.py"
else
    echo "⚠️ lambda_main_optimized.py not found, falling back to original..."
    if [[ -f "$WEBHOOK_SOURCE_DIR/lambda_main.py" ]]; then
        cp "$WEBHOOK_SOURCE_DIR/lambda_main.py" "$DEPLOY_DIR/"
    else
        echo "❌ No lambda_main.py found in webhook-handler directory"
        exit 1
    fi
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
if [[ -f "$WEBHOOK_SOURCE_DIR/requirements.txt" ]]; then
    pip install -r "$WEBHOOK_SOURCE_DIR/requirements.txt" -t "$DEPLOY_DIR/" --quiet
    echo "✅ Dependencies installed from requirements.txt"
else
    echo "❌ requirements.txt not found"
    exit 1
fi

# Clean up unnecessary files for Lambda deployment
echo "🧹 Cleaning up deployment package..."

# Remove test files and directories
find "$DEPLOY_DIR" -name "tests" -type d -exec rm -rf {} + 2>/dev/null || true
find "$DEPLOY_DIR" -name "*test*.py" -delete 2>/dev/null || true
find "$DEPLOY_DIR" -name "test_*" -delete 2>/dev/null || true
find "$DEPLOY_DIR" -name "*_test*" -delete 2>/dev/null || true

# Remove Python cache files
find "$DEPLOY_DIR" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find "$DEPLOY_DIR" -name "*.pyc" -delete 2>/dev/null || true
find "$DEPLOY_DIR" -name "*.pyo" -delete 2>/dev/null || true

# Remove development and documentation files
find "$DEPLOY_DIR" -name "*.md" -delete 2>/dev/null || true
find "$DEPLOY_DIR" -name "*.rst" -delete 2>/dev/null || true
find "$DEPLOY_DIR" -name "*.txt" -not -name "requirements.txt" -delete 2>/dev/null || true
find "$DEPLOY_DIR" -name "*.yml" -delete 2>/dev/null || true
find "$DEPLOY_DIR" -name "*.yaml" -delete 2>/dev/null || true

# Remove .dist-info directories (package metadata)
find "$DEPLOY_DIR" -name "*.dist-info" -type d -exec rm -rf {} + 2>/dev/null || true
find "$DEPLOY_DIR" -name "*.egg-info" -type d -exec rm -rf {} + 2>/dev/null || true

# Remove .git directories and files
find "$DEPLOY_DIR" -name ".git*" -exec rm -rf {} + 2>/dev/null || true

# Remove pytest and other development tools if accidentally included
rm -rf "$DEPLOY_DIR/pytest" "$DEPLOY_DIR/_pytest" 2>/dev/null || true
rm -rf "$DEPLOY_DIR/flake8" "$DEPLOY_DIR/mypy" 2>/dev/null || true

# Verify the optimized structure is intact
echo "🔍 Verifying deployment package structure..."
if [[ -f "$DEPLOY_DIR/lambda_main.py" ]]; then
    echo "✅ Entry point: lambda_main.py"
else
    echo "❌ Missing lambda_main.py"
    exit 1
fi

if [[ -d "$DEPLOY_DIR/config" && -d "$DEPLOY_DIR/models" && -d "$DEPLOY_DIR/clients" && -d "$DEPLOY_DIR/services" && -d "$DEPLOY_DIR/handlers" && -d "$DEPLOY_DIR/utils" ]]; then
    echo "✅ Optimized modular structure verified"
    echo "  📁 config/ - Configuration management"
    echo "  📁 models/ - Pydantic data models"  
    echo "  📁 clients/ - HTTP clients with pooling"
    echo "  📁 services/ - Business logic"
    echo "  📁 handlers/ - Request handlers"
    echo "  📁 utils/ - Utilities and helpers"
else
    echo "❌ Incomplete modular structure in deployment"
    ls -la "$DEPLOY_DIR"
    exit 1
fi

# Test that the Lambda handler can be imported
echo "🧪 Testing Lambda handler import..."
cd "$DEPLOY_DIR"
python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from lambda_main import lambda_handler
    print('✅ Lambda handler imports successfully')
except ImportError as e:
    print(f'❌ Lambda handler import failed: {e}')
    sys.exit(1)
except Exception as e:
    print(f'❌ Unexpected error: {e}')
    sys.exit(1)
"
cd - > /dev/null

# Create deployment ZIP
echo "📦 Creating deployment ZIP..."
cd "$DEPLOY_DIR"
zip -r deployment.zip . \
    -x "*.md" "*.txt" "tests/*" ".*" "__pycache__/*" "*.pyc" \
    > /dev/null
cd - > /dev/null

# Check final package size
PACKAGE_SIZE=$(du -h "$DEPLOY_DIR/deployment.zip" | cut -f1)
PACKAGE_SIZE_BYTES=$(du -b "$DEPLOY_DIR/deployment.zip" | cut -f1)
PACKAGE_SIZE_MB=$((PACKAGE_SIZE_BYTES / 1024 / 1024))

echo ""
echo "📊 Deployment Package Summary:"
echo "  📦 Package: $DEPLOY_DIR/deployment.zip"
echo "  📏 Size: $PACKAGE_SIZE (${PACKAGE_SIZE_MB}MB)"

# Warn if package is large
if [[ $PACKAGE_SIZE_MB -gt 50 ]]; then
    echo "⚠️  WARNING: Package size exceeds 50MB Lambda limit for direct upload"
    echo "💡 Consider using Lambda Layers for dependencies"
elif [[ $PACKAGE_SIZE_MB -gt 30 ]]; then
    echo "⚠️  NOTICE: Package size is getting large (>${PACKAGE_SIZE_MB}MB)"
    echo "💡 Monitor size for future deployments"
else
    echo "✅ Package size is within Lambda limits"
fi

# Final verification test
echo "🔬 Final verification test..."
cd "$DEPLOY_DIR"
python3 -c "
import json
from lambda_main import lambda_handler

# Test basic health check
test_event = {
    'httpMethod': 'GET',
    'path': '/health',
    'headers': {}
}

class MockContext:
    aws_request_id = 'test-build-verification'
    function_name = 'webhook-handler-build-test'

try:
    result = lambda_handler(test_event, MockContext())
    print('✅ Lambda handler executes successfully')
    
    # Verify response structure  
    if 'statusCode' in result and 'body' in result:
        print('✅ Response structure is valid')
        status_code = result.get('statusCode')
        if status_code == 200:
            print('✅ Health check returns 200 OK')
        else:
            print(f'⚠️  Health check returned status: {status_code}')
    else:
        print('❌ Invalid response structure')
        exit(1)
        
except Exception as e:
    print(f'❌ Lambda execution test failed: {e}')
    import traceback
    traceback.print_exc()
    exit(1)
"
cd - > /dev/null

echo ""
echo "🎉 Optimized Webhook Handler built successfully!"
echo "📁 Deployment package: $DEPLOY_DIR/deployment.zip"
echo "🚀 Ready for deployment to AWS Lambda"

# Return success
exit 0