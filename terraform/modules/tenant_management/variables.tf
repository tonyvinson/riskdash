variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "tenant_ksi_configurations_table_name" {
  description = "Name of the existing tenant KSI configurations table"
  type        = string
}

variable "tenant_ksi_configurations_table_arn" {
  description = "ARN of the existing tenant KSI configurations table"
  type        = string
}

variable "ksi_execution_history_table_name" {
  description = "Name of the existing KSI execution history table"
  type        = string
}

variable "ksi_execution_history_table_arn" {
  description = "ARN of the existing KSI execution history table"
  type        = string
}
