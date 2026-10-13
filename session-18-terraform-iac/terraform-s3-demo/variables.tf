variable "aws_region" {
  description = "AWS region to create resources in"
  type        = string
  default     = "ap-south-1"
}

variable "localstack_endpoint" {
  description = "LocalStack edge endpoint"
  type        = string
  default     = "http://localhost:4566"
}

variable "bucket_name" {
  description = "Name of the S3 bucket (must be globally unique on real AWS)"
  type        = string
}

variable "environment" {
  description = "Environment tag"
  type        = string
  default     = "dev"
}

variable "enable_versioning" {
  description = "Turn on S3 object versioning"
  type        = bool
  default     = true
}
