from threading import Thread
from time import time, sleep, perf_counter
from requests import request
from .config import Config
from .utils import database, error_logger


__all__ = (
    "API_KEY",
    "PAGE_ID",
    "METRIC_LATENCY",
    "BASE_URL",
    "build_header",
    "update_latency",
    "create_latency_update_runner",
)


API_KEY = Config["statuspage.io"]["api key"]
PAGE_ID = Config["statuspage.io"]["page id"]
METRIC_LATENCY = Config["statuspage.io"]["latency metric id"]

BASE_URL = "https://{base}/{version}/pages/{page}/".format(
    base=Config["statuspage.io"]["api base"].lstrip("https://").rstrip("/"),
    version=Config["statuspage.io"]["api version"].strip("/"),
    page=PAGE_ID,
)


def build_header(
    *,
    key: str = API_KEY,
) -> dict[str, str]:
    """
    Creates the headers for the API-requests.

    Parameters
    ----------
    key: str
        The API-key.

    Returns
    -------
    dict[str, str]
    """
    return {
        "Authorization": f"OAuth {key}",
        "Content-Type": "application/json",
    }


def update_latency(
    *,
    ms: float,
    timestamp: int = None,
    metric: str = METRIC_LATENCY,
    key: str = API_KEY,
):
    """
    Updates the latency-metric on StatusPage.io.

    Parameters
    ----------
    ms: float
        The latency in ms.
    timestamp:
        The timestamp for the latency.
    metric: str
        The id for the metric.
    key: str
        The API-key.
    """
    header = build_header(key=key)
    url = "{base}/metrics/{metric}/data".format(
        base=BASE_URL.rstrip("/"),
        metric=metric,
    )
    data = {
        "data[timestamp]": timestamp or time(),
        "data[value]": ms,
    }

    response = request("POST", url=url, headers=header, params=data)

    lvl = 2 + (not response.ok)  # 3 if requests fails
    database.add_log(
        level=lvl, version=None, ip=None, msg=response.text, headers={**header, **data}
    )


def create_latency_update_runner(
    *,
    start_after: float = 10,
    interval: float = 60 * 5,
    target: str = f"http://127.0.0.1:{Config['port']}",
    method: str = "GET",
    header: dict[str, str] = None,
) -> Thread:
    """
    Creates a thread which automatically updates the latency displayed on statuspage.io.

    Parameters
    ----------
    start_after: float
        The pause before pinging first time (in s).
    interval: float
        The update interval (in s).
    target: str
        The target to ping.
    method: str
        The method which should be used for the target.
    header: dict[str, str]
        The header which should be used for the target.

    Returns
    -------
    Thread
    """
    if header is None:
        header = {"Authorization": "User Server.LatencyUpdater"}

    @error_logger(retry_timeout=60)
    def runner():
        sleep(start_after)
        while True:
            t1 = perf_counter()
            request(method, target, headers=header)
            t2 = perf_counter()

            update_latency(ms=(t2 - t1) * 1000)

            sleep(interval)

    updater = Thread(
        target=runner,
        name="<Thread: Automatic Latency Updater>",
        daemon=True,
    )
    updater.start()
    return updater
