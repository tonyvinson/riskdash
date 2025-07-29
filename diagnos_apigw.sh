#!/bin/bash
# cors-diagnostic.sh - Check if CORS is actually deployed and working

echo "🔍 CORS Diagnostic for KSI Validator API"
echo "========================================"

API_BASE="https://d5804hjt80.execute-api.us-gov-west-1.amazonaws.com/production"
echo "Testing API: $API_BASE"
echo ""

# Test 1: Check if OPTIONS methods are working (CORS preflight)
echo "📋 Test 1: CORS Preflight Requests (OPTIONS)"
echo "---------------------------------------------"

endpoints=("api/ksi/validate" "api/ksi/executions" "api/ksi/results" "api/ksi/tenants")

for endpoint in "${endpoints[@]}"; do
    echo "Testing: $endpoint"
    response=$(curl -s -o /dev/null -w "%{http_code}" -X OPTIONS \
        -H "Origin: http://localhost:3000" \
        -H "Access-Control-Request-Method: GET" \
        -H "Access-Control-Request-Headers: Content-Type" \
        "$API_BASE/$endpoint")
    
    if [ "$response" = "200" ]; then
        echo "  ✅ OPTIONS $endpoint: $response (CORS preflight working)"
    else
        echo "  ❌ OPTIONS $endpoint: $response (CORS preflight FAILED)"
    fi
done

echo ""

# Test 2: Check actual CORS headers in responses
echo "📋 Test 2: CORS Headers in Actual Responses"
echo "--------------------------------------------"

for endpoint in "${endpoints[@]}"; do
    echo "Testing headers for: $endpoint"
    
    if [ "$endpoint" = "api/ksi/validate" ]; then
        method="POST"
        data='{"tenant_id": "test"}'
        headers=$(curl -s -I -X $method -H "Content-Type: application/json" -d "$data" "$API_BASE/$endpoint")
    else
        method="GET"
        headers=$(curl -s -I -X $method "$API_BASE/$endpoint")
    fi
    
    cors_origin=$(echo "$headers" | grep -i "access-control-allow-origin" | head -1)
    
    if [[ -n "$cors_origin" ]]; then
        echo "  ✅ $endpoint: $cors_origin"
    else
        echo "  ❌ $endpoint: No Access-Control-Allow-Origin header found"
    fi
done

echo ""

# Test 3: Check if API Gateway deployment is current
echo "📋 Test 3: API Gateway Deployment Status"
echo "----------------------------------------"

# This requires AWS CLI to be configured
if command -v aws &> /dev/null; then
    echo "Checking API Gateway deployment..."
    
    # Get the API Gateway ID (you might need to adjust this)
    API_ID="d5804hjt80"
    
    # Check deployment status
    deployment_info=$(aws apigateway get-deployments --rest-api-id $API_ID --region us-gov-west-1 2>/dev/null)
    
    if [[ $? -eq 0 ]]; then
        echo "✅ AWS CLI connected - checking latest deployment..."
        echo "$deployment_info" | jq -r '.items[0] | "Latest deployment: \(.id) created \(.createdDate)"' 2>/dev/null || echo "Deployment info retrieved (jq not available for parsing)"
    else
        echo "⚠️ AWS CLI not configured or no access to API Gateway"
    fi
else
    echo "⚠️ AWS CLI not available - cannot check deployment status"
fi

echo ""

# Test 4: Direct browser test simulation
echo "📋 Test 4: Browser CORS Test Simulation"
echo "---------------------------------------"

echo "Simulating browser request to executions endpoint..."
response=$(curl -s -w "\nHTTP_CODE:%{http_code}\n" \
    -H "Origin: http://localhost:3000" \
    -H "Content-Type: application/json" \
    "$API_BASE/api/ksi/executions?limit=1")

echo "$response"

echo ""
echo "🎯 DIAGNOSIS COMPLETE"
echo "===================="
echo ""
echo "If you see ❌ errors above, then CORS is NOT properly deployed despite being in Terraform."
echo ""
echo "Quick fixes:"
echo "1. Run: terraform apply -target=module.api_gateway (redeploy API Gateway)"
echo "2. Add missing /tenants endpoint with CORS"
echo "3. Verify API Gateway deployment in AWS Console"
