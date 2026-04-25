import json
import urllib.error
from io import BytesIO
from unittest.mock import patch

from smsbot import telegram


class _Resp:
    def __init__(self, body: bytes = b'{"ok":true}'):
        self._body = body

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self):
        return self._body


def _http_error(status: int = 400, body: bytes = b'{"ok":false}'):
    return urllib.error.HTTPError(
        url="https://api.telegram.org",
        code=status,
        msg="bad",
        hdrs=None,
        fp=BytesIO(body),
    )


def test_send_message_posts_json():
    with patch.object(telegram._OPENER, "open", return_value=_Resp()) as opener:
        telegram.send_message("token", 42, "hello")

    req = opener.call_args.args[0]
    assert req.full_url == "https://api.telegram.org/bottoken/sendMessage"
    assert req.get_method() == "POST"
    body = json.loads(req.data.decode())
    assert body == {"chat_id": 42, "text": "hello", "parse_mode": "MarkdownV2"}


def test_send_message_truncates_long_body():
    long_text = "x" * (telegram._MAX_MESSAGE_LEN + 500)
    with patch.object(telegram._OPENER, "open", return_value=_Resp()) as opener:
        telegram.send_message("token", 1, long_text)

    body = json.loads(opener.call_args.args[0].data.decode())
    assert len(body["text"]) == telegram._MAX_MESSAGE_LEN
    assert body["text"].endswith(telegram._TRUNCATION_SUFFIX)


def test_truncate_walks_back_over_dangling_backslash():
    # An escape sequence sitting right at the cut boundary would leave a
    # dangling backslash and trigger Telegram's "can't parse entities" error.
    # Build a string where index `limit-1` is '\\'.
    limit = 10
    text = "abcdefgh\\." + "x" * 5  # length 15; cut at 9 would orphan '\\'
    out = telegram._truncate(text, limit=limit)
    # Suffix is len 1, so naive cut would be at index 9 (the '\\').
    # Walk-back must drop the '\\' — output has no trailing backslash.
    assert not out[: -len(telegram._TRUNCATION_SUFFIX)].endswith("\\")
    assert out.endswith(telegram._TRUNCATION_SUFFIX)


def test_broadcast_continues_after_per_chat_failure():
    calls = []

    def fake_open(req, **_):
        calls.append(req)
        if len(calls) == 1:
            raise _http_error(403, b'{"description":"forbidden"}')
        return _Resp()

    with patch.object(telegram._OPENER, "open", side_effect=fake_open):
        telegram.broadcast("token", [111, 222, 333], "hello")

    assert len(calls) == 3


def test_broadcast_handles_url_error():
    def fake_open(req, **_):
        raise urllib.error.URLError("dns")

    with patch.object(telegram._OPENER, "open", side_effect=fake_open):
        telegram.broadcast("token", [111, 222], "hello")

    # No assertion needed; exits cleanly without raising.


def test_no_redirect_handler_blocks_redirects():
    handler = telegram._NoRedirectHandler()
    assert handler.redirect_request() is None
