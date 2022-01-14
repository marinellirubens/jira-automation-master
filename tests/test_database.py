"""Module to handle database tests."""
import logging
from typing import Callable, Generator
from unittest import mock

import cx_Oracle
import pytest

from automation_service.database import Oracle, get_mail_list

class CursorMock:
    """Mock class for cursor."""
    def __init__(self, *args, **kwargs):
        """Initialize mock."""
        # self.fetchall = mock.MagicMock(side_effect=collateral_database_error)
        # self.execute = mock.MagicMock(side_effect=collateral_command_execution)
        # self.fetchone = mock.MagicMock(side_effect=collateral_database_error)

    def fetchone(self):
        """Mock fetchone."""
        return ['teste;teste1']

def collateral_database_error(*args, **kwargs):
    """Function to simulate database error."""
    raise cx_Oracle.DatabaseError('test')


def collateral_command_execution(*args, **kwargs):
    """Function to simulate query builder."""
    return CursorMock(*args, **kwargs)


@mock.patch.object(logging, 'Logger')
def test_oracle_connection_error(logger_mock):
    """Test Oracle connection."""
    oracle = Oracle(logger_mock)
    assert oracle.connection is None

    oracle.create_connection('user', 'password', 'host', 'port', 'sid')
    assert oracle.connection is None


@mock.patch.object(logging, 'Logger')
def test_oracle_connection_success(logger_mock):
    """Test Oracle connection."""
    oracle = Oracle(logger_mock)
    assert oracle.connection is None
    with mock.patch('cx_Oracle.connect') as mock_oracle:
        result_set = {}
        mock_oracle.cursor.callfunc.fetch_all = result_set

        oracle.create_connection('user', 'password', 'host', 'port', 'sid')
        assert oracle.connection is not None

@mock.patch('cx_Oracle.connect')
@mock.patch.object(logging, 'Logger')
def test_query_generator_success(logger_mock, mock_oracle):
    """Test command_execution."""
    oracle = Oracle(logger_mock)
    result_set = {}
    mock_oracle.cursor.callfunc.fetch_all = result_set
    mock_oracle.cursor.callfunc.fetchone = result_set

    oracle.create_connection('user', 'password', 'host', 'port', 'sid')
    cursor = oracle.command_execution(
        "SELECT ATTRIBUTE1 FROM LGE_CODE_LOOKUP WHERE CLASS = "+ \
        "'EMAIL_LIST' CODE = :lookup_code and enabled = 'Y'",
        ['teste']
    )

    def fetchmany(fetch_size):
        return [x for x in range(fetch_size)]

    cursor.fetchmany = fetchmany
    # teste = oracle

    generator = oracle.query_generator(cursor, 10)

    assert generator is not None
    assert isinstance(generator, Generator)

    for rows in generator:
        assert isinstance(rows, list)
        assert rows == [0,1,2,3,4,5,6,7,8,9]
        break


@mock.patch('cx_Oracle.connect')
@mock.patch.object(logging, 'Logger')
def test_row_factory_success(logger_mock, mock_oracle):
    """Test command_execution."""
    oracle = Oracle(logger_mock)
    result_set = {}
    mock_oracle.cursor.callfunc.fetch_all = result_set
    mock_oracle.cursor.callfunc.fetch_one = result_set

    oracle.create_connection('user', 'password', 'host', 'port', 'sid')
    cursor = oracle.command_execution(
        "SELECT ATTRIBUTE1 FROM LGE_CODE_LOOKUP WHERE CLASS = "+ \
        "'EMAIL_LIST' CODE = :lookup_code and enabled = 'Y'",
        ['teste']
    )

    rowfactory = oracle.row_factory(cursor)

    assert rowfactory is not None
    assert isinstance(rowfactory, Callable)


@mock.patch('cx_Oracle.connect')
@mock.patch.object(logging, 'Logger')
def test_command_execution_success(logger_mock, mock_oracle):
    """Test command_execution."""
    oracle = Oracle(logger_mock)
    result_set = {}
    mock_oracle.cursor.callfunc.fetch_all = result_set
    mock_oracle.cursor.callfunc.fetch_one = result_set

    oracle.create_connection('user', 'password', 'host', 'port', 'sid')
    cursor = oracle.command_execution(
        "SELECT ATTRIBUTE1 FROM LGE_CODE_LOOKUP WHERE CLASS = "+ \
        "'EMAIL_LIST' CODE = :lookup_code and enabled = 'Y'",
        ['teste']
    )

    assert cursor is not None


@mock.patch.object(logging, 'Logger')
@mock.patch('cx_Oracle.connect')
def test_command_execution_error(mock_oracle: mock.MagicMock, logger: mock.MagicMock):
    """Test command_execution."""
    oracle = Oracle(logger)
    result_set = {}
    mock_oracle.cursor.callfunc.fetch_all = result_set
    mock_oracle.cursor.callfunc.fetch_one = result_set

    def return_mock_cursor(*args, **kwargs): # pylint: disable=unused-argument
        cursor = oracle._get_cursor() # pylint: disable=protected-access
        cursor.execute = collateral_database_error
        return cursor

    oracle.create_connection('user', 'password', 'host', 'port', 'sid')
    oracle._get_cursor = oracle.get_cursor # pylint: disable=protected-access
    oracle.get_cursor = return_mock_cursor
    # mock_oracle.cursor.execute = collateral_database_error
    cursor = oracle.command_execution(
        "SELECT ATTRIBUTE1 FROM LGE_CODE_LOOKUP WHERE CLASS = "+ \
        "'EMAIL_LIST' CODE = :lookup_code and enabled = 'Y'",
        ['teste']
    )

    assert cursor is None


@mock.patch('cx_Oracle.connect')
@mock.patch.object(logging, 'Logger')
def test_get_mail_list_success(logger_mock, mock_oracle):
    """Test get_mail_list."""
    oracle = Oracle(logger_mock)
    result_set = {}
    mock_oracle.cursor.callfunc.fetch_all = result_set
    mock_oracle.cursor.callfunc.fetch_one = result_set

    oracle.create_connection('user', 'password', 'host', 'port', 'sid')
    oracle.command_execution = collateral_command_execution
    result = get_mail_list('teste', oracle)

    assert result is not None
    assert isinstance(result, list)
    assert result == ['teste', 'teste1']


@mock.patch('cx_Oracle.connect')
@mock.patch.object(logging, 'Logger')
def test_get_mail_list_error(logger_mock, mock_oracle):
    """Test get_mail_list error."""
    oracle = Oracle(logger_mock)
    result_set = {}
    mock_oracle.cursor.callfunc.fetch_all = result_set
    # mock_oracle.cursor.callfunc.fetch_one = None
    oracle.create_connection('user', 'password', 'host', 'port', 'sid')

    def return_mock_cursor(*args, **kwargs): # pylint: disable=unused-argument
        cursor = oracle.get_cursor()
        cursor.fetchone = collateral_database_error
        return cursor

    oracle.command_execution = return_mock_cursor

    result = get_mail_list('teste', oracle)
    assert result == [] # pylint: disable=use-implicit-booleaness-not-comparison


@mock.patch('cx_Oracle.connect')
@mock.patch.object(logging, 'Logger')
def test_get_mail_list_error_on_list(logger_mock, mock_oracle):
    """Test get_mail_list error."""
    oracle = Oracle(logger_mock)
    result_set = {}
    mock_oracle.cursor.callfunc.fetch_all = result_set
    # mock_oracle.cursor.callfunc.fetch_one = ['teste;asdasd'
    oracle.create_connection('user', 'password', 'host', 'port', 'sid')

    def return_mock_cursor(*args, **kwargs): # pylint: disable=unused-argument
        cursor = oracle.get_cursor()
        cursor.fetchone = lambda: 1
        return cursor


    with pytest.raises(TypeError):
        oracle.command_execution = return_mock_cursor

        result = get_mail_list('teste', oracle)
        assert result == [] # pylint: disable=use-implicit-booleaness-not-comparison


@mock.patch('cx_Oracle.connect')
@mock.patch.object(logging, 'Logger')
def test_get_cursor_error(logger_mock, mock_oracle):
    """Test get_cursor."""
    oracle = Oracle(logger_mock)
    result_set = {}
    mock_oracle.cursor.callfunc.fetch_all = result_set
    mock_oracle.cursor.callfunc.fetch_one = None

    oracle.create_connection('user', 'password', 'host', 'port', 'sid')
    oracle.connection.cursor = collateral_database_error
    cursor = oracle.get_cursor()

    assert cursor is None


@mock.patch('cx_Oracle.connect')
@mock.patch.object(logging, 'Logger')
def test_close_connection_error(logger_mock, mock_oracle):
    """Test close_connection."""
    oracle = Oracle(logger_mock)
    result_set = {}
    mock_oracle.cursor.callfunc.fetch_all = result_set

    oracle.create_connection('user', 'password', 'host', 'port', 'sid')
    oracle.connection.close = collateral_database_error

    _return = oracle.close_connection()
    assert _return is not None
    assert _return is False


@mock.patch('cx_Oracle.connect')
@mock.patch.object(logging, 'Logger')
def test_close_connection(logger_mock, mock_oracle):
    """Test close_connection."""
    oracle = Oracle(logger_mock)
    result_set = {}
    mock_oracle.cursor.callfunc.fetch_all = result_set

    oracle.create_connection('user', 'password', 'host', 'port', 'sid')

    _return = oracle.close_connection()
    assert _return is not None
    assert _return is True


@mock.patch('cx_Oracle.connect')
@mock.patch.object(logging, 'Logger')
def test_single_insert_update_on_database(logger_mock, mock_oracle: mock.MagicMock):
    """Test close_connection."""
    oracle = Oracle(logger_mock)
    mock_logger_type = mock.patch.object(oracle, 'logger')
    mock_logger = mock_logger_type.start()

    # mock_logger.autospec = oracle.logger
    result_set = {}
    mock_oracle.cursor.callfunc.fetch_all = result_set

    oracle.create_connection('user', 'password', 'host', 'port', 'sid')
    with mock.patch.object(oracle, 'connection'): # as mock_connection:
        message = 'teste single_insert_update_on_database'
        oracle.single_insert_update_on_database(
            'insert into teste (teste) values (:teste)',
            ['teste'],
            message
        )

        mock_logger.info.assert_called_with(message)
        # mock_connection.assert_called_once()

        oracle.single_insert_update_on_database(
            'insert into teste (teste) values (:teste)',
            ['teste']
        )

        mock_logger.info.assert_called_with("Inserting/updating database")
    mock_logger_type.stop()


@mock.patch('cx_Oracle.connect')
@mock.patch.object(logging, 'Logger')
def test_is_connected(logger_mock, mock_oracle):
    """Test close_connection."""
    oracle = Oracle(logger_mock)
    result_set = {}
    mock_oracle.cursor.callfunc.fetch_all = result_set
    oracle.create_connection('user', 'password', 'host', 'port', 'sid')

    oracle.connection.ping.return_value = None

    # assert oracle.connection.ping()
    connected = oracle.is_connected()
    assert connected

    oracle.connection.ping.side_effect = ConnectionError('')
    connected = oracle.is_connected()
    assert connected is False


@mock.patch('cx_Oracle.connect')
@mock.patch.object(logging, 'Logger')
def test_reconnect_to_database(logger_mock, mock_oracle):
    """Test close_connection."""
    oracle = Oracle(logger_mock)
    result_set = {}
    mock_oracle.cursor.callfunc.fetch_all = result_set
    oracle.create_connection('user', 'password', 'host', 'port', 'sid')

    ret = oracle.reconnect_to_database()
    assert ret is not None

    mock_oracle.side_effect = ConnectionError('')
    ret = oracle.reconnect_to_database()
    assert ret is None
