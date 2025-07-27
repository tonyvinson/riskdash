#!/bin/bash

echo "🔍 Debugging KSI Validator Network Connection..."

# 1. Check if .env file exists and has correct API URL
echo "📁 Checking environment configuration..."
cd frontend

if [ -f .env ]; then
    echo "✅ .env file exists:"
    cat .env
else
    echo "❌ .env file missing! Creating it now..."
    cat > .env << 'ENV_EOF'
REACT_APP_API_URL=https://d5804hjt80.execute-api.us-gov-west-1.amazonaws.com/production
REACT_APP_ENVIRONMENT=production
REACT_APP_PROJECT_NAME=riskuity-ksi-validator
ENV_EOF
    echo "✅ Created .env file"
fi

echo ""
echo "🌐 Testing API Gateway connectivity..."

# 2. Test API Gateway directly
API_URL="https://d5804hjt80.execute-api.us-gov-west-1.amazonaws.com/production"

echo "Testing base API URL: $API_URL"
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" "$API_URL" || echo "❌ Base URL not reachable"

echo ""
echo "Testing /api/ksi/executions endpoint..."
curl -s -w "HTTP Status: %{http_code}\n" "$API_URL/api/ksi/executions?limit=1" || echo "❌ Executions endpoint failed"

echo ""
echo "Testing /api/ksi/validate endpoint..."
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"tenant_id": "default", "trigger_source": "manual"}' \
  -w "HTTP Status: %{http_code}\n" \
  "$API_URL/api/ksi/validate" || echo "❌ Validate endpoint failed"

echo ""
echo "🔧 Troubleshooting steps:"
echo "1. Restart your React development server: npm start"
echo "2. Check browser console for detailed error messages"
echo "3. Verify Lambda functions are deployed:"
echo "   aws lambda list-functions --query 'Functions[?starts_with(FunctionName, \`riskuity-ksi-validator\`)].FunctionName'"
echo "4. Check API Gateway logs in CloudWatch"
echo "5. Verify CORS is enabled on API Gateway"

echo ""
echo "🚀 If API tests above show HTTP 200, the issue is likely CORS or React configuration"
echo "   Try opening browser dev tools and checking the Network tab for detailed error info"
