import json
import boto3
import os
from typing import Dict, Any

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    API endpoint for triggering KSI validation
    """
    try:
        # Extract request body
        if 'body' in event:
            if isinstance(event['body'], str):
                body = json.loads(event['body'])
            else:
                body = event['body']
        else:
            body = event

        # Get tenant_id from request
        tenant_id = body.get('tenant_id', 'default')
        
        # Call orchestrator
        lambda_client = boto3.client('lambda')
        orchestrator_function = f"{os.environ.get('PROJECT_NAME', 'riskuity-ksi-validator')}-orchestrator-{os.environ.get('ENVIRONMENT', 'production')}"
        
        # Invoke orchestrator
        response = lambda_client.invoke(
            FunctionName=orchestrator_function,
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'tenant_id': tenant_id,
                'source': 'api'
            })
        )
        
        # Parse response
        payload = response['Payload'].read()
        result = json.loads(payload)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST, OPTIONS'
            },
            'body': json.dumps({
                'success': True,
                'data': result
            })
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
