[
    {
        "name": "api",
        "image": "${app_image}",
        "essential": true,
        "memoryReservation": 8192,
        "environment": [
            {"name": "PATH", "value": "/project/venv/bin:/root/.local/bin:$PATH"},
            {"name": "RDS_DB_NAME", "value": "${db_name}"},
            {"name": "RDS_USERNAME", "value": "${db_user}"},
            {"name": "RDS_PASSWORD", "value": "${db_password}"},
            {"name": "RDS_HOSTNAME", "value": "${db_host}"},
            {"name": "RDS_PORT", "value": "5432"},
            {"name": "ALLOWED_ORIGINS", "value": "${allowed_hosts}"},
            {"name": "AWS_ACCESS_KEY_ID", "value": "${aws_access_key_id}"},
            {"name": "AWS_SECRET_ACCESS_KEY", "value": "${aws_secret_access_key}"},
            {"name": "AWS_DEFAULT_REGION", "value": "${aws_default_region}"},
            {"name": "S3_STORAGE_BUCKET_NAME", "value": "${s3_storage_bucket_name}"},
            {"name": "S3_STORAGE_BUCKET_REGION", "value": "${s3_storage_bucket_name}"},
            {"name": "COGNITO_ACCESS_KEY_ID", "value": "${aws_access_key_id}"},
            {"name": "COGNITO_SECRET_ACCESS_KEY", "value": "${aws_secret_access_key}"},
            {"name": "COGNITO_USER_POOL_ID", "value": "${cognito_user_pool_id}"},
            {"name": "COGNITO_WEB_CLIENT_ID", "value": "${cognito_web_client_id}"},
            {"name": "SMTP_USERNAME", "value": "${smtp_username}"},
            {"name": "SMTP_PASSWORD", "value": "${smtp_password}"},
            {"name": "SMTP_HOST", "value": "${smtp_host}"},
            {"name": "SMTP_PORT", "value": "${smtp_port}"},
            {"name": "SMTP_SENDER_EMAIL", "value": "${smtp_sender_email}"},
            {"name": "SMTP_SENDER_NAME", "value": "${smtp_sender_name}"},
            {"name": "FRONTEND_SERVER_URL", "value": "${frontend_server_url}"},
            {"name": "FEDRISK_JWT_SECRET_KEY", "value": "${fedrisk_jwt_secret_key}"},
            {"name": "STRIPE_SECRET_KEY", "value": "${stripe_secret_key}"},
            {"name": "STRIPE_PUBLIC_KEY", "value": "${stripe_public_key}"},
            {"name": "ENVIRONMENT", "value": "${environment}"},
            {"name": "AWS_SES_REGION", "value": "${aws_ses_region}"},
            {"name": "AWS_USER", "value": "${aws_user}"},
            {"name": "AWS_SES_VERIFIED_MAIL", "value": "${aws_ses_verified_mail}"},
            {"name": "RECAPTCHA_SECRET_KEY", "value": "${recaptcha_secret_key}"}
        ],
        "logConfiguration": {
            "logDriver": "awslogs",
            "options": {
                "awslogs-group": "${log_group_name}",
                "awslogs-region": "${log_group_region}",
                "awslogs-stream-prefix": "api"
            }
        },
        "portMappings": [
            {
                "containerPort": 8000,
                "hostPort": 8000,
                "protocol": "tcp"
            }
        ],
        "mountPoints": []
    }
]