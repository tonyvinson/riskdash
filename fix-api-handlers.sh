#!/bin/bash
# fix-api-handlers.sh - Fix API handlers to use GSI properly

echo "🔧 Fixing API Handlers to Use GSI Properly"
echo "=========================================="

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}Step 1: Backing up current handlers...${NC}"
cp lambdas/api/executions_handler.py lambdas/api/executions_handler.py.bak 2>/dev/null || echo "No existing executions_handler found"
cp lambdas/api/results_handler.py lambdas/api/results_handler.py.bak 2>/dev/null || echo "No existing results_handler found"

echo -e "${BLUE}Step 2: Creating fixed executions_handler.py...${NC}"
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
    Retrieves KSI execution history from DynamoDB using GSI for efficient querying
    """
    try:
        # Parse query parameters
        query_params = event.get('queryStringParameters') or {}
        tenant_id = query_params.get('tenant_id', 'default')  # Default to 'default' if not provided
        limit = int(query_params.get('limit', 50))
        start_key = query_params.get('start_key')
        
        # Validate limit
        if limit > 100:
            limit = 100
        
        logger.info(f"Fetching executions for tenant: {tenant_id}, limit: {limit}")
        
        table = dynamodb.Table(KSI_EXECUTION_HISTORY_TABLE)
        
        # Use GSI to query by tenant_id efficiently
        query_params_gsi = {
            'IndexName': 'tenant-timestamp-index',
            'KeyConditionExpression': boto3.dynamodb.conditions.Key('tenant_id').eq(tenant_id),
            'Limit': limit,
            'ScanIndexForward': False  # Sort by timestamp descending (most recent first)
        }
        
        # Add pagination if start_key provided
        if start_key:
            try:
                query_params_gsi['ExclusiveStartKey'] = json.loads(start_key)
            except json.JSONDecodeError:
                logger.warning(f"Invalid start_key format: {start_key}")
        
        # Execute GSI query
        response = table.query(**query_params_gsi)
        
        executions = response.get('Items', [])
        last_evaluated_key = response.get('LastEvaluatedKey')
        
        logger.info(f"Retrieved {len(executions)} executions for tenant {tenant_id}")
        
        # Build API response
        api_response = {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'GET, OPTIONS'
            },
            'body': json.dumps({
                'success': True,
                'data': {
                    'executions': executions,
                    'count': len(executions),
                    'tenant_id': tenant_id,
                    'next_page_key': json.dumps(last_evaluated_key) if last_evaluated_key else None
                }
            }, default=decimal_default)
        }
        
        return api_response
        
    except Exception as e:
        logger.error(f"Error fetching executions: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({
                'success': False,
                'error': str(e),
                'message': 'Failed to fetch execution history'
            }, default=decimal_default)
        }
EOF

echo -e "${BLUE}Step 3: Creating fixed results_handler.py...${NC}"
cat > lambdas/api/results_handler.py << 'EOF'
import json
import boto3
import logging
import os
from typing import Dict, Any
from decimal import Decimal

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')

# Environment variables
KSI_EXECUTION_HISTORY_TABLE = os.environ['KSI_EXECUTION_HISTORY_TABLE']

def decimal_default(obj):
    """JSON serializer for DynamoDB Decimal objects"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    API endpoint for getting KSI validation results
    Uses GSI for efficient querying by tenant_id
    """
    try:
        # Get query parameters
        query_params = event.get('queryStringParameters') or {}
        tenant_id = query_params.get('tenant_id', 'default')
        execution_id = query_params.get('execution_id')
        limit = int(query_params.get('limit', 10))
        
        logger.info(f"Fetching results for tenant: {tenant_id}, execution: {execution_id}")
        
        table = dynamodb.Table(KSI_EXECUTION_HISTORY_TABLE)
        
        if execution_id:
            # Get specific execution - need to query GSI first to get timestamp
            gsi_response = table.query(
                IndexName='tenant-timestamp-index',
                KeyConditionExpression=boto3.dynamodb.conditions.Key('tenant_id').eq(tenant_id),
                FilterExpression=boto3.dynamodb.conditions.Attr('execution_id').eq(execution_id),
                Limit=1
            )
            
            if not gsi_response.get('Items'):
                return {
                    'statusCode': 404,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'success': False,
                        'error': 'Execution not found',
                        'tenant_id': tenant_id,
                        'execution_id': execution_id
                    })
                }
            
            results = gsi_response['Items'][0]
            
        else:
            # Get latest executions for tenant using GSI
            response = table.query(
                IndexName='tenant-timestamp-index',
                KeyConditionExpression=boto3.dynamodb.conditions.Key('tenant_id').eq(tenant_id),
                Limit=limit,
                ScanIndexForward=False  # Most recent first
            )
            
            results = response.get('Items', [])
            
            if not results:
                # Return empty results with helpful message
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Headers': 'Content-Type',
                        'Access-Control-Allow-Methods': 'GET, OPTIONS'
                    },
                    'body': json.dumps({
                        'success': True,
                        'data': {
                            'executions': [],
                            'count': 0,
                            'tenant_id': tenant_id,
                            'message': f'No executions found for tenant {tenant_id}. Try triggering a validation first.'
                        }
                    }, default=decimal_default)
                }
        
        logger.info(f"Retrieved results for tenant {tenant_id}: {len(results) if isinstance(results, list) else 1} items")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'GET, OPTIONS'
            },
            'body': json.dumps({
                'success': True,
                'data': {
                    'executions': results if isinstance(results, list) else [results],
                    'count': len(results) if isinstance(results, list) else 1,
                    'tenant_id': tenant_id
                }
            }, default=decimal_default)
        }
        
    except Exception as e:
        logger.error(f"Error fetching results: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': str(e),
                'message': 'Failed to fetch validation results'
            })
        }
EOF

echo -e "${BLUE}Step 4: Deploying updated Lambda functions...${NC}"
echo "Deploying API Gateway module with updated handlers..."

# Check if terraform directory exists
if [ ! -d "terraform" ]; then
    echo -e "${RED}❌ terraform directory not found. Running from project root...${NC}"
    if [ ! -f "terraform/main.tf" ]; then
        echo -e "${RED}❌ Could not find terraform/main.tf. Please run from project root directory.${NC}"
        exit 1
    fi
fi

cd terraform
terraform apply -target=module.api_gateway -auto-approve

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ API handlers updated successfully!${NC}"
    echo ""
    echo -e "${YELLOW}🧪 Test Commands:${NC}"
    echo "# Test with existing tenant 'real-test':"
    echo "curl -X GET 'https://d5804hjt80.execute-api.us-gov-west-1.amazonaws.com/production/api/ksi/executions?tenant_id=real-test'"
    echo ""
    echo "# Test with tenant 'riskuity-production':"
    echo "curl -X GET 'https://d5804hjt80.execute-api.us-gov-west-1.amazonaws.com/production/api/ksi/executions?tenant_id=riskuity-production'"
    echo ""
    echo "# Trigger validation for riskuity-production:"
    echo "curl -X POST 'https://d5804hjt80.execute-api.us-gov-west-1.amazonaws.com/production/api/ksi/validate' \\"
    echo "     -H 'Content-Type: application/json' \\"
    echo "     -d '{\"tenant_id\": \"riskuity-production\"}'"
else
    echo -e "${RED}❌ Deployment failed. Check the error above.${NC}"
    exit 1
fi

echo -e "${GREEN}🎯 Fix completed! Your API handlers now use GSI efficiently.${NC}"
