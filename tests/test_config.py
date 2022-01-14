"""Module to test the setup/configuration methods"""
import configparser
import os
import logging
import uuid
from unittest import mock
import shutil

import pytest
from typing import Tuple

from automation_service.config import get_config
from automation_service.config import set_logger
from automation_service.config import get_config_handler_file
from automation_service.config import configdecorator
from automation_service.config import logdecorator
from automation_service.config import checks_log_folder
from automation_service.config import DEFAULT_CONFIG_FILE


class SetLoggerMock(Exception):
    """Mock the set_logger function"""
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


def mock_set_logger():
    """Mock the set_logger function"""
    raise SetLoggerMock('Mock set_logger')


@mock.patch('logging.getLogger')
@mock.patch('pathlib.Path')
def test_set_logger_if_parent_folder_does_not_exists(
        pathlib_mock: mock.MagicMock,
        get_logger_mock: mock.MagicMock
    ):
    """Method to test set_logger method when parent folder does not exists"""
    logger_name=str(uuid.uuid4())

    pathlib_mock.parent.exists.return_value = False
    get_logger_mock.return_value = None
    with mock.patch('os.stat') as os_stat_mock:
        os_stat_mock.return_value = False
        with mock.patch('os.makedirs') as posix_path_mock:
            with pytest.raises(FileNotFoundError):
                logger = set_logger(
                    log_folder='testasdasd',
                    logger_name=logger_name
                )
                get_logger_mock.assert_called_once_with(logger_name)
                # assert logger.handlers == []
                assert posix_path_mock.call_count == 1
                assert os_stat_mock.call_count == 1
                posix_path_mock.mkdir.assert_called_once()


@mock.patch('logging.Logger')
def test_get_config_file_not_found(logger_mock):
    """Method to test get_config when file not found"""
    logger_mock.info('test_get_config')
    with pytest.raises(SystemExit):
        get_config('config.ini', logger_mock)


def test_check_log_folder_if_folder_exists():
    """Method to test check_log_folder method"""
    with mock.patch('os.makedirs') as posix_path_mock:
        assert checks_log_folder('logs') is False
        posix_path_mock.assert_not_called()

        assert checks_log_folder(str(uuid.uuid4())) is True
        posix_path_mock.assert_called_once()

@mock.patch('builtins.open')
@mock.patch('logging.Logger')
def test_get_config_without_logger(logger_mock: mock.MagicMock, open_mock: mock.MagicMock):
    """Method to test get_config when file not found"""
    with mock.patch('automation_service.config.set_logger') as set_logger_mock:
        set_logger_mock.side_effect = mock_set_logger
        with pytest.raises(SetLoggerMock):
            get_config('config.ini', None)
        set_logger_mock.assert_called_once()

        assert open_mock.call_count == 0


@mock.patch('builtins.open')
@mock.patch('logging.Logger')
def test_get_config(logger_mock: mock.MagicMock, open_mock: mock.MagicMock):
    """Method to test get_config"""
    config = get_config('config.ini', logger_mock)
    open_mock.assert_called_once()
    assert open_mock.call_args == mock.call(
        os.path.abspath(os.path.join('./config', 'config.ini')).replace('\\', '/'),
        encoding="UTF-8")

    assert isinstance(config, configparser.ConfigParser)

def test_set_logger():
    """Method to test set_logger method"""
    logger = set_logger()

    assert logger is not None
    assert isinstance(logger, logging.Logger)


@mock.patch('logging.getLogger')
def test_set_logger_if_there_is_a_logger(get_logger_mock: mock.MagicMock):
    """Method to test set_logger method"""
    get_logger_mock.return_value = None
    logger = set_logger(logger_name='automation_service')
    get_logger_mock.assert_called_once()
    get_logger_mock.assert_called_once_with('automation_service')

    assert logger is not None
    assert isinstance(logger, logging.Logger)


def test_set_logger_if_there_is_already_handlers():
    """Method to test set_logger method"""
    logger = set_logger()

    assert logger is not None
    assert isinstance(logger, logging.Logger)

    logger = set_logger()
    assert logger.handlers != []
    assert logger.handlers.__len__() == 2


@mock.patch('json.load')
@mock.patch('builtins.open')
def test_get_config_handler_file(open_mock: mock.MagicMock,
                                 json_loads_mock: mock.MagicMock):
    """Method to test get_config_handler_file method"""
    json_loads_mock.return_value = {}
    config = get_config_handler_file('config.ini')

    assert isinstance(config, dict)
    assert open_mock.call_args == mock.call('config/config.ini', encoding="UTF-8")

    open_mock.side_effect = FileNotFoundError('test')
    with pytest.raises(FileNotFoundError):
        get_config_handler_file('teste.ini')


@mock.patch('logging.getLogger')
def test_logdecorator(get_logger_mock: mock.MagicMock):
    """Method to test logdecorator method"""
    get_logger_mock.return_value = None
    @logdecorator
    def test_decorator(arg1: str, arg2: str, logger: logging.Logger = None):
        return arg1 + arg2, logger

    return_ = test_decorator('test', 'test')
    assert isinstance(return_, tuple)
    get_logger_mock.assert_called_once()


@mock.patch('automation_service.config')
def test_configdecorator(config_file_mock: mock.MagicMock):
    """Method to test configdecorator method"""
    shutil.copy('./config/config.ini.example', './config/config.ini')

    @configdecorator
    def test_decorator(arg1: str, arg2: str, config: logging.Logger = None):
        return arg1 + arg2, config

    return_: Tuple[str, configparser.ConfigParser] = test_decorator('test', 'test')
    assert isinstance(return_, tuple)
    assert isinstance(return_[1], configparser.ConfigParser)
    assert return_[1].sections() == ['JIRA', 'ORACLE', 'SETUP']
    os.remove('./config/config.ini')


def test_configdecorator_withparameter():
    """Method to test configdecorator method"""
    config_file = 'config.ini.example'

    @configdecorator(config_group='SETUP', config_file=config_file)
    def test_decorator(arg1: str, arg2: str, config: logging.Logger = None):
        return arg1 + arg2, config

    return_: Tuple[str, configparser.ConfigParser] = test_decorator('test', 'test')
    assert isinstance(return_[1], configparser.SectionProxy)
