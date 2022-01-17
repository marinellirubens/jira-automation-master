"""Module to test main module automation_service.jira_service"""
import threading
from unittest import mock
import pytest
import jira
import requests

from automation_service import jira_service
from handlers import jira_handler


JIRA_CONFIG_MOCK = {
    'jql_master': '',
    'user': '',
    'server': '',
    'password': '',
}
DATABASE_CONFIG = {}


def get_jira_instance(
        logger,
        process_queue=' '.split(),
        process_queue_size = 10
    ):
    """Gets jira instance for testing"""
    service = jira_service.JiraService(
        logger=logger,
        jira_config=JIRA_CONFIG_MOCK,
        database_config=DATABASE_CONFIG,
        PROCESS_QUEUE=process_queue,
        mail_list_lookup_code='teste',
        PROCESS_QUEUE_SIZE=process_queue_size,
        sleep_time=60,
    )
    return service


@mock.patch('logging.Logger')
def test_jira_service_instance(mock_logger: mock.MagicMock = None):
    """Method to test Jira service instance"""
    process_queue=[]
    process_queue_size = 10

    service = jira_service.JiraService(
        logger=mock_logger,
        jira_config=JIRA_CONFIG_MOCK,
        database_config=DATABASE_CONFIG,
        PROCESS_QUEUE=process_queue,
        mail_list_lookup_code='teste',
        PROCESS_QUEUE_SIZE=process_queue_size,
        sleep_time=60,
    )

    assert service.logger == mock_logger
    assert isinstance(service, jira_service.JiraService)
    assert isinstance(service, threading.Thread)

    assert service.process_queue == process_queue
    assert service.process_queue_size == process_queue_size
    assert service.alive
    assert service.is_alive() is False

    assert service.handlers_holder is None

    return service


@mock.patch('automation_service.config.get_config_handler_file')
@mock.patch('automation_service.loader.load_handlers')
@mock.patch('logging.Logger')
def test_jira_service_run(
        mock_logger: mock.MagicMock,
        mock_load_handlers: mock.MagicMock,
        mock_get_config_handler_file: mock.MagicMock,
    ):
    """Method to test Jira service run"""
    service = get_jira_instance(mock_logger)

    with mock.patch.object(service, '_service_loop') as mock_service_loop:
        service.run()

        assert mock_logger.info.call_count == 1

        assert service.alive
        assert service.is_alive() is False

        mock_load_handlers.assert_called_once()
        mock_get_config_handler_file.assert_called_once()
        assert isinstance(service.handlers_holder, jira_handler.JiraHandlerData)

        mock_service_loop.assert_called_once()


@mock.patch('logging.Logger')
def test_jira_service_stop(mock_logger: mock.MagicMock):
    """Method to test stop method"""
    service = get_jira_instance(mock_logger)

    assert service.alive

    service.stop()
    assert mock_logger.info.call_count == 1
    assert not service.alive


@pytest.mark.parametrize(
    argnames='queue_size,max_queue_size,result,info_call_count',
    argvalues=[(10, 10, True, 1), (1, 0, False, 0)],
    ids=['Full', 'Empty'],
)
@mock.patch('logging.Logger')
def test_jira_service_check_queue_size(
        mock_logger: mock.MagicMock,
        queue_size: int,
        max_queue_size: int,
        result: bool,
        info_call_count: int,
    ):
    """Tests the check_queue_size method"""
    service = get_jira_instance(mock_logger)

    service.process_queue = [None] * queue_size
    service.process_queue_size = max_queue_size
    assert service._check_queue_size() is result

    assert mock_logger.info.call_count == info_call_count


# TODO: parametrize tests with multiple queue zise, connection status and tickets
def test_jira_service_service_loop():
    ...


@mock.patch('logging.Logger')
def test_jira_service_set_ticket_assignee(mock_logger: mock.MagicMock):
    """Test method set_ticket_assignee"""
    service = get_jira_instance(mock_logger)
    ticket = mock.MagicMock()
    service.set_ticket_assignee(ticket, 'teste')
    ticket.update.assert_called_with(fields={"assignee": {"name": "teste"}})


@mock.patch('logging.Logger')
def test_jira_service_set_ticket_assignee_attribute_error(mock_logger):
    """Test method set_ticket_assignee"""
    service = get_jira_instance(mock_logger)
    ticket = mock.MagicMock()

    ticket.update.side_effect = AttributeError('teste')
    service.set_ticket_assignee(ticket, 'teste')
    mock_logger.error.assert_called_with('Ticket assignee error')


def test_jira_service_create_process():
    ...


def test_jira_service_create_process_runtime_error():
    ...


@pytest.mark.parametrize(
    argnames=['handler_type', 'handlers_not_found', 'result', 'handlers', 'handlers_classes'],
    argvalues=[
        ('teste', {'teste'}, None, {}, {}),
        ('teste', set(), mock.MagicMock, {'teste': 'Mock'}, {'Mock': mock.MagicMock}),
        ('error', set(), None, {'teste': 'Mock'}, {'Mock': mock.MagicMock}),
    ],
    ids=['HandlerType not found', 'HandlerType found', 'HandlerType not found, error'],
)
@mock.patch('logging.Logger')
def test_jira_service_get_handler(
        mock_logger: mock.MagicMock,
        handler_type: str,
        handlers_not_found: list,
        result: str,
        handlers: dict,
        handlers_classes: dict,
    ):
    service = get_jira_instance(mock_logger)
    service.handlers_holder = mock.MagicMock()
    service.handlers_holder.handlers = handlers.copy()
    service.handlers_holder.handlers_classes = handlers_classes.copy()

    service.handlers_not_found = handlers_not_found.copy()
    handler = service._get_handler(handler_type)

    assert handler == result


@pytest.mark.parametrize(
    argnames=['handler_type', 'handlers_not_found', 'result', 'handlers', 'handlers_classes'],
    argvalues=[
        ('error', set(), None, {'teste': 'Mock'}, {'Mock': mock.MagicMock}),
    ],
    ids=['HandlerType not found, error 2'],
)
@mock.patch('logging.Logger')
def test_jira_service_get_handler_key_error(
        mock_logger: mock.MagicMock,
        handler_type: str,
        handlers_not_found: list,
        result: str,
        handlers: dict,
        handlers_classes: dict,
    ):
    service = get_jira_instance(mock_logger)
    service.handlers_holder = mock.MagicMock()
    service.handlers_holder.handlers = handlers.copy()
    service.handlers_holder.handlers_classes = handlers_classes.copy()

    service.handlers_not_found = handlers_not_found.copy()
    handler = service._get_handler(handler_type)

    mock_logger.error.assert_called_once()
    assert service.handlers_not_found != handlers_not_found
    assert handler == result


@pytest.mark.parametrize(
    argnames='sleep_value,sleep_time,result',
    argvalues=[(True, 60, True), (False, 60, False)],
    ids=['Sleep', 'No Sleep'],
)
@mock.patch('time.sleep')
@mock.patch('logging.Logger')
def test_jira_service_loop_message(
        mock_logger: mock.MagicMock,
        mock_sleep: mock.MagicMock,
        sleep_value: bool,
        sleep_time: int,
        result: bool
    ):
    """Tets method _loop_message """
    service = get_jira_instance(mock_logger)

    service.sleep_time = sleep_time
    service.sleep = sleep_value
    service._loop_message()
    assert mock_sleep.called is result
    assert mock_logger.info.call_count == 1


@mock.patch('jira.JIRA')
@mock.patch('logging.Logger')
def test_jira_service_set_jira_connection(
        mock_logger: mock.MagicMock,
        mock_jira: mock.MagicMock,
    ):
    """Test method set_jira_connection"""
    service = get_jira_instance(mock_logger)
    service.set_jira_connection()
    assert service.connection is not None
    assert mock_jira.called is True


@mock.patch('jira.JIRA')
@mock.patch('logging.Logger')
def test_jira_service_set_jira_connection_error_on_connection(
        mock_logger: mock.MagicMock,
        mock_jira: mock.MagicMock,
    ):
    """Test method set_jira_connection"""
    service = get_jira_instance(mock_logger)
    mock_jira.side_effect = jira.exceptions.JIRAError('teste')
    service.set_jira_connection()
    assert service.connection is None
    assert mock_logger.error.called is True


@pytest.mark.parametrize(argnames='excetion_type', argvalues=[
    ConnectionError, AttributeError, requests.exceptions.ConnectTimeout
], ids=['ConnectionError', 'AttributeError', 'ConnectTimeout'])
@mock.patch('jira.JIRA')
@mock.patch('logging.Logger')
def test_jira_service_set_jira_connection_error_on_jira(
        mock_logger: mock.MagicMock,
        mock_jira: mock.MagicMock,
        excetion_type: Exception,
    ):
    """Test method set_jira_connection"""
    service = get_jira_instance(mock_logger)
    mock_jira.side_effect = excetion_type('teste')
    service.set_jira_connection()
    assert service.connection is None
    assert mock_logger.error.called is True
