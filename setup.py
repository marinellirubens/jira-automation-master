"""Module to handle the setup/configuration methods"""
import logging
import configparser
import sys


def set_logger(log_file: str = 'jira_auto_main.log') -> logging.Logger:
    """Set the logger"""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler = logging.FileHandler(log_file)
    stream_handler = logging.StreamHandler()
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger


def get_config(config_file: str, logger: logging.Logger) -> dict:
    """Read the configuration file"""
    try:
        config = configparser.ConfigParser()
        with open(config_file) as cfg:
            config.read_file(cfg)
            return config
    except FileNotFoundError:
        logger.error('Config file not found')
        sys.exit(1)
