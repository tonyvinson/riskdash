import json
import logging
import boto3
import os
from boto3.dynamodb.conditions import Key

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    API Gateway handler for GET /api/ksi/results
    Retrieves KSI validation results with filtering
    """
    try:
        # Parse query parameters
        params = event.get('queryStringParameters') or {}
        tenant_id = params.get('tenant_id', 'default')
        execution_id = params.get('execution_id')
        ksi_category = params.get('category')
        status_filter = params.get('status')
        limit = int(params.get('limit', 100))
        
        logger.info(f"Results requested for tenant: {tenant_id}, execution: {execution_id}")
        
        # Query DynamoDB
        dynamodb = boto3.resource('dynamodb')
        table_name = os.environ.get('KSI_EXECUTION_HISTORY_TABLE')
        
        if not table_name:
            raise ValueError("KSI_EXECUTION_HISTORY_TABLE environment variable not set")
        
        table = dynamodb.Table(table_name)
        
        # Query validation results
        if execution_id:
            # Get specific execution results
            response = table.get_item(
                Key={
                    'tenant_id': tenant_id,
                    'execution_id': execution_id
                }
            )
            results = [response.get('Item')] if response.get('Item') else []
        else:
            # Get recent results for tenant
            response = table.query(
                KeyConditionExpression=Key('tenant_id').eq(tenant_id),
                ScanIndexForward=False,  # Newest first
                Limit=limit
            )
            results = response.get('Items', [])
        
        # Apply filters
        if ksi_category:
            results = [r for r in results if r.get('category') == ksi_category]
        
        if status_filter:
            results = [r for r in results if r.get('status') == status_filter]
        
        # Format response
        formatted_results = []
        for result in results:
            if result:
                formatted_results.append({
                    'execution_id': result.get('execution_id'),
                    'tenant_id': result.get('tenant_id'),
                    'timestamp': result.get('timestamp'),
                    'status': result.get('status'),
                    'validation_results': result.get('validation_results', []),
                    'validators_completed': result.get('validators_completed', []),
                    'summary': result.get('summary', {})
                })
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps({
                'results': formatted_results,
                'count': len(formatted_results),
                'filters': {
                    'tenant_id': tenant_id,
                    'execution_id': execution_id,
                    'category': ksi_category,
                    'status': status_filter
                }
            })
        }
        
    except Exception as e:
        logger.error(f"Error in results handler: {str(e)}")
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
