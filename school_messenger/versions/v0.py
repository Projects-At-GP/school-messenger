from NAA import APIRequest
from NAA.web import API
from AlbertUnruhUtils.ratelimit import ServerRateLimit

from ..utils import has_user_agent, is_authorized, get_user_type
from ..config import Config, redis
from .base import VersionBase


class V0(VersionBase):
    def __init__(self, api: API):
        api.add_global_request_check(401)(has_user_agent)

        @api.add(ignore_invalid_methods=True)
        @ServerRateLimit(Config["ratelimits"], get_user_type, redis=redis)
        def users(_):
            ...

        @users.add("GET")
        @ServerRateLimit(Config["ratelimits"], get_user_type, redis=redis)
        def info(request: APIRequest):
            if not all([(query := request.get("Query"))]):
                return 400, "Missing `Query`!"
            return {"name": "", "id": ""}

        info.add_request_check(401)(is_authorized)

        @users.add("GET")
        @ServerRateLimit(Config["ratelimits"], get_user_type, redis=redis)
        def whoami(request: APIRequest):
            token = request.get("Authorization").split()[1]  # noqa
            return {"name": "", "id": ""}

        whoami.add_request_check(401)(is_authorized)

        @users.add("POST", "DELETE")
        @ServerRateLimit(Config["ratelimits"], get_user_type, redis=redis)
        def registration(request: APIRequest):
            if request.method == "POST":
                if not all([(name := request.get("Name", "")),
                            (password := request.get("Password", ""))]):
                    return 400, "Incorrect `Name` and/or `Password`!"
                return 201, {"Token": ""}

            if request.method == "DELETE":
                if not is_authorized(request):
                    return 401
                if not all([(password := request.get("Password", ""))]):
                    return 400, "Missing `Password`!"
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
            return {"Token": ""}

        @api.add("POST", "GET")
        @ServerRateLimit(Config["ratelimits"], get_user_type, redis=redis)
        def messages(request: APIRequest):
            if request.method == "GET":
                if not all([(amount := request.get("Amount", "20")).isnumeric(),
                            (before := request.get("Before", "-1")).isnumeric(),
                            (after := request.get("After", "-1")).isnumeric()]):
                    return 400, "Incorrect `Amount`, `Before` and/or `After`! (They must all be numeric!)"
                return {"messages": [{"id": "", "content": "", "author": {"id": "", "name": ""}}]}

            if request.method == "POST":
                if not all([(content := request.get("Content", ""))]):
                    return 400, "Missing `Content`!"
                return 201, {"ID": ""}

        messages.add_request_check(401)(is_authorized)
