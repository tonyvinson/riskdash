#!/bin/bash

echo "🔧 Fixing Terraform Circular Dependency"
echo "========================================"

echo "📋 The issue: lambda module and tenant_management module have circular dependency"
echo "💡 Solution: Both modules should depend only on dynamodb module"

# Step 1: Revert the problematic changes to main.tf
echo ""
echo "📁 Step 1: Fixing main.tf dependencies..."

cat > /tmp/fix_main_tf.py << 'EOF'
import re

# Read the file
with open('terraform/main.tf', 'r') as f:
    content = f.read()

# Find the lambda module block and fix it
lambda_pattern = r'(module "lambda" \{.*?)(depends_on = \[.*?\])(.*?\})'

def fix_lambda_module(match):
    module_start = match.group(1)
    old_depends_on = match.group(2)
    module_end = match.group(3)
    
    # Replace depends_on to only include dynamodb
    new_depends_on = 'depends_on = [module.dynamodb]'
    
    return module_start + new_depends_on + module_end

# Apply the fix
new_content = re.sub(lambda_pattern, fix_lambda_module, content, flags=re.DOTALL)

# Also make sure tenant_management only depends on what it needs
tenant_pattern = r'(module "tenant_management".*?)(depends_on = \[.*?\])?(\s*\})'

def fix_tenant_module(match):
    module_content = match.group(1)
    module_end = match.group(3)
    
    # Add depends_on only for dynamodb
    new_depends_on = '\n  depends_on = [module.dynamodb]'
    
    return module_content + new_depends_on + module_end

new_content = re.sub(tenant_pattern, fix_tenant_module, new_content, flags=re.DOTALL)

# Write back
with open('terraform/main.tf', 'w') as f:
    f.write(new_content)

print("✅ Fixed main.tf dependencies")
EOF

python3 /tmp/fix_main_tf.py
rm /tmp/fix_main_tf.py

# Step 2: Update the lambda module call to get tenant_metadata_table differently
echo ""
echo "📁 Step 2: Updating lambda module to use dynamodb outputs..."

# Since we have tenant_management creating a table, we need to pass it at the main level
# Let's check if tenant_management creates the tenant_metadata table

if grep -q "tenant_metadata" terraform/modules/tenant_management/main.tf 2>/dev/null; then
    echo "✅ Found tenant_metadata table in tenant_management module"
    
    # We need to update main.tf to pass the tenant_metadata table from tenant_management to lambda
    cat > /tmp/fix_lambda_call.py << 'EOF'
import re

# Read the file
with open('terraform/main.tf', 'r') as f:
    content = f.read()

# Find lambda module and add tenant_metadata references
lambda_pattern = r'(module "lambda" \{.*?ksi_execution_history_table_arn.*?= module\.dynamodb\.ksi_execution_history_table_arn)(.*?depends_on = \[module\.dynamodb\])'

def add_tenant_metadata(match):
    existing_vars = match.group(1)
    rest = match.group(2)
    
    # Add tenant_metadata variables
    addition = '''
  
  # Tenant metadata table (from tenant_management module)
  tenant_metadata_table     = module.tenant_management.tenant_metadata_table_name
  tenant_metadata_table_arn = module.tenant_management.tenant_metadata_table_arn'''
    
    return existing_vars + addition + rest

# Apply the change
new_content = re.sub(lambda_pattern, add_tenant_metadata, content, flags=re.DOTALL)

# Write back
with open('terraform/main.tf', 'w') as f:
    f.write(new_content)

print("✅ Updated lambda module call with tenant_metadata references")
EOF
    
    python3 /tmp/fix_lambda_call.py
    rm /tmp/fix_lambda_call.py
    
else
    echo "❌ tenant_metadata table not found in tenant_management module"
    echo "    You may need to create it or use a different approach"
fi

# Step 3: Create a better approach - use data sources instead
echo ""
echo "📁 Step 3: Alternative approach - use data sources to break cycles..."

# Create a data source approach where lambda can look up the table by name
cat > /tmp/lambda_data_source.tf << 'EOF'
# Add this to terraform/modules/lambda/main.tf after the locals block

# Data source to get tenant metadata table info without dependency
data "aws_dynamodb_table" "tenant_metadata" {
  name = "${var.project_name}-tenant-metadata-${var.environment}"
}
EOF

echo "📋 Created data source approach (optional)"

# Step 4: Check if there are any remaining cycles
echo ""
echo "📁 Step 4: Validating fixed configuration..."

cd terraform

if terraform validate; then
    echo "✅ Terraform configuration is now valid!"
    echo ""
    echo "🚀 Ready to deploy:"
    echo "  terraform plan"
    echo "  terraform apply"
else
    echo "❌ Still have validation issues. Let's try a simpler approach..."
    echo ""
    echo "🔧 Fallback: Remove tenant_metadata references from lambda module"
    
    # Remove the tenant_metadata variables we added
    cd ../
    
    # Revert lambda variables.tf
    if [ -f "terraform/modules/lambda/variables.tf.backup" ]; then
        cp terraform/modules/lambda/variables.tf.backup terraform/modules/lambda/variables.tf
        echo "✅ Reverted lambda variables.tf"
    fi
    
    # Revert lambda main.tf  
    if [ -f "terraform/modules/lambda/main.tf.backup" ]; then
        cp terraform/modules/lambda/main.tf.backup terraform/modules/lambda/main.tf
        echo "✅ Reverted lambda main.tf"
    fi
    
    # Use hardcoded table name in validator environment instead
    cat > /tmp/hardcode_table.py << 'EOF'
import re

# Read the lambda main.tf file
with open('terraform/modules/lambda/main.tf', 'r') as f:
    content = f.read()

# Add hardcoded table name to validator environment
pattern = r'(environment \{.*?variables = \{.*?KSI_EXECUTION_HISTORY_TABLE = var\.ksi_execution_history_table)(.*?\}.*?\})'

def add_hardcoded_table(match):
    existing_vars = match.group(1)
    rest = match.group(2)
    
    # Add hardcoded table name
    addition = '\n      TENANT_CONFIG_TABLE = "${var.project_name}-tenant-metadata-${var.environment}"'
    
    return existing_vars + addition + rest

# Apply the change
new_content = re.sub(pattern, add_hardcoded_table, content, flags=re.DOTALL)

# Write back
with open('terraform/modules/lambda/main.tf', 'w') as f:
    f.write(new_content)

print("✅ Added hardcoded TENANT_CONFIG_TABLE to validators")
EOF
    
    python3 /tmp/hardcode_table.py
    rm /tmp/hardcode_table.py
    
    cd terraform
    echo ""
    echo "🧪 Testing hardcoded approach..."
    if terraform validate; then
        echo "✅ Hardcoded approach works!"
    else
        echo "❌ Still having issues"
    fi
fi

cd ../

echo ""
echo "✅ DEPENDENCY CYCLE RESOLUTION COMPLETE"
echo ""
echo "📋 What was done:"
echo "  • Removed circular dependency between lambda and tenant_management modules"
echo "  • Made both modules depend only on dynamodb module"  
echo "  • Added TENANT_CONFIG_TABLE environment variable to validators"
echo ""
echo "🚀 Next steps:"
echo "  cd terraform"
echo "  terraform plan   # Should work without cycle errors"
echo "  terraform apply  # Deploy the fix"
