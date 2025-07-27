#!/usr/bin/env python3
"""
Populate KSI DynamoDB Tables with FedRAMP 20X Validation Engine Data
This script loads your existing validation commands and definitions into DynamoDB
"""

import boto3
import json
from datetime import datetime, timezone

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-gov-west-1')

# Table names (update these to match your Terraform outputs)
KSI_DEFINITIONS_TABLE = "riskuity-ksi-validator-ksi-definitions-production"
TENANT_KSI_CONFIGURATIONS_TABLE = "riskuity-ksi-validator-tenant-ksi-configurations-production"

def load_ksi_definitions():
    """Load KSI definitions from your existing validation engine"""
    
    # Based on your cli_command_register.json structure
    ksi_definitions = {
        "KSI-CMT-01": {
            "ksi_id": "KSI-CMT-01",
            "version": "1.0",
            "category": "CMT",
            "title": "Configuration Management and Change Tracking",
            "description": "Validate that all system modifications are logged, tracked, and approved through automated infrastructure as code processes",
            "compliance_framework": "FedRAMP-20X",
            "control_references": ["CM-2", "CM-3", "CM-6", "AU-2"],
            "validation_commands": [
                {
                    "command": "aws cloudtrail describe-trails --output json",
                    "note": "Check CloudTrail log file validation for audit trail integrity and tamper-evident logging"
                },
                {
                    "command": "aws config describe-configuration-recorders --output json", 
                    "note": "Validate AWS Config for configuration change integrity tracking and compliance monitoring"
                },
                {
                    "command": "aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE UPDATE_ROLLBACK_COMPLETE --output json",
                    "note": "Check CloudFormation stacks for Infrastructure as Code deployment tracking"
                }
            ],
            "expected_results": {
                "cloudtrail_trails": {"min_count": 1, "encryption": "required"},
                "config_recorders": {"min_count": 1},
                "cloudformation_stacks": {"min_count": 1}
            },
            "pass_criteria": {
                "infrastructure_as_code": True,
                "change_tracking": True,
                "encryption_enabled": True,
                "logging_configured": True
            },
            "validator": "cmt",
            "last_updated": datetime.now(timezone.utc).isoformat()
        },
        
        "KSI-SVC-06": {
            "ksi_id": "KSI-SVC-06",
            "version": "1.0",
            "category": "SVC", 
            "title": "Automated Key Management Systems",
            "description": "Use automated key management systems to manage, protect, and regularly rotate digital keys and certificates",
            "compliance_framework": "FedRAMP-20X",
            "control_references": ["SC-12", "SC-13"],
            "validation_commands": [
                {
                    "command": "aws kms list-keys --output json",
                    "note": "Check KMS keys for automated key management and cryptographic service availability"
                },
                {
                    "command": "aws kms list-aliases --output json", 
                    "note": "Validate KMS key aliases and management for key governance and rotation tracking"
                }
            ],
            "validator": "svc",
            "last_updated": datetime.now(timezone.utc).isoformat()
        },
        
        "KSI-CNA-01": {
            "ksi_id": "KSI-CNA-01", 
            "version": "1.0",
            "category": "CNA",
            "title": "Network Architecture Security",
            "description": "Validate secure network architecture and configuration",
            "compliance_framework": "FedRAMP-20X",
            "control_references": ["SC-7", "AC-4"],
            "validation_commands": [
                {
                    "command": "aws ec2 describe-vpcs --output json",
                    "note": "Check VPC configurations for network segmentation and security"
                }
            ],
            "validator": "cna",
            "last_updated": datetime.now(timezone.utc).isoformat()
        },
        
        "KSI-IAM-01": {
            "ksi_id": "KSI-IAM-01",
            "version": "1.0", 
            "category": "IAM",
            "title": "Identity and Access Management",
            "description": "Validate comprehensive identity and access management controls",
            "compliance_framework": "FedRAMP-20X",
            "control_references": ["AC-2", "AC-3", "IA-2"],
            "validation_commands": [
                {
                    "command": "aws iam list-users --output json",
                    "note": "Check IAM users for proper identity management"
                }
            ],
            "validator": "iam",
            "last_updated": datetime.now(timezone.utc).isoformat()
        },
        
        "KSI-MLA-01": {
            "ksi_id": "KSI-MLA-01",
            "version": "1.0",
            "category": "MLA", 
            "title": "Monitoring, Logging & Alerting",
            "description": "Validate comprehensive monitoring, logging, and alerting capabilities",
            "compliance_framework": "FedRAMP-20X",
            "control_references": ["AU-2", "AU-3", "SI-4"],
            "validation_commands": [
                {
                    "command": "aws logs describe-log-groups --output json",
                    "note": "Check CloudWatch log groups for comprehensive logging coverage"
                }
            ],
            "validator": "mla",
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
    }
    
    return ksi_definitions

def populate_definitions_table():
    """Populate the KSI definitions DynamoDB table"""
    table = dynamodb.Table(KSI_DEFINITIONS_TABLE)
    definitions = load_ksi_definitions()
    
    print(f"Populating {KSI_DEFINITIONS_TABLE} with {len(definitions)} KSI definitions...")
    
    for ksi_id, definition in definitions.items():
        try:
            table.put_item(Item=definition)
            print(f"✅ Added {ksi_id}: {definition['title']}")
        except Exception as e:
            print(f"❌ Error adding {ksi_id}: {str(e)}")

def populate_tenant_configurations():
    """Populate tenant KSI configurations"""
    table = dynamodb.Table(TENANT_KSI_CONFIGURATIONS_TABLE)
    
    # Default tenant configuration - enable all KSIs
    tenant_configs = [
        {
            "tenant_id": "default", 
            "ksi_id": "KSI-CMT-01",
            "enabled": True,
            "priority": "high",
            "schedule": "daily",
            "last_updated": datetime.now(timezone.utc).isoformat()
        },
        {
            "tenant_id": "default",
            "ksi_id": "KSI-SVC-06",
            "enabled": True,
            "priority": "medium", 
            "schedule": "daily",
            "last_updated": datetime.now(timezone.utc).isoformat()
        },
        {
            "tenant_id": "default",
            "ksi_id": "KSI-CNA-01",
            "enabled": True,
            "priority": "high",
            "schedule": "daily", 
            "last_updated": datetime.now(timezone.utc).isoformat()
        },
        {
            "tenant_id": "default",
            "ksi_id": "KSI-IAM-01",
            "enabled": True,
            "priority": "critical",
            "schedule": "daily",
            "last_updated": datetime.now(timezone.utc).isoformat()
        },
        {
            "tenant_id": "default",
            "ksi_id": "KSI-MLA-01", 
            "enabled": True,
            "priority": "medium",
            "schedule": "daily",
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    print(f"Populating {TENANT_KSI_CONFIGURATIONS_TABLE} with {len(tenant_configs)} configurations...")
    
    for config in tenant_configs:
        try:
            table.put_item(Item=config)
            print(f"✅ Added config: {config['tenant_id']}/{config['ksi_id']}")
        except Exception as e:
            print(f"❌ Error adding config {config['ksi_id']}: {str(e)}")

def main():
    """Main function to populate all tables"""
    print("🚀 Populating KSI DynamoDB tables with validation engine data...")
    print("=" * 60)
    
    try:
        populate_definitions_table()
        print()
        populate_tenant_configurations()
        
        print("\n" + "=" * 60)
        print("🎉 Successfully populated KSI DynamoDB tables!")
        print("\n📋 Next steps:")
        print("1. Verify data: aws dynamodb scan --table-name", KSI_DEFINITIONS_TABLE, "--region us-gov-west-1")
        print("2. Test orchestrator: aws lambda invoke --function-name riskuity-ksi-validator-orchestrator-production output.json")
        print("3. View results: cat output.json")
        
    except Exception as e:
        print(f"\n❌ Error populating tables: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
