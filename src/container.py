from dataclasses import dataclass
from src.services.base import OSConsoleServiceBase


@dataclass
class Container:
    console_service: OSConsoleServiceBase
