import os

import telegram
from celery import shared_task

from customers.models import Customer


@shared_task
def send_telegram_message(chat_id, text):
    bot = telegram.Bot(os.getenv("BOT_TOKEN"))
    bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode="HTML",
        connect_timeout=30,
        read_timeout=30,
        write_timeout=30,
    )


@shared_task
def send_broadcast(text_ru, text_uz, text_qp):
    for customer in Customer.objects.all():
        text = {
            "ru": text_ru,
            "uz": text_uz,
            "qp": text_qp,
        }
        msg_text = text[customer.language] if text[customer.language] else text["ru"]
        send_telegram_message.delay(customer.chat_id, msg_text)
