import json
import boto3
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import uuid

def generate_execution_id() -> str:
    """Generate unique execution ID"""
    return str(uuid.uuid4())

def current_timestamp() -> str:
    """Get current UTC timestamp in ISO format"""
    return datetime.now(timezone.utc).isoformat()

def parse_ksi_id(ksi_id: str) -> Dict[str, str]:
    """
    Parse KSI ID into components
    Example: KSI-CNA-01 -> {category: 'CNA', number: '01'}
    """
    if not ksi_id.startswith('KSI-'):
        raise ValueError(f"Invalid KSI ID format: {ksi_id}")
    
    parts = ksi_id.split('-')
    if len(parts) != 3:
        raise ValueError(f"Invalid KSI ID format: {ksi_id}")
    
    return {
        'prefix': parts[0],
        'category': parts[1],
        'number': parts[2]
    }

def get_validator_type(ksi_id: str) -> str:
    """Get validator type from KSI ID"""
    parsed = parse_ksi_id(ksi_id)
    return parsed['category'].lower()

class DynamoDBHelper:
    """Helper class for DynamoDB operations"""
    
    def __init__(self, table_name: str):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(table_name)
        self.table_name = table_name
    
    def put_item(self, item: Dict) -> bool:
        """Put item into table"""
        try:
            self.table.put_item(Item=item)
            return True
        except Exception as e:
            print(f"Error putting item into {self.table_name}: {str(e)}")
            return False
    
    def get_item(self, key: Dict) -> Optional[Dict]:
        """Get item from table"""
        try:
            response = self.table.get_item(Key=key)
            return response.get('Item')
        except Exception as e:
            print(f"Error getting item from {self.table_name}: {str(e)}")
            return None

def validate_event_structure(event: Dict, required_fields: List[str]) -> bool:
    """Validate that event contains required fields"""
    for field in required_fields:
        if field not in event:
            raise ValueError(f"Missing required field in event: {field}")
    return True

def format_validation_result(ksi_id: str, passed: bool, reason: str, **kwargs) -> Dict:
    """Format standardized validation result"""
    return {
        'ksi_id': ksi_id,
        'validation_id': ksi_id,
        'assertion': passed,
        'assertion_reason': reason,
        'timestamp': current_timestamp(),
        'validation_method': kwargs.get('method', 'automated'),
        **{k: v for k, v in kwargs.items() if k != 'method'}
    }
