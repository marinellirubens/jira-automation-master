"""Module to test the handlers, very basic tests on this case."""
from handlers import jira_handler
from handlers import credit_hold
from handlers import update_tlp
from handlers import user_handlers
from typing import Callable
import threading
import pytest

@pytest.mark.parametrize(
    argnames='module,handler_class',
    argvalues=[
        (jira_handler, jira_handler.JiraHandler),
        (credit_hold, credit_hold.CreditHoldHandler),
        (update_tlp, update_tlp.TlpUpdateHandler),
        (user_handlers, user_handlers.CreateUserHandler)
    ],
    ids=['jira_handler', 'credit_hold', 'update_tlp', 'user_handlers']
)
def test_jira_handler(module, handler_class):
    """Test the JiraHandler class."""
    assert hasattr(module, 'initialize')
    assert isinstance(module.initialize, Callable)
    assert issubclass(handler_class, threading.Thread)
    assert hasattr(handler_class, 'run')
    assert callable(getattr(handler_class, 'run'))
