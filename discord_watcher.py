import asyncio
import os
import threading
import uuid
from pathlib import Path

import requests

from sync_store import (
    get_message_record_by_discord,
    save_message_record
)
from viber_sync import send_to_viber


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

        await send_to_viber(data)

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
            text
        )

        record["text"] = text
        record["discord_edited_at"] = _discord_datetime(after.edited_at)
        save_message_record(record)

    @client.event
    async def on_message_delete(message):
        if message.author.bot or message.channel.id != channel_id:
            return

        record = get_message_record_by_discord(message.id)
        if not record:
            return

        _delete_telegram_message(
            record["telegram_chat_id"],
            record["telegram_message_id"]
        )

        record["deleted"] = True
        record["deleted_at"] = _discord_datetime(message.created_at)
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
        "duration": None
    }

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

    if content_type.startswith("image/"):
        data["type"] = "photo"
    elif content_type.startswith("video/"):
        data["type"] = "video"
    else:
        data["type"] = "document"

    return data


def _discord_text(message):
    return message.content or ""


def _discord_datetime(value):
    if not value:
        return None

    return value.isoformat()


def _send_to_telegram(chat_id, data):
    message_type = data["type"]
    text = data.get("text", "")

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

    print(f"TELEGRAM FROM DISCORD -> {response.status_code}")
    print(response.text)

    if not response.ok:
        return None

    result = response.json()
    if not result.get("ok"):
        return None

    return result.get("result")


def _edit_telegram_message(chat_id, message_id, text):
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
