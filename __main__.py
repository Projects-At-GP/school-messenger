import asyncio
from json import load

import NAA
from NAA.models import APIResponse
from NAA.web import API

import AlbertUnruhUtils
from AlbertUnruhUtils.ratelimit import ServerRateLimit


from school_messenger.config import Config, redis
from school_messenger.statuspage import create_latency_update_runner
from school_messenger.utils import (
    create_log_deleter_runner,
    create_message_deleter_runner,
    error_logger,
    get_user_type,
)

from school_messenger.versions import (
    V0,
    V1,
    V2,
    V3,
)


NAA_REQUIRED_MIN_VERSION = "2021.12.16.001"
AlbertUnruhUtils_REQUIRED_MIN_VERSION = "2021.11.13.000"


@error_logger(log_level=5, raise_on_error=True)
async def check_lib_versions():
    if NAA.__version__ < NAA_REQUIRED_MIN_VERSION:
        raise RuntimeError(
            "NAA out of date! (require at least version %s instead of %s)"
            % (NAA_REQUIRED_MIN_VERSION, NAA.__version__)
        )

    if AlbertUnruhUtils.__version__ < AlbertUnruhUtils_REQUIRED_MIN_VERSION:
        raise RuntimeError(
            "AlbertUnruhUtils out of date! (require at least version %s instead of %s)"
            % (AlbertUnruhUtils_REQUIRED_MIN_VERSION, AlbertUnruhUtils.__version__)
        )


asyncio.run(check_lib_versions())  # in a call because so errors can be logged


api = API(
    host=Config["host"],
    port=Config["port"],
    name=Config["name"],
    version_pattern=Config["version"]["pattern"],
    default=Config["version"]["default"],
    used_libs=["AlbertUnruhUtils"],
)

api.add_version(version=0)(V0)  # test-version without database
api.add_version(version=1)(V1)
api.add_version(version=2, fallback=[V1])(V2)
api.add_version(version=3, fallback=[V1, V2])(V3)

# add default endpoint
with open("main-response.json") as f:
    default_response = load(f)


@api.default_endpoint
@ServerRateLimit(Config["ratelimits"], get_user_type, redis=redis)
def _(*_):
    return APIResponse(default_response)


run = error_logger(log_level=5, retry_timeout=60)(api.run_api)


async def run_main_processes():
    # create background tasks
    await asyncio.gather(
        create_latency_update_runner(**Config["runner"]["latency updater"]),
        create_log_deleter_runner(**Config["runner"]["log deleter"]),
        create_message_deleter_runner(**Config["runner"]["message deleter"]),
    )

    # run server
    run(**Config["server"])


asyncio.run(run_main_processes())
