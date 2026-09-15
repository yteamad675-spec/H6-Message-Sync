import asyncio
import os
import threading
from datetime import datetime, timezone


TELEGRAM_API_ID = os.getenv("TELEGRAM_API_ID")
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH")
TELETHON_SESSION = os.getenv("TELETHON_SESSION")
SOURCE_CHANNEL_ID = os.getenv("SOURCE_CHANNEL_ID")


def telethon_configured():
    return all([
        TELEGRAM_API_ID,
        TELEGRAM_API_HASH,
        TELETHON_SESSION,
        SOURCE_CHANNEL_ID
    ])


def start_delete_watcher(on_deleted):
    if not telethon_configured():
        print("Telethon delete watcher is not configured")
        return

    thread = threading.Thread(
        target=_run_watcher,
        args=(on_deleted,),
        daemon=True
    )
    thread.start()


def _run_watcher(on_deleted):
    asyncio.run(_watch_deletions(on_deleted))


async def _watch_deletions(on_deleted):
    try:
        from telethon import TelegramClient, events
        from telethon.sessions import StringSession
    except Exception as e:
        print("TELETHON IMPORT ERROR:", e)
        return

    session = (
        StringSession(TELETHON_SESSION)
        if len(TELETHON_SESSION) > 80
        else TELETHON_SESSION
    )

    client = TelegramClient(
        session,
        int(TELEGRAM_API_ID),
        TELEGRAM_API_HASH
    )

    channel_id = int(SOURCE_CHANNEL_ID)

    @client.on(events.MessageDeleted(chats=channel_id))
    async def deleted_handler(event):
        deleted_at = datetime.now(timezone.utc).isoformat()
        bot_api_chat_id = _as_bot_api_channel_id(channel_id)

        for message_id in event.deleted_ids:
            await on_deleted(
                bot_api_chat_id,
                message_id,
                deleted_at=deleted_at
            )

    try:
        await client.start()
        print("Telethon delete watcher started")
        await client.run_until_disconnected()
    except Exception as e:
        print("TELETHON WATCHER ERROR:", e)


def _as_bot_api_channel_id(channel_id):
    value = int(channel_id)

    if str(value).startswith("-100"):
        return value

    if value < 0:
        value = abs(value)

    return int(f"-100{value}")
