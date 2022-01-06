from __future__ import absolute_import

import logging
import os
import re

import jira
import pandas

from handlers.jira_handler import JiraHandler, JiraHandlerData, Status


class TlpUpdateHandler(JiraHandler):
    """Halndles the tlp requests"""
    def __init__(self, ticket, database_config: dict, logger: logging.Logger,
                 jira_session: jira.JIRA, lookup_code: str) -> None:
        super().__init__(ticket=ticket, database_config=database_config,
                         logger=logger, jira_session=jira_session, lookup_code=lookup_code)
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
        attach_filename = self.download_tlp_file()

        if not self.valid_file:
            self.logger.error(f"[{self.ticket.key}]: File is not valid")
            self.include_comment("Arquivo não é valido")
            return

        self.set_status(Status.TAKE.value)
        self.set_status(Status.ANALYZE_THE_PROBLEM.value)
        self.set_status(Status.WORK_IN_LOCAL_SOLUTION.value)

        tlp_file = self.read_xls_file(attach_filename)
        if not tlp_file:
            self.logger.error(f"[{self.ticket.key}]: File is not valid")
            self.include_comment("Arquivo não é valido")
            return

        commands = self.get_insert_update_commands()
        for line in tlp_file:
            self.execute_command(commands, line)

        self.include_comment("Tlp processado, ticket finalizado.")
        self.set_status(Status.RESOLVE.value)

        os.remove(attach_filename)

    @staticmethod
    def get_insert_update_commands() -> str:
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
            cursor.execute(command, tlp=commands_args[1], model=commands_args[0])
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

    def download_tlp_file(self) -> str:
        """Downloads file from the ticket"""
        issue = self.jira_session.search_issues(
            f'key = {self.ticket.key}', json_result=True,
            fields="key, attachment"
        )

        attachment = self.jira_session.attachment(
            issue['issues'][0]['fields']['attachment'][0]['id']
        )

        self.attach = attachment.get()
        attach_filename = attachment.filename
        self.valid_file = self.validate_tlp_file_name(attach_filename)

        if self.valid_file:
            with open(attach_filename, 'wb') as file_object:
                file_object.write(self.attach)

            return attach_filename
        return None

    @staticmethod
    def validate_tlp_file_name(file_name) -> None:
        """Use regex to check file name"""
        regex = re.compile(r'^TLP_.*\.xlsx$')
        match = regex.match(file_name)
        if not match:
            return False

        return True

def initialize(handlers_holder: JiraHandlerData) -> None:
    """
    Initializes the credit hold handler.
    """
    handlers_holder.add_handler(TlpUpdateHandler)
