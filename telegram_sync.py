import os
import asyncio
import uuid

from pathlib import Path

from telegram import Update

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from viber_sync import (
    VIBER_TOKEN,
    send_to_viber
)


# --------------------
# Токены
# --------------------

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден")


# --------------------
# Настройки
# --------------------

MEDIA_FOLDER = "media"

BASE_URL = "https://h6-message-sync-production.up.railway.app/media/"

Path(MEDIA_FOLDER).mkdir(exist_ok=True)


# --------------------
# Альбомы
# --------------------

albums = {}

album_tasks = {}


async def send_album(group_id):

    await asyncio.sleep(10)

    if group_id not in albums:
        return

    messages = albums.pop(group_id)

    album_tasks.pop(group_id, None)

    for message in messages:
        
    await send_to_viber(message)


# --------------------
# Команды
# --------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(

        "Н6 Sync запущен.\n\n"

        "/testviber - проверка токена\n"

        "/testaccount - информация о канале\n"

        "/viber - отправить текст\n"

        "/setwebhook - установить webhook\n"

        "/tasks - список задач"

    )


async def tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "Задач пока нет."
    )


async def testviber(update: Update, context: ContextTypes.DEFAULT_TYPE):

    import requests

    try:

        response = requests.post(

            "https://chatapi.viber.com/pa/get_account_info",

            json={
                "auth_token": VIBER_TOKEN
            },

            timeout=20

        )

        await update.message.reply_text(

            f"Ответ Viber:\n"

            f"{response.status_code}\n\n"

            f"{response.text}"

        )

    except Exception as e:

        await update.message.reply_text(
            f"Ошибка:\n{e}"
        )


async def testaccount(update: Update, context: ContextTypes.DEFAULT_TYPE):

    import requests

    try:

        response = requests.post(

            "https://chatapi.viber.com/pa/get_account_info",

            json={
                "auth_token": VIBER_TOKEN
            },

            timeout=20

        )

        data = response.json()

        await update.message.reply_text(

            f"Канал: {data.get('name')}\n"

            f"Статус: {data.get('status_message')}\n"

            f"Администраторов: {len(data.get('members', []))}"

        )

    except Exception as e:

        await update.message.reply_text(
            f"Ошибка:\n{e}"
        )


async def setwebhook(update: Update, context: ContextTypes.DEFAULT_TYPE):

    import requests

    response = requests.post(

        "https://chatapi.viber.com/pa/set_webhook",

        json={

            "url": "https://h6-message-sync-production.up.railway.app/webhook",

            "auth_token": VIBER_TOKEN

        },

        timeout=20

    )

    await update.message.reply_text(
        response.text
    )


async def viber(update: Update, context: ContextTypes.DEFAULT_TYPE):

    from viber_sync import send_to_viber

    text = " ".join(context.args)

    if not text:

        await update.message.reply_text(

            "Использование:\n"

            "/viber Ваш текст"

        )

        return

    await send_text(text)

    await update.message.reply_text(
        "Отправлено."
    )


# --------------------
# Получение сообщений
# --------------------

async def channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.channel_post:
        return

    message = update.channel_post

    # ---------- Альбом ----------
    if message.media_group_id:

        group_id = message.media_group_id

        if group_id not in albums:

            albums[group_id] = []

            album_tasks[group_id] = asyncio.create_task(
                send_album(group_id)
            )

        albums[group_id].append(message)

        return

    await process_message(message)


# --------------------
# Подготовка сообщения
# --------------------

async def process_message(message):

    text = message.text or message.caption or ""

    data = {
        "type": None,
        "text": text,
        "path": None,
        "filename": None,
        "size": None,
        "duration": None
    }


    # Фото

    if message.photo:

        file = await message.photo[-1].get_file()

        filename = f"{uuid.uuid4()}.jpg"

        path = f"{MEDIA_FOLDER}/{filename}"

        await file.download_to_drive(path)

        data["type"] = "photo"
        data["path"] = path
        data["filename"] = filename


    elif message.video:

        file = await message.video.get_file()

        filename = f"{uuid.uuid4()}.mp4"

        path = f"{MEDIA_FOLDER}/{filename}"

        await file.download_to_drive(path)

        data["type"] = "video"
        data["path"] = path
        data["filename"] = filename
        data["size"] = message.video.file_size
        data["duration"] = message.video.duration


    elif message.animation:

        file = await message.animation.get_file()

        filename = f"{uuid.uuid4()}.gif"

        path = f"{MEDIA_FOLDER}/{filename}"

        await file.download_to_drive(path)

        data["type"] = "gif"
        data["path"] = path
        data["filename"] = filename
        data["size"] = message.animation.file_size


    elif message.document:

        file = await message.document.get_file()

        filename = message.document.file_name or f"{uuid.uuid4()}"

        path = f"{MEDIA_FOLDER}/{filename}"

        await file.download_to_drive(path)

        data["type"] = "document"
        data["path"] = path
        data["filename"] = filename
        data["size"] = message.document.file_size


    elif message.voice:

        file = await message.voice.get_file()

        filename = f"{uuid.uuid4()}.ogg"

        path = f"{MEDIA_FOLDER}/{filename}"

        await file.download_to_drive(path)

        data["type"] = "voice"
        data["path"] = path
        data["filename"] = filename
        data["size"] = message.voice.file_size
        data["duration"] = message.voice.duration


    elif message.video_note:

        file = await message.video_note.get_file()

        filename = f"{uuid.uuid4()}.mp4"

        path = f"{MEDIA_FOLDER}/{filename}"

        await file.download_to_drive(path)

        data["type"] = "video_note"
        data["path"] = path
        data["filename"] = filename
        data["size"] = message.video_note.file_size
        data["duration"] = message.video_note.duration


    elif message.sticker:

        file = await message.sticker.get_file()

        filename = f"{uuid.uuid4()}.webp"

        path = f"{MEDIA_FOLDER}/{filename}"

        await file.download_to_drive(path)

        data["type"] = "sticker"
        data["path"] = path
        data["filename"] = filename


    elif text:

        data["type"] = "text"


    else:
        return

    await send_to_viber(data)


# --------------------
# Запуск Telegram
# --------------------

def setup_telegram(app):

    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )


    app.add_handler(
        CommandHandler(
            "testviber",
            testviber
        )
    )


    app.add_handler(
        CommandHandler(
            "testaccount",
            testaccount
        )
    )


    app.add_handler(
        CommandHandler(
            "viber",
            viber
        )
    )


    app.add_handler(
        CommandHandler(
            "setwebhook",
            setwebhook
        )
    )


    app.add_handler(
        CommandHandler(
            "tasks",
            tasks
        )
    )


    app.add_handler(

        MessageHandler(

            filters.ALL,

            channel_post

        )

    )


# --------------------
# Запуск приложения
# --------------------


def run():

    app = Application.builder().token(BOT_TOKEN).build()

    setup_telegram(app)

    app.run_polling()
