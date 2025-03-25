from constance import config as constance
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response

from common.mixins import PublicJSONRendererMixin
from menu.models import Category, MenuItem
from menu.serializers import CategorySerializer, MenuItemSerializer


class MenuView(PublicJSONRendererMixin, ListAPIView):
    queryset = Category.objects.filter(is_hidden=False)
    serializer_class = CategorySerializer
    pagination_class = None

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        result_data = [category for category in serializer.data if category['items']]
        popular_items = MenuItem.objects.filter(is_hidden=False, is_popular=True)
        if popular_items.exists():
            text = {
                "ru": constance.POPULAR_CATEGORY_RU,
                "uz": constance.POPULAR_CATEGORY_UZ,
                "qp": constance.POPULAR_CATEGORY_QP,
            }
            popular_category = {
                "id": 0,
                "name": text[request.language],
                "items": MenuItemSerializer(popular_items, many=True, context=self.get_serializer_context()).data
            }
            result_data.insert(0, popular_category)
        return Response(result_data)


class MenuItemView(PublicJSONRendererMixin, RetrieveAPIView):
    queryset = MenuItem.objects.filter(is_hidden=False)
    serializer_class = MenuItemSerializer
    pagination_class = None


class CartCategoryMenuItemView(PublicJSONRendererMixin, ListAPIView):
    queryset = MenuItem.objects.filter(is_hidden=False, is_cart_category=True)
    serializer_class = MenuItemSerializer
    pagination_class = None
