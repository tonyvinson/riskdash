import json
import boto3
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any
import os

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')

# Environment variables
KSI_DEFINITIONS_TABLE = os.environ['KSI_DEFINITIONS_TABLE']
TENANT_KSI_CONFIGURATIONS_TABLE = os.environ['TENANT_KSI_CONFIGURATIONS_TABLE']
KSI_EXECUTION_HISTORY_TABLE = os.environ['KSI_EXECUTION_HISTORY_TABLE']
VALIDATOR_FUNCTION_PREFIX = os.environ['VALIDATOR_FUNCTION_PREFIX']
ENVIRONMENT = os.environ['ENVIRONMENT']

def lambda_handler(event, context):
    """
    KSI Orchestrator Lambda Handler
    Coordinates validation execution across all KSI validators
    """
    try:
        logger.info(f"KSI Orchestrator started with event: {json.dumps(event)}")
        
        # Extract tenant ID from event or default to all tenants
        tenant_id = event.get('tenant_id', 'all')
        execution_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Start execution record
        execution_record = {
            'execution_id': execution_id,
            'timestamp': timestamp,
            'tenant_id': tenant_id,
            'status': 'STARTED',
            'trigger_source': event.get('source', 'manual'),
            'validators_requested': [],
            'validators_completed': [],
            'total_ksis_validated': 0,
            'ttl': int((datetime.now(timezone.utc).timestamp() + (90 * 24 * 60 * 60)))  # 90 days TTL
        }
        
        # Get tenant configurations
        if tenant_id == 'all':
            tenant_configurations = get_all_tenant_configurations()
        else:
            tenant_configurations = get_tenant_configurations(tenant_id)
        
        logger.info(f"Found {len(tenant_configurations)} tenant configurations")
        
        # Group KSIs by validator type
        validator_groups = group_ksis_by_validator(tenant_configurations)
        execution_record['validators_requested'] = list(validator_groups.keys())
        
        # Save initial execution record
        save_execution_record(execution_record)
        
        # Invoke validator Lambdas
        validation_results = []
        for validator_type, ksi_list in validator_groups.items():
            try:
                result = invoke_validator(validator_type, {
                    'execution_id': execution_id,
                    'tenant_id': tenant_id,
                    'ksis': ksi_list,
                    'timestamp': timestamp
                })
                validation_results.append(result)
                execution_record['validators_completed'].append(validator_type)
                
            except Exception as e:
                logger.error(f"Failed to invoke validator {validator_type}: {str(e)}")
                validation_results.append({
                    'validator': validator_type,
                    'status': 'ERROR',
                    'error': str(e)
                })
        
        # Update execution record with results
        execution_record['status'] = 'COMPLETED'
        execution_record['validation_results'] = validation_results
        execution_record['total_ksis_validated'] = sum(len(ksis) for ksis in validator_groups.values())
        execution_record['completed_at'] = datetime.now(timezone.utc).isoformat()
        
        save_execution_record(execution_record)
        
        response = {
            'statusCode': 200,
            'body': json.dumps({
                'execution_id': execution_id,
                'tenant_id': tenant_id,
                'status': execution_record['status'],
                'validators_invoked': list(validator_groups.keys()),
                'total_ksis': execution_record['total_ksis_validated'],
                'results': validation_results
            })
        }
        
        logger.info(f"KSI Orchestrator completed: {response}")
        return response
        
    except Exception as e:
        logger.error(f"KSI Orchestrator error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'execution_id': execution_id if 'execution_id' in locals() else None
            })
        }

def get_all_tenant_configurations() -> List[Dict]:
    """Retrieve all tenant KSI configurations"""
    table = dynamodb.Table(TENANT_KSI_CONFIGURATIONS_TABLE)
    
    try:
        response = table.scan()
        return response.get('Items', [])
    except Exception as e:
        logger.error(f"Error scanning tenant configurations: {str(e)}")
        return []

def get_tenant_configurations(tenant_id: str) -> List[Dict]:
    """Retrieve KSI configurations for a specific tenant - FIXED VERSION"""
    table = dynamodb.Table(TENANT_KSI_CONFIGURATIONS_TABLE)
    
    try:
        response = table.query(
            KeyConditionExpression='tenant_id = :tid',
            ExpressionAttributeValues={':tid': tenant_id}
        )
        return response.get('Items', [])
    except Exception as e:
        logger.error(f"Error querying tenant configurations for {tenant_id}: {str(e)}")
        return []

def group_ksis_by_validator(configurations: List[Dict]) -> Dict[str, List[Dict]]:
    """Group KSIs by their validator type based on KSI ID prefix"""
    validator_groups = {
        'cna': [],  # Configuration & Network Architecture
        'svc': [],  # Service Configuration
        'iam': [],  # Identity & Access Management
        'mla': [],  # Monitoring, Logging & Alerting
        'cmt': []   # Configuration Management & Tracking
    }
    
    for config in configurations:
        ksi_id = config.get('ksi_id', '')
        
        # Parse KSI ID to determine validator (e.g., KSI-CNA-01 -> cna)
        if ksi_id.startswith('KSI-'):
            parts = ksi_id.split('-')
            if len(parts) >= 2:
                validator_type = parts[1].lower()
                if validator_type in validator_groups:
                    validator_groups[validator_type].append(config)
                else:
                    logger.warning(f"Unknown validator type for KSI: {ksi_id}")
    
    # Remove empty groups
    return {k: v for k, v in validator_groups.items() if v}

def invoke_validator(validator_type: str, payload: Dict) -> Dict:
    """Invoke a specific KSI validator Lambda function"""
    function_name = f"{VALIDATOR_FUNCTION_PREFIX}-{validator_type}-{ENVIRONMENT}"
    
    try:
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        result_payload = json.loads(response['Payload'].read().decode('utf-8'))
        
        return {
            'validator': validator_type,
            'status': 'SUCCESS',
            'function_name': function_name,
            'result': result_payload
        }
        
    except Exception as e:
        logger.error(f"Error invoking validator {validator_type}: {str(e)}")
        return {
            'validator': validator_type,
            'status': 'ERROR',
            'function_name': function_name,
            'error': str(e)
        }

def save_execution_record(record: Dict) -> None:
    """Save execution record to DynamoDB"""
    table = dynamodb.Table(KSI_EXECUTION_HISTORY_TABLE)
    
    try:
        table.put_item(Item=record)
        logger.info(f"Saved execution record: {record['execution_id']}")
    except Exception as e:
        logger.error(f"Error saving execution record: {str(e)}")
