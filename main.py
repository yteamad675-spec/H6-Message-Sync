import os
import requests
import threading
import asyncio

from flask import Flask, send_from_directory
from telegram import Update
from pathlib import Path
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
VIBER_TOKEN = os.getenv("VIBER_POST_API_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден")

if not VIBER_TOKEN:
    raise ValueError("VIBER_POST_API_TOKEN не найден")


# --------------------
# Flask
# --------------------

web = Flask(__name__)
MEDIA_FOLDER = "media"
albums = {}
Path(MEDIA_FOLDER).mkdir(exist_ok=True)


@web.route("/")
def home():
    return "H6 Sync Online", 200


@web.route("/media/<path:filename>")
def media(filename):
    return send_from_directory(MEDIA_FOLDER, filename)


@web.route("/webhook", methods=["GET", "POST"])
def webhook():
    return "OK", 200


def run_web():
    port = int(os.getenv("PORT", 8080))
    web.run(host="0.0.0.0", port=port)


# --------------------
# Telegram команды
# --------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Н6 Sync запущен.\n\n"
        "/testviber - проверка токена\n"
        "/testaccount - информация о канале\n"
        "/viberpost - тестовая публикация\n"
        "/tasks - список задач"
    )


async def testviber(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:

        response = requests.post(
            "https://chatapi.viber.com/pa/get_account_info",
            json={
                "auth_token": VIBER_TOKEN
            },
            timeout=20
        )

        await update.message.reply_text(
            f"Ответ Viber:\n{response.status_code}\n\n{response.text}"
        )

    except Exception as e:

        await update.message.reply_text(
            f"Ошибка:\n{e}"
        )


async def testaccount(update: Update, context: ContextTypes.DEFAULT_TYPE):

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

    response = requests.post(
        "https://chatapi.viber.com/pa/set_webhook",
        json={
            "url": "https://h6-message-sync-production.up.railway.app/webhook",
            "auth_token": VIBER_TOKEN
        },
        timeout=20
    )

    await update.message.reply_text(response.text)

async def viber(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:

        text = " ".join(context.args)

        if not text:
            await update.message.reply_text(
                "Использование:\n/viber Ваш текст"
            )
            return

        data = {
            "auth_token": VIBER_TOKEN,
            "from": "879ZbjRz2zQwAi4wLdNohQ==",
            "type": "text",
            "text": text
        }

        response = requests.post(
            "https://chatapi.viber.com/pa/post",
            json=data,
            timeout=20
        )

        await update.message.reply_text(
            f"Ответ:\n{response.status_code}\n\n{response.text}"
        )

    except Exception as e:

        await update.message.reply_text(
            f"Ошибка:\n{e}"
        )

async def tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Задач пока нет."
    )


# --------------------
# Telegram Bot
# --------------------
async def send_to_viber(message):

    try:

        text = message.text or message.caption or ""


        # ----------------
        # Фото альбомы
        # ----------------

        if message.photo:

            group_id = message.media_group_id


            if group_id:

                if group_id not in albums:
                    albums[group_id] = []


                file = await message.photo[-1].get_file()

                filename = f"{message.message_id}.jpg"

                path = f"media/{filename}"


                await file.download_to_drive(path)


                albums[group_id].append(path)


                # ждём остальные фото
                await asyncio.sleep(2)


                photos = albums.pop(group_id)


                for photo in photos:

                    url = (
                        "https://h6-message-sync-production.up.railway.app/"
                        + photo
                    )


                    data = {

                        "auth_token": VIBER_TOKEN,

                        "from": "879ZbjRz2zQwAi4wLdNohQ==",

                        "type": "picture",

                        "text": text,

                        "media": url

                    }


                    requests.post(

                        "https://chatapi.viber.com/pa/post",

                        json=data

                    )


                return


            else:


                file = await message.photo[-1].get_file()

                filename = f"{message.message_id}.jpg"

                path = f"media/{filename}"


                await file.download_to_drive(path)


                url = (
                    "https://h6-message-sync-production.up.railway.app/"
                    + path
                )


                data = {

                    "auth_token": VIBER_TOKEN,

                    "from": "879ZbjRz2zQwAi4wLdNohQ==",

                    "type": "picture",

                    "text": text,

                    "media": url

                }



        # ----------------
        # Видео
        # ----------------

        elif message.video:


            file = await message.video.get_file()


            filename = f"{message.message_id}.mp4"


            path = f"media/{filename}"


            await file.download_to_drive(path)


            url = (
                "https://h6-message-sync-production.up.railway.app/"
                + path
            )


            data = {

                "auth_token": VIBER_TOKEN,

                "from": "879ZbjRz2zQwAi4wLdNohQ==",

                "type": "video",

                "media": url,

                "size": message.video.file_size,

                "duration": message.video.duration

            }



        # ----------------
        # GIF
        # ----------------

        elif message.animation:


            file = await message.animation.get_file()


            filename = f"{message.message_id}.gif"


            path = f"media/{filename}"


            await file.download_to_drive(path)



            url = (
                "https://h6-message-sync-production.up.railway.app/"
                + path
            )


            data = {

                "auth_token": VIBER_TOKEN,

                "from": "879ZbjRz2zQwAi4wLdNohQ==",

                "type": "file",

                "media": url,

                "size": message.animation.file_size,

                "file_name": filename

            }



        # ----------------
        # Стикер
        # ----------------

        elif message.sticker:


            file = await message.sticker.get_file()


            filename = f"{message.message_id}.webp"


            path = f"media/{filename}"


            await file.download_to_drive(path)


            url = (
                "https://h6-message-sync-production.up.railway.app/"
                + path
            )


            data = {

                "auth_token": VIBER_TOKEN,

                "from": "879ZbjRz2zQwAi4wLdNohQ==",

                "type": "picture",

                "text": "",

                "media": url

            }



        # ----------------
        # Обычный текст
        # ----------------

        else:


            if not text:

                return


            data = {

                "auth_token": VIBER_TOKEN,

                "from": "879ZbjRz2zQwAi4wLdNohQ==",

                "type": "text",

                "text": text

            }



        response = requests.post(

            "https://chatapi.viber.com/pa/post",

            json=data,

            timeout=20

        )


        print(
            f"TG → Viber | {response.status_code} | {response.text}"
        )



    except Exception as e:

        print(
            f"ОШИБКА MEDIA: {e}"
        )


async def channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.channel_post:

        await send_to_viber(
            update.channel_post
        )

app = Application.builder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("testviber", testviber))
app.add_handler(CommandHandler("testaccount", testaccount))
app.add_handler(CommandHandler("viber", viber))
app.add_handler(CommandHandler("setwebhook", setwebhook))
app.add_handler(CommandHandler("tasks", tasks))
app.add_handler(
    MessageHandler(
        filters.ALL,
        channel_post
    )
)
# --------------------
# Запуск
# --------------------

threading.Thread(target=run_web).start()

app.run_polling()
