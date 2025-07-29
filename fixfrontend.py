#!/usr/bin/env python3
"""
Complete Frontend Fix Script
Fixes all KSIManager.js data parsing issues and provides verification
"""

import os
import re
import shutil
from datetime import datetime

def create_backup(file_path):
    """Create backup of original file"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{file_path}.backup.{timestamp}"
    shutil.copy2(file_path, backup_path)
    return backup_path

def fix_frontend_completely():
    """Complete fix for all frontend data structure issues"""
    
    file_path = "frontend/src/components/KSIManager/KSIManager.js"
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        print("Make sure you're running this from the project root directory")
        return False
    
    print(f"🔧 Applying complete fix to {file_path}")
    
    # Create backup
    backup_path = create_backup(file_path)
    print(f"💾 Backup created: {backup_path}")
    
    # Read the file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    fixes_applied = []
    
    # FIX 1: fetchCurrentKSIData function - handle API response structure
    fix1_pattern = r'(if \(response\.success && response\.data && response\.data\.validation_results\) \{\s*const results = response\.data\.validation_results;)'
    
    fix1_replacement = '''// ✅ FIXED: Handle the actual API response structure
            let results = [];
            
            if (response.success && response.data) {
                // Check for validators_completed (the actual API structure)
                if (response.data.validators_completed) {
                    results = response.data.validators_completed;
                    console.log('✅ Found validators_completed in response.data');
                }
                // Fallback: Check for validation_results 
                else if (response.data.validation_results) {
                    results = response.data.validation_results;
                    console.log('✅ Found validation_results in response.data');
                }
                // Fallback: Check for results array directly in data
                else if (response.data.results) {
                    results = response.data.results;
                    console.log('✅ Found results in response.data');
                }
                // Fallback: Check if data itself is an array
                else if (Array.isArray(response.data)) {
                    results = response.data;
                    console.log('✅ Response.data is array of results');
                }
            }
            // Fallback: Check top-level properties
            else if (response.validators_completed) {
                results = response.validators_completed;
                console.log('✅ Found validators_completed at top level');
            }
            else if (response.results) {
                results = response.results;
                console.log('✅ Found results at top level');
            }
            
            console.log('📊 Processing results:', results);
            
            if (results && results.length > 0) {
                const results = results;'''
    
    if re.search(fix1_pattern, content):
        content = re.sub(fix1_pattern, fix1_replacement, content)
        fixes_applied.append("Fixed API response structure handling")
    
    # FIX 2: Fix execution history data access
    fix2_pattern = r'(if \(execution && execution\.validation_results\) \{)'
    
    fix2_replacement = '''// ✅ FIXED: Check for different possible result locations
                let resultsData = [];
                
                if (execution.validation_results) {
                    resultsData = execution.validation_results;
                    console.log('✅ Found validation_results in execution');
                } else if (execution.validators_completed) {
                    resultsData = execution.validators_completed;
                    console.log('✅ Found validators_completed in execution');
                } else if (execution.results) {
                    resultsData = execution.results;
                    console.log('✅ Found results in execution');
                }
                
                if (resultsData.length > 0) {'''
    
    if re.search(fix2_pattern, content):
        content = re.sub(fix2_pattern, fix2_replacement, content)
        fixes_applied.append("Fixed execution history data access")
        
        # Also need to update the reference to validation_results
        content = content.replace('execution.validation_results.map', 'resultsData.map')
    
    # FIX 3: Add better error handling and logging
    fix3_pattern = r'(console\.log\(\'ℹ️ No current KSI data found for this tenant\'\);)'
    
    fix3_replacement = '''console.log('ℹ️ No current KSI data found for this tenant');
                console.log('🔍 Response structure:', Object.keys(response));
                if (response.data) {
                    console.log('🔍 Response.data structure:', Object.keys(response.data));
                }'''
    
    if re.search(fix3_pattern, content):
        content = re.sub(fix3_pattern, fix3_replacement, content)
        fixes_applied.append("Added better error logging")
    
    # FIX 4: Fix the closing condition check
    fix4_pattern = r'(\} else \{\s*console\.log\(\'ℹ️ No current KSI data found for this tenant\'\);)'
    
    fix4_replacement = '''} else {
                console.log('ℹ️ No current KSI data found for this tenant');
                console.log('🔍 Full response:', response);'''
    
    if re.search(fix4_pattern, content):
        content = re.sub(fix4_pattern, fix4_replacement, content)
        fixes_applied.append("Enhanced debugging output")
    
    # Write the fixed content
    if fixes_applied:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Applied fixes: {', '.join(fixes_applied)}")
        return True
    else:
        print("ℹ️ No fixes needed - file appears to be correct already")
        # Remove backup since no changes were made
        os.remove(backup_path)
        return True

def verify_fix():
    """Verify that the fix was applied correctly"""
    file_path = "frontend/src/components/KSIManager/KSIManager.js"
    
    if not os.path.exists(file_path):
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for the fix patterns
    checks = [
        ('validators_completed check', 'validators_completed' in content),
        ('Better error handling', 'Response structure:' in content),
        ('Multiple fallback checks', 'response.data.results' in content),
        ('Execution data handling', 'resultsData' in content)
    ]
    
    print("\n🔍 Verification Results:")
    all_good = True
    for check_name, result in checks:
        status = "✅" if result else "❌"
        print(f"   {status} {check_name}")
        if not result:
            all_good = False
    
    return all_good

def main():
    """Main execution function"""
    print("🚀 Complete Frontend Data Structure Fix")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("frontend/src/components/KSIManager"):
        print("❌ Error: Please run this script from the project root directory")
        print("   (Should contain 'frontend/src/components/KSIManager' directory)")
        return
    
    print("📋 This script will fix:")
    print("   • API response data structure handling")
    print("   • Execution history data access")
    print("   • Error logging and debugging")
    print("   • Fallback data parsing")
    print("")
    
    # Apply the fix
    success = fix_frontend_completely()
    
    if success:
        # Verify the fix
        if verify_fix():
            print("\n🎉 COMPLETE FIX APPLIED SUCCESSFULLY!")
        else:
            print("\n⚠️ Fix applied but verification failed")
        
        print("\n📋 Next Steps:")
        print("1. Restart your React development server:")
        print("   cd frontend")
        print("   # Press Ctrl+C to stop current server")
        print("   npm start")
        print("")
        print("2. Hard refresh your browser: Ctrl+Shift+R")
        print("")
        print("3. Expected Results:")
        print("   ✅ Compliance Overview shows real percentages")
        print("   ✅ KSI Categories show actual status (not all 'ISSUE')")
        print("   ✅ Browser console shows data loading successfully")
        print("   ✅ Dashboard displays actual AWS resource counts")
        print("")
        print("4. If still not working, check browser console for:")
        print("   • New debug messages showing data structure")
        print("   • 'Found validators_completed in response.data' messages")
        print("")
        print("💡 Backup files saved with .backup.timestamp extension")
    else:
        print("\n❌ Fix failed. Check the error messages above.")

if __name__ == "__main__":
    main()
