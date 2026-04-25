import base64
import logging
import os
from urllib.parse import parse_qsl

from smsbot import config, telegram, twilio

logger = logging.getLogger("smsbot")
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

_TWIML_EMPTY = '<?xml version="1.0" encoding="UTF-8"?><Response></Response>'
_TWIML_REJECT = '<?xml version="1.0" encoding="UTF-8"?><Response><Reject/></Response>'


def handler(event: dict, _context) -> dict:
    path = event.get("requestContext", {}).get("http", {}).get("path", "")
    method = event.get("requestContext", {}).get("http", {}).get("method", "")

    if method != "POST":
        return _response(405, "Method Not Allowed")
    if path not in ("/message", "/call"):
        return _response(404, "Not Found")

    try:
        cfg = config.load()
    except Exception:
        logger.exception("Failed to load configuration from SSM")
        return _response(500, "Internal Server Error")

    params = _parse_form_body(event)

    if not _verify_twilio(event, params, cfg.twilio_auth_token):
        logger.warning("Twilio signature verification failed for %s", path)
        return _response(403, "Forbidden")

    payload = twilio.parse_payload(params)
    if payload is None:
        logger.warning("Unrecognized Twilio payload on %s: keys=%s", path, list(params))
        return _response(400, "Bad Request")

    text = payload.to_markdown_v2()
    telegram.broadcast(cfg.telegram_bot_token, cfg.subscribers, text)

    if path == "/call":
        return _twiml(_TWIML_REJECT)
    return _twiml(_TWIML_EMPTY)


def _parse_form_body(event: dict) -> dict[str, str]:
    body = event.get("body") or ""
    if event.get("isBase64Encoded"):
        body = base64.b64decode(body).decode("utf-8")
    return dict(parse_qsl(body, keep_blank_values=True))


def _verify_twilio(event: dict, params: dict[str, str], auth_token: str) -> bool:
    headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
    signature = headers.get("x-twilio-signature", "")
    if not signature:
        return False

    proto = headers.get("x-forwarded-proto", "https")
    host = headers.get("host") or event.get("requestContext", {}).get("domainName", "")
    path = event.get("requestContext", {}).get("http", {}).get("path", "")
    url = f"{proto}://{host}{path}"

    return twilio.validate_signature(auth_token, url, params, signature)


def _twiml(body: str) -> dict:
    return {
        "statusCode": 200,
        "headers": {"content-type": "application/xml"},
        "body": body,
    }


def _response(status: int, body: str) -> dict:
    return {
        "statusCode": status,
        "headers": {"content-type": "text/plain"},
        "body": body,
    }
