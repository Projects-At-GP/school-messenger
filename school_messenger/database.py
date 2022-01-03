import sqlite3  # just for sqlite3.ProgrammingError if the database was already closed
import aiosqlite
import asyncio
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

    async def __aenter__(self):
        self._connection = await aiosqlite.connect(self._database)
        self._cursor = await self._connection.cursor()
        return self

    async def __aexit__(self, *_):
        try:
            # commit
            await self.commit()

            # close
            await self._cursor.close()
            await self._connection.close()

            # delete
            del self._cursor
            del self._connection

        # already triggered?
        except (AttributeError, sqlite3.ProgrammingError):
            pass

    @property
    def database(self):
        return self._database

    async def execute(self, __sql, __parameters=()):
        """
        Shortcut for `aiosqlite.Cursor.execute`

        Parameters
        ----------
        __sql: str
        __parameters: typing.Iterable
        """
        return await self._cursor.execute(__sql, __parameters)

    async def fetchone(self):
        """
        Shortcut for `aiosqlite.Cursor.fetchone`
        """
        return await self._cursor.fetchone()

    async def fetchall(self):
        """
        Shortcut for `aiosqlite.Cursor.fetchall`
        """
        return await self._cursor.fetchall()

    async def fetchmany(self, size):
        """
        Shortcut for `aiosqlite.Cursor.fetchmany`

        Parameters
        ----------
        size: int
        """
        return await self._cursor.fetchmany(size)

    async def commit(self):
        """
        Shortcut for `aiosqlite.Connection.commit`
        """
        await self._connection.commit()

    async def findone(self, table, column=None, query=None):
        """
        Parameters
        ----------
        table, column: str
        query: str, int
        """
        if column is not None and query is not None:
            async with self:
                await self.execute(f"SELECT * FROM {table!r} WHERE {column}=={query!r}")
        else:
            async with self:
                await self.execute(f"SELECT * FROM {table!r}")
        return await self.fetchone()

    async def findall(self, table, column=None, query=None):
        """
        Parameters
        ----------
        table, column: str
        query: str, int
        """
        if column is not None and query is not None:
            async with self:
                await self.execute(f"SELECT * FROM {table!r} WHERE {column}=={query!r}")
        else:
            async with self:
                await self.execute(f"SELECT * FROM {table!r}")
        return await self.fetchall()

    async def findmany(self, size, table, column=None, query=None):
        """
        Parameters
        ----------
        table, column: str
        query: str, int
        size: int
        """
        if column is not None and query is not None:
            await self.execute(f"SELECT * FROM {table!r} WHERE {column}=={query!r}")
        else:
            await self.execute(f"SELECT * FROM {table!r}")
        return await self.fetchmany(size)

    async def add(self, table, values):
        """
        Parameters
        ----------
        table: str
        values: list
        """
        async with self:
            await self.execute(
                f"""
            INSERT INTO {table!r} VALUES ({", ".join(f"{v!r}" for v in values)})
            """
            )


class AccountDB(DatabaseBase):
    __TABLE_ACCOUNTS__ = "accounts"

    async def setup_accounts(self):
        async with self:
            await self.execute(
                f"""
            CREATE TABLE IF NOT EXISTS {self.__TABLE_ACCOUNTS__!r} (
                'id'        BIGINT  UNIQUE  PRIMARY KEY     NOT NULL,
                'name'      TEXT    UNIQUE                  NOT NULL,
                'password'  TEXT    UNIQUE                  NOT NULL,
                'token'     TEXT    UNIQUE                  NOT NULL
            )
            """
            )

    async def add_account(self, name, password):
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

        try:
            assert not name.isnumeric(), "This can be an ID!"
            name = b64encode(name.encode("utf-8", "ignore")).decode("utf-8")
            async with self:
                assert not await self.findone(
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
            async with self:
                await self.add(self.__TABLE_ACCOUNTS__, (id, name, password, token))
            return token

    async def account_token(self, name, password):
        """
        Parameters
        ----------
        name, password: str

        Returns
        -------
        str, optional
        """
        from .utils import set_id_type  # noqa

        try:
            name = b64encode(name.encode("utf-8", "ignore")).decode("utf-8")
            async with self:
                user = await self.findone(self.__TABLE_ACCOUNTS__, "name", name)
            assert user is not None, "Invalid Name!"
            password += str(set_id_type(user[0], 1))
            password = sha512(password.encode("utf-8", "ignore"))
            password = password.hexdigest()
            assert password == user[2], "Invalid Password!"
        except AssertionError:
            return
        else:
            return user[3]

    async def account_delete(
        self,
        token: str = None,
        password: str = None,
        id: typing.Union[str, int] = None,  # noqa
    ) -> bool:
        """
        Parameters
        ----------
        token, password: str, optional
        id: str, int, optional

        Returns
        -------
        bool
            Whether the account could be deleted.
        """
        if token is not None and password is not None and id is None:
            try:
                async with self:
                    user = await self.findone(self.__TABLE_ACCOUNTS__, "token", token)
                password += str(user[0])
                password = sha512(password.encode("utf-8", "ignore"))
                password = password.hexdigest()
                assert password == user[2], "Wrong Password!"
                async with self:
                    await self.execute(
                        f"DELETE FROM {self.__TABLE_ACCOUNTS__!r} "
                        f"WHERE token=={token!r}"
                    )
            except AssertionError:
                return False
            else:
                return True

        elif token is None and password is None and id is not None:
            try:
                assert (
                    user := await self.findone(self.__TABLE_ACCOUNTS__, "id", int(id))
                ), "Invalid id!"
                from .utils import get_id_type

                assert get_id_type(user[0]) != 31, "Is admin!"
                async with self:
                    await self.execute(
                        f"DELETE FROM {self.__TABLE_ACCOUNTS__!r} WHERE id=={id}"
                    )
            except AssertionError:
                return False
            else:
                return True

        else:
            raise ValueError(
                "Invalid combination of following arguments: 'token', 'password', 'id'"
            )

    async def account_info(self, *, query=None, token=None):
        """
        Parameters
        ----------
        query, token: str, optional

        Returns
        -------
        tuple[int, str]
        """
        if query is not None:
            if query.isnumeric():
                data = await self.findone(self.__TABLE_ACCOUNTS__, "id", int(query))
            else:
                query = b64encode(query.encode("utf-8", "ignore")).decode("utf-8")
                data = await self.findone(self.__TABLE_ACCOUNTS__, "name", query)
        else:
            data = await self.findone(self.__TABLE_ACCOUNTS__, "token", token)
        if data is None:
            return ()
        return data[0], b64decode(data[1].encode("utf-8", "ignore")).decode("utf-8")

    async def change_account_type(
        self,
        id: typing.Union[str, int],  # noqa
        type: typing.Union[str, int],  # noqa
    ) -> int:
        """
        Parameters
        ----------
        id, type: str, int

        Returns
        -------
        int
        """
        from .utils import set_id_type

        new_id = set_id_type(int(id), int(type))
        async with self:
            await self.execute(
                f"UPDATE {self.__TABLE_ACCOUNTS__} "
                f"SET id={new_id} "
                f"WHERE id=={id}"
            )
        return new_id


class MessageDB(DatabaseBase):
    __TABLE_MESSAGES__ = "messages"

    async def setup_messages(self):
        async with self:
            await self.execute(
                f"""
            CREATE TABLE IF NOT EXISTS {self.__TABLE_MESSAGES__!r} (
                'id'        BIGINT  UNIQUE  PRIMARY KEY     NOT NULL,
                'author'    BIGINT                          NOT NULL,
                'content'   TEXT                            NOT NULL
            )
            """
            )

    async def add_message(self, author, content):
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

        id = generate_id(2)  # noqa
        content = b64encode(content.encode("utf-8", "ignore")).decode("utf-8")
        await self.add(self.__TABLE_MESSAGES__, (id, author, content))
        return str(id)

    async def delete_message(
        self,
        id: typing.Union[str, int],  # noqa
    ) -> typing.Optional[tuple[int, int, str]]:
        """
        Parameters
        ----------
        id: str, int

        Returns
        -------
        tuple[int, int, str], optional
        """
        if not (msg := await self.findone(self.__TABLE_MESSAGES__, "id", int(id))):
            return
        async with self:
            await self.execute(f"DELETE FROM {self.__TABLE_MESSAGES__} WHERE id=={id}")
        return msg

    async def get_messages(self, maximum=20, before=-1, after=-1):
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

        async with self:
            await self.execute(
                f"SELECT * FROM {self.__TABLE_MESSAGES__!r} "
                f"WHERE {before} > id > {after} ORDER BY id DESC"
            )
            msgs = await self.fetchmany(maximum)
        return [
            (str(msg[0]), msg[1], b64decode(msg[2].encode("utf-8")).decode())
            for msg in msgs
        ]

    async def delete_old_messages(
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

        async with self:
            # fmt: off
            await self.execute(
                f"SELECT null FROM {self.__TABLE_MESSAGES__} "
                f"WHERE id < {up_to}"
            )
            many = len([r for r in await self.fetchall()])
            await self.execute(
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
        await log_db.add_log(
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

    async def setup_logs(self):
        async with self:
            await self.execute(
                f"""
            CREATE TABLE IF NOT EXISTS {self.__TABLE_LOGS__!r} (
                'date'      TEXT    PRIMARY KEY     NOT NULL,
                'level'     INTEGER                 NOT NULL,
                'version'   TEXT                    NOT NULL,
                'ip'        TEXT                    NOT NULL,
                'log'       TEXT                    NOT NULL,
                'headers'   TEXT                    NOT NULL
            )
            """
            )

    async def add_log(self, level, version, ip, msg, headers):
        """
        Parameters
        ----------
        level: int
        version, ip: str, optional
        msg: str
        headers: dict, optional
        """
        if level >= self._log_level:
            now = datetime.utcnow().isoformat(sep=" ")
            ip = ip or "nA"
            version = version or "nA"
            msg = b64encode(msg.encode("utf-8", "ignore")).decode("utf-8")
            headers = b64encode(str(headers or {}).encode("utf-8", "ignore")).decode(
                "utf-8"
            )
            await self.add(self.__TABLE_LOGS__, (now, level, version, ip, msg, headers))
            print(
                f"\033[32m{now}\033[0m\t"
                f"\033[31m{level}\033[0m\t"
                f"\033[36m{version}\033[0m\t"
                f"\033[37m{ip:15}\033[0m\t"
                f"\033[35m{b64decode(msg.encode('utf-8')).decode('utf-8')}\033[0m\t"
                f"\033[30m{b64decode(headers.encode('utf-8')).decode('utf-8')}\033[0m"
            )

    async def get_logs(self, maximum=-1, before=-1, after=-1):
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

        async with self:
            await self.execute(
                f"SELECT * FROM {self.__TABLE_LOGS__!r} "
                f"WHERE {before.isoformat(sep=' ')!r} > date > {after.isoformat(sep=' ')!r} ORDER BY date DESC"
            )
            logs = await self.fetchmany(maximum)
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

    async def delete_old_logs(self, up_to: typing.Union[datetime, int]):
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

        async with self:
            await self.execute(
                f"SELECT null FROM {self.__TABLE_LOGS__} "
                f"WHERE date < {up_to.isoformat(sep=' ')!r}"
            )
            many = len([r for r in await self.fetchall()])
            await self.execute(
                f"DELETE FROM {self.__TABLE_LOGS__} "
                f"WHERE date < {up_to.isoformat(sep=' ')!r}"
            )

        await self.add_log(
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
        asyncio.run(self.setup_database_tables())

    async def setup_database_tables(self):
        await asyncio.gather(
            self.setup_accounts(),
            self.setup_messages(),
            self.setup_logs(),
        )
