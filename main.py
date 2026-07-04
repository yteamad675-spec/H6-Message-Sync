import os
import requests
import threading
import asyncio
import uuid
import subprocess

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


# --------------------
# Токены
# --------------------

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден")


# --------------------
# Flask
# --------------------

MEDIA_FOLDER = "media"

Path(MEDIA_FOLDER).mkdir(exist_ok=True)

web = Flask(__name__)


@web.route("/")
def home():
    return "Н6 Sync Online", 200


@web.route("/media/<path:filename>")
def media(filename):
    return send_from_directory(MEDIA_FOLDER, filename)


@web.route("/webhook", methods=["GET", "POST"])
def webhook():
    return "OK", 200


def run_web():

    port = int(os.getenv("PORT", 8080))

    web.run(
        host="0.0.0.0",
        port=port
    )


# --------------------
# Telegram
# --------------------

app = Application.builder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("testviber", testviber))
app.add_handler(CommandHandler("testaccount", testaccount))
app.add_handler(CommandHandler("setwebhook", setwebhook))
app.add_handler(CommandHandler("viber", viber))
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

threading.Thread(
    target=run_web,
    daemon=True
).start()

app.run_polling()
