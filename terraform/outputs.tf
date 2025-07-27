# DynamoDB Tables
output "ksi_definitions_table_name" {
  description = "Name of the KSI definitions DynamoDB table"
  value       = module.dynamodb.ksi_definitions_table_name
}

output "tenant_ksi_configurations_table_name" {
  description = "Name of the tenant KSI configurations DynamoDB table"
  value       = module.dynamodb.tenant_ksi_configurations_table_name
}

output "ksi_execution_history_table_name" {
  description = "Name of the KSI execution history DynamoDB table"
  value       = module.dynamodb.ksi_execution_history_table_name
}

# Lambda Functions
output "orchestrator_lambda_arn" {
  description = "ARN of the KSI orchestrator Lambda function"
  value       = module.lambda.orchestrator_lambda_arn
}

output "validator_lambda_arns" {
  description = "ARNs of all KSI validator Lambda functions"
  value       = module.lambda.validator_lambda_arns
}

# API Gateway
output "api_gateway" {
  description = "API Gateway information"
  value = {
    id         = module.api_gateway.api_gateway_id
    invoke_url = module.api_gateway.api_gateway_invoke_url
    endpoints = {
      validate_url   = module.api_gateway.validate_endpoint_url
      executions_url = module.api_gateway.executions_endpoint_url
      results_url    = module.api_gateway.results_endpoint_url
    }
  }
}

# EventBridge
output "eventbridge_rule_arn" {
  description = "ARN of the EventBridge rule for scheduled validations"
  value       = module.eventbridge.eventbridge_rule_arn
}

# Quick Reference
output "quick_reference" {
  description = "Quick reference for key endpoints and functions"
  value = {
    api_base_url = module.api_gateway.api_gateway_invoke_url
    validate_url = module.api_gateway.validate_endpoint_url
    executions_url = module.api_gateway.executions_endpoint_url
    results_url = module.api_gateway.results_endpoint_url
    orchestrator_function = module.lambda.orchestrator_lambda_function_name
  }
}

# Account Information
output "riskuity_account_id" {
  description = "Current AWS account ID"
  value       = data.aws_caller_identity.current.account_id
}

# Tenant Management Outputs (if module exists)
output "tenant_management_api_url" {
  description = "Tenant Management API Gateway URL"
  value       = try(module.tenant_management.api_gateway_url, "Not deployed")
}

output "tenant_onboarding_instructions" {
  description = "Instructions for tenant onboarding"
  value = try({
    api_url = module.tenant_management.api_gateway_url
    endpoints = {
      generate_role_instructions = "${module.tenant_management.api_gateway_url}/api/tenant/generate-role-instructions"
      test_connection = "${module.tenant_management.api_gateway_url}/api/tenant/test-connection"
      onboard = "${module.tenant_management.api_gateway_url}/api/tenant/onboard"
      list = "${module.tenant_management.api_gateway_url}/api/tenant/list"
    }
  }, "Tenant management not deployed")
}

output "cross_account_validator_function_name" {
  description = "Cross-account validator Lambda function name"
  value       = try(module.tenant_management.cross_account_validator_function_name, "Not deployed")
}
