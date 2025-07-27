# KSI Definitions Table
resource "aws_dynamodb_table" "ksi_definitions" {
  name           = "${var.project_name}-ksi-definitions-${var.environment}"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "ksi_id"
  range_key      = "version"
  
  attribute {
    name = "ksi_id"
    type = "S"
  }
  
  attribute {
    name = "version"
    type = "S"
  }
  
  point_in_time_recovery {
    enabled = true
  }
  
  server_side_encryption {
    enabled = true
  }
  
  tags = {
    Name = "KSI Definitions"
    Purpose = "Store KSI validation rule definitions"
  }
}

# Tenant KSI Configurations Table
resource "aws_dynamodb_table" "tenant_ksi_configurations" {
  name           = "${var.project_name}-tenant-ksi-configurations-${var.environment}"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "tenant_id"
  range_key      = "ksi_id"
  
  attribute {
    name = "tenant_id"
    type = "S"
  }
  
  attribute {
    name = "ksi_id"
    type = "S"
  }
  
  point_in_time_recovery {
    enabled = true
  }
  
  server_side_encryption {
    enabled = true
  }
  
  tags = {
    Name = "Tenant KSI Configurations"
    Purpose = "Store tenant-specific KSI validation configurations"
  }
}

# KSI Execution History Table
resource "aws_dynamodb_table" "ksi_execution_history" {
  name           = "${var.project_name}-ksi-execution-history-${var.environment}"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "execution_id"
  range_key      = "timestamp"
  
  attribute {
    name = "execution_id"
    type = "S"
  }
  
  attribute {
    name = "timestamp"
    type = "S"
  }
  
  # Global Secondary Index for querying by tenant
  attribute {
    name = "tenant_id"
    type = "S"
  }
  
  global_secondary_index {
    name     = "tenant-timestamp-index"
    hash_key = "tenant_id"
    range_key = "timestamp"
    projection_type = "ALL"
  }
  
  # TTL for automatic cleanup of old execution records
  ttl {
    attribute_name = "ttl"
    enabled        = true
  }
  
  point_in_time_recovery {
    enabled = true
  }
  
  server_side_encryption {
    enabled = true
  }
  
  tags = {
    Name = "KSI Execution History"
    Purpose = "Store historical KSI validation execution results"
  }
}
