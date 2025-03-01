import json

from django.db import models
from django.db.models import TextChoices
from localized_fields.fields import LocalizedTextField
from phonenumber_field.modelfields import PhoneNumberField

from menu.models import MenuItem


class CustomerLanguages(TextChoices):
    RUSSIAN = "ru", "Русский"
    UZBEK = "uz", "Узбекский"


class Customer(models.Model):
    telegram_user_id = models.BigIntegerField(unique=True, verbose_name='Telegram user ID')
    chat_id = models.BigIntegerField(verbose_name='Chat ID')
    phone_number = PhoneNumberField(null=True, blank=True, verbose_name='Номер телефона')
    language = models.CharField(
        max_length=5,
        choices=CustomerLanguages.choices,
        null=True,
        blank=True,
        verbose_name='Язык'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата и время создания')

    class Meta:
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'
        ordering = ('-created_at', '-id')

    def __str__(self):
        return f"Клиент {self.phone_number}" if self.phone_number else f"Клиент #{self.id}"


class Address(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='addresses', verbose_name='Клиент')
    latitude = models.DecimalField(max_digits=12, decimal_places=8, verbose_name='Широта')
    longitude = models.DecimalField(max_digits=12, decimal_places=8, verbose_name='Долгота')
    value = models.TextField(verbose_name='Значение')
    is_current = models.BooleanField(default=False, verbose_name='Выбран')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата и время создания')

    class Meta:
        verbose_name = 'Адрес'
        verbose_name_plural = 'Адреса'
        ordering = ('-created_at', '-id')

    def __str__(self):
        return self.value


class DeliveryZone(models.Model):
    is_active = models.BooleanField(default=False, verbose_name='Активная зона')
    zone_file = models.FileField(verbose_name='Файл зоны доставки')
    zone_json = models.JSONField(null=True, blank=True, verbose_name='JSON зоны доставки')

    class Meta:
        verbose_name = "Зона доставки"
        verbose_name_plural = "Зоны доставок"

    def save(self, *args, **kwargs):
        if self.zone_file:
            f = self.zone_file.file.open('r')
            f_lines = f.readlines()
            if f_lines:
                json_data = f_lines[0].decode('utf8')
                self.zone_json = json.loads(json_data)
        super(DeliveryZone, self).save(*args, **kwargs)
        if self.zone_file:
            self.zone_file.file.close()


class CartItem(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='cart_items', verbose_name='Клиент')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, verbose_name='Позиция')
    quantity = models.PositiveSmallIntegerField(default=1, verbose_name='Количество')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата и время создания')

    class Meta:
        verbose_name = 'Позиция корзины'
        verbose_name_plural = 'Позиции корзины'
        ordering = ('-created_at', '-id')
        unique_together = ('customer', 'menu_item')


class OrderStatuses(TextChoices):
    ACCEPTED = "accepted", "Принят"
    CONFIRMED = "confirmed", "Подтвержден"
    PREPARING = "preparing", "Готовится"
    IN_DELIVERY = "in_delivery", "Доставляется"
    DELIVERED = "delivered", "Доставлен"
    CANCELLED = "cancelled", "Отменен"


readable_statuses = {
    OrderStatuses.ACCEPTED: {
        CustomerLanguages.RUSSIAN: "Принят",
        CustomerLanguages.UZBEK: "Qabul qilingan"
    },
    OrderStatuses.CONFIRMED: {
        CustomerLanguages.RUSSIAN: "Подтвержден",
        CustomerLanguages.UZBEK: "Tasdiqlangan"
    },
    OrderStatuses.PREPARING: {
        CustomerLanguages.RUSSIAN: "Готовится",
        CustomerLanguages.UZBEK: "Tayyorgarlikda"
    },
    OrderStatuses.IN_DELIVERY: {
        CustomerLanguages.RUSSIAN: "Доставляется",
        CustomerLanguages.UZBEK: "Yetkazib berishda"
    },
    OrderStatuses.DELIVERED: {
        CustomerLanguages.RUSSIAN: "Доставлен",
        CustomerLanguages.UZBEK: "Yetkazib berildi"
    },
    OrderStatuses.CANCELLED: {
        CustomerLanguages.RUSSIAN: "Отменен",
        CustomerLanguages.UZBEK: "Bekor qilingan"
    }
}


class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='orders', verbose_name='Клиент')
    status = models.CharField(
        max_length=20,
        choices=OrderStatuses.choices,
        default=OrderStatuses.ACCEPTED,
        verbose_name='Статус'
    )
    address = models.TextField(verbose_name='Адрес')
    cart_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Стоимость всех позиций')
    delivery_fee = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Стоимость доставки')
    service_fee = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Сервисный сбор')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Общая стоимость')
    comment = models.TextField(null=True, blank=True, verbose_name='Комментарий')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата и время создания')

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ('-created_at', '-id')

    def __str__(self):
        return f"Заказ #{self.id}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items', verbose_name='Заказ')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, verbose_name='Позиция')
    quantity = models.PositiveSmallIntegerField(default=1, verbose_name='Количество')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата и время создания')

    class Meta:
        verbose_name = 'Позиция заказа'
        verbose_name_plural = 'Позиции заказа'
        ordering = ('-created_at', '-id')
        unique_together = ('order', 'menu_item')


class Notification(models.Model):
    text = LocalizedTextField(required=True, verbose_name="Текст")

    class Meta:
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'
