from typing import Dict, TYPE_CHECKING

from . import handlers
from .dataclasses import CustomResponse

if TYPE_CHECKING:
    from rest_framework.response import Response


def _get_handler_class(status_code: str):
    if status_code.startswith("2"):
        return handlers.HandlerCode200

    if hasattr(handlers, f"HandlerCode{status_code}"):
        return getattr(handlers, f"HandlerCode{status_code}")


def execute_handler(
    data: Dict,
    raw_response: 'Response',
) -> Dict:
    status_code = str(raw_response.status_code)
    handler_class = _get_handler_class(status_code)

    if handler_class is None:
        return data

    data, error = handler_class(data).format()

    return CustomResponse(data, error).__dict__
