variable "aws_region" {
  description = "AWS region for Parameter Store"
  type        = string
  default     = "us-east-1"
}

variable "teacher_email" {
  description = "Teacher's email for board notifications"
  type        = string
  default     = ""
}

variable "enable_webhooks" {
  description = "Enable webhook integration"
  type        = bool
  default     = false
}

variable "webhook_url" {
  description = "URL for webhook callbacks"
  type        = string
  default     = "https://placeholder.com/webhook"
}