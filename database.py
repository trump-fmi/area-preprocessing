import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from psycopg2 import pool


class DatabaseConnection:
    def __init__(self, host, database, user, password=None):
        self.connection_pool = psycopg2.pool.SimpleConnectionPool(1, 20, user=user,
                                                                  password=password,
                                                                  host=host,
                                                                  database=database)

    def open_cursor(self):
        connection = self.connection_pool.getconn()
        connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        return connection.cursor()

    def close_cursor(self, cursor):
        connection = cursor.connection
        cursor.close()
        self.connection_pool.putconn(connection)

    def query(self, query):
        try:
            cursor = self.open_cursor()
            cursor.execute(query)
        except:
            print(f"Failed query: {query}")
            exit(-1)
        finally:
            self.close_cursor(cursor)

    def queryForResult(self, query):
        cursor = self.open_cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        self.close_cursor(cursor)
        return result

    def disconnect(self):
        if self.connection_pool:
            self.connection_pool.closeall()
