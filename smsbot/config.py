import logging
import os
from dataclasses import dataclass
from functools import lru_cache

import boto3

logger = logging.getLogger(__name__)

_PLACEHOLDER = "REPLACE_ME"


@dataclass(frozen=True)
class Config:
    twilio_auth_token: str
    telegram_bot_token: str
    subscribers: list[int]


@lru_cache(maxsize=1)
def load() -> Config:
    """Fetch configuration from SSM Parameter Store.

    All parameters live under ``SSM_PATH_PREFIX`` (default ``/smsbot``).
    Cached for the lifetime of the Lambda execution environment.
    """
    prefix = os.environ.get("SSM_PATH_PREFIX", "/smsbot").rstrip("/")
    ssm = boto3.client("ssm")

    params: dict[str, str] = {}
    paginator = ssm.get_paginator("get_parameters_by_path")
    for page in paginator.paginate(Path=prefix, Recursive=True, WithDecryption=True):
        for p in page["Parameters"]:
            params[p["Name"]] = p["Value"]

    def _get(suffix: str) -> str:
        key = f"{prefix}/{suffix}"
        try:
            return params[key]
        except KeyError:
            raise RuntimeError(f"Missing required SSM parameter: {key}") from None

    raw_subs = _get("telegram/subscribers")
    subscribers = [int(s.strip()) for s in raw_subs.split(",") if s.strip()]
    if not subscribers:
        logger.warning(
            "No Telegram subscribers configured at %s/telegram/subscribers — messages will be discarded",
            prefix,
        )

    twilio_auth_token = _get("twilio/auth_token")
    telegram_bot_token = _get("telegram/bot_token")
    if _PLACEHOLDER in (twilio_auth_token, telegram_bot_token):
        raise RuntimeError(
            f"SSM parameters under {prefix} still hold placeholder values; "
            "populate them out-of-band before invoking the function."
        )

    return Config(
        twilio_auth_token=twilio_auth_token,
        telegram_bot_token=telegram_bot_token,
        subscribers=subscribers,
    )
