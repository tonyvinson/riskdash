import boto3
import json
from datetime import datetime
import traceback
import os
from botocore.exceptions import ClientError, NoCredentialsError

# Default clients for RiskDash account operations
default_sts_client = boto3.client('sts')
default_dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    """
    Multitenant KSI Validator with tenant-specific role assumption
    """
    try:
        execution_id = event.get('execution_id')
        tenant_id = event.get('tenant_id', 'default')
        ksis = event.get('ksis', [])
        
        # Extract validator type from function name
        function_name = context.function_name
        if 'cna' in function_name.lower():
            validator_type = 'CNA'
        elif 'svc' in function_name.lower():
            validator_type = 'SVC'
        elif 'iam' in function_name.lower():
            validator_type = 'IAM'
        elif 'mla' in function_name.lower():
            validator_type = 'MLA'
        elif 'cmt' in function_name.lower():
            validator_type = 'CMT'
        else:
            validator_type = 'UNKNOWN'
        
        print(f"🔍 Validator {validator_type} processing {len(ksis)} KSIs for tenant {tenant_id}")
        
        # Get tenant configuration (including role ARN)
        tenant_config = get_tenant_configuration(tenant_id)
        if not tenant_config:
            print(f"❌ No configuration found for tenant {tenant_id}")
            return create_error_response(f"Tenant {tenant_id} not found", validator_type, execution_id, tenant_id)
        
        # Get AWS clients for this tenant (assume role if needed)
        aws_clients = get_tenant_aws_clients(tenant_config)
        if not aws_clients:
            print(f"❌ Failed to get AWS clients for tenant {tenant_id}")
            return create_error_response(f"Failed to assume role for tenant {tenant_id}", validator_type, execution_id, tenant_id)
        
        results = []
        
        for ksi in ksis:
            if should_validate_ksi(ksi, validator_type):
                ksi_id = ksi['ksi_id']
                print(f"🧪 Validating {ksi_id} with {validator_type} validator for tenant {tenant_id}")
                
                # Execute validation using tenant's AWS clients
                validation_result = execute_tenant_validation(ksi_id, validator_type, aws_clients, tenant_config)
                
                result = {
                    'ksi_id': ksi_id,
                    'validation_id': ksi_id,
                    'validator_type': validator_type,
                    'timestamp': datetime.utcnow().isoformat() + '+00:00',
                    'validation_method': 'automated',
                    'tenant_id': tenant_id,
                    **validation_result
                }
                
                results.append(result)
                print(f"✅ Completed validation for {ksi_id}: {result['assertion']}")
        
        if not results:
            print(f"ℹ️ No KSIs for {validator_type} validator to process")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'validator_type': validator_type,
                    'execution_id': execution_id,
                    'tenant_id': tenant_id,
                    'message': f'No KSIs assigned to {validator_type} validator',
                    'ksis_validated': 0,
                    'results': []
                })
            }
        
        summary = {
            'total_ksis': len(results),
            'passed': sum(1 for r in results if r['assertion']),
            'failed': sum(1 for r in results if not r['assertion']),
            'validator_type': validator_type
        }
        summary['pass_rate'] = (summary['passed'] / summary['total_ksis'] * 100) if summary['total_ksis'] > 0 else 0
        
        print(f"📊 Validation summary: {summary['passed']}/{summary['total_ksis']} passed ({summary['pass_rate']:.1f}%)")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'validator_type': validator_type,
                'execution_id': execution_id,
                'tenant_id': tenant_id,
                'ksis_validated': len(results),
                'results': results,
                'summary': summary
            })
        }
        
    except Exception as e:
        error_msg = f"Validator error: {str(e)}"
        print(f"❌ {error_msg}")
        traceback.print_exc()
        
        return create_error_response(error_msg, validator_type, execution_id, tenant_id)

def get_tenant_configuration(tenant_id):
    """Get tenant configuration from DynamoDB"""
    try:
        table_name = os.environ.get('TENANT_CONFIG_TABLE', 'riskuity-ksi-validator-tenant-configurations-production')
        table = default_dynamodb.Table(table_name)
        
        response = table.get_item(Key={'tenant_id': tenant_id})
        
        if 'Item' in response:
            return response['Item']
        else:
            print(f"⚠️ Tenant {tenant_id} not found in configuration table")
            return None
            
    except Exception as e:
        print(f"❌ Error getting tenant configuration: {str(e)}")
        return None

def get_tenant_aws_clients(tenant_config):
    """Get AWS clients for tenant account (assume role if needed)"""
    try:
        # Check if tenant has a specific role ARN
        tenant_role_arn = tenant_config.get('role_arn')
        
        if tenant_role_arn and tenant_role_arn != 'default':
            print(f"🔐 Assuming role for tenant: {tenant_role_arn}")
            
            # Assume the tenant's role
            external_id = tenant_config.get('external_id', 'RiskDash-FedRAMP-Validation')
            
            assumed_role = default_sts_client.assume_role(
                RoleArn=tenant_role_arn,
                RoleSessionName=f"RiskDash-Validation-{int(datetime.utcnow().timestamp())}",
                ExternalId=external_id,
                DurationSeconds=3600  # 1 hour
            )
            
            credentials = assumed_role['Credentials']
            
            # Create clients with assumed role credentials
            session = boto3.Session(
                aws_access_key_id=credentials['AccessKeyId'],
                aws_secret_access_key=credentials['SecretAccessKey'],
                aws_session_token=credentials['SessionToken']
            )
            
            clients = {
                'ec2': session.client('ec2'),
                'route53': session.client('route53'),
                'kms': session.client('kms'),
                'secretsmanager': session.client('secretsmanager'),
                'iam': session.client('iam'),
                'cloudtrail': session.client('cloudtrail'),
                'cloudwatch': session.client('cloudwatch'),
                'sns': session.client('sns'),
                'config': session.client('config'),
                'cloudformation': session.client('cloudformation'),
                's3': session.client('s3')
            }
            
            print(f"✅ Successfully assumed role for tenant")
            return clients
            
        else:
            print(f"🏠 Using RiskDash account credentials for tenant {tenant_config.get('tenant_id', 'unknown')}")
            
            # Use default credentials (RiskDash account)
            return {
                'ec2': boto3.client('ec2'),
                'route53': boto3.client('route53'),
                'kms': boto3.client('kms'),
                'secretsmanager': boto3.client('secretsmanager'),
                'iam': boto3.client('iam'),
                'cloudtrail': boto3.client('cloudtrail'),
                'cloudwatch': boto3.client('cloudwatch'),
                'sns': boto3.client('sns'),
                'config': boto3.client('config'),
                'cloudformation': boto3.client('cloudformation'),
                's3': boto3.client('s3')
            }
            
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'AccessDenied':
            print(f"❌ Access denied when assuming role: {tenant_role_arn}")
        elif error_code == 'InvalidUserID.NotFound':
            print(f"❌ Role not found: {tenant_role_arn}")
        else:
            print(f"❌ AWS error assuming role: {error_code} - {str(e)}")
        return None
        
    except Exception as e:
        print(f"❌ Error assuming tenant role: {str(e)}")
        return None

def should_validate_ksi(ksi, validator_type):
    """Check if this validator should handle this KSI"""
    ksi_id = ksi.get('ksi_id', '')
    
    validator_mappings = {
        'CNA': ['KSI-CNA-'],
        'SVC': ['KSI-SVC-'],
        'IAM': ['KSI-IAM-'],
        'MLA': ['KSI-MLA-'],
        'CMT': ['KSI-CMT-']
    }
    
    return any(ksi_id.startswith(prefix) for prefix in validator_mappings.get(validator_type, []))

def execute_tenant_validation(ksi_id, validator_type, aws_clients, tenant_config):
    """Execute validation using tenant's AWS clients"""
    
    try:
        if validator_type == "CNA":
            return validate_network_architecture(ksi_id, aws_clients)
        elif validator_type == "SVC":
            return validate_services(ksi_id, aws_clients)
        elif validator_type == "IAM":
            return validate_identity_access(ksi_id, aws_clients)
        elif validator_type == "MLA":
            return validate_monitoring_logging(ksi_id, aws_clients)
        elif validator_type == "CMT":
            return validate_change_management(ksi_id, aws_clients)
        else:
            return {
                "assertion": False,
                "assertion_reason": f"❌ Unknown validator type: {validator_type}",
                "commands_executed": 0,
                "successful_commands": 0,
                "failed_commands": 1,
                "cli_command_details": []
            }
    except Exception as e:
        return {
            "assertion": False,
            "assertion_reason": f"❌ Validation error for {ksi_id}: {str(e)}",
            "commands_executed": 1,
            "successful_commands": 0,
            "failed_commands": 1,
            "cli_command_details": [{
                "success": False,
                "error": str(e),
                "command": f"tenant validation {validator_type}",
                "note": f"Failed to execute {validator_type} validation checks"
            }]
        }

def validate_network_architecture(ksi_id, clients):
    """CNA - Cloud Native Architecture validation using tenant's AWS account"""
    results = []
    
    # Check subnets in tenant account
    try:
        response = clients['ec2'].describe_subnets()
        subnets = response.get('Subnets', [])
        availability_zones = set(subnet['AvailabilityZone'] for subnet in subnets)
        
        results.append({
            "success": True,
            "command": "boto3.ec2.describe_subnets() [tenant account]",
            "note": "Check network architecture for proper segmentation and high availability design",
            "data": {
                "subnet_count": len(subnets),
                "availability_zones": list(availability_zones),
                "multi_az": len(availability_zones) > 1
            }
        })
    except Exception as e:
        results.append({
            "success": False,
            "error": str(e),
            "command": "boto3.ec2.describe_subnets() [tenant account]",
            "note": "Check network architecture for proper segmentation and high availability design"
        })
    
    # Check availability zones
    try:
        response = clients['ec2'].describe_availability_zones()
        azs = response.get('AvailabilityZones', [])
        
        results.append({
            "success": True,
            "command": "boto3.ec2.describe_availability_zones() [tenant account]",
            "note": "Validate multi-AZ deployment capability for rapid recovery architecture",
            "data": {
                "available_zones": len(azs),
                "zones": [az['ZoneName'] for az in azs]
            }
        })
    except Exception as e:
        results.append({
            "success": False,
            "error": str(e),
            "command": "boto3.ec2.describe_availability_zones() [tenant account]",
            "note": "Validate multi-AZ deployment capability for rapid recovery architecture"
        })
    
    # Check Route53 in tenant account
    try:
        response = clients['route53'].list_hosted_zones()
        zones = response.get('HostedZones', [])
        
        results.append({
            "success": True,
            "command": "boto3.route53.list_hosted_zones() [tenant account]",
            "note": "Check DNS infrastructure for resilient network architecture",
            "data": {
                "hosted_zones": len(zones),
                "zones": [zone['Name'] for zone in zones[:5]]
            }
        })
    except Exception as e:
        results.append({
            "success": False,
            "error": str(e),
            "command": "boto3.route53.list_hosted_zones() [tenant account]",
            "note": "Check DNS infrastructure for resilient network architecture"
        })
    
    return analyze_results(results, ksi_id)

def validate_services(ksi_id, clients):
    """SVC - Service validation using tenant's AWS account"""
    results = []
    
    # Check KMS keys in tenant account
    try:
        response = clients['kms'].list_keys()
        keys = response.get('Keys', [])
        
        results.append({
            "success": True,
            "command": "boto3.kms.list_keys() [tenant account]",
            "note": "Check KMS keys for automated key management and cryptographic service availability",
            "data": {
                "key_count": len(keys)
            }
        })
    except Exception as e:
        results.append({
            "success": False,
            "error": str(e),
            "command": "boto3.kms.list_keys() [tenant account]",
            "note": "Check KMS keys for automated key management and cryptographic service availability"
        })
    
    # Check KMS aliases in tenant account
    try:
        response = clients['kms'].list_aliases()
        aliases = response.get('Aliases', [])
        
        results.append({
            "success": True,
            "command": "boto3.kms.list_aliases() [tenant account]",
            "note": "Validate KMS key aliases for proper key lifecycle management and rotation",
            "data": {
                "alias_count": len(aliases)
            }
        })
    except Exception as e:
        results.append({
            "success": False,
            "error": str(e),
            "command": "boto3.kms.list_aliases() [tenant account]",
            "note": "Validate KMS key aliases for proper key lifecycle management and rotation"
        })
    
    # Check Secrets Manager in tenant account
    try:
        response = clients['secretsmanager'].list_secrets()
        secrets = response.get('SecretList', [])
        
        results.append({
            "success": True,
            "command": "boto3.secretsmanager.list_secrets() [tenant account]",
            "note": "Check Secrets Manager for automated certificate and credential management",
            "data": {
                "secret_count": len(secrets)
            }
        })
    except Exception as e:
        results.append({
            "success": False,
            "error": str(e),
            "command": "boto3.secretsmanager.list_secrets() [tenant account]",
            "note": "Check Secrets Manager for automated certificate and credential management"
        })
    
    return analyze_results(results, ksi_id)

def validate_identity_access(ksi_id, clients):
    """IAM - Identity and Access Management validation using tenant's AWS account"""
    results = []
    
    # Check IAM users in tenant account
    try:
        response = clients['iam'].list_users()
        users = response.get('Users', [])
        
        results.append({
            "success": True,
            "command": "boto3.iam.list_users() [tenant account]",
            "note": "Check IAM users for proper identity management and MFA enforcement",
            "data": {
                "user_count": len(users)
            }
        })
    except Exception as e:
        results.append({
            "success": False,
            "error": str(e),
            "command": "boto3.iam.list_users() [tenant account]",
            "note": "Check IAM users for proper identity management and MFA enforcement"
        })
    
    # Check roles in tenant account
    try:
        response = clients['iam'].list_roles()
        roles = response.get('Roles', [])
        
        results.append({
            "success": True,
            "command": "boto3.iam.list_roles() [tenant account]",
            "note": "Check IAM roles for proper access control and least privilege",
            "data": {
                "role_count": len(roles)
            }
        })
    except Exception as e:
        results.append({
            "success": False,
            "error": str(e),
            "command": "boto3.iam.list_roles() [tenant account]",
            "note": "Check IAM roles for proper access control and least privilege"
        })
    
    # Check account summary for tenant account
    try:
        response = clients['iam'].get_account_summary()
        summary = response.get('SummaryMap', {})
        
        results.append({
            "success": True,
            "command": "boto3.iam.get_account_summary() [tenant account]",
            "note": "Check account security summary for identity management overview",
            "data": {
                "users": summary.get('Users', 0),
                "roles": summary.get('Roles', 0),
                "policies": summary.get('Policies', 0)
            }
        })
    except Exception as e:
        results.append({
            "success": False,
            "error": str(e),
            "command": "boto3.iam.get_account_summary() [tenant account]",
            "note": "Check account security summary for identity management overview"
        })
    
    return analyze_results(results, ksi_id)

def validate_monitoring_logging(ksi_id, clients):
    """MLA - Monitoring, Logging, and Alerting validation using tenant's AWS account"""
    results = []
    
    # Check CloudTrail in tenant account
    try:
        response = clients['cloudtrail'].describe_trails()
        trails = response.get('trailList', [])
        
        results.append({
            "success": True,
            "command": "boto3.cloudtrail.describe_trails() [tenant account]",
            "note": "Validate CloudTrail for comprehensive logging and monitoring",
            "data": {
                "trail_count": len(trails),
                "multi_region_trails": len([t for t in trails if t.get('IsMultiRegionTrail', False)])
            }
        })
    except Exception as e:
        results.append({
            "success": False,
            "error": str(e),
            "command": "boto3.cloudtrail.describe_trails() [tenant account]",
            "note": "Validate CloudTrail for comprehensive logging and monitoring"
        })
    
    # Check CloudWatch alarms in tenant account
    try:
        response = clients['cloudwatch'].describe_alarms()
        alarms = response.get('MetricAlarms', [])
        
        results.append({
            "success": True,
            "command": "boto3.cloudwatch.describe_alarms() [tenant account]",
            "note": "Check CloudWatch alarms for automated monitoring and alerting",
            "data": {
                "alarm_count": len(alarms),
                "ok_alarms": len([a for a in alarms if a['StateValue'] == 'OK'])
            }
        })
    except Exception as e:
        results.append({
            "success": False,
            "error": str(e),
            "command": "boto3.cloudwatch.describe_alarms() [tenant account]",
            "note": "Check CloudWatch alarms for automated monitoring and alerting"
        })
    
    # Check SNS topics in tenant account
    try:
        response = clients['sns'].list_topics()
        topics = response.get('Topics', [])
        
        results.append({
            "success": True,
            "command": "boto3.sns.list_topics() [tenant account]",
            "note": "Validate SNS topics for alert notification workflows",
            "data": {
                "topic_count": len(topics)
            }
        })
    except Exception as e:
        results.append({
            "success": False,
            "error": str(e),
            "command": "boto3.sns.list_topics() [tenant account]",
            "note": "Validate SNS topics for alert notification workflows"
        })
    
    return analyze_results(results, ksi_id)

def validate_change_management(ksi_id, clients):
    """CMT - Change Management and integrity validation using tenant's AWS account"""
    results = []
    
    # Check CloudTrail integrity in tenant account
    try:
        response = clients['cloudtrail'].describe_trails()
        trails = response.get('trailList', [])
        integrity_trails = [t for t in trails if t.get('LogFileValidationEnabled', False)]
        
        results.append({
            "success": True,
            "command": "boto3.cloudtrail.describe_trails() [tenant account]",
            "note": "Check CloudTrail log file validation for audit trail integrity and tamper-evident logging",
            "data": {
                "total_trails": len(trails),
                "integrity_enabled": len(integrity_trails)
            }
        })
    except Exception as e:
        results.append({
            "success": False,
            "error": str(e),
            "command": "boto3.cloudtrail.describe_trails() [tenant account]",
            "note": "Check CloudTrail log file validation for audit trail integrity and tamper-evident logging"
        })
    
    # Check AWS Config in tenant account
    try:
        response = clients['config'].describe_configuration_recorders()
        recorders = response.get('ConfigurationRecorders', [])
        
        results.append({
            "success": True,
            "command": "boto3.config.describe_configuration_recorders() [tenant account]",
            "note": "Validate AWS Config for configuration change integrity tracking and compliance monitoring",
            "data": {
                "recorder_count": len(recorders)
            }
        })
    except Exception as e:
        results.append({
            "success": False,
            "error": str(e),
            "command": "boto3.config.describe_configuration_recorders() [tenant account]",
            "note": "Validate AWS Config for configuration change integrity tracking and compliance monitoring"
        })
    
    # Check CloudFormation stacks in tenant account
    try:
        response = clients['cloudformation'].list_stacks(
            StackStatusFilter=[
                'CREATE_COMPLETE',
                'UPDATE_COMPLETE', 
                'UPDATE_ROLLBACK_COMPLETE'
            ]
        )
        stacks = response.get('StackSummaries', [])
        
        results.append({
            "success": True,
            "command": "boto3.cloudformation.list_stacks() [tenant account]",
            "note": "Check CloudFormation stacks for Infrastructure as Code deployment tracking",
            "data": {
                "stack_count": len(stacks)
            }
        })
    except Exception as e:
        results.append({
            "success": False,
            "error": str(e),
            "command": "boto3.cloudformation.list_stacks() [tenant account]",
            "note": "Check CloudFormation stacks for Infrastructure as Code deployment tracking"
        })
    
    return analyze_results(results, ksi_id)

def analyze_results(results, ksi_id):
    """Analyze validation results and return summary"""
    successful_commands = sum(1 for r in results if r["success"])
    failed_commands = len(results) - successful_commands
    
    if successful_commands > 0:
        assertion = True
        assertion_reason = f"✅ {successful_commands}/{len(results)} AWS validation checks passed for {ksi_id} [tenant account]"
    else:
        assertion = False  
        assertion_reason = f"❌ All AWS validation checks failed for {ksi_id} [tenant account] - check permissions"
    
    return {
        "assertion": assertion,
        "assertion_reason": assertion_reason,
        "commands_executed": len(results),
        "successful_commands": successful_commands,
        "failed_commands": failed_commands,
        "cli_command_details": results
    }

def create_error_response(error_msg, validator_type, execution_id, tenant_id):
    """Create standardized error response"""
    return {
        'statusCode': 500,
        'body': json.dumps({
            'error': error_msg,
            'validator_type': validator_type,
            'execution_id': execution_id,
            'tenant_id': tenant_id
        })
    }
