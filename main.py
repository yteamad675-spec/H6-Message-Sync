import os
import requests
import threading
import asyncio
import uuid

from PIL import Image
from moviepy import VideoFileClip
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


        base_url = "https://h6-message-sync-production.up.railway.app/media/"


        # ----------------
        # Фото
        # ----------------

        if message.photo:

            file = await message.photo[-1].get_file()

            filename = f"{uuid.uuid4()}.jpg"

            path = f"media/{filename}"

            await file.download_to_drive(path)


            data = {

                "auth_token": VIBER_TOKEN,

                "from": "879ZbjRz2zQwAi4wLdNohQ==",

                "type": "picture",

                "media": base_url + filename

            }


        # ----------------
        # Видео
        # ----------------

        elif message.video:

            file = await message.video.get_file()

            filename = f"{uuid.uuid4()}.mp4"

            path = f"media/{filename}"

            await file.download_to_drive(path)


            data = {

                "auth_token": VIBER_TOKEN,

                "from": "879ZbjRz2zQwAi4wLdNohQ==",

                "type": "video",

                "media": base_url + filename,

                "size": message.video.file_size,

                "duration": message.video.duration

            }


        # ----------------
        # Документ
        # ----------------

        elif message.document:

            file = await message.document.get_file()

            filename = message.document.file_name or f"{uuid.uuid4()}"

            path = f"media/{filename}"

            await file.download_to_drive(path)

            data = {

                "auth_token": VIBER_TOKEN,

                "from": "879ZbjRz2zQwAi4wLdNohQ==",

                "type": "file",

                "media": base_url + filename,

                "size": message.document.file_size,

                "file_name": filename

            }




        # ----------------
        # GIF → MP4
        # ----------------

        elif message.animation:


            gif = await message.animation.get_file()


            gif_name = f"{uuid.uuid4()}.gif"

            gif_path = f"media/{gif_name}"


            await gif.download_to_drive(gif_path)



            mp4_name = gif_name.replace(".gif",".mp4")

            mp4_path = f"media/{mp4_name}"


            clip = VideoFileClip(gif_path)

            clip.write_videofile(
                mp4_path,
                logger=None
            )

            clip.close()



            data = {

                "auth_token": VIBER_TOKEN,

                "from": "879ZbjRz2zQwAi4wLdNohQ==",

                "type": "video",

                "media": base_url + mp4_name

            }



        # ----------------
        # Стикер
        # ----------------

        elif message.sticker:


            file = await message.sticker.get_file()


            filename = f"{uuid.uuid4()}.webp"

            path = f"media/{filename}"


            await file.download_to_drive(path)



            img = Image.open(path)

            img.thumbnail((512,512))

            img.save(path)



            data = {

                "auth_token": VIBER_TOKEN,

                "from": "879ZbjRz2zQwAi4wLdNohQ==",

                "type": "picture",

                "media": base_url + filename

            }



        # ----------------
        # Текст
        # ----------------

        elif text:


            data = {

                "auth_token": VIBER_TOKEN,

                "from": "879ZbjRz2zQwAi4wLdNohQ==",

                "type": "text",

                "text": text

            }


        else:

            return



        response = requests.post(

            "https://chatapi.viber.com/pa/post",

            json=data,

            timeout=30

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
