#!/bin/bash

echo "🔍 REACT PROXY DIAGNOSTIC"
echo "========================="

echo ""
echo "📁 1. Checking if setupProxy.js exists and is configured..."
if [ -f "frontend/src/setupProxy.js" ]; then
    echo "✅ setupProxy.js found"
    echo "📄 Content preview:"
    head -10 frontend/src/setupProxy.js
else
    echo "❌ setupProxy.js not found!"
fi

echo ""
echo "📦 2. Checking if http-proxy-middleware is installed..."
cd frontend
if npm list http-proxy-middleware > /dev/null 2>&1; then
    echo "✅ http-proxy-middleware is installed"
    npm list http-proxy-middleware
else
    echo "❌ http-proxy-middleware NOT installed!"
    echo "💡 Install with: npm install http-proxy-middleware --save-dev"
fi

echo ""
echo "🚀 3. Checking if React dev server is running with proxy..."
if pgrep -f "react-scripts start" > /dev/null; then
    echo "✅ React dev server is running"
    echo "🔄 Restart recommendation: Stop and start dev server to ensure proxy is active"
else
    echo "❌ React dev server not running"
fi

echo ""
echo "🌐 4. Testing direct API call (should work)..."
curl -s -o /dev/null -w "Direct API: %{http_code}\n" \
  -X POST "https://d5804hjt80.execute-api.us-gov-west-1.amazonaws.com/production/api/ksi/validate" \
  -H "Content-Type: application/json" \
  -d '{"tenant_id": "riskuity-production"}'

echo ""
echo "🔧 5. Testing proxy (if dev server running on :3000)..."
if curl -s -o /dev/null -w "Proxy API: %{http_code}\n" \
  -X POST "http://localhost:3000/api/ksi/validate" \
  -H "Content-Type: application/json" \
  -d '{"tenant_id": "riskuity-production"}' 2>/dev/null; then
    echo "✅ Proxy working!"
else
    echo "❌ Proxy not responding (dev server may not be running with proxy)"
fi

echo ""
echo "💡 SOLUTIONS:"
echo "   1. Restart React dev server: Ctrl+C then 'npm start'"
echo "   2. Install proxy middleware if missing: npm install http-proxy-middleware --save-dev"
echo "   3. Check browser Network tab - requests should go to localhost:3000/api/* (not the full AWS URL)"
echo "   4. Clear browser cache and try again"
