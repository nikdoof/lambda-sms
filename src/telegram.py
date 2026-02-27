"""
Telegram client for sending SMS and call notifications with text and media support.
"""

import requests


def format_call_notification(call_data):
    """
    Format call data into a readable Telegram message.

    Args:
        call_data: Dictionary containing call details

    Returns:
        str: Formatted message text
    """
    from_number = call_data.get("from", "Unknown")
    call_status = call_data.get("call_status", "")

    message = f"📞 Incoming Call (Rejected)\nFrom: {from_number}"

    if call_status:
        message += f"\nStatus: {call_status}"

    return message


def format_message(sms_data):
    """
    Format SMS data into a readable Telegram message.

    Args:
        sms_data: Dictionary containing SMS details

    Returns:
        str: Formatted message text
    """
    from_number = sms_data.get("from", "Unknown")
    body = sms_data.get("body", "")

    message = f"📱 New SMS\nFrom: {from_number}"

    if body:
        message += f"\nMessage: {body}"

    media_count = len(sms_data.get("media", []))
    if media_count > 0:
        message += f"\n📎 {media_count} media file(s) attached"

    return message


def send_call_notification(bot_token, chat_id, call_data):
    """
    Send call notification to Telegram chat.

    Args:
        bot_token: Telegram bot token
        chat_id: Telegram chat ID
        call_data: Dictionary containing call details

    Returns:
        bool: True if message sent successfully
    """
    base_url = f"https://api.telegram.org/bot{bot_token}"

    try:
        message_text = format_call_notification(call_data)

        response = requests.post(
            f"{base_url}/sendMessage",
            json={"chat_id": chat_id, "text": message_text, "parse_mode": "HTML"},
            timeout=10,
        )

        if response.status_code != 200:
            print(f"ERROR: Telegram call notification failed: {response.text}")
            return False

        return True

    except requests.exceptions.Timeout:
        print("ERROR: Telegram API timeout")
        return False
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Telegram API request failed: {str(e)}")
        return False
    except Exception as e:
        print(f"ERROR: Unexpected error sending call notification: {str(e)}")
        return False


def send_telegram_message(bot_token, chat_id, sms_data):
    """
    Send SMS notification to Telegram chat.
    Handles both text messages and media files.

    Args:
        bot_token: Telegram bot token
        chat_id: Telegram chat ID
        sms_data: Dictionary containing SMS details

    Returns:
        bool: True if message sent successfully
    """
    base_url = f"https://api.telegram.org/bot{bot_token}"

    try:
        message_text = format_message(sms_data)
        media_urls = sms_data.get("media", [])

        # Send text message first
        text_response = requests.post(
            f"{base_url}/sendMessage",
            json={"chat_id": chat_id, "text": message_text, "parse_mode": "HTML"},
            timeout=10,
        )

        if text_response.status_code != 200:
            print(f"ERROR: Telegram text message failed: {text_response.text}")
            return False

        # Send media files if present
        for media in media_urls:
            media_url = media.get("url")
            content_type = media.get("content_type", "").lower()

            if not media_url:
                continue

            # Determine appropriate Telegram method based on content type
            if content_type.startswith("image/"):
                method = "sendPhoto"
                file_param = "photo"
            elif content_type.startswith("video/"):
                method = "sendVideo"
                file_param = "video"
            elif content_type.startswith("audio/"):
                method = "sendAudio"
                file_param = "audio"
            else:
                method = "sendDocument"
                file_param = "document"

            media_response = requests.post(
                f"{base_url}/{method}",
                json={"chat_id": chat_id, file_param: media_url},
                timeout=30,
            )

            if media_response.status_code != 200:
                print(
                    f"WARNING: Failed to send media {media_url}: {media_response.text}"
                )
                # Continue with other media even if one fails

        return True

    except requests.exceptions.Timeout:
        print("ERROR: Telegram API timeout")
        return False
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Telegram API request failed: {str(e)}")
        return False
    except Exception as e:
        print(f"ERROR: Unexpected error sending Telegram message: {str(e)}")
        return False
