import sqlite3
import typing
from hashlib import sha512
from secrets import token_bytes
from base64 import b64encode, b64decode
from datetime import datetime, timedelta


__all__ = ("DataBase",)


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

    def findone(self, table, column=None, query=None):
        """
        Parameters
        ----------
        table, column: str
        query: str, int
        """
        with self as db:
            if column is not None and query is not None:
                db.execute(f"SELECT * FROM {table!r} WHERE {column}=={query!r}")
            else:
                db.execute(f"SELECT * FROM {table!r}")
            return db.fetchone()

    def findall(self, table, column=None, query=None):
        """
        Parameters
        ----------
        table, column: str
        query: str, int
        """
        with self as db:
            if column is not None and query is not None:
                db.execute(f"SELECT * FROM {table!r} WHERE {column}=={query!r}")
            else:
                db.execute(f"SELECT * FROM {table!r}")
            return db.fetchall()

    def findmany(self, size, table, column=None, query=None):
        """
        Parameters
        ----------
        table, column: str
        query: str, int
        size: int
        """
        with self as db:
            if column is not None and query is not None:
                db.execute(f"SELECT * FROM {table!r} WHERE {column}=={query!r}")
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
            db.execute(
                f"""
            INSERT INTO {table!r} VALUES ({", ".join(f"{v!r}" for v in values)})
            """
            )


class AccountDB(DatabaseBase):
    __TABLE_ACCOUNTS__ = "accounts"

    def setup_accounts(self):
        with self as db:
            db.execute(
                f"""
            CREATE TABLE IF NOT EXISTS {self.__TABLE_ACCOUNTS__!r} (
                'id'        BIGINT  UNIQUE  PRIMARY KEY,
                'name'      TEXT    UNIQUE,
                'password'  TEXT    UNIQUE,
                'token'     TEXT    UNIQUE
            )
            """
            )

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
        from .utils import generate_id  # noqa

        with self as db:
            try:
                assert not name.isnumeric(), "This can be an ID!"
                name = b64encode(name.encode("utf-8", "ignore")).decode("utf-8")
                assert not db.findone(
                    self.__TABLE_ACCOUNTS__, "name", name
                ), "User already registered!"
                id = generate_id(1)  # noqa
                password += str(id)
                password = sha512(password.encode("utf-8", "ignore"))
                password = password.hexdigest()
            except (AssertionError, ValueError):
                return False
            else:
                token = (
                    b64encode(str(id).encode()).decode(),
                    b64encode(token_bytes()).decode(),
                )
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
                name = b64encode(name.encode("utf-8", "ignore")).decode("utf-8")
                user = db.findone(self.__TABLE_ACCOUNTS__, "name", name)
                assert user is not None, "Invalid Name!"
                password += str(user[0])
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
                password += str(user[0])
                password = sha512(password.encode("utf-8", "ignore"))
                password = password.hexdigest()
                assert password == user[2], "Wrong Password!"
                db.execute(
                    f"DELETE FROM {self.__TABLE_ACCOUNTS__!r} "
                    f"WHERE token=={token!r}"
                )
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
                    query = b64encode(query.encode("utf-8", "ignore")).decode("utf-8")
                    data = db.findone(self.__TABLE_ACCOUNTS__, "name", query)
            else:
                data = db.findone(self.__TABLE_ACCOUNTS__, "token", token)
            if data is None:
                return ()
            return data[0], b64decode(data[1].encode("utf-8", "ignore")).decode("utf-8")


class MessageDB(DatabaseBase):
    __TABLE_MESSAGES__ = "messages"

    def setup_messages(self):
        with self as db:
            db.execute(
                f"""
            CREATE TABLE IF NOT EXISTS {self.__TABLE_MESSAGES__!r} (
                'id'        BIGINT  UNIQUE  PRIMARY KEY,
                'author'    BIGINT,
                'content'   TEXT
            )
            """
            )

    def add_message(self, author, content):
        """
        Parameters
        ----------
        author: int
        content: str

        Returns
        -------
        str
        """
        from .utils import generate_id  # noqa

        with self as db:
            id = generate_id(2)  # noqa
            content = b64encode(content.encode("utf-8", "ignore")).decode("utf-8")
            db.add(self.__TABLE_MESSAGES__, (id, author, content))
            return str(id)

    def get_messages(self, maximum=20, before=-1, after=-1):
        """
        Parameters
        ----------
        maximum, before, after: int

        Returns
        -------
        list[tuple[str, int, str]]
        """
        if before == -1:
            # 18446744073709551615 -> 1111111111111111111111111111111111111111111111111111111111111111
            before = 18446744073709551615
        else:
            before = ((before - 1609455600000) << 16) + 65535
        if after == -1:
            # 0 -> 0000000000000000000000000000000000000000000000000000000000000000
            after = 0
        else:
            after = (after - 1609455600000) << 16

        with self as db:
            db.execute(
                f"SELECT * FROM {self.__TABLE_MESSAGES__!r} "
                f"WHERE {before} > id > {after} ORDER BY id DESC"
            )
            msgs = db.fetchmany(maximum)
            return [
                (str(msg[0]), msg[1], b64decode(msg[2].encode("utf-8")).decode())
                for msg in msgs
            ]

    def delete_old_messages(
        self,
        up_to: typing.Union[datetime, int],
        *,
        already_id: bool = False,
    ) -> int:
        """
        Deletes old messages.

        Parameters
        ----------
        up_to: datetime, int  # in days if int and not already_id
            Is datetime is given all messages until the date 'll be deleted.
            Otherwise, the messages older than n days 'll be deleted.
            The above-mentioned behavior is only active if already_id is *not*
            False (already_id=True), otherwise up_to is treated as a final id.
        already_id: bool
            Whether `up_to` should *not* be converted to an id.

        Returns
        -------
        int
            The amount of deleted messages.
        """
        if not already_id:
            if isinstance(up_to, int):
                up_to = datetime.now() - timedelta(days=up_to)
            if isinstance(up_to, datetime):
                up_to = up_to.timestamp() * 1000
            up_to = int(up_to - 1609455600000) << 16

        with self as db:
            # fmt: off
            db.execute(
                f"SELECT null FROM {self.__TABLE_MESSAGES__} "
                f"WHERE id < {up_to}"
            )
            many = len(db.fetchall())
            db.execute(
                f"DELETE FROM {self.__TABLE_MESSAGES__} "
                f"WHERE id < {up_to}"
            )
            # fmt: on

        # if we run this class directly and not from :class:`DataBase`
        if not isinstance(self, LogDB):
            log_db = LogDB(self.database)
        else:
            log_db = self

        date = datetime.fromtimestamp(((up_to >> 16) + 1609455600000) / 1000).isoformat(
            sep=" "
        )
        log_db.add_log(
            level=log_db.LOG_LEVEL["INFO"],
            version=None,
            ip=None,
            msg=f"{many} messages deleted from database",
            headers={"reason": f"older than {date}"},
        )

        return many


class LogDB(DatabaseBase):
    __TABLE_LOGS__ = "logs"
    LOG_LEVEL = {
        "UNSET": 0,
        "DEBUG": 1,
        "INFO": 2,
        "ERROR": 3,
        "WARNING": 4,
        "CRITICAL": 5,
    }

    def __init__(self, database, log_level=LOG_LEVEL["UNSET"]):
        super().__init__(database)
        self._log_level = log_level

    def setup_logs(self):
        with self as db:
            db.execute(
                f"""
            CREATE TABLE IF NOT EXISTS {self.__TABLE_LOGS__!r} (
                'date'      TEXT    PRIMARY KEY,
                'level'     INTEGER,
                'version'   TEXT,
                'ip'        TEXT,
                'log'       TEXT,
                'headers'   TEXT
            )
            """
            )

    def add_log(self, level, version, ip, msg, headers):
        """
        Parameters
        ----------
        level: int
        version, ip: str, optional
        msg: str
        headers: dict, optional
        """
        if level >= self._log_level:
            with self as db:
                now = datetime.utcnow().isoformat(sep=" ")
                ip = ip or "nA"
                version = version or "nA"
                msg = b64encode(msg.encode("utf-8", "ignore")).decode("utf-8")
                headers = b64encode(
                    str(headers or {}).encode("utf-8", "ignore")
                ).decode("utf-8")
                db.add(self.__TABLE_LOGS__, (now, level, version, ip, msg, headers))
                print(
                    f"\033[32m{now}\033[0m\t"
                    f"\033[31m{level}\033[0m\t"
                    f"\033[36m{version}\033[0m\t"
                    f"\033[37m{ip:15}\033[0m\t"
                    f"\033[35m{b64decode(msg.encode('utf-8')).decode('utf-8')}\033[0m\t"
                    f"\033[30m{b64decode(headers.encode('utf-8')).decode('utf-8')}\033[0m"
                )

    def get_logs(self, maximum=-1, before=-1, after=-1):
        """
        Parameters
        ----------
        maximum, before, after: int

        Returns
        -------
        list[tuple[str, str, str, str, str, str]]
        """
        if before == -1:
            before = datetime(9999, 12, 31, 23, 59, 59, 59)
        else:
            before = datetime.fromtimestamp(before / 1000)
        if after == -1:
            after = datetime(1, 1, 1)
        else:
            after = datetime.fromtimestamp(after / 1000)

        with self as db:
            db.execute(
                f"SELECT * FROM {self.__TABLE_LOGS__!r} "
                f"WHERE {before.isoformat(sep=' ')!r} > date > {after.isoformat(sep=' ')!r} ORDER BY date DESC"
            )
            logs = db.fetchmany(maximum)
            return [
                (
                    log[0],
                    str(log[1]),
                    log[2],
                    log[3],
                    b64decode(log[4].encode("utf-8")).decode(),
                    b64decode(log[5].encode("utf-8")).decode(),
                )
                for log in logs
            ]

    def delete_old_logs(self, up_to: typing.Union[datetime, int]):
        """
        Deletes old logs.

        Parameters
        ----------
        up_to: datetime, int  # in days if int
            Is datetime is given all logs until the date 'll be deleted.
            Otherwise, the logs older than n days 'll be deleted.

        Returns
        -------
        int
            The amount of deleted logs.
        """
        if isinstance(up_to, (int, float)):
            up_to = datetime.utcnow() - timedelta(days=up_to)

        with self as db:
            db.execute(
                f"SELECT null FROM {self.__TABLE_LOGS__} "
                f"WHERE date < {up_to.isoformat(sep=' ')!r}"
            )
            many = len(db.fetchall())
            db.execute(
                f"DELETE FROM {self.__TABLE_LOGS__} "
                f"WHERE date < {up_to.isoformat(sep=' ')!r}"
            )

        self.add_log(
            level=self.LOG_LEVEL["INFO"],
            version=None,
            ip=None,
            msg=f"{many} logs deleted from log",
            headers={"reason": f"older than {up_to.isoformat(sep=' ')}"},
        )

        return many


class DataBase(AccountDB, MessageDB, LogDB):
    """
    A morph of all DataBase models (AccountDB, MessageDB, LogDB).
    """

    def __init__(self, database, log_level=0):
        super().__init__(database=database, log_level=log_level)
        self.setup_accounts()
        self.setup_messages()
        self.setup_logs()
