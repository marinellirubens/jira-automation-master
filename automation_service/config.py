"""Module to handle the setup/configuration methods"""
# from __future__ import annotations


import logging
import configparser
import sys
import os
import json
import pathlib

from enum import Enum


DEFAULT_CONFIG_FILE = 'config.ini'

def set_file_handler_args_kwargs(log_folder: str, log_file: str) -> tuple:
    """Returns the args and kwargs for the file handler

    :param log_file: name of the config file
    :type log_file: str
    :param log_folder: folder where the config file is
    :type log_folder: str
    :return: args and kwargs
    :rtype: tuple
    """

    log_path = pathlib.Path(log_folder, log_file)
    checks_log_folder(log_folder)

    handler_args = []
    handler_kwargs = {'filename': log_path.as_posix()}

    return handler_args, handler_kwargs


def checks_log_folder(log_folder: str) -> bool:
    """Checks if the log folder exists if does not creates it

    :param log_folder: folder where the log file is
    :type log_folder: str
    :return: True if the folder exists, False otherwise
    :rtype: bool
    """
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)
        return True
    return False


class LogHandler(Enum):
    """Enum to define the log handler"""
    CONSOLE = (logging.StreamHandler, None)
    FILE = (logging.FileHandler, set_file_handler_args_kwargs)


def set_logger(log_file: str = 'jira_auto_main.log',
               log_folder='logs', logger_name: str = __name__) -> logging.Logger:
    """Set the logger

    :param log_file: name of the log file, defaults to 'jira_auto_main.log'
    :type log_file: str, optional
    :param log_folder: folder where the log file is, defaults to 'logs'
    :type log_folder: str, optional
    :return: logger
    """
    logger = logging.getLogger(logger_name)
    if not logger:
        logger = logging.Logger(logger_name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s - %(module)s.%(funcName)s:%(lineno)d - %(levelname)s - %(message)s'
    )
    for handler_type in LogHandler:
        handler_args, handler_kwargs = [], {}
        if handler_type.value[1]:
            handler_args, handler_kwargs = handler_type.value[1](log_folder, log_file)

        handler = get_log_handler(handler_type, formatter, handler_args, handler_kwargs)
        logger.addHandler(handler)
    return logger

def get_log_handler(
    handler_type: LogHandler,
    formatter: logging.Formatter,
    handler_args: list = None,
    handler_kwargs: dict = None) -> logging.Handler:
    """Returns a log handler

    :param handler_type: type of the handler
    :type handler_type: LogHandler
    :param formatter: formatter of the handler
    :type formatter: logging.Formatter
    :return: handler
    """
    handler = handler_type.value[0](*handler_args, **handler_kwargs)
    handler.setFormatter(formatter)
    return handler


def get_config(config_file: str, logger: logging.Logger = None) -> dict:
    """Read the configuration file

    :param config_file: name of the config file
    :type config_file: str
    :param logger: logger, defaults to None
    :type logger: logging.Logger, optional
    :return: config
    """
    if not logger:
        logger = set_logger()

    try:
        config_file_path = os.path.abspath(os.path.join('./config', config_file)).replace('\\', '/')
        config = configparser.ConfigParser()
        with open(config_file_path, encoding="UTF-8") as cfg:
            config.read_file(cfg)
            return config
    except FileNotFoundError:
        logger.error('Config file not found')
        sys.exit(1)


def get_config_handler_file(config_file_name: str) -> dict:
    """Read json file information with handlers

    :param config_file_name: name of the config file
    :type config_file_name: str
    :return: dict with handlers
    """
    config_file_path = os.path.join('config', config_file_name)
    with open(config_file_path, encoding="UTF-8") as json_file:
        data = json.load(json_file)
    return data


def configdecorator(*args, **kwargs): # pylint: disable=unused-argument
    """Decorator to get the config file.

    :param config_file: name of the config file, defaults to 'pre_rate.ini'
    :type config_file: str, optional
    :param config_folder: folder where the config file is, defaults to 'config'
    :type config_folder: str, optional
    :return: decorated function
    :rtype: function
    """
    config_file = kwargs.get('config_file', DEFAULT_CONFIG_FILE)
    if kwargs:
        config_group = kwargs.get('config_group')

        def function_wrapper_param(function, *args, **kwargs): # pylint: disable=unused-argument
            def func_wrapped(*args, **kwargs):
                config = get_config(config_file=config_file)
                if config_group:
                    config = config[config_group]

                return function(config=config, *args, **kwargs)
            return func_wrapped
        return function_wrapper_param

    function = args[0]
    def func_wrapped(*args, **kwargs):
        config = get_config(config_file=config_file)

        return function(config=config, *args, **kwargs)
    return func_wrapped


def logdecorator(function, *args, **kwargs): # pylint: disable=unused-argument
    """Decorator to get the logger."""
    def func_wrapped(*args, **kwargs):
        logger = set_logger()

        return function(logger=logger, *args, **kwargs)
    return func_wrapped
