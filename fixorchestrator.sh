#!/bin/bash

# 🔧 FINAL FIX: Update orchestrator to return proper API Gateway response format

echo "🔧 FINAL FIX: API Gateway Response Format"
echo "========================================"

FUNCTION_NAME="riskuity-ksi-validator-orchestrator-production"
REGION="us-gov-west-1"

# Create the final fixed orchestrator
mkdir -p temp_api_fix
cd temp_api_fix

cat > orchestrator_handler.py << 'EOF'
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
    KSI Orchestrator Lambda Handler - FINAL VERSION
    Returns proper API Gateway response format
    """
    try:
        logger.info(f"🚀 KSI Orchestrator started with event: {json.dumps(event)}")
        
        # Extract tenant ID from API Gateway event
        tenant_id = extract_tenant_id(event)
        
        if not tenant_id or tenant_id == 'all':
            return create_api_response(400, {
                'success': False,
                'error': f'Invalid tenant_id: {tenant_id}. Must specify a specific tenant.'
            })
        
        execution_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        
        logger.info(f"✅ Processing validation for tenant: {tenant_id}")
        
        # Get tenant configurations  
        tenant_configurations = get_tenant_configurations(tenant_id)
        logger.info(f"📊 Found {len(tenant_configurations)} KSI configurations for tenant: {tenant_id}")
        
        # Group KSIs by validator type
        validator_groups = group_ksis_by_validator(tenant_configurations)
        
        # Results collection
        validation_results = []
        validators_invoked = []
        total_ksis_validated = 0
        
        # Execute validators
        for validator_type, ksis in validator_groups.items():
            logger.info(f"🔍 Invoking {validator_type.upper()} validator for {len(ksis)} KSIs")
            
            function_name = f"{VALIDATOR_FUNCTION_PREFIX}-{validator_type}-{ENVIRONMENT}"
            validators_invoked.append(validator_type)
            
            validator_payload = {
                'tenant_id': tenant_id,
                'execution_id': execution_id,
                'ksis': ksis,
                'validator_type': validator_type.upper()
            }
            
            try:
                response = lambda_client.invoke(
                    FunctionName=function_name,
                    InvocationType='RequestResponse',
                    Payload=json.dumps(validator_payload)
                )
                
                response_payload = json.loads(response['Payload'].read())
                
                validation_results.append({
                    'validator': validator_type,
                    'status': 'SUCCESS' if response['StatusCode'] == 200 else 'ERROR',
                    'function_name': function_name,
                    'result': response_payload
                })
                
                if response['StatusCode'] == 200:
                    total_ksis_validated += len(ksis)
                
                logger.info(f"✅ {validator_type.upper()} validator completed")
                
            except Exception as e:
                logger.error(f"❌ Error invoking {validator_type} validator: {str(e)}")
                validation_results.append({
                    'validator': validator_type,
                    'status': 'ERROR',
                    'function_name': function_name,
                    'result': {'error': str(e)}
                })
        
        # Save execution record
        execution_record = {
            'execution_id': execution_id,
            'timestamp': timestamp,
            'tenant_id': tenant_id,
            'status': 'COMPLETED',
            'trigger_source': event.get('trigger_source', 'manual'),
            'validators_requested': validators_invoked,
            'validators_completed': validators_invoked,
            'total_ksis_validated': total_ksis_validated,
            'ttl': int((datetime.now(timezone.utc).timestamp() + (90 * 24 * 60 * 60)))
        }
        
        try:
            table = dynamodb.Table(KSI_EXECUTION_HISTORY_TABLE)
            table.put_item(Item=execution_record)
            logger.info(f"📝 Execution record saved: {execution_id}")
        except Exception as e:
            logger.error(f"❌ Failed to save execution record: {str(e)}")
        
        # ✅ FIXED: Return proper API Gateway response format
        response_data = {
            'success': True,
            'execution_id': execution_id,
            'tenant_id': tenant_id,
            'status': 'COMPLETED',
            'validators_invoked': validators_invoked,
            'total_ksis': total_ksis_validated,
            'timestamp': timestamp,
            'message': f'Validation completed successfully for {len(validators_invoked)} validators'
        }
        
        logger.info(f"🎉 KSI Orchestrator completed successfully")
        return create_api_response(200, response_data)
        
    except Exception as e:
        logger.error(f"💥 KSI Orchestrator error: {str(e)}")
        return create_api_response(500, {
            'success': False,
            'error': str(e),
            'execution_id': execution_id if 'execution_id' in locals() else None
        })

def create_api_response(status_code, body):
    """Create properly formatted API Gateway response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        },
        'body': json.dumps(body)
    }

def extract_tenant_id(event):
    """Extract tenant_id from API Gateway event"""
    tenant_id = None
    
    # From event body (API Gateway format)
    if 'body' in event and event['body']:
        try:
            body = json.loads(event['body'])
            tenant_id = body.get('tenant_id')
            if tenant_id:
                logger.info(f"📋 Found tenant_id in event body: {tenant_id}")
        except Exception as e:
            logger.warning(f"⚠️ Could not parse event body: {e}")
    
    # Direct invocation (non-API Gateway)
    if not tenant_id and 'tenant_id' in event:
        tenant_id = event['tenant_id']
        logger.info(f"📋 Found tenant_id in event root: {tenant_id}")
    
    logger.info(f"✅ Using tenant_id: {tenant_id}")
    return tenant_id

def get_tenant_configurations(tenant_id: str) -> List[Dict]:
    """Retrieve KSI configurations for a specific tenant"""
    table = dynamodb.Table(TENANT_KSI_CONFIGURATIONS_TABLE)
    
    try:
        logger.info(f"🔍 Querying KSI configurations for tenant: {tenant_id}")
        
        response = table.query(
            KeyConditionExpression='tenant_id = :tid',
            ExpressionAttributeValues={':tid': tenant_id}
        )
        
        configs = response.get('Items', [])
        logger.info(f"📊 Found {len(configs)} KSI configurations for tenant {tenant_id}")
        
        return configs
        
    except Exception as e:
        logger.error(f"❌ Error querying tenant configurations for {tenant_id}: {str(e)}")
        return []

def group_ksis_by_validator(configurations: List[Dict]) -> Dict[str, List[Dict]]:
    """Group KSIs by their validator type based on KSI ID prefix"""
    validator_groups = {
        'cna': [],
        'svc': [],
        'iam': [],
        'mla': [],
        'cmt': []
    }
    
    for config in configurations:
        ksi_id = config.get('ksi_id', '')
        
        if ksi_id.startswith('KSI-CNA'):
            validator_groups['cna'].append(config)
        elif ksi_id.startswith('KSI-SVC'):
            validator_groups['svc'].append(config)
        elif ksi_id.startswith('KSI-IAM'):
            validator_groups['iam'].append(config)
        elif ksi_id.startswith('KSI-MLA'):
            validator_groups['mla'].append(config)
        elif ksi_id.startswith('KSI-CMT'):
            validator_groups['cmt'].append(config)
    
    return validator_groups
EOF

# Package and deploy
echo "📦 Creating deployment package..."
zip -r orchestrator_final.zip orchestrator_handler.py

echo "🚀 Deploying final fix..."
aws lambda update-function-code \
  --region $REGION \
  --function-name $FUNCTION_NAME \
  --zip-file fileb://orchestrator_final.zip

echo "⏳ Waiting for deployment..."
aws lambda wait function-updated \
  --region $REGION \
  --function-name $FUNCTION_NAME

# Cleanup
cd ..
rm -rf temp_api_fix

echo ""
echo "✅ FINAL FIX DEPLOYED!"
echo ""
echo "🧪 Test now:"
echo "curl -X POST 'https://d5804hjt80.execute-api.us-gov-west-1.amazonaws.com/production/api/ksi/validate' \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"tenant_id\": \"riskuity-production\", \"trigger_source\": \"manual\"}'"
