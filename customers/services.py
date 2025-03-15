from datetime import datetime
from decimal import Decimal

import numpy
from constance import config as constance
from matplotlib.path import Path

from customers.models import DeliveryZone, Order, OrderStatuses
from customers.serializers import CartItemSerializer


def get_cart_data(customer_id, cart_items, context):
    language = context['request'].language
    serializer = CartItemSerializer(cart_items, many=True, context=context)
    total_amount = Decimal(0)
    for item in serializer.data:
        total_amount = total_amount + item['menu_item']['price'] * item['quantity']
    is_first_order = constance.PRESENT_ON and Order.objects.filter(customer_id=customer_id).count() == 0
    extra_text = {'ru': constance.PRESENT_CART_RU, 'uz': constance.PRESENT_CART_UZ}
    result_data = {
        "cart_items": serializer.data,
        "total_amount": total_amount,
        "is_first_order": is_first_order,
        "extra_text": extra_text[language] if is_first_order else None
    }
    return result_data


def check_point(vertices, point):
    return Path(numpy.array(vertices)).contains_point(point)


def is_in_delivery_zone(address):
    for zone in DeliveryZone.objects.filter(is_active=True):
        if zone.zone_json and check_point(
            zone.zone_json["features"][0]["geometry"]["coordinates"][0],
            [address.longitude, address.latitude]
        ):
            return True
    return False


def get_notification_text(address, cart_data, order_id, order_comment, is_admin=False):
    customer = address.customer
    language = 'ru' if is_admin else customer.language
    constance_text = {
        "ru": (constance.BILL_INITIAL_RU, constance.BILL_TOTAL_RU, constance.BILL_FINAL_RU, constance.PICKUP_BUTTON_RU),
        "uz": (constance.BILL_INITIAL_UZ, constance.BILL_TOTAL_UZ, constance.BILL_FINAL_UZ, constance.PICKUP_BUTTON_UZ),
    }
    text = f"{constance_text[language][0]}:\n\n"
    for item in cart_data['cart_items']:
        text = text + f" {item['quantity']}x " + item['menu_item']['name'] + "\n"
    text = text + f"\n{constance_text[language][1]}: {cart_data['total_amount']}\n\n"
    if customer.for_pickup:
        text = text + constance_text[language][3] + "\n\n"
    else:
        text = text + f"{address.value}\n\n"
    if is_admin:
        if not customer.for_pickup:
            text = text + f"https://yandex.ru/maps/?ll={address.longitude},{address.latitude}&pt={address.longitude},{address.latitude}&z=17\n\n"
        order_count = Order.objects.filter(customer=customer).exclude(status=OrderStatuses.CANCELLED).count()
        text = text + f"Номер телефона: {customer.phone_number}\n"
        text = text + f"Количество заказов: {order_count}\n"
        text = text + f"Комментарий: {order_comment}\n"
        text = text + f"Ссылка на заказ: https://miraapa.uz/admin/customers/order/{order_id}/change/\n"
    else:
        text = text + f"{constance_text[language][2]}"
    return text


def is_working_time():
    try:
        start_time = datetime.strptime(constance.START_TIME, "%H:%M").time()
        end_time = datetime.strptime(constance.END_TIME, "%H:%M").time()
    except Exception:
        raise ValueError("Неверный формат времени")
    time_now = datetime.now().time()
    if end_time > start_time:
        return start_time <= time_now < end_time
    else:
        return time_now >= start_time or time_now < end_time
