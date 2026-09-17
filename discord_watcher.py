import asyncio
import os
import threading
import uuid
from pathlib import Path
from urllib.parse import urlparse

import requests

from sync_store import (
    get_message_record_by_discord,
    save_message_record
)


BOT_TOKEN = os.getenv("BOT_TOKEN")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID")
TELEGRAM_TARGET_CHAT_ID = os.getenv("TELEGRAM_TARGET_CHAT_ID")

MEDIA_FOLDER = "media"


def discord_watcher_configured():
    return all([
        BOT_TOKEN,
        DISCORD_BOT_TOKEN,
        DISCORD_CHANNEL_ID,
        TELEGRAM_TARGET_CHAT_ID
    ])


def start_discord_watcher():
    if not discord_watcher_configured():
        print("Discord watcher is not configured")
        return

    thread = threading.Thread(
        target=_run_discord_watcher,
        daemon=True
    )
    thread.start()


def _run_discord_watcher():
    asyncio.run(_watch_discord())


async def _watch_discord():
    try:
        import discord
    except Exception as e:
        print("DISCORD WATCHER IMPORT ERROR:", e)
        return

    intents = discord.Intents.default()
    intents.message_content = True
    intents.messages = True

    client = discord.Client(intents=intents)
    channel_id = int(DISCORD_CHANNEL_ID)
    telegram_chat_id = int(TELEGRAM_TARGET_CHAT_ID)

    @client.event
    async def on_ready():
        print(f"Discord watcher started as {client.user}")

    @client.event
    async def on_message(message):
        if message.author.bot:
            return

        if message.channel.id != channel_id:
            return

        data = await _discord_message_to_data(message)
        telegram_message = _send_to_telegram(
            telegram_chat_id,
            data
        )

        if not telegram_message:
            return

        telegram_message_id = telegram_message["message_id"]

        save_message_record({
            "telegram_chat_id": telegram_chat_id,
            "telegram_message_id": telegram_message_id,
            "telegram_media_group_id": None,
            "telegram_date": telegram_message.get("date"),
            "telegram_edited_at": None,
            "type": data["type"],
            "text": data.get("text", ""),
            "filename": data.get("filename"),
            "discord_message_id": str(message.id),
            "source": "discord",
            "deleted": False,
            "deleted_at": None
        })

    @client.event
    async def on_message_edit(before, after):
        if after.author.bot or after.channel.id != channel_id:
            return

        record = get_message_record_by_discord(after.id)
        if not record:
            return

        text = _discord_text(after)
        _edit_telegram_message(
            record["telegram_chat_id"],
            record["telegram_message_id"],
            text,
            record.get("type")
        )

        record["text"] = text
        record["discord_edited_at"] = _discord_datetime(after.edited_at)
        save_message_record(record)

    @client.event
    async def on_message_delete(message):
        if message.author.bot or message.channel.id != channel_id:
            return

        await _sync_discord_delete(message.id)

    @client.event
    async def on_raw_message_delete(payload):
        if payload.channel_id != channel_id:
            return

        await _sync_discord_delete(payload.message_id)

    async def _sync_discord_delete(discord_message_id):
        record = get_message_record_by_discord(discord_message_id)
        if not record:
            print(
                "DISCORD DELETE SKIPPED: no sync record for",
                discord_message_id
            )
            return

        if record.get("deleted"):
            return

        _delete_telegram_message(
            record["telegram_chat_id"],
            record["telegram_message_id"]
        )

        record["deleted"] = True
        record["deleted_at"] = None
        save_message_record(record)

    try:
        await client.start(DISCORD_BOT_TOKEN)
    except Exception as e:
        print("DISCORD WATCHER ERROR:", e)


async def _discord_message_to_data(message):
    text = _discord_text(message)

    data = {
        "type": "text",
        "text": text,
        "path": None,
        "filename": None,
        "size": None,
        "duration": None,
        "source_url": message.jump_url
    }

    if _looks_like_external_gif_link(text) and not message.attachments:
        data["text"] = ""
        data["type"] = "unsupported"
        return data

    if message.stickers:
        sticker = message.stickers[0]
        sticker_url = str(sticker.url)
        filename = _filename_from_url(
            sticker_url,
            fallback_suffix=".png"
        )
        path = str(Path(MEDIA_FOLDER) / filename)

        _download_file(sticker_url, path)

        data["path"] = path
        data["filename"] = filename
        data["size"] = Path(path).stat().st_size
        data["type"] = _type_from_filename_and_content(
            filename,
            None
        )
        return data

    if not message.attachments:
        return data

    attachment = message.attachments[0]
    suffix = Path(attachment.filename).suffix
    filename = f"{uuid.uuid4()}{suffix}"
    path = str(Path(MEDIA_FOLDER) / filename)

    Path(MEDIA_FOLDER).mkdir(exist_ok=True)
    await attachment.save(path)

    content_type = attachment.content_type or ""

    data["path"] = path
    data["filename"] = filename
    data["size"] = attachment.size
    data["duration"] = getattr(attachment, "duration_secs", None)
    data["type"] = _type_from_filename_and_content(
        filename,
        content_type
    )

    return data


def _looks_like_external_gif_link(text):
    value = (text or "").lower()

    return any(
        marker in value for marker in (
            "tenor.com/",
            "giphy.com/",
            "gfycat.com/"
        )
    )


def _type_from_filename_and_content(filename, content_type):
    suffix = Path(filename).suffix.lower()
    content_type = content_type or ""

    if suffix == ".gif" or content_type == "image/gif":
        return "animation"

    if content_type.startswith("image/"):
        return "photo"

    if content_type.startswith("video/"):
        return "video"

    if content_type.startswith("audio/"):
        if suffix == ".ogg":
            return "voice"

        return "audio"

    if suffix in (".png", ".jpg", ".jpeg", ".webp"):
        return "photo"

    if suffix in (".mp4", ".mov", ".webm"):
        return "video"

    if suffix in (".mp3", ".wav", ".m4a", ".aac", ".flac"):
        return "audio"

    return "document"


def _filename_from_url(url, fallback_suffix=""):
    path = urlparse(url).path
    suffix = Path(path).suffix or fallback_suffix
    return f"{uuid.uuid4()}{suffix}"


def _download_file(url, path):
    Path(path).parent.mkdir(exist_ok=True)

    response = requests.get(
        url,
        timeout=60
    )
    response.raise_for_status()

    with open(path, "wb") as output:
        output.write(response.content)


def _discord_text(message):
    return message.content or ""


def _discord_datetime(value):
    if not value:
        return None

    return value.isoformat()


def _send_to_telegram(chat_id, data):
    message_type = data["type"]
    text = data.get("text", "")

    if message_type == "unsupported":
        return _send_telegram_fallback(
            chat_id,
            text,
            data.get("source_url")
        )

    if message_type == "text":
        response = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text or " "
            },
            timeout=30
        )
    else:
        method = "sendDocument"
        file_field = "document"

        if message_type == "photo":
            method = "sendPhoto"
            file_field = "photo"
        elif message_type == "video":
            method = "sendVideo"
            file_field = "video"
        elif message_type == "animation":
            method = "sendAnimation"
            file_field = "animation"
        elif message_type == "voice":
            method = "sendVoice"
            file_field = "voice"
        elif message_type == "audio":
            method = "sendAudio"
            file_field = "audio"

        try:
            with open(data["path"], "rb") as upload:
                response = requests.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/{method}",
                    data={
                        "chat_id": chat_id,
                        "caption": text
                    },
                    files={
                        file_field: upload
                    },
                    timeout=60
                )
        except Exception as e:
            print("TELEGRAM MEDIA SEND ERROR:", e)
            return _send_telegram_fallback(
                chat_id,
                text,
                data.get("source_url")
            )

    print(f"TELEGRAM FROM DISCORD -> {response.status_code}")
    print(response.text)

    if not response.ok:
        return _send_telegram_fallback(
            chat_id,
            text,
            data.get("source_url")
        )

    result = response.json()
    if not result.get("ok"):
        return _send_telegram_fallback(
            chat_id,
            text,
            data.get("source_url")
        )

    return result.get("result")


def _send_telegram_fallback(chat_id, text, discord_url=None):
    parts = [
        "⚠️ Это сообщение не может прогрузиться в Telegram.",
        "Просмотрите его в Discord:"
    ]

    if discord_url:
        parts.append(discord_url)

    if text:
        parts.extend([
            "",
            text
        ])

    response = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": "\n".join(parts)
        },
        timeout=30
    )

    print(f"TELEGRAM FALLBACK FROM DISCORD -> {response.status_code}")
    print(response.text)

    if not response.ok:
        return None

    result = response.json()
    if not result.get("ok"):
        return None

    return result.get("result")


def _edit_telegram_message(chat_id, message_id, text, message_type=None):
    if message_type and message_type != "text":
        response = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageCaption",
            json={
                "chat_id": chat_id,
                "message_id": message_id,
                "caption": text or ""
            },
            timeout=30
        )

        print(f"TELEGRAM CAPTION EDIT FROM DISCORD -> {response.status_code}")
        print(response.text)
        return response.ok

    response = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText",
        json={
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text or " "
        },
        timeout=30
    )

    print(f"TELEGRAM EDIT FROM DISCORD -> {response.status_code}")
    print(response.text)
    return response.ok


def _delete_telegram_message(chat_id, message_id):
    response = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/deleteMessage",
        json={
            "chat_id": chat_id,
            "message_id": message_id
        },
        timeout=30
    )

    print(f"TELEGRAM DELETE FROM DISCORD -> {response.status_code}")
    print(response.text)
    return response.ok
