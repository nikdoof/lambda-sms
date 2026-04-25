import base64
from unittest.mock import patch
from urllib.parse import urlencode

import pytest

from smsbot import config, handler, twilio


@pytest.fixture(autouse=True)
def _reset_config_cache():
    config.load.cache_clear()
    yield
    config.load.cache_clear()


@pytest.fixture
def fake_config(monkeypatch):
    cfg = config.Config(
        twilio_auth_token="test-auth",
        telegram_bot_token="test-bot",
        subscribers=[111, 222],
    )
    monkeypatch.setattr(config, "load", lambda: cfg)
    monkeypatch.setattr(handler.config, "load", lambda: cfg)
    return cfg


def _make_event(path: str, params: dict[str, str], auth_token: str, *, base64_body: bool = False):
    body = urlencode(params)
    url = f"https://api.example.com{path}"
    signature = _sign(auth_token, url, params)
    return {
        "requestContext": {
            "http": {"method": "POST", "path": path},
            "domainName": "api.example.com",
        },
        "headers": {
            "host": "api.example.com",
            "x-forwarded-proto": "https",
            "x-twilio-signature": signature,
            "content-type": "application/x-www-form-urlencoded",
        },
        "body": base64.b64encode(body.encode()).decode() if base64_body else body,
        "isBase64Encoded": base64_body,
    }


def _sign(auth_token: str, url: str, params: dict[str, str]) -> str:
    import base64 as b64
    import hashlib
    import hmac

    payload = url + "".join(k + params[k] for k in sorted(params))
    digest = hmac.new(auth_token.encode(), payload.encode(), hashlib.sha1).digest()
    return b64.b64encode(digest).decode()


def test_message_dispatches_to_subscribers(fake_config):
    event = _make_event(
        "/message",
        {
            "SmsMessageSid": "SM123",
            "From": "+1234567890",
            "To": "+0987654321",
            "Body": "hello",
        },
        fake_config.twilio_auth_token,
    )

    with patch("smsbot.handler.telegram.broadcast") as broadcast:
        resp = handler.handler(event, None)

    assert resp["statusCode"] == 200
    assert "<Response></Response>" in resp["body"]
    broadcast.assert_called_once()
    args = broadcast.call_args.args
    assert args[0] == fake_config.telegram_bot_token
    assert args[1] == fake_config.subscribers


def test_call_returns_reject_twiml(fake_config):
    event = _make_event(
        "/call",
        {"CallSid": "CA123", "From": "+1234567890", "To": "+0987654321"},
        fake_config.twilio_auth_token,
    )

    with patch("smsbot.handler.telegram.broadcast"):
        resp = handler.handler(event, None)

    assert resp["statusCode"] == 200
    assert "<Reject/>" in resp["body"]


def test_invalid_signature_returns_403(fake_config):
    event = _make_event(
        "/message",
        {"SmsMessageSid": "SM1", "From": "+1", "To": "+2", "Body": "hi"},
        "wrong-token",
    )

    with patch("smsbot.handler.telegram.broadcast") as broadcast:
        resp = handler.handler(event, None)

    assert resp["statusCode"] == 403
    broadcast.assert_not_called()


def test_non_post_returns_405(fake_config):
    event = {
        "requestContext": {"http": {"method": "GET", "path": "/message"}},
        "headers": {},
    }
    resp = handler.handler(event, None)
    assert resp["statusCode"] == 405


def test_base64_body_decoded(fake_config):
    event = _make_event(
        "/message",
        {"SmsMessageSid": "SM2", "From": "+1", "To": "+2", "Body": "b64"},
        fake_config.twilio_auth_token,
        base64_body=True,
    )

    with patch("smsbot.handler.telegram.broadcast") as broadcast:
        resp = handler.handler(event, None)

    assert resp["statusCode"] == 200
    broadcast.assert_called_once()


def test_unknown_payload_returns_400(fake_config):
    event = _make_event(
        "/message",
        {"some_other_field": "value"},
        fake_config.twilio_auth_token,
    )

    with patch("smsbot.handler.telegram.broadcast") as broadcast:
        resp = handler.handler(event, None)

    assert resp["statusCode"] == 400
    broadcast.assert_not_called()


def test_validate_signature_roundtrip():
    """Sanity check: our test signing helper agrees with the production validator."""
    params = {"a": "1", "b": "2"}
    url = "https://example.com/x"
    sig = _sign("token", url, params)
    assert twilio.validate_signature("token", url, params, sig)
