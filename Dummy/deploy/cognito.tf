resource "aws_iam_role" "cognito_sms_role" {
  name = "${local.prefix}-cognito-sms-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          Service = "cognito-idp.amazonaws.com"
        },
        Action = "sts:AssumeRole",
        Condition = {
          StringEquals = {
            "sts:ExternalId" = "MyExternalId-${local.prefix}"
          }
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "cognito_sms_policy" {
  name = "${local.prefix}-cognito-sms-policy"
  role = aws_iam_role.cognito_sms_role.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = ["sns:Publish"],
        Resource = "*"
      }
    ]
  })
}

resource "aws_cognito_user_pool" "main" {
  name = "${local.prefix}-cognito-user-pool"

  alias_attributes         = ["email", "preferred_username"]
  auto_verified_attributes = ["email", "phone_number"]

  mfa_configuration = "OPTIONAL"

  email_configuration {
    email_sending_account = "DEVELOPER"
    from_email_address    = "sarah.vardy@longevityconsulting.com"
    source_arn            = "arn:aws-us-gov:ses:us-gov-east-1:736539455039:identity/sarah.vardy@longevityconsulting.com"
  }

  sms_configuration {
    external_id    = "MyExternalId-${local.prefix}"
    sns_caller_arn = aws_iam_role.cognito_sms_role.arn
  }

  software_token_mfa_configuration {
    enabled = true
  }

  sms_authentication_message = "Your authentication code is {####}"

  verification_message_template {
    default_email_option = "CONFIRM_WITH_CODE"
    email_subject        = "Account Confirmation"
    email_message        = "Your confirmation code is {####}"
  }

  password_policy {
    minimum_length = 8
  }

  schema {
    attribute_data_type = "String"
    name                = "email"
    required            = true
    mutable             = true
    string_attribute_constraints {
      min_length = 1
      max_length = 256
    }
  }

  depends_on = [aws_iam_role_policy.cognito_sms_policy]
}

resource "aws_cognito_user_pool_client" "main" {
  name                           = "${local.prefix}-cognito-user-pool-client"
  user_pool_id                   = aws_cognito_user_pool.main.id
  generate_secret                = false
  prevent_user_existence_errors = "ENABLED"

  access_token_validity         = 1
  id_token_validity             = 1
  refresh_token_validity        = 90

  explicit_auth_flows = [
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_USER_PASSWORD_AUTH",
    "ALLOW_ADMIN_USER_PASSWORD_AUTH"
  ]
}


output "cognito_user_pool_id" {
  value = aws_cognito_user_pool.main.id
}

output "user_pool_client_id" {
  value = aws_cognito_user_pool_client.main.id
}
