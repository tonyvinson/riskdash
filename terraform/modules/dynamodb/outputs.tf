output "ksi_definitions_table_name" {
  description = "Name of the KSI definitions table"
  value       = aws_dynamodb_table.ksi_definitions.name
}

output "ksi_definitions_table_arn" {
  description = "ARN of the KSI definitions table"
  value       = aws_dynamodb_table.ksi_definitions.arn
}

output "tenant_ksi_configurations_table_name" {
  description = "Name of the tenant KSI configurations table"
  value       = aws_dynamodb_table.tenant_ksi_configurations.name
}

output "tenant_ksi_configurations_table_arn" {
  description = "ARN of the tenant KSI configurations table"
  value       = aws_dynamodb_table.tenant_ksi_configurations.arn
}

output "ksi_execution_history_table_name" {
  description = "Name of the KSI execution history table"
  value       = aws_dynamodb_table.ksi_execution_history.name
}

output "ksi_execution_history_table_arn" {
  description = "ARN of the KSI execution history table"
  value       = aws_dynamodb_table.ksi_execution_history.arn
}
