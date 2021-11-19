"""Module with the handlers for the automations"""
from __future__ import absolute_import

import logging
import sys
import threading
from abc import ABC, abstractmethod

import jira

import database as db


class JiraHandler(ABC, threading.Thread):
    """Handler base class"""
    def __init__(self, ticket: jira.Issue, database_config: dict,
                 logger: logging.Logger, jira_session) -> None:
        threading.Thread.__init__(self)
        self.daemon = True
        self.ticket = ticket
        self.database_config = database_config
        self.database = None
        self.logger = logger
        self.jira_session = jira_session
        self.set_database_connection()
        self.statusses = {
            "Take" : 101,
            "Analyze the problem" : 61,
            "Work in local solution" : 141,
            "Resolve" : 71,
        }

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
        except jira.exceptions.JIRAError as error:
            self.logger.error("Error on transition of status")

    def include_comment(self, comment: str) -> None:
        """
        Adds a comment to a ticket.
        """
        self.jira_session.add_comment(self.ticket, comment)


class CreditHoldHandler(JiraHandler):
    """Handles the Credit hold requests"""
    def __init__(self, ticket, database_config: dict, logger: logging.Logger, jira_session) -> None:
        super().__init__(ticket=ticket, database_config=database_config,
                         logger=logger, jira_session=jira_session)

        self.client_code = ''
        self.possible_outcomes = {
            "error": "Erro ao incluir cliente na lista de credit hold do tms",

            "created": "Cliente incluido na lista de credit hold do tms",
            "updated": "Cliente alterado na lista de credit hold do tms",
            "exists": "Cliente ja esta na lista de credit hold do TMS",

            "deactivated": "Cliente removido na lista de credit hold do tms",
            "not exists": "Cliente não esta na lista de credit hold do tms",
            "disabled": "Cliente ja esta desabilitado da lista de credit hold do TMS",
        }

    def run(self) -> None:
        """
        Runs the credit hold handler.
        """
        self.set_status(self.statusses["Take"])
        self.set_status(self.statusses["Analyze the problem"])
        self.set_status(self.statusses["Work in local solution"])

        self.client_code = self.ticket.fields.customfield_11701
        self.operation = self.ticket.fields.customfield_11700.value

        if self.operation == 'Incluir':
            status = self.credit_hold_include()
        else:
            status = self.credit_hold_exclude()
        self.include_comment(self.possible_outcomes[status])
        if status == "error":
            # TODO: Send email to the team
            return

        self.include_comment("Credit Hold processado, ticket finalizado.")
        self.set_status(self.statusses["Resolve"])

    def credit_hold_exclude(self) -> bool:
        """
        Checks if a client has a credit hold.
        """
        # self.connection = self.database.create_connection()
        cursor = self.database.get_cursor()
        credit_hold_query = """
            select enabled 
            from   lge_code_lookup 
            where  class = 'CREDIT_HOLD' 
            and    code = :client_code"""

        cursor.execute(credit_hold_query, client_code=self.client_code)
        enabled = cursor.fetchone()

        if not enabled:
            return "not exists"

        if enabled[0] == 'N':
            return "disabled"

        self.deactivate_credit_hold()
        return "deactivated"

    def deactivate_credit_hold(self) -> None:
        """Deactivates credit hold on the database"""
        deactivate_credit_hold_command = """
            update lge_code_lookup
            set enabled = 'N'
            where class = 'CREDIT_HOLD'
            and code = :client_code"""
        cursor = self.database.get_cursor()
        cursor.execute(deactivate_credit_hold_command, client_code=self.client_code)
        self.database.connection.commit()
        return True

    def credit_hold_include(self) -> bool:
        """
        Checks if a client has a credit hold.
        """
        # self.connection = self.database.create_connection()
        cursor = self.database.get_cursor()
        credit_hold_query = """
            select enabled 
            from   lge_code_lookup 
            where  class = 'CREDIT_HOLD' 
            and    code = :client_code"""

        cursor.execute(credit_hold_query, client_code=self.client_code)
        enabled = cursor.fetchone()

        if not enabled:
            self.insert_credit_hold()
            return "created"

        if enabled[0] == 'Y':
            return "exists"

        self.activate_credit_hold()
        return "updated"

    def insert_credit_hold(self) -> None:
        """Inserts credit hold on the database"""
        insert_credit_hold_command = """
            insert into lge_code_lookup (class, code, description, enabled)
            values('CREDIT_HOLD', :client_code, 'Customer with credit on Hold', 'Y')"""
        cursor = self.database.get_cursor()
        cursor.execute(insert_credit_hold_command, client_code=self.client_code)
        self.database.connection.commit()
        return True

    def activate_credit_hold(self) -> None:
        """
        Activates a credit hold.
        """
        update_credit_hold_command = """
            update lge_code_lookup
            set    enabled = 'Y'
            where  class = 'CREDIT_HOLD'
            and    code = :client_code"""
        cursor = self.database.get_cursor()

        cursor.execute(update_credit_hold_command, client_code=self.client_code)
        self.database.connection.commit()
        return True


class CreateUserHandler(JiraHandler):
    """Handles the user creation requests"""
    def __init__(self, ticket, database_config: dict, logger: logging.Logger, jira_session) -> None:
        super().__init__(ticket=ticket, database_config=database_config,
                         logger=logger, jira_session=jira_session)

    def run(self) -> None:
        pass


class UserPasswordResetHandler(JiraHandler):
    """Handles the user creation requests"""
    def __init__(self, ticket, database_config: dict, logger: logging.Logger, jira_session) -> None:
        super().__init__(ticket=ticket, database_config=database_config,
                         logger=logger, jira_session=jira_session)

    def run(self) -> None:
        pass


class TlpUpdateHandler(JiraHandler):
    """Halndles the tlp requests"""
    def __init__(self, ticket, database_config: dict, logger: logging.Logger, jira_session) -> None:
        super().__init__(ticket=ticket, database_config=database_config,
                         logger=logger, jira_session=jira_session)

    def run(self) -> None:
        """Runs the main execution steps"""

    def download_tlp_file(self) -> None:
        """Downloads file from the ticket"""

    def check_tlp_file_name(self) -> None:
        """Use regex to check file name"""


HANDLER_TYPES = {
    "TMS: Registrar cliente para Credit Hold": CreditHoldHandler,
    "TMS: Solicitação de acesso": CreateUserHandler,
    "Atualização de Tlp": TlpUpdateHandler,
}
