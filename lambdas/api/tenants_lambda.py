import json
import boto3
import os
from decimal import Decimal

def lambda_handler(event, context):
    """Handle GET /api/ksi/tenants - Return list of available tenants"""
    
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'GET,OPTIONS'
    }
    
    try:
        # Handle CORS preflight
        if event.get('httpMethod') == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'message': 'CORS preflight successful'})
            }
        
        # Get DynamoDB client
        dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION', 'us-gov-west-1'))
        table_name = os.environ.get('TENANT_KSI_CONFIGURATIONS_TABLE', 'riskuity-ksi-validator-tenant-ksi-configurations-production')
        table = dynamodb.Table(table_name)
        
        # Scan for unique tenant IDs
        response = table.scan(ProjectionExpression='tenant_id')
        items = response.get('Items', [])
        
        # Get unique tenants
        tenant_ids = list(set(item.get('tenant_id') for item in items if item.get('tenant_id')))
        tenant_ids.sort()
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'success': True,
                'data': tenant_ids,
                'total_count': len(tenant_ids)
            }, default=lambda x: float(x) if isinstance(x, Decimal) else str(x))
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }
