output "tenant_metadata_table_name" {
  description = "Name of the tenant metadata table"
  value       = aws_dynamodb_table.tenant_metadata.name
}

output "tenant_metadata_table_arn" {
  description = "ARN of the tenant metadata table"
  value       = aws_dynamodb_table.tenant_metadata.arn
}

output "tenant_onboarding_api_function_name" {
  description = "Name of the tenant onboarding API function"
  value       = aws_lambda_function.tenant_onboarding_api.function_name
}

output "tenant_onboarding_api_function_arn" {
  description = "ARN of the tenant onboarding API function"
  value       = aws_lambda_function.tenant_onboarding_api.arn
}

output "cross_account_validator_function_name" {
  description = "Name of the cross-account validator function"
  value       = aws_lambda_function.cross_account_ksi_validator.function_name
}

output "cross_account_validator_function_arn" {
  description = "ARN of the cross-account validator function"
  value       = aws_lambda_function.cross_account_ksi_validator.arn
}

output "riskuity_account_id" {
  description = "Riskuity's AWS Account ID for customer role setup"
  value       = data.aws_caller_identity.current.account_id
}
