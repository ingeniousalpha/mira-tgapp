from rest_framework.renderers import JSONRenderer as DefaultJSONRenderer

from .response_handler.services import execute_handler


class JSONRenderer(DefaultJSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        formatted_response = execute_handler(
            data=data,
            raw_response=renderer_context['response'],
        )

        return super(JSONRenderer, self).render(formatted_response, accepted_media_type, renderer_context)
