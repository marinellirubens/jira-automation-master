"""Module to handle the setup/configuration methods"""
import logging
import configparser
import sys
import os
import json

DEFAULT_CONFIG_FILE = 'config.ini'


def set_logger(log_file: str = 'jira_auto_main.log', log_folder='logs') -> logging.Logger:
    """Set the logger"""
    logger = logging.getLogger('__name__')
    if not logger:
        logger = logging.Logger('__name__')

    if logger.handlers:
        return logger

    if not os.path.exists(log_folder):
        os.makedirs(log_folder)

    log_path = os.path.join(log_folder, log_file)

    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s - %(module)s.%(funcName)s:%(lineno)d - %(levelname)s - %(message)s'
    )
    file_handler = logging.FileHandler(log_path)
    stream_handler = logging.StreamHandler()
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger


def get_config(config_file: str, logger: logging.Logger = None) -> dict:
    """Read the configuration file"""
    if not logger:
        logger = set_logger()

    try:
        config_file_path = os.path.join('config', config_file)
        config = configparser.ConfigParser(config_file_path)
        with open(config_file, encoding="UTF-8") as cfg:
            config.read_file(cfg)
            return config
    except FileNotFoundError:
        logger.error('Config file not found')
        sys.exit(1)


def get_config_handler_file(config_file_name: str) -> dict:
    """Read json file information with handlers"""
    config_file_path = os.path.join('config', config_file_name)
    with open(config_file_path, encoding="UTF-8") as json_file:
        data = json.load(json_file)
    return data


def configdecorator(function, *args, **kwargs): # pylint: disable=unused-argument
    """Decorator to get the config file.

    :param function: function to be decorated
    :type function: function
    :param config_file: name of the config file, defaults to 'pre_rate.ini'
    :type config_file: str, optional
    :param config_folder: folder where the config file is, defaults to 'config'
    :type config_folder: str, optional
    :return: decorated function
    :rtype: function
    """
    config_file = kwargs.get('config_file', DEFAULT_CONFIG_FILE)
    config_group = kwargs.get('config_group')
    def func_wrapped(*args, **kwargs):
        config = get_config(config_file=config_file)
        if config_group:
            config = config[config_group]

        return function(config=config, *args, **kwargs)
    return func_wrapped


def logdecorator(function, *args, **kwargs): # pylint: disable=unused-argument
    """Decorator to get the logger."""
    def func_wrapped(*args, **kwargs):
        logger = set_logger()

        return function(logger=logger, *args, **kwargs)
    return func_wrapped
