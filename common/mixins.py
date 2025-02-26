import traceback

from constance import config
from django.conf import settings
from django.http import JsonResponse
from rest_framework.permissions import AllowAny

from .renderers import JSONRenderer
from .response_handler.dataclasses import CustomError, CustomResponse


class JSONRendererMixin:
    renderer_classes = [JSONRenderer]

    def dispatch(self, request, *args, **kwargs):
        try:
            response = super().dispatch(request, *args, **kwargs)
            print(request)
            return response

        except Exception as e:
            error = CustomError('internal_server_error', str(e)).__dict__
            error['traceback'] = traceback.format_exc()

            if not settings.DEBUG:
                error.pop('traceback')

            return JsonResponse(
                CustomResponse(None, error).__dict__,
                status=500, safe=True,
                json_dumps_params={'ensure_ascii': False}
            )


class PublicAPIMixin:
    permission_classes = [AllowAny]


class PublicJSONRendererMixin(JSONRendererMixin, PublicAPIMixin):
    ...
