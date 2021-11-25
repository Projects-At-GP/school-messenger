import datetime
from .database import DataBase
from .config import Config


__all__ = (
    "is_authorized",
    "has_user_agent",
    "generate_id",
    "get_user_type",
    "database",
)


database = DataBase(Config["database"]["file"], Config["database"]["log level"])


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
