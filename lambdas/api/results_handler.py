import json
import boto3
import logging
import os
from typing import Dict, Any
from decimal import Decimal
from boto3.dynamodb.conditions import Key

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')

# Environment variables
KSI_EXECUTION_HISTORY_TABLE = os.environ['KSI_EXECUTION_HISTORY_TABLE']

def decimal_default(obj):
    """JSON serializer for DynamoDB Decimal objects"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    API endpoint for getting KSI validation results
    Handles both execution summaries and individual validator records with CLI details
    """
    
    # CORS headers for all responses
    cors_headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'GET,OPTIONS'
    }
    
    try:
        # Get query parameters
        query_params = event.get('queryStringParameters') or {}
        tenant_id = query_params.get('tenant_id', 'default')
        execution_id = query_params.get('execution_id')
        limit = int(query_params.get('limit', 10))
        
        logger.info(f"Results API called - tenant: {tenant_id}, execution_id: {execution_id}")
        
        table = dynamodb.Table(KSI_EXECUTION_HISTORY_TABLE)
        
        if execution_id:
            # Check if this is an individual validator record (contains #)
            if '#' in execution_id:
                logger.info(f"Querying individual validator record: {execution_id}")
                # Query for specific individual validator record
                response = table.query(
                    KeyConditionExpression=Key('execution_id').eq(execution_id),
                    Limit=1
                )
                items = response.get('Items', [])
                
                if items:
                    # Return the individual validator record with CLI details
                    validator_record = items[0]
                    validation_result = validator_record.get('validation_result', {})
                    
                    return {
                        'statusCode': 200,
                        'headers': cors_headers,
                        'body': json.dumps({
                            'success': True,
                            'debug': {
                                'table_name': KSI_EXECUTION_HISTORY_TABLE,
                                'tenant_id_requested': tenant_id,
                                'execution_id_requested': execution_id,
                                'total_items_found': len(items),
                                'validation_items_found': 1 if validation_result else 0,
                                'sample_item_keys': [list(validator_record.keys())] if items else [],
                                'function_name': context.function_name if context else 'results_handler',
                                'aws_region': os.environ.get('AWS_REGION', 'us-gov-west-1')
                            },
                            'data': {
                                'validation_results': [validation_result] if validation_result else [],
                                'message': 'Individual validator record retrieved successfully'
                            }
                        }, default=decimal_default)
                    }
                else:
                    return {
                        'statusCode': 404,
                        'headers': cors_headers,
                        'body': json.dumps({
                            'success': False,
                            'error': 'Individual validator record not found',
                            'execution_id': execution_id
                        })
                    }
            else:
                # Query for execution summary records using GSI
                logger.info(f"Querying execution summaries for: {execution_id}")
                response = table.query(
                    IndexName='tenant-timestamp-index',
                    KeyConditionExpression=Key('tenant_id').eq(tenant_id),
                    FilterExpression=Key('execution_id').begins_with(execution_id),
                    ScanIndexForward=False,
                    Limit=limit
                )
                items = response.get('Items', [])
                
                # Filter for execution summaries (not individual validator records)
                execution_summaries = []
                validation_records = []
                
                for item in items:
                    if '#' not in item.get('execution_id', ''):
                        # This is an execution summary
                        execution_summaries.append(item)
                    else:
                        # This is an individual validator record
                        validation_records.append(item)
                
                return {
                    'statusCode': 200,
                    'headers': cors_headers,
                    'body': json.dumps({
                        'success': True,
                        'debug': {
                            'table_name': KSI_EXECUTION_HISTORY_TABLE,
                            'tenant_id_requested': tenant_id,
                            'execution_id_requested': execution_id,
                            'total_items_found': len(items),
                            'validation_items_found': len(validation_records),
                            'sample_item_keys': [list(items[0].keys()), list(items[1].keys()) if len(items) > 1 else []] if items else [],
                            'function_name': context.function_name if context else 'results_handler',
                            'aws_region': os.environ.get('AWS_REGION', 'us-gov-west-1')
                        },
                        'data': {
                            'validation_results': execution_summaries if execution_summaries else validation_records,
                            'message': 'Diagnostic scan successful'
                        }
                    }, default=decimal_default)
                }
        else:
            # No execution_id provided - get recent results for tenant
            logger.info(f"Querying recent results for tenant: {tenant_id}")
            response = table.query(
                IndexName='tenant-timestamp-index',
                KeyConditionExpression=Key('tenant_id').eq(tenant_id),
                ScanIndexForward=False,
                Limit=limit
            )
            items = response.get('Items', [])
            
            # Filter for execution summaries (not individual validator records)
            execution_summaries = [item for item in items if '#' not in item.get('execution_id', '')]
            
            return {
                'statusCode': 200,
                'headers': cors_headers,
                'body': json.dumps({
                    'success': True,
                    'debug': {
                        'table_name': KSI_EXECUTION_HISTORY_TABLE,
                        'tenant_id_requested': tenant_id,
                        'execution_id_requested': execution_id,
                        'total_items_found': len(items),
                        'validation_items_found': len(execution_summaries),
                        'sample_item_keys': [list(items[0].keys())] if items else [],
                        'function_name': context.function_name if context else 'results_handler',
                        'aws_region': os.environ.get('AWS_REGION', 'us-gov-west-1')
                    },
                    'data': {
                        'validation_results': execution_summaries,
                        'message': 'Recent execution summaries retrieved successfully'
                    }
                }, default=decimal_default)
            }
            
    except Exception as e:
        logger.error(f"Error in results handler: {str(e)}")
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({
                'success': False,
                'error': 'Internal server error',
                'message': str(e)
            })
        }
