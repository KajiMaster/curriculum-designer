# Curriculum Designer

An AI-powered curriculum design platform that revolutionizes how English teachers create personalized lessons for online 1-on-1 teaching. Built specifically for teachers transitioning from traditional classrooms to digital education, reducing curriculum preparation time from hours to minutes.

## 🎯 Problem Statement

English teachers transitioning to online 1-on-1 teaching face a significant challenge: creating customized curriculum for each student's unique needs, proficiency level, and professional context. Traditional methods require 2-3 hours of preparation per student per week. This platform reduces that to under 15 minutes while maintaining high-quality, personalized education.

## ✨ Key Features

### Intelligent Lesson Planning
- **AI-Powered Activity Suggestions**: Get contextually relevant activities based on student profiles
- **Modular Activity Library**: 25-45 minute activities with flexible endpoints
- **Smart Sequencing**: AI optimizes lesson flow for maximum learning impact
- **Professional Context Integration**: Tailored content for lawyers, doctors, marketers, and other professionals

### Seamless Workflow Integration
- **Trello-First Interface**: Works within teachers' existing Trello workflow
- **Natural Language Commands**: Simply comment `@ai` to get instant assistance
- **Automated Scheduling**: Drag cards to "This Week" and get automatic prep checklists
- **Real-Time Updates**: Webhook-powered instant responses

### Content Generation
- **Canva Integration**: Automated creation of professional lesson presentations
- **Activity Card Generation**: Visual materials created automatically
- **PDF Export**: Ready-to-use lesson materials
- **Template-Based Design**: Consistent, professional look across all materials

### Student Management
- **Comprehensive Profiles**: Track proficiency, interests, and professional needs
- **Progress Tracking**: Monitor improvement across all skill areas
- **Assessment Tools**: Initial placement and ongoing evaluation
- **Learning Analytics**: Data-driven insights into student progress

## 🛠 Tech Stack

### Frontend & Backend
- **Next.js 14** with App Router and TypeScript
- **Tailwind CSS** for responsive design
- **Prisma ORM** with PostgreSQL
- **NextAuth** for secure authentication
- **React Query** for efficient data fetching

### AI & Integrations
- **OpenAI GPT** for intelligent content generation
- **Trello API** for workflow management
- **Canva API** for automated design creation
- **MCP (Model Context Protocol)** server in Python for AI integration layer

### Infrastructure
- **AWS Lambda** for serverless webhook processing
- **AWS DynamoDB** for lesson plan storage
- **AWS Parameter Store** for secure configuration
- **Terraform** for infrastructure as code
- **GitHub Actions** for CI/CD

## 🏗 Architecture

```
                                   Primary Workflow
                    ┌─────────────────────────────────────────────────┐
                    │                                                 │
                    ▼                                                 │
         ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
         │   Trello Board  │────▶│  AWS Lambda     │────▶│   OpenAI GPT    │
         │ (Primary UI)    │     │   (MCP Server)  │     │   (AI Service)  │
         │                 │◀────│   + Webhooks    │◀────│                 │
         └─────────────────┘     └─────────────────┘     └─────────────────┘
                    │                       │                        │
                    │                       ▼                        ▼
                    │              ┌─────────────────┐    ┌─────────────────┐
                    │              │ AWS Parameter   │    │   Canva API     │
                    │              │     Store       │    │ (Presentations) │
                    │              │  (Credentials)  │    └─────────────────┘
                    │              └─────────────────┘              │
                    │                       │                       │
                    │                       ▼                       │
                    │              ┌─────────────────┐              │
                    └─────────────▶│  AWS DynamoDB   │◀─────────────┘
                                   │ (Lesson Plans)  │
                                   └─────────────────┘

                            Optional Legacy Components
                                       │
                              ┌─────────────────┐
                              │   Next.js App   │
                              │   (Optional)    │
                              └─────────────────┘
                                       │
                              ┌─────────────────┐
                              │   PostgreSQL    │
                              │  (via Vercel)   │
                              └─────────────────┘
```

## 🚀 Getting Started

The primary interface for this system is **Trello** - teachers work directly in their Trello boards and interact with AI through comments. This project also includes a Next.js web application and Vercel PostgreSQL database as optional/legacy components that demonstrate full-stack development capabilities, though they are not required for the core Trello-based workflow.

### Prerequisites
- Python 3.11+ (for MCP server and Lambda functions)
- AWS account (for production deployment)
- Trello account and API credentials
- OpenAI API key
- Optional: Node.js >= 18 (if running the Next.js companion app)

### Core Setup (Trello Integration)

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/curriculum-designer.git
cd curriculum-designer
```

2. **Set up the MCP server**
```bash
cd mcp-server
pip install -r requirements.txt
```

3. **Configure environment variables**
Create a `.env` file with:
- `OPENAI_API_KEY` - Your OpenAI API key
- `TRELLO_API_KEY` and `TRELLO_TOKEN`
- `CANVA_CLIENT_ID` and `CANVA_CLIENT_SECRET` (optional, for presentation generation)

4. **Deploy to AWS Lambda**
```bash
./deploy.sh
```

5. **Set up Trello webhook**
```bash
python scripts/register_webhook.py
```

Once configured, teachers can interact with the AI directly in Trello by commenting `@ai` on cards.

### Optional: Legacy Next.js Application

The project includes a Next.js web application with Prisma/PostgreSQL that was built during initial development. While not required for the core Trello workflow, it demonstrates full-stack development capabilities and could be useful for admin functions or reporting.

To run the web application:

```bash
npm install
npx prisma generate
# Set up Vercel PostgreSQL or other database
npm run dev
```

### Production Deployment

1. **Infrastructure Setup**
```bash
cd terraform/environments/production
terraform init
terraform plan
terraform apply
```

2. **Deploy Lambda Functions**
```bash
cd mcp-server
./deploy.sh
```

3. **Configure Webhooks**
- Set up Trello webhooks to point to your Lambda endpoint
- Configure Canva OAuth redirect URLs

## 📁 Project Structure

```
curriculum-designer/
├── app/                    # Next.js app router pages
│   ├── activities/        # Activities management UI
│   ├── api/               # API routes
│   ├── layout.tsx         # Root layout
│   └── page.tsx           # Home page
├── components/            # React components
├── lib/                   # Utility functions and configs
├── prisma/                # Database schema and migrations
├── mcp-server/            # MCP integration server (Python)
│   ├── lambda_handler.py  # AWS Lambda webhook handler
│   ├── server.py          # MCP server implementation
│   ├── canva_integration.py # Canva API integration
│   └── requirements.txt   # Python dependencies
├── terraform/             # Infrastructure as code
│   └── environments/      # Environment-specific configs
└── .github/               # CI/CD workflows
```

## 🔑 Key Workflows

### Teacher Creates a Lesson Plan
1. Teacher opens their Trello board
2. Comments `@ai suggest activities for B2 lawyer focusing on negotiations`
3. AI responds with 3-5 relevant activity suggestions
4. Teacher selects activities and moves to "This Week"
5. System automatically generates preparation checklist
6. Canva presentation created automatically

### Student Assessment Flow
1. New student completes initial assessment
2. System analyzes responses and determines proficiency
3. AI generates personalized curriculum recommendations
4. Teacher reviews and approves curriculum
5. Lessons scheduled based on availability

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.