# IAM Role for KSI Orchestrator
resource "aws_iam_role" "ksi_orchestrator_role" {
  name = "${var.project_name}-orchestrator-role-${var.environment}"
  
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
    Name = "KSI Orchestrator Role"
    Purpose = "Lambda execution role for KSI orchestrator"
  }
}

# IAM Policy for DynamoDB access
resource "aws_iam_policy" "ksi_dynamodb_policy" {
  name        = "${var.project_name}-dynamodb-policy-${var.environment}"
  description = "Policy for KSI Lambda functions to access DynamoDB tables"
  
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
          var.ksi_definitions_table_arn,
          var.tenant_ksi_configurations_table_arn,
          var.ksi_execution_history_table_arn,
          "${var.ksi_execution_history_table_arn}/index/*",
          var.tenant_metadata_table_arn,
          "${var.tenant_metadata_table_arn}/index/*"
        ]
      }
    ]
  })
}

# IAM Policy for Lambda invocation
resource "aws_iam_policy" "ksi_lambda_invoke_policy" {
  name        = "${var.project_name}-lambda-invoke-policy-${var.environment}"
  description = "Policy for orchestrator to invoke validator Lambda functions"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = [
          "arn:aws-us-gov:lambda:*:*:function:${var.project_name}-validator-*-${var.environment}"
        ]
      }
    ]
  })
}

# Attach policies to orchestrator role
resource "aws_iam_role_policy_attachment" "orchestrator_basic" {
  policy_arn = "arn:aws-us-gov:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.ksi_orchestrator_role.name
}

resource "aws_iam_role_policy_attachment" "orchestrator_dynamodb" {
  policy_arn = aws_iam_policy.ksi_dynamodb_policy.arn
  role       = aws_iam_role.ksi_orchestrator_role.name
}

resource "aws_iam_role_policy_attachment" "orchestrator_lambda_invoke" {
  policy_arn = aws_iam_policy.ksi_lambda_invoke_policy.arn
  role       = aws_iam_role.ksi_orchestrator_role.name
}

# KSI Orchestrator Lambda Function
resource "aws_lambda_function" "ksi_orchestrator" {
  function_name = "${var.project_name}-orchestrator-${var.environment}"
  role          = aws_iam_role.ksi_orchestrator_role.arn
  handler       = "orchestrator_handler.lambda_handler"
  runtime       = var.lambda_runtime
  timeout       = var.lambda_timeout
  memory_size   = var.lambda_memory_size
  
  filename         = "orchestrator.zip"
  source_code_hash = filebase64sha256("orchestrator.zip")
  
  environment {
    variables = {
      ENVIRONMENT = var.environment
      KSI_DEFINITIONS_TABLE = var.ksi_definitions_table
      TENANT_KSI_CONFIGURATIONS_TABLE = var.tenant_ksi_configurations_table
      KSI_EXECUTION_HISTORY_TABLE = var.ksi_execution_history_table
      TENANT_CONFIG_TABLE = "${var.project_name}-tenant-metadata-${var.environment}"
      VALIDATOR_FUNCTION_PREFIX = "${var.project_name}-validator"
    }
  }
  
  tags = {
    Name = "KSI Orchestrator"
    Purpose = "Orchestrate KSI validation workflows"
  }
}

# Validator Lambda Functions
locals {
  validators = ["cna", "svc", "iam", "mla", "cmt"]
}

resource "aws_lambda_function" "ksi_validators" {
  for_each = toset(local.validators)
  
  function_name = "${var.project_name}-validator-${each.key}-${var.environment}"
  role          = aws_iam_role.ksi_orchestrator_role.arn
  handler       = "handler.lambda_handler"
  runtime       = var.lambda_runtime
  timeout       = var.lambda_timeout
  memory_size   = var.lambda_memory_size
  
  filename         = "validator-${each.key}.zip"
  source_code_hash = filebase64sha256("validator-${each.key}.zip")
  
  environment {
    variables = {
      ENVIRONMENT = var.environment
      VALIDATOR_TYPE = upper(each.key)
      KSI_DEFINITIONS_TABLE = var.ksi_definitions_table
      KSI_EXECUTION_HISTORY_TABLE = var.ksi_execution_history_table
      TENANT_CONFIG_TABLE = var.tenant_ksi_configurations_table
    }
  }
  
  tags = {
    Name = "KSI Validator ${upper(each.key)}"
    Purpose = "Validate ${upper(each.key)} category KSIs"
  }
}
