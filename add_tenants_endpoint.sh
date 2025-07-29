#!/bin/bash
# add_tenants_endpoint.sh - Add the missing /api/ksi/tenants endpoint

echo "🔧 Adding missing /api/ksi/tenants endpoint to your API Gateway..."

# 1. Create the Lambda handler for tenants endpoint
echo "📝 Step 1: Creating tenants Lambda handler..."
cat > lambdas/api/tenants_handler.py << 'EOF'
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
        table = dynamodb.Table(os.environ['TENANT_KSI_CONFIGURATIONS_TABLE'])
        
        # Scan the table to get all tenants
        response = table.scan()
        items = response.get('Items', [])
        
        # Process tenants and count KSIs
        tenants_map = {}
        for item in items:
            tenant_id = item.get('tenant_id')
            if tenant_id and tenant_id not in tenants_map:
                tenants_map[tenant_id] = {
                    'tenant_id': tenant_id,
                    'ksi_count': 0,
                    'display_name': format_tenant_name(tenant_id)
                }
            
            if tenant_id:
                tenants_map[tenant_id]['ksi_count'] += 1
        
        # Convert to list and sort
        tenants = list(tenants_map.values())
        tenants.sort(key=lambda x: x['tenant_id'])
        
        print(f"✅ Retrieved {len(tenants)} tenants from DynamoDB")
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'tenants': tenants,
                'total_count': len(tenants)
            }, default=decimal_default)
        }
        
    except Exception as e:
        print(f"❌ Error retrieving tenants: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'error': 'Failed to retrieve tenants',
                'message': str(e)
            })
        }

def format_tenant_name(tenant_id):
    """Convert tenant-001 to 'Tenant 001' for better display"""
    if not tenant_id:
        return 'Unknown Tenant'
    
    # Handle common patterns
    if tenant_id.startswith('tenant-'):
        number = tenant_id.replace('tenant-', '')
        return f'Tenant {number.upper()}'
    elif tenant_id.startswith('real-test'):
        return 'Real Test Tenant'
    else:
        # Convert kebab-case to Title Case
        return tenant_id.replace('-', ' ').replace('_', ' ').title()

def decimal_default(obj):
    """JSON serializer for Decimal objects"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
EOF

# 2. Add the Terraform resources to API Gateway module
echo "📝 Step 2: Adding Terraform resources..."

# Backup current main.tf
cd terraform/modules/api_gateway
cp main.tf main.tf.backup.$(date +%Y%m%d_%H%M%S)

# Add the tenants resource and method to main.tf
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
      AWS_REGION = var.aws_region
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

cd ../../..

# 3. Package the Lambda function
echo "📝 Step 3: Packaging Lambda function..."
cd lambdas/api
zip -q api-tenants.zip tenants_handler.py
cp api-tenants.zip ../../terraform/modules/api_gateway/
cd ../..

# 4. Update outputs to include tenants endpoint
echo "📝 Step 4: Updating outputs..."
sed -i.backup '/results_url.*=.*results/a\
    tenants_url    = "https://${aws_api_gateway_rest_api.ksi_api.id}.execute-api.${data.aws_region.current.id}.amazonaws.com/${var.environment}/api/ksi/tenants"' terraform/modules/api_gateway/outputs.tf

echo ""
echo "✅ Setup complete! Now deploy with:"
echo "   cd terraform"
echo "   terraform plan"
echo "   terraform apply"
echo ""
echo "🔗 New endpoint will be:"
echo "   GET https://d5804hjt80.execute-api.us-gov-west-1.amazonaws.com/production/api/ksi/tenants"
