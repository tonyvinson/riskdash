#!/usr/bin/env python3
"""
Task 2: DynamoDB Composite Key Issues Verification
"""

import os
import re
from pathlib import Path

def check_file_for_issues(file_path):
    """Check a single file for DynamoDB key issues"""
    issues = []
    fixes_present = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for problematic patterns
        if re.search(r'table\.get_item\(\s*Key\s*=\s*\{\s*[\'"]tenant_id[\'"]:\s*tenant_id\s*\}\s*\)', content):
            issues.append("❌ Single-key get_item() with tenant_id found")
        
        if re.search(r'tenant_config_table\.get_item.*tenant_id.*tenant_id', content):
            issues.append("❌ Problematic tenant_config_table.get_item() pattern")
        
        # Check for proper patterns
        if 'KeyConditionExpression' in content and 'table.query(' in content:
            fixes_present.append("✅ Proper query() with KeyConditionExpression found")
        
        if '# ✅ FIXED:' in content or 'FIXED VERSION' in content:
            fixes_present.append("✅ File contains fix markers")
        
        return issues, fixes_present
        
    except Exception as e:
        return [f"❌ Error reading file: {str(e)}"], []

def main():
    files_with_issues = 0
    total_issues = 0
    
    print("🔍 Scanning Lambda files for DynamoDB key issues...")
    print("")
    
    for file_path in Path('.').glob('lambdas/**/*.py'):
        if file_path.is_file():
            issues, fixes = check_file_for_issues(str(file_path))
            
            if issues or fixes:
                print(f"📄 {file_path}")
                
                if issues:
                    files_with_issues += 1
                    total_issues += len(issues)
                    for issue in issues:
                        print(f"   {issue}")
                
                if fixes:
                    for fix in fixes:
                        print(f"   {fix}")
                
                print("")
    
    print("=" * 60)
    print(f"📊 SUMMARY:")
    print(f"   Files with issues: {files_with_issues}")
    print(f"   Total issues found: {total_issues}")
    
    return total_issues

if __name__ == "__main__":
    exit(main())
