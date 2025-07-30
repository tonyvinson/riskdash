#!/bin/bash
# exact-fix.sh - Fix the exact issues based on actual codebase analysis
set -e

echo "🔧 Fixing exact issues in your codebase..."

# 1. Remove the broken cors_fix.tf file
echo "📝 Step 1: Removing broken cors_fix.tf file..."
rm -f terraform/modules/api_gateway/cors_fix.tf
echo "✅ Removed broken cors_fix.tf"

# 2. Create the missing tenants_handler.py (your terraform expects it)
echo "📝 Step 2: Creating missing tenants_handler.py..."
cat > lambdas/api/tenants_handler.py << 'EOF'
import json
import boto3
import os
from decimal import Decimal

def lambda_handler(event, context):
    """
    Handler for GET /api/ksi/tenants endpoint
    Returns list of configured tenants from DynamoDB
    """
    
    # CORS headers
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'GET,OPTIONS',
        'Content-Type': 'application/json'
    }
    
    try:
        # Get table name from environment
        table_name = os.environ.get('TENANT_KSI_CONFIGURATIONS_TABLE')
        if not table_name:
            return {
                'statusCode': 500,
                'headers': headers,
                'body': json.dumps({'error': 'TENANT_KSI_CONFIGURATIONS_TABLE not configured'})
            }
        
        # Initialize DynamoDB
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(table_name)
        
        # Scan for all tenant configurations
        response = table.scan(
            ProjectionExpression='tenant_id, tenant_name, #status',
            ExpressionAttributeNames={
                '#status': 'status'
            }
        )
        
        # Format tenant data
        tenants = []
        for item in response.get('Items', []):
            tenants.append({
                'tenant_id': item.get('tenant_id', ''),
                'tenant_name': format_tenant_name(item.get('tenant_id', '')),
                'status': item.get('status', 'unknown')
            })
        
        # Sort by tenant_id
        tenants.sort(key=lambda x: x['tenant_id'])
        
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
    
    if tenant_id.startswith('tenant-'):
        number = tenant_id.replace('tenant-', '')
        return f'Tenant {number.upper()}'
    elif tenant_id == 'riskuity-production':
        return 'Riskuity Production'
    elif tenant_id == 'real-test':
        return 'Real Test'
    elif tenant_id == 'default':
        return 'Default'
    else:
        return tenant_id.replace('-', ' ').replace('_', ' ').title()

def decimal_default(obj):
    """JSON serializer for Decimal objects"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
EOF
echo "✅ Created tenants_handler.py"

# 3. Use your existing deploy script to package everything
echo "📝 Step 3: Using your existing deploy script..."
./scripts/deploy_lambdas.sh package-only
echo "✅ All lambdas packaged"

# 4. Deploy
echo "🚀 Step 4: Deploy with terraform..."
cd terraform
terraform apply -auto-approve
cd ..

echo ""
echo "🧪 Test the fixes:"
echo "   curl 'https://d5804hjt80.execute-api.us-gov-west-1.amazonaws.com/production/api/ksi/tenants'"
echo "   curl -X OPTIONS -H 'Origin: http://localhost:3000' 'https://d5804hjt80.execute-api.us-gov-west-1.amazonaws.com/production/api/ksi/validate'"
echo ""
echo "✅ Fixed the exact issues in your codebase!"
