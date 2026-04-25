# Lambda SMS

An AWS Lambda function that receives Twilio SMS and voice webhooks and forwards
them to one or more Telegram chats. Useful for redirecting 2FA codes and
notification SMS from a Twilio number into Telegram.

Based on the work of [FiveBoroughs/Twilio2Telegram](https://github.com/FiveBoroughs/Twilio2Telegram) and [nikdoof/smsbot](https://github.com/nikdoof/smsbot).

## How it works

```
Twilio  ──POST /message, /call──►  API Gateway HTTP API  ──►  Lambda  ──►  Telegram Bot API
                                                               │
                                                               ▼
                                                              SSM Parameter Store
                                                              (bot token, twilio
                                                               auth token, subscribers)
```

The Lambda is outbound only on the Telegram side: incoming messages and rejected
calls are formatted as MarkdownV2 and posted to every chat ID listed in the
`telegram/subscribers` SSM parameter. The function has no runtime dependencies
beyond `boto3`, which is provided by the Lambda runtime.

## Repository layout

```
smsbot/          Python package — the Lambda source
  handler.py     Lambda entry point (smsbot.handler.handler)
  config.py      SSM-backed configuration loader, cached per execution env
  twilio.py      Webhook signature validator + payload parser
  telegram.py    Minimal urllib-based sendMessage client
terraform/       Self-contained Terraform module — see terraform/README.md
tests/           pytest suite
```

## Deploying

The `terraform/` directory is a Terraform module designed to be consumed from a
parent configuration. See [`terraform/README.md`](terraform/README.md) for usage,
inputs, and post-apply steps to populate SSM parameters.

Default region is `eu-west-2` — set whatever you like in your provider block.

## Configuration

All runtime configuration lives in SSM Parameter Store under a configurable path
prefix (default `/smsbot`). The Terraform module creates the parameters with
placeholder values; populate them out-of-band so secrets stay out of state:

| Parameter | Type | Description |
| --- | --- | --- |
| `/smsbot/telegram/bot_token` | SecureString | Telegram bot token |
| `/smsbot/twilio/auth_token` | SecureString | Twilio auth token (for webhook signature verification) |
| `/smsbot/telegram/subscribers` | String | Comma-separated Telegram chat IDs |

Lambda environment variables:

| Variable | Default | Description |
| --- | --- | --- |
| `SSM_PATH_PREFIX` | `/smsbot` | Prefix where the loader fetches parameters |
| `LOG_LEVEL` | `INFO` | Python logging level |

## Twilio setup

1. Buy a Twilio number.
2. Under *Phone Numbers → Manage → Active Numbers*, open the number.
3. **Messaging → A Message Comes In**: set to the `message_url` output.
4. **Voice & Fax → A Call Comes In**: set to the `call_url` output.

Twilio cannot send SMS from your account *to* your own Twilio numbers — they're
silently dropped. Test from a different phone.

## Local development

```sh
uv sync
uv run pytest
uv run ruff check
```

There's no local server: the function is written against API Gateway HTTP API
v2 events. Tests in `tests/test_handler.py` exercise the handler with realistic
event shapes, including the Twilio signature path.
