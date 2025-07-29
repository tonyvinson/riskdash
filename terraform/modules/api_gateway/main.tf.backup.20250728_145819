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
  description = "Policy for API Lambda functions to access DynamoDB table"
  
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
  handler       = "lambda_function.lambda_handler"
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
  handler       = "lambda_function.lambda_handler"
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
  handler       = "lambda_function.lambda_handler"
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

#  policy = jsonencode({
#    Version = "2012-10-17"
#    Statement = [
#      {
#        Effect = "Allow"
#        Principal = "*"
#        Action = "execute-api:Invoke"
#        Resource = "*"
#        Condition = {
#          StringEquals = {
#            "aws:SourceAccount" = data.aws_caller_identity.current.account_id
#          }
#        }
#      }
#    ]
#  })

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

# CORS OPTIONS methods
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

# CORS Integrations (Mock)
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
    "method.response.header.Access-Control-Allow-Headers" = false
    "method.response.header.Access-Control-Allow-Methods" = false
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_method_response" "cors_executions" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  resource_id = aws_api_gateway_resource.executions.id
  http_method = aws_api_gateway_method.cors_executions.http_method
  status_code = "200"
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = false
    "method.response.header.Access-Control-Allow-Methods" = false
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_method_response" "cors_results" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  resource_id = aws_api_gateway_resource.results.id
  http_method = aws_api_gateway_method.cors_results.http_method
  status_code = "200"
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = false
    "method.response.header.Access-Control-Allow-Methods" = false
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

# CORS Integration responses (fixed dependencies)
resource "aws_api_gateway_integration_response" "cors_validate" {
  depends_on = [aws_api_gateway_integration.cors_validate]
  
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
  depends_on = [aws_api_gateway_integration.cors_executions]
  
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
  depends_on = [aws_api_gateway_integration.cors_results]
  
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
  authorization = "NONE"  # Changed from AWS_IAM to NONE for easier testing
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
  authorization = "NONE"  # Changed from AWS_IAM to NONE for easier testing

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
  authorization = "NONE"  # Changed from AWS_IAM to NONE for easier testing

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
    "method.response.header.Access-Control-Allow-Origin" = false
  }
}

resource "aws_api_gateway_method_response" "executions_get_200" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  resource_id = aws_api_gateway_resource.executions.id
  http_method = aws_api_gateway_method.executions_get.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = false
  }
}

resource "aws_api_gateway_method_response" "results_get_200" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  resource_id = aws_api_gateway_resource.results.id
  http_method = aws_api_gateway_method.results_get.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = false
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
    aws_api_gateway_integration.results_get,
    aws_api_gateway_integration_response.cors_validate,
    aws_api_gateway_integration_response.cors_executions,
    aws_api_gateway_integration_response.cors_results
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

# API Gateway Stage (simplified - no CloudWatch logging to avoid role issues)
resource "aws_api_gateway_stage" "ksi_api" {
  deployment_id = aws_api_gateway_deployment.ksi_api.id
  rest_api_id   = aws_api_gateway_rest_api.ksi_api.id
  stage_name    = var.environment

  tags = {
    Name = "KSI API Stage"
    Environment = var.environment
  }
}

# CloudWatch Log Groups for Lambda functions only
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

# =============================================================================
# TENANT MANAGEMENT API ROUTES
# =============================================================================

# /api/tenant resource
resource "aws_api_gateway_resource" "tenant" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  parent_id   = aws_api_gateway_resource.api.id
  path_part   = "tenant"
}

# /api/tenant/generate-role-instructions
resource "aws_api_gateway_resource" "tenant_generate_role" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  parent_id   = aws_api_gateway_resource.tenant.id
  path_part   = "generate-role-instructions"
}

# /api/tenant/test-connection
resource "aws_api_gateway_resource" "tenant_test_connection" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  parent_id   = aws_api_gateway_resource.tenant.id
  path_part   = "test-connection"
}

# /api/tenant/onboard
resource "aws_api_gateway_resource" "tenant_onboard" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  parent_id   = aws_api_gateway_resource.tenant.id
  path_part   = "onboard"
}

# =============================================================================
# TENANT API METHODS
# =============================================================================

# POST /api/tenant/generate-role-instructions
resource "aws_api_gateway_method" "tenant_generate_role_post" {
  rest_api_id   = aws_api_gateway_rest_api.ksi_api.id
  resource_id   = aws_api_gateway_resource.tenant_generate_role.id
  http_method   = "POST"
  authorization = "NONE"
}

# POST /api/tenant/test-connection
resource "aws_api_gateway_method" "tenant_test_connection_post" {
  rest_api_id   = aws_api_gateway_rest_api.ksi_api.id
  resource_id   = aws_api_gateway_resource.tenant_test_connection.id
  http_method   = "POST"
  authorization = "NONE"
}

# POST /api/tenant/onboard
resource "aws_api_gateway_method" "tenant_onboard_post" {
  rest_api_id   = aws_api_gateway_rest_api.ksi_api.id
  resource_id   = aws_api_gateway_resource.tenant_onboard.id
  http_method   = "POST"
  authorization = "NONE"
}

# OPTIONS methods for CORS
resource "aws_api_gateway_method" "tenant_generate_role_options" {
  rest_api_id   = aws_api_gateway_rest_api.ksi_api.id
  resource_id   = aws_api_gateway_resource.tenant_generate_role.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_method" "tenant_test_connection_options" {
  rest_api_id   = aws_api_gateway_rest_api.ksi_api.id
  resource_id   = aws_api_gateway_resource.tenant_test_connection.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_method" "tenant_onboard_options" {
  rest_api_id   = aws_api_gateway_rest_api.ksi_api.id
  resource_id   = aws_api_gateway_resource.tenant_onboard.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

# =============================================================================
# LAMBDA INTEGRATIONS
# =============================================================================

# Integration for generate-role-instructions
resource "aws_api_gateway_integration" "tenant_generate_role_post" {
  rest_api_id             = aws_api_gateway_rest_api.ksi_api.id
  resource_id             = aws_api_gateway_resource.tenant_generate_role.id
  http_method             = aws_api_gateway_method.tenant_generate_role_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = "arn:aws-us-gov:apigateway:us-gov-west-1:lambda:path/2015-03-31/functions/arn:aws-us-gov:lambda:us-gov-west-1:736539455039:function:riskuity-ksi-validator-orchestrator-production/invocations"
}

# Integration for test-connection
resource "aws_api_gateway_integration" "tenant_test_connection_post" {
  rest_api_id             = aws_api_gateway_rest_api.ksi_api.id
  resource_id             = aws_api_gateway_resource.tenant_test_connection.id
  http_method             = aws_api_gateway_method.tenant_test_connection_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = "arn:aws-us-gov:apigateway:us-gov-west-1:lambda:path/2015-03-31/functions/arn:aws-us-gov:lambda:us-gov-west-1:736539455039:function:riskuity-ksi-validator-orchestrator-production/invocations"
}

# Integration for onboard
resource "aws_api_gateway_integration" "tenant_onboard_post" {
  rest_api_id             = aws_api_gateway_rest_api.ksi_api.id
  resource_id             = aws_api_gateway_resource.tenant_onboard.id
  http_method             = aws_api_gateway_method.tenant_onboard_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = "arn:aws-us-gov:apigateway:us-gov-west-1:lambda:path/2015-03-31/functions/arn:aws-us-gov:lambda:us-gov-west-1:736539455039:function:riskuity-ksi-validator-orchestrator-production/invocations"
}

# CORS integrations
resource "aws_api_gateway_integration" "tenant_generate_role_options" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  resource_id = aws_api_gateway_resource.tenant_generate_role.id
  http_method = aws_api_gateway_method.tenant_generate_role_options.http_method
  type        = "MOCK"
  
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_integration" "tenant_test_connection_options" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  resource_id = aws_api_gateway_resource.tenant_test_connection.id
  http_method = aws_api_gateway_method.tenant_test_connection_options.http_method
  type        = "MOCK"
  
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_integration" "tenant_onboard_options" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  resource_id = aws_api_gateway_resource.tenant_onboard.id
  http_method = aws_api_gateway_method.tenant_onboard_options.http_method
  type        = "MOCK"
  
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

# =============================================================================
# METHOD RESPONSES
# =============================================================================

resource "aws_api_gateway_method_response" "tenant_generate_role_post_200" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  resource_id = aws_api_gateway_resource.tenant_generate_role.id
  http_method = aws_api_gateway_method.tenant_generate_role_post.http_method
  status_code = "200"
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = false
  }
}

resource "aws_api_gateway_method_response" "tenant_test_connection_post_200" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  resource_id = aws_api_gateway_resource.tenant_test_connection.id
  http_method = aws_api_gateway_method.tenant_test_connection_post.http_method
  status_code = "200"
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = false
  }
}

resource "aws_api_gateway_method_response" "tenant_onboard_post_200" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  resource_id = aws_api_gateway_resource.tenant_onboard.id
  http_method = aws_api_gateway_method.tenant_onboard_post.http_method
  status_code = "200"
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = false
  }
}

# CORS method responses
resource "aws_api_gateway_method_response" "tenant_generate_role_options_200" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  resource_id = aws_api_gateway_resource.tenant_generate_role.id
  http_method = aws_api_gateway_method.tenant_generate_role_options.http_method
  status_code = "200"
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = false
    "method.response.header.Access-Control-Allow-Methods" = false
    "method.response.header.Access-Control-Allow-Origin"  = false
  }
}

resource "aws_api_gateway_method_response" "tenant_test_connection_options_200" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  resource_id = aws_api_gateway_resource.tenant_test_connection.id
  http_method = aws_api_gateway_method.tenant_test_connection_options.http_method
  status_code = "200"
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = false
    "method.response.header.Access-Control-Allow-Methods" = false
    "method.response.header.Access-Control-Allow-Origin"  = false
  }
}

resource "aws_api_gateway_method_response" "tenant_onboard_options_200" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  resource_id = aws_api_gateway_resource.tenant_onboard.id
  http_method = aws_api_gateway_method.tenant_onboard_options.http_method
  status_code = "200"
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = false
    "method.response.header.Access-Control-Allow-Methods" = false
    "method.response.header.Access-Control-Allow-Origin"  = false
  }
}

# =============================================================================
# INTEGRATION RESPONSES
# =============================================================================

resource "aws_api_gateway_integration_response" "tenant_generate_role_options" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  resource_id = aws_api_gateway_resource.tenant_generate_role.id
  http_method = aws_api_gateway_method.tenant_generate_role_options.http_method
  status_code = aws_api_gateway_method_response.tenant_generate_role_options_200.status_code
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'POST,OPTIONS'"
  }
}

resource "aws_api_gateway_integration_response" "tenant_test_connection_options" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  resource_id = aws_api_gateway_resource.tenant_test_connection.id
  http_method = aws_api_gateway_method.tenant_test_connection_options.http_method
  status_code = aws_api_gateway_method_response.tenant_test_connection_options_200.status_code
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'POST,OPTIONS'"
  }
}

resource "aws_api_gateway_integration_response" "tenant_onboard_options" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  resource_id = aws_api_gateway_resource.tenant_onboard.id
  http_method = aws_api_gateway_method.tenant_onboard_options.http_method
  status_code = aws_api_gateway_method_response.tenant_onboard_options_200.status_code
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'POST,OPTIONS'"
  }
}

# =============================================================================
# LAMBDA PERMISSIONS
# =============================================================================

# resource "aws_lambda_permission" "api_tenant_onboarding" {
#   statement_id  = "AllowExecutionFromAPIGateway"
#   action        = "lambda:InvokeFunction"
#   function_name = aws_lambda_function.api_validate.function_name
#   principal     = "apigateway.amazonaws.com"
#   source_arn    = "${aws_api_gateway_rest_api.ksi_api.execution_arn}/*/*"
# }

# Local values for API Gateway URLs
locals {
  api_base_url = "https://${aws_api_gateway_rest_api.ksi_api.id}.execute-api.${var.aws_region}.amazonaws.com/${aws_api_gateway_stage.ksi_api.stage_name}"
}

# =============================================================================
# LAMBDA PERMISSIONS FOR REAL FUNCTIONS
# =============================================================================

# Permission for orchestrator to be invoked by API Gateway
resource "aws_lambda_permission" "orchestrator_api_gateway" {
  statement_id  = "AllowExecutionFromAPIGatewayOrchestrator"
  action        = "lambda:InvokeFunction"
  function_name = "riskuity-ksi-validator-orchestrator-production"
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.ksi_api.execution_arn}/*/*"
}

# Permission for cross-account validator to be invoked by API Gateway  
resource "aws_lambda_permission" "cross_account_validator_api_gateway" {
  statement_id  = "AllowExecutionFromAPIGatewayCrossAccount"
  action        = "lambda:InvokeFunction"
  function_name = "riskuity-ksi-validator-cross-account-validator-production"
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.ksi_api.execution_arn}/*/*"
}
