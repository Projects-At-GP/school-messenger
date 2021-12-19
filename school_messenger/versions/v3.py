from NAA import APIRequest
from NAA.web import API
from AlbertUnruhUtils.ratelimit import ServerRateLimit

from ..utils import is_authorized, get_user_type
from ..config import Config, redis
from .base import VersionBase


__all__ = ("V3",)


# all from v2
class V3(VersionBase):
    def __init__(self, api: API):
        database = self.database

        @api.add(ignore_invalid_methods=True)
        @ServerRateLimit(Config["ratelimits"], get_user_type, redis=redis)
        def admin(_: APIRequest):
            ...

        @admin.add("GET")
        @ServerRateLimit(Config["ratelimits"], get_user_type, redis=redis)
        def logs(request: APIRequest):
            if not all(
                [
                    (amount := request.get("Amount", "-1"))
                    .removeprefix("-")
                    .isnumeric(),
                    (before := request.get("Before", "-1"))
                    .removeprefix("-")
                    .isnumeric(),
                    (after := request.get("After", "-1")).removeprefix("-").isnumeric(),
                ]
            ):
                database.add_log(
                    level=database.LOG_LEVEL["INFO"],
                    version=request.version,
                    ip=request.ip,
                    msg=f"invalid amount/before/after while requesting log history",
                    headers=request.headers,
                )
                return (
                    400,
                    "Incorrect `Amount`, `Before` and/or `After`! (They must all be numeric!)",
                )
            logs = []  # noqa
            (data) = database.get_logs(int(amount), int(before), int(after))
            for log in data:
                logs.append(
                    {
                        "date": log[0],
                        "level": log[1],
                        "version": log[2],
                        "ip": log[3],
                        "message": log[4],
                        "headers": log[5],
                    }
                )
            database.add_log(
                level=database.LOG_LEVEL["INFO"],
                version=request.version,
                ip=request.ip,
                msg=f"Requested max {amount} logs from {before} to {after}.",
                headers={"logs": logs},
            )
            return {"logs": logs}

        logs.add_request_check(401)(is_authorized)

        @admin.add("DELETE", "PUT")
        @ServerRateLimit(Config["ratelimits"], get_user_type, redis=redis)
        def user(request: APIRequest):
            # DELETE -> delete acc (req. id)
            # PUT -> update acc (req. id, mode (cur. "admin" only))
            return 501

        @admin.add("DELETE")
        @ServerRateLimit(Config["ratelimits"], get_user_type, redis=redis)
        def messages(request: APIRequest):
            if not all(
                [
                    (id := request.get("Id", "null")).isnumeric(),  # noqa
                ]
            ):
                return 400, "Incorrect `Id`! (Must be numeric!)"
            if not (msg := database.delete_message(id)):
                return 400, "Incorrect `Id`! (Not in database!)"
            return {"msg": msg}

        @admin.add_request_check(401)
        @logs.add_request_check(401)
        @user.add_request_check(401)
        @messages.add_request_check(401)
        def is_admin(request: APIRequest) -> bool:
            return get_user_type(request) == 31  # == "admin"
