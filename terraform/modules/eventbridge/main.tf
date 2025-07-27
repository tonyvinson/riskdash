# EventBridge Rule for Daily KSI Validation
resource "aws_cloudwatch_event_rule" "ksi_daily_validation" {
  name                = "${var.project_name}-daily-validation-${var.environment}"
  description         = "Trigger KSI validation daily at 6 AM UTC"
  schedule_expression = var.schedule_expression
  
  tags = {
    Name = "KSI Daily Validation Schedule"
    Purpose = "Automated daily KSI compliance validation"
  }
}

# EventBridge Target for Orchestrator Lambda
resource "aws_cloudwatch_event_target" "ksi_orchestrator_target" {
  rule      = aws_cloudwatch_event_rule.ksi_daily_validation.name
  target_id = "KSIOrchestratorTarget"
  arn       = var.orchestrator_lambda_arn
  
  input = jsonencode({
    source = "eventbridge-scheduler"
    detail = {
      validation_type = "daily_full_scan"
      trigger_time = "06:00:00Z"
    }
  })
}

# Lambda Permission for EventBridge
resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = var.orchestrator_lambda_arn
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.ksi_daily_validation.arn
}
