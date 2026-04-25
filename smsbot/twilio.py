import base64
import hashlib
import hmac

_MARKDOWN_V2_RESERVED = "_*[]()~`>#+-=|{}.!"


def _escape_markdown_v2(text: str) -> str:
    return "".join(f"\\{c}" if c in _MARKDOWN_V2_RESERVED else c for c in text)


class TwilioMessage:
    def __init__(self, data: dict[str, str]) -> None:
        self.from_number: str = data.get("From", "Unknown")
        self.to_number: str = data.get("To", "Unknown")
        self.body: str = data.get("Body", "")

        try:
            num_media = int(data.get("NumMedia", "0"))
        except ValueError:
            num_media = 0
        self.media: list[str | None] = [data.get(f"MediaUrl{i}") for i in range(num_media)]

    def to_markdown_v2(self) -> str:
        lines = [
            f"*From*: {_escape_markdown_v2(self.from_number)}",
            f"*To*: {_escape_markdown_v2(self.to_number)}",
            "",
            _escape_markdown_v2(self.body),
        ]
        if self.media:
            lines.append("")
            lines.extend(_escape_markdown_v2(url) for url in self.media if url)
        return "\n".join(lines)


class TwilioCall:
    def __init__(self, data: dict[str, str]) -> None:
        self.from_number: str = data.get("From", "Unknown")
        self.to_number: str = data.get("To", "Unknown")

    def to_markdown_v2(self) -> str:
        return f"Call from {_escape_markdown_v2(self.from_number)}, rejected\\."


def parse_payload(data: dict[str, str]) -> TwilioMessage | TwilioCall | None:
    if "SmsMessageSid" in data:
        return TwilioMessage(data)
    if "CallSid" in data:
        return TwilioCall(data)
    return None


def validate_signature(
    auth_token: str,
    url: str,
    params: dict[str, str],
    signature: str,
) -> bool:
    """Verify a Twilio webhook signature.

    https://www.twilio.com/docs/usage/security#validating-requests
    """
    payload = url + "".join(k + params[k] for k in sorted(params))
    digest = hmac.new(auth_token.encode("utf-8"), payload.encode("utf-8"), hashlib.sha1).digest()
    expected = base64.b64encode(digest).decode("ascii")
    return hmac.compare_digest(expected, signature)
