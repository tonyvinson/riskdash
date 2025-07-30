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
    Diagnostic version - API endpoint for getting KSI validation results
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
        tenant_id = query_params.get('tenant_id', 'default')
        execution_id = query_params.get('execution_id')
        
        print(f"🔍 Query params - tenant_id: {tenant_id}, execution_id: {execution_id}")
        
        # Step 4: Try a simple scan to see what data exists
        print(f"🔍 Attempting table scan...")
        response = table.scan(Limit=3)  # Just get 3 items for testing
        
        items = response.get('Items', [])
        print(f"🔍 Scan successful - found {len(items)} items")
        
        # Step 5: Try to find items with validation_results
        validation_items = []
        for item in items:
            if 'validation_results' in item or 'validators_completed' in item:
                validation_items.append(item)
        
        print(f"🔍 Found {len(validation_items)} items with validation data")
        
        # Step 6: Return diagnostic info
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({
                'success': True,
                'debug': {
                    'table_name': table_name,
                    'tenant_id_requested': tenant_id,
                    'execution_id_requested': execution_id,
                    'total_items_found': len(items),
                    'validation_items_found': len(validation_items),
                    'sample_item_keys': [list(item.keys()) for item in items[:2]] if items else [],
                    'function_name': context.function_name if context else 'unknown',
                    'aws_region': os.environ.get('AWS_REGION', 'unknown')
                },
                'data': {
                    'validation_results': validation_items,
                    'message': 'Diagnostic scan successful'
                }
            }, default=decimal_default)
        }
        
    except Exception as e:
        print(f"❌ Error in results handler: {str(e)}")
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
