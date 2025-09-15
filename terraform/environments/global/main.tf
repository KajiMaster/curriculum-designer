terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  backend "s3" {
    bucket = "terraform-state-curriculum-designer"
    key    = "global/terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region
}

# S3 Bucket for Terraform State
resource "aws_s3_bucket" "terraform_state" {
  bucket = "terraform-state-curriculum-designer"
  
  tags = {
    Name        = "Terraform State Bucket"
    Project     = "curriculum-designer"
    Environment = "global"
    ManagedBy   = "terraform"
  }
}

resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id
  
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id
  
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id
  
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# DynamoDB Table for State Locking
resource "aws_dynamodb_table" "terraform_locks" {
  name         = "terraform-locks-curriculum-designer"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"
  
  attribute {
    name = "LockID"
    type = "S"
  }
  
  tags = {
    Name        = "Terraform State Locks"
    Project     = "curriculum-designer"
    Environment = "global"
    ManagedBy   = "terraform"
  }
}

# ============================================
# GITHUB OIDC PROVIDER
# ============================================

# GitHub OIDC Identity Provider
resource "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"

  client_id_list = [
    "sts.amazonaws.com",
  ]

  thumbprint_list = [
    "6938fd4d98bab03faadb97b34396831e3780aea1",
    "1c58a3a8518e8759bf075b76b750d4f2df264fcd"
  ]

  tags = {
    Name        = "GitHub OIDC Provider"
    Project     = "curriculum-designer"
    Environment = "global"
    ManagedBy   = "terraform"
  }
}

# GitHub Actions Role for CI/CD
resource "aws_iam_role" "github_actions" {
  name = "curriculum-designer-github-actions"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = aws_iam_openid_connect_provider.github.arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          }
          StringLike = {
            "token.actions.githubusercontent.com:sub" = "repo:KajiMaster/curriculum-designer:*"
          }
        }
      }
    ]
  })

  tags = {
    Name        = "GitHub Actions Role"
    Project     = "curriculum-designer" 
    Environment = "global"
    ManagedBy   = "terraform"
  }
}

# Policy for GitHub Actions to deploy Lambda functions and manage infrastructure
resource "aws_iam_role_policy" "github_actions_lambda_deploy" {
  name = "curriculum-designer-github-actions-lambda-deploy"
  role = aws_iam_role.github_actions.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:UpdateFunctionCode",
          "lambda:UpdateFunctionConfiguration",
          "lambda:GetFunction",
          "lambda:GetFunctionConfiguration",
          "lambda:InvokeFunction",
          "lambda:CreateFunction",
          "lambda:DeleteFunction",
          "lambda:GetLayerVersion",
          "lambda:ListLayers",
          "lambda:ListLayerVersions",
          "lambda:AddPermission",
          "lambda:RemovePermission"
        ]
        Resource = [
          "arn:aws:lambda:us-east-1:*:function:curriculum-designer-webhook-*",
          "arn:aws:lambda:us-east-1:*:function:curriculum-activity-generator*",
          "arn:aws:lambda:us-east-1:*:layer:curriculum-*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::terraform-state-curriculum-designer",
          "arn:aws:s3:::terraform-state-curriculum-designer/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:CreateTable",
          "dynamodb:DeleteTable",
          "dynamodb:DescribeTable",
          "dynamodb:DescribeContinuousBackups",
          "dynamodb:DescribeTimeToLive",
          "dynamodb:UpdateContinuousBackups",
          "dynamodb:TagResource",
          "dynamodb:ListTagsOfResource",
          "dynamodb:UntagResource"
        ]
        Resource = [
          "arn:aws:dynamodb:us-east-1:*:table/curriculum-*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "iam:GetRole",
          "iam:PassRole",
          "iam:CreateRole",
          "iam:DeleteRole",
          "iam:AttachRolePolicy",
          "iam:DetachRolePolicy",
          "iam:PutRolePolicy",
          "iam:DeleteRolePolicy",
          "iam:GetRolePolicy",
          "iam:ListAttachedRolePolicies",
          "iam:ListRolePolicies",
          "iam:TagRole",
          "iam:UntagRole"
        ]
        Resource = [
          "arn:aws:iam::*:role/curriculum-*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:DeleteLogGroup",
          "logs:DescribeLogGroups",
          "logs:ListTagsForResource",
          "logs:TagResource",
          "logs:UntagResource",
          "logs:PutRetentionPolicy"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "apigateway:*"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters"
        ]
        Resource = [
          "arn:aws:ssm:us-east-1:*:parameter/global/curriculum-designer/*"
        ]
      }
    ]
  })
}

# Output the role ARN for GitHub Actions
output "github_actions_role_arn" {
  value = aws_iam_role.github_actions.arn
  description = "ARN of the IAM role for GitHub Actions"
}

# Parameter Store values are managed manually via AWS CLI  
# They already exist and don't need to be created by Terraform