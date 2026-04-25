from smsbot.twilio import TwilioMessage, parse_payload, validate_signature


def test_message_basic():
    msg = TwilioMessage(
        {
            "From": "+1234567890",
            "To": "+0987654321",
            "Body": "Hello, world!",
            "NumMedia": "2",
            "MediaUrl0": "http://example.com/media1.jpg",
            "MediaUrl1": "http://example.com/media2.jpg",
        }
    )

    assert msg.from_number == "+1234567890"
    assert msg.to_number == "+0987654321"
    assert msg.body == "Hello, world!"
    assert msg.media == [
        "http://example.com/media1.jpg",
        "http://example.com/media2.jpg",
    ]


def test_message_no_media():
    msg = TwilioMessage({"From": "+1", "To": "+2", "Body": "hi"})
    assert msg.media == []


def test_message_markdown_escapes_reserved():
    msg = TwilioMessage({"From": "+1.2", "To": "+3", "Body": "hello-world!"})
    rendered = msg.to_markdown_v2()
    assert "\\+1\\.2" in rendered
    assert "hello\\-world\\!" in rendered


def test_parse_payload_dispatch():
    assert parse_payload({"SmsMessageSid": "x", "From": "+1", "To": "+2"}).__class__.__name__ == "TwilioMessage"
    assert parse_payload({"CallSid": "x", "From": "+1", "To": "+2"}).__class__.__name__ == "TwilioCall"
    assert parse_payload({"unrelated": "x"}) is None


def test_validate_signature_matches_twilio_example():
    # Reference vector from Twilio docs
    # https://www.twilio.com/docs/usage/security#test-the-validity-of-your-webhook-signature
    auth_token = "12345"
    url = "https://mycompany.com/myapp.php?foo=1&bar=2"
    params = {
        "CallSid": "CA1234567890ABCDE",
        "Caller": "+14158675309",
        "Digits": "1234",
        "From": "+14158675309",
        "To": "+18005551212",
    }
    expected = "RSOYDt4T1cUTdK1PDd93/VVr8B8="
    assert validate_signature(auth_token, url, params, expected)
    assert not validate_signature(auth_token, url, params, "wrong")
