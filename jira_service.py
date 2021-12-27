"""Module to contain jira main service"""
import logging
import threading
import time
from dataclasses import dataclass

import jira
import requests

from jira_handlers import HANDLER_TYPES, JiraHandler


@dataclass
class JiraProcess:
    """Class to contain jira hanlders processes"""
    process: JiraHandler
    ticket: jira.Issue
    issue_key: str
    status: str = "running"


class JiraService(threading.Thread):
    """Jira service to automate issue solving

    :param logger: logger
    :param jira_config: jira config
    :param database_config: database config
    :param process_queue: process queue
    :param process_queue_size: process queue size
    :param sleep_time: sleep time

    :type logger: logging.Logger
    :type jira_config: dict
    :type database_config: dict
    :type process_queue: list
    :type process_queue_size: int
    :type sleep_time: int

    :return: None
    """
    def __init__(self, logger: logging.Logger, jira_config: dict,
                 database_config: dict, PROCESS_QUEUE: list, mail_list_lookup_code: str,
                 PROCESS_QUEUE_SIZE: int = 10, sleep_time: int = 60) -> None:
        threading.Thread.__init__(self)
        self.logger = logger
        self.daemon = True
        self.alive = True
        self.process_queue_size = PROCESS_QUEUE_SIZE
        self.process_queue = PROCESS_QUEUE
        self.search_query = jira_config['jql_master']
        self.jira_config = jira_config
        self.sleep_time = sleep_time
        self.sleep = False
        self.database_config = database_config
        self.connection = None

        self.handlers_not_found = set()
        self.mail_list_lookup_code = mail_list_lookup_code

    def run(self) -> None:
        """Start jira service"""
        self.logger.info("Jira service started")
        self._service_loop()

    def stop(self) -> None:
        """Stop jira service"""
        self.logger.info("Stoping service...")
        self.alive = False

    def _check_queue_size(self) -> None:
        """Check the queue size"""
        if self.process_queue_size == self.process_queue.__len__():
            self.logger.info("Queue is full")
            return True
        return False

    def _service_loop(self) -> None:
        """Service loop"""
        while self.alive:
            self._loop_message()
            self.set_jira_connection()

            if not self.connection:
                continue

            if self._check_queue_size():
                continue

            tickets = self.connection.search_issues(self.search_query)
            if not tickets:
                continue

            for ticket in tickets:
                if self._check_queue_size():
                    continue

                self._create_process(ticket)

    def set_ticket_assignee(self, ticket: object, assignee: str) -> None:
        """Set ticket assignee

        :param ticket: ticket
        :param assignee: assignee

        :type ticket: object
        :type assignee: str

        :return: None
        """
        try:
            ticket.update(fields={"assignee": {"name": assignee}})
        except AttributeError:
            self.logger.error("Ticket assignee error")
            return

    def _create_process(self, ticket: object) -> None:
        """Create process

        :param ticket: ticket
        :type ticket: object

        :return: None
        """
        handler = self._get_handler(ticket.fields.summary)
        if not handler:
            return

        process: JiraHandler = handler(ticket, self.database_config,
                                       self.logger, self.connection, self.mail_list_lookup_code)

        self.set_ticket_assignee(ticket=ticket, assignee=self.jira_config['user'])
        self.process_queue.append(JiraProcess(process, ticket, ticket.key))
        try:
            process.start()
        except RuntimeError as error:
            self.logger.error("Process error")
            ticket.comment("Process error: {}".format(error))
            self.process_queue.popleft()
            return None

    def _get_handler(self, handler_type: str) -> object:
        """Get handler

        :param handler_type: handler type
        :type handler_type: str

        :return: handler type class
        """
        if handler_type in self.handlers_not_found:
            return None

        try:
            return HANDLER_TYPES[handler_type]
        except KeyError:
            self.logger.error(f'Handler type "{handler_type}" not found')
            self.handlers_not_found.add(handler_type)
            return None

    def _loop_message(self) -> None:
        """Loop message"""
        if self.sleep:
            time.sleep(self.sleep_time)
        else:
            self.sleep = True
        self.logger.info("Jira service loop")

    def set_jira_connection(self) -> None:
        """Sets self.connection as a new jira.JIRA instance"""
        try:
            self.connection: jira.JIRA = jira.JIRA(
                server=self.jira_config['server'],
                basic_auth=(self.jira_config['user'], self.jira_config['password']),
                max_retries=0, timeout=5,
            )
        except (ConnectionError, AttributeError, requests.exceptions.ConnectTimeout):
            self.logger.error("Jira connection error")
            self.connection = None
        except jira.exceptions.JIRAError as error:
            self.logger.error("Jira error: %s", str(error))
            self.connection = None
