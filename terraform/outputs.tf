output "api_endpoint" {
  description = "Base URL of the HTTP API. Twilio webhooks should target /message and /call under this URL."
  value       = aws_apigatewayv2_api.this.api_endpoint
}

output "message_url" {
  description = "URL to configure as the Twilio 'A Message Comes In' webhook."
  value       = "${aws_apigatewayv2_api.this.api_endpoint}/message"
}

output "call_url" {
  description = "URL to configure as the Twilio 'A Call Comes In' webhook."
  value       = "${aws_apigatewayv2_api.this.api_endpoint}/call"
}

output "lambda_function_name" {
  description = "Name of the deployed Lambda function."
  value       = aws_lambda_function.this.function_name
}

output "lambda_log_group_name" {
  description = "CloudWatch log group for the Lambda function."
  value       = aws_cloudwatch_log_group.lambda.name
}

output "ssm_parameter_names" {
  description = "Names of SSM parameters to populate after apply."
  value = {
    telegram_bot_token   = aws_ssm_parameter.secure["telegram/bot_token"].name
    twilio_auth_token    = aws_ssm_parameter.secure["twilio/auth_token"].name
    telegram_subscribers = aws_ssm_parameter.plain["telegram/subscribers"].name
  }
}
