import json
import boto3
import logging
from datetime import datetime, timezone
import os
import uuid

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
sts_client = boto3.client('sts')

TENANT_METADATA_TABLE = os.environ['TENANT_METADATA_TABLE']
RISKUITY_ACCOUNT_ID = os.environ['RISKUITY_ACCOUNT_ID']

# Determine AWS partition based on region
def get_aws_partition():
    try:
        region = boto3.Session().region_name
        if region and region.startswith('us-gov-'):
            return 'aws-us-gov'
        else:
            return 'aws'
    except:
        return 'aws'

def lambda_handler(event, context):
    """
    Tenant onboarding API handler
    """
    try:
        logger.info(f"Tenant onboarding request: {json.dumps(event)}")
        
        # Parse request
        if 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            body = event
        
        action = body.get('action', 'onboard')
        
        if action == 'generate_role_instructions':
            return generate_role_instructions(body)
        elif action == 'test_connection':
            return test_connection(body)
        elif action == 'onboard':
            return onboard_tenant(body)
        elif action == 'list':
            return list_tenants(body)
        else:
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({'error': 'Invalid action'})
            }
            
    except Exception as e:
        logger.error(f"Error in tenant onboarding: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'error': str(e)})
        }

def generate_role_instructions(body):
    """Generate IAM role setup instructions with correct partition"""
    tenant_id = body.get('tenantId', f"tenant-{int(datetime.now().timestamp())}")
    external_id = f"riskuity-{tenant_id}-{datetime.now().strftime('%Y%m%d')}"
    partition = get_aws_partition()
    
    instructions = {
        "role_name": "RiskuityKSIValidatorRole",
        "external_id": external_id,
        "riskuity_account_id": RISKUITY_ACCOUNT_ID,
        "role_arn_template": f"arn:{partition}:iam::YOUR_ACCOUNT_ID:role/RiskuityKSIValidatorRole",
        "cli_commands": [
            f"""aws iam create-role --role-name RiskuityKSIValidatorRole --assume-role-policy-document '{{"Version":"2012-10-17","Statement":[{{"Effect":"Allow","Principal":{{"AWS":"arn:{partition}:iam::{RISKUITY_ACCOUNT_ID}:root"}},"Action":"sts:AssumeRole","Condition":{{"StringEquals":{{"sts:ExternalId":"{external_id}"}}}}}}]}}'""",
            f"aws iam attach-role-policy --role-name RiskuityKSIValidatorRole --policy-arn arn:{partition}:iam::aws:policy/SecurityAudit",
            f"aws iam attach-role-policy --role-name RiskuityKSIValidatorRole --policy-arn arn:{partition}:iam::aws:policy/ReadOnlyAccess"
        ]
    }
    
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Content-Type': 'application/json'
        },
        'body': json.dumps(instructions)
    }

def test_connection(body):
    """Test cross-account connection"""
    role_arn = body.get('roleArn')
    external_id = body.get('externalId')
    
    if not role_arn or not external_id:
        return {
            'statusCode': 400,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'error': 'roleArn and externalId required'})
        }
    
    try:
        # Test assume role
        response = sts_client.assume_role(
            RoleArn=role_arn,
            RoleSessionName=f"riskuity-test-{int(datetime.now().timestamp())}",
            ExternalId=external_id,
            DurationSeconds=3600
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'connection_status': 'SUCCESS',
                'message': 'Cross-account role assumption successful'
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'connection_status': 'FAILED',
                'error': str(e)
            })
        }

def onboard_tenant(body):
    """Complete tenant onboarding"""
    table = dynamodb.Table(TENANT_METADATA_TABLE)
    
    # Generate tenant ID
    tenant_id = f"tenant-{int(datetime.now().timestamp())}"
    
    # Create tenant metadata record
    tenant_data = {
        'tenant_id': tenant_id,
        'tenant_type': 'federal_customer',
        'onboarding_status': 'active',
        'organization': body.get('organization', {}),
        'contact_info': body.get('contacts', {}),
        'aws_configuration': body.get('awsAccounts', {}),
        'compliance_profile': body.get('compliance', {}),
        'ksi_configuration': body.get('preferences', {}),
        'metadata': {
            'created_date': datetime.now(timezone.utc).isoformat(),
            'created_by': 'onboarding_api',
            'status': 'active'
        }
    }
    
    # Save to DynamoDB
    table.put_item(Item=tenant_data)
    
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Content-Type': 'application/json'
        },
        'body': json.dumps({
            'tenant_id': tenant_id,
            'status': 'success',
            'message': 'Tenant onboarded successfully'
        })
    }

def list_tenants(body):
    """List all tenants"""
    try:
        table = dynamodb.Table(TENANT_METADATA_TABLE)
        
        response = table.scan()
        tenants = response.get('Items', [])
        
        # Format tenants for frontend display
        formatted_tenants = []
        for tenant in tenants:
            formatted_tenants.append({
                'tenant_id': tenant.get('tenant_id'),
                'display_name': tenant.get('organization', {}).get('name', tenant.get('tenant_id', 'Unknown')),
                'organization_type': tenant.get('organization', {}).get('type', 'unknown'),
                'status': tenant.get('onboarding_status', 'unknown'),
                'created_date': tenant.get('metadata', {}).get('created_date')
            })
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'tenants': formatted_tenants,
                'count': len(formatted_tenants)
            })
        }
        
    except Exception as e:
        logger.error(f"Error listing tenants: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'error': str(e)})
        }
