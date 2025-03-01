from decimal import Decimal

import numpy
from constance import config as constance
from matplotlib.path import Path
from rest_framework import status
from rest_framework.generics import GenericAPIView, ListAPIView, DestroyAPIView
from rest_framework.response import Response

from common.mixins import PublicJSONRendererMixin
from customers.models import CartItem, Order, OrderItem, Address, DeliveryZone
from customers.serializers import CartItemSerializer, AddOrUpdateCartItemSerializer, OrderSerializer
from customers.tasks import send_telegram_message


class InfoView(PublicJSONRendererMixin, GenericAPIView):
    pagination_class = None

    def get_queryset(self):
        return Address.objects.filter(customer_id=self.kwargs.get('pk'), is_current=True).first()

    def get(self, request, *args, **kwargs):
        address = self.get_queryset()
        if not address:
            return Response(
                {'data': None, 'error': {'code': 'bad_request', 'message': 'Добавьте адрес'}},
                status=status.HTTP_400_BAD_REQUEST
            )
        data = {
            "address": address.value,
            "start_time": constance.START_TIME,
            "end_time": constance.END_TIME,
        }
        return Response(data=data, status=status.HTTP_200_OK)


def get_cart_data(cart_items, context):
    serializer = CartItemSerializer(cart_items, many=True, context=context)
    cart_amount = Decimal(0)
    for item in serializer.data:
        cart_amount = cart_amount + item['menu_item']['price'] * item['quantity']
    delivery_fee = constance.DELIVERY_FEE if cart_amount < constance.MIN_CART_AMOUNT_FOR_FREE_DELIVERY else 0
    service_fee = cart_amount * constance.SERVICE_FEE_PERCENTAGE / 100
    result_data = {
        "cart_items": serializer.data,
        "cart_amount": cart_amount,
        "delivery_fee": Decimal(delivery_fee),
        "service_fee": service_fee,
        "total_amount": cart_amount + delivery_fee + service_fee,
    }
    return result_data


class CartView(PublicJSONRendererMixin, DestroyAPIView, GenericAPIView):
    pagination_class = None

    def get_queryset(self):
        return CartItem.objects.filter(customer_id=self.kwargs.get('pk'))

    def get(self, request, *args, **kwargs):
        return Response(
            data=get_cart_data(self.get_queryset(), context=self.get_serializer_context()),
            status=status.HTTP_200_OK
        )

    def post(self, request, *args, **kwargs):
        request.data['customer_id'] = self.kwargs.get('pk')
        serializer = AddOrUpdateCartItemSerializer(data=request.data)
        if serializer.is_valid():
            cart_item = serializer.save()
            if cart_item.quantity == 0:
                cart_item.delete()
            return Response(
                data=get_cart_data(self.get_queryset(), context=self.get_serializer_context()),
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        queryset.delete()
        return Response(data={}, status=status.HTTP_200_OK)


def check_point(vertices, point):
    return Path(numpy.array(vertices)).contains_point(point)


def get_notification_text(language, order_id, address, cart_data):
    bill_text = {
        "ru": {
            "initial": constance.BILL_INITIAL_RU,
            "cart": constance.BILL_CART_RU,
            "delivery": constance.BILL_DELIVERY_RU,
            "service": constance.BILL_SERVICE_RU,
            "total": constance.BILL_TOTAL_RU,
        },
        "uz": {
            "initial": constance.BILL_INITIAL_UZ,
            "cart": constance.BILL_CART_UZ,
            "delivery": constance.BILL_DELIVERY_UZ,
            "service": constance.BILL_SERVICE_UZ,
            "total": constance.BILL_TOTAL_UZ,
        }
    }
    text = f"{bill_text[language]['initial']}:\n\n"
    for item in OrderItem.objects.filter(order_id=order_id).order_by('-created_at'):
        text = text + f" {item.quantity}x " + item.menu_item.name.translate() + "\n"
    text = (
        text
        + f"\n{address}\n"
        + f"\n{bill_text[language]['cart']}: {cart_data['cart_amount']}"
        + f"\n{bill_text[language]['delivery']}: {cart_data['delivery_fee']}"
        + f"\n{bill_text[language]['service']}: {cart_data['service_fee']}"
        + f"\n{bill_text[language]['total']}: {cart_data['total_amount']}"
    )
    return text


class OrderView(PublicJSONRendererMixin, ListAPIView, GenericAPIView):
    serializer_class = OrderSerializer
    pagination_class = None

    def get_queryset(self):
        return Order.objects.filter(customer_id=self.kwargs.get('pk'))

    def post(self, request, *args, **kwargs):
        cart_items = CartItem.objects.filter(customer_id=self.kwargs.get('pk'))
        if not cart_items.exists():
            return Response(
                {'data': None, 'error': {'code': 'bad_request', 'message': 'Корзина пуста'}},
                status=status.HTTP_400_BAD_REQUEST
            )
        cart_data = get_cart_data(cart_items, context=self.get_serializer_context())
        is_in_delivery_zone = False
        delivery_zones = DeliveryZone.objects.filter(is_active=True)
        address = Address.objects.filter(is_current=True).first()
        for zone in delivery_zones:
            if zone.zone_json:
                vertices = zone.zone_json["features"][0]["geometry"]["coordinates"][0]
                if check_point(vertices, [address.longitude, address.latitude]):
                    is_in_delivery_zone = True
                    break
        if not is_in_delivery_zone:
            Response(
                {'data': None, 'error': {'code': 'not_in_delivery_zone', 'message': 'Адрес вне зоны доставки'}},
                status=status.HTTP_400_BAD_REQUEST
            )
        order = Order.objects.create(
            customer_id=self.kwargs.get('pk'),
            address=address.value,
            cart_amount=cart_data['cart_amount'],
            delivery_fee=cart_data['delivery_fee'],
            service_fee=cart_data['service_fee'],
            total_amount=cart_data['total_amount'],
            comment=request.data.get('comment')
        )
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                menu_item=cart_item.menu_item,
                quantity=cart_item.quantity
            )
            cart_item.delete()
        notification_text_ru = get_notification_text("ru", order.id, address.value, cart_data)
        send_telegram_message.delay('-1002384142591', notification_text_ru)
        notification_text = get_notification_text(order.customer.language, order.id, address.value, cart_data)
        send_telegram_message.delay(order.customer.chat_id, notification_text)
        return Response(data={}, status=status.HTTP_200_OK)
