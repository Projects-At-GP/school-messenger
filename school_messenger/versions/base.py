from ..database import DataBase
from ..config import Config


class VersionBase:
    database = DataBase(
        Config["database"]["file"],
        Config["database"]["log level"]
    )
