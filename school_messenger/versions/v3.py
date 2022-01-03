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
        async def admin(_: APIRequest):
            ...

        @admin.add("GET")
        @ServerRateLimit(Config["ratelimits"], get_user_type, redis=redis)
        async def logs(request: APIRequest):
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
                await database.add_log(
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
            (data) = await database.get_logs(int(amount), int(before), int(after))
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
            await database.add_log(
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
        async def user(request: APIRequest):
            if request.method == "DELETE":
                if not all(
                    [
                        (id := request.get("Id", "null")).isnumeric(),  # noqa
                    ]
                ):
                    if not await database.account_delete(id=id):
                        return 400, "Invalid `Id`! (Not in database or admin!)"
                    return 204, f"Account {id} successfully deleted."

            if request.method == "PUT":
                valid_modes = {
                    "admin": 31,
                }
                if not all(
                    [
                        (id := request.get("Id", "null")).isnumeric(),  # noqa
                        (mode := request.get("Mode", "invalid mode")) in valid_modes,
                    ]
                ):
                    return (
                        400,
                        f"Invalid `Id` or `Mode`! (`Id` must be numeric! `Mode` must be in {', '.join(valid_modes)}!)",
                    )
                new_id = await database.change_account_type(id, valid_modes[mode])
                return 202, {"id": str(new_id), "type": str(valid_modes[mode])}

        @admin.add("DELETE")
        @ServerRateLimit(Config["ratelimits"], get_user_type, redis=redis)
        async def messages(request: APIRequest):
            if not all(
                [
                    (id := request.get("Id", "null")).isnumeric(),  # noqa
                ]
            ):
                return 400, "Incorrect `Id`! (Must be numeric!)"
            if not (msg := await database.delete_message(id)):
                return 400, "Invalid `Id`! (Not in database!)"
            return {"id": str(msg[0]), "author": str(msg[1]), "content": msg[2]}

        @admin.add_request_check(401)
        @logs.add_request_check(401)
        @user.add_request_check(401)
        @messages.add_request_check(401)
        async def is_admin(request: APIRequest) -> bool:
            return await get_user_type(request) == 31  # == "admin"
