from __future__ import absolute_import

import logging

import jira

import automation_service.database as db
import automation_service.email as email
from handlers.jira_handler import JiraHandler, JiraHandlerData, Status


class CreditHoldHandler(JiraHandler):
    """Handles the Credit hold requests"""
    def __init__(self, ticket, database_config: dict, logger: logging.Logger,
                 jira_session: jira.JIRA, lookup_code: str) -> None:
        super().__init__(ticket=ticket, database_config=database_config,
                         logger=logger, jira_session=jira_session, lookup_code=lookup_code)

        self.client_code = ''
        self.possible_outcomes = {
            "error": "Erro ao incluir cliente na lista de credit hold do tms",

            "created": "Cliente incluido na lista de credit hold do tms",
            "updated": "Cliente alterado na lista de credit hold do tms",
            "exists": "Cliente ja esta na lista de credit hold do TMS",

            "deactivated": "Cliente removido na lista de credit hold do tms",
            # "not exists": "Cliente não esta na lista de credit hold do tms",
            # "disabled": "Cliente ja esta desabilitado da lista de credit hold do TMS",
        }

    def run(self) -> None:
        """
        Runs the credit hold handler.
        """
        self.set_status(Status.TAKE.value)
        self.set_status(Status.ANALYZE_THE_PROBLEM.value)
        self.set_status(Status.WORK_IN_LOCAL_SOLUTION.value)

        self.client_code = self.ticket.fields.customfield_11701
        operation = self.ticket.fields.customfield_11700.value

        include_flag = 'Y' if operation == 'Incluir' else 'N'
        status = self.credit_hold_include(include_flag)

        self.include_comment(self.possible_outcomes[status])
        if status == "error":
            message_body = "Erro ao incluir cliente na lista de credit hold do tms"
            message_builder = email.MessageBuilder(subject='[JIRA] Error on handler',
                                                   body=message_body,
                                                   sender_email='brtms@lge.com', mime_type='plain')

            receiver_email_list = db.get_mail_list(self.mail_list_lookup_code, self.database)
            if not receiver_email_list:
                return

            message = message_builder.build()
            sender = email.EmailSender(port=25, smtp_server='lgekrhqmh01.lge.com',
                                       sender_email='brtms@lge.com', )
            sender.send_email(receiver_email_list, message)
            return

        self.include_comment("Credit Hold processado, ticket finalizado.")
        self.set_status(Status.RESOLVE.value)

    @staticmethod
    def set_database_commands():
        """
        Sets the database commands to be executed.
        """
        insert_credit_hold_command = """
            insert into lge_code_lookup (class, code, description, enabled)
            values('CREDIT_HOLD', :client_code, 'Customer with credit on Hold', :enabled)"""

        update_credit_hold_command = """
            update lge_code_lookup
            set enabled = :enabled
            where class = 'CREDIT_HOLD'
            and code = :client_code"""

        credit_hold_query = """
            select enabled
            from   lge_code_lookup
            where  class = 'CREDIT_HOLD'
            and    code = :client_code"""

        return credit_hold_query, update_credit_hold_command, insert_credit_hold_command

    def execute_command(self, command: str, client_code: str, enabled: str) -> None:
        """execute command for credit hold on the database"""
        cursor = self.database.get_cursor()
        cursor.execute(command, client_code=client_code, enabled=enabled)
        self.database.connection.commit()
        return True

    def credit_hold_include(self, include_flag: str) -> bool:
        """
        Checks if a client has a credit hold.
        """
        # self.connection = self.database.create_connection()
        cursor = self.database.get_cursor()
        credit_hold_query, update_credit_hold_command, insert_credit_hold_command = \
            self.set_database_commands()

        cursor.execute(credit_hold_query, client_code=self.client_code)
        enabled = cursor.fetchone()

        if not enabled and include_flag == 'Y':
            self.execute_command(insert_credit_hold_command, self.client_code, include_flag)
            return "created"

        if enabled[0] == include_flag:
            return "exists" if include_flag == 'Y' else "deactivated"

        self.execute_command(update_credit_hold_command, self.client_code, include_flag)
        return "updated"


def initialize(handlers_holder: JiraHandlerData) -> None:
    """
    Initializes the credit hold handler.
    """
    handlers_holder.add_handler(CreditHoldHandler)
