#!/bin/bash

echo "🧪 Simple KSI Platform Test"
echo "=========================="

# Create simple payload 
echo '{"tenant_id":"default","source":"simple_test"}' > simple_payload.json

# Test the platform
echo "🚀 Testing orchestrator..."
aws lambda invoke \
  --function-name riskuity-ksi-validator-orchestrator-production \
  --payload file://simple_payload.json \
  --cli-binary-format raw-in-base64-out \
  --region us-gov-west-1 \
  simple_response.json

echo ""
echo "📊 Results:"
cat simple_response.json | python3 -m json.tool

# Check execution history
echo ""
echo "📈 Checking recent executions..."
aws dynamodb scan \
  --table-name riskuity-ksi-validator-ksi-execution-history-production \
  --region us-gov-west-1 \
  --query 'Items[*].{ExecutionID:execution_id.S,Status:status.S,TotalKSIs:total_ksis_validated.N,CompletedAt:completed_at.S}' \
  --output table

# Cleanup
rm -f simple_payload.json simple_response.json

echo ""
echo "✅ Test completed!"
