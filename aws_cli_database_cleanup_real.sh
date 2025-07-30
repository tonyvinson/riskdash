#!/bin/bash
# 🗄️ AWS CLI DATABASE CLEANUP - Riskuity KSI Validator Production
# Using actual deployed infrastructure from your Terraform

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 RISKUITY KSI VALIDATOR DATABASE CLEANUP${NC}"
echo "Region: us-gov-west-1"
echo "Environment: production"
echo ""

# Your actual table names from Terraform
EXECUTION_HISTORY_TABLE="riskuity-ksi-validator-ksi-execution-history-production"
KSI_DEFINITIONS_TABLE="riskuity-ksi-validator-ksi-definitions-production"
TENANT_CONFIG_TABLE="riskuity-ksi-validator-tenant-ksi-configurations-production"
REGION="us-gov-west-1"

echo -e "${BLUE}Step 1: Verify table access and structure${NC}"
echo "Checking table: $EXECUTION_HISTORY_TABLE"

# Verify table exists and we have access
aws dynamodb describe-table \
  --table-name $EXECUTION_HISTORY_TABLE \
  --region $REGION \
  --output table \
  --query 'Table.{TableName:TableName,Status:TableStatus,ItemCount:ItemCount,GSIs:GlobalSecondaryIndexes[].{IndexName:IndexName,Status:IndexStatus}}'

echo -e "\n${BLUE}Step 2: Audit all tenant data in execution history${NC}"

# Get count of records by tenant using the GSI
echo "Counting records by tenant_id using tenant-timestamp-index..."

# Get all unique tenant_ids first
echo -e "\n📊 Scanning for all tenant_ids..."
aws dynamodb scan \
  --table-name $EXECUTION_HISTORY_TABLE \
  --region $REGION \
  --projection-expression "tenant_id" \
  --output json | \
jq -r '.Items[].tenant_id.S' | sort | uniq -c | sort -nr

echo -e "\n${YELLOW}Detailed breakdown by tenant:${NC}"

# Check each problematic tenant
TENANTS=("all" "real-test" "default")

for tenant in "${TENANTS[@]}"; do
  echo -e "\n--- Tenant: '$tenant' ---"
  
  # Query using GSI for efficient access
  aws dynamodb query \
    --table-name $EXECUTION_HISTORY_TABLE \
    --region $REGION \
    --index-name tenant-timestamp-index \
    --key-condition-expression "tenant_id = :tenant" \
    --expression-attribute-values "{\":tenant\": {\"S\": \"$tenant\"}}" \
    --projection-expression "execution_id, #ts, validator_type" \
    --expression-attribute-names '{"#ts": "timestamp"}' \
    --limit 10 \
    --output table
    
  # Get count for this tenant
  count=$(aws dynamodb query \
    --table-name $EXECUTION_HISTORY_TABLE \
    --region $REGION \
    --index-name tenant-timestamp-index \
    --key-condition-expression "tenant_id = :tenant" \
    --expression-attribute-values "{\":tenant\": {\"S\": \"$tenant\"}}" \
    --select COUNT \
    --output json | jq '.Count')
    
  echo -e "${RED}Total records to DELETE for tenant '$tenant': $count${NC}"
done

# Check what we're keeping
echo -e "\n${GREEN}Step 3: Records we're KEEPING (riskuity-production)${NC}"

aws dynamodb query \
  --table-name $EXECUTION_HISTORY_TABLE \
  --region $REGION \
  --index-name tenant-timestamp-index \
  --key-condition-expression "tenant_id = :tenant" \
  --expression-attribute-values '{"tenant": {"S": "riskuity-production"}}' \
  --projection-expression "execution_id, #ts, validator_type" \
  --expression-attribute-names '{"#ts": "timestamp"}' \
  --output table

# Get count for riskuity-production
keep_count=$(aws dynamodb query \
  --table-name $EXECUTION_HISTORY_TABLE \
  --region $REGION \
  --index-name tenant-timestamp-index \
  --key-condition-expression "tenant_id = :tenant" \
  --expression-attribute-values '{"tenant": {"S": "riskuity-production"}}' \
  --select COUNT \
  --output json | jq '.Count')

echo -e "${GREEN}Total records to KEEP for riskuity-production: $keep_count${NC}"

echo -e "\n${YELLOW}Step 4: Summary before deletion${NC}"
echo "Tables to clean:"
echo "  - $EXECUTION_HISTORY_TABLE"
echo ""
echo "Tenants to DELETE:"
echo "  - 'all' tenant records"
echo "  - 'real-test' tenant records" 
echo "  - 'default' tenant records"
echo "  - Any other non-riskuity-production tenants"
echo ""
echo "Tenants to KEEP:"
echo "  - 'riskuity-production' records only"

echo -e "\n${RED}⚠️  WARNING: Review the data above carefully!${NC}"
echo "Do you want to proceed with deletion? (y/N)"
read -r response

if [[ "$response" =~ ^[Yy]$ ]]; then
    echo -e "\n${RED}🚨 STARTING DELETION PROCESS${NC}"
    
    # Create deletion script for each problematic tenant
    for tenant in "${TENANTS[@]}"; do
        echo -e "\n${YELLOW}Deleting records for tenant: '$tenant'${NC}"
        
        # Get all items for this tenant and delete them
        aws dynamodb query \
          --table-name $EXECUTION_HISTORY_TABLE \
          --region $REGION \
          --index-name tenant-timestamp-index \
          --key-condition-expression "tenant_id = :tenant" \
          --expression-attribute-values "{\":tenant\": {\"S\": \"$tenant\"}}" \
          --projection-expression "execution_id, #ts" \
          --expression-attribute-names '{"#ts": "timestamp"}' \
          --output json | \
        jq -r '.Items[] | @base64' | \
        while read -r item; do
            # Decode the item
            decoded=$(echo "$item" | base64 --decode)
            execution_id=$(echo "$decoded" | jq -r '.execution_id.S')
            timestamp=$(echo "$decoded" | jq -r '.timestamp.S')
            
            echo "Deleting: $execution_id at $timestamp"
            
            # Delete the item using primary key
            aws dynamodb delete-item \
              --table-name $EXECUTION_HISTORY_TABLE \
              --region $REGION \
              --key "{\"execution_id\": {\"S\": \"$execution_id\"}, \"timestamp\": {\"S\": \"$timestamp\"}}" \
              --output text > /dev/null
              
            if [ $? -eq 0 ]; then
                echo "  ✅ Deleted successfully"
            else
                echo "  ❌ Failed to delete"
            fi
        done
    done
    
    echo -e "\n${GREEN}✅ Deletion completed!${NC}"
    
    # Verify deletion worked
    echo -e "\n${BLUE}Verifying deletion...${NC}"
    
    for tenant in "${TENANTS[@]}"; do
        remaining=$(aws dynamodb query \
          --table-name $EXECUTION_HISTORY_TABLE \
          --region $REGION \
          --index-name tenant-timestamp-index \
          --key-condition-expression "tenant_id = :tenant" \
          --expression-attribute-values "{\":tenant\": {\"S\": \"$tenant\"}}" \
          --select COUNT \
          --output json | jq '.Count')
          
        if [ "$remaining" -eq 0 ]; then
            echo -e "✅ Tenant '$tenant': $remaining records remaining"
        else
            echo -e "❌ Tenant '$tenant': $remaining records still exist"
        fi
    done
    
    # Show final count for riskuity-production
    final_count=$(aws dynamodb query \
      --table-name $EXECUTION_HISTORY_TABLE \
      --region $REGION \
      --index-name tenant-timestamp-index \
      --key-condition-expression "tenant_id = :tenant" \
      --expression-attribute-values '{"tenant": {"S": "riskuity-production"}}' \
      --select COUNT \
      --output json | jq '.Count')
      
    echo -e "\n${GREEN}Final count for riskuity-production: $final_count records${NC}"
    
else
    echo -e "\n${YELLOW}Deletion cancelled. No changes made.${NC}"
fi

echo -e "\n${BLUE}🏁 Database cleanup script completed${NC}"
echo ""
echo "Next steps:"
echo "1. Test validation with: aws lambda invoke --function-name riskuity-ksi-validator-orchestrator-production output.json"
echo "2. Verify frontend shows only riskuity-production data"
echo "3. Configure proper tenant isolation in Lambda functions"
