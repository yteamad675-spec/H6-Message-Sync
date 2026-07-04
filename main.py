import os
import threading

from pathlib import Path
from flask import Flask, send_from_directory

from telegram_sync import run as telegram_run


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
# Запуск
# --------------------

threading.Thread(
    target=run_web,
    daemon=True
).start()

telegram_run()
