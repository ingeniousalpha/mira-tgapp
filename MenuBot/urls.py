from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from common.dashboard import dashboard_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/customers/", include("customers.urls")),
    path("api/menu/", include("menu.urls")),
    path('dashboard/', dashboard_view),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.STATIC_URL,
        document_root=settings.STATIC_ROOT
    )
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )