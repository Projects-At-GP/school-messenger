import datetime
import traceback
import typing
import functools
from time import sleep
from threading import Thread
from .database import DataBase
from .config import Config


__all__ = (
    "error_logger",
    "is_authorized",
    "has_user_agent",
    "generate_id",
    "get_id_type",
    "get_user_type",
    "database",
    "create_log_deleter_runner",
    "create_message_deleter_runner",
)


database = DataBase(Config["database"]["file"], Config["database"]["log level"])


def error_logger(
    *,
    log_level: int = database.LOG_LEVEL["ERROR"],
    retry_on_error: bool = True,
    retry_timeout: typing.Optional[float] = 0,
    raise_on_error: bool = False,
) -> typing.Callable[[typing.Callable], typing.Callable]:
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
    typing.Callable[[typing.Callable], typing.Callable]
    """
    if retry_timeout is None:
        retry_timeout = 0.0
    elif not isinstance(retry_timeout, float):
        retry_timeout = float(retry_timeout)  # type: ignore

    def outer(clb, /):
        """
        Parameters
        ----------
        clb: callable

        Returns
        -------
        callable
        """

        def inner(*args, **kwargs):
            while True:
                try:
                    return clb(*args, **kwargs)
                except Exception as e:
                    database.add_log(
                        level=log_level,
                        version=None,
                        ip=None,
                        msg="".join(
                            traceback.format_exception(None, e, e.__traceback__)
                        ).rstrip("\n"),
                        headers={"retry": retry_on_error, "timeout": retry_timeout},
                    )
                    if raise_on_error:
                        raise
                    if not retry_on_error:
                        return
                    sleep(retry_timeout)

        return functools.update_wrapper(inner, clb)

    return outer


def is_authorized(request, *, authorization_key="Authorization", valid=("User",)):
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
        assert database.account_info(token=token.split()[1]), "Invalid Token!"
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


def get_user_type(request):
    """
    Parameters
    ----------
    request: NAA.APIRequest

    Returns
    -------
    tuple[str, typing.Union[int, str]]
    """
    user_id = request.ip
    user_type = "over ip"  # default value
    token = (request.get("Authorization", default="/").split() + [""])[1]
    if token:
        data = database.account_info(token=token)
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
) -> Thread:
    """
    Creates a thread which automatically deletes old logs.

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
    Thread
    """

    @error_logger()
    def runner():
        sleep(start_after)
        while True:
            database.delete_old_logs(up_to=up_to)
            sleep(interval)

    deleter = Thread(
        target=runner,
        name="<Thread: Automatic Log Deleter>",
        daemon=True,
    )
    deleter.start()
    return deleter


def create_message_deleter_runner(
    *,
    up_to: typing.Union[datetime.datetime, int] = 7,
    start_after: float = 5,
    interval: float = 60 * 60,
) -> Thread:
    """
    Creates a thread which automatically deletes old messages.

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
    Thread
    """

    @error_logger()
    def runner():
        sleep(start_after)
        while True:
            database.delete_old_messages(up_to=up_to)
            sleep(interval)

    deleter = Thread(
        target=runner,
        name="<Thread: Automatic Message Deleter>",
        daemon=True,
    )
    deleter.start()
    return deleter
