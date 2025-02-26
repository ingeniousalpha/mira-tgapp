from django.urls import path

from menu.views import MenuView, MenuItemView

urlpatterns = [
    path('', MenuView.as_view()),
    path('items/<int:pk>/', MenuItemView.as_view()),
]
