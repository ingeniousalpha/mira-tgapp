from rest_framework import serializers

from menu.models import Category, MenuItem


class MenuItemSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    price = serializers.DecimalField(max_digits=12, decimal_places=2)
    image = serializers.SerializerMethodField()

    class Meta:
        model = MenuItem
        fields = ('id', 'name', 'description', 'price', 'image')

    def get_name(self, obj):
        return obj.name.translate()

    def get_description(self, obj):
        return obj.description.translate()

    def get_image(self, obj):
        return self.context['request'].build_absolute_uri(obj.image.url)


class CategorySerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    items = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ('id', 'name', 'items')

    def get_name(self, obj):
        return obj.name.translate()

    def get_items(self, obj):
        items = MenuItem.objects.filter(category=obj, is_hidden=False).order_by('-priority', '-id')
        serializer = MenuItemSerializer(items, many=True, context=self.context)
        return serializer.data