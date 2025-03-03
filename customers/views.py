from constance import config as constance
from rest_framework import status
from rest_framework.generics import GenericAPIView, ListAPIView, DestroyAPIView
from rest_framework.response import Response

from common.mixins import PublicJSONRendererMixin
from customers.models import CartItem, Order, OrderItem, Address
from customers.serializers import AddOrUpdateCartItemSerializer, OrderSerializer
from customers.services import get_cart_data, is_in_delivery_zone, get_notification_text
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


class CartView(PublicJSONRendererMixin, DestroyAPIView, GenericAPIView):
    pagination_class = None

    def get_queryset(self):
        return CartItem.objects.filter(customer_id=self.kwargs.get('pk'))

    def get(self, request, *args, **kwargs):
        return Response(
            data=get_cart_data(self.kwargs.get('pk'), self.get_queryset(), context=self.get_serializer_context()),
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
                data=get_cart_data(self.kwargs.get('pk'), self.get_queryset(), context=self.get_serializer_context()),
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        queryset.delete()
        return Response(data={}, status=status.HTTP_200_OK)


class OrderView(PublicJSONRendererMixin, ListAPIView, GenericAPIView):
    serializer_class = OrderSerializer
    pagination_class = None

    def get_queryset(self):
        return Order.objects.filter(customer_id=self.kwargs.get('pk'))

    def post(self, request, *args, **kwargs):
        customer_id = self.kwargs.get('pk')
        cart_items = CartItem.objects.filter(customer_id=customer_id)
        if not cart_items.exists():
            return Response(
                {'data': None, 'error': {'code': 'cart_is_empty', 'message': 'Корзина пуста'}},
                status=status.HTTP_400_BAD_REQUEST
            )
        address = Address.objects.filter(customer_id=customer_id, is_current=True).first()
        if not is_in_delivery_zone(address):
            Response(
                {'data': None, 'error': {'code': 'not_in_delivery_zone', 'message': 'Адрес вне зоны доставки'}},
                status=status.HTTP_400_BAD_REQUEST
            )
        cart_data = get_cart_data(self.kwargs.get('pk'), cart_items, context=self.get_serializer_context())
        order = Order.objects.create(
            customer_id=self.kwargs.get('pk'),
            address=address.value,
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
        send_telegram_message.delay(
            '-1002384142591',
            get_notification_text(address, cart_data, order.comment or '-', True)
        )
        send_telegram_message.delay(
            order.customer.chat_id,
            get_notification_text(address, cart_data, order.comment or '-')
        )
        return Response(data={}, status=status.HTTP_200_OK)
