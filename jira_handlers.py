"""Module with the handlers for the automations"""
from __future__ import absolute_import

import logging
import re
import sys
import threading
from abc import ABC, abstractmethod

import jira
import pandas

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
        except jira.exceptions.JIRAError:
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
            # "not exists": "Cliente não esta na lista de credit hold do tms",
            # "disabled": "Cliente ja esta desabilitado da lista de credit hold do TMS",
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

        include_flag = 'Y' if self.operation == 'Incluir' else 'N'
        status = self.credit_hold_include(include_flag)

        self.include_comment(self.possible_outcomes[status])
        if status == "error":
            # TODO: Send email to the team
            return

        self.include_comment("Credit Hold processado, ticket finalizado.")
        self.set_status(self.statusses["Resolve"])

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
            return "exists" if include_flag == 'Y' else "disabled"

        self.execute_command(update_credit_hold_command, self.client_code, include_flag)
        return "updated"


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
        self.valid_file = False
        self.columns_validation = [
            'MODEL_CODE', 'CBM', 'WEIGHT', 'HEIGHT', 'WIDTH', 'DEPTH',
            '=ARRUMAR(SUBSTITUIR(F1;CARACT(160);CARACT(32)))', 'Unnamed: 7',
            'Unnamed: 8', 'Unnamed: 9', 'Products', 'Unnamed: 11', 'Unnamed: 12',
            'Unnamed: 13', 'Unnamed: 14', 'Unnamed: 15', 'Unnamed: 16',
            'Unnamed: 17'
        ]

    def run(self) -> None:
        """Runs the main execution steps"""
        self.download_tlp_file()

        if not self.valid_file:
            self.logger.error("File is not valid")
            self.include_comment("Arquivo não é valido")
            return

        self.set_status(self.statusses["Take"])
        self.set_status(self.statusses["Analyze the problem"])
        self.set_status(self.statusses["Work in local solution"])

        tlp_file = self.read_xls_file(self.attach.filename)
        if not tlp_file:
            self.logger.error("File is not valid")
            self.include_comment("Arquivo não é valido")
            return

        commands = self.set_commands()
        for line in tlp_file:
            self.execute_command(commands, line)

        self.include_comment("Tlp processado, ticket finalizado.")
        self.set_status(self.statusses["Resolve"])

    @staticmethod
    def set_commands() -> str:
        """Function to define the commands to be executed on database

        :param parameters: List with the data to be inserted/updated on database.
        :type parameters: list
        :return: Return the commands to be executed.
        :rtype: str
        """
        command_update = """update tb_ocs_tlp
                    set tlp            = :tlp, 
                        div_code       = 'LGBR', 
                        final_user_id  = 'TMS', 
                        use_yn         = 'Y',
                        update_date    = sysdate
                    where model = :model"""

        command_insert = """
            insert into tb_ocs_tlp (model,tlp,div_code,create_date,final_user_id,use_yn)
            select  :model, :tlp, 'LGBR', sysdate, 'TMS', 'Y'
            from dual
            where not exists (select * from tb_ocs_tlp where model = :model)"""

        return command_update, command_insert

    def execute_command(self, commands: tuple, commands_args: tuple) -> None:
        """Function to connect on database and execute tho commands.

        :param commands: Commands to be executed.
        :type commands: str
        """
        cursor = self.database.get_cursor()
        for command in commands:
            cursor.execute(command, commands_args)
        self.database.connection.commit()

    def read_xls_file(self, excel_file) -> list:
        """ Function to extract TLP data from an excel file and returns a list with these values.

        :param excel_file: Excel file path
        :type excel_file: str
        :return: List with the data extracted from excel file.
        :rtype: list
        """
        excel_lines = []
        excel = pandas.read_excel(excel_file, engine='openpyxl', sheet_name='Plan1')

        if not all(excel.columns == self.columns_validation):
            self.valid_file = False
            return None

        for row in excel.iloc[1:].iterrows():
            excel_lines.append([row[1].iloc[10] , row[1].iloc[16]])

        return excel_lines

    def download_tlp_file(self) -> None:
        """Downloads file from the ticket"""
        issue = self.jira_session.search_issues(
            f'key = {self.ticket.key}', json_result=True,
            fields="key, attachment"
        )

        attachment = self.jira_session.attachment(
            issue['issues'][0]['fields']['attachment'][0]['id']
        )

        self.attach = attachment.get()

        self.valid_file = self.check_tlp_file_name(self.attach.filename)

        if self.valid_file:
            with open(self.attach.filename, 'wb') as file_object:
                file_object.write(self.attach)

    @staticmethod
    def check_tlp_file_name(file_name) -> None:
        """Use regex to check file name"""
        regex = re.compile(r'^TLP_.*\.xlsx$')
        match = regex.match(file_name)
        if not match:
            return False

        return True

HANDLER_TYPES = {
    "TMS: Registrar cliente para Credit Hold": CreditHoldHandler,
    "TMS: Solicitação de acesso": CreateUserHandler,
    "Atualização de Tlp": TlpUpdateHandler,
}
