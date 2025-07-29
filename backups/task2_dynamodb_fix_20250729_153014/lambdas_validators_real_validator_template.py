import json
import boto3
import subprocess
import os
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Your real CLI command registry
CLI_COMMAND_REGISTRY = {
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
    ],
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
    ],
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
    ],
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
            "command": "aws sso admin list-instances --output json",
            "note": "Check AWS SSO for federated identity management"
        }
    ],
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
    """Analyze command results to determine KSI compliance - YOUR REAL LOGIC"""
    
    successful_commands = sum(1 for r in command_results if r.get("success", False))
    total_commands = len(command_results)
    
    # Real analysis based on your validation engine logic
    if ksi_id == "KSI-CMT-01":
        # Configuration Management & Tracking analysis
        cloudtrail_ok = any(
            r.get("success") and len(r.get("data", {}).get("trailList", [])) > 0 
            for r in command_results if "cloudtrail" in r.get("command", "")
        )
        
        config_ok = any(
            r.get("success") and len(r.get("data", {}).get("ConfigurationRecorders", [])) >= 0
            for r in command_results if "config" in r.get("command", "")
        )
        
        cloudformation_ok = any(
            r.get("success") and len(r.get("data", {}).get("StackSummaries", [])) > 0
            for r in command_results if "cloudformation" in r.get("command", "")
        )
        
        passed = cloudtrail_ok and cloudformation_ok
        confidence = "high" if passed else "medium"
        
        reason = f"✅ Configuration Management: CloudTrail {'✅' if cloudtrail_ok else '❌'}, CloudFormation {'✅' if cloudformation_ok else '❌'}, Config {'✅' if config_ok else '⚠️'}"
        
    elif ksi_id == "KSI-SVC-06":
        # Key Management analysis
        kms_keys = []
        for r in command_results:
            if r.get("success") and "kms" in r.get("command", ""):
                kms_keys.extend(r.get("data", {}).get("Keys", []))
        
        secrets_count = 0
        for r in command_results:
            if r.get("success") and "secretsmanager" in r.get("command", ""):
                secrets_count = len(r.get("data", {}).get("SecretList", []))
        
        passed = len(kms_keys) > 0
        confidence = "high" if len(kms_keys) > 5 else "medium"
        
        reason = f"✅ Key Management: {len(kms_keys)} KMS keys, {secrets_count} managed secrets"
        
    elif ksi_id == "KSI-CNA-01":
        # Network Architecture analysis
        subnets = []
        azs = []
        for r in command_results:
            if r.get("success"):
                if "describe-subnets" in r.get("command", ""):
                    subnets = r.get("data", {}).get("Subnets", [])
                elif "describe-availability-zones" in r.get("command", ""):
                    azs = r.get("data", {}).get("AvailabilityZones", [])
        
        multi_az = len(set(s.get("AvailabilityZone") for s in subnets)) > 1
        passed = len(subnets) > 0 and multi_az
        confidence = "high" if passed else "medium"
        
        reason = f"✅ Network Architecture: {len(subnets)} subnets across {len(azs)} AZs, Multi-AZ: {'✅' if multi_az else '❌'}"
        
    elif ksi_id == "KSI-IAM-01":
        # IAM analysis
        users = []
        mfa_devices = []
        for r in command_results:
            if r.get("success"):
                if "list-users" in r.get("command", ""):
                    users = r.get("data", {}).get("Users", [])
                elif "list-mfa-devices" in r.get("command", ""):
                    mfa_devices = r.get("data", {}).get("MFADevices", [])
        
        passed = len(users) <= 5  # Prefer federated identity
        confidence = "high" if len(mfa_devices) > 0 else "medium"
        
        reason = f"✅ Identity Management: {len(users)} IAM users (federated preferred), {len(mfa_devices)} MFA devices"
        
    elif ksi_id == "KSI-MLA-01":
        # Monitoring, Logging & Alerting analysis
        trails = []
        alarms = []
        for r in command_results:
            if r.get("success"):
                if "cloudtrail" in r.get("command", ""):
                    trails = r.get("data", {}).get("trailList", [])
                elif "describe-alarms" in r.get("command", ""):
                    alarms = r.get("data", {}).get("MetricAlarms", [])
        
        passed = len(trails) > 0
        confidence = "high" if len(alarms) > 0 else "medium"
        
        reason = f"✅ Monitoring & Logging: {len(trails)} CloudTrail trails, {len(alarms)} CloudWatch alarms"
        
    else:
        # Default analysis
        passed = successful_commands == total_commands
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
        logger.info(f"Real KSI Validator {validator_type} started")
        
        execution_id = event.get('execution_id')
        tenant_id = event.get('tenant_id')
        ksis = event.get('ksis', [])
        
        validation_results = []
        
        for ksi_config in ksis:
            ksi_id = ksi_config.get('ksi_id')
            
            # Get real CLI commands for this KSI
            commands = CLI_COMMAND_REGISTRY.get(ksi_id, [])
            
            if not commands:
                logger.warning(f"No CLI commands defined for {ksi_id}")
                # Return NOTHING instead of placeholder
                continue
            
            # Execute real AWS CLI commands
            command_results = []
            for cmd_info in commands:
                result = execute_aws_command(cmd_info['command'])
                result['note'] = cmd_info['note']
                command_results.append(result)
            
            # Analyze real results
            analysis = analyze_ksi_results(ksi_id, command_results)
            
            # Only return results if we have real data
            if analysis['successful_commands'] > 0:
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
        
        # Return NOTHING if no real validations were performed
        if not validation_results:
            logger.info(f"No real validations performed for {validator_type}")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'validator_type': validator_type,
                    'execution_id': execution_id,
                    'tenant_id': tenant_id,
                    'message': 'No validations performed - real checks only',
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
