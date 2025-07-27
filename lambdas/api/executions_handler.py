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
    API endpoint for getting KSI execution history
    """
    try:
        # Get query parameters
        query_params = event.get('queryStringParameters') or {}
        tenant_id = query_params.get('tenant_id', 'default')
        
        # Query DynamoDB for execution history
        dynamodb = boto3.resource('dynamodb')
        table_name = os.environ.get('KSI_EXECUTION_HISTORY_TABLE')
        
        if not table_name:
            raise Exception("KSI_EXECUTION_HISTORY_TABLE environment variable not set")
        
        table = dynamodb.Table(table_name)
        
        # Scan for recent executions (in production, use proper pagination)
        response = table.scan(
            FilterExpression=boto3.dynamodb.conditions.Attr('tenant_id').eq(tenant_id),
            Limit=50
        )
        
        executions = response.get('Items', [])
        
        # Sort by timestamp (most recent first)
        executions.sort(key=lambda x: x.get('execution_timestamp', ''), reverse=True)
        
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
                    'executions': executions,
                    'count': len(executions)
                }
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
