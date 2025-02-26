from rest_framework import serializers

from customers.models import CartItem, OrderItem, Order, readable_statuses
from menu.serializers import MenuItemSerializer


class CartItemSerializer(serializers.ModelSerializer):
    menu_item = MenuItemSerializer(read_only=True)

    class Meta:
        model = CartItem
        fields = ('menu_item', 'quantity')


class AddOrUpdateCartItemSerializer(serializers.ModelSerializer):
    customer_id = serializers.IntegerField(required=True, min_value=1)
    menu_item_id = serializers.IntegerField(required=True, min_value=1)
    quantity = serializers.IntegerField(required=True, min_value=0)

    class Meta:
        model = CartItem
        fields = ('customer_id', 'menu_item_id', 'quantity')

    def create(self, validated_data):
        customer_id = validated_data['customer_id']
        menu_item_id = validated_data['menu_item_id']
        quantity = validated_data['quantity']

        cart_item, created = CartItem.objects.get_or_create(
            customer_id=customer_id,
            menu_item_id=menu_item_id,
            defaults={'quantity': quantity}
        )
        if not created:
            cart_item.quantity = quantity
            cart_item.save()
        return cart_item


class OrderItemSerializer(serializers.ModelSerializer):
    menu_item = MenuItemSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ('menu_item', 'quantity')


class OrderSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    items = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ('status', 'total_amount', 'created_at', 'items')

    def get_status(self, obj):
        return readable_statuses[obj.status][self.context['request'].language]

    def get_items(self, obj):
        serializer = OrderItemSerializer(obj.order_items, many=True, context=self.context)
        return serializer.data
