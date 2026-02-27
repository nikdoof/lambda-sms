# Call Handling Feature

## Overview

The Lambda function now supports both SMS and call webhooks from Twilio. When a call is received, the Lambda will:

1. **Detect** the event type (call vs SMS)
2. **Notify** Telegram with caller information
3. **Reject** the call automatically with TwiML response

## How It Works

### Event Detection

The handler detects call events by checking for `CallSid` parameter without `MessageSid`:

```python
if "CallSid" in params and "MessageSid" not in params:
    return "call"
```

### Call Notification Format

Telegram notifications for calls appear as:

```
📞 Incoming Call (Rejected)
From: +1234567890
Status: ringing
```

### Call Rejection

The Lambda returns TwiML to Twilio that immediately rejects the call:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Reject />
</Response>
```

## Configuration

### Twilio Setup

Configure the same webhook URL for both:

1. **Voice webhook** (A CALL COMES IN) → `/webhook`
2. **Messaging webhook** (A MESSAGE COMES IN) → `/webhook`

Both should use HTTP POST method.

### No Additional Configuration Required

- Uses the same secrets (Twilio auth token, Telegram bot token)
- Same signature validation
- Same API Gateway endpoint

## Benefits

- **Single endpoint** for both SMS and calls
- **Spam prevention** - Unknown calls are automatically rejected
- **Awareness** - Get notified when someone tries to call
- **Security** - Signature validation prevents fake call notifications

## Call Flow

```
1. Twilio receives call
2. Twilio sends webhook to Lambda
3. Lambda validates signature
4. Lambda detects it's a call event
5. Lambda sends Telegram notification
6. Lambda returns <Reject/> TwiML
7. Twilio rejects the call
```

## Testing

Use the test examples in `test_examples.py`:

```python
from test_examples import CALL_RINGING_EVENT
from handler import lambda_handler

response = lambda_handler(CALL_RINGING_EVENT, None)
# Expect: 200 status with <Reject/> TwiML body
```

## Future Enhancements

Potential improvements:

- **Configurable action** - Option to forward calls instead of rejecting
- **Whitelist** - Allow specific numbers to ring through
- **Voicemail** - Record message and transcribe to Telegram
- **Call screening** - Play message before rejecting