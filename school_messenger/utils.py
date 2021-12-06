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
    "get_user_type",
    "database",
    "create_log_deleter_runner",
)


database = DataBase(Config["database"]["file"], Config["database"]["log level"])


def error_logger(
    *,
    log_level: int = database.LOG_LEVEL["ERROR"],
    restart_if_fails: bool = True,
    restart_timeout: typing.Optional[float] = 0,
) -> typing.Callable[[typing.Callable], typing.Callable]:
    """
    Logs errors and restarts the task if needed.

    Parameters
    ----------
    log_level: int
        The level the errors should be logged with.
    restart_if_fails: bool
        Whether the task should be restarted if it fails.
    restart_timeout: float, optional
        The pause until the task 'll be rerun (in s).

    Returns
    -------
    typing.Callable[[typing.Callable], typing.Callable]
    """
    if restart_timeout is None:
        restart_timeout = 0.0
    elif not isinstance(restart_timeout, float):
        restart_timeout = float(restart_timeout)  # type: ignore

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
                        headers={"retry": restart_if_fails, "timeout": restart_timeout},
                    )
                    if not restart_if_fails:
                        return
                    sleep(restart_timeout)

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
    return (int(unix * 1000 - 1609455600000) << 15) + (type << 11) + increment


def get_user_type(request):
    """
    Parameters
    ----------
    request: NAA.APIRequest

    Returns
    -------
    tuple[str, typing.Union[int, str]]
    """
    user_type = "admin"  # static at the moment...  # FixMe: FOR PRODUCTION THIS MUST BE "user" OR DYNAMIC!!!
    user_id = 0
    token = (request.get("Authorization", default="/").split() + [""])[1]
    if token:
        data = database.account_info(token=token)
        if data:
            user_id = data[0]

    if not user_id:
        user_id = request.ip

    return user_type, user_id


def create_log_deleter_runner(
    *,
    up_to: typing.Union[datetime.datetime, int] = 24 * 7,
    start_after: float = 5,
    interval: float = 60 * 60,
) -> Thread:
    """
    Creates a thread which automatically updates the latency displayed on statuspage.io.

    Parameters
    ----------
    up_to: datetime.datetime, int
    start_after: float
        The pause before deleting first time (in s).
    interval: float
        The delete interval (in s).

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

    deleter = Thread(target=runner, name="<Thread: Automatic Log Deleter>", daemon=True)
    deleter.start()
    return deleter
