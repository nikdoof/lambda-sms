"""
Test examples for SMS and call webhook events.
Run these to test the Lambda handler locally.

Usage:
    cd src
    uv run python test_examples.py
"""

import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
# Example SMS event (text only)
SMS_TEXT_EVENT = {
    "body": "From=%2B15551234567&To=%2B15559876543&Body=Hello+World&NumMedia=0&MessageSid=SM1234567890abcdef",
    "isBase64Encoded": False,
    "headers": {
        "X-Twilio-Signature": "test_signature_here",
        "Content-Type": "application/x-www-form-urlencoded",
    },
    "requestContext": {
        "domainName": "abc123.execute-api.us-east-1.amazonaws.com",
        "http": {"path": "/webhook", "sourceIp": "54.88.0.0"},
        "path": "/webhook",
    },
}

# Example SMS event (with media)
SMS_MEDIA_EVENT = {
    "body": "From=%2B15551234567&To=%2B15559876543&Body=Check+this+out&NumMedia=2&MediaUrl0=https%3A%2F%2Fexample.com%2Fimage.jpg&MediaContentType0=image%2Fjpeg&MediaUrl1=https%3A%2F%2Fexample.com%2Fvideo.mp4&MediaContentType1=video%2Fmp4&MessageSid=SM9876543210fedcba",
    "isBase64Encoded": False,
    "headers": {
        "X-Twilio-Signature": "test_signature_here",
        "Content-Type": "application/x-www-form-urlencoded",
    },
    "requestContext": {
        "domainName": "abc123.execute-api.us-east-1.amazonaws.com",
        "http": {"path": "/webhook", "sourceIp": "54.88.0.0"},
        "path": "/webhook",
    },
}

# Example call event (ringing)
CALL_RINGING_EVENT = {
    "body": "From=%2B15551234567&To=%2B15559876543&CallSid=CA1234567890abcdef&CallStatus=ringing&Direction=inbound",
    "isBase64Encoded": False,
    "headers": {
        "X-Twilio-Signature": "test_signature_here",
        "Content-Type": "application/x-www-form-urlencoded",
    },
    "requestContext": {
        "domainName": "abc123.execute-api.us-east-1.amazonaws.com",
        "http": {"path": "/webhook", "sourceIp": "54.88.0.0"},
        "path": "/webhook",
    },
}

# Example call event (in-progress)
CALL_IN_PROGRESS_EVENT = {
    "body": "From=%2B15551234567&To=%2B15559876543&CallSid=CA1234567890abcdef&CallStatus=in-progress&Direction=inbound",
    "isBase64Encoded": False,
    "headers": {
        "X-Twilio-Signature": "test_signature_here",
        "Content-Type": "application/x-www-form-urlencoded",
    },
    "requestContext": {
        "domainName": "abc123.execute-api.us-east-1.amazonaws.com",
        "http": {"path": "/webhook", "sourceIp": "54.88.0.0"},
        "path": "/webhook",
    },
}


def test_locally():
    """
    Test the Lambda handler locally with example events.

    Note: This requires AWS credentials and secrets configured.
    """
    from handler import lambda_handler

    print("=" * 60)
    print("Testing SMS (Text Only)")
    print("=" * 60)
    response = lambda_handler(SMS_TEXT_EVENT, None)
    print(f"Status: {response['statusCode']}")
    print(f"Response: {response.get('body', 'N/A')}")
    print()

    print("=" * 60)
    print("Testing SMS (With Media)")
    print("=" * 60)
    response = lambda_handler(SMS_MEDIA_EVENT, None)
    print(f"Status: {response['statusCode']}")
    print(f"Response: {response.get('body', 'N/A')}")
    print()

    print("=" * 60)
    print("Testing Call (Ringing)")
    print("=" * 60)
    response = lambda_handler(CALL_RINGING_EVENT, None)
    print(f"Status: {response['statusCode']}")
    print("Response Body:")
    print(response.get("body", "N/A"))
    print()

    print("=" * 60)
    print("Testing Call (In Progress)")
    print("=" * 60)
    response = lambda_handler(CALL_IN_PROGRESS_EVENT, None)
    print(f"Status: {response['statusCode']}")
    print("Response Body:")
    print(response.get("body", "N/A"))


if __name__ == "__main__":
    print("Note: This test requires AWS credentials and Secrets Manager configured.")
    print("Set environment variables:")
    print("  export SECRET_NAME=lambda-sms-secrets")
    print("  export AWS_REGION=us-east-1")
    print()

    try:
        test_locally()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        print("\nThis is expected if AWS credentials/secrets are not configured.")
        sys.exit(1)
