from __future__ import absolute_import

import logging

import jira
from handlers.jira_handler import JiraHandlerData, JiraHandler


class CreateUserHandler(JiraHandler):
    """Handles the user creation requests"""
    def __init__(self, ticket, database_config: dict, logger: logging.Logger,
                 jira_session: jira.JIRA, lookup_code: str) -> None:
        super().__init__(ticket=ticket, database_config=database_config,
                         logger=logger, jira_session=jira_session, lookup_code=lookup_code)

    def run(self) -> None:
        pass


class UserPasswordResetHandler(JiraHandler):
    """Handles the user creation requests"""
    def __init__(self, ticket, database_config: dict, logger: logging.Logger,
                jira_session: jira.JIRA, lookup_code: str) -> None:
        super().__init__(ticket=ticket, database_config=database_config,
                         logger=logger, jira_session=jira_session, lookup_code=lookup_code)

    def run(self) -> None:
        pass
    
def initialize(handlers_holder: JiraHandlerData) -> None:
    """
    Initializes the credit hold handler.
    """
    handlers_holder.add_handler(CreateUserHandler)
    handlers_holder.add_handler(UserPasswordResetHandler)