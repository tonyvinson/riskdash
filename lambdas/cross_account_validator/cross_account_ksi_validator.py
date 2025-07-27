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
