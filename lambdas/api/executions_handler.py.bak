import json
import logging
import boto3
import os
from boto3.dynamodb.conditions import Key

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    API Gateway handler for GET /api/ksi/executions
    Retrieves KSI execution history
    """
    try:
        # Parse query parameters
        params = event.get('queryStringParameters') or {}
        tenant_id = params.get('tenant_id', 'default')
        limit = int(params.get('limit', 50))
        
        logger.info(f"Execution history requested for tenant: {tenant_id}, limit: {limit}")
        
        # Query DynamoDB
        dynamodb = boto3.resource('dynamodb')
        table_name = os.environ.get('KSI_EXECUTION_HISTORY_TABLE')
        
        if not table_name:
            raise ValueError("KSI_EXECUTION_HISTORY_TABLE environment variable not set")
        
        table = dynamodb.Table(table_name)
        
        # Query execution history for tenant
        response = table.query(
            KeyConditionExpression=Key('tenant_id').eq(tenant_id),
            ScanIndexForward=False,  # Sort in descending order (newest first)
            Limit=limit
        )
        
        executions = response.get('Items', [])
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps({
                'executions': executions,
                'count': len(executions),
                'tenant_id': tenant_id
            })
        }
        
    except Exception as e:
        logger.error(f"Error in executions handler: {str(e)}")
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
