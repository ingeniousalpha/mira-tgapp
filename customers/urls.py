from django.urls import path

from customers.views import CartView, OrderView, InfoView

urlpatterns = [
    path('<int:pk>/info/', InfoView.as_view()),
    path('<int:pk>/cart/', CartView.as_view()),
    path('<int:pk>/orders/', OrderView.as_view()),
]
