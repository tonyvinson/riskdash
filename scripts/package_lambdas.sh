#!/bin/bash

echo "📦 Packaging Lambda functions..."

# Create lambda packages directory
mkdir -p terraform/lambda_packages

# Package tenant onboarding API
echo "Packaging tenant onboarding API..."
cd lambdas/tenant_onboarding
zip -r ../../terraform/lambda_packages/tenant_onboarding_api.zip .
cd ../..

# Package cross-account validator
echo "Packaging cross-account validator..."
cd lambdas/cross_account_validator
zip -r ../../terraform/lambda_packages/cross_account_ksi_validator.zip .
cd ../..

echo "✅ Lambda packages created:"
ls -la terraform/lambda_packages/

echo ""
echo "🚀 Next steps:"
echo "1. terraform plan"
echo "2. terraform apply"
echo "3. python3 scripts/initialize_riskuity_tenant.py"
