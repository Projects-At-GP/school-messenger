from NAA import APIRequest
from NAA.web import API

from school_messenger.utils import has_user_agent, is_authorized, generate_id


class V0:
    def __init__(self, api: API):
        api.add_global_request_check(401)(has_user_agent)

        @api.add(ignore_invalid_methods=True)
        def users(_):
            ...

        @users.add("GET")
        def info(request: APIRequest):
            return {"name": "",
                    "id": str(generate_id(1))}

        info.add_request_check(401)(is_authorized)

        @users.add("GET")
        def whoami(request: APIRequest):
            return {"name": "",
                    "id": str(generate_id(1))}

        whoami.add_request_check(401)(is_authorized)

        @users.add("POST", "DELETE")
        def registration(request: APIRequest):
            if request.method == "POST":
                return 201, {"Token": ""}

            if request.method == "DELETE":
                if not is_authorized(request):
                    return 401

                return 204

        @users.add(ignore_invalid_methods=True)
        def me(_):
            ...

        @me.add("GET")
        def token(request: APIRequest):
            return {"Token": ""}

        @api.add("POST", "GET")
        def messages(request: APIRequest):
            if request.method == "POST":
                return 201, {"ID": str(generate_id(2))}

            if request.method == "GET":
                return {"messages": [
                    {"id": str(generate_id(2)), "content": "", "author": {"id": str(generate_id(1)), "name": ""}}]}

        messages.add_request_check(401)(is_authorized)
