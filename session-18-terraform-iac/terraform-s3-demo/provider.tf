terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.80"
    }
  }
}

# Using LocalStack (AWS emulator running on localhost:4566) instead of a real AWS account.
# For real AWS remove the endpoints/skip_* settings and the dummy keys - credentials come from `aws configure`.
provider "aws" {
  region                      = var.aws_region
  access_key                  = "test"
  secret_key                  = "test"
  s3_use_path_style           = true
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true

  endpoints {
    s3  = var.localstack_endpoint
    sts = var.localstack_endpoint
    iam = var.localstack_endpoint
  }

  default_tags {
    tags = {
      Project   = "devops-homework"
      ManagedBy = "terraform"
    }
  }
}
