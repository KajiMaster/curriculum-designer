variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "curriculum-designer"
}

# GitHub configuration is now stored in Parameter Store globally

variable "base_domain" {
  description = "Base domain for the application (environment will be prepended)"
  type        = string
}

variable "postgres_prisma_url" {
  description = "Vercel Postgres connection string (pooled)"
  type        = string
  default     = ""
}

variable "postgres_url_non_pooling" {
  description = "Vercel Postgres connection string (non-pooled for migrations)"
  type        = string
  default     = ""
}