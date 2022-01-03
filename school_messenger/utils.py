import asyncio
import datetime
import traceback
import typing
import functools
from .database import DataBase
from .config import Config


__all__ = (
    "get_error",
    "error_logger",
    "is_authorized",
    "has_user_agent",
    "generate_id",
    "get_id_type",
    "set_id_type",
    "get_user_type",
    "database",
    "create_log_deleter_runner",
    "create_message_deleter_runner",
)


database = DataBase(Config["database"]["file"], Config["database"]["log level"])


def get_error(
    error: Exception,
) -> str:
    """
    Returns the Error/Exception-Feedback which normally appears in STDOUT.

    Parameters
    ----------
    error: Exception
        The Error/Exception which was raised.

    Returns
    -------
    str
    """
    output = "".join(traceback.format_exception(None, error, error.__traceback__))
    return output.rstrip("\n")


_C = typing.TypeVar("_C", bound=typing.Callable[[...], typing.Coroutine])


def error_logger(
    *,
    log_level: int = database.LOG_LEVEL["ERROR"],
    retry_on_error: bool = True,
    retry_timeout: typing.Optional[float] = 0,
    raise_on_error: bool = False,
) -> typing.Callable[[_C], _C]:
    """
    Logs errors and restarts the task if needed.

    Parameters
    ----------
    log_level: int
        The level the errors should be logged with.
    retry_on_error: bool
        Whether the task should be restarted if it fails.
    retry_timeout: float, optional
        The pause until the task 'll be rerun (in s).
    raise_on_error: bool
        Whether the error should be raised after it's logged.

    Returns
    -------
    typing.Callable[[_C], _C]
    """
    if retry_timeout is None:
        retry_timeout = 0.0
    elif not isinstance(retry_timeout, float):
        retry_timeout = float(retry_timeout)  # type: ignore

    def outer(clb: _C, /) -> _C:
        """
        Parameters
        ----------
        clb: _C

        Returns
        -------
        _C
        """

        async def inner(*args, **kwargs):
            while True:
                try:
                    return await clb(*args, **kwargs)
                except Exception as e:
                    await database.add_log(
                        level=log_level,
                        version=None,
                        ip=None,
                        msg=get_error(e),
                        headers={"retry": retry_on_error, "timeout": retry_timeout},
                    )
                    if raise_on_error:
                        raise
                    if not retry_on_error:
                        return
                    await asyncio.sleep(retry_timeout)

        return functools.update_wrapper(inner, clb)

    return outer


async def is_authorized(request, *, authorization_key="Authorization", valid=("User",)):
    """
    Parameters
    ----------
    request: NAA.APIRequest
    authorization_key: str
    valid: list[str]

    Returns
    -------
    bool
    """
    try:
        assert (token := request.headers.get(authorization_key, "")), "Missing Header!"
        assert token.startswith(valid), "Missing Clarification!"
        assert len(token.split()) == 2, "Missing Token! (Just 'User' etc. ...)"
        assert await database.account_info(token=token.split()[1]), "Invalid Token!"
        return True
    except AssertionError:
        return False


def has_user_agent(request, *, user_agent_key="User-Agent", min_user_agent_len=2):
    """
    Parameters
    ----------
    request: NAA.APIRequest
    user_agent_key: str
    min_user_agent_len: int

    Returns
    -------
    bool
    """
    try:
        assert (agent := request.headers.get(user_agent_key, "")), "Missing Header."
        assert len(agent.split()) >= min_user_agent_len, "User Agent To Short."
        return True
    except AssertionError:
        return False


__INCREMENT = -1


def generate_id(type=0):  # noqa
    """
    Parameters
    ----------
    type: int

    Returns
    -------
    int
    """
    global __INCREMENT
    if __INCREMENT == 2047:
        __INCREMENT = 0
    else:
        __INCREMENT += 1
    increment = __INCREMENT
    now = datetime.datetime.utcnow()
    unix = (now - datetime.datetime(1970, 1, 1)).total_seconds()
    return (int(unix * 1000 - 1609455600000) << 16) + (type << 11) + increment


def get_id_type(
    id: int,  # noqa
) -> int:
    """
    Parameters
    ----------
    id: int

    Returns
    -------
    int
    """
    return (id & 65535) >> 11  # retrieves the type (WHITEPAPER.md)


def set_id_type(
    id: int,  # noqa
    type: int,  # noqa
) -> int:
    """
    Replaces the type-part in an ID with the given ``type``.

    Parameters
    ----------
    id, type: int

    Returns
    -------
    int
    """
    return ((id >> 16) << 16) + (type << 11) + (id & 2047)


async def get_user_type(request):
    """
    Parameters
    ----------
    request: NAA.APIRequest

    Returns
    -------
    tuple[str, typing.Union[int, str]]
    """
    user_id = request.ip
    user_type = "over_ip"  # default value
    token = (request.get("Authorization", default="/").split() + [""])[1]
    if token:
        data = await database.account_info(token=token)
        if data:
            user_id = data[0]
            raw_user_type = get_id_type(user_id)
            if raw_user_type:
                if raw_user_type == 1:
                    user_type = "user"
                elif raw_user_type == 31:
                    user_type = "admin"

    return user_type, user_id


def create_log_deleter_runner(
    *,
    up_to: typing.Union[datetime.datetime, int] = 7,
    start_after: float = 5,
    interval: float = 60 * 60,
) -> typing.Coroutine:
    """
    Creates a Coroutine which automatically deletes old logs.

    Parameters
    ----------
    up_to: datetime.datetime, int
        The max age a log is allowed to have.
        If integer is given: N in days.
    start_after: float
        The pause before deleting first time (in s).
    interval: float
        The delete-interval (in s).

    Returns
    -------
    typing.Coroutine
    """

    @error_logger()
    async def runner():
        await asyncio.sleep(start_after)
        while True:
            await database.delete_old_logs(up_to=up_to)
            await asyncio.sleep(interval)

    return runner()


def create_message_deleter_runner(
    *,
    up_to: typing.Union[datetime.datetime, int] = 7,
    start_after: float = 5,
    interval: float = 60 * 60,
) -> typing.Coroutine:
    """
    Creates a Coroutine which automatically deletes old messages.

    Parameters
    ----------
    up_to: datetime.datetime, int
        The max age a message is allowed to have.
        If integer is given: N in days.
    start_after: float
        The pause before deleting first time (in s).
    interval: float
        The delete-interval (in s).

    Returns
    -------
    typing.Coroutine
    """

    @error_logger()
    async def runner():
        await asyncio.sleep(start_after)
        while True:
            await database.delete_old_messages(up_to=up_to)
            await asyncio.sleep(interval)

    return runner()
