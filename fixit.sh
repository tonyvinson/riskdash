#!/bin/bash

# Master Backend Fix Script
# Fixes all DynamoDB composite key issues across the entire project

set -e  # Exit on any error

echo "🚀 MASTER BACKEND KEY FIX SCRIPT"
echo "================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -d "lambdas" ] || [ ! -d "terraform" ]; then
    echo -e "${RED}❌ Error: Please run this script from the project root directory${NC}"
    echo "   (Should contain 'lambdas' and 'terraform' directories)"
    exit 1
fi

echo "📋 This script will:"
echo "   1. Run verification scan to identify issues"
echo "   2. Fix all validator handler files"
echo "   3. Fix orchestrator files"  
echo "   4. Run final verification"
echo "   5. Provide deployment instructions"
echo ""

read -p "🤔 Continue with the fix process? (y/N): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}❌ Operation cancelled${NC}"
    exit 1
fi

echo ""
echo "🔍 STEP 1: Initial Verification Scan"
echo "======================================"

# Create the verification script if it doesn't exist
cat > fix_verification.py << 'EOF'
#!/usr/bin/env python3
"""
Key Fix Verification Script
"""

import os
import re
from pathlib import Path

def check_file_for_issues(file_path):
    """Check a single file for DynamoDB key issues"""
    issues = []
    suggestions = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for old get_item pattern with single key
        if re.search(r'table\.get_item\(Key=\{[\'"]tenant_id[\'"]:\s*tenant_id\}\)', content):
            issues.append("❌ Found old get_item() with single tenant_id key")
        
        # Check for proper query usage
        if 'table.query(' in content and 'KeyConditionExpression' in content:
            suggestions.append("✅ Found proper query() usage")
        
        return issues, suggestions
        
    except Exception as e:
        return [f"❌ Error reading file: {str(e)}"], []

def main():
    files_with_issues = 0
    total_issues = 0
    
    for file_path in Path('.').glob('**/*.py'):
        if file_path.is_file():
            issues, suggestions = check_file_for_issues(str(file_path))
            
            if issues:
                files_with_issues += 1
                total_issues += len(issues)
                print(f"📄 {file_path}")
                for issue in issues:
                    print(f"   {issue}")
    
    print(f"\n📊 Found {total_issues} issues in {files_with_issues} files")
    return total_issues

if __name__ == "__main__":
    main()
EOF

python3 fix_verification.py
verification_result=$?

echo ""
echo "🔧 STEP 2: Fix Validator Handler Files"
echo "======================================"

# Create validator fix script
cat > fix_validators.py << 'EOF'
#!/usr/bin/env python3
"""
Backend Key Fix Script for Validators
"""

import os
import re
import shutil
from pathlib import Path
from datetime import datetime

FIXED_FUNCTION = '''def get_tenant_configuration(tenant_id):
    """Get tenant configuration from DynamoDB - FIXED VERSION"""
    try:
        table_name = os.environ.get('TENANT_CONFIG_TABLE', 'riskuity-ksi-validator-tenant-configurations-production')
        table = default_dynamodb.Table(table_name)
        
        # ✅ FIXED: Use query() instead of get_item() for composite key table
        response = table.query(
            KeyConditionExpression='tenant_id = :tid',
            ExpressionAttributeValues={':tid': tenant_id}
        )
        
        configurations = response.get('Items', [])
        
        if configurations:
            return {
                'tenant_id': tenant_id,
                'configurations': configurations,
                'has_config': True
            }
        else:
            print(f"⚠️ No configuration found for tenant: {tenant_id}")
            return None
            
    except Exception as e:
        print(f"❌ Error getting tenant configuration: {str(e)}")
        return None'''

def find_validator_files():
    validator_files = []
    for root, dirs, files in os.walk('.'):
        if 'handler.py' in files and 'validators' in root:
            handler_path = os.path.join(root, 'handler.py')
            if os.path.exists(handler_path):
                validator_files.append(handler_path)
    return validator_files

def fix_file(file_path):
    # Create backup
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{file_path}.backup.{timestamp}"
    shutil.copy2(file_path, backup_path)
    
    # Read and fix content
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace the function
    pattern = r'def get_tenant_configuration\(tenant_id\):.*?(?=\n\ndef|\nclass|\nif __name__|\Z)'
    
    if re.search(pattern, content, re.DOTALL):
        new_content = re.sub(pattern, FIXED_FUNCTION, content, flags=re.DOTALL)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✅ Fixed: {file_path}")
        return True
    else:
        os.remove(backup_path)  # No changes needed
        print(f"ℹ️ No changes needed: {file_path}")
        return False

def main():
    validator_files = find_validator_files()
    print(f"Found {len(validator_files)} validator files")
    
    fixed_count = 0
    for file_path in validator_files:
        if fix_file(file_path):
            fixed_count += 1
    
    print(f"Fixed {fixed_count} files")

if __name__ == "__main__":
    main()
EOF

python3 fix_validators.py

echo ""
echo "🔧 STEP 3: Fix Orchestrator Files"  
echo "=================================="

# Create orchestrator fix script
cat > fix_orchestrator.py << 'EOF'
#!/usr/bin/env python3
"""
Orchestrator Fix Script
"""

import os
import re
import shutil
from pathlib import Path
from datetime import datetime

FIXED_ORCHESTRATOR_FUNCTION = '''def get_tenant_configurations(tenant_id: str) -> List[Dict]:
    """Retrieve KSI configurations for a specific tenant - FIXED VERSION"""
    table = dynamodb.Table(TENANT_KSI_CONFIGURATIONS_TABLE)
    
    try:
        response = table.query(
            KeyConditionExpression='tenant_id = :tid',
            ExpressionAttributeValues={':tid': tenant_id}
        )
        return response.get('Items', [])
    except Exception as e:
        logger.error(f"Error querying tenant configurations for {tenant_id}: {str(e)}")
        return []'''

def find_orchestrator_files():
    files = []
    for root, dirs, file_list in os.walk('.'):
        for file in file_list:
            if 'orchestrator' in file.lower() and file.endswith('.py'):
                files.append(os.path.join(root, file))
    return files

def fix_orchestrator_file(file_path):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{file_path}.backup.{timestamp}"
    shutil.copy2(file_path, backup_path)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix the function
    pattern = r'def get_tenant_configurations\(tenant_id: str\) -> List\[Dict\]:.*?(?=\n\ndef|\nclass|\nif __name__|\Z)'
    
    if re.search(pattern, content, re.DOTALL):
        new_content = re.sub(pattern, FIXED_ORCHESTRATOR_FUNCTION, content, flags=re.DOTALL)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✅ Fixed: {file_path}")
        return True
    else:
        os.remove(backup_path)
        print(f"ℹ️ No changes needed: {file_path}")
        return False

def main():
    orchestrator_files = find_orchestrator_files()
    print(f"Found {len(orchestrator_files)} orchestrator files")
    
    fixed_count = 0
    for file_path in orchestrator_files:
        if fix_orchestrator_file(file_path):
            fixed_count += 1
    
    print(f"Fixed {fixed_count} files")

if __name__ == "__main__":
    main()
EOF

python3 fix_orchestrator.py

echo ""
echo "🔍 STEP 4: Final Verification"
echo "============================="

python3 fix_verification.py
final_issues=$?

echo ""
if [ $final_issues -eq 0 ]; then
    echo -e "${GREEN}🎉 SUCCESS! All DynamoDB key issues have been resolved.${NC}"
else
    echo -e "${YELLOW}⚠️ Some issues may remain. Check the output above.${NC}"
fi

echo ""
echo "📋 STEP 5: Next Steps"
echo "===================="
echo ""
echo -e "${BLUE}🚀 Deployment Instructions:${NC}"
echo ""
echo "1. Test the fixes locally:"
echo "   python3 -m pytest tests/ -v"
echo ""
echo "2. Deploy the updated Lambda functions:"
echo "   cd terraform"
echo "   terraform plan"
echo "   terraform apply"
echo ""
echo "3. Test the deployed functions:"
echo "   # Test a validator directly"
echo "   aws lambda invoke --function-name ksi-validator-cna response.json"
echo ""
echo "4. Check CloudWatch logs for any remaining errors:"
echo "   aws logs tail /aws/lambda/ksi-validator-cna --follow"
echo ""
echo -e "${GREEN}✅ Fix script completed successfully!${NC}"
echo ""
echo -e "${YELLOW}💡 Backup files created with .backup.timestamp extension${NC}"
echo "   Remove them once you've verified everything works:"
echo "   find . -name '*.backup.*' -delete"

# Cleanup temporary scripts
rm -f fix_verification.py fix_validators.py fix_orchestrator.py

echo ""
echo "🏁 Master fix script completed!"
