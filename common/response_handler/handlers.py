from abc import ABC, abstractmethod
from typing import Dict, Tuple, Optional

from constance import config
from rest_framework.exceptions import ErrorDetail

from constants import error_codes
from .dataclasses import CustomError


class AbstractHandler(ABC):
    _default_error_code: str = None

    def __init__(
            self,
            raw_data: Dict
    ) -> None:
        self.raw_data = raw_data

    def get_error_detail(self) -> Tuple[str, str]:
        _error_code, _error_message = self._default_error_code, ""
        if isinstance(self.raw_data.get("detail"), ErrorDetail):
            _error_code = self.raw_data.get("detail").code
            _error_message = str(self.raw_data.get("detail"))
        _config_error_code = f"{_error_code}"
        if hasattr(config, _config_error_code):
            _error_message = getattr(config, _config_error_code)
        return _error_code, _error_message

    @abstractmethod
    def format_logic(self) -> Tuple[
        Optional[Dict], Optional[Dict]
    ]:
        """
        Response format logic
        """

    def format(self):
        return self.format_logic()


class HandlerCode200(AbstractHandler):
    def format_logic(self):
        return self.raw_data, None


class HandlerCode400(AbstractHandler):
    _default_error_code = error_codes.INVALID_INPUT_DATA

    def format_logic(self):
        return None, CustomError(*self.get_error_detail()).__dict__


class HandlerCode401(AbstractHandler):
    _default_error_code = error_codes.USER_NOT_AUTHORIZED

    def format_logic(self):
        return None, CustomError(*self.get_error_detail()).__dict__


class HandlerCode403(AbstractHandler):
    _default_error_code = error_codes.ACCESS_DENIED

    def format_logic(self):
        return None, CustomError(*self.get_error_detail()).__dict__


class HandlerCode404(AbstractHandler):
    _default_error_code = error_codes.NOT_FOUND

    def format_logic(self):
        return None, CustomError(*self.get_error_detail()).__dict__


class HandlerCode429(AbstractHandler):
    _default_error_code = error_codes.TOO_MANY_REQUEST

    def format_logic(self):
        return None, CustomError(*self.get_error_detail()).__dict__


class HandlerCode500(AbstractHandler):
    _default_error_code = error_codes.INTERNAL_SERVER_ERROR

    def format_logic(self):
        return None, CustomError(*self.get_error_detail()).__dict__
