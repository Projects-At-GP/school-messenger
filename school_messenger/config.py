from AlbertUnruhUtils.config.jsonconfig import JSONConfig
from redis import Redis


__all__ = (
    "Config",
    "redis",
)


# fmt: off
DEFAULT_CONFIG = {
    "host": "127.0.0.1",
    "port": 3333,

    # I don't know why I have this, I know I have it, but I think I had it on my To-Do-List...
    "name": "School Messenger",

    "database": {
        "file": "database.sqlite",
        "log level": 0
    },

    "version": {
        "pattern": "v{version}",
        "default": 0
    },

    "server": {
        "debug": False,
        "reload": False
    },

    # the settings for redis
    "redis": {
        "host": "127.0.0.1",
        "port": 6379,
        "db": 1,
        "password": None
    },

    # the settings for the ratelimiting
    "ratelimits":  {
        "admin": {
            "amount": 60,
            "interval": 30,
            "timeout": 0
        },
        "user": {
            "amount": 60,
            "interval": 60,
            "timeout": 10
        },
        "over ip": {
            "amount": 10,
            "interval": 60,
            "timeout": 30
        },
    },

    "statuspage.io": {
        # must be set
        "api key": "YOUR-API-KEY",
        "page id": "YOUR-PAGE-ID",
        "latency metric id": "YOUR-METRIC-ID",
        # can be set (but isn't recommended)
        "api base": "api.statuspage.io",
        "api version": "/v1/",  # "/" is optional
    },

    # automated background tasks
    "runner": {
        "latency updater": {
            "start_after": 10,
            "interval": 60 * 5,  # 5 minutes
            "target": f"http://127.0.0.1:{3333}",  # default port from this config
            "method": "GET",
        },
        "log deleter": {
            "start_after": 5,
            "interval": 60 * 60,  # 60 minutes / 1 hour
            "up_to": 7,  # 7 days / 1 week
        },
    },
}
# fmt: on


Config = JSONConfig(
    file="./config.json",
    default_config=DEFAULT_CONFIG,
)

redis = Redis(
    host=Config["redis"]["host"],
    port=Config["redis"]["port"],
    db=Config["redis"]["db"],
    password=Config["redis"]["password"],
)
