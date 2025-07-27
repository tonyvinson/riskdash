import json
import boto3
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List
import os
from decimal import Decimal

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')

# Environment variables
ENVIRONMENT = os.environ['ENVIRONMENT']
KSI_EXECUTION_HISTORY_TABLE = os.environ['KSI_EXECUTION_HISTORY_TABLE']
KSI_DEFINITIONS_TABLE = os.environ['KSI_DEFINITIONS_TABLE']

def decimal_default(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def get_ksi_categories():
    """Get KSI categories mapping"""
    return {
        'CNA': 'Configuration & Network Architecture',
        'SVC': 'Service Configuration', 
        'IAM': 'Identity & Access Management',
        'MLA': 'Monitoring, Logging & Alerting',
        'CMT': 'Configuration Management & Tracking'
    }

def parse_ksi_status(assertion_reason: str) -> str:
    """Parse KSI status from assertion reason"""
    if not assertion_reason:
        return 'unknown'
    
    assertion_lower = assertion_reason.lower()
    if '✅' in assertion_reason or 'pass' in assertion_lower:
        return 'passed'
    elif '❌' in assertion_reason or 'fail' in assertion_lower:
        return 'failed'
    elif '⚠️' in assertion_reason or 'warning' in assertion_lower:
        return 'warning'
    elif '🟡' in assertion_reason or 'low risk' in assertion_lower:
        return 'warning'
    elif 'ℹ️' in assertion_reason or 'info' in assertion_lower:
        return 'info'
    else:
        return 'info'

def lambda_handler(event, context):
    """
    API Handler for GET /api/ksi/results
    Retrieves KSI validation results from DynamoDB
    """
    try:
        # Parse query parameters
        query_params = event.get('queryStringParameters') or {}
        tenant_id = query_params.get('tenant_id')
        execution_id = query_params.get('execution_id')
        ksi_id = query_params.get('ksi_id')
        category = query_params.get('category')
        limit = int(query_params.get('limit', 100))
        
        # Validate limit
        if limit > 500:
            limit = 500
        
        logger.info(f"Fetching results - tenant: {tenant_id}, execution: {execution_id}, ksi: {ksi_id}, category: {category}")
        
        table = dynamodb.Table(KSI_EXECUTION_HISTORY_TABLE)
        
        # Build scan parameters
        scan_params = {
            'Limit': limit
        }
        
        # Build filter expressions
        filter_expressions = []
        expression_values = {}
        
        if tenant_id:
            filter_expressions.append('tenant_id = :tenant_id')
            expression_values[':tenant_id'] = tenant_id
            
        if execution_id:
            filter_expressions.append('execution_id = :execution_id')
            expression_values[':execution_id'] = execution_id
            
        if ksi_id:
            filter_expressions.append('ksi_id = :ksi_id')
            expression_values[':ksi_id'] = ksi_id
            
        if category:
            filter_expressions.append('contains(ksi_id, :category)')
            expression_values[':category'] = f'KSI-{category.upper()}-'
        
        # Apply filters if any
        if filter_expressions:
            scan_params['FilterExpression'] = ' AND '.join(filter_expressions)
            scan_params['ExpressionAttributeValues'] = expression_values
        
        # Execute scan
        response = table.scan(**scan_params)
        results = response.get('Items', [])
        
        # Process results
        processed_results = []
        categories = get_ksi_categories()
        
        for result in results:
            # Parse KSI category from ID
            ksi_id = result.get('ksi_id', '')
            category_code = ''
            if ksi_id.startswith('KSI-') and len(ksi_id.split('-')) >= 2:
                category_code = ksi_id.split('-')[1]
            
            processed_result = {
                'ksi_id': result.get('ksi_id'),
                'validation_id': result.get('validation_id'),
                'execution_id': result.get('execution_id'),
                'tenant_id': result.get('tenant_id'),
                'status': parse_ksi_status(result.get('assertion_reason', '')),
                'assertion': result.get('assertion'),
                'assertion_reason': result.get('assertion_reason'),
                'cli_command': result.get('cli_command'),
                'commands_executed': result.get('commands_executed'),
                'successful_commands': result.get('successful_commands'),
                'failed_commands': result.get('failed_commands'),
                'timestamp': result.get('timestamp'),
                'validation_method': result.get('validation_method'),
                'category_code': category_code,
                'category_name': categories.get(category_code, 'Unknown'),
                'evidence_path': result.get('evidence_path'),
                'requirement': result.get('requirement')
            }
            processed_results.append(processed_result)
        
        # Sort by timestamp (most recent first)
        processed_results = sorted(
            processed_results,
            key=lambda x: x.get('timestamp', ''),
            reverse=True
        )
        
        # Generate summary statistics
        summary = {
            'total_results': len(processed_results),
            'by_status': {},
            'by_category': {},
            'execution_summary': {}
        }
        
        for result in processed_results:
            status = result['status']
            category_code = result['category_code']
            execution_id = result['execution_id']
            
            summary['by_status'][status] = summary['by_status'].get(status, 0) + 1
            summary['by_category'][category_code] = summary['by_category'].get(category_code, 0) + 1
            
            if execution_id not in summary['execution_summary']:
                summary['execution_summary'][execution_id] = {
                    'total': 0,
                    'passed': 0,
                    'failed': 0,
                    'warning': 0,
                    'info': 0,
                    'unknown': 0 
                }
            summary['execution_summary'][execution_id]['total'] += 1
            summary['execution_summary'][execution_id][status] += 1
        
        # Build API response
        api_response = {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
            },
            'body': json.dumps({
                'results': processed_results,
                'summary': summary,
                'categories': categories,
                'filters': {
                    'tenant_id': tenant_id,
                    'execution_id': execution_id,
                    'ksi_id': ksi_id,
                    'category': category,
                    'limit': limit
                },
                'timestamp': datetime.now(timezone.utc).isoformat()
            }, default=decimal_default)
        }
        
        logger.info(f"Successfully retrieved {len(processed_results)} results")
        return api_response
        
    except Exception as e:
        logger.error(f"Error retrieving results: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }
