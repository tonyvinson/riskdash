#!/bin/bash

echo "🔧 Simple Terraform Fix - Manual Cleanup"
echo "========================================"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}Manually fixing Terraform files...${NC}"

cd terraform

echo ""
echo -e "${YELLOW}Step 1: Backup and fix outputs.tf${NC}"

# Backup current outputs.tf
cp outputs.tf outputs.tf.backup.$(date +%Y%m%d_%H%M%S)

# Create clean outputs.tf
cat > outputs.tf << 'EOF'
# DynamoDB Tables
output "ksi_definitions_table_name" {
  description = "Name of the KSI definitions DynamoDB table"
  value       = module.dynamodb.ksi_definitions_table_name
}

output "tenant_ksi_configurations_table_name" {
  description = "Name of the tenant KSI configurations DynamoDB table"
  value       = module.dynamodb.tenant_ksi_configurations_table_name
}

output "ksi_execution_history_table_name" {
  description = "Name of the KSI execution history DynamoDB table"
  value       = module.dynamodb.ksi_execution_history_table_name
}

# Lambda Functions
output "orchestrator_lambda_arn" {
  description = "ARN of the KSI orchestrator Lambda function"
  value       = module.lambda.orchestrator_lambda_arn
}

output "validator_lambda_arns" {
  description = "ARNs of all KSI validator Lambda functions"
  value       = module.lambda.validator_lambda_arns
}

# API Gateway
output "api_gateway" {
  description = "API Gateway information"
  value = {
    id         = module.api_gateway.api_gateway_id
    invoke_url = module.api_gateway.api_gateway_invoke_url
    endpoints = {
      validate_url   = module.api_gateway.validate_endpoint_url
      executions_url = module.api_gateway.executions_endpoint_url
      results_url    = module.api_gateway.results_endpoint_url
    }
  }
}

# EventBridge
output "eventbridge_rule_arn" {
  description = "ARN of the EventBridge rule for scheduled validations"
  value       = module.eventbridge.eventbridge_rule_arn
}

# Quick Reference
output "quick_reference" {
  description = "Quick reference for key endpoints and functions"
  value = {
    api_base_url = module.api_gateway.api_gateway_invoke_url
    validate_url = module.api_gateway.validate_endpoint_url
    executions_url = module.api_gateway.executions_endpoint_url
    results_url = module.api_gateway.results_endpoint_url
    orchestrator_function = module.lambda.orchestrator_lambda_function_name
  }
}

# Account Information
output "riskuity_account_id" {
  description = "Current AWS account ID"
  value       = data.aws_caller_identity.current.account_id
}

# Tenant Management Outputs (if module exists)
output "tenant_management_api_url" {
  description = "Tenant Management API Gateway URL"
  value       = try(module.tenant_management.api_gateway_url, "Not deployed")
}

output "tenant_onboarding_instructions" {
  description = "Instructions for tenant onboarding"
  value = try({
    api_url = module.tenant_management.api_gateway_url
    endpoints = {
      generate_role_instructions = "${module.tenant_management.api_gateway_url}/api/tenant/generate-role-instructions"
      test_connection = "${module.tenant_management.api_gateway_url}/api/tenant/test-connection"
      onboard = "${module.tenant_management.api_gateway_url}/api/tenant/onboard"
      list = "${module.tenant_management.api_gateway_url}/api/tenant/list"
    }
  }, "Tenant management not deployed")
}

output "cross_account_validator_function_name" {
  description = "Cross-account validator Lambda function name"
  value       = try(module.tenant_management.cross_account_validator_function_name, "Not deployed")
}
EOF

echo -e "${GREEN}✅ Fixed outputs.tf${NC}"

echo ""
echo -e "${YELLOW}Step 2: Check and fix main.tf${NC}"

# Check if main.tf has duplicate tenant_management modules
TENANT_COUNT=$(grep -c "module \"tenant_management\"" main.tf)

if [ "$TENANT_COUNT" -gt 1 ]; then
    echo "📝 Fixing duplicate tenant_management modules in main.tf..."
    
    # Backup main.tf
    cp main.tf main.tf.backup.$(date +%Y%m%d_%H%M%S)
    
    # Remove all tenant_management modules and add one clean one at the end
    sed '/module "tenant_management"/,/^}/d' main.tf > main.tf.temp
    
    # Add clean tenant management module
    cat >> main.tf.temp << 'EOF'

# Tenant Management Module
module "tenant_management" {
  source = "./modules/tenant_management"
  
  environment  = var.environment
  project_name = var.project_name
  
  # DynamoDB table references
  ksi_definitions_table = module.dynamodb.ksi_definitions_table_name
  tenant_ksi_configurations_table = module.dynamodb.tenant_ksi_configurations_table_name
  ksi_execution_history_table = module.dynamodb.ksi_execution_history_table_name
  
  depends_on = [module.dynamodb]
}
EOF
    
    mv main.tf.temp main.tf
    echo -e "${GREEN}✅ Fixed duplicate tenant_management modules${NC}"
else
    echo -e "${GREEN}✅ No duplicate modules found${NC}"
fi

echo ""
echo -e "${YELLOW}Step 3: Fix API Gateway tenant variables${NC}"

# Make sure API Gateway has the right tenant variables
if grep -q "tenant_onboarding_lambda_function_name = null" main.tf; then
    sed -i.bak 's/tenant_onboarding_lambda_function_name = null/tenant_onboarding_lambda_function_name = try(module.tenant_management.tenant_onboarding_api_function_name, null)/' main.tf
    sed -i.bak 's/tenant_onboarding_lambda_invoke_arn    = null/tenant_onboarding_lambda_invoke_arn    = try(module.tenant_management.tenant_onboarding_api_function_arn, null)/' main.tf
    echo -e "${GREEN}✅ Fixed API Gateway tenant variables${NC}"
fi

echo ""
echo -e "${YELLOW}Step 4: Validate Terraform configuration${NC}"

echo "🔍 Validating Terraform configuration..."
if terraform validate; then
    echo -e "${GREEN}✅ Terraform configuration is valid${NC}"
else
    echo -e "${RED}❌ Terraform validation still failing${NC}"
    terraform validate
    exit 1
fi

echo ""
echo -e "${YELLOW}Step 5: Deploy tenant management${NC}"

echo "📋 Planning tenant management deployment..."
terraform plan -target=module.tenant_management

echo ""
read -p "Deploy tenant management infrastructure? (y/n): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 Deploying tenant management..."
    terraform apply -target=module.tenant_management -auto-approve
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Tenant management deployed successfully!${NC}"
    else
        echo -e "${RED}❌ Tenant management deployment failed${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️ Skipped tenant management deployment${NC}"
    exit 0
fi

echo ""
echo -e "${YELLOW}Step 6: Generate role instructions${NC}"

cd ..

# Get tenant management API URL
cd terraform
TENANT_API_URL=""
if terraform output tenant_management_api_url >/dev/null 2>&1; then
    TENANT_API_URL=$(terraform output -raw tenant_management_api_url)
    echo -e "${GREEN}✅ Tenant Management API: $TENANT_API_URL${NC}"
else
    # Try getting from API Gateway
    API_BASE=$(terraform output -json api_gateway | jq -r '.invoke_url' 2>/dev/null)
    if [ "$API_BASE" != "null" ] && [ -n "$API_BASE" ]; then
        TENANT_API_URL="$API_BASE"
        echo -e "${BLUE}Using API Gateway URL: $TENANT_API_URL${NC}"
    fi
fi

cd ..

if [ -n "$TENANT_API_URL" ]; then
    echo "📋 Generating Riskuity tenant role instructions..."
    
    ROLE_RESPONSE=$(curl -X POST "$TENANT_API_URL/api/tenant/generate-role-instructions" \
        -H "Content-Type: application/json" \
        -d '{
            "tenantId": "riskuity-internal",
            "accountId": "736539455039",
            "tenantName": "Riskuity Internal"
        }' \
        -s)
    
    echo "$ROLE_RESPONSE" | jq . || echo "$ROLE_RESPONSE"
    
    # Save to file
    echo "$ROLE_RESPONSE" > riskuity-tenant-role-instructions.json
    echo -e "${GREEN}💾 Saved to: riskuity-tenant-role-instructions.json${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Tenant Management Ready!${NC}"
echo ""
echo -e "${BLUE}📋 What's ready:${NC}"
echo "   ✅ Clean Terraform configuration"
echo "   ✅ Tenant management infrastructure deployed"
echo "   ✅ IAM role instructions generated"
echo ""
echo -e "${YELLOW}🔧 Next: Create the IAM role and test real validation!${NC}"
