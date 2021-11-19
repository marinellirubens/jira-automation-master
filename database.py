"""Module to handle database connection"""
import logging

import cx_Oracle


class Oracle:
    """Class to handle oracle connection"""
    def __init__(self, logger: logging.Logger) -> None:
        self.logger = logger
        self.connection = None

    def create_connection(self, user: str, password: str,
                          host: str, port: str, sid: str) -> cx_Oracle.Connection:
        """Create connection to oracle database"""
        try:
            dsn = cx_Oracle.makedsn(host, port, sid)
            self.connection = cx_Oracle.connect(user, password, dsn)
            return self.connection
        except (cx_Oracle.DatabaseError, ConnectionError) as error:
            self.logger.error(error)
            return None

    def get_cursor(self):
        """Get cursor from connection"""
        try:
            cursor = self.connection.cursor()
            return cursor
        except cx_Oracle.DatabaseError as error:
            self.logger.error(error)
            return None

    def close_connection(self):
        """Close connection"""
        try:
            self.connection.close()
        except cx_Oracle.DatabaseError as error:
            self.logger.error(error)

    def query_builder(self, query: str, params: list):
        """Query builder"""
        try:
            cursor = self.get_cursor()
            cursor.execute(query, params)
            return cursor
        except cx_Oracle.DatabaseError as error:
            self.logger.error(error)
            return None
