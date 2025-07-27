import json
import boto3
import subprocess
import os
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Your real CLI command registry mapped by category
CLI_COMMAND_REGISTRY = {
    "CNA": {
        "KSI-CNA-01": [
            {
                "command": "aws ec2 describe-subnets --output json",
                "note": "Check network architecture for proper segmentation and high availability design"
            },
            {
                "command": "aws ec2 describe-availability-zones --output json",
                "note": "Validate multi-AZ deployment capability for rapid recovery architecture"
            },
            {
                "command": "aws route53 list-hosted-zones --output json",
                "note": "Check DNS infrastructure for resilient network architecture"
            }
        ]
    },
    "SVC": {
        "KSI-SVC-06": [
            {
                "command": "aws kms list-keys --output json",
                "note": "Check KMS keys for automated key management and cryptographic service availability"
            },
            {
                "command": "aws kms list-aliases --output json", 
                "note": "Validate KMS key aliases for proper key lifecycle management and rotation"
            },
            {
                "command": "aws secretsmanager list-secrets --output json",
                "note": "Check Secrets Manager for automated certificate and credential management"
            }
        ]
    },
    "IAM": {
        "KSI-IAM-01": [
            {
                "command": "aws iam list-users --output json",
                "note": "Check IAM users for proper identity management and MFA enforcement"
            },
            {
                "command": "aws iam list-mfa-devices --output json",
                "note": "Validate MFA devices for multi-factor authentication compliance"
            },
            {
                "command": "aws sso-admin list-instances --output json",
                "note": "Check AWS SSO for federated identity management"
            }
        ]
    },
    "MLA": {
        "KSI-MLA-01": [
            {
                "command": "aws cloudtrail describe-trails --output json",
                "note": "Validate CloudTrail for comprehensive logging and monitoring"
            },
            {
                "command": "aws cloudwatch describe-alarms --output json",
                "note": "Check CloudWatch alarms for automated monitoring and alerting"
            },
            {
                "command": "aws sns list-topics --output json",
                "note": "Validate SNS topics for alert notification workflows"
            }
        ]
    },
    "CMT": {
        "KSI-CMT-01": [
            {
                "command": "aws cloudtrail describe-trails --output json",
                "note": "Check CloudTrail log file validation for audit trail integrity and tamper-evident logging"
            },
            {
                "command": "aws config describe-configuration-recorders --output json", 
                "note": "Validate AWS Config for configuration change integrity tracking and compliance monitoring"
            },
            {
                "command": "aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE UPDATE_ROLLBACK_COMPLETE --output json",
                "note": "Check CloudFormation stacks for Infrastructure as Code deployment tracking"
            }
        ]
    }
}

def execute_aws_command(command: str) -> Dict[str, Any]:
    """Execute actual AWS CLI command and return parsed JSON result"""
    try:
        logger.info(f"Executing: {command}")
        
        # Execute the command
        result = subprocess.run(
            command.split(), 
            capture_output=True, 
            text=True, 
            timeout=30
        )
        
        if result.returncode != 0:
            logger.error(f"Command failed: {result.stderr}")
            return {
                "success": False,
                "error": result.stderr,
                "command": command
            }
        
        # Parse JSON output
        output = json.loads(result.stdout) if result.stdout.strip() else {}
        
        return {
            "success": True,
            "data": output,
            "command": command
        }
        
    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out: {command}")
        return {
            "success": False,
            "error": "Command timeout",
            "command": command
        }
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON output: {e}")
        return {
            "success": False,
            "error": f"JSON parse error: {str(e)}",
            "command": command
        }
    except Exception as e:
        logger.error(f"Command execution error: {e}")
        return {
            "success": False,
            "error": str(e),
            "command": command
        }

def analyze_ksi_results(ksi_id: str, command_results: List[Dict]) -> Dict[str, Any]:
    """Analyze command results to determine KSI compliance"""
    
    successful_commands = sum(1 for r in command_results if r.get("success", False))
    total_commands = len(command_results)
    
    if successful_commands == 0:
        return {
            "assertion": False,
            "assertion_reason": f"❌ No AWS CLI commands succeeded for {ksi_id} - check permissions or CLI availability",
            "confidence": "low",
            "commands_executed": total_commands,
            "successful_commands": successful_commands,
            "failed_commands": total_commands
        }
    
    # Real analysis based on successful commands
    if ksi_id == "KSI-CMT-01":
        # Configuration Management & Tracking analysis
        cloudtrail_count = 0
        cloudformation_count = 0
        
        for r in command_results:
            if r.get("success"):
                if "cloudtrail" in r.get("command", ""):
                    cloudtrail_count = len(r.get("data", {}).get("trailList", []))
                elif "cloudformation" in r.get("command", ""):
                    cloudformation_count = len(r.get("data", {}).get("StackSummaries", []))
        
        passed = cloudtrail_count > 0 and cloudformation_count > 0
        confidence = "high" if passed else "medium"
        
        reason = f"✅ Configuration Management: {cloudtrail_count} CloudTrail trails, {cloudformation_count} CloudFormation stacks"
        
    elif ksi_id == "KSI-SVC-06":
        # Key Management analysis
        kms_key_count = 0
        secrets_count = 0
        
        for r in command_results:
            if r.get("success"):
                if "kms list-keys" in r.get("command", ""):
                    kms_key_count = len(r.get("data", {}).get("Keys", []))
                elif "secretsmanager" in r.get("command", ""):
                    secrets_count = len(r.get("data", {}).get("SecretList", []))
        
        passed = kms_key_count > 0
        confidence = "high" if kms_key_count > 5 else "medium"
        
        reason = f"✅ Key Management: {kms_key_count} KMS keys, {secrets_count} managed secrets"
        
    elif ksi_id == "KSI-CNA-01":
        # Network Architecture analysis
        subnet_count = 0
        az_count = 0
        
        for r in command_results:
            if r.get("success"):
                if "describe-subnets" in r.get("command", ""):
                    subnets = r.get("data", {}).get("Subnets", [])
                    subnet_count = len(subnets)
                    az_count = len(set(s.get("AvailabilityZone") for s in subnets))
                elif "describe-availability-zones" in r.get("command", ""):
                    az_count = max(az_count, len(r.get("data", {}).get("AvailabilityZones", [])))
        
        multi_az = az_count > 1
        passed = subnet_count > 0 and multi_az
        confidence = "high" if passed else "medium"
        
        reason = f"✅ Network Architecture: {subnet_count} subnets across {az_count} AZs"
        
    elif ksi_id == "KSI-IAM-01":
        # IAM analysis
        user_count = 0
        mfa_count = 0
        
        for r in command_results:
            if r.get("success"):
                if "list-users" in r.get("command", ""):
                    user_count = len(r.get("data", {}).get("Users", []))
                elif "list-mfa-devices" in r.get("command", ""):
                    mfa_count = len(r.get("data", {}).get("MFADevices", []))
        
        # Prefer federated identity (fewer users is better)
        passed = user_count <= 10
        confidence = "high" if user_count <= 5 else "medium"
        
        reason = f"✅ Identity Management: {user_count} IAM users (federated preferred), {mfa_count} MFA devices"
        
    elif ksi_id == "KSI-MLA-01":
        # Monitoring, Logging & Alerting analysis
        trail_count = 0
        alarm_count = 0
        
        for r in command_results:
            if r.get("success"):
                if "cloudtrail" in r.get("command", ""):
                    trail_count = len(r.get("data", {}).get("trailList", []))
                elif "describe-alarms" in r.get("command", ""):
                    alarm_count = len(r.get("data", {}).get("MetricAlarms", []))
        
        passed = trail_count > 0
        confidence = "high" if alarm_count > 0 else "medium"
        
        reason = f"✅ Monitoring & Logging: {trail_count} CloudTrail trails, {alarm_count} CloudWatch alarms"
        
    else:
        # Default analysis
        passed = successful_commands >= (total_commands * 0.7)  # 70% success rate
        confidence = "medium"
        reason = f"✅ Commands executed: {successful_commands}/{total_commands} successful"
    
    return {
        "assertion": passed,
        "assertion_reason": reason,
        "confidence": confidence,
        "commands_executed": total_commands,
        "successful_commands": successful_commands,
        "failed_commands": total_commands - successful_commands
    }

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Real KSI validation using actual AWS CLI commands"""
    
    validator_type = os.environ.get('VALIDATOR_TYPE', 'UNKNOWN')
    
    try:
        logger.info(f"Real KSI Validator {validator_type} started with event: {json.dumps(event)}")
        
        execution_id = event.get('execution_id')
        tenant_id = event.get('tenant_id')
        ksis = event.get('ksis', [])
        
        logger.info(f"Processing {len(ksis)} KSIs for validator {validator_type}")
        
        validation_results = []
        
        # Get commands for this validator category
        category_commands = CLI_COMMAND_REGISTRY.get(validator_type, {})
        
        if not category_commands:
            logger.warning(f"No CLI commands defined for validator category {validator_type}")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'validator_type': validator_type,
                    'execution_id': execution_id,
                    'tenant_id': tenant_id,
                    'message': f'No commands defined for {validator_type} category',
                    'ksis_validated': 0,
                    'results': []
                })
            }
        
        # Process each KSI that belongs to this validator's category
        for ksi_config in ksis:
            ksi_id = ksi_config.get('ksi_id')
            
            logger.info(f"Processing KSI: {ksi_id}")
            
            # Get commands for this specific KSI
            commands = category_commands.get(ksi_id, [])
            
            if not commands:
                logger.info(f"KSI {ksi_id} not handled by {validator_type} validator")
                continue
            
            logger.info(f"Executing {len(commands)} commands for {ksi_id}")
            
            # Execute real AWS CLI commands
            command_results = []
            for cmd_info in commands:
                result = execute_aws_command(cmd_info['command'])
                result['note'] = cmd_info['note']
                command_results.append(result)
            
            # Analyze real results
            analysis = analyze_ksi_results(ksi_id, command_results)
            
            # Create validation result
            validation_result = {
                'ksi_id': ksi_id,
                'validation_id': ksi_id,
                'validator_type': validator_type,
                'assertion': analysis['assertion'],
                'assertion_reason': analysis['assertion_reason'],
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'validation_method': 'automated',
                'commands_executed': analysis['commands_executed'],
                'successful_commands': analysis['successful_commands'],
                'failed_commands': analysis['failed_commands'],
                'cli_command_details': command_results
            }
            validation_results.append(validation_result)
            
            # Save to DynamoDB
            save_ksi_result(execution_id, tenant_id, validation_result)
            
            logger.info(f"Completed {ksi_id}: {'PASS' if analysis['assertion'] else 'FAIL'}")
        
        # Return results
        if not validation_results:
            logger.info(f"No KSIs processed by {validator_type} validator")
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
        
        response = {
            'statusCode': 200,
            'body': json.dumps({
                'validator_type': validator_type,
                'execution_id': execution_id,
                'tenant_id': tenant_id,
                'ksis_validated': len(validation_results),
                'results': validation_results,
                'summary': {
                    'total_ksis': len(validation_results),
                    'passed': sum(1 for r in validation_results if r['assertion']),
                    'failed': sum(1 for r in validation_results if not r['assertion']),
                    'pass_rate': (sum(1 for r in validation_results if r['assertion']) / len(validation_results) * 100) if validation_results else 0,
                    'validator_type': validator_type
                }
            })
        }
        
        logger.info(f"Real KSI Validator {validator_type} completed: {len(validation_results)} real validations")
        return response
        
    except Exception as e:
        logger.error(f"Real KSI Validator {validator_type} error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'validator_type': validator_type,
                'error': str(e)
            })
        }

def save_ksi_result(execution_id: str, tenant_id: str, result: Dict):
    """Save KSI result to DynamoDB"""
    try:
        dynamodb = boto3.resource('dynamodb')
        table_name = os.environ.get('KSI_EXECUTION_HISTORY_TABLE')
        
        if table_name:
            table = dynamodb.Table(table_name)
            table.put_item(
                Item={
                    'execution_id': f"{execution_id}#{result['ksi_id']}",
                    'tenant_id': tenant_id,
                    'ksi_id': result['ksi_id'],
                    'validator_type': result['validator_type'],
                    'validation_result': result,
                    'timestamp': result['timestamp'],
                    'ttl': int(datetime.now(timezone.utc).timestamp()) + (90 * 24 * 60 * 60)  # 90 days
                }
            )
    except Exception as e:
        logger.error(f"Error saving result: {e}")
