# smsbot — Terraform module

Deploys an AWS Lambda function behind API Gateway HTTP API that receives Twilio
SMS/voice webhooks and forwards them to a list of Telegram chats.

## Usage

```hcl
provider "aws" {
  region = "eu-west-2"
}

module "smsbot" {
  source = "github.com/nikdoof/smsbot//terraform?ref=lambda-rewrite"

  name            = "smsbot"
  ssm_path_prefix = "/smsbot"

  tags = {
    Project = "smsbot"
  }
}

output "twilio_message_url" {
  value = module.smsbot.message_url
}

output "twilio_call_url" {
  value = module.smsbot.call_url
}
```

## After apply

The module creates SSM Parameter Store entries with placeholder values. Populate
them out-of-band so the secret values never enter Terraform state:

```sh
aws ssm put-parameter --overwrite --type SecureString \
  --name /smsbot/telegram/bot_token --value "<your bot token>"

aws ssm put-parameter --overwrite --type SecureString \
  --name /smsbot/twilio/auth_token --value "<your twilio auth token>"

aws ssm put-parameter --overwrite --type String \
  --name /smsbot/telegram/subscribers --value "111111,222222"
```

Then point your Twilio number at the URLs from the module outputs:

- **A Message Comes In** → `module.smsbot.message_url`
- **A Call Comes In** → `module.smsbot.call_url`

## Operational notes

- **Access logs may take a few minutes to appear after the first apply.** API
  Gateway grants the implicit resource policy on its log group asynchronously;
  if `/aws/apigateway/<name>` looks empty for the first few requests after
  deploy, that's the cause — it self-heals once propagated.
- **No CloudWatch alarms are created by this module.** Wiring up a
  `Lambda Errors` or `4XXError` / `5XXError` alarm against `lambda_function_name`
  / the API stage is left to the caller, since alarm topology and notification
  routing typically live in your monitoring config rather than per-service.

## Inputs

| Name | Description | Default |
| --- | --- | --- |
| `name` | Resource name. Required — must be unique within the AWS account/region. | _(required)_ |
| `ssm_path_prefix` | Path prefix for SSM parameters. | `/smsbot` |
| `kms_key_id` | KMS key for SecureString parameters. `null` uses the AWS-managed default. | `null` |
| `log_retention_days` | CloudWatch Logs retention. | `30` |
| `lambda_memory_mb` | Lambda memory. | `256` |
| `lambda_timeout_seconds` | Lambda timeout (Twilio's webhook timeout is 15s). | `10` |
| `log_level` | `LOG_LEVEL` env var passed to the runtime. | `INFO` |
| `tags` | Tags applied to all resources. | `{}` |

## Outputs

`api_endpoint`, `message_url`, `call_url`, `lambda_function_name`,
`lambda_log_group_name`, `ssm_parameter_names`.
