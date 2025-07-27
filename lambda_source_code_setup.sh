#!/bin/bash

# Create Lambda Source Code Structure for Tenant Management
# This creates the actual source files in your project

echo "🔧 Creating Lambda source code structure..."

# Create directories for Lambda source code
mkdir -p lambdas/tenant_onboarding
mkdir -p lambdas/cross_account_validator

# Create tenant onboarding API Lambda
cat > lambdas/tenant_onboarding/tenant_onboarding_api.py << 'EOF'
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
EOF

# Create requirements.txt for tenant onboarding
cat > lambdas/tenant_onboarding/requirements.txt << 'EOF'
boto3>=1.26.0
botocore>=1.29.0
EOF

# Create cross-account KSI validator Lambda
cat > lambdas/cross_account_validator/cross_account_ksi_validator.py << 'EOF'
import json
import boto3
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
sts_client = boto3.client('sts')

TENANT_METADATA_TABLE = os.environ['TENANT_METADATA_TABLE']
TENANT_KSI_CONFIGURATIONS_TABLE = os.environ['TENANT_KSI_CONFIGURATIONS_TABLE']
KSI_EXECUTION_HISTORY_TABLE = os.environ['KSI_EXECUTION_HISTORY_TABLE']

class CrossAccountKSIValidator:
    """
    Handles KSI validation across multiple customer AWS accounts
    """
    
    def __init__(self):
        self.tenant_metadata_table = dynamodb.Table(TENANT_METADATA_TABLE)
        self.tenant_config_table = dynamodb.Table(TENANT_KSI_CONFIGURATIONS_TABLE)
        self.execution_history_table = dynamodb.Table(KSI_EXECUTION_HISTORY_TABLE)
    
    def get_tenant_session(self, tenant_id: str) -> Optional[Dict]:
        """Get AWS session for tenant (either native or cross-account)"""
        try:
            # Get tenant metadata
            response = self.tenant_metadata_table.get_item(Key={'tenant_id': tenant_id})
            tenant = response.get('Item')
            
            if not tenant:
                logger.error(f"Tenant {tenant_id} not found")
                return None
            
            # Check if it's Riskuity's own account
            if tenant.get('tenant_type') == 'csp_internal':
                logger.info(f"Using native session for internal tenant {tenant_id}")
                return {
                    'session': boto3.Session(),
                    'account_id': tenant.get('aws_configuration', {}).get('account_id', 'unknown'),
                    'tenant_metadata': tenant
                }
            
            # For customer accounts, assume cross-account role
            aws_config = tenant.get('aws_configuration', {})
            role_arn = aws_config.get('cross_account_role_arn')
            external_id = aws_config.get('external_id')
            
            if not role_arn or not external_id:
                logger.error(f"Cross-account role not configured for tenant {tenant_id}")
                return None
            
            # Assume role in customer account
            logger.info(f"Assuming role {role_arn} for tenant {tenant_id}")
            response = sts_client.assume_role(
                RoleArn=role_arn,
                RoleSessionName=f"riskuity-ksi-validation-{tenant_id}-{int(datetime.now().timestamp())}",
                ExternalId=external_id,
                DurationSeconds=3600
            )
            
            credentials = response['Credentials']
            customer_session = boto3.Session(
                aws_access_key_id=credentials['AccessKeyId'],
                aws_secret_access_key=credentials['SecretAccessKey'],
                aws_session_token=credentials['SessionToken']
            )
            
            # Extract account ID from role ARN
            account_id = role_arn.split(':')[4]
            
            logger.info(f"Successfully assumed role for tenant {tenant_id} in account {account_id}")
            return {
                'session': customer_session,
                'account_id': account_id,
                'tenant_metadata': tenant
            }
            
        except Exception as e:
            logger.error(f"Error getting session for tenant {tenant_id}: {str(e)}")
            return None
    
    def validate_ksi_cna_01(self, session: boto3.Session, account_id: str) -> Dict:
        """KSI-CNA-01: Use logical networking to protect resources"""
        try:
            ec2_client = session.client('ec2')
            
            # Get VPCs
            vpcs = ec2_client.describe_vpcs()['Vpcs']
            security_groups = ec2_client.describe_security_groups()['SecurityGroups']
            
            issues = []
            
            # Check for default VPC usage
            default_vpcs = [vpc for vpc in vpcs if vpc.get('IsDefault', False)]
            if default_vpcs:
                issues.append("Default VPC is in use - consider using custom VPC")
            
            # Check for overly permissive security groups
            for sg in security_groups:
                for rule in sg.get('IpPermissions', []):
                    for ip_range in rule.get('IpRanges', []):
                        if ip_range.get('CidrIp') == '0.0.0.0/0':
                            issues.append(f"Security group {sg['GroupId']} allows inbound from 0.0.0.0/0")
            
            status = "PASS" if not issues else "FAIL"
            
            return {
                'ksi_id': 'KSI-CNA-01',
                'status': status,
                'account_id': account_id,
                'findings': {
                    'vpcs_count': len(vpcs),
                    'security_groups_count': len(security_groups),
                    'issues': issues
                },
                'evidence': {
                    'vpcs': [{'VpcId': vpc['VpcId'], 'CidrBlock': vpc['CidrBlock']} for vpc in vpcs[:5]],
                    'security_groups_summary': len(security_groups)
                }
            }
            
        except Exception as e:
            logger.error(f"Error validating KSI-CNA-01: {str(e)}")
            return {
                'ksi_id': 'KSI-CNA-01',
                'status': 'ERROR',
                'account_id': account_id,
                'error': str(e)
            }
    
    def validate_ksi_iam_01(self, session: boto3.Session, account_id: str) -> Dict:
        """KSI-IAM-01: Use multi-factor authentication"""
        try:
            iam_client = session.client('iam')
            
            # Get users
            users = iam_client.list_users()['Users']
            
            # Check MFA devices for each user
            users_without_mfa = []
            users_with_mfa = []
            
            for user in users[:10]:  # Limit to first 10 users
                try:
                    mfa_devices = iam_client.list_mfa_devices(UserName=user['UserName'])['MFADevices']
                    if not mfa_devices:
                        users_without_mfa.append(user['UserName'])
                    else:
                        users_with_mfa.append(user['UserName'])
                except Exception:
                    # Skip users we can't check
                    continue
            
            issues = []
            if users_without_mfa:
                issues.append(f"{len(users_without_mfa)} users without MFA")
            
            status = "PASS" if len(users_with_mfa) > len(users_without_mfa) else "FAIL"
            
            return {
                'ksi_id': 'KSI-IAM-01',
                'status': status,
                'account_id': account_id,
                'findings': {
                    'total_users_checked': len(users_with_mfa) + len(users_without_mfa),
                    'users_with_mfa': len(users_with_mfa),
                    'users_without_mfa': len(users_without_mfa),
                    'issues': issues
                },
                'evidence': {
                    'mfa_compliance_rate': f"{len(users_with_mfa)}/{len(users_with_mfa) + len(users_without_mfa)} users"
                }
            }
            
        except Exception as e:
            logger.error(f"Error validating KSI-IAM-01: {str(e)}")
            return {
                'ksi_id': 'KSI-IAM-01',
                'status': 'ERROR',
                'account_id': account_id,
                'error': str(e)
            }
    
    def validate_ksi_svc_01(self, session: boto3.Session, account_id: str) -> Dict:
        """KSI-SVC-01: Harden and review network and system configurations"""
        try:
            ec2_client = session.client('ec2')
            
            # Check EC2 instances
            instances = ec2_client.describe_instances()
            running_instances = []
            
            for reservation in instances['Reservations']:
                for instance in reservation['Instances']:
                    if instance['State']['Name'] == 'running':
                        running_instances.append(instance)
            
            issues = []
            
            # Check for instances without monitoring
            instances_without_monitoring = [
                inst for inst in running_instances 
                if not inst.get('Monitoring', {}).get('State') == 'enabled'
            ]
            if instances_without_monitoring:
                issues.append(f"{len(instances_without_monitoring)} EC2 instances without detailed monitoring")
            
            status = "PASS" if not issues else "FAIL"
            
            return {
                'ksi_id': 'KSI-SVC-01',
                'status': status,
                'account_id': account_id,
                'findings': {
                    'running_instances': len(running_instances),
                    'instances_without_monitoring': len(instances_without_monitoring),
                    'issues': issues
                },
                'evidence': {
                    'services_checked': ['EC2'],
                    'hardening_checks': ['monitoring']
                }
            }
            
        except Exception as e:
            logger.error(f"Error validating KSI-SVC-01: {str(e)}")
            return {
                'ksi_id': 'KSI-SVC-01',
                'status': 'ERROR',
                'account_id': account_id,
                'error': str(e)
            }
    
    def validate_ksi_mla_01(self, session: boto3.Session, account_id: str) -> Dict:
        """KSI-MLA-01: Monitoring, Logging & Alerting"""
        try:
            cloudwatch_client = session.client('cloudwatch')
            cloudtrail_client = session.client('cloudtrail')
            logs_client = session.client('logs')
            
            # Check CloudTrail
            trails = cloudtrail_client.describe_trails()['trailList']
            
            # Check CloudWatch Alarms
            alarms = cloudwatch_client.describe_alarms(MaxRecords=10)['MetricAlarms']
            
            # Check Log Groups
            log_groups = logs_client.describe_log_groups(limit=10)['logGroups']
            
            issues = []
            
            if len(trails) == 0:
                issues.append("No CloudTrail trails found")
            
            if len(alarms) == 0:
                issues.append("No CloudWatch alarms configured")
            
            if len(log_groups) == 0:
                issues.append("No CloudWatch log groups found")
            
            status = "PASS" if len(issues) < 2 else "FAIL"
            
            return {
                'ksi_id': 'KSI-MLA-01',
                'status': status,
                'account_id': account_id,
                'findings': {
                    'cloudtrail_trails': len(trails),
                    'cloudwatch_alarms': len(alarms),
                    'log_groups': len(log_groups),
                    'issues': issues
                },
                'evidence': {
                    'monitoring_services': ['CloudTrail', 'CloudWatch', 'CloudWatch Logs'],
                    'compliance_checks': ['trails_configured', 'alarms_configured', 'logs_available']
                }
            }
            
        except Exception as e:
            logger.error(f"Error validating KSI-MLA-01: {str(e)}")
            return {
                'ksi_id': 'KSI-MLA-01',
                'status': 'ERROR',
                'account_id': account_id,
                'error': str(e)
            }
    
    def validate_tenant_ksis(self, tenant_id: str) -> Dict:
        """Main function to validate all KSIs for a tenant"""
        execution_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        
        logger.info(f"Starting KSI validation for tenant {tenant_id} - execution {execution_id}")
        
        # Get tenant session
        tenant_session_info = self.get_tenant_session(tenant_id)
        if not tenant_session_info:
            return {
                'execution_id': execution_id,
                'tenant_id': tenant_id,
                'status': 'ERROR',
                'error': 'Unable to establish session with tenant account'
            }
        
        session = tenant_session_info['session']
        account_id = tenant_session_info['account_id']
        tenant_metadata = tenant_session_info['tenant_metadata']
        
        # Get tenant's KSI configuration
        try:
            config_response = self.tenant_config_table.query(
                KeyConditionExpression='tenant_id = :tid',
                ExpressionAttributeValues={':tid': tenant_id}
            )
            tenant_configs = config_response.get('Items', [])
        except Exception as e:
            logger.error(f"Error getting tenant configuration: {str(e)}")
            tenant_configs = []
        
        # If no specific configuration, use default KSIs
        if not tenant_configs:
            logger.info(f"No specific configuration for {tenant_id}, using default KSIs")
            tenant_configs = [
                {'ksi_id': 'KSI-CNA-01', 'enabled': True},
                {'ksi_id': 'KSI-IAM-01', 'enabled': True},
                {'ksi_id': 'KSI-SVC-01', 'enabled': True},
                {'ksi_id': 'KSI-MLA-01', 'enabled': True}
            ]
        
        # Execute KSI validations
        validation_results = []
        enabled_ksis = [config for config in tenant_configs if config.get('enabled', True)]
        
        for ksi_config in enabled_ksis:
            ksi_id = ksi_config['ksi_id']
            logger.info(f"Validating {ksi_id} for tenant {tenant_id}")
            
            try:
                if ksi_id == 'KSI-CNA-01':
                    result = self.validate_ksi_cna_01(session, account_id)
                elif ksi_id == 'KSI-IAM-01':
                    result = self.validate_ksi_iam_01(session, account_id)
                elif ksi_id == 'KSI-SVC-01':
                    result = self.validate_ksi_svc_01(session, account_id)
                elif ksi_id == 'KSI-MLA-01':
                    result = self.validate_ksi_mla_01(session, account_id)
                else:
                    result = {
                        'ksi_id': ksi_id,
                        'status': 'SKIPPED',
                        'account_id': account_id,
                        'reason': 'Validation not implemented'
                    }
                
                result['tenant_id'] = tenant_id
                result['execution_id'] = execution_id
                result['timestamp'] = timestamp
                validation_results.append(result)
                
            except Exception as e:
                logger.error(f"Error validating {ksi_id}: {str(e)}")
                validation_results.append({
                    'ksi_id': ksi_id,
                    'status': 'ERROR',
                    'tenant_id': tenant_id,
                    'account_id': account_id,
                    'execution_id': execution_id,
                    'timestamp': timestamp,
                    'error': str(e)
                })
        
        # Calculate overall status
        passed = len([r for r in validation_results if r['status'] == 'PASS'])
        failed = len([r for r in validation_results if r['status'] == 'FAIL'])
        errors = len([r for r in validation_results if r['status'] == 'ERROR'])
        
        overall_status = 'PASS' if failed == 0 and errors == 0 else 'FAIL'
        
        # Save execution record
        execution_record = {
            'execution_id': execution_id,
            'timestamp': timestamp,
            'tenant_id': tenant_id,
            'account_id': account_id,
            'status': overall_status,
            'ksis_validated': len(validation_results),
            'ksis_passed': passed,
            'ksis_failed': failed,
            'ksis_errors': errors,
            'tenant_type': tenant_metadata.get('tenant_type', 'unknown'),
            'organization_name': tenant_metadata.get('organization', {}).get('name', 'Unknown'),
            'validation_results': validation_results,
            'ttl': int((datetime.now(timezone.utc).timestamp() + (90 * 24 * 60 * 60)))  # 90 days TTL
        }
        
        try:
            self.execution_history_table.put_item(Item=execution_record)
            logger.info(f"Saved execution record for {tenant_id}")
        except Exception as e:
            logger.error(f"Error saving execution record: {str(e)}")
        
        return {
            'execution_id': execution_id,
            'tenant_id': tenant_id,
            'account_id': account_id,
            'status': overall_status,
            'summary': {
                'total_ksis': len(validation_results),
                'passed': passed,
                'failed': failed,
                'errors': errors
            },
            'results': validation_results
        }

def lambda_handler(event, context):
    """Lambda handler for cross-account KSI validation"""
    try:
        logger.info(f"Cross-Account KSI Validator started with event: {json.dumps(event)}")
        
        validator = CrossAccountKSIValidator()
        
        # Handle different event types
        if event.get('validate_all_tenants'):
            # Get all active tenants and validate each
            tenant_table = dynamodb.Table(TENANT_METADATA_TABLE)
            response = tenant_table.scan(
                FilterExpression='onboarding_status = :status',
                ExpressionAttributeValues={':status': 'active'}
            )
            
            results = []
            for tenant in response['Items']:
                tenant_id = tenant['tenant_id']
                try:
                    result = validator.validate_tenant_ksis(tenant_id)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error validating tenant {tenant_id}: {str(e)}")
                    results.append({
                        'tenant_id': tenant_id,
                        'status': 'ERROR',
                        'error': str(e)
                    })
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': f'Validated {len(results)} tenants',
                    'results': results
                })
            }
        
        # Single tenant validation
        tenant_id = event.get('tenant_id')
        if not tenant_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'tenant_id is required'})
            }
        
        # Validate single tenant
        result = validator.validate_tenant_ksis(tenant_id)
        
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
        
    except Exception as e:
        logger.error(f"Cross-Account KSI Validator error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
EOF

# Create requirements.txt for cross-account validator
cat > lambdas/cross_account_validator/requirements.txt << 'EOF'
boto3>=1.26.0
botocore>=1.29.0
EOF

# Create deployment script
cat > scripts/package_lambdas.sh << 'EOF'
#!/bin/bash

echo "📦 Packaging Lambda functions..."

# Create lambda packages directory
mkdir -p terraform/lambda_packages

# Package tenant onboarding API
echo "Packaging tenant onboarding API..."
cd lambdas/tenant_onboarding
zip -r ../../terraform/lambda_packages/tenant_onboarding_api.zip .
cd ../..

# Package cross-account validator
echo "Packaging cross-account validator..."
cd lambdas/cross_account_validator
zip -r ../../terraform/lambda_packages/cross_account_ksi_validator.zip .
cd ../..

echo "✅ Lambda packages created:"
ls -la terraform/lambda_packages/

echo ""
echo "🚀 Next steps:"
echo "1. terraform plan"
echo "2. terraform apply"
echo "3. python3 scripts/initialize_riskuity_tenant.py"
EOF

chmod +x scripts/package_lambdas.sh

echo "✅ Created Lambda source code structure:"
echo ""
echo "📁 Directory structure:"
echo "lambdas/"
echo "├── tenant_onboarding/"
echo "│   ├── tenant_onboarding_api.py"
echo "│   └── requirements.txt"
echo "└── cross_account_validator/"
echo "    ├── cross_account_ksi_validator.py"
echo "    └── requirements.txt"
echo ""
echo "scripts/"
echo "└── package_lambdas.sh"
echo ""
echo "🔧 To update Lambda packages:"
echo "   ./scripts/package_lambdas.sh"
echo ""
echo "🚀 To deploy updates:"
echo "   terraform apply"
