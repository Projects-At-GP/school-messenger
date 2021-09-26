from NAA import APIRequest
from NAA.web import API

from ..utils import has_user_agent, is_authorized
from ..database import DataBase


class V1:
    def __init__(self, api: API):
        database = DataBase("database.sqlite")

        api.add_global_request_check(401)(has_user_agent)

        @api.add(ignore_invalid_methods=True)
        def users(_):
            ...

        @users.add("GET")
        def info(request: APIRequest):
            if not all([(query := request.get("Query"))]):
                return 400
            data = database.account_info(query=query)
            if not data:
                return 404
            return {"name": data[1], "id": str(data[0])}

        info.add_request_check(401)(is_authorized)

        @users.add("GET")
        def whoami(request: APIRequest):
            token = request.get("Authorization")  # noqa
            data = database.account_info(token=token)
            return {"name": data[1], "id": str(data[0])}

        whoami.add_request_check(401)(is_authorized)

        @users.add("POST", "DELETE")
        def registration(request: APIRequest):
            if request.method == "POST":
                if not all([(name := request.get("Name", "")),
                            (password := request.get("Password", ""))]):
                    return 400
                data = database.add_account(name, password)
                if data is False:
                    return 400
                return 201, {"Token": data}

            if request.method == "DELETE":
                if not is_authorized(request):
                    return 401
                if not all([(password := request.get("Password", ""))]):
                    return 400
                token = request.get("Authorization")  # noqa
                data = database.account_delete(token, password)
                if data is False:
                    return 401
                return 204

        @users.add(ignore_invalid_methods=True)
        def me(_):
            ...

        @me.add("GET")
        def token(request: APIRequest):
            if not all([(name := request.get("Name", "")),
                        (password := request.get("Password", ""))]):
                return 400
            data = database.account_token(name, password)
            if data is None:
                return 401
            return {"Token": data}

        @api.add("POST", "GET")
        def messages(request: APIRequest):
            if request.method == "GET":
                if not all([(amount := request.get("Amount", "20")).removeprefix("-").isnumeric(),
                            (before := request.get("Before", "-1")).removeprefix("-").isnumeric(),
                            (after := request.get("After", "-1")).removeprefix("-").isnumeric()]):
                    return 400
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
                    return 400
                author = database.account_info(token=request.get("Authorization").split()[1])
                data = database.add_message(author[0], content)
                return 201, {"ID": data}

        messages.add_request_check(401)(is_authorized)
