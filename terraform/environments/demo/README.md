# Trello Demo Board - Terraform Managed

This creates a fully Terraform-managed Trello board to demonstrate capabilities.

## Prerequisites

1. **Trello API Credentials**
   - Get API Key: https://trello.com/app-key
   - Generate Token: Click "Token" link on the API key page
   - Store in Parameter Store:
   ```bash
   aws ssm put-parameter \
     --name "/global/curriculum-designer/trello-api-key" \
     --value "YOUR_API_KEY" \
     --type "SecureString"
   
   aws ssm put-parameter \
     --name "/global/curriculum-designer/trello-token" \
     --value "YOUR_TOKEN" \
     --type "SecureString"
   ```

2. **Terraform installed** (>= 1.0)

## Setup

```bash
# Initialize Terraform
terraform init

# Plan changes
terraform plan

# Create the demo board
terraform apply
```

## What Gets Created

- 1 Trello Board with blue background
- 7 Lists (workflow columns)
- 10 Labels (categories, levels, tags)
- 5 Sample Activity Cards with structured data
- 2 Checklists (reusable templates)
- 1 Webhook (for automation)

## Access Your Board

After apply, get the board URL:
```bash
terraform output board_url
```

## Features Demonstrated

### ✅ What Terraform CAN Do:
- Create/destroy boards
- Manage lists and labels
- Create cards with descriptions
- Set up webhooks
- Add team members
- Create checklists

### ❌ What Terraform CANNOT Do:
- Add card attachments
- Create comments
- Use Power-Ups
- Set due dates (easily)
- Create Butler rules
- Manage card positions dynamically

## Daily Operations

After initial setup, use:
- **Trello UI**: For moving cards, updating content
- **Trello API**: For bulk operations, automation
- **Butler**: For Trello-native automation rules

## Destroy

To remove everything:
```bash
terraform destroy
```

## Tips

1. **Don't manage content cards with Terraform** - They change too often
2. **Use Terraform for structure** - Lists, labels, webhooks
3. **Use API/UI for content** - Daily card management
4. **Version control the structure** - Not the content

## Integration Points

The board ID and list IDs are output for use in:
- MCP Server configuration
- API automation scripts
- Webhook handlers
- AI integration