import os
import requests
import threading

from flask import Flask
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes
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


@web.route("/")
def home():
    return "N6 Sync Online", 200


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


async def viberpost(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:

        data = {
            "auth_token": VIBER_TOKEN,
            "from": "879ZbjRz2zQwAi4wLdNohQ==",
            "type": "text",
            "text": "Тестовая публикация из Н6 Sync"
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

app = Application.builder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("testviber", testviber))
app.add_handler(CommandHandler("testaccount", testaccount))
app.add_handler(CommandHandler("viberpost", viberpost))
app.add_handler(CommandHandler("tasks", tasks))


# --------------------
# Запуск
# --------------------

threading.Thread(target=run_web).start()

app.run_polling()
