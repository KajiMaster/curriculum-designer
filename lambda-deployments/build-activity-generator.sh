#!/bin/bash

# Build Activity Generator Lambda deployment package for CI/CD

set -e

echo "Building Activity Generator Lambda deployment package..."

# Create deployment directory
rm -rf activity-generator-deployment
mkdir -p activity-generator-deployment

# Copy Lambda function code
cp ../lambda/activity_generator.py activity-generator-deployment/

# Create deployment package
cd activity-generator-deployment
zip -r ../activity_generator.zip .
cd ..

# Clean up
rm -rf activity-generator-deployment

echo "Deployment package created: activity_generator.zip"
echo "Ready for GitHub Actions deployment"