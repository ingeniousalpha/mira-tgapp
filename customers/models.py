import json

from constance import config as constance
from django.db import models
from django.db.models import TextChoices
from localized_fields.fields import LocalizedTextField
from phonenumber_field.modelfields import PhoneNumberField

from menu.models import MenuItem


class CustomerLanguages(TextChoices):
    RUSSIAN = "ru", "Русский"
    UZBEK = "uz", "Узбекский"
    KARAKALPAK = "qp", "Каракалпакский"


class Customer(models.Model):
    telegram_user_id = models.BigIntegerField(unique=True, verbose_name='Telegram user ID')
    chat_id = models.BigIntegerField(verbose_name='Chat ID')
    phone_number = PhoneNumberField(null=True, blank=True, verbose_name='Номер телефона')
    name = models.TextField(null=True, blank=True, verbose_name="Имя")
    cashback = models.DecimalField(default=0, max_digits=12, decimal_places=2, verbose_name='Cashback')
    for_pickup = models.BooleanField(default=False, verbose_name='Самовывоз')
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
        CustomerLanguages.UZBEK: "Qabul qilindi",
        CustomerLanguages.KARAKALPAK: "Qabıllandı",
    },
    OrderStatuses.CONFIRMED: {
        CustomerLanguages.RUSSIAN: "Подтвержден",
        CustomerLanguages.UZBEK: "Tasdiqlandi",
        CustomerLanguages.KARAKALPAK: "Tastıyıqlandı",
    },
    OrderStatuses.PREPARING: {
        CustomerLanguages.RUSSIAN: "Готовится",
        CustomerLanguages.UZBEK: "Tayyorlanmoqda",
        CustomerLanguages.KARAKALPAK: "Tayarlanıwda",
    },
    OrderStatuses.IN_DELIVERY: {
        CustomerLanguages.RUSSIAN: "Доставляется",
        CustomerLanguages.UZBEK: "Yetkazib berilmoqda",
        CustomerLanguages.KARAKALPAK: " Jetkizip beriliwde",
    },
    OrderStatuses.DELIVERED: {
        CustomerLanguages.RUSSIAN: "Доставлен",
        CustomerLanguages.UZBEK: "Yetkazib berildi",
        CustomerLanguages.KARAKALPAK: " Jetkizip berildi",
    },
    OrderStatuses.CANCELLED: {
        CustomerLanguages.RUSSIAN: "Отменен",
        CustomerLanguages.UZBEK: "Bekor qilindi",
        CustomerLanguages.KARAKALPAK: "Biykar qılındı",
    }
}


class PaymentTypes(TextChoices):
    CASH = "cash", "Наличными"
    CARD = "card", "Картой"


class PaymentStatuses(TextChoices):
    WAITING = "waiting", "Ожидает подтверждения"
    CONFIRMED = "confirmed", "Подтвержден"
    REJECTED = "rejected", "Отклонен"


class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='orders', verbose_name='Клиент')
    status = models.CharField(
        max_length=20,
        choices=OrderStatuses.choices,
        default=OrderStatuses.ACCEPTED,
        verbose_name='Статус'
    )
    address = models.TextField(verbose_name='Адрес')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Общая стоимость')
    payment_type = models.CharField(
        max_length=10,
        choices=PaymentTypes.choices,
        default=PaymentTypes.CASH,
        verbose_name='Тип платежа'
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatuses.choices,
        null=True,
        blank=True,
        verbose_name='Статус платежа'
    )
    for_pickup = models.BooleanField(default=False, verbose_name='Самовывоз')
    comment = models.TextField(null=True, blank=True, verbose_name='Комментарий')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата и время создания')
    is_finished = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ('-created_at', '-id')

    def __str__(self):
        return f"Заказ #{self.id}"

    def save(self, *args, **kwargs):
        super(Order, self).save(*args, **kwargs)
        if self.status == OrderStatuses.DELIVERED and not self.is_finished:
            self.customer.cashback = self.customer.cashback + self.total_amount * constance.CASHBACK_PERCENTAGE / 100
            self.customer.save()
            self.is_finished = True
            self.save()


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
    text = LocalizedTextField(required=['ru'], verbose_name="Текст")

    class Meta:
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'


class State(models.Model):
    user_id = models.BigIntegerField()
    state = models.TextField(null=True)
