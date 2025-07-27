# Tenant Management Module - integrates with existing KSI Validator architecture

# Get current AWS account info and region
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# Determine the correct partition based on region
locals {
  aws_partition = startswith(data.aws_region.current.name, "us-gov-") ? "aws-us-gov" : "aws"
}

# Tenant Metadata Table - NEW for SaaS functionality
resource "aws_dynamodb_table" "tenant_metadata" {
  name           = "${var.project_name}-tenant-metadata-${var.environment}"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "tenant_id"
  
  attribute {
    name = "tenant_id"
    type = "S"
  }
  
  # Global Secondary Index for querying by organization type
  attribute {
    name = "tenant_type"
    type = "S"
  }
  
  attribute {
    name = "onboarding_status"
    type = "S"
  }
  
  global_secondary_index {
    name     = "tenant-type-index"
    hash_key = "tenant_type"
    range_key = "onboarding_status"
    projection_type = "ALL"
  }
  
  point_in_time_recovery {
    enabled = true
  }
  
  server_side_encryption {
    enabled = true
  }
  
  tags = {
    Name = "Tenant Metadata"
    Purpose = "Store comprehensive tenant information for SaaS KSI validation"
  }
}

# IAM Role for Tenant Onboarding API
resource "aws_iam_role" "tenant_onboarding_role" {
  name = "${var.project_name}-tenant-onboarding-role-${var.environment}"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
  
  tags = {
    Name = "Tenant Onboarding Role"
    Purpose = "Lambda execution role for tenant onboarding API"
  }
}

# IAM Policy for Tenant Metadata Access
resource "aws_iam_policy" "tenant_metadata_policy" {
  name        = "${var.project_name}-tenant-metadata-policy-${var.environment}"
  description = "Policy for accessing tenant metadata table"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:BatchGetItem",
          "dynamodb:BatchWriteItem"
        ]
        Resource = [
          aws_dynamodb_table.tenant_metadata.arn,
          "${aws_dynamodb_table.tenant_metadata.arn}/index/*",
          var.tenant_ksi_configurations_table_arn,
          "${var.tenant_ksi_configurations_table_arn}/index/*"
        ]
      }
    ]
  })
}

# IAM Policy for Cross-Account Role Assumption - FIXED FOR GOVCLOUD
resource "aws_iam_policy" "cross_account_assume_policy" {
  name        = "${var.project_name}-cross-account-assume-policy-${var.environment}"
  description = "Policy for assuming roles in customer accounts"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sts:AssumeRole"
        ]
        Resource = "arn:${local.aws_partition}:iam::*:role/RiskuityKSIValidatorRole"
        Condition = {
          StringEquals = {
            "sts:ExternalId" = "riskuity-*"
          }
        }
      }
    ]
  })
}

# Attach policies to tenant onboarding role
resource "aws_iam_role_policy_attachment" "tenant_onboarding_basic" {
  role       = aws_iam_role.tenant_onboarding_role.name
  policy_arn = "arn:${local.aws_partition}:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "tenant_onboarding_metadata" {
  role       = aws_iam_role.tenant_onboarding_role.name
  policy_arn = aws_iam_policy.tenant_metadata_policy.arn
}

resource "aws_iam_role_policy_attachment" "tenant_onboarding_assume" {
  role       = aws_iam_role.tenant_onboarding_role.name
  policy_arn = aws_iam_policy.cross_account_assume_policy.arn
}

# Lambda Function for Tenant Onboarding API
resource "aws_lambda_function" "tenant_onboarding_api" {
  filename         = "${path.module}/../../lambda_packages/tenant_onboarding_api.zip"
  function_name    = "${var.project_name}-tenant-onboarding-api-${var.environment}"
  role            = aws_iam_role.tenant_onboarding_role.arn
  handler         = "tenant_onboarding_api.lambda_handler"
  runtime         = "python3.11"
  timeout         = 30
  memory_size     = 256
  source_code_hash = filebase64sha256("${path.module}/../../lambda_packages/tenant_onboarding_api.zip")
  
  environment {
    variables = {
      TENANT_METADATA_TABLE = aws_dynamodb_table.tenant_metadata.name
      TENANT_KSI_CONFIGURATIONS_TABLE = var.tenant_ksi_configurations_table_name
      RISKUITY_ACCOUNT_ID = data.aws_caller_identity.current.account_id
      ENVIRONMENT = var.environment
      PROJECT_NAME = var.project_name
    }
  }
  
  tags = {
    Name = "Tenant Onboarding API"
    Purpose = "Handle tenant registration and AWS role setup"
  }
  
  depends_on = [aws_iam_role_policy_attachment.tenant_onboarding_basic]
}

# IAM Role for Cross-Account KSI Validator
resource "aws_iam_role" "cross_account_validator_role" {
  name = "${var.project_name}-cross-account-validator-role-${var.environment}"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
  
  tags = {
    Name = "Cross-Account Validator Role"
    Purpose = "Lambda execution role for cross-account KSI validation"
  }
}

# Enhanced Cross-Account KSI Validator
resource "aws_lambda_function" "cross_account_ksi_validator" {
  filename         = "${path.module}/../../lambda_packages/cross_account_ksi_validator.zip"
  function_name    = "${var.project_name}-cross-account-validator-${var.environment}"
  role            = aws_iam_role.cross_account_validator_role.arn
  handler         = "cross_account_ksi_validator.lambda_handler"
  runtime         = "python3.11"
  timeout         = 900  # 15 minutes for cross-account operations
  memory_size     = 512
  source_code_hash = filebase64sha256("${path.module}/../../lambda_packages/cross_account_ksi_validator.zip")
  
  environment {
    variables = {
      TENANT_METADATA_TABLE = aws_dynamodb_table.tenant_metadata.name
      TENANT_KSI_CONFIGURATIONS_TABLE = var.tenant_ksi_configurations_table_name
      KSI_EXECUTION_HISTORY_TABLE = var.ksi_execution_history_table_name
      RISKUITY_ACCOUNT_ID = data.aws_caller_identity.current.account_id
      ENVIRONMENT = var.environment
      PROJECT_NAME = var.project_name
    }
  }
  
  tags = {
    Name = "Cross-Account KSI Validator"
    Purpose = "Validate KSIs across customer AWS accounts"
  }
  
  depends_on = [aws_iam_role_policy_attachment.cross_account_validator_basic]
}

# Attach policies to cross-account validator role
resource "aws_iam_role_policy_attachment" "cross_account_validator_basic" {
  role       = aws_iam_role.cross_account_validator_role.name
  policy_arn = "arn:${local.aws_partition}:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "cross_account_validator_metadata" {
  role       = aws_iam_role.cross_account_validator_role.name
  policy_arn = aws_iam_policy.tenant_metadata_policy.arn
}

resource "aws_iam_role_policy_attachment" "cross_account_validator_assume" {
  role       = aws_iam_role.cross_account_validator_role.name
  policy_arn = aws_iam_policy.cross_account_assume_policy.arn
}

# EventBridge Rule for Scheduled Multi-Tenant Validation
resource "aws_cloudwatch_event_rule" "scheduled_multi_tenant_validation" {
  name        = "${var.project_name}-multi-tenant-validation-${var.environment}"
  description = "Trigger KSI validation for all active tenants"
  
  schedule_expression = "rate(1 hour)"  # Run every hour
  
  tags = {
    Name = "Scheduled Multi-Tenant Validation"
    Purpose = "Automated validation scheduling for all tenants"
  }
}

resource "aws_cloudwatch_event_target" "cross_account_validator_target" {
  rule      = aws_cloudwatch_event_rule.scheduled_multi_tenant_validation.name
  target_id = "CrossAccountValidatorTarget"
  arn       = aws_lambda_function.cross_account_ksi_validator.arn
  
  input = jsonencode({
    "trigger_source" = "scheduled"
    "validate_all_tenants" = true
  })
}

resource "aws_lambda_permission" "allow_eventbridge_cross_account" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.cross_account_ksi_validator.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.scheduled_multi_tenant_validation.arn
}
