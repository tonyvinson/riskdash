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
  default     = 300
}

variable "lambda_memory_size" {
  description = "Lambda memory size in MB"
  type        = number
  default     = 256
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

variable "tenant_metadata_table" {
  description = "Name of tenant metadata table"
  type        = string
}

variable "tenant_metadata_table_arn" {
  description = "ARN of tenant metadata table"
  type        = string
}
