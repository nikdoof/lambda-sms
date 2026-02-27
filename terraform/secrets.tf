# AWS Secrets Manager secret for storing credentials
resource "aws_secretsmanager_secret" "lambda_secrets" {
  name        = var.secret_name
  description = "Credentials for Lambda SMS function (Twilio and Telegram)"

  tags = var.tags
}

# Secret version (placeholder - must be updated manually or via AWS CLI)
resource "aws_secretsmanager_secret_version" "lambda_secrets_version" {
  secret_id = aws_secretsmanager_secret.lambda_secrets.id
  secret_string = jsonencode({
    twilio_auth_token  = "REPLACE_WITH_TWILIO_AUTH_TOKEN"
    telegram_bot_token = "REPLACE_WITH_TELEGRAM_BOT_TOKEN"
    telegram_chat_id   = "REPLACE_WITH_TELEGRAM_CHAT_ID"
  })

  lifecycle {
    ignore_changes = [secret_string]
  }
}
