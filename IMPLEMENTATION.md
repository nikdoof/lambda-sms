# Implementation Summary

## Overview

Lambda SMS is a Python-based AWS Lambda function that bridges Twilio SMS and call webhooks with Telegram notifications. It validates incoming Twilio requests, processes SMS messages (including media) and call events, and forwards notifications to a Telegram chat.

## Architecture

```
Twilio (SMS/Calls) → API Gateway → Lambda → Telegram Bot API
                                     ↓
                             Secrets Manager
```

## Components

### Lambda Function (`src/`)

**handler.py**
- Entry point for Lambda execution
- Detects event type (SMS or call)
- Validates Twilio signature using HMAC-SHA1
- Extracts SMS data (from, to, body, media URLs)
- Handles call events with rejection TwiML
- Returns proper HTTP status codes (200/403/500)

**telegram.py**
- Sends formatted messages to Telegram
- Handles SMS text messages and media files
- Sends call notifications with caller ID
- Auto-detects content type (image/video/audio/document)
- Continues on media failure (doesn't block text delivery)

**secrets_manager.py**
- Retrieves credentials from AWS Secrets Manager
- Caches secrets during Lambda execution context
- Validates required fields on load

### Infrastructure (`terraform/`)

**Resources Created:**
- Lambda function (Python 3.12)
- API Gateway HTTP API (webhook endpoint)
- IAM roles and policies
- Secrets Manager secret
- CloudWatch Log Group

**Configurable Variables:**
- `aws_region` - Deployment region
- `project_name` - Resource naming prefix
- `lambda_timeout` - Execution timeout (default: 30s)
- `lambda_memory` - Memory allocation (default: 256MB)
- `secret_name` - Secrets Manager identifier

## Security

1. **Twilio Signature Validation** - Prevents unauthorized webhook calls
2. **AWS Secrets Manager** - Credentials never hardcoded
3. **IAM Least Privilege** - Lambda only has required permissions
4. **HTTPS Only** - API Gateway enforces TLS

## Deployment Flow

1. Run `terraform apply` to create infrastructure
2. Update Secrets Manager with actual credentials
3. Configure Twilio phone number with webhook URL
4. Test by sending SMS to Twilio number

## Message Format

**SMS messages** appear in Telegram as:
```
📱 New SMS
From: +1234567890
Message: [SMS body]
📎 2 media file(s) attached
```

**Call notifications** appear as:
```
📞 Incoming Call (Rejected)
From: +1234567890
Status: ringing
```

Media files are sent as separate Telegram messages after the text notification.

## Error Handling

- **Invalid signature** → 403 (rejected)
- **Telegram API failure** → 500 (Twilio retries for SMS)
- **Call notification failure** → Call still rejected (best effort notification)
- **Media send failure** → Warning logged, continues with text
- **Secrets missing** → 500 (Lambda fails)

## Module Usage

Can be used standalone or as Terraform module:

```hcl
module "lambda_sms" {
  source = "./path/to/lambda-sms/terraform"
  
  aws_region   = "us-west-2"
  project_name = "my-sms-handler"
  
  tags = {
    Environment = "production"
  }
}
```

## Dependencies

- Python: `requests`, `boto3`
- Terraform: AWS provider ~> 5.0, null provider ~> 3.0
- AWS Services: Lambda, API Gateway, Secrets Manager, IAM, CloudWatch
- Build Requirements: Python 3.12+ with `uv` package installer

## Build Process

Terraform automatically builds the Lambda deployment package:

1. **Dependency Installation** - `null_resource` runs `uv pip install` to a build directory
2. **File Copying** - Python source files copied to build directory
3. **Packaging** - Archive provider zips the complete package
4. **Triggers** - Rebuilds when source files change

Manual build available via `lambda/build.sh` for local testing.

Dependencies are managed via `pyproject.toml` and installed using `uv` (fast Python package installer):
```bash
uv pip install --python 3.12 --target <build_dir> requests boto3
```

## Future Enhancements

Potential improvements:
- DLQ for failed messages
- CloudWatch alarms for errors
- Multiple Telegram destinations
- SMS reply support
- Message filtering/routing
- Call forwarding option instead of rejection
- Voicemail transcription
