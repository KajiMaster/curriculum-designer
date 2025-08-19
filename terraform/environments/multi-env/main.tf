terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    vercel = {
      source  = "vercel/vercel"
      version = "~> 1.0"
    }
  }
  
}

provider "aws" {
  region = var.aws_region
}

# Retrieve global configuration and secrets from Parameter Store
data "aws_ssm_parameter" "github_org" {
  name = "/global/curriculum-designer/github-org"
}

data "aws_ssm_parameter" "github_repo" {
  name = "/global/curriculum-designer/github-repo"
}

data "aws_ssm_parameter" "vercel_api_token" {
  name = "/global/curriculum-designer/vercel-api-token"
}

data "aws_ssm_parameter" "openai_api_key" {
  name = "/global/curriculum-designer/openai-api-key"
}

# Environment-specific secrets
data "aws_ssm_parameter" "nextauth_secret" {
  name = "/${var.environment}/curriculum-designer/nextauth-secret"
}

provider "vercel" {
  api_token = data.aws_ssm_parameter.vercel_api_token.value
}

# Environment-specific Parameter Store parameters (already exists, just reference it)

# Vercel Project
resource "vercel_project" "curriculum_designer" {
  name      = "${var.project_name}-${var.environment}"
  framework = "nextjs"
  
  git_repository = {
    type = "github"
    repo = "${data.aws_ssm_parameter.github_org.value}/${data.aws_ssm_parameter.github_repo.value}"
  }
  
  # Use Vercel's default Next.js build process
  # build_command is automatically detected for Next.js
  # output_directory is automatically detected 
  # install_command is automatically detected
  
  environment = [
    {
      target = ["production", "preview", "development"]
      key    = "OPENAI_API_KEY"
      value  = data.aws_ssm_parameter.openai_api_key.value
    },
    {
      target = ["production", "preview", "development"]
      key    = "NEXTAUTH_URL"
      value  = "https://${var.environment}.${var.base_domain}"
    },
    {
      target = ["production", "preview", "development"]
      key    = "NEXTAUTH_SECRET"
      value  = data.aws_ssm_parameter.nextauth_secret.value
    },
    {
      target = ["production", "preview", "development"]
      key    = "ENVIRONMENT"
      value  = var.environment
    }
  ]
}

# Environment-specific subdomain
resource "vercel_project_domain" "environment_domain" {
  project_id = vercel_project.curriculum_designer.id
  domain     = "${var.environment}.${var.base_domain}"
}

# Outputs for manual setup
output "next_steps" {
  value = <<-EOT
    After Terraform apply:
    1. Go to Vercel Dashboard > Storage > Create Postgres Database
    2. Link it to your project: ${var.project_name}-${var.environment}
    3. Copy the connection strings from Vercel Dashboard
    4. Update environment variables in Vercel with the database URLs
    5. Run: npx prisma migrate dev locally
  EOT
}