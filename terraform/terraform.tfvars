aws_region   = "us-gov-west-1"
environment  = "production"
project_name = "riskuity-ksi-validator"

# Lambda Configuration
lambda_timeout     = 300
lambda_memory_size = 256

# API Gateway Configuration
api_cors_allow_origin       = "*"
api_throttling_rate_limit   = 1000
api_throttling_burst_limit  = 2000
