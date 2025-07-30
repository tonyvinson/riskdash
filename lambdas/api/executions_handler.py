import json
import boto3
import os
from decimal import Decimal
from datetime import datetime, timezone

def decimal_default(obj):
    """JSON serializer for DynamoDB Decimal objects"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def lambda_handler(event, context):
    """
    Diagnostic version - API endpoint for getting KSI execution history
    """
    
    # CORS headers for all responses
    cors_headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'GET,OPTIONS'
    }
    
    try:
        # Step 1: Check environment variables
        table_name = os.environ.get('KSI_EXECUTION_HISTORY_TABLE')
        print(f"🔍 Environment check - Table name: {table_name}")
        
        if not table_name:
            return {
                'statusCode': 500,
                'headers': cors_headers,
                'body': json.dumps({
                    'success': False,
                    'error': 'KSI_EXECUTION_HISTORY_TABLE environment variable not set',
                    'debug': {
                        'available_env_vars': list(os.environ.keys()),
                        'function_name': context.function_name if context else 'unknown'
                    }
                })
            }
        
        # Step 2: Try to connect to DynamoDB
        print(f"🔍 Connecting to DynamoDB...")
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(table_name)
        
        # Step 3: Check query parameters
        query_params = event.get('queryStringParameters') or {}
        tenant_id = query_params.get('tenant_id', 'all')
        limit = int(query_params.get('limit', 20))
        
        print(f"🔍 Query params - tenant_id: {tenant_id}, limit: {limit}")
        
        # Step 4: Try a simple scan first (without filters)
        print(f"🔍 Attempting table scan...")
        response = table.scan(Limit=5)  # Just get 5 items for testing
        
        items = response.get('Items', [])
        print(f"🔍 Scan successful - found {len(items)} items")
        
        # Step 5: Return diagnostic info
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({
                'success': True,
                'debug': {
                    'table_name': table_name,
                    'tenant_id_requested': tenant_id,
                    'limit_requested': limit,
                    'items_found': len(items),
                    'sample_item_keys': [list(item.keys()) for item in items[:2]] if items else [],
                    'function_name': context.function_name if context else 'unknown',
                    'aws_region': os.environ.get('AWS_REGION', 'unknown')
                },
                'data': {
                    'executions': items,
                    'count': len(items),
                    'message': 'Diagnostic scan successful'
                }
            }, default=decimal_default)
        }
        
    except Exception as e:
        print(f"❌ Error in executions handler: {str(e)}")
        print(f"❌ Error type: {type(e).__name__}")
        
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({
                'success': False,
                'error': f'{type(e).__name__}: {str(e)}',
                'debug': {
                    'table_name': os.environ.get('KSI_EXECUTION_HISTORY_TABLE', 'NOT_SET'),
                    'function_name': context.function_name if context else 'unknown',
                    'aws_region': os.environ.get('AWS_REGION', 'unknown'),
                    'available_env_vars': list(os.environ.keys())
                }
            })
        }
