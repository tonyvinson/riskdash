import json
import boto3
import logging
from datetime import datetime, timezone
from typing import Dict, Any
import os
import uuid

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
lambda_client = boto3.client('lambda')

# Environment variables
ENVIRONMENT = os.environ['ENVIRONMENT']
ORCHESTRATOR_LAMBDA_ARN = os.environ['ORCHESTRATOR_LAMBDA_ARN']

def lambda_handler(event, context):
    """
    API Handler for POST /api/ksi/validate
    Triggers KSI validation via orchestrator Lambda
    """
    try:
        # Parse request
        if 'body' in event:
            if isinstance(event['body'], str):
                body = json.loads(event['body'])
            else:
                body = event['body']
        else:
            body = {}
        
        # Extract parameters
        tenant_id = body.get('tenant_id', 'default')
        trigger_source = body.get('trigger_source', 'api')
        execution_id = body.get('execution_id', str(uuid.uuid4()))
        
        logger.info(f"Triggering validation for tenant: {tenant_id}, execution: {execution_id}")
        
        # Prepare orchestrator payload
        orchestrator_payload = {
            'tenant_id': tenant_id,
            'trigger_source': trigger_source,
            'execution_id': execution_id,
            'triggered_by': 'api-gateway',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # Invoke orchestrator Lambda
        response = lambda_client.invoke(
            FunctionName=ORCHESTRATOR_LAMBDA_ARN,
            InvocationType='Event',  # Async invocation
            Payload=json.dumps(orchestrator_payload)
        )
        
        # Return API response
        api_response = {
            'statusCode': 202,  # Accepted
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
            },
            'body': json.dumps({
                'message': 'KSI validation triggered successfully',
                'execution_id': execution_id,
                'tenant_id': tenant_id,
                'trigger_source': trigger_source,
                'status': 'TRIGGERED',
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        }
        
        logger.info(f"Successfully triggered validation: {execution_id}")
        return api_response
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in request body: {str(e)}")
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Invalid JSON in request body',
                'message': str(e)
            })
        }
    except Exception as e:
        logger.error(f"Error triggering validation: {str(e)}")
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
