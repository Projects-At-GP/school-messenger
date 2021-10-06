import NAA
from NAA.web import API

from school_messenger.config import Config

from school_messenger.versions import (
    V0,
    V1,
    V2
)


NAA_REQUIRED_MIN_VERSION = "2021.10.06.001"

if NAA.__version__ < NAA_REQUIRED_MIN_VERSION:
    raise RuntimeError("NAA out of date! (require at least version %s instead of %s)"
                       % (NAA_REQUIRED_MIN_VERSION, NAA.__version__))


api = API(host=Config["host"], port=Config["port"], name=Config["name"],
          version_pattern=Config["version"]["pattern"], default=Config["version"]["default"])


api.add_version(version=0)(V0)  # test-version without database
api.add_version(version=1)(V1)
api.add_version(version=2, fallback=V1)(V2)


api(debug=Config["server"]["debug"], reload=Config["server"]["reload"])
