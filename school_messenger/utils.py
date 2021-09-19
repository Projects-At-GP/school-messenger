
__all__ = (
    "is_authorized",
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
