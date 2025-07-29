#!/bin/bash
# fix_lambda_env_vars.sh - Remove reserved AWS_REGION environment variable

echo "🔧 Fixing Lambda environment variables..."

cd terraform/modules/api_gateway

# Remove AWS_REGION from the tenants Lambda environment variables
sed -i.backup '/AWS_REGION = var.aws_region/d' main.tf

echo "✅ Removed reserved AWS_REGION environment variable"

cd ../../..

echo "📝 Apply the fix:"
echo "   cd terraform"
echo "   terraform apply"
