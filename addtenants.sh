#!/bin/bash
# add-tenants-resources.sh - Add missing tenants resources to main.tf
set -e

echo "🔧 Adding missing tenants resources to main.tf..."

cd terraform/modules/api_gateway

# Backup current main.tf
cp main.tf main.tf.backup.$(date +%Y%m%d_%H%M%S)

# Add the complete tenants endpoint resources to main.tf
cat >> main.tf << 'EOF'

# =============================================================================
# TENANTS ENDPOINT (/api/ksi/tenants)
# =============================================================================

# /api/ksi/tenants resource
resource "aws_api_gateway_resource" "tenants" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  parent_id   = aws_api_gateway_resource.ksi.id
  path_part   = "tenants"
}

# GET /api/ksi/tenants method
resource "aws_api_gateway_method" "tenants_get" {
  rest_api_id   = aws_api_gateway_rest_api.ksi_api.id
  resource_id   = aws_api_gateway_resource.tenants.id
  http_method   = "GET"
  authorization = "NONE"
}

# OPTIONS /api/ksi/tenants method for CORS
resource "aws_api_gateway_method" "tenants_options" {
  rest_api_id   = aws_api_gateway_rest_api.ksi_api.id
  resource_id   = aws_api_gateway_resource.tenants.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

# Lambda function for tenants endpoint
resource "aws_lambda_function" "api_tenants" {
  function_name = "${var.project_name}-api-tenants-${var.environment}"
  role          = aws_iam_role.api_lambda_role.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = var.lambda_runtime
  timeout       = var.lambda_timeout
  memory_size   = var.lambda_memory_size
  
  filename         = "api-tenants.zip"
  source_code_hash = filebase64sha256("api-tenants.zip")
  
  environment {
    variables = {
      ENVIRONMENT = var.environment
      TENANT_KSI_CONFIGURATIONS_TABLE = var.tenant_ksi_configurations_table
    }
  }
  
  tags = {
    Name = "KSI API Tenants"
    Purpose = "API endpoint for retrieving tenant list"
  }
}

# CloudWatch Log Group for tenants Lambda
resource "aws_cloudwatch_log_group" "api_tenants_logs" {
  name              = "/aws/lambda/${aws_lambda_function.api_tenants.function_name}"
  retention_in_days = 14
  
  tags = {
    Name = "KSI API Tenants Logs"
    Purpose = "Log group for tenants API endpoint"
  }
}

# Lambda integration for GET /api/ksi/tenants
resource "aws_api_gateway_integration" "tenants_get" {
  rest_api_id             = aws_api_gateway_rest_api.ksi_api.id
  resource_id             = aws_api_gateway_resource.tenants.id
  http_method             = aws_api_gateway_method.tenants_get.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.api_tenants.invoke_arn
}

# CORS integration for OPTIONS /api/ksi/tenants
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
resource "aws_api_gateway_integration_response" "tenants_options" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  resource_id = aws_api_gateway_resource.tenants.id
  http_method = aws_api_gateway_method.tenants_options.http_method
  status_code = aws_api_gateway_method_response.tenants_options_200.status_code
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS'"
  }
}

# Lambda permission for API Gateway
resource "aws_lambda_permission" "api_tenants" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api_tenants.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.ksi_api.execution_arn}/*/*"
}
EOF

echo "✅ Added complete tenants resources to main.tf"

cd ../../..

echo "🚀 Deploying with terraform..."
cd terraform
terraform apply -auto-approve
cd ..

echo ""
echo "🧪 Test the tenants endpoint:"
echo "   curl 'https://d5804hjt80.execute-api.us-gov-west-1.amazonaws.com/production/api/ksi/tenants'"
echo ""
echo "✅ Tenants endpoint should now work!"
