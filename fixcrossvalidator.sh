#!/bin/bash

echo "🎯 Precise Cross-Account Validator Fix"
echo "====================================="

FILE_PATH="lambdas/cross_account_validator/cross_account_ksi_validator.py"

if [ ! -f "$FILE_PATH" ]; then
    echo "❌ File not found: $FILE_PATH"
    exit 1
fi

echo "📄 Processing: $FILE_PATH"

# Create backup
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_PATH="${FILE_PATH}.backup.${TIMESTAMP}"
cp "$FILE_PATH" "$BACKUP_PATH"
echo "💾 Backup created: $BACKUP_PATH"

# Create Python script to make precise fixes
cat > precise_fix.py << 'EOF'
import re

# Read the file
with open('lambdas/cross_account_validator/cross_account_ksi_validator.py', 'r') as f:
    content = f.read()

original_content = content

# Fix 1: Find and fix tenant_config_table.get_item (the problematic one)
# This pattern looks for config_response = self.tenant_config_table.get_item followed by accessing config_response.get('Item')
pattern1 = r'(config_response = self\.tenant_config_table\.get_item\(Key=\{[\'"]tenant_id[\'"]:\s*tenant_id\}\))\s*(\n\s*tenant_configs = config_response\.get\([\'"]Item[\'"], \[\]\))'

if re.search(pattern1, content):
    replacement1 = '''config_response = self.tenant_config_table.query(
            KeyConditionExpression='tenant_id = :tid',
            ExpressionAttributeValues={':tid': tenant_id}
        )
        tenant_configs = config_response.get('Items', [])'''
    
    content = re.sub(pattern1, replacement1, content)
    print("✅ Fixed tenant_config_table.get_item call")

# Fix 2: Look for any other tenant_config_table.get_item patterns
pattern2 = r'self\.tenant_config_table\.get_item\(Key=\{[\'"]tenant_id[\'"]:\s*tenant_id\}\)'

if re.search(pattern2, content):
    replacement2 = '''self.tenant_config_table.query(
            KeyConditionExpression='tenant_id = :tid',
            ExpressionAttributeValues={':tid': tenant_id}
        )'''
    
    content = re.sub(pattern2, replacement2, content)
    print("✅ Fixed additional tenant_config_table.get_item calls")

# Fix 3: Update any references to .get('Item') that should now be .get('Items')
# Look for tenant_configs = response.get('Item', []) after our changes
pattern3 = r'(tenant_configs = .*?\.get\([\'"]Item[\'"], \[\]\))'
if re.search(pattern3, content):
    content = re.sub(r'\.get\([\'"]Item[\'"], \[\]\)', ".get('Items', [])", content)
    print("✅ Fixed Item -> Items references")

# Check if we made any changes
if content != original_content:
    # Write the fixed content
    with open('lambdas/cross_account_validator/cross_account_ksi_validator.py', 'w') as f:
        f.write(content)
    print("📝 File updated with fixes")
else:
    print("ℹ️ No changes needed - file appears to be correct")

# Final verification - check for remaining issues
remaining_issues = []
if re.search(r'tenant_config_table\.get_item.*tenant_id.*tenant_id', content):
    remaining_issues.append("tenant_config_table.get_item with single tenant_id still found")

if remaining_issues:
    print("⚠️ Remaining issues found:")
    for issue in remaining_issues:
        print(f"   - {issue}")
else:
    print("✅ No remaining DynamoDB key issues detected")

EOF

# Run the precise fix
python3 precise_fix.py

# Clean up
rm precise_fix.py

echo ""
echo "🔍 Final verification..."

# Check for the specific problematic pattern
if grep -q "tenant_config_table\.get_item.*tenant_id.*tenant_id" "$FILE_PATH"; then
    echo "⚠️ tenant_config_table.get_item issue still exists"
    echo "📋 Let's see what's there:"
    grep -n "tenant_config_table\.get_item" "$FILE_PATH" || echo "No tenant_config_table.get_item found"
    grep -n "get_item.*tenant_id.*tenant_id" "$FILE_PATH" || echo "No get_item with tenant_id pattern found"
else
    echo "✅ No tenant_config_table.get_item issues found!"
fi

echo ""
echo "🎉 Precise cross-account fix completed!"
