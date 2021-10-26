from NAA import APIRequest
from NAA.web import API
from AlbertUnruhUtils.ratelimit import ServerRateLimit

from ..utils import has_user_agent, is_authorized, get_user_type
from ..config import Config, redis
from .base import VersionBase


class V1(VersionBase):
    def __init__(self, api: API):
        database = self.database

        api.add_global_request_check(401)(has_user_agent)
        api.add_global_response_check()(lambda response: print(response))

        @api.add_global_request_check(-1)
        @ServerRateLimit(Config["ratelimits"], get_user_type, redis=redis)
        def log_requests(request: APIRequest):
            database.add_log(
                level=database.LOG_LEVEL["DEBUG"],
                version=request.version,
                ip=request.ip,
                msg=f"{request.method} {request.url}",
                headers=request.headers
            )
            return True

        @api.add(ignore_invalid_methods=True)
        @ServerRateLimit(Config["ratelimits"], get_user_type, redis=redis)
        def users(_):
            ...

        @users.add("GET")
        @ServerRateLimit(Config["ratelimits"], get_user_type, redis=redis)
        def info(request: APIRequest):
            if not all([(query := request.get("Query"))]):
                return 400, "Missing `Query`!"
            data = database.account_info(query=query)
            if not data:
                return 404, "User Not Found!"
            return {"name": data[1], "id": str(data[0])}

        info.add_request_check(401)(is_authorized)

        @users.add("GET")
        @ServerRateLimit(Config["ratelimits"], get_user_type, redis=redis)
        def whoami(request: APIRequest):
            token = request.get("Authorization").split()[1]  # noqa
            data = database.account_info(token=token)
            return {"name": data[1], "id": str(data[0])}

        whoami.add_request_check(401)(is_authorized)

        @users.add("POST", "DELETE")
        @ServerRateLimit(Config["ratelimits"], get_user_type, redis=redis)
        def registration(request: APIRequest):
            if request.method == "POST":
                if not all([(name := request.get("Name", "")),
                            (password := request.get("Password", ""))]):
                    return 400, "Missing `Name` and/or `Password`!"
                data = database.add_account(name, password)
                if data is False:
                    return 400, "Incorrect `Name`! (Already registered or numeric!)"
                database.add_log(
                    level=database.LOG_LEVEL["INFO"],
                    version=request.version,
                    ip=request.ip,
                    msg=f"add account {name!r}"
                )
                return 201, {"Token": data}

            if request.method == "DELETE":
                if not is_authorized(request):
                    return 401
                if not all([(password := request.get("Password", ""))]):
                    return 400, "Missing `Password`!"
                token = request.get("Authorization").split()[1]  # noqa
                name = database.account_info(token=token)[1]
                data = database.account_delete(token, password)
                if data is False:
                    database.add_log(
                        level=database.LOG_LEVEL["WARNING"],
                        version=request.version,
                        ip=request.ip,
                        msg=f"trying delete account {name!r}",
                        headers=request.headers
                    )
                    return 401, "Password incorrect!"
                database.add_log(
                    level=database.LOG_LEVEL["INFO"],
                    version=request.version,
                    ip=request.ip,
                    msg=f"delete account {name!r}",
                    headers=request.headers
                )
                return 204

        @users.add(ignore_invalid_methods=True)
        @ServerRateLimit(Config["ratelimits"], get_user_type, redis=redis)
        def me(_):
            ...

        @me.add("GET")
        @ServerRateLimit(Config["ratelimits"], get_user_type, redis=redis)
        def token(request: APIRequest):
            if not all([(name := request.get("Name", "")),
                        (password := request.get("Password", ""))]):
                return 400, "Missing `Name` and/or `Password`!"
            data = database.account_token(name, password)
            if data is None:
                return 401
            return {"Token": data}

        @api.add("POST", "GET")
        @ServerRateLimit(Config["ratelimits"], get_user_type, redis=redis)
        def messages(request: APIRequest):
            if request.method == "GET":
                if not all([(amount := request.get("Amount", "20")).removeprefix("-").isnumeric(),
                            (before := request.get("Before", "-1")).removeprefix("-").isnumeric(),
                            (after := request.get("After", "-1")).removeprefix("-").isnumeric()]):
                    return 400, "Incorrect `Amount`, `Before` and/or `After`! (They must all be numeric!)"
                cached_authors = {}
                msgs = []
                (data) = database.get_messages(int(amount), int(before), int(after))
                for msg in data:
                    if msg[1] not in cached_authors:
                        cached_authors[msg[1]] = database.account_info(query=str(msg[1]))
                    msgs.append({"id": msg[0], "content": msg[2], "author": {"id": cached_authors[msg[1]][0],
                                                                             "name": cached_authors[msg[1]][1]}})
                return {"messages": msgs}

            if request.method == "POST":
                if not all([(content := request.get("Content", ""))]):
                    return 400, "Missing `Content`!"
                author = database.account_info(token=request.get("Authorization").split()[1])
                data = database.add_message(author[0], content)
                return 201, {"ID": data}

        messages.add_request_check(401)(is_authorized)
