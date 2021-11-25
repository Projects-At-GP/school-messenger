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
        }
    }
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
