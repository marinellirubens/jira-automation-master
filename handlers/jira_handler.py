"""Module with the handlers for the automations"""
from __future__ import absolute_import

import configparser
import logging
import sys
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List

import jira

import automation_service.database as db


class Status(Enum):
    """Enum with the status code for jira transitions"""
    TAKE = 101
    ANALYZE_THE_PROBLEM = 61
    WORK_IN_LOCAL_SOLUTION = 141
    RESOLVE = 71


# TODO: Improve the logging
class JiraHandler(ABC, threading.Thread):
    """Handler base class"""
    def __init__(self, ticket: jira.Issue, database_config: configparser.ConfigParser,
                 logger: logging.Logger, jira_session: jira.JIRA, lookup_code: str) -> None:
        threading.Thread.__init__(self)
        self.daemon = True
        self.ticket = ticket
        self.database_config = database_config
        self.database = None
        self.logger = logger
        self.jira_session = jira_session
        if self.database_config:
            self.set_database_connection()
        self.mail_list_lookup_code = lookup_code
        self.handler_type = None

    def set_database_connection(self) -> None:
        """Set database connection"""
        self.database = db.Oracle(None)
        try:
            self.database.create_connection(
                user=self.database_config['user'],
                password=self.database_config['password'],
                host=self.database_config['host'],
                port=self.database_config['port'],
                sid=self.database_config['sid'],
            )
        except ConnectionError:
            sys.exit(1)

    @abstractmethod
    def run(self) -> None:
        """Method to be implemented by subclasses."""

    def set_status(self, transition_id: int) -> None:
        """
        Sets the status of a ticket.
        """
        try:
            self.jira_session.transition_issue(self.ticket, transition_id)
        except jira.exceptions.JIRAError:
            self.logger.error(f"[{self.ticket.key}]: Error on transition of status")

    def include_comment(self, comment: str) -> None:
        """
        Adds a comment to a ticket.
        """
        self.jira_session.add_comment(self.ticket, comment)


@dataclass
class JiraHandlerData:
    """Data class for the JiraHandler"""
    handlers_classes: dict
    handlers: Dict[str, str]

    def add_handler(self, handler: JiraHandler) -> None:
        """Add a handler to the list"""
        class_name = handler(None, None, None, None, None).__class__.__name__
        self.handlers_classes[class_name] = handler

    def remove_handler(self, handler: JiraHandler) -> None:
        """Remove a handler from the list"""
        class_name = handler(None, None, None, None, None).__class__.__name__
        del self.handlers_classes[class_name]


def initialize(handlers_holder: JiraHandlerData) -> None:
    """
    Initializes the credit hold handler.
    """
    handlers_holder.add_handler(JiraHandler)
