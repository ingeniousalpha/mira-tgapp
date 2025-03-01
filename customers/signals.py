from django.db.models.signals import post_save
from django.dispatch import receiver

from customers.models import Notification
from customers.tasks import send_broadcast


@receiver(post_save, sender=Notification)
def notification_post_save(sender, instance, created=False, **kwargs):
    if created:
        send_broadcast.delay(instance.text.ru, instance.text.uz)
