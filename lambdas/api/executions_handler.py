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
