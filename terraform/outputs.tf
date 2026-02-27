output "webhook_url" {
  description = "Twilio webhook URL to configure in Twilio console"
  value       = "${aws_apigatewayv2_api.webhook_api.api_endpoint}/webhook"
}

output "api_gateway_id" {
  description = "API Gateway ID"
  value       = aws_apigatewayv2_api.webhook_api.id
}

output "lambda_function_name" {
  description = "Lambda function name"
  value       = aws_lambda_function.sms_handler.function_name
}

output "lambda_function_arn" {
  description = "Lambda function ARN"
  value       = aws_lambda_function.sms_handler.arn
}

output "secret_name" {
  description = "AWS Secrets Manager secret name"
  value       = aws_secretsmanager_secret.lambda_secrets.name
}

output "secret_arn" {
  description = "AWS Secrets Manager secret ARN"
  value       = aws_secretsmanager_secret.lambda_secrets.arn
}
