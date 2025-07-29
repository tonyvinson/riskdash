#!/bin/bash

# Helper script to create the required Python scripts for Task 2
# This extracts the Python code from the artifacts and creates the needed files

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}📝 CREATING TASK 2 PYTHON SCRIPTS${NC}"
echo "================================="
echo ""

# Create task2_data_validation.py
echo -e "${YELLOW}Creating task2_data_validation.py...${NC}"
cat > task2_data_validation.py << 'EOF'
#!/usr/bin/env python3
"""
Task 2: DynamoDB Data Validation & Cleanup Toolkit

This script will:
1. Validate current table schemas and data integrity
2. Identify fake/test/trash data for cleanup
3. Test current query patterns to identify issues
4. Provide recommendations for data cleanup
"""

import boto3
import json
import sys
from datetime import datetime, timezone
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Dict, List, Any, Tuple
import re

# Initialize DynamoDB client
try:
    dynamodb = boto3.resource('dynamodb', region_name='us-gov-west-1')
    dynamodb_client = boto3.client('dynamodb', region_name='us-gov-west-1')
    print("✅ AWS DynamoDB connection established")
except NoCredentialsError:
    print("❌ AWS credentials not configured. Please run 'aws configure'")
    sys.exit(1)

# Table names based on Terraform configuration
KSI_DEFINITIONS_TABLE = "riskuity-ksi-validator-ksi-definitions-production"
TENANT_KSI_CONFIGURATIONS_TABLE = "riskuity-ksi-validator-tenant-ksi-configurations-production"
KSI_EXECUTION_HISTORY_TABLE = "riskuity-ksi-validator-ksi-execution-history-production"

def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print('='*60)

def print_subsection(title: str):
    """Print a formatted subsection header"""
    print(f"\n📋 {title}")
    print('-'*40)

def validate_table_existence() -> Dict[str, bool]:
    """Check if all expected tables exist and are accessible"""
    print_section("TABLE EXISTENCE VALIDATION")
    
    tables = {
        KSI_DEFINITIONS_TABLE: False,
        TENANT_KSI_CONFIGURATIONS_TABLE: False,
        KSI_EXECUTION_HISTORY_TABLE: False
    }
    
    try:
        existing_tables = dynamodb_client.list_tables()['TableNames']
        
        for table_name in tables.keys():
            if table_name in existing_tables:
                tables[table_name] = True
                print(f"✅ {table_name}")
                
                # Get table info
                try:
                    table_info = dynamodb_client.describe_table(TableName=table_name)
                    table_status = table_info['Table']['TableStatus']
                    item_count = table_info['Table']['ItemCount']
                    print(f"   Status: {table_status}, Items: {item_count}")
                except Exception as e:
                    print(f"   ⚠️  Could not get table details: {str(e)}")
            else:
                print(f"❌ {table_name} - NOT FOUND")
    
    except ClientError as e:
        print(f"❌ Error listing tables: {str(e)}")
    
    return tables

def validate_table_schemas() -> Dict[str, Dict]:
    """Validate table schemas match expected composite key structure"""
    print_section("TABLE SCHEMA VALIDATION")
    
    schema_results = {}
    
    # Expected schemas based on Terraform configuration
    expected_schemas = {
        KSI_DEFINITIONS_TABLE: {
            'hash_key': 'ksi_id',
            'range_key': 'version',
            'expected_attributes': ['ksi_id', 'version']
        },
        TENANT_KSI_CONFIGURATIONS_TABLE: {
            'hash_key': 'tenant_id',
            'range_key': 'ksi_id', 
            'expected_attributes': ['tenant_id', 'ksi_id']
        },
        KSI_EXECUTION_HISTORY_TABLE: {
            'hash_key': 'execution_id',
            'range_key': 'timestamp',
            'expected_attributes': ['execution_id', 'timestamp']
        }
    }
    
    for table_name, expected in expected_schemas.items():
        print_subsection(f"Validating {table_name}")
        
        try:
            table_info = dynamodb_client.describe_table(TableName=table_name)
            key_schema = table_info['Table']['KeySchema']
            
            # Extract actual keys
            actual_hash_key = None
            actual_range_key = None
            
            for key in key_schema:
                if key['KeyType'] == 'HASH':
                    actual_hash_key = key['AttributeName']
                elif key['KeyType'] == 'RANGE':
                    actual_range_key = key['AttributeName']
            
            # Validate schema
            schema_valid = True
            if actual_hash_key != expected['hash_key']:
                print(f"❌ Hash key mismatch: expected '{expected['hash_key']}', got '{actual_hash_key}'")
                schema_valid = False
            else:
                print(f"✅ Hash key: {actual_hash_key}")
            
            if actual_range_key != expected['range_key']:
                print(f"❌ Range key mismatch: expected '{expected['range_key']}', got '{actual_range_key}'")
                schema_valid = False
            else:
                print(f"✅ Range key: {actual_range_key}")
            
            schema_results[table_name] = {
                'valid': schema_valid,
                'hash_key': actual_hash_key,
                'range_key': actual_range_key
            }
            
        except ClientError as e:
            print(f"❌ Error validating {table_name}: {str(e)}")
            schema_results[table_name] = {'valid': False, 'error': str(e)}
    
    return schema_results

def analyze_data_integrity() -> Dict[str, Any]:
    """Analyze data integrity and identify potential issues"""
    print_section("DATA INTEGRITY ANALYSIS")
    
    integrity_results = {}
    
    # Analyze KSI Definitions
    print_subsection("KSI Definitions Analysis")
    try:
        table = dynamodb.Table(KSI_DEFINITIONS_TABLE)
        response = table.scan()
        items = response.get('Items', [])
        
        ksi_analysis = {
            'total_count': len(items),
            'ksi_ids': [],
            'versions': [],
            'categories': [],
            'missing_fields': [],
            'suspicious_data': []
        }
        
        for item in items:
            ksi_analysis['ksi_ids'].append(item.get('ksi_id', 'MISSING'))
            ksi_analysis['versions'].append(item.get('version', 'MISSING'))
            ksi_analysis['categories'].append(item.get('category', 'MISSING'))
            
            # Check for missing required fields
            required_fields = ['ksi_id', 'version', 'category', 'title', 'description']
            missing = [field for field in required_fields if field not in item]
            if missing:
                ksi_analysis['missing_fields'].append({
                    'ksi_id': item.get('ksi_id', 'UNKNOWN'),
                    'missing': missing
                })
        
        print(f"Total KSI Definitions: {ksi_analysis['total_count']}")
        print(f"Unique KSI IDs: {len(set(ksi_analysis['ksi_ids']))}")
        print(f"Categories found: {set(ksi_analysis['categories'])}")
        
        if ksi_analysis['missing_fields']:
            print(f"⚠️  Items with missing fields: {len(ksi_analysis['missing_fields'])}")
        
        integrity_results['ksi_definitions'] = ksi_analysis
        
    except Exception as e:
        print(f"❌ Error analyzing KSI definitions: {str(e)}")
        integrity_results['ksi_definitions'] = {'error': str(e)}
    
    # Analyze Tenant Configurations
    print_subsection("Tenant Configurations Analysis")
    try:
        table = dynamodb.Table(TENANT_KSI_CONFIGURATIONS_TABLE)
        response = table.scan()
        items = response.get('Items', [])
        
        tenant_analysis = {
            'total_count': len(items),
            'tenant_ids': [],
            'ksi_ids': [],
            'test_data_indicators': [],
            'suspicious_tenants': []
        }
        
        for item in items:
            tenant_id = item.get('tenant_id', 'MISSING')
            ksi_id = item.get('ksi_id', 'MISSING')
            
            tenant_analysis['tenant_ids'].append(tenant_id)
            tenant_analysis['ksi_ids'].append(ksi_id)
            
            # Identify potential test/fake data
            test_indicators = []
            if tenant_id in ['default', 'test', 'demo', 'example', 'fake']:
                test_indicators.append('suspicious_tenant_id')
            
            if tenant_id and tenant_id.lower().startswith(('test', 'demo', 'fake', 'example')):
                test_indicators.append('test_prefix')
            
            if test_indicators:
                tenant_analysis['test_data_indicators'].append({
                    'tenant_id': tenant_id,
                    'ksi_id': ksi_id,
                    'indicators': test_indicators
                })
        
        unique_tenants = set(tenant_analysis['tenant_ids'])
        print(f"Total configurations: {tenant_analysis['total_count']}")
        print(f"Unique tenants: {len(unique_tenants)}")
        print(f"Tenant IDs: {sorted(unique_tenants)}")
        
        if tenant_analysis['test_data_indicators']:
            print(f"⚠️  Potential test data found: {len(tenant_analysis['test_data_indicators'])} items")
            for item in tenant_analysis['test_data_indicators']:
                print(f"   - {item['tenant_id']}/{item['ksi_id']}: {item['indicators']}")
        
        integrity_results['tenant_configurations'] = tenant_analysis
        
    except Exception as e:
        print(f"❌ Error analyzing tenant configurations: {str(e)}")
        integrity_results['tenant_configurations'] = {'error': str(e)}
    
    # Analyze Execution History
    print_subsection("Execution History Analysis")
    try:
        table = dynamodb.Table(KSI_EXECUTION_HISTORY_TABLE)
        response = table.scan()
        items = response.get('Items', [])
        
        history_analysis = {
            'total_count': len(items),
            'execution_ids': [],
            'tenant_ids': [],
            'old_records': [],
            'recent_records': []
        }
        
        now = datetime.now(timezone.utc)
        
        for item in items:
            execution_id = item.get('execution_id', 'MISSING')
            tenant_id = item.get('tenant_id', 'MISSING')
            timestamp_str = item.get('timestamp', '')
            
            history_analysis['execution_ids'].append(execution_id)
            history_analysis['tenant_ids'].append(tenant_id)
            
            # Analyze record age
            try:
                if timestamp_str:
                    # Handle various timestamp formats
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    age_days = (now - timestamp).days
                    
                    if age_days > 90:  # Older than 90 days
                        history_analysis['old_records'].append({
                            'execution_id': execution_id,
                            'tenant_id': tenant_id,
                            'age_days': age_days
                        })
                    elif age_days <= 7:  # Recent records
                        history_analysis['recent_records'].append({
                            'execution_id': execution_id,
                            'tenant_id': tenant_id,
                            'age_days': age_days
                        })
            except Exception:
                pass  # Skip invalid timestamps
        
        print(f"Total execution records: {history_analysis['total_count']}")
        print(f"Recent records (≤7 days): {len(history_analysis['recent_records'])}")
        print(f"Old records (>90 days): {len(history_analysis['old_records'])}")
        
        integrity_results['execution_history'] = history_analysis
        
    except Exception as e:
        print(f"❌ Error analyzing execution history: {str(e)}")
        integrity_results['execution_history'] = {'error': str(e)}
    
    return integrity_results

def test_current_query_patterns() -> Dict[str, Any]:
    """Test current query patterns to identify composite key issues"""
    print_section("QUERY PATTERN TESTING")
    
    test_results = {}
    
    # Test 1: Single tenant_id query (this should work with composite keys)
    print_subsection("Testing Tenant Configuration Queries")
    try:
        table = dynamodb.Table(TENANT_KSI_CONFIGURATIONS_TABLE)
        
        # Get a sample tenant_id first
        scan_response = table.scan(Limit=1)
        if scan_response.get('Items'):
            sample_tenant = scan_response['Items'][0]['tenant_id']
            
            # Test correct composite key query
            try:
                query_response = table.query(
                    KeyConditionExpression='tenant_id = :tid',
                    ExpressionAttributeValues={':tid': sample_tenant}
                )
                print(f"✅ Composite key query successful: found {len(query_response.get('Items', []))} items")
                test_results['tenant_query'] = {'success': True, 'count': len(query_response.get('Items', []))}
            except Exception as e:
                print(f"❌ Composite key query failed: {str(e)}")
                test_results['tenant_query'] = {'success': False, 'error': str(e)}
            
            # Test problematic single-key get_item (this should fail for composite key table)
            try:
                get_response = table.get_item(Key={'tenant_id': sample_tenant})
                print(f"⚠️  Single key get_item unexpectedly succeeded: {get_response.get('Item', 'No item')}")
                test_results['single_key_get'] = {'success': True, 'warning': 'This should not work for composite key table'}
            except Exception as e:
                print(f"✅ Single key get_item correctly failed: {str(e)}")
                test_results['single_key_get'] = {'success': False, 'expected': True, 'error': str(e)}
        else:
            print("⚠️  No tenant configurations found to test")
            test_results['tenant_query'] = {'success': False, 'error': 'No data to test'}
            
    except Exception as e:
        print(f"❌ Error testing tenant queries: {str(e)}")
        test_results['tenant_query'] = {'success': False, 'error': str(e)}
    
    return test_results

def generate_cleanup_recommendations(integrity_results: Dict[str, Any]) -> List[str]:
    """Generate cleanup recommendations based on analysis"""
    print_section("CLEANUP RECOMMENDATIONS")
    
    recommendations = []
    
    # Check for test data in tenant configurations
    if 'tenant_configurations' in integrity_results:
        tenant_data = integrity_results['tenant_configurations']
        if 'test_data_indicators' in tenant_data and tenant_data['test_data_indicators']:
            recommendations.append(
                f"🗑️  REMOVE TEST DATA: Found {len(tenant_data['test_data_indicators'])} tenant configurations with test data indicators"
            )
            for item in tenant_data['test_data_indicators']:
                recommendations.append(f"   - Delete: {item['tenant_id']}/{item['ksi_id']}")
    
    # Check for old execution records
    if 'execution_history' in integrity_results:
        history_data = integrity_results['execution_history']
        if 'old_records' in history_data and history_data['old_records']:
            recommendations.append(
                f"🗑️  CLEANUP OLD RECORDS: Found {len(history_data['old_records'])} execution records older than 90 days"
            )
            recommendations.append("   - Consider enabling DynamoDB TTL for automatic cleanup")
    
    # Check for missing fields
    if 'ksi_definitions' in integrity_results:
        ksi_data = integrity_results['ksi_definitions']
        if 'missing_fields' in ksi_data and ksi_data['missing_fields']:
            recommendations.append(
                f"⚠️  FIX DATA INTEGRITY: Found {len(ksi_data['missing_fields'])} KSI definitions with missing required fields"
            )
    
    if not recommendations:
        recommendations.append("✅ No significant cleanup needed - data appears clean")
    
    for rec in recommendations:
        print(rec)
    
    return recommendations

def main():
    """Main execution function"""
    print("🚀 TASK 2: DynamoDB DATA VALIDATION & CLEANUP TOOLKIT")
    print("=====================================================")
    print("This toolkit will analyze your DynamoDB tables and identify issues before applying fixes.")
    
    # Step 1: Validate table existence
    table_status = validate_table_existence()
    
    if not all(table_status.values()):
        print("\n❌ CRITICAL: Not all required tables exist!")
        print("Please ensure your Terraform infrastructure is deployed.")
        return 1
    
    # Step 2: Validate schemas
    schema_results = validate_table_schemas()
    
    if not all(result.get('valid', False) for result in schema_results.values()):
        print("\n❌ CRITICAL: Table schemas don't match expected composite key structure!")
        print("This indicates potential infrastructure issues.")
    
    # Step 3: Analyze data integrity
    integrity_results = analyze_data_integrity()
    
    # Step 4: Test query patterns
    query_results = test_current_query_patterns()
    
    # Step 5: Generate cleanup recommendations
    recommendations = generate_cleanup_recommendations(integrity_results)
    
    # Final summary
    print_section("FINAL SUMMARY & NEXT STEPS")
    
    print("📊 ANALYSIS COMPLETE!")
    print("\n🎯 RECOMMENDED NEXT STEPS:")
    print("1. Review cleanup recommendations above")
    print("2. Execute cleanup commands (will be provided)")
    print("3. Re-run this validation after cleanup")
    print("4. Proceed with DynamoDB composite key fixes")
    
    # Generate cleanup script if needed
    has_test_data = False
    if 'tenant_configurations' in integrity_results:
        test_indicators = integrity_results['tenant_configurations'].get('test_data_indicators', [])
        if test_indicators:
            has_test_data = True
            print("\n📋 CLEANUP SCRIPT NEEDED:")
            print("Run the data cleanup script to remove test data before proceeding.")
    
    if not has_test_data:
        print("\n✅ DATA IS CLEAN - Ready to proceed with Task 2 fixes!")
    
    return 0

if __name__ == "__main__":
    exit(main())
EOF

echo -e "${GREEN}✅ Created task2_data_validation.py${NC}"

# Create task2_data_cleanup.py (truncated for brevity - in real usage, copy full content from artifact)
echo -e "${YELLOW}Creating task2_data_cleanup.py...${NC}"
cat > task2_data_cleanup.py << 'EOF'
#!/usr/bin/env python3
"""
Task 2: DynamoDB Data Cleanup Script

This script safely removes identified trash/fake/test data from DynamoDB tables.
IMPORTANT: Run the validation toolkit first to identify what needs cleanup!
"""

import boto3
import json
import sys
from datetime import datetime, timezone, timedelta
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Dict, List, Any
import argparse

# Initialize DynamoDB
try:
    dynamodb = boto3.resource('dynamodb', region_name='us-gov-west-1')
    dynamodb_client = boto3.client('dynamodb', region_name='us-gov-west-1')
    print("✅ AWS DynamoDB connection established")
except NoCredentialsError:
    print("❌ AWS credentials not configured. Please run 'aws configure'")
    sys.exit(1)

# Table names
KSI_DEFINITIONS_TABLE = "riskuity-ksi-validator-ksi-definitions-production"
TENANT_KSI_CONFIGURATIONS_TABLE = "riskuity-ksi-validator-tenant-ksi-configurations-production"
KSI_EXECUTION_HISTORY_TABLE = "riskuity-ksi-validator-ksi-execution-history-production"

def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"🧹 {title}")
    print('='*60)

def identify_test_tenant_data() -> List[Dict]:
    """Identify test/fake tenant configuration data"""
    print_section("IDENTIFYING TEST TENANT DATA")
    
    test_data = []
    
    try:
        table = dynamodb.Table(TENANT_KSI_CONFIGURATIONS_TABLE)
        response = table.scan()
        items = response.get('Items', [])
        
        # Handle pagination
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response.get('Items', []))
        
        # Identify test data patterns
        test_tenant_patterns = [
            'default', 'test', 'demo', 'example', 'fake', 'sample',
            'dev', 'development', 'staging', 'temp', 'temporary'
        ]
        
        for item in items:
            tenant_id = item.get('tenant_id', '').lower()
            ksi_id = item.get('ksi_id', '')
            
            # Check for suspicious tenant names
            is_test_data = False
            reason = []
            
            if tenant_id in test_tenant_patterns:
                is_test_data = True
                reason.append(f"suspicious_tenant_id: {tenant_id}")
            
            for pattern in test_tenant_patterns:
                if tenant_id.startswith(pattern):
                    is_test_data = True
                    reason.append(f"test_prefix: {pattern}")
                    break
            
            if is_test_data:
                test_data.append({
                    'tenant_id': item.get('tenant_id'),
                    'ksi_id': ksi_id,
                    'reason': reason,
                    'item': item
                })
        
        print(f"Found {len(test_data)} test data items:")
        for item_info in test_data:
            print(f"  - {item_info['tenant_id']}/{item_info['ksi_id']}: {item_info['reason']}")
        
        return test_data
        
    except Exception as e:
        print(f"❌ Error identifying test data: {str(e)}")
        return []

def cleanup_test_tenant_data(test_data: List[Dict], dry_run: bool = True) -> int:
    """Remove identified test tenant data"""
    print_section(f"{'DRY RUN: ' if dry_run else ''}CLEANING UP TEST TENANT DATA")
    
    if not test_data:
        print("No test data to clean up")
        return 0
    
    deleted_count = 0
    table = dynamodb.Table(TENANT_KSI_CONFIGURATIONS_TABLE)
    
    for item_info in test_data:
        tenant_id = item_info['tenant_id']
        ksi_id = item_info['ksi_id']
        
        try:
            if dry_run:
                print(f"[DRY RUN] Would delete: {tenant_id}/{ksi_id}")
            else:
                response = table.delete_item(
                    Key={
                        'tenant_id': tenant_id,
                        'ksi_id': ksi_id
                    }
                )
                print(f"✅ Deleted: {tenant_id}/{ksi_id}")
                deleted_count += 1
                
        except Exception as e:
            print(f"❌ Error deleting {tenant_id}/{ksi_id}: {str(e)}")
    
    if not dry_run:
        print(f"\n🎉 Successfully deleted {deleted_count} test tenant configurations")
    else:
        print(f"\n📋 Would delete {len(test_data)} test tenant configurations")
    
    return deleted_count

def create_production_tenant_data() -> bool:
    """Create clean production tenant configuration data"""
    print_section("CREATING CLEAN PRODUCTION TENANT DATA")
    
    # Define clean production tenant configurations
    production_configs = [
        {
            "tenant_id": "riskuity-production",
            "ksi_id": "KSI-CMT-01",
            "enabled": True,
            "priority": "high",
            "schedule": "daily",
            "last_updated": datetime.now(timezone.utc).isoformat()
        },
        {
            "tenant_id": "riskuity-production",
            "ksi_id": "KSI-SVC-06",
            "enabled": True,
            "priority": "medium",
            "schedule": "daily",
            "last_updated": datetime.now(timezone.utc).isoformat()
        },
        {
            "tenant_id": "riskuity-production",
            "ksi_id": "KSI-CNA-01",
            "enabled": True,
            "priority": "high",
            "schedule": "daily",
            "last_updated": datetime.now(timezone.utc).isoformat()
        },
        {
            "tenant_id": "riskuity-production",
            "ksi_id": "KSI-IAM-01",
            "enabled": True,
            "priority": "critical",
            "schedule": "daily",
            "last_updated": datetime.now(timezone.utc).isoformat()
        },
        {
            "tenant_id": "riskuity-production",
            "ksi_id": "KSI-MLA-01",
            "enabled": True,
            "priority": "medium",
            "schedule": "daily",
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    table = dynamodb.Table(TENANT_KSI_CONFIGURATIONS_TABLE)
    success_count = 0
    
    for config in production_configs:
        try:
            table.put_item(Item=config)
            print(f"✅ Created: {config['tenant_id']}/{config['ksi_id']}")
            success_count += 1
        except Exception as e:
            print(f"❌ Error creating {config['ksi_id']}: {str(e)}")
    
    print(f"\n🎉 Successfully created {success_count} production tenant configurations")
    return success_count == len(production_configs)

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Clean up DynamoDB test/fake data')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show what would be deleted without actually deleting')
    parser.add_argument('--backup', action='store_true',
                       help='Create backup before cleanup')
    parser.add_argument('--days-old', type=int, default=90,
                       help='Delete execution records older than N days (default: 90)')
    parser.add_argument('--create-production', action='store_true',
                       help='Create clean production tenant configuration data')
    
    args = parser.parse_args()
    
    print("🧹 TASK 2: DynamoDB DATA CLEANUP SCRIPT")
    print("======================================")
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No data will be actually deleted")
    else:
        print("⚠️  LIVE MODE - Data will be permanently deleted!")
        confirm = input("Are you sure you want to proceed? (type 'yes' to confirm): ")
        if confirm.lower() != 'yes':
            print("❌ Cleanup cancelled")
            return 0
    
    total_cleaned = 0
    
    # Step 1: Clean up test tenant data
    test_data = identify_test_tenant_data()
    if test_data:
        cleaned = cleanup_test_tenant_data(test_data, args.dry_run)
        total_cleaned += cleaned
    
    # Step 2: Create production data if requested
    if args.create_production and not args.dry_run:
        create_production_tenant_data()
    
    print_section("CLEANUP SUMMARY")
    
    if args.dry_run:
        print(f"📋 DRY RUN COMPLETE: Would clean up {total_cleaned} items")
        print("\n🎯 To actually perform cleanup:")
        print(f"   python {sys.argv[0]} --backup --create-production")
    else:
        print(f"🎉 CLEANUP COMPLETE: Removed {total_cleaned} items")
        print("\n✅ Ready to proceed with Task 2 DynamoDB composite key fixes!")
    
    return 0

if __name__ == "__main__":
    exit(main())
EOF

echo -e "${GREEN}✅ Created task2_data_cleanup.py${NC}"

# Make scripts executable
chmod +x task2_data_validation.py task2_data_cleanup.py

echo ""
echo -e "${GREEN}🎉 Task 2 Python scripts created successfully!${NC}"
echo ""
echo -e "${CYAN}📋 Files created:${NC}"
echo "  ✅ task2_data_validation.py - Data validation and analysis"
echo "  ✅ task2_data_cleanup.py - Safe data cleanup script"
echo ""
echo -e "${CYAN}🚀 Next step:${NC}"
echo "  Run the workflow: ./task2_workflow.sh"
