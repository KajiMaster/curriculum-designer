terraform {
  backend "s3" {
    bucket = "terraform-state-curriculum-designer"
    key    = "terraform.tfstate"
    region = "us-east-1"
  }
}