import os
import requests
import subprocess
import uuid
import asyncio

from PIL import Image
from moviepy import VideoFileClip, AudioFileClip, ColorClip


VIBER_TOKEN = os.getenv(
    "VIBER_POST_API_TOKEN"
)


VIBER_ID = "879ZbjRz2zQwAi4wLdNohQ=="


MEDIA_URL = (
    "https://h6-message-sync-production.up.railway.app/media/"
)


if not VIBER_TOKEN:

    raise ValueError(
        "VIBER_POST_API_TOKEN не найден"
    )



# --------------------
# Отправка в Viber
# --------------------

async def send_to_viber(data):

    try:


        message_type = data["type"]

        text = data.get(
            "text",
            ""
        )


        # ----------------
        # Текст
        # ----------------

        if message_type == "text":


            payload = {

                "auth_token": VIBER_TOKEN,

                "from": VIBER_ID,

                "type": "text",

                "text": text

            }



            response = requests.post(

                "https://chatapi.viber.com/pa/post",

                json=payload,

                timeout=30

            )


            print(response.text)

            return




        filename = data.get(
            "filename"
        )


        file_url = (
            MEDIA_URL + filename
        )



        # ----------------
        # Фото
        # ----------------

        if message_type == "photo":


            payload = {

                "auth_token": VIBER_TOKEN,

                "from": VIBER_ID,

                "type": "picture",

                "media": file_url

            }




        # ----------------
        # Видео
        # ----------------

        elif message_type == "video":


            payload = {

                "auth_token": VIBER_TOKEN,

                "from": VIBER_ID,

                "type": "video",

                "media": file_url,

                "size": data.get("size"),

                "duration": data.get("duration")

            }




        # ----------------
        # GIF
        # ----------------

        elif message_type == "gif":


            payload = {

                "auth_token": VIBER_TOKEN,

                "from": VIBER_ID,

                "type": "video",

                "media": file_url

            }




        # ----------------
        # Документ
        # ----------------

        elif message_type == "document":


            payload = {

                "auth_token": VIBER_TOKEN,

                "from": VIBER_ID,

                "type": "file",

                "media": file_url,

                "size": data.get("size"),

                "file_name": filename

            }




        # ----------------
        # Голос
        # ----------------

        elif message_type == "voice":


            payload = {

                "auth_token": VIBER_TOKEN,

                "from": VIBER_ID,

                "type": "file",

                "media": file_url,

                "size": data.get("size"),

                "file_name": filename

            }




        # ----------------
        # Кружок
        # ----------------

        elif message_type == "video_note":


            payload = {

                "auth_token": VIBER_TOKEN,

                "from": VIBER_ID,

                "type": "video",

                "media": file_url,

                "size": data.get("size"),

                "duration": data.get("duration")

            }




        # ----------------
        # Стикер
        # ----------------

        elif message_type == "sticker":


            payload = {

                "auth_token": VIBER_TOKEN,

                "from": VIBER_ID,

                "type": "picture",

                "media": file_url

            }



        else:

            print(
                "Неизвестный тип:",
                message_type
            )

            return




        response = requests.post(

            "https://chatapi.viber.com/pa/post",

            json=payload,

            timeout=30

        )



        print(

            f"VIBER → {response.status_code}"

        )

        print(response.text)




        # ----------------
        # Отдельная подпись
        # ----------------

        if text:


            requests.post(

                "https://chatapi.viber.com/pa/post",

                json={

                    "auth_token": VIBER_TOKEN,

                    "from": VIBER_ID,

                    "type": "text",

                    "text": text

                },

                timeout=30

            )



    except Exception as e:


        print(

            "ОШИБКА VIBER:",

            e

        )
