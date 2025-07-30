#!/bin/bash

# 🔍 DEBUG: Check CloudWatch logs to see what's crashing in the orchestrator

echo "🔍 DEBUGGING ORCHESTRATOR LOGS"
echo "=============================="

FUNCTION_NAME="riskuity-ksi-validator-orchestrator-production"
REGION="us-gov-west-1"

echo "Function: $FUNCTION_NAME"
echo "Region: $REGION"
echo ""

# 1. Get the latest log events from CloudWatch
echo "=== RECENT ORCHESTRATOR LOG EVENTS ==="
aws logs tail "/aws/lambda/$FUNCTION_NAME" \
  --region $REGION \
  --since 5m \
  --format short

echo ""
echo "=== RECENT ERROR EVENTS ONLY ==="
aws logs tail "/aws/lambda/$FUNCTION_NAME" \
  --region $REGION \
  --since 5m \
  --filter-pattern "ERROR" \
  --format short

echo ""
echo "=== CHECKING FOR SPECIFIC ISSUES ==="

# Check for common issues
aws logs tail "/aws/lambda/$FUNCTION_NAME" \
  --region $REGION \
  --since 5m \
  --filter-pattern "tenant_id" \
  --format short

echo ""
echo "=== TESTING ORCHESTRATOR DIRECTLY ==="
echo "Invoking orchestrator Lambda directly (bypassing API Gateway):"

# Test the orchestrator directly
aws lambda invoke \
  --region $REGION \
  --function-name $FUNCTION_NAME \
  --payload '{"tenant_id": "riskuity-production", "trigger_source": "manual"}' \
  orchestrator_test_output.json

echo ""
echo "Direct orchestrator result:"
cat orchestrator_test_output.json | jq

echo ""
echo "=== DIAGNOSIS CHECKLIST ==="
echo "🔍 Look for these common issues in the logs above:"
echo "   • 'No module named' errors → Missing Python dependencies"
echo "   • 'Unable to import module' → Handler function name wrong"
echo "   • 'Table not found' → DynamoDB table permissions issue"
echo "   • 'KeyConditionExpression' errors → DynamoDB query syntax issue"
echo "   • 'AccessDenied' → IAM permissions issue"
echo "   • 'tenant_id' related errors → Our fix working/not working"
