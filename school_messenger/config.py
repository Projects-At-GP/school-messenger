from json import load, dump


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


class Config:
    def __init__(self, *, file, default=None):
        """
        Parameters
        ----------
        file: str
        default: Any
        """
        try:
            with open(file) as f:
                self._config = load(f)
        except OSError:
            self._config = DEFAULT_CONFIG.copy()
            with open(file, "w") as f:
                dump(self._config, f, indent=4)

        self.default = default
        self._file = file

    @property
    def file(self):
        return self._file

    @file.setter
    def file(self, value):
        self.__init__(file=value, default=self.default)

    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, value):
        assert isinstance(value, dict), \
            f"{self.__class__.__name__}.config must be an instance of 'dict', not {value.__class__.__name__!r}!"
        self._config = value
        with open(self._file, "w") as f:
            dump(self._config, f, indent=4)

    def __getitem__(self, item):
        return self._config.get(item, self.default)

    def __setitem__(self, key, value):
        self._config[key] = value
        with open(self._file, "w") as f:
            dump(self._config, f, indent=4)


Config = Config(file="./config.json")
