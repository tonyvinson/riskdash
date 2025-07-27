#!/bin/bash

echo "🔧 Fixing AWS GovCloud Partition Issues in Tenant Management"
echo "=========================================================="

# Check if tenant management module exists
if [ ! -f "terraform/modules/tenant_management/main.tf" ]; then
    echo "❌ Tenant management module not found"
    exit 1
fi

echo "✅ Found tenant management module"

# First, let's fix the IAM policy to use the correct partition
echo "📝 Fixing IAM policy partition for GovCloud..."

# Create a temporary file to hold the corrected main.tf
cat > terraform/modules/tenant_management/main.tf << 'EOF'
# Tenant Management Module - integrates with existing KSI Validator architecture

# Get current AWS account info and region
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# Determine the correct partition based on region
locals {
  aws_partition = startswith(data.aws_region.current.name, "us-gov-") ? "aws-us-gov" : "aws"
}

# Tenant Metadata Table - NEW for SaaS functionality
resource "aws_dynamodb_table" "tenant_metadata" {
  name           = "${var.project_name}-tenant-metadata-${var.environment}"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "tenant_id"
  
  attribute {
    name = "tenant_id"
    type = "S"
  }
  
  # Global Secondary Index for querying by organization type
  attribute {
    name = "tenant_type"
    type = "S"
  }
  
  attribute {
    name = "onboarding_status"
    type = "S"
  }
  
  global_secondary_index {
    name     = "tenant-type-index"
    hash_key = "tenant_type"
    range_key = "onboarding_status"
    projection_type = "ALL"
  }
  
  point_in_time_recovery {
    enabled = true
  }
  
  server_side_encryption {
    enabled = true
  }
  
  tags = {
    Name = "Tenant Metadata"
    Purpose = "Store comprehensive tenant information for SaaS KSI validation"
  }
}

# IAM Role for Tenant Onboarding API
resource "aws_iam_role" "tenant_onboarding_role" {
  name = "${var.project_name}-tenant-onboarding-role-${var.environment}"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
  
  tags = {
    Name = "Tenant Onboarding Role"
    Purpose = "Lambda execution role for tenant onboarding API"
  }
}

# IAM Policy for Tenant Metadata Access
resource "aws_iam_policy" "tenant_metadata_policy" {
  name        = "${var.project_name}-tenant-metadata-policy-${var.environment}"
  description = "Policy for accessing tenant metadata table"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:BatchGetItem",
          "dynamodb:BatchWriteItem"
        ]
        Resource = [
          aws_dynamodb_table.tenant_metadata.arn,
          "${aws_dynamodb_table.tenant_metadata.arn}/index/*",
          var.tenant_ksi_configurations_table_arn,
          "${var.tenant_ksi_configurations_table_arn}/index/*"
        ]
      }
    ]
  })
}

# IAM Policy for Cross-Account Role Assumption - FIXED FOR GOVCLOUD
resource "aws_iam_policy" "cross_account_assume_policy" {
  name        = "${var.project_name}-cross-account-assume-policy-${var.environment}"
  description = "Policy for assuming roles in customer accounts"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sts:AssumeRole"
        ]
        Resource = "arn:${local.aws_partition}:iam::*:role/RiskuityKSIValidatorRole"
        Condition = {
          StringEquals = {
            "sts:ExternalId" = "riskuity-*"
          }
        }
      }
    ]
  })
}

# Attach policies to tenant onboarding role
resource "aws_iam_role_policy_attachment" "tenant_onboarding_basic" {
  role       = aws_iam_role.tenant_onboarding_role.name
  policy_arn = "arn:${local.aws_partition}:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "tenant_onboarding_metadata" {
  role       = aws_iam_role.tenant_onboarding_role.name
  policy_arn = aws_iam_policy.tenant_metadata_policy.arn
}

resource "aws_iam_role_policy_attachment" "tenant_onboarding_assume" {
  role       = aws_iam_role.tenant_onboarding_role.name
  policy_arn = aws_iam_policy.cross_account_assume_policy.arn
}

# Lambda Function for Tenant Onboarding API
resource "aws_lambda_function" "tenant_onboarding_api" {
  filename         = "${path.module}/../../lambda_packages/tenant_onboarding_api.zip"
  function_name    = "${var.project_name}-tenant-onboarding-api-${var.environment}"
  role            = aws_iam_role.tenant_onboarding_role.arn
  handler         = "tenant_onboarding_api.lambda_handler"
  runtime         = "python3.11"
  timeout         = 30
  memory_size     = 256
  source_code_hash = filebase64sha256("${path.module}/../../lambda_packages/tenant_onboarding_api.zip")
  
  environment {
    variables = {
      TENANT_METADATA_TABLE = aws_dynamodb_table.tenant_metadata.name
      TENANT_KSI_CONFIGURATIONS_TABLE = var.tenant_ksi_configurations_table_name
      RISKUITY_ACCOUNT_ID = data.aws_caller_identity.current.account_id
      ENVIRONMENT = var.environment
      PROJECT_NAME = var.project_name
    }
  }
  
  tags = {
    Name = "Tenant Onboarding API"
    Purpose = "Handle tenant registration and AWS role setup"
  }
  
  depends_on = [aws_iam_role_policy_attachment.tenant_onboarding_basic]
}

# IAM Role for Cross-Account KSI Validator
resource "aws_iam_role" "cross_account_validator_role" {
  name = "${var.project_name}-cross-account-validator-role-${var.environment}"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
  
  tags = {
    Name = "Cross-Account Validator Role"
    Purpose = "Lambda execution role for cross-account KSI validation"
  }
}

# Enhanced Cross-Account KSI Validator
resource "aws_lambda_function" "cross_account_ksi_validator" {
  filename         = "${path.module}/../../lambda_packages/cross_account_ksi_validator.zip"
  function_name    = "${var.project_name}-cross-account-validator-${var.environment}"
  role            = aws_iam_role.cross_account_validator_role.arn
  handler         = "cross_account_ksi_validator.lambda_handler"
  runtime         = "python3.11"
  timeout         = 900  # 15 minutes for cross-account operations
  memory_size     = 512
  source_code_hash = filebase64sha256("${path.module}/../../lambda_packages/cross_account_ksi_validator.zip")
  
  environment {
    variables = {
      TENANT_METADATA_TABLE = aws_dynamodb_table.tenant_metadata.name
      TENANT_KSI_CONFIGURATIONS_TABLE = var.tenant_ksi_configurations_table_name
      KSI_EXECUTION_HISTORY_TABLE = var.ksi_execution_history_table_name
      RISKUITY_ACCOUNT_ID = data.aws_caller_identity.current.account_id
      ENVIRONMENT = var.environment
      PROJECT_NAME = var.project_name
    }
  }
  
  tags = {
    Name = "Cross-Account KSI Validator"
    Purpose = "Validate KSIs across customer AWS accounts"
  }
  
  depends_on = [aws_iam_role_policy_attachment.cross_account_validator_basic]
}

# Attach policies to cross-account validator role
resource "aws_iam_role_policy_attachment" "cross_account_validator_basic" {
  role       = aws_iam_role.cross_account_validator_role.name
  policy_arn = "arn:${local.aws_partition}:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "cross_account_validator_metadata" {
  role       = aws_iam_role.cross_account_validator_role.name
  policy_arn = aws_iam_policy.tenant_metadata_policy.arn
}

resource "aws_iam_role_policy_attachment" "cross_account_validator_assume" {
  role       = aws_iam_role.cross_account_validator_role.name
  policy_arn = aws_iam_policy.cross_account_assume_policy.arn
}

# EventBridge Rule for Scheduled Multi-Tenant Validation
resource "aws_cloudwatch_event_rule" "scheduled_multi_tenant_validation" {
  name        = "${var.project_name}-multi-tenant-validation-${var.environment}"
  description = "Trigger KSI validation for all active tenants"
  
  schedule_expression = "rate(1 hour)"  # Run every hour
  
  tags = {
    Name = "Scheduled Multi-Tenant Validation"
    Purpose = "Automated validation scheduling for all tenants"
  }
}

resource "aws_cloudwatch_event_target" "cross_account_validator_target" {
  rule      = aws_cloudwatch_event_rule.scheduled_multi_tenant_validation.name
  target_id = "CrossAccountValidatorTarget"
  arn       = aws_lambda_function.cross_account_ksi_validator.arn
  
  input = jsonencode({
    "trigger_source" = "scheduled"
    "validate_all_tenants" = true
  })
}

resource "aws_lambda_permission" "allow_eventbridge_cross_account" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.cross_account_ksi_validator.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.scheduled_multi_tenant_validation.arn
}
EOF

echo "✅ Fixed tenant management module for GovCloud"

# Also update the Lambda function to generate proper GovCloud ARNs
echo "📝 Updating tenant onboarding Lambda for GovCloud ARNs..."

cat > terraform/lambda_packages/tenant_onboarding_api.py << 'EOF'
import json
import boto3
import logging
from datetime import datetime, timezone
import os
import uuid

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
sts_client = boto3.client('sts')

TENANT_METADATA_TABLE = os.environ['TENANT_METADATA_TABLE']
RISKUITY_ACCOUNT_ID = os.environ['RISKUITY_ACCOUNT_ID']

# Determine AWS partition based on region
def get_aws_partition():
    try:
        region = boto3.Session().region_name
        if region and region.startswith('us-gov-'):
            return 'aws-us-gov'
        else:
            return 'aws'
    except:
        return 'aws'

def lambda_handler(event, context):
    """
    Tenant onboarding API handler
    """
    try:
        logger.info(f"Tenant onboarding request: {json.dumps(event)}")
        
        # Parse request
        if 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            body = event
        
        action = body.get('action', 'onboard')
        
        if action == 'generate_role_instructions':
            return generate_role_instructions(body)
        elif action == 'test_connection':
            return test_connection(body)
        elif action == 'onboard':
            return onboard_tenant(body)
        elif action == 'list':
            return list_tenants(body)
        else:
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({'error': 'Invalid action'})
            }
            
    except Exception as e:
        logger.error(f"Error in tenant onboarding: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'error': str(e)})
        }

def generate_role_instructions(body):
    """Generate IAM role setup instructions with correct partition"""
    tenant_id = body.get('tenantId', f"tenant-{int(datetime.now().timestamp())}")
    external_id = f"riskuity-{tenant_id}-{datetime.now().strftime('%Y%m%d')}"
    partition = get_aws_partition()
    
    instructions = {
        "role_name": "RiskuityKSIValidatorRole",
        "external_id": external_id,
        "riskuity_account_id": RISKUITY_ACCOUNT_ID,
        "role_arn_template": f"arn:{partition}:iam::YOUR_ACCOUNT_ID:role/RiskuityKSIValidatorRole",
        "cli_commands": [
            f"""aws iam create-role --role-name RiskuityKSIValidatorRole --assume-role-policy-document '{{"Version":"2012-10-17","Statement":[{{"Effect":"Allow","Principal":{{"AWS":"arn:{partition}:iam::{RISKUITY_ACCOUNT_ID}:root"}},"Action":"sts:AssumeRole","Condition":{{"StringEquals":{{"sts:ExternalId":"{external_id}"}}}}}}]}}'""",
            f"aws iam attach-role-policy --role-name RiskuityKSIValidatorRole --policy-arn arn:{partition}:iam::aws:policy/SecurityAudit",
            f"aws iam attach-role-policy --role-name RiskuityKSIValidatorRole --policy-arn arn:{partition}:iam::aws:policy/ReadOnlyAccess"
        ]
    }
    
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Content-Type': 'application/json'
        },
        'body': json.dumps(instructions)
    }

def test_connection(body):
    """Test cross-account connection"""
    role_arn = body.get('roleArn')
    external_id = body.get('externalId')
    
    if not role_arn or not external_id:
        return {
            'statusCode': 400,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'error': 'roleArn and externalId required'})
        }
    
    try:
        # Test assume role
        response = sts_client.assume_role(
            RoleArn=role_arn,
            RoleSessionName=f"riskuity-test-{int(datetime.now().timestamp())}",
            ExternalId=external_id,
            DurationSeconds=3600
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'connection_status': 'SUCCESS',
                'message': 'Cross-account role assumption successful'
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'connection_status': 'FAILED',
                'error': str(e)
            })
        }

def onboard_tenant(body):
    """Complete tenant onboarding"""
    table = dynamodb.Table(TENANT_METADATA_TABLE)
    
    # Generate tenant ID
    tenant_id = f"tenant-{int(datetime.now().timestamp())}"
    
    # Create tenant metadata record
    tenant_data = {
        'tenant_id': tenant_id,
        'tenant_type': 'federal_customer',
        'onboarding_status': 'active',
        'organization': body.get('organization', {}),
        'contact_info': body.get('contacts', {}),
        'aws_configuration': body.get('awsAccounts', {}),
        'compliance_profile': body.get('compliance', {}),
        'ksi_configuration': body.get('preferences', {}),
        'metadata': {
            'created_date': datetime.now(timezone.utc).isoformat(),
            'created_by': 'onboarding_api',
            'status': 'active'
        }
    }
    
    # Save to DynamoDB
    table.put_item(Item=tenant_data)
    
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Content-Type': 'application/json'
        },
        'body': json.dumps({
            'tenant_id': tenant_id,
            'status': 'success',
            'message': 'Tenant onboarded successfully'
        })
    }

def list_tenants(body):
    """List all tenants"""
    try:
        table = dynamodb.Table(TENANT_METADATA_TABLE)
        
        response = table.scan()
        tenants = response.get('Items', [])
        
        # Format tenants for frontend display
        formatted_tenants = []
        for tenant in tenants:
            formatted_tenants.append({
                'tenant_id': tenant.get('tenant_id'),
                'display_name': tenant.get('organization', {}).get('name', tenant.get('tenant_id', 'Unknown')),
                'organization_type': tenant.get('organization', {}).get('type', 'unknown'),
                'status': tenant.get('onboarding_status', 'unknown'),
                'created_date': tenant.get('metadata', {}).get('created_date')
            })
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'tenants': formatted_tenants,
                'count': len(formatted_tenants)
            })
        }
        
    except Exception as e:
        logger.error(f"Error listing tenants: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'error': str(e)})
        }
EOF

echo "✅ Updated tenant onboarding Lambda for GovCloud"

# Re-package the Lambda function
echo "📦 Re-packaging tenant onboarding Lambda..."
cd terraform/lambda_packages
rm -f tenant_onboarding_api.zip
zip tenant_onboarding_api.zip tenant_onboarding_api.py
cd ../..

echo ""
echo "🎉 GovCloud Partition Fix Complete!"
echo ""
echo "📋 What was fixed:"
echo "   ✅ IAM policy ARNs now use correct partition (aws-us-gov)"
echo "   ✅ Lambda IAM role attachments use correct partition"  
echo "   ✅ Tenant onboarding Lambda generates GovCloud ARNs"
echo "   ✅ Added proper CORS headers to all responses"
echo "   ✅ Added tenant list functionality"
echo ""
echo "🚀 Next Steps:"
echo "1. Run: cd terraform && terraform apply"
echo "2. Your deployment should now succeed!"
echo ""
echo "✨ Ready for AWS GovCloud deployment!"
