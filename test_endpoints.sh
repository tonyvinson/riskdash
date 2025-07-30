#!/bin/bash

set -e

echo "🧪 Testing all API endpoints..."

API_ID="d5804hjt80"
AWS_REGION="us-gov-west-1"
BASE_URL="https://${API_ID}.execute-api.${AWS_REGION}.amazonaws.com/production"

echo "Base URL: $BASE_URL"
echo ""

# Test each endpoint
test_endpoint() {
    local method=$1
    local endpoint=$2
    local data=$3
    
    echo "🔍 Testing $method $endpoint"
    
    if [ "$method" = "POST" ]; then
        RESPONSE=$(curl -X POST "${BASE_URL}${endpoint}" \
            -H "Content-Type: application/json" \
            -d "$data" \
            -w "HTTPCODE:%{http_code}" \
            -s --max-time 15)
    else
        RESPONSE=$(curl -X GET "${BASE_URL}${endpoint}" \
            -w "HTTPCODE:%{http_code}" \
            -s --max-time 15)
    fi
    
    HTTP_CODE=$(echo "$RESPONSE" | grep -o "HTTPCODE:[0-9]*" | cut -d: -f2)
    BODY=$(echo "$RESPONSE" | sed 's/HTTPCODE:[0-9]*$//')
    
    echo "   Status: $HTTP_CODE"
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo "   ✅ Working"
        echo "   Response: $(echo "$BODY" | jq -c . 2>/dev/null || echo "$BODY" | head -c 100)..."
    elif [ "$HTTP_CODE" = "404" ]; then
        echo "   ❌ 404 Not Found - Integration missing"
    elif [ "$HTTP_CODE" = "502" ]; then
        echo "   ❌ 502 Bad Gateway - Lambda function broken"
    elif [ "$HTTP_CODE" = "500" ]; then
        echo "   ❌ 500 Internal Error - Lambda function error"
    else
        echo "   ⚠️  Unexpected status: $HTTP_CODE"
        echo "   Response: $BODY"
    fi
    echo ""
}

# Test all endpoints
test_endpoint "POST" "/api/ksi/validate" '{"tenant_id":"riskuity-production","trigger_source":"manual"}'
test_endpoint "GET" "/api/ksi/executions" ""
test_endpoint "GET" "/api/ksi/results" ""
test_endpoint "GET" "/api/ksi/tenants" ""

echo "🔍 Checking which Lambda functions are actually connected..."

# Check integrations for each resource
check_integration() {
    local resource_id=$1
    local path=$2
    local method=$3
    
    echo "📋 Integration for $method $path:"
    
    INTEGRATION=$(aws apigateway get-integration \
        --rest-api-id "$API_ID" \
        --resource-id "$resource_id" \
        --http-method "$method" \
        --region "$AWS_REGION" \
        --query '{Type:type,Uri:uri}' \
        --output json 2>/dev/null || echo '{"Type":"NONE","Uri":"NONE"}')
    
    echo "   $(echo "$INTEGRATION" | jq -r '.Type'): $(echo "$INTEGRATION" | jq -r '.Uri')"
    echo ""
}

echo ""
echo "🔍 API Gateway Integrations:"
check_integration "732u0c" "/api/ksi/validate" "POST"
check_integration "r5nzil" "/api/ksi/executions" "GET"  
check_integration "dg62xn" "/api/ksi/results" "GET"
check_integration "m5r8ac" "/api/ksi/tenants" "GET"

echo "🎯 DIAGNOSIS & FIXES:"
echo ""
echo "If endpoints return:"
echo "  404 → Lambda integration missing (need to connect to Lambda function)"
echo "  502 → Lambda function exists but crashes (check function code)" 
echo "  500 → Lambda function exists but has errors (check CloudWatch logs)"
echo "  200 → Working! 🎉"
echo ""
echo "💡 Quick Fix: Point all broken endpoints to working orchestrator function"
