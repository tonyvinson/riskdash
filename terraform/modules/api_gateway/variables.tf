variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "lambda_runtime" {
  description = "Python runtime version"
  type        = string
  default     = "python3.9"
}

variable "lambda_timeout" {
  description = "Lambda timeout in seconds"
  type        = number
  default     = 30
}

variable "lambda_memory_size" {
  description = "Lambda memory size in MB"
  type        = number
  default     = 256
}

variable "orchestrator_lambda_arn" {
  description = "ARN of the KSI orchestrator Lambda function"
  type        = string
}

variable "ksi_definitions_table" {
  description = "Name of KSI definitions table"
  type        = string
}

variable "ksi_definitions_table_arn" {
  description = "ARN of KSI definitions table"
  type        = string
}

variable "tenant_ksi_configurations_table" {
  description = "Name of tenant KSI configurations table"
  type        = string
}

variable "tenant_ksi_configurations_table_arn" {
  description = "ARN of tenant KSI configurations table"
  type        = string
}

variable "ksi_execution_history_table" {
  description = "Name of KSI execution history table"
  type        = string
}

variable "ksi_execution_history_table_arn" {
  description = "ARN of KSI execution history table"
  type        = string
}

variable "api_cors_allow_origin" {
  description = "CORS allow origin for API Gateway"
  type        = string
  default     = "*"
}

variable "api_throttling_rate_limit" {
  description = "API Gateway throttling rate limit (requests per second)"
  type        = number
  default     = 1000
}

variable "api_throttling_burst_limit" {
  description = "API Gateway throttling burst limit"
  type        = number
  default     = 2000
}
