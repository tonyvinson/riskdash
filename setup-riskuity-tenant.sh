#!/bin/bash

echo "🏢 Setting Up Riskuity as Tenant Zero"
echo "====================================="

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}Creating Riskuity tenant configuration in DynamoDB...${NC}"

# Create Python script to set up Riskuity tenant
cat > setup_riskuity_tenant.py << 'EOF'
#!/usr/bin/env python3
"""
Setup Riskuity as Tenant Zero
"""

import boto3
import json
from datetime import datetime, timezone

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-gov-west-1')

# Table names
TENANT_KSI_CONFIGURATIONS_TABLE = "riskuity-ksi-validator-tenant-ksi-configurations-production"

def setup_riskuity_tenant():
    """Setup Riskuity as tenant zero with all KSIs enabled"""
    
    print("🏢 Setting up Riskuity as Tenant Zero...")
    
    table = dynamodb.Table(TENANT_KSI_CONFIGURATIONS_TABLE)
    
    # Riskuity tenant configurations for all KSIs
    riskuity_configs = [
        {
            "tenant_id": "riskuity-internal",
            "ksi_id": "KSI-CMT-01", 
            "enabled": True,
            "priority": "critical",
            "schedule": "daily",
            "tenant_name": "Riskuity Internal",
            "account_id": "736539455039",
            "environment": "production",
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "validation_frequency": "daily",
            "notification_enabled": True
        },
        {
            "tenant_id": "riskuity-internal",
            "ksi_id": "KSI-SVC-06",
            "enabled": True,
            "priority": "high",
            "schedule": "daily", 
            "tenant_name": "Riskuity Internal",
            "account_id": "736539455039",
            "environment": "production",
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "validation_frequency": "daily",
            "notification_enabled": True
        },
        {
            "tenant_id": "riskuity-internal",
            "ksi_id": "KSI-CNA-01",
            "enabled": True,
            "priority": "high",
            "schedule": "daily",
            "tenant_name": "Riskuity Internal", 
            "account_id": "736539455039",
            "environment": "production",
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "validation_frequency": "daily",
            "notification_enabled": True
        },
        {
            "tenant_id": "riskuity-internal",
            "ksi_id": "KSI-IAM-01",
            "enabled": True,
            "priority": "critical",
            "schedule": "daily",
            "tenant_name": "Riskuity Internal",
            "account_id": "736539455039", 
            "environment": "production",
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "validation_frequency": "daily",
            "notification_enabled": True
        },
        {
            "tenant_id": "riskuity-internal",
            "ksi_id": "KSI-MLA-01",
            "enabled": True,
            "priority": "high",
            "schedule": "daily",
            "tenant_name": "Riskuity Internal",
            "account_id": "736539455039",
            "environment": "production", 
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "validation_frequency": "daily",
            "notification_enabled": True
        }
    ]
    
    print(f"📝 Adding {len(riskuity_configs)} KSI configurations for Riskuity...")
    
    for config in riskuity_configs:
        try:
            table.put_item(Item=config)
            print(f"✅ Added Riskuity config: {config['ksi_id']}")
        except Exception as e:
            print(f"❌ Error adding config {config['ksi_id']}: {str(e)}")
    
    print("\n🎉 Riskuity tenant setup complete!")
    
    # Verify the setup
    print("\n🔍 Verifying Riskuity tenant configuration...")
    
    try:
        response = table.scan(
            FilterExpression=boto3.dynamodb.conditions.Attr('tenant_id').eq('riskuity-internal')
        )
        
        configs = response.get('Items', [])
        print(f"✅ Found {len(configs)} KSI configurations for Riskuity:")
        
        for config in configs:
            print(f"   • {config['ksi_id']} - {config['priority']} priority")
            
    except Exception as e:
        print(f"❌ Error verifying setup: {str(e)}")

def main():
    print("🚀 Setting up Riskuity as Tenant Zero...")
    print("=" * 50)
    
    try:
        setup_riskuity_tenant()
        
        print("\n" + "=" * 50)
        print("🎉 SUCCESS! Riskuity is now configured as Tenant Zero")
        print("\n📋 Next steps:")
        print("1. Test validation: curl -X POST 'API_URL/api/ksi/validate' -d '{\"tenant_id\": \"riskuity-internal\"}'")
        print("2. Check results: curl 'API_URL/api/ksi/results?tenant_id=riskuity-internal'")
        print("3. Monitor executions: curl 'API_URL/api/ksi/executions?tenant_id=riskuity-internal'")
        
    except Exception as e:
        print(f"\n❌ Error setting up Riskuity tenant: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
EOF

echo -e "${GREEN}✅ Created Riskuity tenant setup script${NC}"

echo ""
echo -e "${YELLOW}Running tenant setup...${NC}"

# Run the setup script
python3 setup_riskuity_tenant.py

echo ""
echo -e "${BLUE}🧪 Testing Riskuity tenant validation...${NC}"

# Test with Riskuity tenant
echo "📋 Testing validation for Riskuity tenant..."

curl -X POST "https://d5804hjt80.execute-api.us-gov-west-1.amazonaws.com/production/api/ksi/validate" \
  -H "Content-Type: application/json" \
  -d '{"tenant_id": "riskuity-internal"}' \
  -s | jq .

echo ""
echo -e "${GREEN}🎉 Riskuity Tenant Setup Complete!${NC}"
echo ""
echo -e "${BLUE}📋 What was created:${NC}"
echo "   ✅ Riskuity tenant: riskuity-internal"
echo "   ✅ Account ID: 736539455039"
echo "   ✅ All 5 KSIs enabled: CMT, SVC, CNA, IAM, MLA"
echo "   ✅ Critical/High priority validation"
echo "   ✅ Daily validation schedule"
echo ""
echo -e "${YELLOW}🧪 Test commands:${NC}"
echo "# Test Riskuity validation:"
echo "curl -X POST 'https://d5804hjt80.execute-api.us-gov-west-1.amazonaws.com/production/api/ksi/validate' \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"tenant_id\": \"riskuity-internal\"}'"
echo ""
echo "# Check Riskuity results:"
echo "curl 'https://d5804hjt80.execute-api.us-gov-west-1.amazonaws.com/production/api/ksi/results?tenant_id=riskuity-internal'"
