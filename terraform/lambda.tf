data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

data "archive_file" "lambda" {
  type        = "zip"
  output_path = "${path.module}/.build/smsbot.zip"

  dynamic "source" {
    for_each = toset([
      for f in fileset("${path.module}/..", "smsbot/**") :
      f if !strcontains(f, "__pycache__") && !endswith(f, ".pyc")
    ])
    content {
      content  = file("${path.module}/../${source.value}")
      filename = source.value
    }
  }
}

resource "aws_iam_role" "lambda" {
  name = var.name
  tags = var.tags

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "logs" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

data "aws_iam_policy_document" "ssm_read" {
  statement {
    sid     = "ReadParameters"
    effect  = "Allow"
    actions = ["ssm:GetParametersByPath", "ssm:GetParameter", "ssm:GetParameters"]
    resources = [
      "arn:aws:ssm:${data.aws_region.current.region}:${data.aws_caller_identity.current.account_id}:parameter${local.ssm_prefix}",
      "arn:aws:ssm:${data.aws_region.current.region}:${data.aws_caller_identity.current.account_id}:parameter${local.ssm_prefix}/*",
    ]
  }

  dynamic "statement" {
    for_each = var.kms_key_id == null ? [] : [1]
    content {
      sid       = "DecryptSecureString"
      effect    = "Allow"
      actions   = ["kms:Decrypt"]
      resources = [var.kms_key_id]
    }
  }
}

resource "aws_iam_role_policy" "ssm" {
  name   = "ssm-read"
  role   = aws_iam_role.lambda.id
  policy = data.aws_iam_policy_document.ssm_read.json
}

resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${var.name}"
  retention_in_days = var.log_retention_days
  tags              = var.tags
}

resource "aws_lambda_function" "this" {
  function_name = var.name
  description   = "Forwards Twilio message and call webhooks to Telegram."
  role          = aws_iam_role.lambda.arn
  runtime       = "python3.13"
  handler       = "smsbot.handler.handler"
  memory_size   = var.lambda_memory_mb
  timeout       = var.lambda_timeout_seconds
  architectures = ["arm64"]

  filename         = data.archive_file.lambda.output_path
  source_code_hash = data.archive_file.lambda.output_base64sha256

  reserved_concurrent_executions = var.reserved_concurrency

  environment {
    variables = {
      LOG_LEVEL       = var.log_level
      SSM_PATH_PREFIX = local.ssm_prefix
    }
  }

  tags = var.tags

  depends_on = [
    aws_iam_role_policy_attachment.logs,
    aws_iam_role_policy.ssm,
    aws_cloudwatch_log_group.lambda,
  ]
}
