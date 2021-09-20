
__all__ = (
    "is_authorized",
    "has_user_agent"
)


def is_authorized(request, *, authorization_key="Authorization"):
    """
    Parameters
    ----------
    request: NAA.APIRequest
    authorization_key: str

    Returns
    -------
    bool
    """
    try:
        assert (token := request.headers.get(authorization_key, "")), "Missing Header."
        assert token  # todo: check if `token` is in database
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
