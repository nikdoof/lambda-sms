"""
AWS Secrets Manager client with caching for Lambda execution context.
"""

import json
import os

import boto3
from botocore.exceptions import ClientError

# Cache secrets during Lambda execution context
_secrets_cache = None


def get_secrets():
    """
    Retrieve secrets from AWS Secrets Manager with caching.

    Returns:
        dict: Secrets containing:
            - twilio_auth_token
            - telegram_bot_token
            - telegram_chat_id
    """
    global _secrets_cache

    # Return cached secrets if available
    if _secrets_cache is not None:
        return _secrets_cache

    secret_name = os.environ.get("SECRET_NAME")
    if not secret_name:
        raise ValueError("SECRET_NAME environment variable not set")

    region_name = os.environ.get("AWS_REGION", "us-east-1")

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "ResourceNotFoundException":
            raise ValueError(f"Secret {secret_name} not found") from e
        elif error_code == "InvalidRequestException":
            raise ValueError(f"Invalid request for secret {secret_name}") from e
        elif error_code == "InvalidParameterException":
            raise ValueError(f"Invalid parameter for secret {secret_name}") from e
        elif error_code == "DecryptionFailure":
            raise ValueError(f"Cannot decrypt secret {secret_name}") from e
        elif error_code == "InternalServiceError":
            raise ValueError("Internal service error retrieving secret") from e
        else:
            raise

    # Parse the secret
    secret_string = get_secret_value_response.get("SecretString")
    if not secret_string:
        raise ValueError("Secret string is empty")

    secrets = json.loads(secret_string)

    # Validate required fields
    required_fields = ["twilio_auth_token", "telegram_bot_token", "telegram_chat_id"]
    missing_fields = [field for field in required_fields if field not in secrets]

    if missing_fields:
        raise ValueError(f"Missing required secret fields: {', '.join(missing_fields)}")

    # Cache the secrets
    _secrets_cache = secrets

    return secrets
