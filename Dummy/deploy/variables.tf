variable "prefix" {
  default = "frapi"
}

variable "project" {
  default = "fedrisk-api"
}

variable "contact" {
  default = "Sarah.Vardy@longevityconsulting.com"
}

variable "db_username" {
  description = "Username for the Postgres Database Instance"
}

variable "db_password" {
  description = "Password for the Postgres Database Instance"
}

variable "bastion_key_name" {
  description = "Name of the key pair to use for the bastion instance"
  default     = "frapiccino-jumphost-key"
}

variable "ecr_image_api" {
  description = "ECR image to use for the API"
  default     = "736539455039.dkr.ecr.us-gov-east-1.amazonaws.com/fedrisk-api:V1.28.3"
}

variable "aws_access_key_id" {
  description = "aws_access_key_id"
}

variable "aws_secret_access_key" {
  description = "aws_secret_access_key"
}

variable "fedrisk_jwt_secret_key" {
  description = "secret key for jwt"
  default     = "alkasdflkja88837377"
}

variable "smtp_sender_email" {
  description = "email address to be used for from address"
  default     = "support@fedrisk.com"
}

variable "smtp_sender_name" {
  description = "Name to be used for sending emails from"
  default     = "FedRisk System"
}

variable "smtp_username" {
  description = "SMTP User to authenticate with SES"
}

variable "smtp_password" {
  description = "SMTP Password to authenticate with SES"
}

variable "smtp_host" {
  description = "SMTP Host for SES"
}

variable "smtp_port" {
  description = "SMTP Port for SES"
}

variable "frontend_server_url" {
  description = "URL for the frontend server"
}

variable "stripe_secret_key" {
  description = "Secret for using Stripe"
}

variable "stripe_public_key" {
  description = "Public key for using Stripe"
}

variable "allowed_origins" {
  description = "Allowed origins"
}

variable "environment" {
  description = "Environment - production, staging, dev"
}

variable "aws_user" {
  description = "AWS user for SES"
}

variable "aws_ses_region" {
  description = "AWS SES region"
}

variable "aws_ses_verified_mail" {
  description = "AWS SES verified email address"
}

variable "cognito_user_pool_id" {
  description = "AWS Cognito user pool ID"
}

variable "cognito_web_client_id" {
  description = "AWS Cognito web client ID"
}

variable "recaptcha_secret_key" {
  description = "Site secret key for Google reCAPTCHA"
}

variable "sms_external_id" {
  description = "External ID used by Cognito to call SNS"
  type        = string
}

variable "sns_caller_arn" {
  description = "ARN of the IAM role that Cognito uses to send SMS"
  type        = string
}
