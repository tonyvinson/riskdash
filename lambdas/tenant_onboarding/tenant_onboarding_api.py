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
TENANT_KSI_CONFIGURATIONS_TABLE = os.environ['TENANT_KSI_CONFIGURATIONS_TABLE']
RISKUITY_ACCOUNT_ID = os.environ['RISKUITY_ACCOUNT_ID']

def lambda_handler(event, context):
    """
    Tenant onboarding API handler
    Handles customer registration and AWS role setup
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
        elif action == 'list_tenants':
            return list_tenants()
        else:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Invalid action'})
            }
            
    except Exception as e:
        logger.error(f"Error in tenant onboarding: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)})
        }

def generate_role_instructions(body):
    """Generate IAM role setup instructions for customers"""
    tenant_id = body.get('tenantId', f"tenant-{int(datetime.now().timestamp())}")
    customer_account_id = body.get('accountId', 'YOUR_ACCOUNT_ID')
    external_id = f"riskuity-{tenant_id}-{datetime.now().strftime('%Y%m%d')}"
    
    instructions = {
        "overview": {
            "title": "AWS Cross-Account Role Setup for Riskuity KSI Validator",
            "description": "Create an IAM role that allows Riskuity secure, read-only access for compliance validation",
            "estimated_time": "10-15 minutes"
        },
        "step_1_create_role": {
            "title": "Create IAM Role",
            "role_name": "RiskuityKSIValidatorRole",
            "aws_console_url": f"https://console.aws.amazon.com/iam/home#/roles$new?step=type&roleType=crossAccount&accountID={RISKUITY_ACCOUNT_ID}",
            "cli_command": f"""aws iam create-role \\
  --role-name RiskuityKSIValidatorRole \\
  --assume-role-policy-document '{{
    "Version": "2012-10-17",
    "Statement": [
      {{
        "Effect": "Allow",
        "Principal": {{
          "AWS": "arn:aws:iam::{RISKUITY_ACCOUNT_ID}:root"
        }},
        "Action": "sts:AssumeRole",
        "Condition": {{
          "StringEquals": {{
            "sts:ExternalId": "{external_id}"
          }}
        }}
      }}
    ]
  }}'"""
        },
        "step_2_attach_policies": {
            "title": "Attach Required Policies",
            "required_policies": [
                {
                    "name": "SecurityAudit",
                    "arn": "arn:aws:iam::aws:policy/SecurityAudit",
                    "description": "Provides read-only access to security-related resources"
                },
                {
                    "name": "ReadOnlyAccess", 
                    "arn": "arn:aws:iam::aws:policy/ReadOnlyAccess",
                    "description": "Provides read-only access to all AWS resources"
                }
            ],
            "cli_commands": [
                "aws iam attach-role-policy --role-name RiskuityKSIValidatorRole --policy-arn arn:aws:iam::aws:policy/SecurityAudit",
                "aws iam attach-role-policy --role-name RiskuityKSIValidatorRole --policy-arn arn:aws:iam::aws:policy/ReadOnlyAccess"
            ]
        },
        "step_3_verification": {
            "title": "Verify Setup",
            "role_arn": f"arn:aws:iam::{customer_account_id}:role/RiskuityKSIValidatorRole",
            "external_id": external_id,
            "test_command": "Use the 'Test Connection' button in the Riskuity onboarding portal"
        },
        "configuration": {
            "external_id": external_id,
            "riskuity_account_id": RISKUITY_ACCOUNT_ID,
            "role_arn_template": f"arn:aws:iam::{customer_account_id}:role/RiskuityKSIValidatorRole"
        },
        "security_notes": {
            "principle_of_least_privilege": "This role provides only read-only access required for security validations",
            "external_id": "The external ID prevents unauthorized access even if someone knows your account ID", 
            "auditing": "All actions taken by Riskuity are logged in your CloudTrail",
            "revocation": "You can delete this role at any time to revoke access"
        }
    }
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'success': True,
            'instructions': instructions
        })
    }

def test_connection(body):
    """Test cross-account connection by attempting to assume role"""
    role_arn = body.get('roleArn')
    external_id = body.get('externalId')
    
    if not role_arn or not external_id:
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': 'roleArn and externalId are required'
            })
        }
    
    try:
        # Test assume role
        response = sts_client.assume_role(
            RoleArn=role_arn,
            RoleSessionName=f"riskuity-test-{int(datetime.now().timestamp())}",
            ExternalId=external_id,
            DurationSeconds=3600
        )
        
        # Try a basic operation with assumed credentials
        credentials = response['Credentials']
        temp_session = boto3.Session(
            aws_access_key_id=credentials['AccessKeyId'],
            aws_secret_access_key=credentials['SecretAccessKey'],
            aws_session_token=credentials['SessionToken']
        )
        
        # Test basic permissions
        ec2_client = temp_session.client('ec2')
        ec2_client.describe_regions(MaxResults=1)  # Simple test
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'connection_status': 'SUCCESS',
                'message': 'Cross-account role assumption successful',
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Connection test failed: {str(e)}")
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'connection_status': 'FAILED',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        }

def onboard_tenant(body):
    """Complete tenant onboarding process"""
    table = dynamodb.Table(TENANT_METADATA_TABLE)
    config_table = dynamodb.Table(TENANT_KSI_CONFIGURATIONS_TABLE)
    
    # Generate unique tenant ID
    tenant_id = f"tenant-{int(datetime.now().timestamp())}"
    
    # Create comprehensive tenant metadata record
    tenant_data = {
        'tenant_id': tenant_id,
        'tenant_type': 'federal_customer',
        'onboarding_status': 'active',
        'organization': {
            'name': body.get('organization', {}).get('name'),
            'display_name': body.get('organization', {}).get('name'),
            'type': body.get('organization', {}).get('type'),
            'federal_entity': body.get('organization', {}).get('federalEntity', False),
            'industry': body.get('organization', {}).get('industry'),
            'size': body.get('organization', {}).get('size'),
            'duns_number': body.get('organization', {}).get('dunsNumber'),
            'cage_code': body.get('organization', {}).get('cageCode')
        },
        'contact_info': {
            'primary_contact': {
                'name': body.get('contacts', {}).get('primaryName'),
                'email': body.get('contacts', {}).get('primaryEmail'),
                'phone': body.get('contacts', {}).get('primaryPhone'),
                'role': body.get('contacts', {}).get('primaryRole')
            },
            'technical_contact': {
                'name': body.get('contacts', {}).get('technicalName'),
                'email': body.get('contacts', {}).get('technicalEmail'),
                'phone': body.get('contacts', {}).get('technicalPhone'),
                'role': body.get('contacts', {}).get('technicalRole')
            },
            'billing_contact': {
                'name': body.get('contacts', {}).get('billingName'),
                'email': body.get('contacts', {}).get('billingEmail'),
                'phone': body.get('contacts', {}).get('billingPhone'),
                'role': body.get('contacts', {}).get('billingRole')
            }
        },
        'aws_configuration': {
            'account_id': body.get('awsAccounts', {}).get('primaryAccountId'),
            'primary_region': body.get('awsAccounts', {}).get('primaryRegion'),
            'access_method': 'cross_account',
            'cross_account_role_arn': body.get('awsAccounts', {}).get('roleArn'),
            'external_id': body.get('awsAccounts', {}).get('externalId'),
            'connection_status': 'configured',
            'account_purpose': body.get('awsAccounts', {}).get('purpose')
        },
        'compliance_profile': {
            'fedramp_level': body.get('compliance', {}).get('fedrampLevel'),
            'target_compliance': body.get('compliance', {}).get('frameworks', []),
            'authorization_boundary': body.get('compliance', {}).get('authorizationBoundary'),
            'current_status': body.get('compliance', {}).get('currentStatus')
        },
        'ksi_configuration': {
            'validation_frequency': body.get('preferences', {}).get('validationFrequency', 'daily'),
            'automated_remediation': body.get('preferences', {}).get('automatedRemediation', False),
            'notification_preferences': {
                'email': [body.get('preferences', {}).get('notificationEmail')],
                'additional_emails': body.get('preferences', {}).get('additionalEmails', '').split(',') if body.get('preferences', {}).get('additionalEmails') else [],
                'slack_webhook': body.get('preferences', {}).get('slackWebhook')
            }
        },
        'subscription': {
            'plan': 'standard',
            'status': 'active',
            'billing_cycle': 'monthly',
            'max_aws_accounts': 1,
            'support_level': 'standard'
        },
        'metadata': {
            'created_date': datetime.now(timezone.utc).isoformat(),
            'last_updated': datetime.now(timezone.utc).isoformat(),
            'created_by': 'onboarding_api',
            'status': 'active',
            'onboarding_completed': True
        }
    }
    
    try:
        # Save tenant metadata
        table.put_item(Item=tenant_data)
        
        # Create default KSI configurations
        default_ksis = [
            'KSI-CNA-01', 'KSI-IAM-01', 'KSI-SVC-01', 'KSI-MLA-01'
        ]
        
        for ksi_id in default_ksis:
            ksi_config = {
                'tenant_id': tenant_id,
                'ksi_id': ksi_id,
                'enabled': True,
                'priority': 'high',
                'schedule': body.get('preferences', {}).get('validationFrequency', 'daily'),
                'last_updated': datetime.now(timezone.utc).isoformat()
            }
            config_table.put_item(Item=ksi_config)
        
        logger.info(f"Tenant onboarded successfully: {tenant_id}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'tenant_id': tenant_id,
                'message': 'Tenant onboarded successfully',
                'next_steps': [
                    'Verify AWS cross-account role setup',
                    'Run initial KSI validation',
                    'Configure notification preferences',
                    'Review compliance dashboard'
                ]
            })
        }
        
    except Exception as e:
        logger.error(f"Error saving tenant data: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': f'Failed to save tenant data: {str(e)}'
            })
        }

def list_tenants():
    """List all tenants with metadata for dropdown"""
    table = dynamodb.Table(TENANT_METADATA_TABLE)
    config_table = dynamodb.Table(TENANT_KSI_CONFIGURATIONS_TABLE)
    
    try:
        # Get all active tenants
        response = table.scan(
            FilterExpression='onboarding_status = :status',
            ExpressionAttributeValues={':status': 'active'}
        )
        
        tenants = []
        for tenant in response['Items']:
            # Get KSI count for this tenant
            ksi_response = config_table.query(
                KeyConditionExpression='tenant_id = :tid',
                ExpressionAttributeValues={':tid': tenant['tenant_id']}
            )
            
            enabled_ksis = len([item for item in ksi_response.get('Items', []) if item.get('enabled')])
            
            tenant_summary = {
                'id': tenant['tenant_id'],
                'name': tenant.get('organization', {}).get('display_name') or tenant.get('organization', {}).get('name') or tenant['tenant_id'],
                'tenant_type': tenant.get('tenant_type'),
                'ksi_count': enabled_ksis,
                'total_ksi_count': len(ksi_response.get('Items', [])),
                'aws_account': tenant.get('aws_configuration', {}).get('account_id'),
                'compliance_level': tenant.get('compliance_profile', {}).get('fedramp_level'),
                'last_updated': tenant.get('metadata', {}).get('last_updated')
            }
            tenants.append(tenant_summary)
        
        # Sort tenants - internal first, then by name
        tenants.sort(key=lambda x: (x['tenant_type'] != 'csp_internal', x['name']))
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'tenants': tenants,
                'count': len(tenants)
            })
        }
        
    except Exception as e:
        logger.error(f"Error listing tenants: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': str(e),
                # Fallback data
                'tenants': [{
                    'id': 'riskuity-internal',
                    'name': 'Riskuity (Internal)',
                    'tenant_type': 'csp_internal',
                    'ksi_count': 4,
                    'total_ksi_count': 4
                }]
            })
        }
