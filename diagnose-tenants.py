#!/usr/bin/env python3
"""
Diagnose tenant data in DynamoDB to understand the API issue
"""

import boto3
import json
from datetime import datetime
from collections import defaultdict

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-gov-west-1')

# Table names
EXECUTION_HISTORY_TABLE = "riskuity-ksi-validator-ksi-execution-history-production"
TENANT_CONFIG_TABLE = "riskuity-ksi-validator-tenant-ksi-configurations-production"

def diagnose_execution_history():
    """Scan execution history to see what tenants exist"""
    print("🔍 Scanning KSI Execution History Table...")
    print("=" * 50)
    
    table = dynamodb.Table(EXECUTION_HISTORY_TABLE)
    
    # Scan to get all tenant data
    response = table.scan()
    items = response.get('Items', [])
    
    # Group by tenant_id
    tenant_counts = defaultdict(int)
    tenant_latest = defaultdict(str)
    tenant_statuses = defaultdict(set)
    
    for item in items:
        tenant_id = item.get('tenant_id', 'unknown')
        timestamp = item.get('timestamp', '')
        status = item.get('status', 'unknown')
        
        tenant_counts[tenant_id] += 1
        tenant_statuses[tenant_id].add(status)
        
        if timestamp > tenant_latest[tenant_id]:
            tenant_latest[tenant_id] = timestamp
    
    print(f"Total execution records found: {len(items)}")
    print(f"Number of unique tenants: {len(tenant_counts)}")
    print()
    
    print("📊 Tenant Execution Summary:")
    print("-" * 70)
    print(f"{'Tenant ID':<25} {'Count':<8} {'Latest Execution':<20} {'Statuses'}")
    print("-" * 70)
    
    for tenant_id, count in sorted(tenant_counts.items()):
        latest = tenant_latest[tenant_id][:19] if tenant_latest[tenant_id] else 'N/A'
        statuses = ', '.join(sorted(tenant_statuses[tenant_id]))
        print(f"{tenant_id:<25} {count:<8} {latest:<20} {statuses}")
    
    return tenant_counts

def diagnose_tenant_configs():
    """Check tenant configurations"""
    print("\n🏢 Scanning Tenant KSI Configurations Table...")
    print("=" * 50)
    
    table = dynamodb.Table(TENANT_CONFIG_TABLE)
    
    try:
        response = table.scan()
        items = response.get('Items', [])
        
        tenant_ksi_counts = defaultdict(int)
        tenant_names = {}
        
        for item in items:
            tenant_id = item.get('tenant_id', 'unknown')
            tenant_name = item.get('tenant_name', tenant_id)
            tenant_ksi_counts[tenant_id] += 1
            tenant_names[tenant_id] = tenant_name
        
        print(f"Total tenant configurations: {len(items)}")
        print(f"Number of configured tenants: {len(tenant_ksi_counts)}")
        print()
        
        print("🏗️ Tenant Configuration Summary:")
        print("-" * 60)
        print(f"{'Tenant ID':<25} {'Display Name':<20} {'KSI Count'}")
        print("-" * 60)
        
        for tenant_id, ksi_count in sorted(tenant_ksi_counts.items()):
            display_name = tenant_names.get(tenant_id, tenant_id)
            print(f"{tenant_id:<25} {display_name:<20} {ksi_count}")
        
        return tenant_ksi_counts
        
    except Exception as e:
        print(f"❌ Error accessing tenant configurations: {e}")
        return {}

def check_specific_tenant(tenant_id):
    """Check specific tenant data"""
    print(f"\n🎯 Detailed Check for Tenant: {tenant_id}")
    print("=" * 50)
    
    table = dynamodb.Table(EXECUTION_HISTORY_TABLE)
    
    try:
        # Use GSI to query by tenant_id
        response = table.query(
            IndexName='tenant-timestamp-index',
            KeyConditionExpression=boto3.dynamodb.conditions.Key('tenant_id').eq(tenant_id),
            Limit=5,
            ScanIndexForward=False  # Most recent first
        )
        
        items = response.get('Items', [])
        
        if items:
            print(f"✅ Found {len(items)} recent executions for tenant '{tenant_id}'")
            print("\nMost recent executions:")
            for i, item in enumerate(items, 1):
                execution_id = item.get('execution_id', 'N/A')[:8] + '...'
                timestamp = item.get('timestamp', 'N/A')[:19]
                status = item.get('status', 'N/A')
                validators = len(item.get('validators_completed', []))
                print(f"  {i}. {execution_id} | {timestamp} | {status} | {validators} validators")
        else:
            print(f"❌ No executions found for tenant '{tenant_id}'")
            print("   This explains why the API returns empty results!")
        
    except Exception as e:
        print(f"❌ Error querying tenant '{tenant_id}': {e}")

def main():
    """Main diagnostic function"""
    print("🩺 KSI Validator Platform - Tenant Diagnostics")
    print("=" * 60)
    
    # Check execution history
    execution_tenants = diagnose_execution_history()
    
    # Check tenant configurations  
    config_tenants = diagnose_tenant_configs()
    
    # Check specific problematic tenant
    print("\n" + "=" * 60)
    check_specific_tenant('riskuity-production')
    
    # Check if any configured tenants have no executions
    print(f"\n🔄 Cross-Reference Analysis:")
    print("-" * 40)
    
    configured_but_no_executions = set(config_tenants.keys()) - set(execution_tenants.keys())
    executions_but_no_config = set(execution_tenants.keys()) - set(config_tenants.keys())
    
    if configured_but_no_executions:
        print(f"⚠️  Tenants configured but no executions: {list(configured_but_no_executions)}")
    
    if executions_but_no_config:
        print(f"⚠️  Tenants with executions but no config: {list(executions_but_no_config)}")
    
    if not configured_but_no_executions and not executions_but_no_config:
        print("✅ All configured tenants have execution history")
    
    print(f"\n💡 Recommendation:")
    if 'riskuity-production' in configured_but_no_executions:
        print("   1. Run a validation for 'riskuity-production' to create execution history")
        print("   2. Then test the API endpoints")
    elif 'riskuity-production' not in config_tenants:
        print("   1. Configure 'riskuity-production' tenant in the configurations table")
        print("   2. Then run a validation to create execution history")
    else:
        print("   Data looks good - the API handler fix should resolve the issue")

if __name__ == "__main__":
    main()

