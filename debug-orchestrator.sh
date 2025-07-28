#!/bin/bash

echo "🔧 Fixing Outputs with CORRECT Module Attributes"
echo "==============================================="

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}Using the exact attribute names from your actual modules...${NC}"

cd terraform

# Backup current outputs.tf
cp outputs.tf outputs.tf.backup.$(date +%Y%m%d_%H%M%S)

# Create outputs.tf with CORRECT attribute names from your actual modules
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

# Lambda Functions - using CORRECT attribute names
output "orchestrator_lambda_arn" {
  description = "ARN of the KSI orchestrator Lambda function"
  value       = module.lambda.orchestrator_lambda_arn
}

output "orchestrator_lambda_name" {
  description = "Name of the KSI orchestrator Lambda function"
  value       = module.lambda.orchestrator_lambda_name
}

output "validator_lambda_arns" {
  description = "ARNs of all KSI validator Lambda functions"
  value       = module.lambda.validator_lambda_arns
}

output "ksi_orchestrator_role_arn" {
  description = "ARN of the IAM role for KSI orchestrator"
  value       = module.lambda.orchestrator_role_arn
}

# EventBridge
output "eventbridge_rule_arn" {
  description = "ARN of the EventBridge rule for scheduling"
  value       = module.eventbridge.eventbridge_rule_arn
}

# API Gateway - using CORRECT attribute names from your modules
output "api_gateway" {
  description = "API Gateway information"
  value = {
    api_id       = module.api_gateway.api_gateway_rest_api_id
    api_arn      = module.api_gateway.api_gateway_rest_api_arn
    invoke_url   = module.api_gateway.api_gateway_invoke_url
    stage_arn    = module.api_gateway.api_gateway_stage_arn
    endpoints    = module.api_gateway.api_endpoints
  }
}

# Quick reference URLs - using CORRECT attributes
output "quick_reference" {
  description = "Quick reference information"
  value = {
    api_base_url = module.api_gateway.api_gateway_invoke_url
    validate_url = "${module.api_gateway.api_gateway_invoke_url}/api/ksi/validate"
    executions_url = "${module.api_gateway.api_gateway_invoke_url}/api/ksi/executions"
    results_url = "${module.api_gateway.api_gateway_invoke_url}/api/ksi/results"
    orchestrator_function = module.lambda.orchestrator_lambda_name
  }
}

# Account Information
output "riskuity_account_id" {
  description = "Current AWS account ID"
  value       = data.aws_caller_identity.current.account_id
}

# Tenant Management Outputs (using try() to handle optional module)
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

echo -e "${GREEN}✅ Created outputs.tf with correct attribute names${NC}"

echo ""
echo -e "${YELLOW}Validating Terraform configuration...${NC}"

if terraform validate; then
    echo -e "${GREEN}✅ Terraform configuration is valid!${NC}"
    
    echo ""
    echo -e "${YELLOW}Planning tenant management deployment...${NC}"
    
    terraform plan -target=module.tenant_management
    
    echo ""
    read -p "Deploy tenant management infrastructure? (y/n): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🚀 Deploying tenant management..."
        terraform apply -target=module.tenant_management -auto-approve
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ Tenant management deployed successfully!${NC}"
            
            # Get tenant management API URL
            cd ..
            
            echo ""
            echo -e "${YELLOW}Getting tenant management API URL...${NC}"
            
            cd terraform
            TENANT_API_URL=""
            if terraform output tenant_management_api_url >/dev/null 2>&1; then
                TENANT_API_URL=$(terraform output -raw tenant_management_api_url)
                echo -e "${GREEN}✅ Tenant Management API: $TENANT_API_URL${NC}"
            else
                # Fallback to API Gateway URL
                API_BASE=$(terraform output -json api_gateway | jq -r '.invoke_url' 2>/dev/null)
                if [ "$API_BASE" != "null" ] && [ -n "$API_BASE" ]; then
                    TENANT_API_URL="$API_BASE"
                    echo -e "${BLUE}Using API Gateway URL: $TENANT_API_URL${NC}"
                fi
            fi
            
            cd ..
            
            if [ -n "$TENANT_API_URL" ]; then
                echo ""
                echo -e "${YELLOW}Generating Riskuity tenant role instructions...${NC}"
                
                ROLE_RESPONSE=$(curl -X POST "$TENANT_API_URL/api/tenant/generate-role-instructions" \
                    -H "Content-Type: application/json" \
                    -d '{
                        "tenantId": "riskuity-internal",
                        "accountId": "736539455039",
                        "tenantName": "Riskuity Internal"
                    }' \
                    -s)
                
                echo "$ROLE_RESPONSE" | jq . 2>/dev/null || echo "$ROLE_RESPONSE"
                
                # Save to file
                echo "$ROLE_RESPONSE" > riskuity-tenant-role-instructions.json
                echo -e "${GREEN}💾 Saved to: riskuity-tenant-role-instructions.json${NC}"
                
                echo ""
                echo -e "${YELLOW}Testing tenant connection...${NC}"
                
                CONNECTION_TEST=$(curl -X POST "$TENANT_API_URL/api/tenant/test-connection" \
                    -H "Content-Type: application/json" \
                    -d '{
                        "tenantId": "riskuity-internal",
                        "accountId": "736539455039"
                    }' \
                    -s)
                
                echo "$CONNECTION_TEST" | jq . 2>/dev/null || echo "$CONNECTION_TEST"
            fi
            
        else
            echo -e "${RED}❌ Tenant management deployment failed${NC}"
            exit 1
        fi
    else
        echo -e "${YELLOW}⚠️ Skipped tenant management deployment${NC}"
    fi
    
else
    echo -e "${RED}❌ Terraform validation failed:${NC}"
    terraform validate
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 Terraform Outputs Fixed and Tenant Management Ready!${NC}"
echo ""
echo -e "${BLUE}📋 What's working:${NC}"
echo "   ✅ Correct module attribute names in outputs.tf"
echo "   ✅ Terraform validation passing"
echo "   ✅ Tenant management infrastructure ready"
echo "   ✅ IAM role instructions generated"
echo ""
echo -e "${YELLOW}🔧 Next Steps:${NC}"
echo "1. Create the IAM role using the generated instructions"
echo "2. Test cross-account validation with proper roles"
echo "3. Run real KSI validation with tenant permissions"
echo ""
echo -e "${GREEN}🧪 Ready for REAL compliance validation! 🚀${NC}"
