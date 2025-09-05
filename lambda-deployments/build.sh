#!/bin/bash

# Universal Lambda build script
# Usage: ./build.sh [function-name]
# If no function name provided, builds all functions

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LAMBDA_SOURCE_DIR="$PROJECT_ROOT/lambda"
DEPLOY_DIR="$PROJECT_ROOT/lambda-deployments"

build_function() {
    local function_name="$1"
    local source_dir="$LAMBDA_SOURCE_DIR/$function_name"
    local deploy_dir="$DEPLOY_DIR/$function_name"
    
    if [[ ! -d "$source_dir" ]]; then
        echo "❌ Function directory not found: $source_dir"
        return 1
    fi
    
    echo "🔨 Building Lambda function: $function_name"
    
    # Create clean deployment directory
    rm -rf "$deploy_dir"
    mkdir -p "$deploy_dir"
    
    # Copy source files (exclude tests and cache)
    cp -r "$source_dir"/* "$deploy_dir/"
    find "$deploy_dir" -name "tests" -type d -exec rm -rf {} + 2>/dev/null || true
    find "$deploy_dir" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    find "$deploy_dir" -name "*.pyc" -delete 2>/dev/null || true
    
    # Create deployment package
    cd "$deploy_dir"
    zip -r deployment.zip . -x "requirements.txt" "*.md" "tests/*" ".*"
    
    echo "✅ Built: $deploy_dir/deployment.zip"
    return 0
}

# If specific function provided, build only that function
if [[ $# -gt 0 ]]; then
    build_function "$1"
    exit $?
fi

# Otherwise, build all functions
echo "🚀 Building all Lambda functions..."

success_count=0
total_count=0

for function_dir in "$LAMBDA_SOURCE_DIR"/*; do
    if [[ -d "$function_dir" ]]; then
        function_name=$(basename "$function_dir")
        total_count=$((total_count + 1))
        
        if build_function "$function_name"; then
            success_count=$((success_count + 1))
        fi
    fi
done

echo ""
echo "📊 Build Summary:"
echo "   Total functions: $total_count"
echo "   Successful: $success_count"
echo "   Failed: $((total_count - success_count))"

if [[ $success_count -eq $total_count ]]; then
    echo "🎉 All functions built successfully!"
    exit 0
else
    echo "❌ Some functions failed to build"
    exit 1
fi