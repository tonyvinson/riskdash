import json
import boto3
import os
from typing import Dict, Any
from decimal import Decimal

def decimal_default(obj):
    """JSON serializer for DynamoDB Decimal objects"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    API endpoint for getting KSI validation results
    """
    try:
        # Get query parameters
        query_params = event.get('queryStringParameters') or {}
        tenant_id = query_params.get('tenant_id', 'default')
        execution_id = query_params.get('execution_id')
        
        # Query DynamoDB for results
        dynamodb = boto3.resource('dynamodb')
        table_name = os.environ.get('KSI_EXECUTION_HISTORY_TABLE')
        
        if not table_name:
            raise Exception("KSI_EXECUTION_HISTORY_TABLE environment variable not set")
        
        table = dynamodb.Table(table_name)
        
        if execution_id:
            # Get specific execution by primary key
            response = table.get_item(
                Key={
                    'execution_id': execution_id,
                    'tenant_id': tenant_id
                }
            )
            
            if 'Item' not in response:
                return {
                    'statusCode': 404,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'success': False,
                        'error': 'Execution not found'
                    })
                }
            
            results = response['Item']
        else:
            # Get latest executions for tenant using scan (since we don't know the key structure)
            response = table.scan(
                FilterExpression=boto3.dynamodb.conditions.Attr('tenant_id').eq(tenant_id),
                Limit=10
            )
            
            items = response.get('Items', [])
            if not items:
                # Return empty results instead of error
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'success': True,
                        'data': {
                            'executions': [],
                            'message': 'No executions found yet. Try triggering a validation first.'
                        }
                    })
                }
            
            # Sort by timestamp and get the most recent
            items.sort(key=lambda x: x.get('execution_timestamp', ''), reverse=True)
            results = items[0]
        
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
                'data': results
            }, default=decimal_default)  # Fix Decimal serialization
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }
