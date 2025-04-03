from django.urls import path
from . import views


urlpatterns = [
    path('click/prepare', views.prepare, name='prepare'),
    path('click/complete', views.complete, name='complete'),
]
