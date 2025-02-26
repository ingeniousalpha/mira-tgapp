from decimal import Decimal

from constance import config as constance
from rest_framework import status
from rest_framework.generics import GenericAPIView, ListAPIView, DestroyAPIView
from rest_framework.response import Response

from common.mixins import PublicJSONRendererMixin
from customers.models import CartItem, Order, OrderItem, Address
from customers.serializers import CartItemSerializer, AddOrUpdateCartItemSerializer, OrderSerializer


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
        "delivery_fee": delivery_fee,
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
        order = Order.objects.create(
            customer_id=self.kwargs.get('pk'),
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
        return Response(data={}, status=status.HTTP_200_OK)
