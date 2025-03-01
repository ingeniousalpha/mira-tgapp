from django.contrib import admin
from localized_fields.admin import LocalizedFieldsAdminMixin

from customers.models import Customer, CartItem, OrderItem, Order, Address, DeliveryZone, Notification


@admin.register(DeliveryZone)
class DeliveryZoneAdmin(admin.ModelAdmin):
    list_display = ('id', 'is_active')
    fields = ('is_active', 'zone_file', 'zone_json')
    readonly_fields = ('zone_json',)


class CartItemInline(admin.StackedInline):
    model = CartItem
    fields = ('menu_item', 'quantity')
    extra = 0


class AddressInline(admin.StackedInline):
    model = Address
    fields = ('value', 'latitude', 'longitude', 'is_current')
    readonly_fields = ('is_current',)
    extra = 0


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('id', 'telegram_user_id', 'phone_number', 'language', 'created_at')
    list_display_links = ('id', 'telegram_user_id', 'phone_number')
    search_fields = ('id', 'telegram_user_id', 'phone_number')
    sortable_by = ()
    fields = ('id', 'telegram_user_id', 'chat_id', 'phone_number', 'language', 'created_at')
    readonly_fields = ('id', 'telegram_user_id', 'chat_id', 'created_at')
    inlines = [AddressInline, CartItemInline]

    def has_add_permission(self, request):
        return False

    # def has_delete_permission(self, request, obj=None):
    #     return False


class OrderItemInline(admin.StackedInline):
    model = OrderItem
    fields = ('menu_item', 'quantity')
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'status', 'created_at', 'comment')
    search_fields = ('customer__phone_number', 'comment')
    list_filter = ('status',)
    sortable_by = ()
    fields = (
        'customer',
        'status',
        'created_at',
        'cart_amount',
        'delivery_fee',
        'service_fee',
        'total_amount',
        'comment',
    )
    readonly_fields = (
        'customer',
        'created_at',
        'cart_amount',
        'delivery_fee',
        'service_fee',
        'total_amount',
        'comment',
    )
    inlines = [OrderItemInline]

    def has_add_permission(self, request):
        return False

    # def has_delete_permission(self, request, obj=None):
    #     return False


@admin.register(Notification)
class NotificationAdmin(LocalizedFieldsAdminMixin, admin.ModelAdmin):
    fields = ('text',)

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
