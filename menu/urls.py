from django.urls import path

from menu.views import MenuView, MenuItemView, CartCategoryMenuItemView

urlpatterns = [
    path('', MenuView.as_view()),
    path('cart-category/', CartCategoryMenuItemView.as_view()),
    path('items/<int:pk>/', MenuItemView.as_view()),
]
