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
