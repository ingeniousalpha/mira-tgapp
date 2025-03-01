import os

import telegram
from celery import shared_task
from django.templatetags.i18n import language

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
def send_broadcast(text_ru, text_uz):
    for customer in Customer.objects.all():
        text = text_uz if customer.language == "uz" else text_ru
        send_telegram_message.delay(customer.chat_id, text)
