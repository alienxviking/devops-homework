terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.70"
    }
  }
}

# Credentials come from `aws configure` (IAM user terraform-student) - never hard-coded here.
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project   = "devops-homework"
      ManagedBy = "terraform"
    }
  }
}
