#!/bin/bash

# Build script for Lambda deployments
# Creates deployment packages with source code and dependencies

set -e

echo "Building Lambda deployment packages..."

# Function to build a Lambda deployment
build_lambda() {
    local lambda_dir=$1
    local lambda_name=$(basename $lambda_dir)
    
    echo "Building $lambda_name..."
    
    cd "$lambda_dir"
    
    # Remove old deployment package
    rm -f deployment.zip
    
    # Create deployment package with source files
    cd src
    zip -r ../deployment.zip . -x "*.pyc" -x "*__pycache__*"
    cd ..
    
    # Add dependencies from package directory (at root level)
    if [ -d "package" ] && [ "$(ls -A package)" ]; then
        cd package
        zip -r ../deployment.zip . -x "*.pyc" -x "*__pycache__*" -x "*.dist-info/*" -x "httpx-layer/*" -x "*.zip"
        cd ..
    fi
    
    echo "✓ Built $lambda_name/deployment.zip ($(du -h deployment.zip | cut -f1))"
    cd ../..
}

# Build webhook-handler Lambda
if [ -d "lambda-deployments/webhook-handler" ]; then
    build_lambda "lambda-deployments/webhook-handler"
fi

# Build mcp-server Lambda
if [ -d "lambda-deployments/mcp-server" ]; then
    build_lambda "lambda-deployments/mcp-server"
fi

echo "✅ All Lambda packages built successfully!"