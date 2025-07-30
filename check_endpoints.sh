#!/bin/bash

set -e

echo "🔍 Checking what API endpoints actually exist..."

API_ID="d5804hjt80"
AWS_REGION="us-gov-west-1"

echo "API Gateway ID: $API_ID"
echo ""

# Get all resources and methods
echo "📋 Available API Resources:"
aws apigateway get-resources \
    --rest-api-id "$API_ID" \
    --region "$AWS_REGION" \
    --query 'items[].{Path:path,Methods:resourceMethods,Id:id}' \
    --output table

echo ""
echo "🔍 Detailed API structure:"

# Get all resources
RESOURCES=$(aws apigateway get-resources --rest-api-id "$API_ID" --region "$AWS_REGION" --query 'items[].{path:path,id:id}' --output json)

echo "$RESOURCES" | jq -r '.[] | "\(.path) (ID: \(.id))"'

echo ""
echo "🧪 Testing existing endpoints:"

BASE_URL="https://${API_ID}.execute-api.${AWS_REGION}.amazonaws.com/production"

# Test validate (we know this exists)
echo "Testing POST /api/ksi/validate..."
curl -X POST "${BASE_URL}/api/ksi/validate" \
    -H "Content-Type: application/json" \
    -d '{"tenant_id":"test"}' \
    -w "Status: %{http_code}\n" \
    -s --max-time 10 -o /dev/null

# Test executions
echo "Testing GET /api/ksi/executions..."
curl -X GET "${BASE_URL}/api/ksi/executions" \
    -w "Status: %{http_code}\n" \
    -s --max-time 10 -o /dev/null

# Test results  
echo "Testing GET /api/ksi/results..."
curl -X GET "${BASE_URL}/api/ksi/results" \
    -w "Status: %{http_code}\n" \
    -s --max-time 10 -o /dev/null

# Test tenants
echo "Testing GET /api/ksi/tenants..."
curl -X GET "${BASE_URL}/api/ksi/tenants" \
    -w "Status: %{http_code}\n" \
    -s --max-time 10 -o /dev/null

echo ""
echo "🔧 Checking Lambda functions that should handle these endpoints:"

# Check what Lambda functions exist
echo "Available Lambda functions:"
aws lambda list-functions \
    --region "$AWS_REGION" \
    --query 'Functions[?contains(FunctionName, `riskuity-ksi-validator`)].{Name:FunctionName,Runtime:Runtime,LastModified:LastModified}' \
    --output table

echo ""
echo "🎯 DIAGNOSIS:"
echo "If endpoints are missing (404), we need to:"
echo "1. Create the missing API Gateway resources"
echo "2. Create or fix the Lambda functions" 
echo "3. Set up proper integrations"
echo ""
echo "💡 Quick fix options:"
echo "A) Create missing endpoints manually"
echo "B) Use working orchestrator for all endpoints (simplest)"
echo "C) Deploy proper Terraform configuration"
