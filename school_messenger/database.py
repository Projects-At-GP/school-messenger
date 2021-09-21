import sqlite3


__all__ = (
    "DataBase",
)


class DataBase:
    def __init__(self, database):
        """
        Parameters
        ----------
        database: str
        """
        self._database = database

    def __enter__(self):
        self._connection = sqlite3.connect(self._database)
        self._cursor = self._connection.cursor()
        return self

    def __exit__(self, *_):
        # commit
        self.commit()

        # close
        self._cursor.close()
        self._connection.close()

        # delete
        del self._cursor
        del self._connection

    def execute(self, __sql, __parameters):
        """
        Shortcut for `sqlite3.Cursor.execute`

        Parameters
        ----------
        __sql: str
        __parameters: typing.Iterable
        """
        return self._cursor.execute(__sql, __parameters)

    def fetchone(self):
        """
        Shortcut for `sqlite3.Cursor.fetchone`
        """
        return self._cursor.fetchone()

    def fetchall(self):
        """
        Shortcut for `sqlite3.Cursor.fetchall`
        """
        return self._cursor.fetchall()

    def fetchmany(self, size):
        """
        Shortcut for `sqlite3.Cursor.fetchmany`

        Parameters
        ----------
        size: int
        """
        return self._cursor.fetchmany(size)

    def commit(self):
        """
        Shortcut for `sqlite3.Connection.commit`
        """
        self._connection.commit()
