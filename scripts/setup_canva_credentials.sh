#!/bin/bash

# Script to setup Canva API credentials in AWS Parameter Store
# You'll need to get your Canva Access Token from https://www.canva.dev/

echo "Setting up Canva API credentials..."

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "Error: AWS CLI not configured. Please configure AWS credentials first."
    exit 1
fi

echo "Please enter your Canva Access Token (get it from https://www.canva.dev/):"
read -s CANVA_ACCESS_TOKEN

if [ -z "$CANVA_ACCESS_TOKEN" ]; then
    echo "Error: Canva Access Token is required"
    exit 1
fi

# Store in Parameter Store
echo "Storing Canva Access Token in Parameter Store..."
aws ssm put-parameter \
    --name "/global/curriculum-designer/canva-access-token" \
    --value "$CANVA_ACCESS_TOKEN" \
    --type "SecureString" \
    --description "Canva API Access Token for curriculum designer" \
    --overwrite

if [ $? -eq 0 ]; then
    echo "✅ Canva Access Token stored successfully"
else
    echo "❌ Failed to store Canva Access Token"
    exit 1
fi

# Optional: Store template IDs if you have them
echo ""
echo "Optional: Enter Canva Lesson Template ID (press Enter to skip):"
read CANVA_LESSON_TEMPLATE_ID

if [ ! -z "$CANVA_LESSON_TEMPLATE_ID" ]; then
    aws ssm put-parameter \
        --name "/global/curriculum-designer/canva-lesson-template-id" \
        --value "$CANVA_LESSON_TEMPLATE_ID" \
        --type "String" \
        --description "Canva template ID for lesson plans" \
        --overwrite
    echo "✅ Lesson template ID stored"
fi

echo ""
echo "Optional: Enter Canva Activity Card Template ID (press Enter to skip):"
read CANVA_ACTIVITY_TEMPLATE_ID

if [ ! -z "$CANVA_ACTIVITY_TEMPLATE_ID" ]; then
    aws ssm put-parameter \
        --name "/global/curriculum-designer/canva-activity-template-id" \
        --value "$CANVA_ACTIVITY_TEMPLATE_ID" \
        --type "String" \
        --description "Canva template ID for activity cards" \
        --overwrite
    echo "✅ Activity template ID stored"
fi

echo ""
echo "✅ Canva credentials setup complete!"
echo ""
echo "Next steps:"
echo "1. Deploy the updated MCP server with Canva integration"
echo "2. Test creating a presentation from a lesson plan"