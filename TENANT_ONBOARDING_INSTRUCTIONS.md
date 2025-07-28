# RiskDash Tenant Onboarding Instructions

## Step 1: Create IAM Role in Your AWS Account

Create an IAM role in your AWS account that RiskDash can assume for compliance validation.

### 1.1 Create the Role

```bash
aws iam create-role \
    --role-name RiskDashValidationRole \
    --assume-role-policy-document file://tenant_validation_role_template.json \
    --description "Role for RiskDash FedRAMP compliance validation"
```

### 1.2 Attach Permissions Policy

```bash
aws iam put-role-policy \
    --role-name RiskDashValidationRole \
    --policy-name RiskDashValidationPolicy \
    --policy-document file://tenant_validation_permissions.json
```

### 1.3 Get Role ARN

```bash
aws iam get-role --role-name RiskDashValidationRole --query 'Role.Arn' --output text
```

## Step 2: Register with RiskDash

Use the Role ARN from Step 1.3 when registering your tenant:

```bash
curl -X POST "https://your-riskdash-api/api/tenant/onboard" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "your-organization-id",
    "account_id": "123456789012",
    "role_arn": "arn:aws-us-gov:iam::123456789012:role/RiskDashValidationRole",
    "external_id": "RiskDash-FedRAMP-Validation",
    "contact_email": "security@yourorg.gov"
  }'
```

## Step 3: Test Validation

After registration, test the validation:

```bash
curl -X POST "https://your-riskdash-api/api/ksi/validate" \
  -H "Content-Type: application/json" \
  -d '{"tenant_id": "your-organization-id"}'
```

## Security Notes

- The role only grants READ permissions for compliance validation
- External ID provides additional security for role assumption
- RiskDash can only access your account when performing validations
- All validations are logged in CloudTrail

## What Gets Validated

- **Network Architecture**: VPCs, subnets, Route53
- **Services**: KMS keys, Secrets Manager, S3 encryption
- **Identity & Access**: IAM users, roles, policies
- **Monitoring & Logging**: CloudTrail, CloudWatch, SNS
- **Change Management**: AWS Config, CloudFormation
