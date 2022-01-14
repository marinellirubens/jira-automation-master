from abc import ABC, ABCMeta, abstractmethod
import importlib
from handlers.jira_handler import JiraHandlerData


class HandlerInterface(ABC, metaclass=ABCMeta):
    """Initialize the handler, class used only for typing purposes"""

    @staticmethod
    @abstractmethod
    def initialize():
        """Ïnitilize the handler"""


def import_module(module_name: str) -> HandlerInterface:
    """Import a module"""
    return importlib.import_module(module_name)


def load_handlers(handlers: list, handlers_holder: JiraHandlerData) -> None:
    """Load handlers"""
    for handler in handlers:
        module: HandlerInterface = import_module(handler)
        module.initialize(handlers_holder)
