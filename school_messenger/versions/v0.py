from NAA import APIRequest
from NAA.web import API

from school_messenger.utils import has_user_agent, is_authorized


class V0:
    def __init__(self, api: API):
        api.add_global_request_check(401)(has_user_agent)

        @api.add(ignore_invalid_methods=True)
        def users(_):
            ...

        @users.add("GET")
        def info(request: APIRequest):
            if not all([(query := request.get("Query"))]):
                return 400
            return {"name": "", "id": ""}

        info.add_request_check(401)(is_authorized)

        @users.add("GET")
        def whoami(request: APIRequest):
            token = request.get("Authorization")  # noqa
            return {"name": "", "id": ""}

        whoami.add_request_check(401)(is_authorized)

        @users.add("POST", "DELETE")
        def registration(request: APIRequest):
            if request.method == "POST":
                if not all([(name := request.get("Name", "")),
                            (password := request.get("Password", ""))]):
                    return 400
                return 201, {"Token": ""}

            if request.method == "DELETE":
                if not is_authorized(request):
                    return 401
                if not all([(password := request.get("Password", ""))]):
                    return 400
                return 204

        @users.add(ignore_invalid_methods=True)
        def me(_):
            ...

        @me.add("GET")
        def token(request: APIRequest):
            if not all([(name := request.get("Name", "")),
                        (password := request.get("Password", ""))]):
                return 400
            return {"Token": ""}

        @api.add("POST", "GET")
        def messages(request: APIRequest):
            if request.method == "GET":
                if not all([(amount := request.get("Amount", "20")).isnumeric(),
                            (before := request.get("Before", "-1")).isnumeric(),
                            (after := request.get("After", "-1")).isnumeric()]):
                    return 400
                return {"messages": [{"id": "", "content": "", "author": {"id": "", "name": ""}}]}

            if request.method == "POST":
                if not all([(content := request.get("Content", ""))]):
                    return 400
                return 201, {"ID": ""}

        messages.add_request_check(401)(is_authorized)
