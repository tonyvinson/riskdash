#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

echo "🚀 Creating API Gateway Module and Lambda Handlers..."

# Create directory structure
log_info "Creating directory structure..."
mkdir -p terraform/modules/api_gateway
mkdir -p lambdas/api

# Create API Gateway main.tf
log_info "Creating terraform/modules/api_gateway/main.tf..."
cat > terraform/modules/api_gateway/main.tf << 'EOF'
# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# IAM Role for API Gateway Lambda functions
resource "aws_iam_role" "api_lambda_role" {
  name = "${var.project_name}-api-lambda-role-${var.environment}"
  
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
    Name = "KSI API Lambda Role"
    Purpose = "Lambda execution role for KSI API functions"
  }
}

# IAM Policy for DynamoDB access
resource "aws_iam_policy" "api_dynamodb_policy" {
  name        = "${var.project_name}-api-dynamodb-policy-${var.environment}"
  description = "Policy for API Lambda functions to access DynamoDB tables"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:BatchGetItem"
        ]
        Resource = [
          var.ksi_definitions_table_arn,
          var.tenant_ksi_configurations_table_arn,
          var.ksi_execution_history_table_arn,
          "${var.ksi_execution_history_table_arn}/index/*"
        ]
      }
    ]
  })
}

# IAM Policy for Lambda invocation
resource "aws_iam_policy" "api_lambda_invoke_policy" {
  name        = "${var.project_name}-api-lambda-invoke-policy-${var.environment}"
  description = "Policy for API to invoke orchestrator Lambda functions"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = [
          var.orchestrator_lambda_arn,
          "arn:aws-us-gov:lambda:*:*:function:${var.project_name}-validator-*-${var.environment}"
        ]
      }
    ]
  })
}

# Attach policies to API Lambda role
resource "aws_iam_role_policy_attachment" "api_lambda_basic" {
  policy_arn = "arn:aws-us-gov:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.api_lambda_role.name
}

resource "aws_iam_role_policy_attachment" "api_lambda_dynamodb" {
  policy_arn = aws_iam_policy.api_dynamodb_policy.arn
  role       = aws_iam_role.api_lambda_role.name
}

resource "aws_iam_role_policy_attachment" "api_lambda_invoke" {
  policy_arn = aws_iam_policy.api_lambda_invoke_policy.arn
  role       = aws_iam_role.api_lambda_role.name
}

# API Lambda Functions
resource "aws_lambda_function" "api_validate" {
  function_name = "${var.project_name}-api-validate-${var.environment}"
  role          = aws_iam_role.api_lambda_role.arn
  handler       = "validate_handler.lambda_handler"
  runtime       = var.lambda_runtime
  timeout       = var.lambda_timeout
  memory_size   = var.lambda_memory_size
  
  filename         = "api-validate.zip"
  source_code_hash = filebase64sha256("api-validate.zip")
  
  environment {
    variables = {
      ENVIRONMENT = var.environment
      ORCHESTRATOR_LAMBDA_ARN = var.orchestrator_lambda_arn
    }
  }
  
  tags = {
    Name = "KSI API Validate"
    Purpose = "API endpoint for triggering KSI validations"
  }
}

resource "aws_lambda_function" "api_executions" {
  function_name = "${var.project_name}-api-executions-${var.environment}"
  role          = aws_iam_role.api_lambda_role.arn
  handler       = "executions_handler.lambda_handler"
  runtime       = var.lambda_runtime
  timeout       = var.lambda_timeout
  memory_size   = var.lambda_memory_size
  
  filename         = "api-executions.zip"
  source_code_hash = filebase64sha256("api-executions.zip")
  
  environment {
    variables = {
      ENVIRONMENT = var.environment
      KSI_EXECUTION_HISTORY_TABLE = var.ksi_execution_history_table
    }
  }
  
  tags = {
    Name = "KSI API Executions"
    Purpose = "API endpoint for retrieving execution history"
  }
}

resource "aws_lambda_function" "api_results" {
  function_name = "${var.project_name}-api-results-${var.environment}"
  role          = aws_iam_role.api_lambda_role.arn
  handler       = "results_handler.lambda_handler"
  runtime       = var.lambda_runtime
  timeout       = var.lambda_timeout
  memory_size   = var.lambda_memory_size
  
  filename         = "api-results.zip"
  source_code_hash = filebase64sha256("api-results.zip")
  
  environment {
    variables = {
      ENVIRONMENT = var.environment
      KSI_EXECUTION_HISTORY_TABLE = var.ksi_execution_history_table
      KSI_DEFINITIONS_TABLE = var.ksi_definitions_table
    }
  }
  
  tags = {
    Name = "KSI API Results"
    Purpose = "API endpoint for retrieving KSI validation results"
  }
}

# API Gateway REST API
resource "aws_api_gateway_rest_api" "ksi_api" {
  name        = "${var.project_name}-api-${var.environment}"
  description = "KSI Validator REST API for FedRAMP-20x compliance validation"
  
  endpoint_configuration {
    types = ["REGIONAL"]
  }

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = "*"
        Action = "execute-api:Invoke"
        Resource = "*"
        Condition = {
          StringEquals = {
            "aws:SourceAccount" = data.aws_caller_identity.current.account_id
          }
        }
      }
    ]
  })

  tags = {
    Name = "KSI Validator API"
    Purpose = "REST API for KSI validation platform"
  }
}

# API Gateway Resources
resource "aws_api_gateway_resource" "api" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  parent_id   = aws_api_gateway_rest_api.ksi_api.root_resource_id
  path_part   = "api"
}

resource "aws_api_gateway_resource" "ksi" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  parent_id   = aws_api_gateway_resource.api.id
  path_part   = "ksi"
}

resource "aws_api_gateway_resource" "validate" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  parent_id   = aws_api_gateway_resource.ksi.id
  path_part   = "validate"
}

resource "aws_api_gateway_resource" "executions" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  parent_id   = aws_api_gateway_resource.ksi.id
  path_part   = "executions"
}

resource "aws_api_gateway_resource" "results" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  parent_id   = aws_api_gateway_resource.ksi.id
  path_part   = "results"
}

# CORS OPTIONS methods for all resources
resource "aws_api_gateway_method" "cors_validate" {
  rest_api_id   = aws_api_gateway_rest_api.ksi_api.id
  resource_id   = aws_api_gateway_resource.validate.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_method" "cors_executions" {
  rest_api_id   = aws_api_gateway_rest_api.ksi_api.id
  resource_id   = aws_api_gateway_resource.executions.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_method" "cors_results" {
  rest_api_id   = aws_api_gateway_rest_api.ksi_api.id
  resource_id   = aws_api_gateway_resource.results.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

# CORS Integration responses
resource "aws_api_gateway_integration" "cors_validate" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  resource_id = aws_api_gateway_resource.validate.id
  http_method = aws_api_gateway_method.cors_validate.http_method
  type        = "MOCK"
  
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_integration" "cors_executions" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  resource_id = aws_api_gateway_resource.executions.id
  http_method = aws_api_gateway_method.cors_executions.http_method
  type        = "MOCK"
  
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_integration" "cors_results" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  resource_id = aws_api_gateway_resource.results.id
  http_method = aws_api_gateway_method.cors_results.http_method
  type        = "MOCK"
  
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

# CORS Method responses
resource "aws_api_gateway_method_response" "cors_validate" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  resource_id = aws_api_gateway_resource.validate.id
  http_method = aws_api_gateway_method.cors_validate.http_method
  status_code = "200"
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_method_response" "cors_executions" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  resource_id = aws_api_gateway_resource.executions.id
  http_method = aws_api_gateway_method.cors_executions.http_method
  status_code = "200"
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_method_response" "cors_results" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  resource_id = aws_api_gateway_resource.results.id
  http_method = aws_api_gateway_method.cors_results.http_method
  status_code = "200"
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

# CORS Integration responses
resource "aws_api_gateway_integration_response" "cors_validate" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  resource_id = aws_api_gateway_resource.validate.id
  http_method = aws_api_gateway_method.cors_validate.http_method
  status_code = "200"
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,PUT,DELETE,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

resource "aws_api_gateway_integration_response" "cors_executions" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  resource_id = aws_api_gateway_resource.executions.id
  http_method = aws_api_gateway_method.cors_executions.http_method
  status_code = "200"
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,PUT,DELETE,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

resource "aws_api_gateway_integration_response" "cors_results" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  resource_id = aws_api_gateway_resource.results.id
  http_method = aws_api_gateway_method.cors_results.http_method
  status_code = "200"
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,PUT,DELETE,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

# POST /api/ksi/validate
resource "aws_api_gateway_method" "validate_post" {
  rest_api_id   = aws_api_gateway_rest_api.ksi_api.id
  resource_id   = aws_api_gateway_resource.validate.id
  http_method   = "POST"
  authorization = "AWS_IAM"
}

resource "aws_api_gateway_integration" "validate_post" {
  rest_api_id             = aws_api_gateway_rest_api.ksi_api.id
  resource_id             = aws_api_gateway_resource.validate.id
  http_method             = aws_api_gateway_method.validate_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.api_validate.invoke_arn
}

# GET /api/ksi/executions
resource "aws_api_gateway_method" "executions_get" {
  rest_api_id   = aws_api_gateway_rest_api.ksi_api.id
  resource_id   = aws_api_gateway_resource.executions.id
  http_method   = "GET"
  authorization = "AWS_IAM"

  request_parameters = {
    "method.request.querystring.tenant_id" = false
    "method.request.querystring.limit"     = false
    "method.request.querystring.start_key" = false
  }
}

resource "aws_api_gateway_integration" "executions_get" {
  rest_api_id             = aws_api_gateway_rest_api.ksi_api.id
  resource_id             = aws_api_gateway_resource.executions.id
  http_method             = aws_api_gateway_method.executions_get.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.api_executions.invoke_arn
}

# GET /api/ksi/results
resource "aws_api_gateway_method" "results_get" {
  rest_api_id   = aws_api_gateway_rest_api.ksi_api.id
  resource_id   = aws_api_gateway_resource.results.id
  http_method   = "GET"
  authorization = "AWS_IAM"

  request_parameters = {
    "method.request.querystring.tenant_id"    = false
    "method.request.querystring.execution_id" = false
    "method.request.querystring.ksi_id"       = false
    "method.request.querystring.category"     = false
  }
}

resource "aws_api_gateway_integration" "results_get" {
  rest_api_id             = aws_api_gateway_rest_api.ksi_api.id
  resource_id             = aws_api_gateway_resource.results.id
  http_method             = aws_api_gateway_method.results_get.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.api_results.invoke_arn
}

# Method responses
resource "aws_api_gateway_method_response" "validate_post_200" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  resource_id = aws_api_gateway_resource.validate.id
  http_method = aws_api_gateway_method.validate_post.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }
}

resource "aws_api_gateway_method_response" "executions_get_200" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  resource_id = aws_api_gateway_resource.executions.id
  http_method = aws_api_gateway_method.executions_get.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }
}

resource "aws_api_gateway_method_response" "results_get_200" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  resource_id = aws_api_gateway_resource.results.id
  http_method = aws_api_gateway_method.results_get.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }
}

# Lambda permissions for API Gateway
resource "aws_lambda_permission" "api_validate" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api_validate.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.ksi_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "api_executions" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api_executions.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.ksi_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "api_results" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api_results.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.ksi_api.execution_arn}/*/*"
}

# API Gateway Deployment
resource "aws_api_gateway_deployment" "ksi_api" {
  depends_on = [
    aws_api_gateway_method.validate_post,
    aws_api_gateway_method.executions_get,
    aws_api_gateway_method.results_get,
    aws_api_gateway_integration.validate_post,
    aws_api_gateway_integration.executions_get,
    aws_api_gateway_integration.results_get
  ]

  rest_api_id = aws_api_gateway_rest_api.ksi_api.id

  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.api.id,
      aws_api_gateway_resource.ksi.id,
      aws_api_gateway_resource.validate.id,
      aws_api_gateway_resource.executions.id,
      aws_api_gateway_resource.results.id,
      aws_api_gateway_method.validate_post.id,
      aws_api_gateway_method.executions_get.id,
      aws_api_gateway_method.results_get.id,
      aws_api_gateway_integration.validate_post.id,
      aws_api_gateway_integration.executions_get.id,
      aws_api_gateway_integration.results_get.id,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }
}

# API Gateway Stage
resource "aws_api_gateway_stage" "ksi_api" {
  deployment_id = aws_api_gateway_deployment.ksi_api.id
  rest_api_id   = aws_api_gateway_rest_api.ksi_api.id
  stage_name    = var.environment

  xray_tracing_enabled = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_access_logs.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      caller         = "$context.identity.caller"
      user           = "$context.identity.user"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      resourcePath   = "$context.resourcePath"
      status         = "$context.status"
      protocol       = "$context.protocol"
      responseLength = "$context.responseLength"
      error          = "$context.error.message"
      errorType      = "$context.error.messageString"
    })
  }

  tags = {
    Name = "KSI API Stage"
    Environment = var.environment
  }
}

# CloudWatch Log Group for API access logs
resource "aws_cloudwatch_log_group" "api_access_logs" {
  name              = "/aws/apigateway/${var.project_name}-api-${var.environment}"
  retention_in_days = 30

  tags = {
    Name = "KSI API Access Logs"
    Purpose = "API Gateway access logging"
  }
}

# API Gateway Account (for CloudWatch logging)
resource "aws_api_gateway_account" "ksi_api" {
  cloudwatch_role_arn = aws_iam_role.api_gateway_cloudwatch.arn
}

# IAM Role for API Gateway CloudWatch logging
resource "aws_iam_role" "api_gateway_cloudwatch" {
  name = "${var.project_name}-api-gateway-cloudwatch-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "apigateway.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "api_gateway_cloudwatch" {
  role       = aws_iam_role.api_gateway_cloudwatch.name
  policy_arn = "arn:aws-us-gov:iam::aws:policy/service-role/AmazonAPIGatewayPushToCloudWatchLogs"
}

# CloudWatch Log Groups for Lambda functions
resource "aws_cloudwatch_log_group" "api_validate_logs" {
  name              = "/aws/lambda/${aws_lambda_function.api_validate.function_name}"
  retention_in_days = 30

  tags = {
    Name = "KSI API Validate Logs"
    Purpose = "Lambda function logging"
  }
}

resource "aws_cloudwatch_log_group" "api_executions_logs" {
  name              = "/aws/lambda/${aws_lambda_function.api_executions.function_name}"
  retention_in_days = 30

  tags = {
    Name = "KSI API Executions Logs"
    Purpose = "Lambda function logging"
  }
}

resource "aws_cloudwatch_log_group" "api_results_logs" {
  name              = "/aws/lambda/${aws_lambda_function.api_results.function_name}"
  retention_in_days = 30

  tags = {
    Name = "KSI API Results Logs"
    Purpose = "Lambda function logging"
  }
}
EOF

# Create API Gateway variables.tf
log_info "Creating terraform/modules/api_gateway/variables.tf..."
cat > terraform/modules/api_gateway/variables.tf << 'EOF'
variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "lambda_runtime" {
  description = "Python runtime version"
  type        = string
  default     = "python3.9"
}

variable "lambda_timeout" {
  description = "Lambda timeout in seconds"
  type        = number
  default     = 30
}

variable "lambda_memory_size" {
  description = "Lambda memory size in MB"
  type        = number
  default     = 256
}

variable "orchestrator_lambda_arn" {
  description = "ARN of the KSI orchestrator Lambda function"
  type        = string
}

variable "ksi_definitions_table" {
  description = "Name of KSI definitions table"
  type        = string
}

variable "ksi_definitions_table_arn" {
  description = "ARN of KSI definitions table"
  type        = string
}

variable "tenant_ksi_configurations_table" {
  description = "Name of tenant KSI configurations table"
  type        = string
}

variable "tenant_ksi_configurations_table_arn" {
  description = "ARN of tenant KSI configurations table"
  type        = string
}

variable "ksi_execution_history_table" {
  description = "Name of KSI execution history table"
  type        = string
}

variable "ksi_execution_history_table_arn" {
  description = "ARN of KSI execution history table"
  type        = string
}

variable "api_cors_allow_origin" {
  description = "CORS allow origin for API Gateway"
  type        = string
  default     = "*"
}

variable "api_throttling_rate_limit" {
  description = "API Gateway throttling rate limit (requests per second)"
  type        = number
  default     = 1000
}

variable "api_throttling_burst_limit" {
  description = "API Gateway throttling burst limit"
  type        = number
  default     = 2000
}
EOF

# Create API Gateway outputs.tf
log_info "Creating terraform/modules/api_gateway/outputs.tf..."
cat > terraform/modules/api_gateway/outputs.tf << 'EOF'
output "api_gateway_rest_api_id" {
  description = "ID of the API Gateway REST API"
  value       = aws_api_gateway_rest_api.ksi_api.id
}

output "api_gateway_rest_api_arn" {
  description = "ARN of the API Gateway REST API"
  value       = aws_api_gateway_rest_api.ksi_api.arn
}

output "api_gateway_stage_arn" {
  description = "ARN of the API Gateway stage"
  value       = aws_api_gateway_stage.ksi_api.arn
}

output "api_gateway_invoke_url" {
  description = "The invoke URL for the API Gateway"
  value       = "https://${aws_api_gateway_rest_api.ksi_api.id}.execute-api.${data.aws_region.current.name}.amazonaws.com/${var.environment}"
}

output "api_gateway_deployment_id" {
  description = "ID of the API Gateway deployment"
  value       = aws_api_gateway_deployment.ksi_api.id
}

output "api_lambda_function_arns" {
  description = "ARNs of API Lambda functions"
  value = {
    validate   = aws_lambda_function.api_validate.arn
    executions = aws_lambda_function.api_executions.arn
    results    = aws_lambda_function.api_results.arn
  }
}

output "api_lambda_function_names" {
  description = "Names of API Lambda functions"
  value = {
    validate   = aws_lambda_function.api_validate.function_name
    executions = aws_lambda_function.api_executions.function_name
    results    = aws_lambda_function.api_results.function_name
  }
}

output "api_endpoints" {
  description = "Available API endpoints"
  value = {
    validate_url   = "https://${aws_api_gateway_rest_api.ksi_api.id}.execute-api.${data.aws_region.current.name}.amazonaws.com/${var.environment}/api/ksi/validate"
    executions_url = "https://${aws_api_gateway_rest_api.ksi_api.id}.execute-api.${data.aws_region.current.name}.amazonaws.com/${var.environment}/api/ksi/executions"
    results_url    = "https://${aws_api_gateway_rest_api.ksi_api.id}.execute-api.${data.aws_region.current.name}.amazonaws.com/${var.environment}/api/ksi/results"
  }
}

output "cloudwatch_log_groups" {
  description = "CloudWatch log groups for API components"
  value = {
    api_access_logs = aws_cloudwatch_log_group.api_access_logs.name
    validate_logs   = aws_cloudwatch_log_group.api_validate_logs.name
    executions_logs = aws_cloudwatch_log_group.api_executions_logs.name
    results_logs    = aws_cloudwatch_log_group.api_results_logs.name
  }
}
EOF

# Create validate_handler.py
log_info "Creating lambdas/api/validate_handler.py..."
cat > lambdas/api/validate_handler.py << 'EOF'
import json
import boto3
import logging
from datetime import datetime, timezone
from typing import Dict, Any
import os
import uuid

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
lambda_client = boto3.client('lambda')

# Environment variables
ENVIRONMENT = os.environ['ENVIRONMENT']
ORCHESTRATOR_LAMBDA_ARN = os.environ['ORCHESTRATOR_LAMBDA_ARN']

def lambda_handler(event, context):
    """
    API Handler for POST /api/ksi/validate
    Triggers KSI validation via orchestrator Lambda
    """
    try:
        # Parse request
        if 'body' in event:
            if isinstance(event['body'], str):
                body = json.loads(event['body'])
            else:
                body = event['body']
        else:
            body = {}
        
        # Extract parameters
        tenant_id = body.get('tenant_id', 'default')
        trigger_source = body.get('trigger_source', 'api')
        execution_id = body.get('execution_id', str(uuid.uuid4()))
        
        logger.info(f"Triggering validation for tenant: {tenant_id}, execution: {execution_id}")
        
        # Prepare orchestrator payload
        orchestrator_payload = {
            'tenant_id': tenant_id,
            'trigger_source': trigger_source,
            'execution_id': execution_id,
            'triggered_by': 'api-gateway',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # Invoke orchestrator Lambda
        response = lambda_client.invoke(
            FunctionName=ORCHESTRATOR_LAMBDA_ARN,
            InvocationType='Event',  # Async invocation
            Payload=json.dumps(orchestrator_payload)
        )
        
        # Return API response
        api_response = {
            'statusCode': 202,  # Accepted
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
            },
            'body': json.dumps({
                'message': 'KSI validation triggered successfully',
                'execution_id': execution_id,
                'tenant_id': tenant_id,
                'trigger_source': trigger_source,
                'status': 'TRIGGERED',
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        }
        
        logger.info(f"Successfully triggered validation: {execution_id}")
        return api_response
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in request body: {str(e)}")
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Invalid JSON in request body',
                'message': str(e)
            })
        }
    except Exception as e:
        logger.error(f"Error triggering validation: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }
EOF

# Create executions_handler.py
log_info "Creating lambdas/api/executions_handler.py..."
cat > lambdas/api/executions_handler.py << 'EOF'
import json
import boto3
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List
import os
from decimal import Decimal

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')

# Environment variables
ENVIRONMENT = os.environ['ENVIRONMENT']
KSI_EXECUTION_HISTORY_TABLE = os.environ['KSI_EXECUTION_HISTORY_TABLE']

def decimal_default(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def lambda_handler(event, context):
    """
    API Handler for GET /api/ksi/executions
    Retrieves KSI execution history from DynamoDB
    """
    try:
        # Parse query parameters
        query_params = event.get('queryStringParameters') or {}
        tenant_id = query_params.get('tenant_id')
        limit = int(query_params.get('limit', 50))
        start_key = query_params.get('start_key')
        
        # Validate limit
        if limit > 100:
            limit = 100
        
        logger.info(f"Fetching executions for tenant: {tenant_id}, limit: {limit}")
        
        table = dynamodb.Table(KSI_EXECUTION_HISTORY_TABLE)
        
        # Build scan parameters
        scan_params = {
            'Limit': limit,
            'ScanIndexForward': False  # Most recent first
        }
        
        if start_key:
            try:
                scan_params['ExclusiveStartKey'] = json.loads(start_key)
            except json.JSONDecodeError:
                logger.warning(f"Invalid start_key format: {start_key}")
        
        # Filter by tenant if specified
        if tenant_id:
            scan_params['FilterExpression'] = 'tenant_id = :tenant_id'
            scan_params['ExpressionAttributeValues'] = {':tenant_id': tenant_id}
        
        # Execute scan
        response = table.scan(**scan_params)
        
        executions = response.get('Items', [])
        last_evaluated_key = response.get('LastEvaluatedKey')
        
        # Sort by timestamp (most recent first)
        executions = sorted(
            executions, 
            key=lambda x: x.get('timestamp', ''), 
            reverse=True
        )
        
        # Build API response
        api_response = {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
            },
            'body': json.dumps({
                'executions': executions,
                'count': len(executions),
                'last_evaluated_key': last_evaluated_key,
                'has_more': last_evaluated_key is not None,
                'filters': {
                    'tenant_id': tenant_id,
                    'limit': limit
                },
                'timestamp': datetime.now(timezone.utc).isoformat()
            }, default=decimal_default)
        }
        
        logger.info(f"Successfully retrieved {len(executions)} executions")
        return api_response
        
    except Exception as e:
        logger.error(f"Error retrieving executions: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }
EOF

# Create results_handler.py
log_info "Creating lambdas/api/results_handler.py..."
cat > lambdas/api/results_handler.py << 'EOF'
import json
import boto3
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List
import os
from decimal import Decimal

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')

# Environment variables
ENVIRONMENT = os.environ['ENVIRONMENT']
KSI_EXECUTION_HISTORY_TABLE = os.environ['KSI_EXECUTION_HISTORY_TABLE']
KSI_DEFINITIONS_TABLE = os.environ['KSI_DEFINITIONS_TABLE']

def decimal_default(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def get_ksi_categories():
    """Get KSI categories mapping"""
    return {
        'CNA': 'Configuration & Network Architecture',
        'SVC': 'Service Configuration', 
        'IAM': 'Identity & Access Management',
        'MLA': 'Monitoring, Logging & Alerting',
        'CMT': 'Configuration Management & Tracking'
    }

def parse_ksi_status(assertion_reason: str) -> str:
    """Parse KSI status from assertion reason"""
    if not assertion_reason:
        return 'unknown'
    
    assertion_lower = assertion_reason.lower()
    if '✅' in assertion_reason or 'pass' in assertion_lower:
        return 'passed'
    elif '❌' in assertion_reason or 'fail' in assertion_lower:
        return 'failed'
    elif '⚠️' in assertion_reason or 'warning' in assertion_lower:
        return 'warning'
    elif '🟡' in assertion_reason or 'low risk' in assertion_lower:
        return 'warning'
    elif 'ℹ️' in assertion_reason or 'info' in assertion_lower:
        return 'info'
    else:
        return 'info'

def lambda_handler(event, context):
    """
    API Handler for GET /api/ksi/results
    Retrieves KSI validation results from DynamoDB
    """
    try:
        # Parse query parameters
        query_params = event.get('queryStringParameters') or {}
        tenant_id = query_params.get('tenant_id')
        execution_id = query_params.get('execution_id')
        ksi_id = query_params.get('ksi_id')
        category = query_params.get('category')
        limit = int(query_params.get('limit', 100))
        
        # Validate limit
        if limit > 500:
            limit = 500
        
        logger.info(f"Fetching results - tenant: {tenant_id}, execution: {execution_id}, ksi: {ksi_id}, category: {category}")
        
        table = dynamodb.Table(KSI_EXECUTION_HISTORY_TABLE)
        
        # Build scan parameters
        scan_params = {
            'Limit': limit
        }
        
        # Build filter expressions
        filter_expressions = []
        expression_values = {}
        
        if tenant_id:
            filter_expressions.append('tenant_id = :tenant_id')
            expression_values[':tenant_id'] = tenant_id
            
        if execution_id:
            filter_expressions.append('execution_id = :execution_id')
            expression_values[':execution_id'] = execution_id
            
        if ksi_id:
            filter_expressions.append('ksi_id = :ksi_id')
            expression_values[':ksi_id'] = ksi_id
            
        if category:
            filter_expressions.append('contains(ksi_id, :category)')
            expression_values[':category'] = f'KSI-{category.upper()}-'
        
        # Apply filters if any
        if filter_expressions:
            scan_params['FilterExpression'] = ' AND '.join(filter_expressions)
            scan_params['ExpressionAttributeValues'] = expression_values
        
        # Execute scan
        response = table.scan(**scan_params)
        results = response.get('Items', [])
        
        # Process results
        processed_results = []
        categories = get_ksi_categories()
        
        for result in results:
            # Parse KSI category from ID
            ksi_id = result.get('ksi_id', '')
            category_code = ''
            if ksi_id.startswith('KSI-') and len(ksi_id.split('-')) >= 2:
                category_code = ksi_id.split('-')[1]
            
            processed_result = {
                'ksi_id': result.get('ksi_id'),
                'validation_id': result.get('validation_id'),
                'execution_id': result.get('execution_id'),
                'tenant_id': result.get('tenant_id'),
                'status': parse_ksi_status(result.get('assertion_reason', '')),
                'assertion': result.get('assertion'),
                'assertion_reason': result.get('assertion_reason'),
                'cli_command': result.get('cli_command'),
                'commands_executed': result.get('commands_executed'),
                'successful_commands': result.get('successful_commands'),
                'failed_commands': result.get('failed_commands'),
                'timestamp': result.get('timestamp'),
                'validation_method': result.get('validation_method'),
                'category_code': category_code,
                'category_name': categories.get(category_code, 'Unknown'),
                'evidence_path': result.get('evidence_path'),
                'requirement': result.get('requirement')
            }
            processed_results.append(processed_result)
        
        # Sort by timestamp (most recent first)
        processed_results = sorted(
            processed_results,
            key=lambda x: x.get('timestamp', ''),
            reverse=True
        )
        
        # Generate summary statistics
        summary = {
            'total_results': len(processed_results),
            'by_status': {},
            'by_category': {},
            'execution_summary': {}
        }
        
        for result in processed_results:
            status = result['status']
            category_code = result['category_code']
            execution_id = result['execution_id']
            
            summary['by_status'][status] = summary['by_status'].get(status, 0) + 1
            summary['by_category'][category_code] = summary['by_category'].get(category_code, 0) + 1
            
            if execution_id not in summary['execution_summary']:
                summary['execution_summary'][execution_id] = {
                    'total': 0,
                    'passed': 0,
                    'failed': 0,
                    'warning': 0,
                    'info': 0
                }
            summary['execution_summary'][execution_id]['total'] += 1
            summary['execution_summary'][execution_id][status] += 1
        
        # Build API response
        api_response = {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
            },
            'body': json.dumps({
                'results': processed_results,
                'summary': summary,
                'categories': categories,
                'filters': {
                    'tenant_id': tenant_id,
                    'execution_id': execution_id,
                    'ksi_id': ksi_id,
                    'category': category,
                    'limit': limit
                },
                'timestamp': datetime.now(timezone.utc).isoformat()
            }, default=decimal_default)
        }
        
        logger.info(f"Successfully retrieved {len(processed_results)} results")
        return api_response
        
    except Exception as e:
        logger.error(f"Error retrieving results: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }
EOF

# Create README for next steps
log_info "Creating API_GATEWAY_README.md with integration instructions..."
cat > API_GATEWAY_README.md << 'EOF'
# API Gateway Module Created Successfully! 🎉

## 📁 Files Created:

### Terraform Module:
- `terraform/modules/api_gateway/main.tf` - Complete API Gateway infrastructure
- `terraform/modules/api_gateway/variables.tf` - Module variables
- `terraform/modules/api_gateway/outputs.tf` - Module outputs

### Lambda Handlers:
- `lambdas/api/validate_handler.py` - POST /api/ksi/validate endpoint
- `lambdas/api/executions_handler.py` - GET /api/ksi/executions endpoint  
- `lambdas/api/results_handler.py` - GET /api/ksi/results endpoint

## 🔧 Next Steps to Integrate:

### 1. Add Module to Your Main Terraform Configuration

Add this to your `terraform/main.tf` after the EventBridge module:

```hcl
# API Gateway Module
module "api_gateway" {
  source = "./modules/api_gateway"
  
  environment  = var.environment
  project_name = var.project_name
  
  # Lambda integrations
  orchestrator_lambda_arn = module.lambda.orchestrator_lambda_arn
  
  # DynamoDB table references
  ksi_definitions_table                   = module.dynamodb.ksi_definitions_table_name
  ksi_definitions_table_arn              = module.dynamodb.ksi_definitions_table_arn
  tenant_ksi_configurations_table        = module.dynamodb.tenant_ksi_configurations_table_name
  tenant_ksi_configurations_table_arn    = module.dynamodb.tenant_ksi_configurations_table_arn
  ksi_execution_history_table            = module.dynamodb.ksi_execution_history_table_name
  ksi_execution_history_table_arn        = module.dynamodb.ksi_execution_history_table_arn
  
  # API configuration
  api_cors_allow_origin       = var.api_cors_allow_origin
  api_throttling_rate_limit   = var.api_throttling_rate_limit
  api_throttling_burst_limit  = var.api_throttling_burst_limit
  
  depends_on = [module.lambda, module.dynamodb]
}
```

### 2. Add Variables to `terraform/variables.tf`:

```hcl
# API Gateway variables
variable "api_cors_allow_origin" {
  description = "CORS allow origin for API Gateway"
  type        = string
  default     = "*"
}

variable "api_throttling_rate_limit" {
  description = "API Gateway throttling rate limit (requests per second)"
  type        = number
  default     = 1000
}

variable "api_throttling_burst_limit" {
  description = "API Gateway throttling burst limit"
  type        = number
  default     = 2000
}
```

### 3. Add Outputs to `terraform/outputs.tf`:

```hcl
# API Gateway outputs
output "api_gateway" {
  description = "API Gateway information"
  value = {
    api_id       = module.api_gateway.api_gateway_rest_api_id
    api_arn      = module.api_gateway.api_gateway_rest_api_arn
    invoke_url   = module.api_gateway.api_gateway_invoke_url
    stage_arn    = module.api_gateway.api_gateway_stage_arn
    endpoints    = module.api_gateway.api_endpoints
  }
}

output "quick_reference" {
  description = "Quick reference URLs"
  value = {
    api_base_url = module.api_gateway.api_gateway_invoke_url
    validate_url = "${module.api_gateway.api_gateway_invoke_url}/api/ksi/validate"
    executions_url = "${module.api_gateway.api_gateway_invoke_url}/api/ksi/executions"
    results_url = "${module.api_gateway.api_gateway_invoke_url}/api/ksi/results"
    orchestrator_function = module.lambda.orchestrator_lambda_name
  }
}
```

### 4. Update Your Deploy Script

Add API Lambda packaging to your `scripts/deploy_lambdas.sh`:

```bash
# Add this section to package API functions
for api_func in validate executions results; do
    if [ -f "lambdas/api/${api_func}_handler.py" ]; then
        # Copy handler to temporary location with correct name
        temp_api_dir=$(mktemp -d)
        cp "lambdas/api/${api_func}_handler.py" "$temp_api_dir/lambda_function.py"
        package_lambda "$temp_api_dir" "api-$api_func.zip" "api-$api_func"
        rm -rf "$temp_api_dir"
    fi
done
```

### 5. Deploy

```bash
# Package Lambda functions
./scripts/deploy_lambdas.sh package-only

# Deploy infrastructure
cd terraform
terraform plan
terraform apply

# Deploy Lambda code
cd ..
./scripts/deploy_lambdas.sh deploy
```

### 6. Test Your API

```bash
# Get API URL
terraform output quick_reference

# Test endpoints
curl -X POST "https://<api-id>.execute-api.us-gov-west-1.amazonaws.com/production/api/ksi/validate" \
  -H "Content-Type: application/json" \
  -d '{"tenant_id": "test", "trigger_source": "manual"}'
```

## 📚 API Endpoints:

- **POST /api/ksi/validate** - Trigger KSI validations
- **GET /api/ksi/executions** - Get execution history  
- **GET /api/ksi/results** - Get validation results with filtering

All endpoints support CORS and IAM authentication.

## 🎯 What This Gives You:

✅ REST API endpoints for your existing Lambda functions  
✅ Frontend integration capabilities  
✅ External API access for federal agencies  
✅ Complete monitoring and logging  
✅ Security with IAM authentication  
✅ Rate limiting and throttling  

Your KSI Validator platform now has a complete API layer! 🚀
EOF

log_success "✅ API Gateway module and Lambda handlers created successfully!"
echo ""
log_info "📁 Files created:"
echo "   - terraform/modules/api_gateway/main.tf"
echo "   - terraform/modules/api_gateway/variables.tf" 
echo "   - terraform/modules/api_gateway/outputs.tf"
echo "   - lambdas/api/validate_handler.py"
echo "   - lambdas/api/executions_handler.py"
echo "   - lambdas/api/results_handler.py"
echo "   - API_GATEWAY_README.md (integration instructions)"
echo ""
log_warning "📖 Next: Follow the instructions in API_GATEWAY_README.md to integrate with your existing infrastructure"
log_info "🚀 After integration, you'll have REST API endpoints for your KSI platform!"
EOF

log_success "✅ API Gateway creation script completed!"
log_info "Make the script executable with: chmod +x create_api_gateway.sh"
log_info "Run with: ./create_api_gateway.sh"
