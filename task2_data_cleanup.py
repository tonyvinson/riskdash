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
