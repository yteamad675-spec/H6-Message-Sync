import os
import mimetypes
from pathlib import Path

import requests


DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID")

MEDIA_URL = "https://h6-message-sync.onrender.com/media/"


def _content(text):
    if not text:
        return None

    return text[:2000]


async def send_to_discord(data):
    if not DISCORD_WEBHOOK_URL:
        print("DISCORD_WEBHOOK_URL is not configured")
        return

    try:
        message_type = data["type"]
        text = data.get("text", "")

        if message_type == "text":
            response = requests.post(
                f"{DISCORD_WEBHOOK_URL}?wait=true",
                json={"content": _content(text) or " "},
                timeout=30
            )

            print(f"DISCORD -> {response.status_code}")
            print(response.text)
            return _message_data(response)

        path = data.get("path")
        filename = data.get("filename")

        if not path or not filename:
            response = requests.post(
                f"{DISCORD_WEBHOOK_URL}?wait=true",
                json={"content": _content(text) or _telegram_fallback_text()},
                timeout=30
            )

            print(f"DISCORD -> {response.status_code}")
            print(response.text)
            return _message_data(response)

        file_path = Path(path)

        if file_path.exists():
            content_type = (
                mimetypes.guess_type(filename)[0]
                or "application/octet-stream"
            )

            try:
                with file_path.open("rb") as upload:
                    response = requests.post(
                        f"{DISCORD_WEBHOOK_URL}?wait=true",
                        data={"content": _content(text) or ""},
                        files={
                            "file": (
                                filename,
                                upload,
                                content_type
                            )
                        },
                        timeout=60
                    )
            except Exception as e:
                print("DISCORD FILE SEND ERROR:", e)
                return await send_discord_fallback(text)
        else:
            file_url = MEDIA_URL + filename
            content = "\n".join(
                part for part in [_content(text), file_url] if part
            )

            response = requests.post(
                f"{DISCORD_WEBHOOK_URL}?wait=true",
                json={"content": content},
                timeout=30
            )

        print(f"DISCORD -> {response.status_code}")
        print(response.text)
        if response.ok:
            return _message_data(response)

        return await send_discord_fallback(text)

    except Exception as e:
        print("DISCORD ERROR:", e)
        return await send_discord_fallback(
            data.get("text", "")
            if data else ""
        )


def _message_data(response):
    if not response.ok:
        return None

    try:
        return response.json()
    except ValueError:
        return None


async def edit_discord_message(discord_message_id, data):
    if not DISCORD_WEBHOOK_URL or not discord_message_id:
        return False

    try:
        text = _content(data.get("text", "")) or " "

        response = requests.patch(
            f"{DISCORD_WEBHOOK_URL}/messages/{discord_message_id}",
            json={"content": text},
            timeout=30
        )

        print(f"DISCORD EDIT -> {response.status_code}")
        print(response.text)
        return response.ok

    except Exception as e:
        print("DISCORD EDIT ERROR:", e)
        return False


async def delete_discord_message(discord_message_id):
    if not DISCORD_WEBHOOK_URL or not discord_message_id:
        return False

    try:
        response = requests.delete(
            f"{DISCORD_WEBHOOK_URL}/messages/{discord_message_id}",
            timeout=30
        )

        print(f"DISCORD DELETE -> {response.status_code}")
        print(response.text)
        return response.status_code in (200, 204)

    except Exception as e:
        print("DISCORD DELETE ERROR:", e)
        return False


async def replace_user_discord_message(discord_message_id, data):
    if discord_message_id:
        await delete_discord_user_message(discord_message_id)

    return await send_to_discord(data)


async def delete_discord_user_message(discord_message_id):
    if not DISCORD_BOT_TOKEN or not DISCORD_CHANNEL_ID or not discord_message_id:
        return False

    try:
        response = requests.delete(
            (
                "https://discord.com/api/v10/channels/"
                f"{DISCORD_CHANNEL_ID}/messages/{discord_message_id}"
            ),
            headers={
                "Authorization": f"Bot {DISCORD_BOT_TOKEN}"
            },
            timeout=30
        )

        print(f"DISCORD USER DELETE -> {response.status_code}")
        print(response.text)
        return response.status_code in (200, 204)

    except Exception as e:
        print("DISCORD USER DELETE ERROR:", e)
        return False


async def send_discord_fallback(text=""):
    if not DISCORD_WEBHOOK_URL:
        return None

    try:
        response = requests.post(
            f"{DISCORD_WEBHOOK_URL}?wait=true",
            json={
                "content": "\n".join(
                    part for part in [
                        _telegram_fallback_text(),
                        _content(text)
                    ] if part
                )
            },
            timeout=30
        )

        print(f"DISCORD FALLBACK -> {response.status_code}")
        print(response.text)
        return _message_data(response)

    except Exception as e:
        print("DISCORD FALLBACK ERROR:", e)
        return None


def _telegram_fallback_text():
    return (
        "⚠️ Это сообщение не может прогрузиться в Discord.\n"
        "Просмотрите его в Telegram:\n"
        "https://t.me/H6_team"
    )

