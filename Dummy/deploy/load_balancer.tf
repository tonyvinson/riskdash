resource "aws_lb" "api-alb" {
  name               = "${local.prefix}-main"
  load_balancer_type = "application"
  subnets = [
    aws_subnet.public_a.id,
    aws_subnet.public_b.id
  ]

  security_groups = [aws_security_group.alb-sg.id]

  tags = local.common_tags
}

resource "aws_lb_target_group" "api-alb-tg" {
  name        = "${local.prefix}-api-alb-tg"
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"
  port        = 8000

  health_check {
    path = "/docs"
  }
}

resource "aws_lb_listener" "api-lb-listener" {
  load_balancer_arn = aws_lb.api-alb.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api-alb-tg.arn
  }
}

resource "aws_lb_listener" "api-lb-listener-ssl" {
  load_balancer_arn = aws_lb.api-alb.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = "arn:aws-us-gov:acm:us-gov-east-1:736539455039:certificate/9221450e-8976-477d-bb79-202dd80babfb"
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api-alb-tg.arn
  }
}

resource "aws_security_group" "alb-sg" {
  description = "Allow access to Application Load Balancer"
  name        = "${local.prefix}-alb-sg"
  vpc_id      = aws_vpc.main.id

  ingress {
    protocol    = "tcp"
    from_port   = 443
    to_port     = 443
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    protocol    = "tcp"
    from_port   = 80
    to_port     = 80
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    protocol    = "tcp"
    from_port   = 8000
    to_port     = 8000
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = local.common_tags
}
