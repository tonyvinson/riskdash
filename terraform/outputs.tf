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

output "orchestrator_lambda_arn" {
  description = "ARN of the KSI orchestrator Lambda function"
  value       = module.lambda.orchestrator_lambda_arn
}

output "orchestrator_lambda_name" {
  description = "Name of the KSI orchestrator Lambda function"
  value       = module.lambda.orchestrator_lambda_name
}

output "validator_lambda_arns" {
  description = "ARNs of all KSI validator Lambda functions"
  value       = module.lambda.validator_lambda_arns
}

output "eventbridge_rule_arn" {
  description = "ARN of the EventBridge rule for scheduling"
  value       = module.eventbridge.eventbridge_rule_arn
}

output "ksi_orchestrator_role_arn" {
  description = "ARN of the IAM role for KSI orchestrator"
  value       = module.lambda.orchestrator_role_arn
}

# API Gateway outputs 
output "api_gateway" {
  description = "API Gateway information"
  value = {
    api_id       = module.api_gateway.api_gateway_rest_api_id
    api_arn      = module.api_gateway.api_gateway_rest_api_arn
    invoke_url   = module.api_gateway.api_gateway_invoke_url
    stage_arn    = module.api_gateway.api_gateway_stage_arn
    endpoints    = module.api_gateway.api_endpoints
  }
}

# Quick reference URLs 
output "quick_reference" {
  description = "Quick reference information"
  value = {
    api_base_url = module.api_gateway.api_gateway_invoke_url
    validate_url = "${module.api_gateway.api_gateway_invoke_url}/api/ksi/validate"
    executions_url = "${module.api_gateway.api_gateway_invoke_url}/api/ksi/executions"
    results_url = "${module.api_gateway.api_gateway_invoke_url}/api/ksi/results"
    orchestrator_function = module.lambda.orchestrator_lambda_name
  }
}

# =============================================================================
# ADD THESE TO YOUR terraform/outputs.tf FILE:
# =============================================================================

# Tenant Management Outputs
output "tenant_metadata_table_name" {
  description = "Name of the tenant metadata table"
  value       = module.tenant_management.tenant_metadata_table_name
}

output "tenant_onboarding_api_function_name" {
  description = "Name of the tenant onboarding API function"
  value       = module.tenant_management.tenant_onboarding_api_function_name
}

output "cross_account_validator_function_name" {
  description = "Name of the cross-account validator function"
  value       = module.tenant_management.cross_account_validator_function_name
}

output "riskuity_account_id" {
  description = "Riskuity's AWS Account ID for customer role setup"
  value       = module.tenant_management.riskuity_account_id
}
