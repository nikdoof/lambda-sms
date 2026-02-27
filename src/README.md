# Source Code - Development Guide

## Setup

### Install Dependencies

Using `uv` (recommended):

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies from pyproject.toml
uv sync
```

## Local Testing

### Environment Variables

Set these before running locally:

```bash
export SECRET_NAME=lambda-sms-secrets
export AWS_REGION=us-east-1
```

### Test Payload

Example Twilio webhook payload for **SMS** testing:

```json
{
  "body": "From=%2B1234567890&To=%2B0987654321&Body=Test+message&NumMedia=0&MessageSid=SMxxxx",
  "headers": {
    "X-Twilio-Signature": "signature_here"
  },
  "requestContext": {
    "domainName": "example.execute-api.us-east-1.amazonaws.com",
    "path": "/webhook"
  }
}
```

Example Twilio webhook payload for **Call** testing:

```json
{
  "body": "From=%2B1234567890&To=%2B0987654321&CallSid=CAxxxx&CallStatus=ringing",
  "headers": {
    "X-Twilio-Signature": "signature_here"
  },
  "requestContext": {
    "domainName": "example.execute-api.us-east-1.amazonaws.com",
    "path": "/webhook"
  }
}
```

### Invoke Locally

```python
from handler import lambda_handler

event = {...}  # Your test payload
context = None
response = lambda_handler(event, context)
print(response)
```

## Module Overview

### `handler.py`
- Main Lambda entry point
- Detects event type (SMS or call)
- Validates Twilio webhook signature
- Parses incoming SMS and call data
- Coordinates message forwarding and call rejection

### `telegram.py`
- Telegram Bot API client
- Formats SMS and call notifications with emoji
- Sends text and media files
- Handles different content types
- Sends call rejection notifications

### `secrets_manager.py`
- AWS Secrets Manager integration
- Caches secrets for performance
- Validates required fields

## Deployment

### Via Terraform (Recommended)

Terraform automatically builds the deployment package with dependencies.
See `../terraform/README.md` for deployment instructions.
