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
        table = dynamodb.Table(os.environ['TENANT_KSI_CONFIGURATIONS_TABLE'])
        
        # Scan the table to get all tenants
        response = table.scan()
        items = response.get('Items', [])
        
        # Process tenants and count KSIs
        tenants_map = {}
        for item in items:
            tenant_id = item.get('tenant_id')
            if tenant_id and tenant_id not in tenants_map:
                tenants_map[tenant_id] = {
                    'tenant_id': tenant_id,
                    'ksi_count': 0,
                    'display_name': format_tenant_name(tenant_id)
                }
            
            if tenant_id:
                tenants_map[tenant_id]['ksi_count'] += 1
        
        # Convert to list and sort
        tenants = list(tenants_map.values())
        tenants.sort(key=lambda x: x['tenant_id'])
        
        print(f"✅ Retrieved {len(tenants)} tenants from DynamoDB")
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'tenants': tenants,
                'total_count': len(tenants)
            }, default=decimal_default)
        }
        
    except Exception as e:
        print(f"❌ Error retrieving tenants: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'error': 'Failed to retrieve tenants',
                'message': str(e)
            })
        }

def format_tenant_name(tenant_id):
    """Convert tenant-001 to 'Tenant 001' for better display"""
    if not tenant_id:
        return 'Unknown Tenant'
    
    # Handle common patterns
    if tenant_id.startswith('tenant-'):
        number = tenant_id.replace('tenant-', '')
        return f'Tenant {number.upper()}'
    elif tenant_id.startswith('real-test'):
        return 'Real Test Tenant'
    else:
        # Convert kebab-case to Title Case
        return tenant_id.replace('-', ' ').replace('_', ' ').title()

def decimal_default(obj):
    """JSON serializer for Decimal objects"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
