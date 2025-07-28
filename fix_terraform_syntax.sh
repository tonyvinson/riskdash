#!/bin/bash
# fix_terraform_syntax.sh
# Fix the response_headers syntax error in API Gateway main.tf

echo "🔧 Fixing Terraform syntax errors in API Gateway configuration..."

cd terraform/modules/api_gateway

# Create backup
cp main.tf main.tf.backup.$(date +%Y%m%d_%H%M%S)
echo "✅ Created backup of main.tf"

# Fix the response_headers -> response_parameters
sed -i.tmp '
# Fix method responses - change response_headers to response_parameters
s/response_headers = {/response_parameters = {/g

# Fix the header names to include proper method.response.header prefix
s/"Access-Control-Allow-Origin" = true/"method.response.header.Access-Control-Allow-Origin" = true/g
s/"Access-Control-Allow-Headers" = true/"method.response.header.Access-Control-Allow-Headers" = true/g  
s/"Access-Control-Allow-Methods" = true/"method.response.header.Access-Control-Allow-Methods" = true/g
' main.tf

# Clean up temp file
rm -f main.tf.tmp

echo "✅ Fixed Terraform syntax errors"
echo "📋 Changes made:"
echo "   • response_headers → response_parameters"
echo "   • Added proper method.response.header. prefixes"

cd ../../..

echo ""
echo "🚀 Ready to continue deployment!"
echo "Run: cd terraform && terraform plan"

