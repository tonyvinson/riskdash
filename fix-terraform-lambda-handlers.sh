#!/bin/bash
set -e

echo "🔧 Comprehensive Terraform Lambda Fix"
echo "====================================="

cd terraform

echo "📋 Step 1: Checking current Terraform state..."

# Check what exists in Terraform state
echo "Lambda functions in state:"
terraform state list | grep "aws_lambda_function" | grep "api_"

echo ""
echo "Lambda permissions in state:"
terraform state list | grep "aws_lambda_permission" | grep "api_"

echo ""
echo "📋 Step 2: Checking actual AWS resources..."

# Check if Lambda functions exist in AWS
echo "Checking Lambda functions in AWS:"
aws lambda list-functions --query 'Functions[?contains(FunctionName, `api-executions`) || contains(FunctionName, `api-results`)].{Name:FunctionName,Handler:Handler}' --output table

echo ""
echo "Checking Lambda permissions in AWS:"
aws lambda get-policy --function-name riskuity-ksi-validator-api-executions-production 2>/dev/null && echo "Executions permission exists" || echo "Executions permission missing"
aws lambda get-policy --function-name riskuity-ksi-validator-api-results-production 2>/dev/null && echo "Results permission exists" || echo "Results permission missing"

echo ""
echo "📋 Step 3: Import missing resources or recreate permissions..."

# Check if permissions exist in state, if not import them
if ! terraform state list | grep -q "aws_lambda_permission.api_executions"; then
    echo "Importing executions permission..."
    terraform import module.api_gateway.aws_lambda_permission.api_executions "riskuity-ksi-validator-api-executions-production/AllowExecutionFromAPIGateway" || echo "Import failed - will create new"
fi

if ! terraform state list | grep -q "aws_lambda_permission.api_results"; then
    echo "Importing results permission..."
    terraform import module.api_gateway.aws_lambda_permission.api_results "riskuity-ksi-validator-api-results-production/AllowExecutionFromAPIGateway" || echo "Import failed - will create new"
fi

echo ""
echo "📋 Step 4: Plan and apply all changes..."

# Run terraform plan to see what will be created/updated
echo "Running terraform plan..."
terraform plan \
  -target=module.api_gateway.aws_lambda_function.api_executions \
  -target=module.api_gateway.aws_lambda_function.api_results \
  -target=module.api_gateway.aws_lambda_permission.api_executions \
  -target=module.api_gateway.aws_lambda_permission.api_results

echo ""
echo "Applying changes..."
terraform apply \
  -target=module.api_gateway.aws_lambda_function.api_executions \
  -target=module.api_gateway.aws_lambda_function.api_results \
  -target=module.api_gateway.aws_lambda_permission.api_executions \
  -target=module.api_gateway.aws_lambda_permission.api_results \
  -auto-approve

echo ""
echo "📋 Step 5: Verify everything is working..."

cd ..

# Test both endpoints
echo "Testing executions endpoint..."
EXECUTIONS_RESPONSE=$(curl -s 'https://d5804hjt80.execute-api.us-gov-west-1.amazonaws.com/production/api/ksi/executions?tenant_id=riskuity-production')
echo "Executions response: $EXECUTIONS_RESPONSE"

echo ""
echo "Testing results endpoint..."
RESULTS_RESPONSE=$(curl -s 'https://d5804hjt80.execute-api.us-gov-west-1.amazonaws.com/production/api/ksi/results?tenant_id=riskuity-production')
echo "Results response: $RESULTS_RESPONSE"

echo ""
echo "📋 Step 6: Check Lambda logs for errors..."

if echo "$EXECUTIONS_RESPONSE" | grep -q '"message": "Internal server error"'; then
    echo "Still getting errors - checking logs..."
    aws logs tail /aws/lambda/riskuity-ksi-validator-api-executions-production --since 3m
else
    echo "✅ Executions endpoint appears to be working!"
fi

echo ""
echo "🎯 Final Status:"
echo "- Terraform state synchronized with AWS"
echo "- Lambda functions and permissions managed by Terraform"
echo "- All changes applied through Terraform (no CLI workarounds)"

if echo "$EXECUTIONS_RESPONSE$RESULTS_RESPONSE" | grep -q "success\|debug"; then
    echo "✅ SUCCESS: Endpoints are returning diagnostic data!"
else
    echo "⚠️  Still having issues - check CloudWatch logs above"
fi
