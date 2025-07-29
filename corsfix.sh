#!/bin/bash
# complete-cors-fix.sh - Fix all CORS issues permanently

set -e

echo "🔧 Fixing all CORS issues permanently..."

# 1. Fix the OPTIONS integration responses that are returning 500
echo "📝 Step 1: Fixing OPTIONS integration responses..."

cd terraform/modules/api_gateway

# Create backup
cp main.tf main.tf.backup.$(date +%Y%m%d_%H%M%S)

# Fix the CORS integration responses - they're likely missing proper request templates
cat > cors_fix.tf << 'EOF'

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
EOF

# 2. Remove old broken integrations from main.tf
echo "📝 Step 2: Removing old broken CORS integrations..."

# Comment out the old broken integrations to avoid conflicts
sed -i.backup '
/^resource "aws_api_gateway_integration" "cors_validate"/,/^}$/ {
    s/^/# DISABLED - /
}
/^resource "aws_api_gateway_integration" "cors_executions"/,/^}$/ {
    s/^/# DISABLED - /
}
/^resource "aws_api_gateway_integration" "cors_results"/,/^}$/ {
    s/^/# DISABLED - /
}
/^resource "aws_api_gateway_integration_response" "cors_validate"/,/^}$/ {
    s/^/# DISABLED - /
}
/^resource "aws_api_gateway_integration_response" "cors_executions"/,/^}$/ {
    s/^/# DISABLED - /
}
/^resource "aws_api_gateway_integration_response" "cors_results"/,/^}$/ {
    s/^/# DISABLED - /
}
' main.tf

# 3. Create the missing tenants endpoint
echo "📝 Step 3: Creating missing tenants endpoint..."

cd ../../../

# Create tenants Lambda function
mkdir -p lambdas/api
cat > lambdas/api/tenants_lambda.py << 'EOF'
import json
import boto3
import os
from decimal import Decimal

def lambda_handler(event, context):
    """Handle GET /api/ksi/tenants - Return list of available tenants"""
    
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'GET,OPTIONS'
    }
    
    try:
        # Handle CORS preflight
        if event.get('httpMethod') == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'message': 'CORS preflight successful'})
            }
        
        # Get DynamoDB client
        dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION', 'us-gov-west-1'))
        table_name = os.environ.get('TENANT_KSI_CONFIGURATIONS_TABLE', 'riskuity-ksi-validator-tenant-ksi-configurations-production')
        table = dynamodb.Table(table_name)
        
        # Scan for unique tenant IDs
        response = table.scan(ProjectionExpression='tenant_id')
        items = response.get('Items', [])
        
        # Get unique tenants
        tenant_ids = list(set(item.get('tenant_id') for item in items if item.get('tenant_id')))
        tenant_ids.sort()
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'success': True,
                'data': tenant_ids,
                'total_count': len(tenant_ids)
            }, default=lambda x: float(x) if isinstance(x, Decimal) else str(x))
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }
EOF

# Package Lambda
cd lambdas/api
zip tenants.zip tenants_lambda.py
mv tenants.zip ../../terraform/modules/api_gateway/
cd ../../

# 4. Add tenants endpoint to Terraform
echo "📝 Step 4: Adding tenants endpoint to Terraform..."

cd terraform/modules/api_gateway

cat >> cors_fix.tf << 'EOF'

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
EOF

# 5. Update main terraform to pass variables
cd ../../
echo "📝 Step 5: Updating main terraform..."

# Add the variable to api_gateway module if not present
if ! grep -q "tenant_ksi_configurations_table_name" main.tf; then
    sed -i.backup '/module "api_gateway" {/,/}/ {
        /depends_on = \[module.lambda, module.dynamodb\]/i\
  \
  # DynamoDB table references\
  tenant_ksi_configurations_table_name = module.dynamodb.tenant_ksi_configurations_table_name
    }' main.tf
fi

# 6. Deploy the fixes
echo "🚀 Step 6: Deploying CORS fixes..."

# First deploy the Lambda function
terraform plan -target=module.api_gateway.aws_lambda_function.tenants
terraform apply -target=module.api_gateway.aws_lambda_function.tenants -auto-approve

# Then deploy all API Gateway changes
terraform apply -target=module.api_gateway -auto-approve

echo ""
echo "✅ CORS fixes deployed!"
echo ""
echo "🧪 Test the fixes:"
echo "curl -X OPTIONS -H 'Origin: http://localhost:3000' 'https://d5804hjt80.execute-api.us-gov-west-1.amazonaws.com/production/api/ksi/validate'"
echo "curl 'https://d5804hjt80.execute-api.us-gov-west-1.amazonaws.com/production/api/ksi/tenants'"
echo ""
echo "🎯 Your React app should now work without CORS errors!"
