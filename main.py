import os
import requests

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Н6 Sync запущен.\n\n"
        "/testviber - тест Viber\n"
        "/tasks - список задач"
    )


async def testviber(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:

        headers = {
            "X-Api-Token": VIBER_TOKEN,
            "Content-Type": "application/json"
        }

        data = {
            "type": "text",
            "text": "Тест Н6 Sync"
        }

        response = requests.post(
            "https://chatapi.viber.com/pa/post",
            headers=headers,
            json=data,
            timeout=20
        )

        await update.message.reply_text(
            f"Ответ Viber:\n{response.status_code}\n\n{response.text}"
        )

    except Exception as e:

        await update.message.reply_text(
            f"Ошибка:\n{e}"
        )


async def tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Задач пока нет."
    )


app = Application.builder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("testviber", testviber))
app.add_handler(CommandHandler("tasks", tasks))

app.run_polling()
