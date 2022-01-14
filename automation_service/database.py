"""Module to handle database connection"""
import logging
from typing import Callable
from typing import Union

import cx_Oracle


class Oracle:
    """Class to handle oracle connection"""
    def __init__(self, logger: logging.Logger = logging.getLogger(__name__)) -> None:
        self.logger: logging.Logger = logger
        self.connection: cx_Oracle.Connection = None
        self.connection_params: tuple = ()

    def create_connection(self, user: str, password: str,
                          host: str, port: str, sid: str) -> cx_Oracle.Connection:
        """Create connection to oracle database"""
        self.logger.debug("Connecting to database")
        try:
            dsn = cx_Oracle.makedsn(host, port, sid)
            self.connection_params = (user, password, dsn)
            self.connection = cx_Oracle.connect(*self.connection_params, threaded = True)
            self.logger.debug("Connected to database")

            return self.connection
        except (cx_Oracle.DatabaseError, ConnectionError) as error:
            self.logger.error(error)
            return None

    def reconnect_to_database(self):
        """Reconnect to database"""
        try:
            self.connection = cx_Oracle.connect(*self.connection_params, threaded = True)
            self.logger.debug("Reconnected to database")

            return self.connection
        except (cx_Oracle.DatabaseError, ConnectionError) as error:
            self.logger.error(error)
            return None

    def get_cursor(self) -> cx_Oracle.Connection.cursor:
        """Get cursor from connection"""
        try:
            cursor = self.connection.cursor()
            return cursor
        except cx_Oracle.DatabaseError as error:
            self.logger.error(error)
            return None

    def close_connection(self) -> bool:
        """Close connection"""
        self.logger.debug("Closing connection")
        try:
            self.connection.close()
            self.logger.debug("Connection closed")

            return True
        except cx_Oracle.DatabaseError as error:
            self.logger.error(error)
            return False

    def row_factory(self, cursor: cx_Oracle.Connection.cursor) -> Callable:
        """Row factory"""
        columns = [col[0] for col in cursor.description]
        return lambda *args: dict(zip(columns, args))

    def query_generator(self, cursor: cx_Oracle.Connection.cursor, fetch_size: int) -> list:
        """Query generator"""
        rows = [1]
        while rows:
            rows = cursor.fetchmany(fetch_size)
            yield rows

    def single_insert_update_on_database(self, command: str, args: Union[list, dict],
                                         log_message: str = None):
        """Update the status of the request on database."""
        message = "Inserting/updating database"
        if log_message:
            message = log_message
        self.logger.info(message)
        self.command_execution(
            command,
            args
        )
        self.connection.commit()

    def is_connected(self):
        """Checks if connection is valid and connected"""
        try:
            return self.connection.ping() is None
        except (cx_Oracle.InterfaceError, cx_Oracle.DatabaseError, ConnectionError):
            return False

    def command_execution(self, command: str, params: list):
        """Query builder"""
        self.logger.debug("Building query")
        if not self.is_connected():
            self.reconnect_to_database()

        try:
            cursor = self.get_cursor()
            cursor.execute(command, params)
            return cursor
        except cx_Oracle.DatabaseError as error:
            self.logger.error(error)
            return None


def get_mail_list(lookup_code: str, oracle: Oracle) -> list:
    """Returns the selected mais list

    :param lookup_code: Code of the mail list
    :type lookup_code: str
    """
    oracle.logger.debug("Getting mail list from data")
    mail_list = []
    cursor = oracle.command_execution(
        "SELECT ATTRIBUTE1 FROM LGE_CODE_LOOKUP WHERE CLASS = "+ \
        "'EMAIL_LIST' AND CODE = :lookup_code and enabled = 'Y'",
        [lookup_code]
    )
    try:
        row = cursor.fetchone()
        if row:
            for email in row[0].split(';'):
                if email != '':
                    mail_list.append(email)
    except cx_Oracle.DatabaseError as error:
        oracle.logger.error(error)

    return mail_list
