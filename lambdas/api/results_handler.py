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
