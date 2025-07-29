# =============================================================================
# ROOT MODULE OUTPUTS - Reference module outputs, not resources directly
# =============================================================================

output "api_gateway_rest_api_id" {
  description = "ID of the API Gateway REST API"
  value       = module.api_gateway.api_gateway_rest_api_id
}

output "api_gateway_rest_api_arn" {
  description = "ARN of the API Gateway REST API"
  value       = module.api_gateway.api_gateway_rest_api_arn
}

output "api_gateway_stage_arn" {
  description = "ARN of the API Gateway stage"
  value       = module.api_gateway.api_gateway_stage_arn
}

output "api_gateway_invoke_url" {
  description = "The invoke URL for the API Gateway"
  value       = module.api_gateway.api_gateway_invoke_url
}

output "api_gateway_deployment_id" {
  description = "ID of the API Gateway deployment"
  value       = module.api_gateway.api_gateway_deployment_id
}

output "api_lambda_function_arns" {
  description = "ARNs of API Lambda functions"
  value       = module.api_gateway.api_lambda_function_arns
}

output "api_lambda_function_names" {
  description = "Names of API Lambda functions"
  value       = module.api_gateway.api_lambda_function_names
}

output "api_endpoints" {
  description = "Available API endpoints"
  value       = module.api_gateway.api_endpoints
}

output "cloudwatch_log_groups" {
  description = "CloudWatch log groups for API components"
  value       = module.api_gateway.cloudwatch_log_groups
}

output "quick_reference" {
  description = "Quick reference for testing API endpoints"
  value       = module.api_gateway.quick_reference
}

# =============================================================================
# OTHER MODULE OUTPUTS
# =============================================================================

output "lambda_orchestrator_arn" {
  description = "ARN of the KSI orchestrator Lambda function"
  value       = module.lambda.orchestrator_lambda_arn
}

output "dynamodb_tables" {
  description = "DynamoDB table information"
  value = {
    ksi_definitions_table = module.dynamodb.ksi_definitions_table_name
    tenant_ksi_configurations_table = module.dynamodb.tenant_ksi_configurations_table_name
    ksi_execution_history_table = module.dynamodb.ksi_execution_history_table_name
  }
}
