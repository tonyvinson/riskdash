#!/bin/bash

echo "🔐 Adding IAM Permissions for RiskDash Compliance Validation"
echo "=========================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
ROLE_NAME="riskuity-ksi-validator-orchestrator-role-production"
POLICY_NAME="RiskDashComplianceValidationPolicy"
AWS_REGION="us-gov-west-1"

echo -e "${BLUE}Creating comprehensive IAM policy for compliance validation...${NC}"

# Create the IAM policy document
cat > compliance_policy.json << 'EOF'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "CNANetworkArchitectureValidation",
            "Effect": "Allow",
            "Action": [
                "ec2:DescribeSubnets",
                "ec2:DescribeAvailabilityZones",
                "ec2:DescribeVpcs",
                "ec2:DescribeRouteTables",
                "ec2:DescribeNetworkAcls",
                "ec2:DescribeSecurityGroups",
                "route53:ListHostedZones",
                "route53:GetHostedZone"
            ],
            "Resource": "*"
        },
        {
            "Sid": "SVCServiceValidation",
            "Effect": "Allow",
            "Action": [
                "kms:ListKeys",
                "kms:ListAliases",
                "kms:DescribeKey",
                "secretsmanager:ListSecrets",
                "secretsmanager:DescribeSecret",
                "s3:ListAllMyBuckets",
                "s3:GetBucketEncryption",
                "s3:GetBucketVersioning"
            ],
            "Resource": "*"
        },
        {
            "Sid": "IAMIdentityAccessValidation",
            "Effect": "Allow",
            "Action": [
                "iam:ListUsers",
                "iam:ListRoles",
                "iam:ListPolicies",
                "iam:GetAccountSummary",
                "iam:GetAccountPasswordPolicy",
                "iam:ListMFADevices",
                "iam:GetUser",
                "iam:GetRole",
                "sts:GetCallerIdentity"
            ],
            "Resource": "*"
        },
        {
            "Sid": "MLAMonitoringLoggingValidation",
            "Effect": "Allow",
            "Action": [
                "cloudtrail:DescribeTrails",
                "cloudtrail:GetTrailStatus",
                "cloudwatch:DescribeAlarms",
                "cloudwatch:GetMetricStatistics",
                "logs:DescribeLogGroups",
                "sns:ListTopics",
                "sns:GetTopicAttributes",
                "events:ListRules"
            ],
            "Resource": "*"
        },
        {
            "Sid": "CMTChangeManagementValidation",
            "Effect": "Allow",
            "Action": [
                "cloudtrail:DescribeTrails",
                "config:DescribeConfigurationRecorders",
                "config:DescribeDeliveryChannels",
                "config:GetComplianceSummaryByConfigRule",
                "cloudformation:ListStacks",
                "cloudformation:DescribeStacks",
                "cloudformation:GetStackPolicy"
            ],
            "Resource": "*"
        },
        {
            "Sid": "GeneralComplianceValidation",
            "Effect": "Allow",
            "Action": [
                "organizations:DescribeOrganization",
                "support:DescribeTrustedAdvisorChecks",
                "trustedadvisor:Describe*",
                "securityhub:GetFindings",
                "securityhub:DescribeHub",
                "inspector2:ListFindings",
                "guardduty:ListDetectors",
                "guardduty:GetDetector"
            ],
            "Resource": "*"
        }
    ]
}
EOF

echo -e "${GREEN}✅ Created compliance validation policy${NC}"

echo -e "\n${YELLOW}Step 1: Check if policy already exists${NC}"
if aws iam get-policy --policy-arn "arn:aws-us-gov:iam::736539455039:policy/$POLICY_NAME" --region "$AWS_REGION" &> /dev/null; then
    echo -e "${YELLOW}⚠️ Policy $POLICY_NAME already exists, updating...${NC}"
    
    # Get the current policy version
    VERSION=$(aws iam get-policy --policy-arn "arn:aws-us-gov:iam::736539455039:policy/$POLICY_NAME" --region "$AWS_REGION" --query 'Policy.DefaultVersionId' --output text)
    
    # Create new policy version
    aws iam create-policy-version \
        --policy-arn "arn:aws-us-gov:iam::736539455039:policy/$POLICY_NAME" \
        --policy-document file://compliance_policy.json \
        --set-as-default \
        --region "$AWS_REGION"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Updated policy $POLICY_NAME${NC}"
        
        # Clean up old versions (keep max 2)
        aws iam delete-policy-version \
            --policy-arn "arn:aws-us-gov:iam::736539455039:policy/$POLICY_NAME" \
            --version-id "$VERSION" \
            --region "$AWS_REGION" &> /dev/null
    else
        echo -e "${RED}❌ Failed to update policy${NC}"
        exit 1
    fi
else
    echo -e "${BLUE}Creating new policy...${NC}"
    
    # Create the policy
    aws iam create-policy \
        --policy-name "$POLICY_NAME" \
        --policy-document file://compliance_policy.json \
        --description "Comprehensive IAM policy for RiskDash FedRAMP compliance validation" \
        --region "$AWS_REGION"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Created policy $POLICY_NAME${NC}"
    else
        echo -e "${RED}❌ Failed to create policy${NC}"
        exit 1
    fi
fi

echo -e "\n${YELLOW}Step 2: Attach policy to orchestrator role${NC}"

# Attach the policy to the role
aws iam attach-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-arn "arn:aws-us-gov:iam::736539455039:policy/$POLICY_NAME" \
    --region "$AWS_REGION"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Attached policy to role $ROLE_NAME${NC}"
else
    echo -e "${YELLOW}⚠️ Policy may already be attached to role${NC}"
fi

echo -e "\n${YELLOW}Step 3: Verify role permissions${NC}"

# List attached policies
echo -e "${BLUE}Policies attached to $ROLE_NAME:${NC}"
aws iam list-attached-role-policies \
    --role-name "$ROLE_NAME" \
    --region "$AWS_REGION" \
    --query 'AttachedPolicies[*].PolicyName' \
    --output table

echo -e "\n${YELLOW}Step 4: Wait for permissions to propagate${NC}"
echo -e "${BLUE}Waiting 30 seconds for IAM permissions to propagate...${NC}"
sleep 30

# Cleanup
rm -f compliance_policy.json

echo ""
echo -e "${GREEN}🎉 IAM Permissions Successfully Added!${NC}"
echo -e "${BLUE}What was granted:${NC}"
echo "  ✅ CNA: EC2, VPC, Route53 read permissions"
echo "  ✅ SVC: KMS, Secrets Manager, S3 read permissions"  
echo "  ✅ IAM: Identity and access read permissions"
echo "  ✅ MLA: CloudTrail, CloudWatch, SNS read permissions"
echo "  ✅ CMT: Config, CloudFormation read permissions"
echo "  ✅ General: Security Hub, GuardDuty read permissions"

echo ""
echo -e "${YELLOW}🧪 Test your compliance validation now:${NC}"
echo "curl -X POST 'https://d5804hjt80.execute-api.us-gov-west-1.amazonaws.com/production/api/ksi/validate' \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"tenant_id\": \"default\"}'"

echo ""
echo -e "${GREEN}Your RiskDash platform should now return REAL compliance results! 🚀${NC}"
echo -e "${BLUE}Expected results:${NC}"
echo "  ✅ Network architecture analysis"
echo "  ✅ Encryption and key management status"
echo "  ✅ Identity and access control review"
echo "  ✅ Monitoring and logging assessment"
echo "  ✅ Change management validation"
