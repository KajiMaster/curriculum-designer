# Trello AI Webhook Handler

Lambda function for processing Trello webhook events with AI assistance.

## Features

🤖 **AI Comments** - Teacher writes "@ai suggest activities" → AI responds
📅 **Smart Scheduling** - Move card to "This Week" → Auto-creates prep checklist  
🎯 **Activity Analysis** - AI analyzes activities and suggests improvements
📚 **Lesson Planning** - AI builds complete lesson plans from activities
🔄 **Alternatives** - AI finds similar activities when needed

## Architecture

- **Runtime**: Python 3.11
- **Framework**: FastAPI with Mangum adapter for Lambda
- **AI Provider**: OpenAI GPT-3.5-turbo
- **Deployment**: AWS Lambda + API Gateway
- **Configuration**: AWS Parameter Store for secrets
- **Authentication**: GitHub OIDC for secure CI/CD

## Local Development

### 1. Install Dependencies
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 2. Environment Variables
Create `.env` file:
```
TRELLO_API_KEY=your_trello_api_key
TRELLO_TOKEN=your_trello_token
OPENAI_API_KEY=your_openai_key
TRELLO_WEBHOOK_SECRET=optional_webhook_secret
```

### 3. Run Locally
```bash
python main.py
# Server will start on http://localhost:8000
```

### 4. Testing
```bash
# Run tests
python -m pytest test_lambda.py -v

# Lint code
flake8 lambda_main.py --max-line-length=120
```

## How It Works

### Teacher Experience (100% in Trello):

1. **Ask AI for Help**:
   ```
   Teacher adds comment: "@ai suggest 20-minute grammar activities"
   → AI responds with specific suggestions
   ```

2. **Schedule Activities**:
   ```
   Teacher drags card to "This Week" list
   → AI auto-adds preparation checklist
   → AI posts helpful setup comment
   ```

3. **Get Alternatives**:
   ```
   Teacher comments: "@ai find easier alternatives"
   → AI suggests 3 similar but simpler activities
   ```

4. **Build Lessons**:
   ```
   Teacher creates card: "🤖 AI: Build Lesson - Tuesday 2pm" 
   → AI responds asking for details
   → Teacher provides level/focus in comment
   → AI creates complete lesson plan
   ```

### AI Capabilities:

- **Activity Suggestions** - Based on level, duration, focus
- **Lesson Planning** - Optimal timing and sequencing  
- **Activity Analysis** - Strengths, improvements, variations
- **Alternative Finding** - Similar activities with different complexity
- **Preparation Help** - Automated checklists and reminders
- **Teaching Sequence** - What to teach before/after activities

## Deployment

### Infrastructure
The infrastructure is managed by Terraform in `terraform/environments/multi-env/`. 

**Important**: Terraform only manages the infrastructure (Lambda function resource, IAM roles, API Gateway). The actual code deployment is handled by GitHub Actions CI/CD.

### CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/deploy-lambda.yml`) handles:

1. **Testing**: Linting and unit tests
2. **Development Deployment**: Automatic deployment on `develop` branch

#### Environment
- **Development**: `curriculum-designer-webhook-dev`

#### Required Secrets
Configure these in GitHub repository secrets:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

#### Deployment Process
1. Push to `develop` → Runs tests and deploys to development
2. Each deployment creates a new Lambda deployment package
3. Function configuration is updated
4. Deployment is tested with health check

### Configuration

#### AWS Parameter Store
The following parameters must be configured in AWS Parameter Store:

- `/global/curriculum-designer/trello-api-key`
- `/global/curriculum-designer/trello-token`
- `/global/curriculum-designer/openai-api-key`
- `/global/curriculum-designer/trello-webhook-secret`

#### Lambda Environment Variables
Set by Terraform:
- `ENVIRONMENT`
- `TRELLO_API_KEY_PARAM`
- `TRELLO_TOKEN_PARAM`
- `OPENAI_API_KEY_PARAM`
- `TRELLO_WEBHOOK_SECRET_PARAM`

## Webhook Events Handled

- `commentCard` - "@ai" requests in comments
- `updateCard` - Card moves between lists  
- `createCard` - New AI command cards created

## Cost Estimate

- **AWS Lambda**: ~$1-3/month (depending on usage)
- **API Gateway**: ~$1-2/month (depending on requests)
- **OpenAI API**: ~$2-10/month (depending on usage)
- **Total**: Under $15/month for full AI curriculum assistant

## Monitoring & Troubleshooting

### CloudWatch Logs
- **Development**: `/aws/lambda/curriculum-designer-webhook-dev`

### Common Issues

1. **OpenAI API Quota Exceeded**
   - Update API key in Parameter Store
   - Check billing in OpenAI console

2. **Trello Webhook Not Responding**
   - Verify webhook URL in Trello
   - Check Lambda function logs
   - Test with `/health` endpoint

3. **Parameter Store Access Denied**
   - Verify IAM role permissions
   - Check parameter names and paths

### View Logs
```bash
# View recent logs
aws logs tail /aws/lambda/curriculum-designer-webhook-dev --follow

# View specific log group
aws logs describe-log-streams --log-group-name /aws/lambda/curriculum-designer-webhook-dev
```

## Testing

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test manual webhook
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{"action": {"type": "commentCard", "data": {"text": "@ai help", "card": {"id": "test"}}}}'
```

## Board Setup Guide

1. Create Trello board with lists from `trello-ai-board-design.md`
2. Add labels for levels and categories
3. Create sample activity cards
4. Set up webhook pointing to your deployed service
5. Test with "@ai hello" comment
6. Start using AI assistance!

The teacher never needs to leave Trello - everything happens in the board interface they already know.