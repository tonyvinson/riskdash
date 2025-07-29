import json
import logging
import boto3
import os
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    API Gateway handler for POST /api/ksi/validate
    Triggers KSI validation for specified tenant
    """
    try:
        # Parse request body
        if event.get('body'):
            body = json.loads(event['body'])
        else:
            body = {}
        
        tenant_id = body.get('tenant_id', 'default')
        trigger_source = body.get('trigger_source', 'api')
        
        logger.info(f"Validation requested for tenant: {tenant_id}, source: {trigger_source}")
        
        # Invoke orchestrator Lambda
        lambda_client = boto3.client('lambda')
        orchestrator_arn = os.environ.get('ORCHESTRATOR_LAMBDA_ARN')
        
        if not orchestrator_arn:
            raise ValueError("ORCHESTRATOR_LAMBDA_ARN environment variable not set")
        
        payload = {
            'tenant_id': tenant_id,
            'trigger_source': trigger_source,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        response = lambda_client.invoke(
            FunctionName=orchestrator_arn,
            InvocationType='Event',  # Async invocation
            Payload=json.dumps(payload)
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps({
                'message': 'KSI validation triggered successfully',
                'tenant_id': tenant_id,
                'trigger_source': trigger_source,
                'timestamp': datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Error in validate handler: {str(e)}")
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
