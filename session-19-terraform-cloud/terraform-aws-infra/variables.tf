variable "aws_region" {
  type    = string
  default = "ap-south-1"
}

variable "localstack_endpoint" {
  type    = string
  default = "http://localhost:4566"
}

variable "project" {
  type    = string
  default = "yatri"
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.10.0.0/16"
}

variable "public_subnet_cidr" {
  type    = string
  default = "10.10.1.0/24"
}

variable "private_subnet_cidr" {
  type    = string
  default = "10.10.2.0/24"
}

variable "instance_type" {
  type    = string
  default = "t3.micro"

  validation {
    condition     = can(regex("^t3[.]", var.instance_type))
    error_message = "Only t3 instance types are allowed in this project."
  }
}

variable "allowed_ssh_cidr" {
  description = "Who can SSH to the web server"
  type        = string
  default     = "203.0.113.10/32"
}
