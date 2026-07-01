import os
import requests
import threading

from flask import Flask, send_from_directory
from telegram import Update
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
async def channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:

        chat = update.effective_chat

        if update.channel_post:

            message = update.channel_post

            text = message.text or message.caption or "[Без текста]"

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
                f"TG → Viber | "
                f"{response.status_code} | "
                f"{response.text}"
            )

    except Exception as e:

        print(f"ОШИБКА CHANNEL_POST: {e}")

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
