output "orchestrator_lambda_arn" {
  description = "ARN of the KSI orchestrator Lambda function"
  value       = aws_lambda_function.ksi_orchestrator.arn
}

output "orchestrator_lambda_name" {
  description = "Name of the KSI orchestrator Lambda function"
  value       = aws_lambda_function.ksi_orchestrator.function_name
}

output "orchestrator_role_arn" {
  description = "ARN of the orchestrator IAM role"
  value       = aws_iam_role.ksi_orchestrator_role.arn
}

output "validator_lambda_arns" {
  description = "ARNs of validator Lambda functions"
  value       = { for k, v in aws_lambda_function.ksi_validators : k => v.arn }
}

output "validator_lambda_names" {
  description = "Names of validator Lambda functions"
  value       = { for k, v in aws_lambda_function.ksi_validators : k => v.function_name }
}
