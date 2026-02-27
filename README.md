# Lambda SMS

A simple Lambda function that receives Twilio SMS and call webhooks and forwards notifications to Telegram.

## Features

- **Twilio webhook validation** - Verifies request signatures for security
- **SMS forwarding** - Handles text messages and media files (images, videos, etc.)
- **Call notifications** - Notifies on incoming calls and automatically rejects them
- **Secrets Manager** - All credentials stored securely in AWS Secrets Manager
- **Error handling** - Returns 500 on failures to trigger Twilio retries

## Quick Start

### Validate Setup

Run the validation script to check all requirements:

```bash
./validate.sh
```

This checks dependencies, project structure, builds the package, and validates Terraform configuration.

### 1. Deploy Infrastructure

```bash
cd terraform
terraform init
terraform apply
```

Note the `webhook_url` output.

**Note:** Terraform automatically installs Python dependencies from `requirements.txt` into the Lambda package during deployment.

### 2. Configure Secrets

```bash
aws secretsmanager put-secret-value \
  --secret-id lambda-sms-secrets \
  --secret-string '{
    "twilio_auth_token": "your_token",
    "telegram_bot_token": "bot_token",
    "telegram_chat_id": "chat_id"
  }'
```

### 3. Configure Twilio

Set the webhook URL (from step 1) in your Twilio phone number settings for both:
- **Voice webhook** - For incoming call notifications
- **Messaging webhook** - For incoming SMS messages

## Project Structure

```
src/
  ├── handler.py           # Main Lambda handler
  ├── telegram.py          # Telegram API client
  ├── secrets_manager.py   # AWS Secrets Manager
  └── requirements.txt     # Python dependencies

terraform/
  ├── main.tf             # Lambda & API Gateway
  ├── secrets.tf          # Secrets Manager
  ├── variables.tf        # Configurable inputs
  ├── outputs.tf          # Deployment outputs
  └── README.md           # Module documentation
```

## Configuration

See [terraform/README.md](terraform/README.md) for detailed configuration options.

## Requirements

- Terraform >= 1.0
- AWS CLI configured with credentials
- Python 3.12+
- [`uv`](https://docs.astral.sh/uv/)
