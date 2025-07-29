resource "aws_dynamodb_table" "fedrisk_s3_uploads" {
  name         = "Fedrisk_S3_uploads_${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "upload_data"

  attribute {
    name = "upload_data"
    type = "S"
  }

  tags = {
    Environment = var.environment
    Purpose     = "ClamAV Scan Logging"
  }
}