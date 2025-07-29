# =============================================================================
# CORE PROJECT VARIABLES
# =============================================================================

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "riskuity-ksi-validator"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-gov-west-1"
}

# =============================================================================
# LAMBDA CONFIGURATION
# =============================================================================

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

# =============================================================================
# API GATEWAY CONFIGURATION
# =============================================================================

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

# =============================================================================
# EVENTBRIDGE CONFIGURATION
# =============================================================================

variable "validation_schedule_expression" {
  description = "Schedule expression for KSI validation (CloudWatch Events)"
  type        = string
  default     = "rate(24 hours)"
}

variable "validation_schedule_enabled" {
  description = "Enable/disable the KSI validation schedule"
  type        = bool
  default     = true
}

# =============================================================================
# TAGS
# =============================================================================

variable "default_tags" {
  description = "Default tags to apply to all resources"
  type        = map(string)
  default = {
    Project     = "KSI-Validator"
    Company     = "Riskuity"
    Purpose     = "FedRAMP-20X-Compliance"
  }
}
