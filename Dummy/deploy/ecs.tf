resource "aws_ecs_cluster" "main" {
  name = "${local.prefix}-ecs-cluster"

  tags = local.common_tags
}

resource "aws_iam_policy" "task_execution_role_policy" {
  name        = "${local.prefix}-task-execution-role-policy"
  path        = "/"
  description = "Allow retrieving of images and adding to logs"
  policy      = file("./templates/ecs/task-exec-role.json")
}

resource "aws_iam_role" "task_execution_role" {
  name               = "${local.prefix}-task-execution-role"
  assume_role_policy = file("./templates/ecs/assume-role-policy.json")

  tags = local.common_tags

}

resource "aws_iam_policy_attachment" "task_execution_role_policy_attachment" {
  name       = "${local.prefix}-task-execution-role-policy-attachment"
  roles      = [aws_iam_role.task_execution_role.name]
  policy_arn = aws_iam_policy.task_execution_role_policy.arn
}

resource "aws_iam_role" "app_iam_role" {
  name               = "${local.prefix}-api-task-role"
  assume_role_policy = file("./templates/ecs/assume-role-policy.json")

  tags = local.common_tags
}

resource "aws_cloudwatch_log_group" "api_logs" {
  name = "${local.prefix}-api-logs"
  tags = local.common_tags
}

resource "aws_ecs_task_definition" "api" {
  family                   = "${local.prefix}-api"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "4096"
  memory                   = "8192"
  execution_role_arn       = aws_iam_role.task_execution_role.arn
  task_role_arn            = aws_iam_role.app_iam_role.arn

  container_definitions = jsonencode([
    {
      name      = "api"
      image     = var.ecr_image_api
      essential = true
      memoryReservation = 8192

      environment = [
        { name = "PATH", value = "/project/venv/bin:/root/.local/bin:$PATH" },
        { name = "RDS_DB_NAME", value = aws_db_instance.main.db_name },
        { name = "RDS_USERNAME", value = aws_db_instance.main.username },
        { name = "RDS_PASSWORD", value = aws_db_instance.main.password },
        { name = "RDS_HOSTNAME", value = aws_db_instance.main.address },
        { name = "RDS_PORT", value = "5432" },
        { name = "ALLOWED_ORIGINS", value = var.allowed_origins },
        { name = "AWS_ACCESS_KEY_ID", value = var.aws_access_key_id },
        { name = "AWS_SECRET_ACCESS_KEY", value = var.aws_secret_access_key },
        { name = "AWS_DEFAULT_REGION", value = data.aws_region.current.name },
        { name = "S3_STORAGE_BUCKET_NAME", value = aws_s3_bucket.app_documents.bucket },
        { name = "S3_STORAGE_BUCKET_REGION", value = data.aws_region.current.name },
        { name = "COGNITO_ACCESS_KEY_ID", value = var.aws_access_key_id },
        { name = "COGNITO_SECRET_ACCESS_KEY", value = var.aws_secret_access_key },
        { name = "COGNITO_USER_POOL_ID", value = var.cognito_user_pool_id },
        { name = "COGNITO_WEB_CLIENT_ID", value = var.cognito_web_client_id },
        { name = "SMTP_USERNAME", value = var.smtp_username },
        { name = "SMTP_PASSWORD", value = var.smtp_password },
        { name = "SMTP_HOST", value = var.smtp_host },
        { name = "SMTP_PORT", value = var.smtp_port },
        { name = "SMTP_SENDER_EMAIL", value = var.smtp_sender_email },
        { name = "SMTP_SENDER_NAME", value = var.smtp_sender_name },
        { name = "FRONTEND_SERVER_URL", value = var.frontend_server_url },
        { name = "FEDRISK_JWT_SECRET_KEY", value = var.fedrisk_jwt_secret_key },
        { name = "STRIPE_SECRET_KEY", value = var.stripe_secret_key },
        { name = "STRIPE_PUBLIC_KEY", value = var.stripe_public_key },
        { name = "ENVIRONMENT", value = var.environment },
        { name = "AWS_SES_REGION", value = var.aws_ses_region },
        { name = "AWS_USER", value = var.aws_user },
        { name = "AWS_SES_VERIFIED_MAIL", value = var.aws_ses_verified_mail },
        { name = "RECAPTCHA_SECRET_KEY", value = var.recaptcha_secret_key }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.api_logs.name
          awslogs-region        = data.aws_region.current.name
          awslogs-stream-prefix = "api"
        }
      }

      portMappings = [
        {
          containerPort = 8000
          hostPort      = 8000
          protocol      = "tcp"
        }
      ]
    }
  ])

  volume {
    name = "static"
  }

  tags = local.common_tags
}


resource "aws_security_group" "ecs_service" {
  description = "Access for the ECS Service"
  name        = "${local.prefix}-ecs-service-sg"
  vpc_id      = aws_vpc.main.id

  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port = 5432
    to_port   = 5432
    protocol  = "tcp"
    cidr_blocks = [
      aws_subnet.private_a.cidr_block,
      aws_subnet.private_b.cidr_block,
    ]
  }

  ingress {
    from_port = 8000
    to_port   = 8000
    protocol  = "tcp"
    security_groups = [
      aws_security_group.alb-sg.id
    ]
  }

  tags = local.common_tags
}

resource "aws_ecs_service" "api" {
  name            = "${local.prefix}-api"
  cluster         = aws_ecs_cluster.main.name
  task_definition = aws_ecs_task_definition.api.family
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets = [
      aws_subnet.private_a.id,
      aws_subnet.private_b.id,
    ]
    security_groups = [
      aws_security_group.ecs_service.id,
    ]
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.api-alb-tg.arn
    container_name   = "api"
    container_port   = 8000
  }
}

data "template_file" "ecs_s3_write_policy" {
  template = file("./templates/ecs/s3-write-policy.json.tpl")

  vars = {
    bucket_arn = aws_s3_bucket.app_documents.arn
  }
}

resource "aws_iam_policy" "ecs_s3_access" {
  name        = "${local.prefix}-AppS3AccessPolicy"
  path        = "/"
  description = "Allow access to the fedrisk-api S3 bucket for documents"

  policy = data.template_file.ecs_s3_write_policy.rendered

}

resource "aws_iam_role_policy_attachment" "ecs_s3_access" {
  role       = aws_iam_role.app_iam_role.name
  policy_arn = aws_iam_policy.ecs_s3_access.arn
}
