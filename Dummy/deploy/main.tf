terraform {

  backend "s3" {
    bucket         = "fedrisk-api-tf-state-2025-05-01"
    key            = "fedrisk-api.tf-state"
    region         = "us-gov-east-1"
    encrypt        = true
    dynamodb_table = "fedrisk-api-tf-state-lock"
  }
}

provider "aws" {
  region = "us-gov-east-1"
}

locals {
  prefix = "${var.prefix}-${terraform.workspace}"
  common_tags = {
    Environment = terraform.workspace
    Project     = var.project
    Owner       = var.contact
    ManagedBy   = "Terraform"
  }
}

data "aws_region" "current" {}
