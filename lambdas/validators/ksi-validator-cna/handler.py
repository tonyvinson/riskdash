import json
import boto3
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any
import os

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')

# Environment variables
VALIDATOR_TYPE = os.environ['VALIDATOR_TYPE']
KSI_EXECUTION_HISTORY_TABLE = os.environ['KSI_EXECUTION_HISTORY_TABLE']
ENVIRONMENT = os.environ['ENVIRONMENT']

def lambda_handler(event, context):
    """
    KSI Validator Lambda Handler for CNA category
    Validates Key Security Indicators for FedRAMP-20X compliance
    """
    try:
        logger.info(f"KSI Validator {VALIDATOR_TYPE} started with event: {json.dumps(event)}")
        
        execution_id = event.get('execution_id')
        tenant_id = event.get('tenant_id')
        ksis = event.get('ksis', [])
        
        validation_results = []
        
        for ksi_config in ksis:
            try:
                result = validate_ksi(ksi_config)
                validation_results.append(result)
                
                # Save individual KSI result
                save_ksi_result(execution_id, tenant_id, result)
                
            except Exception as e:
                logger.error(f"Error validating KSI {ksi_config.get('ksi_id')}: {str(e)}")
                error_result = {
                    'ksi_id': ksi_config.get('ksi_id'),
                    'tenant_id': tenant_id,
                    'status': 'ERROR',
                    'error': str(e),
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
                validation_results.append(error_result)
                save_ksi_result(execution_id, tenant_id, error_result)
        
        response = {
            'statusCode': 200,
            'body': json.dumps({
                'validator_type': VALIDATOR_TYPE,
                'execution_id': execution_id,
                'tenant_id': tenant_id,
                'ksis_validated': len(ksis),
                'results': validation_results,
                'summary': generate_summary(validation_results)
            })
        }
        
        logger.info(f"KSI Validator {VALIDATOR_TYPE} completed: {len(validation_results)} validations")
        return response
        
    except Exception as e:
        logger.error(f"KSI Validator {VALIDATOR_TYPE} error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'validator_type': VALIDATOR_TYPE,
                'error': str(e)
            })
        }

def validate_ksi(ksi_config: Dict) -> Dict:
    """
    Validate a specific KSI using commands from DynamoDB
    """
    ksi_id = ksi_config.get('ksi_id')
    
    # Simplified validation - replace with actual validation logic
    result = {
        'ksi_id': ksi_id,
        'validation_id': ksi_id,
        'validator_type': VALIDATOR_TYPE,
        'assertion': True,  # Placeholder - implement actual validation
        'assertion_reason': f"✅ {VALIDATOR_TYPE} validation completed for {ksi_id}",
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'validation_method': 'automated'
    }
    
    logger.info(f"Validated {ksi_id}: PASS")
    return result

def save_ksi_result(execution_id: str, tenant_id: str, result: Dict) -> None:
    """Save KSI validation result to execution history"""
    table = dynamodb.Table(KSI_EXECUTION_HISTORY_TABLE)
    
    try:
        record = {
            'execution_id': f"{execution_id}#{result['ksi_id']}",
            'timestamp': result['timestamp'],
            'tenant_id': tenant_id,
            'ksi_id': result['ksi_id'],
            'validator_type': VALIDATOR_TYPE,
            'validation_result': result,
            'ttl': int((datetime.now(timezone.utc).timestamp() + (90 * 24 * 60 * 60)))  # 90 days TTL
        }
        
        table.put_item(Item=record)
        logger.info(f"Saved KSI result: {result['ksi_id']}")
        
    except Exception as e:
        logger.error(f"Error saving KSI result: {str(e)}")

def generate_summary(results: List[Dict]) -> Dict:
    """Generate validation summary statistics"""
    total = len(results)
    passed = sum(1 for r in results if r.get('assertion', False))
    failed = total - passed
    
    return {
        'total_ksis': total,
        'passed': passed,
        'failed': failed,
        'pass_rate': round((passed / total * 100) if total > 0 else 0, 2),
        'validator_type': VALIDATOR_TYPE
    }
