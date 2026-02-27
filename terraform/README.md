# Terraform Module - Lambda SMS

Deploy the Lambda SMS function to AWS with API Gateway and Secrets Manager.

## Usage

### As a standalone deployment:

```hcl
cd terraform
terraform init
terraform plan
terraform apply
```

### As a module:

```hcl
module "lambda_sms" {
  source = "./path/to/lambda-sms/terraform"

  aws_region     = "us-west-2"
  project_name   = "my-sms-handler"
  lambda_timeout = 30
  lambda_memory  = 256

  tags = {
    Environment = "production"
    Owner       = "team@example.com"
  }
}

output "webhook_url" {
  value = module.lambda_sms.webhook_url
}
```

## Variables

| Name | Description | Default |
|------|-------------|---------|
| `aws_region` | AWS region to deploy resources | `us-east-1` |
| `project_name` | Project name for resource naming | `lambda-sms` |
| `lambda_timeout` | Lambda timeout in seconds | `30` |
| `lambda_memory` | Lambda memory in MB | `256` |
| `lambda_runtime` | Python runtime version | `python3.12` |
| `secret_name` | Secrets Manager secret name | `lambda-sms-secrets` |
| `tags` | Tags to apply to resources | `{}` |

## Outputs

- `webhook_url` - Configure this URL in Twilio console
- `lambda_function_name` - Lambda function name
- `secret_name` - Secret name for credential storage

## Post-Deployment

### 1. Update Secrets Manager

Replace placeholder values with actual credentials:

```bash
aws secretsmanager put-secret-value \
  --secret-id lambda-sms-secrets \
  --secret-string '{
    "twilio_auth_token": "your_twilio_auth_token",
    "telegram_bot_token": "your_telegram_bot_token",
    "telegram_chat_id": "your_telegram_chat_id"
  }'
```

### 2. Configure Twilio

1. Log into Twilio console
2. Navigate to your phone number settings
3. Set webhook URL (from `webhook_url` output) for:
   - **A CALL COMES IN** - Voice webhook (calls will be rejected with notification)
   - **A MESSAGE COMES IN** - Messaging webhook (messages forwarded to Telegram)
4. Set HTTP method to POST for both

## Requirements

- Terraform >= 1.0
- AWS CLI configured with appropriate credentials
- Python 3.12+
- [`uv`](https://docs.astral.sh/uv/)

**Note:** The Terraform build process automatically installs Python dependencies using `uv` into the Lambda deployment package.
