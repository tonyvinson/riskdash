#!/bin/bash

echo "🔗 Adding Tenant Management Routes to API Gateway"
echo "================================================"

# Check if API Gateway module exists
if [ ! -f "terraform/modules/api_gateway/main.tf" ]; then
    echo "❌ API Gateway module not found. Please run create_api_gateway.sh first"
    exit 1
fi

echo "✅ Found existing API Gateway module"

# Add tenant management routes to the API Gateway module
echo "📝 Adding tenant management routes to API Gateway..."

# Append tenant management resources to the existing API Gateway main.tf
cat >> terraform/modules/api_gateway/main.tf << 'EOF'

# =============================================================================
# TENANT MANAGEMENT API ROUTES
# =============================================================================

# /api/tenant resource
resource "aws_api_gateway_resource" "tenant" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  parent_id   = aws_api_gateway_resource.api.id
  path_part   = "tenant"
}

# /api/tenant/generate-role-instructions resource
resource "aws_api_gateway_resource" "tenant_generate_role" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  parent_id   = aws_api_gateway_resource.tenant.id
  path_part   = "generate-role-instructions"
}

# /api/tenant/test-connection resource
resource "aws_api_gateway_resource" "tenant_test_connection" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  parent_id   = aws_api_gateway_resource.tenant.id
  path_part   = "test-connection"
}

# /api/tenant/onboard resource
resource "aws_api_gateway_resource" "tenant_onboard" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  parent_id   = aws_api_gateway_resource.tenant.id
  path_part   = "onboard"
}

# /api/tenant/list resource
resource "aws_api_gateway_resource" "tenant_list" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  parent_id   = aws_api_gateway_resource.tenant.id
  path_part   = "list"
}

# =============================================================================
# TENANT MANAGEMENT METHODS
# =============================================================================

# POST /api/tenant/generate-role-instructions
resource "aws_api_gateway_method" "tenant_generate_role_post" {
  rest_api_id   = aws_api_gateway_rest_api.ksi_api.id
  resource_id   = aws_api_gateway_resource.tenant_generate_role.id
  http_method   = "POST"
  authorization = "AWS_IAM"
}

# POST /api/tenant/test-connection
resource "aws_api_gateway_method" "tenant_test_connection_post" {
  rest_api_id   = aws_api_gateway_rest_api.ksi_api.id
  resource_id   = aws_api_gateway_resource.tenant_test_connection.id
  http_method   = "POST"
  authorization = "AWS_IAM"
}

# POST /api/tenant/onboard
resource "aws_api_gateway_method" "tenant_onboard_post" {
  rest_api_id   = aws_api_gateway_rest_api.ksi_api.id
  resource_id   = aws_api_gateway_resource.tenant_onboard.id
  http_method   = "POST"
  authorization = "AWS_IAM"
}

# GET /api/tenant/list
resource "aws_api_gateway_method" "tenant_list_get" {
  rest_api_id   = aws_api_gateway_rest_api.ksi_api.id
  resource_id   = aws_api_gateway_resource.tenant_list.id
  http_method   = "GET"
  authorization = "AWS_IAM"
}

# =============================================================================
# CORS OPTIONS METHODS FOR TENANT ENDPOINTS
# =============================================================================

# OPTIONS for tenant resources (CORS)
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

resource "aws_api_gateway_method" "tenant_list_options" {
  rest_api_id   = aws_api_gateway_rest_api.ksi_api.id
  resource_id   = aws_api_gateway_resource.tenant_list.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

# =============================================================================
# LAMBDA INTEGRATIONS FOR TENANT MANAGEMENT
# =============================================================================

# Integration for generate-role-instructions
resource "aws_api_gateway_integration" "tenant_generate_role_post" {
  rest_api_id             = aws_api_gateway_rest_api.ksi_api.id
  resource_id             = aws_api_gateway_resource.tenant_generate_role.id
  http_method             = aws_api_gateway_method.tenant_generate_role_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = var.tenant_onboarding_lambda_invoke_arn
}

# Integration for test-connection
resource "aws_api_gateway_integration" "tenant_test_connection_post" {
  rest_api_id             = aws_api_gateway_rest_api.ksi_api.id
  resource_id             = aws_api_gateway_resource.tenant_test_connection.id
  http_method             = aws_api_gateway_method.tenant_test_connection_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = var.tenant_onboarding_lambda_invoke_arn
}

# Integration for onboard
resource "aws_api_gateway_integration" "tenant_onboard_post" {
  rest_api_id             = aws_api_gateway_rest_api.ksi_api.id
  resource_id             = aws_api_gateway_resource.tenant_onboard.id
  http_method             = aws_api_gateway_method.tenant_onboard_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = var.tenant_onboarding_lambda_invoke_arn
}

# Integration for list (uses tenant onboarding lambda for now)
resource "aws_api_gateway_integration" "tenant_list_get" {
  rest_api_id             = aws_api_gateway_rest_api.ksi_api.id
  resource_id             = aws_api_gateway_resource.tenant_list.id
  http_method             = aws_api_gateway_method.tenant_list_get.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = var.tenant_onboarding_lambda_invoke_arn
}

# =============================================================================
# CORS INTEGRATIONS
# =============================================================================

# CORS integration for generate-role-instructions
resource "aws_api_gateway_integration" "tenant_generate_role_options" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  resource_id = aws_api_gateway_resource.tenant_generate_role.id
  http_method = aws_api_gateway_method.tenant_generate_role_options.http_method
  type        = "MOCK"
  
  request_templates = {
    "application/json" = jsonencode({
      statusCode = 200
    })
  }
}

# CORS integration for test-connection
resource "aws_api_gateway_integration" "tenant_test_connection_options" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  resource_id = aws_api_gateway_resource.tenant_test_connection.id
  http_method = aws_api_gateway_method.tenant_test_connection_options.http_method
  type        = "MOCK"
  
  request_templates = {
    "application/json" = jsonencode({
      statusCode = 200
    })
  }
}

# CORS integration for onboard
resource "aws_api_gateway_integration" "tenant_onboard_options" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  resource_id = aws_api_gateway_resource.tenant_onboard.id
  http_method = aws_api_gateway_method.tenant_onboard_options.http_method
  type        = "MOCK"
  
  request_templates = {
    "application/json" = jsonencode({
      statusCode = 200
    })
  }
}

# CORS integration for list
resource "aws_api_gateway_integration" "tenant_list_options" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  resource_id = aws_api_gateway_resource.tenant_list.id
  http_method = aws_api_gateway_method.tenant_list_options.http_method
  type        = "MOCK"
  
  request_templates = {
    "application/json" = jsonencode({
      statusCode = 200
    })
  }
}

# =============================================================================
# METHOD RESPONSES
# =============================================================================

# Method responses for tenant endpoints
resource "aws_api_gateway_method_response" "tenant_generate_role_post_200" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  resource_id = aws_api_gateway_resource.tenant_generate_role.id
  http_method = aws_api_gateway_method.tenant_generate_role_post.http_method
  status_code = "200"
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }
}

resource "aws_api_gateway_method_response" "tenant_test_connection_post_200" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  resource_id = aws_api_gateway_resource.tenant_test_connection.id
  http_method = aws_api_gateway_method.tenant_test_connection_post.http_method
  status_code = "200"
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }
}

resource "aws_api_gateway_method_response" "tenant_onboard_post_200" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  resource_id = aws_api_gateway_resource.tenant_onboard.id
  http_method = aws_api_gateway_method.tenant_onboard_post.http_method
  status_code = "200"
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }
}

resource "aws_api_gateway_method_response" "tenant_list_get_200" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  resource_id = aws_api_gateway_resource.tenant_list.id
  http_method = aws_api_gateway_method.tenant_list_get.http_method
  status_code = "200"
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }
}

# CORS method responses
resource "aws_api_gateway_method_response" "tenant_generate_role_options_200" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  resource_id = aws_api_gateway_resource.tenant_generate_role.id
  http_method = aws_api_gateway_method.tenant_generate_role_options.http_method
  status_code = "200"
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = true
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
  }
}

resource "aws_api_gateway_method_response" "tenant_test_connection_options_200" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  resource_id = aws_api_gateway_resource.tenant_test_connection.id
  http_method = aws_api_gateway_method.tenant_test_connection_options.http_method
  status_code = "200"
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = true
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
  }
}

resource "aws_api_gateway_method_response" "tenant_onboard_options_200" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  resource_id = aws_api_gateway_resource.tenant_onboard.id
  http_method = aws_api_gateway_method.tenant_onboard_options.http_method
  status_code = "200"
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = true
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
  }
}

resource "aws_api_gateway_method_response" "tenant_list_options_200" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  resource_id = aws_api_gateway_resource.tenant_list.id
  http_method = aws_api_gateway_method.tenant_list_options.http_method
  status_code = "200"
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = true
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
  }
}

# =============================================================================
# INTEGRATION RESPONSES
# =============================================================================

# Integration responses for CORS
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

resource "aws_api_gateway_integration_response" "tenant_list_options" {
  rest_api_id = aws_api_gateway_rest_api.ksi_api.id
  resource_id = aws_api_gateway_resource.tenant_list.id
  http_method = aws_api_gateway_method.tenant_list_options.http_method
  status_code = aws_api_gateway_method_response.tenant_list_options_200.status_code
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS'"
  }
}

# =============================================================================
# LAMBDA PERMISSIONS FOR TENANT MANAGEMENT
# =============================================================================

resource "aws_lambda_permission" "api_tenant_onboarding" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = var.tenant_onboarding_lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.ksi_api.execution_arn}/*/*"
}
EOF

echo "✅ Added tenant management routes to API Gateway"

# Update variables.tf to include tenant management Lambda references
echo "📝 Updating API Gateway variables..."
cat >> terraform/modules/api_gateway/variables.tf << 'EOF'

# Tenant Management Lambda variables
variable "tenant_onboarding_lambda_function_name" {
  description = "Name of the tenant onboarding Lambda function"
  type        = string
}

variable "tenant_onboarding_lambda_invoke_arn" {
  description = "Invoke ARN of the tenant onboarding Lambda function"
  type        = string
}
EOF

echo "✅ Updated API Gateway variables"

# Update outputs.tf to include tenant endpoints
echo "📝 Updating API Gateway outputs..."
cat >> terraform/modules/api_gateway/outputs.tf << 'EOF'

# Tenant Management API endpoints
output "tenant_api_endpoints" {
  description = "Tenant management API endpoints"
  value = {
    generate_role_instructions = "${local.api_base_url}/api/tenant/generate-role-instructions"
    test_connection           = "${local.api_base_url}/api/tenant/test-connection"
    onboard                   = "${local.api_base_url}/api/tenant/onboard"
    list                      = "${local.api_base_url}/api/tenant/list"
  }
}
EOF

echo "✅ Updated API Gateway outputs"

# Create updated main.tf integration instructions
echo "📝 Creating integration instructions..."
cat > terraform/INTEGRATION_INSTRUCTIONS.md << 'EOF'
# Tenant Management API Integration Instructions

## 1. Update your main terraform/main.tf

Add these variables to your API Gateway module call:

```hcl
module "api_gateway" {
  source = "./modules/api_gateway"
  
  # ... existing variables ...
  
  # Add these new variables for tenant management
  tenant_onboarding_lambda_function_name = module.tenant_management.tenant_onboarding_api_function_name
  tenant_onboarding_lambda_invoke_arn    = module.tenant_management.tenant_onboarding_api_function_arn
}
```

## 2. Update your outputs.tf

Add tenant API endpoints to your outputs:

```hcl
output "tenant_api_endpoints" {
  description = "Tenant management API endpoints"
  value       = module.api_gateway.tenant_api_endpoints
}
```

## 3. Deploy the changes

```bash
cd terraform
terraform plan
terraform apply
```

## 4. Test the new endpoints

After deployment, test the new tenant management endpoints:

```bash
# Get the API URL
terraform output tenant_api_endpoints

# Test role instructions generation
curl -X POST "https://your-api-gateway-url/api/tenant/generate-role-instructions" \
  -H "Content-Type: application/json" \
  -d '{"tenantId": "test-tenant", "accountId": "123456789012"}'
```

## 5. Update frontend API URL

Make sure your frontend environment is pointing to the correct API Gateway URL:

```bash
# In frontend/.env
REACT_APP_API_URL=https://your-api-gateway-url
```
EOF

echo ""
echo "🎉 API Gateway Tenant Management Routes Added!"
echo ""
echo "📋 What was created:"
echo "   ✅ /api/tenant/generate-role-instructions endpoint"
echo "   ✅ /api/tenant/test-connection endpoint"
echo "   ✅ /api/tenant/onboard endpoint"
echo "   ✅ /api/tenant/list endpoint"
echo "   ✅ CORS support for all tenant endpoints"
echo "   ✅ Lambda integrations and permissions"
echo ""
echo "🔧 Next Steps:"
echo "1. Follow instructions in terraform/INTEGRATION_INSTRUCTIONS.md"
echo "2. Update your main.tf with the new API Gateway variables"
echo "3. Run: cd terraform && terraform apply"
echo "4. Test the frontend integration"
echo ""
echo "✨ Your API Gateway now supports complete tenant management!"
