from typing import Dict
from dataclasses import dataclass


@dataclass
class CustomError:
    code: str
    message: str


@dataclass
class CustomResponse:
    data: Dict = None
    error: Dict = None
