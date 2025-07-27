#!/usr/bin/env python3
"""
Initialize Riskuity as tenant zero in the SaaS KSI Validator
"""

import boto3
import json
from datetime import datetime, timezone
import os

# Get configuration from environment or use defaults
PROJECT_NAME = os.environ.get('PROJECT_NAME', 'riskuity-ksi-validator')
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'dev')
REGION = os.environ.get('AWS_REGION', 'us-gov-west-1')

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb', region_name=REGION)
sts_client = boto3.client('sts', region_name=REGION)

def get_account_id():
    """Get current AWS account ID"""
    return sts_client.get_caller_identity()['Account']

def initialize_riskuity_tenant():
    """Initialize Riskuity as tenant zero"""
    
    account_id = get_account_id()
    tenant_metadata_table = dynamodb.Table(f"{PROJECT_NAME}-tenant-metadata-{ENVIRONMENT}")
    tenant_config_table = dynamodb.Table(f"{PROJECT_NAME}-tenant-ksi-configurations-{ENVIRONMENT}")
    
    print(f"🏢 Initializing Riskuity as tenant zero in account {account_id}")
    
    # Riskuity tenant metadata
    riskuity_tenant = {
        "tenant_id": "riskuity-internal",
        "tenant_type": "csp_internal",
        "onboarding_status": "active",
        "organization": {
            "name": "Riskuity LLC",
            "display_name": "Riskuity (Internal)",
            "type": "cloud_service_provider",
            "federal_entity": False,
            "industry": "Cloud Security & Compliance",
            "size": "small_business"
        },
        "contact_info": {
            "primary_contact": {
                "name": "Riskuity Security Team",
                "email": "security@riskuity.com",
                "role": "Primary Security Contact"
            }
        },
        "aws_configuration": {
            "account_id": account_id,
            "primary_region": REGION,
            "access_method": "native",
            "connection_status": "connected",
            "last_connection_test": datetime.now(timezone.utc).isoformat()
        },
        "compliance_profile": {
            "fedramp_level": "Low",
            "target_compliance": ["FedRAMP", "SOC-2", "NIST-800-53"],
            "authorization_boundary": "riskuity-saas-platform",
            "ato_status": "in_progress"
        },
        "metadata": {
            "created_date": datetime.now(timezone.utc).isoformat(),
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "created_by": "system_admin",
            "status": "active",
            "onboarding_completed": True,
            "notes": "Riskuity's own infrastructure - Customer Zero"
        }
    }
    
    # Save tenant metadata
    try:
        tenant_metadata_table.put_item(Item=riskuity_tenant)
        print("✅ Riskuity tenant metadata created")
    except Exception as e:
        print(f"❌ Error creating tenant metadata: {str(e)}")
        return False
    
    # Create default KSI configurations for Riskuity
    ksi_configs = [
        {
            "tenant_id": "riskuity-internal",
            "ksi_id": "KSI-CNA-01",
            "enabled": True,
            "priority": "critical",
            "schedule": "hourly",
            "last_updated": datetime.now(timezone.utc).isoformat()
        },
        {
            "tenant_id": "riskuity-internal",
            "ksi_id": "KSI-IAM-01",
            "enabled": True,
            "priority": "critical",
            "schedule": "hourly",
            "last_updated": datetime.now(timezone.utc).isoformat()
        },
        {
            "tenant_id": "riskuity-internal",
            "ksi_id": "KSI-SVC-01",
            "enabled": True,
            "priority": "high",
            "schedule": "hourly",
            "last_updated": datetime.now(timezone.utc).isoformat()
        },
        {
            "tenant_id": "riskuity-internal",
            "ksi_id": "KSI-MLA-01",
            "enabled": True,
            "priority": "high",
            "schedule": "hourly",
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    for config in ksi_configs:
        try:
            tenant_config_table.put_item(Item=config)
            print(f"✅ KSI configuration created: {config['ksi_id']}")
        except Exception as e:
            print(f"❌ Error creating KSI config {config['ksi_id']}: {str(e)}")
    
    print("\n🎉 Riskuity tenant initialization complete!")
    print(f"Tenant ID: riskuity-internal")
    print(f"Account ID: {account_id}")
    print(f"Region: {REGION}")
    
    return True

if __name__ == "__main__":
    initialize_riskuity_tenant()
