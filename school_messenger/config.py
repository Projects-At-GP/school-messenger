from AlbertUnruhUtils.config import JSONConfig


__all__ = (
    "Config",
)


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
    }
}

Config = JSONConfig(file="./config.json",
                    default_config=DEFAULT_CONFIG)
