import json
import logging
import urllib.error
import urllib.request

logger = logging.getLogger(__name__)

_API_URL = "https://api.telegram.org/bot{token}/sendMessage"
_MAX_MESSAGE_LEN = 4096
_TRUNCATION_SUFFIX = "…"


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *_args, **_kwargs):
        return None


# Module-scoped opener so HTTPS connections to api.telegram.org are reused
# across invocations within a warm Lambda execution environment.
_OPENER = urllib.request.build_opener(_NoRedirectHandler())


def _truncate(text: str, limit: int = _MAX_MESSAGE_LEN) -> str:
    """Truncate to ``limit`` characters, walking back over any dangling
    MarkdownV2 escape (`\\`) so Telegram doesn't reject the message with
    "can't parse entities".
    """
    if len(text) <= limit:
        return text
    cut = limit - len(_TRUNCATION_SUFFIX)
    while cut > 0 and text[cut - 1] == "\\":
        cut -= 1
    return text[:cut] + _TRUNCATION_SUFFIX


def send_message(token: str, chat_id: int, text: str, *, timeout: float = 5.0) -> None:
    payload = json.dumps({"chat_id": chat_id, "text": _truncate(text), "parse_mode": "MarkdownV2"}).encode("utf-8")
    req = urllib.request.Request(
        _API_URL.format(token=token),
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with _OPENER.open(req, timeout=timeout) as resp:
            resp.read()
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        logger.error("Telegram API error chat=%s status=%s body=%s", chat_id, e.code, body)
        raise
    except urllib.error.URLError as e:
        logger.error("Telegram API unreachable chat=%s reason=%s", chat_id, e.reason)
        raise


def broadcast(token: str, chat_ids: list[int], text: str) -> None:
    for chat_id in chat_ids:
        try:
            send_message(token, chat_id, text)
        except (urllib.error.HTTPError, urllib.error.URLError):
            continue
