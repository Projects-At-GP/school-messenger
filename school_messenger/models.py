import datetime


__all__ = (
    "generate_id",
)


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
