"""Tests for module automation_service.loader"""
from unittest import mock

import pytest
from automation_service import loader
from handlers import jira_handler


def test_handler_interface():
    """Test the handler interface"""
    assert loader.HandlerInterface.initialize() is None


def test_instance_of_handler_interface():
    """Test the instance of the handler interface"""
    with pytest.raises(TypeError):
        loader.HandlerInterface() # pylint: disable=abstract-class-instantiated


def test_import_module():
    """Tests the import module"""
    assert loader.import_module("automation_service.loader") is not None


@mock.patch("handlers.jira_handler.JiraHandler")
def test_load_handlers(mock_handler: mock.MagicMock) -> None:
    """Tests the load handlers"""
    holder = jira_handler.JiraHandlerData({},{})
    assert loader.load_handlers(["handlers.jira_handler"], holder) is None
    assert isinstance(holder.handlers_classes, dict)
    assert holder.handlers_classes != {} # pylint: disable=use-implicit-booleaness-not-comparison
    assert mock_handler.call_count == 1
