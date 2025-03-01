from adminsortable2.admin import SortableAdminMixin
from django.contrib import admin
from localized_fields.admin import LocalizedFieldsAdminMixin

from menu.models import Category, MenuItem


class MenuItemInline(admin.StackedInline):
    model = MenuItem
    fields = ('category', 'name', 'description', 'image', 'price', 'is_popular', 'is_hidden')
    extra = 0


@admin.register(Category)
class CategoryAdmin(LocalizedFieldsAdminMixin, SortableAdminMixin, admin.ModelAdmin):
    list_display = ('id', 'name', 'is_hidden', 'priority')
    list_display_links = ('id', 'name')
    list_editable = ('is_hidden',)
    list_filter = ('is_hidden',)
    search_fields = ('id', 'name__ru', 'name__uz')
    sortable_by = ()
    fields = ('name', 'is_hidden')
    inlines = [MenuItemInline]


@admin.register(MenuItem)
class MenuItemAdmin(LocalizedFieldsAdminMixin, SortableAdminMixin, admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'is_cart_category', 'is_popular', 'is_hidden', 'priority')
    list_display_links = ('id', 'name')
    list_editable = ('is_cart_category', 'is_popular', 'is_hidden')
    list_filter = ('category', 'is_cart_category', 'is_popular', 'is_hidden')
    search_fields = ('id', 'name__ru', 'name__uz', 'description__ru', 'description__uz')
    sortable_by = ()
    fields = ('category', 'name', 'description', 'image', 'price', 'is_cart_category', 'is_popular', 'is_hidden')
