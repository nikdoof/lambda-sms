"""
Lambda handler for processing Twilio SMS and call webhooks and forwarding to Telegram.
"""

import hmac
import json
import urllib.parse
from base64 import b64encode
from hashlib import sha1

from secrets_manager import get_secrets
from telegram import send_telegram_message


def validate_twilio_signature(url, params, signature, auth_token):
    """
    Validate that the request came from Twilio.

    Args:
        url: The full URL of the Lambda function URL
        params: Dictionary of POST parameters
        signature: X-Twilio-Signature header value
        auth_token: Twilio auth token from secrets

    Returns:
        bool: True if signature is valid
    """
    # Sort parameters and concatenate with URL
    sorted_params = sorted(params.items())
    data = url + "".join(f"{k}{v}" for k, v in sorted_params)

    # Compute HMAC-SHA1
    mac = hmac.new(auth_token.encode("utf-8"), data.encode("utf-8"), sha1)
    expected = b64encode(mac.digest()).decode("utf-8")

    return hmac.compare_digest(expected, signature)


def detect_event_type(params):
    """
    Detect whether this is a call or SMS event.

    Args:
        params: Dictionary of parsed parameters

    Returns:
        str: 'call' or 'sms'
    """
    # Twilio call events have CallSid, SMS events have MessageSid
    if "CallSid" in params and "MessageSid" not in params:
        return "call"
    return "sms"


def extract_twilio_data(event):
    """
    Extract relevant data from Twilio webhook event.

    Returns:
        dict: Extracted data including event type, body, from, to, and media URLs
    """
    # Parse form data from body
    body = event.get("body", "")
    if event.get("isBase64Encoded", False):
        import base64

        body = base64.b64decode(body).decode("utf-8")

    params = urllib.parse.parse_qs(body)

    # Convert lists to single values
    data = {k: v[0] if len(v) == 1 else v for k, v in params.items()}

    # Extract media URLs (Twilio sends as MediaUrl0, MediaUrl1, etc.)
    media_urls = []
    num_media_raw = data.get("NumMedia", "0")
    num_media = int(num_media_raw) if isinstance(num_media_raw, str) else 0
    for i in range(num_media):
        media_url = data.get(f"MediaUrl{i}")
        if media_url:
            media_urls.append(
                {
                    "url": media_url,
                    "content_type": data.get(f"MediaContentType{i}", "unknown"),
                }
            )

    # Detect event type
    event_type = detect_event_type(data)

    return {
        "event_type": event_type,
        "from": data.get("From", ""),
        "to": data.get("To", ""),
        "body": data.get("Body", ""),
        "media": media_urls,
        "timestamp": data.get("DateSent", ""),
        "call_status": data.get("CallStatus", ""),
        "raw_params": data,
    }


def handle_call_event(secrets, call_data):
    """
    Handle incoming call event by notifying Telegram and rejecting the call.

    Args:
        secrets: Dictionary of secrets
        call_data: Dictionary containing call details

    Returns:
        dict: API Gateway response with TwiML to reject the call
    """
    from telegram import send_call_notification

    # Send notification to Telegram
    send_call_notification(
        bot_token=secrets["telegram_bot_token"],
        chat_id=secrets["telegram_chat_id"],
        call_data=call_data,
    )

    # Return TwiML to reject the call
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "text/xml"},
        "body": '<?xml version="1.0" encoding="UTF-8"?><Response><Reject /></Response>',
    }


def handle_sms_event(secrets, sms_data):
    """
    Handle incoming SMS event by forwarding to Telegram.

    Args:
        secrets: Dictionary of secrets
        sms_data: Dictionary containing SMS details

    Returns:
        dict: API Gateway response
    """
    success = send_telegram_message(
        bot_token=secrets["telegram_bot_token"],
        chat_id=secrets["telegram_chat_id"],
        sms_data=sms_data,
    )

    if not success:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Failed to send Telegram message"}),
        }

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "text/xml"},
        "body": '<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
    }


def lambda_handler(event, context):
    """
    Main Lambda handler for Twilio webhook (SMS and calls).

    Args:
        event: API Gateway event
        context: Lambda context

    Returns:
        dict: API Gateway response
    """
    try:
        # Get secrets
        secrets = get_secrets()

        # Validate Twilio signature
        signature = event.get("headers", {}).get("X-Twilio-Signature", "")

        # Reconstruct the full URL
        request_context = event.get("requestContext", {})
        domain = request_context.get("domainName", "")
        path = request_context.get("path", "")

        # For API Gateway v2 (HTTP API)
        if "http" in request_context:
            domain = request_context["http"].get("sourceIp", domain)
            path = request_context["http"].get("path", path)

        # For Lambda Function URLs, use the raw path
        full_url = f"https://{domain}{path}"

        # Extract data first to get params for validation
        twilio_data = extract_twilio_data(event)

        if not validate_twilio_signature(
            full_url, twilio_data["raw_params"], signature, secrets["twilio_auth_token"]
        ):
            print("ERROR: Invalid Twilio signature")
            return {
                "statusCode": 403,
                "body": json.dumps({"error": "Invalid signature"}),
            }

        # Handle based on event type
        event_type = twilio_data["event_type"]
        print(f"Processing {event_type} event from {twilio_data['from']}")

        if event_type == "call":
            return handle_call_event(secrets, twilio_data)
        else:
            return handle_sms_event(secrets, twilio_data)

    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback

        traceback.print_exc()

        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"}),
        }
