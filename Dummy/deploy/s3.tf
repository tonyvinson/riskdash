resource "aws_s3_bucket" "app_documents" {
  bucket = "${local.prefix}-app-docs"
  tags   = local.common_tags
}

resource "aws_s3_bucket_server_side_encryption_configuration" "app_docs_sse" {
  bucket = aws_s3_bucket.app_documents.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

