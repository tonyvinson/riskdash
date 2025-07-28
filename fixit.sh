#!/bin/bash

echo "🔧 Terraform Fix: Add tenant-metadata table permissions to validator role"
echo "========================================================================"

# Step 1: Add variables to lambda module (if not already added)
echo "📁 Step 1: Adding tenant_metadata variables to lambda module..."

if ! grep -q "tenant_metadata_table" terraform/modules/lambda/variables.tf; then
    cat >> terraform/modules/lambda/variables.tf << 'EOF'

variable "tenant_metadata_table" {
  description = "Name of tenant metadata table"
  type        = string
}

variable "tenant_metadata_table_arn" {
  description = "ARN of tenant metadata table"
  type        = string
}
EOF
    echo "✅ Added tenant_metadata variables to lambda module"
else
    echo "✅ tenant_metadata variables already exist in lambda module"
fi

# Step 2: Update DynamoDB policy in lambda module
echo ""
echo "📁 Step 2: Updating DynamoDB policy in lambda module..."

# Create backup
cp terraform/modules/lambda/main.tf terraform/modules/lambda/main.tf.backup.$(date +%Y%m%d_%H%M%S)

# Use Python to properly update the DynamoDB policy
cat > /tmp/update_dynamodb_policy.py << 'EOF'
import re

# Read the lambda main.tf file
with open('terraform/modules/lambda/main.tf', 'r') as f:
    content = f.read()

# Find the DynamoDB policy and add tenant_metadata_table_arn to resources
# Look for the Resource array in the DynamoDB policy
policy_pattern = r'(resource "aws_iam_policy" "ksi_dynamodb_policy".*?Resource = \[)(.*?)(\s+\]\s+\})'

def update_policy_resources(match):
    policy_start = match.group(1)
    resources = match.group(2)
    policy_end = match.group(3)
    
    # Check if tenant_metadata_table_arn is already included
    if 'tenant_metadata_table_arn' in resources:
        print("✅ tenant_metadata_table_arn already in DynamoDB policy")
        return match.group(0)
    
    # Add tenant_metadata_table_arn and its index to the resources
    # Insert before the closing bracket
    new_resources = resources.rstrip() + ',\n          var.tenant_metadata_table_arn,\n          "${var.tenant_metadata_table_arn}/index/*"'
    
    print("✅ Added tenant_metadata_table_arn to DynamoDB policy")
    return policy_start + new_resources + policy_end

# Apply the update
new_content = re.sub(policy_pattern, update_policy_resources, content, flags=re.DOTALL)

# Write back to file
with open('terraform/modules/lambda/main.tf', 'w') as f:
    f.write(new_content)
EOF

python3 /tmp/update_dynamodb_policy.py
rm /tmp/update_dynamodb_policy.py

# Step 3: Update main.tf to pass tenant_metadata variables (if not already done)
echo ""
echo "📁 Step 3: Updating main.tf to pass tenant_metadata variables..."

# Check if already added
if grep -q "tenant_metadata_table.*=.*module.tenant_management" terraform/main.tf; then
    echo "✅ tenant_metadata variables already passed to lambda module"
else
    # Use Python to update main.tf lambda module call
    cat > /tmp/update_main_tf.py << 'EOF'
import re

# Read main.tf
with open('terraform/main.tf', 'r') as f:
    content = f.read()

# Find the lambda module block and add tenant_metadata variables
module_pattern = r'(module "lambda" \{.*?ksi_execution_history_table_arn\s*=\s*module\.dynamodb\.ksi_execution_history_table_arn)(.*?depends_on = \[.*?\])'

def add_tenant_metadata_vars(match):
    existing_vars = match.group(1)
    rest = match.group(2)
    
    # Add tenant_metadata variables
    addition = '''
  
  # Tenant metadata table access
  tenant_metadata_table     = module.tenant_management.tenant_metadata_table_name
  tenant_metadata_table_arn = module.tenant_management.tenant_metadata_table_arn'''
    
    # Also update depends_on to include tenant_management if not already there
    new_rest = rest.replace('[module.dynamodb]', '[module.dynamodb, module.tenant_management]')
    
    return existing_vars + addition + new_rest

# Apply the change
new_content = re.sub(module_pattern, add_tenant_metadata_vars, content, flags=re.DOTALL)

# Write back
with open('terraform/main.tf', 'w') as f:
    f.write(new_content)

print("✅ Updated main.tf lambda module call")
EOF

    python3 /tmp/update_main_tf.py
    rm /tmp/update_main_tf.py
fi

# Step 4: Validate Terraform configuration
echo ""
echo "📁 Step 4: Validating Terraform configuration..."

cd terraform
if terraform validate; then
    echo "✅ Terraform configuration is valid!"
    
    echo ""
    echo "📋 Changes made:"
    echo "  ✅ Added tenant_metadata variables to lambda module"
    echo "  ✅ Updated DynamoDB policy to include tenant_metadata table"
    echo "  ✅ Updated main.tf to pass tenant_metadata variables"
    echo ""
    echo "🚀 Ready to deploy:"
    echo "  terraform plan   # Review the IAM policy changes"
    echo "  terraform apply  # Deploy the permission fix"
    echo ""
    echo "✅ This will give validators access to tenant-metadata table!"
    
else
    echo "❌ Terraform validation failed. Please check the configuration."
    terraform validate
fi

cd ../

echo ""
echo "🧪 After terraform apply, test with:"
echo "  curl -X POST 'https://d5804hjt80.execute-api.us-gov-west-1.amazonaws.com/production/api/ksi/validate' \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"tenant_id\": \"real-test\"}'"
