import os
import mimetypes
from pathlib import Path

import requests


DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

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
                DISCORD_WEBHOOK_URL,
                json={"content": _content(text) or " "},
                timeout=30
            )

            print(f"DISCORD -> {response.status_code}")
            print(response.text)
            return

        path = data.get("path")
        filename = data.get("filename")

        if not path or not filename:
            response = requests.post(
                DISCORD_WEBHOOK_URL,
                json={"content": _content(text) or "Unsupported message"},
                timeout=30
            )

            print(f"DISCORD -> {response.status_code}")
            print(response.text)
            return

        file_path = Path(path)

        if file_path.exists():
            content_type = (
                mimetypes.guess_type(filename)[0]
                or "application/octet-stream"
            )

            with file_path.open("rb") as upload:
                response = requests.post(
                    DISCORD_WEBHOOK_URL,
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
        else:
            file_url = MEDIA_URL + filename
            content = "\n".join(
                part for part in [_content(text), file_url] if part
            )

            response = requests.post(
                DISCORD_WEBHOOK_URL,
                json={"content": content},
                timeout=30
            )

        print(f"DISCORD -> {response.status_code}")
        print(response.text)

    except Exception as e:
        print("DISCORD ERROR:", e)
