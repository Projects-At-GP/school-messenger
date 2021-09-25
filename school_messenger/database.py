import sqlite3
from hashlib import sha512
from secrets import token_bytes
from base64 import b64encode, b64decode
from datetime import datetime

from .utils import generate_id


__all__ = (
    "DataBase",
)


class DatabaseBase:
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
        try:
            # commit
            self.commit()

            # close
            self._cursor.close()
            self._connection.close()

            # delete
            del self._cursor
            del self._connection

        # already triggered?
        except AttributeError:
            pass

    @property
    def database(self):
        return self._database

    def execute(self, __sql, __parameters=()):
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

    def findone(self, table, collum=None, query=None):
        """
        Parameters
        ----------
        table, collum: str
        query: str, int
        """
        with self as db:
            if collum is not None and query is not None:
                db.execute(f"SELECT * FROM {table!r} WHERE {collum}=={query!r}")
            else:
                db.execute(f"SELECT * FROM {table!r}")
            return db.fetchone()

    def findall(self, table, collum=None, query=None):
        """
        Parameters
        ----------
        table, collum: str
        query: str, int
        """
        with self as db:
            if collum is not None and query is not None:
                db.execute(f"SELECT * FROM {table!r} WHERE {collum}=={query!r}")
            else:
                db.execute(f"SELECT * FROM {table!r}")
            return db.fetchall()

    def findmany(self, size, table, collum=None, query=None):
        """
        Parameters
        ----------
        table, collum: str
        query: str, int
        size: int
        """
        with self as db:
            if collum is not None and query is not None:
                db.execute(f"SELECT * FROM {table!r} WHERE {collum}=={query!r}")
            else:
                db.execute(f"SELECT * FROM {table!r}")
            return db.fetchmany(size)

    def add(self, table, values):
        """
        Parameters
        ----------
        table: str
        values: list
        """
        with self as db:
            db.execute(f"""
            INSERT INTO {table!r} VALUES ({", ".join(f"{v!r}" for v in values)})
            """)


class AccountDB(DatabaseBase):
    __TABLE_ACCOUNTS__ = "accounts"

    def setup_accounts(self):
        with self as db:
            db.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.__TABLE_ACCOUNTS__!r} (
                'id'        BIGINT  UNIQUE  PRIMARY KEY,
                'name'      TEXT    UNIQUE,
                'password'  TEXT    UNIQUE,
                'token'     TEXT    UNIQUE
            )
            """)

    def add_account(self, name, password):
        """
        Parameters
        ----------
        name: str
        password: str

        Returns
        -------
        Literal[False, str]
        """
        with self as db:
            try:
                assert not name.isnumeric(), "This can be an ID!"
                assert not db.findone(self.__TABLE_ACCOUNTS__, "name", name), "User already registered!"
                id = generate_id(1)  # noqa
                password = password + str(id)
                password = sha512(password.encode("utf-8", "ignore"))
                password = password.hexdigest()
            except (AssertionError, ValueError):
                return False
            else:
                token = (b64encode(str(id).encode()).decode(), b64encode(token_bytes()).decode())
                token = token[0].rstrip("=") + "." + token[1].rstrip("=")
                token = token.replace("+", "-").replace("/", "_")
                db.add(self.__TABLE_ACCOUNTS__, (id, name, password, token))
                return token

    def account_token(self, name, password):
        """
        Parameters
        ----------
        name, password: str

        Returns
        -------
        str
        """
        with self as db:
            try:
                user = db.findone(self.__TABLE_ACCOUNTS__, "name", name)
                assert user is not None, "Invalid Name!"
                password = password + str(user[0])
                password = sha512(password.encode("utf-8", "ignore"))
                password = password.hexdigest()
                assert password == user[2], "Invalid Password!"
            except AssertionError:
                return
            else:
                return user[3]

    def account_delete(self, token, password):
        """
        Parameters
        ----------
        token, password: str

        Returns
        -------
        bool
            Whether the account could be deleted.
        """
        with self as db:
            try:
                user = db.findone(self.__TABLE_ACCOUNTS__, "token", token)
                password = password + str(user[0])
                password = sha512(password.encode("utf-8", "ignore"))
                password = password.hexdigest()
                assert password == user[2], "Wrong Password!"
                db.execute(f"DELETE FROM {self.__TABLE_ACCOUNTS__!r} "
                           f"WHERE token=={token!r}")
            except AssertionError:
                return False
            else:
                return True

    def account_info(self, *, query=None, token=None):
        """
        Parameters
        ----------
        query, token: str, optional

        Returns
        -------
        tuple[int, str]
        """
        with self as db:
            if query is not None:
                if query.isnumeric():
                    data = db.findone(self.__TABLE_ACCOUNTS__, "id", int(query))
                else:
                    data = db.findone(self.__TABLE_ACCOUNTS__, "name", query)
            else:
                data = db.findone(self.__TABLE_ACCOUNTS__, "token", token)
            if data is None:
                return ()
            return data[0], data[1]


class MessageDB(DatabaseBase):
    __TABLE_MESSAGES__ = "messages"

    def setup_messages(self):
        with self as db:
            db.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.__TABLE_MESSAGES__!r} (
                'id'        BIGINT  UNIQUE  PRIMARY KEY,
                'author'    BIGINT,
                'content'   TEXT
            )
            """)

    def add_message(self, author, content):
        """
        Parameters
        ----------
        author: int
        content: str
        """
        with self as db:
            id = generate_id(2)  # noqa
            content = b64encode(content.encode("utf-8", "ignore")).decode("utf-8")
            db.add(self.__TABLE_MESSAGES__, (id, author, content))
            return id

    def get_messages(self, maximum=20, before=-1, after=-1):
        """
        Parameters
        ----------
        maximum: int
        before, after: int

        Returns
        -------
        list[tuple[int, int, str]]
        """
        if before == -1:
            # 18446744073709551615 -> 1111111111111111111111111111111111111111111111111111111111111111
            before = 18446744073709551615
        else:
            before = ((before - 1609455600000) << 15) + 65535
        if after == -1:
            # 0 -> 0000000000000000000000000000000000000000000000000000000000000000
            after = 0
        else:
            after = (after - 1609455600000) << 15

        with self as db:
            db.execute(f"SELECT * FROM {self.__TABLE_MESSAGES__!r} "
                       f"WHERE {before} > id > {after} ORDER BY id DESC")
            msgs = db.fetchmany(maximum)
            return [(msg[0], msg[1], b64decode(msg[2].encode("utf-8")).decode()) for msg in msgs]


class LogDB(DatabaseBase):
    __TABLE_LOGS__ = "logs"
    LOG_LEVEL = {
        "UNSET": 0,
        "DEBUG": 1,
        "INFO": 2,
        "ERROR": 3,
        "WARNING": 4,
        "CRITICAL": 5
    }

    def __init__(self, database, log_level=LOG_LEVEL["UNSET"]):
        super().__init__(database)
        self._log_level = log_level

    def setup_logs(self):
        with self as db:
            db.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.__TABLE_LOGS__!r} (
                'date'      TEXT    PRIMARY KEY,
                'level'     INTEGER,
                'ip'        TEXT,
                'log'       TEXT
            )
            """)

    def add_log(self, level, ip, msg):
        """
        Parameters
        ----------
        level: int, str
        ip, msg: str
        """
        if level >= self._log_level:
            with self as db:
                now = datetime.utcnow().isoformat(sep=" ")
                ip = ip or "nA"
                db.add(self.__TABLE_LOGS__, (now, level, ip, msg))
                print(f"\033[32m{now}\t"
                      f"\033[31m{level}\t"
                      f"\033[37m{ip:15}\t"
                      f"\033[35m{msg}")


class DataBase(AccountDB, MessageDB, LogDB):
    """
    A morph of all DataBase models (AccountDB, MessageDB, LogDB).
    """

    def __init__(self, database, log_level=0):
        super().__init__(database=database, log_level=log_level)
        self.setup_accounts()
        self.setup_messages()
        self.setup_logs()
