
# =============================================================================
# CORS FIXES - Replace broken OPTIONS integrations
# =============================================================================

# Fixed CORS integration for validate OPTIONS
resource "aws_api_gateway_integration" "cors_validate_fixed" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  resource_id = aws_api_gateway_resource.validate.id
  http_method = aws_api_gateway_method.cors_validate.http_method
  type        = "MOCK"
  
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
  
  depends_on = [aws_api_gateway_method.cors_validate]
}

# Fixed CORS integration for executions OPTIONS  
resource "aws_api_gateway_integration" "cors_executions_fixed" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  resource_id = aws_api_gateway_resource.executions.id
  http_method = aws_api_gateway_method.cors_executions.http_method
  type        = "MOCK"
  
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
  
  depends_on = [aws_api_gateway_method.cors_executions]
}

# Fixed CORS integration for results OPTIONS
resource "aws_api_gateway_integration" "cors_results_fixed" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  resource_id = aws_api_gateway_resource.results.id
  http_method = aws_api_gateway_method.cors_results.http_method
  type        = "MOCK"
  
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
  
  depends_on = [aws_api_gateway_method.cors_results]
}

# Fixed CORS integration responses
resource "aws_api_gateway_integration_response" "cors_validate_fixed_200" {
  depends_on = [aws_api_gateway_integration.cors_validate_fixed]
  
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

resource "aws_api_gateway_integration_response" "cors_executions_fixed_200" {
  depends_on = [aws_api_gateway_integration.cors_executions_fixed]
  
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

resource "aws_api_gateway_integration_response" "cors_results_fixed_200" {
  depends_on = [aws_api_gateway_integration.cors_results_fixed]
  
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

# Fix POST /validate integration response to include CORS headers
resource "aws_api_gateway_integration_response" "validate_post_cors" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  resource_id = aws_api_gateway_resource.validate.id
  http_method = aws_api_gateway_method.validate_post.http_method
  status_code = "200"
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = "'*'"
  }
  
  depends_on = [aws_api_gateway_integration.validate_post]
}

# Add method response for POST /validate CORS
resource "aws_api_gateway_method_response" "validate_post_cors" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  resource_id = aws_api_gateway_resource.validate.id
  http_method = aws_api_gateway_method.validate_post.http_method
  status_code = "200"
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = false
  }
}

# =============================================================================
# TENANTS ENDPOINT - Missing endpoint that causes 403
# =============================================================================

# /tenants resource
resource "aws_api_gateway_resource" "tenants" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  parent_id   = aws_api_gateway_resource.ksi.id
  path_part   = "tenants"
}

# GET /tenants method
resource "aws_api_gateway_method" "tenants_get" {
  rest_api_id   = aws_api_gateway_rest_api.ksi_api.id
  resource_id   = aws_api_gateway_resource.tenants.id
  http_method   = "GET"
  authorization = "NONE"
}

# OPTIONS /tenants method for CORS
resource "aws_api_gateway_method" "tenants_options" {
  rest_api_id   = aws_api_gateway_rest_api.ksi_api.id
  resource_id   = aws_api_gateway_resource.tenants.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

# Lambda function for tenants
resource "aws_lambda_function" "tenants" {
  function_name = "${var.project_name}-api-tenants-${var.environment}"
  role          = aws_iam_role.api_lambda_role.arn
  handler       = "tenants_lambda.lambda_handler"
  runtime       = var.lambda_runtime
  timeout       = var.lambda_timeout
  memory_size   = var.lambda_memory_size
  
  filename         = "tenants.zip"
  source_code_hash = filebase64sha256("tenants.zip")
  
  environment {
    variables = {
      ENVIRONMENT = var.environment
      TENANT_KSI_CONFIGURATIONS_TABLE = var.tenant_ksi_configurations_table_name
      AWS_REGION = var.aws_region
    }
  }
}

# Lambda permission
resource "aws_lambda_permission" "tenants_invoke" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.tenants.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.ksi_api.execution_arn}/*/*"
}

# GET integration
resource "aws_api_gateway_integration" "tenants_get" {
  rest_api_id             = aws_api_gateway_rest_api.ksi_api.id
  resource_id             = aws_api_gateway_resource.tenants.id
  http_method             = aws_api_gateway_method.tenants_get.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.tenants.invoke_arn
}

# OPTIONS integration for CORS
resource "aws_api_gateway_integration" "tenants_options" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  resource_id = aws_api_gateway_resource.tenants.id
  http_method = aws_api_gateway_method.tenants_options.http_method
  type        = "MOCK"
  
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

# Method responses
resource "aws_api_gateway_method_response" "tenants_get_200" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  resource_id = aws_api_gateway_resource.tenants.id
  http_method = aws_api_gateway_method.tenants_get.http_method
  status_code = "200"
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = false
  }
}

resource "aws_api_gateway_method_response" "tenants_options_200" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  resource_id = aws_api_gateway_resource.tenants.id
  http_method = aws_api_gateway_method.tenants_options.http_method
  status_code = "200"
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = false
    "method.response.header.Access-Control-Allow-Methods" = false
    "method.response.header.Access-Control-Allow-Origin"  = false
  }
}

# Integration responses
resource "aws_api_gateway_integration_response" "tenants_get_200" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  resource_id = aws_api_gateway_resource.tenants.id
  http_method = aws_api_gateway_method.tenants_get.http_method
  status_code = "200"
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = "'*'"
  }
  
  depends_on = [aws_api_gateway_integration.tenants_get]
}

resource "aws_api_gateway_integration_response" "tenants_options_200" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  resource_id = aws_api_gateway_resource.tenants.id
  http_method = aws_api_gateway_method.tenants_options.http_method
  status_code = "200"
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
  
  depends_on = [aws_api_gateway_integration.tenants_options]
}

# Add required variable
variable "tenant_ksi_configurations_table_name" {
  description = "Name of the tenant KSI configurations DynamoDB table"
  type        = string
  default     = "riskuity-ksi-validator-tenant-ksi-configurations-production"
}
