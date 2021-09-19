from NAA import APIRequest
from NAA.web import API

from .utils import is_authorized


api = API("0.0.0.0", 3333, name="School Messenger")


@api.add(ignore_invalid_methods=True)
def users(_):
    ...


@users.add("GET")
def info(request: APIRequest):
    if not is_authorized(request):
        return 401

    return {"name": "",
            "id": ""}


@users.add("GET")
def whoami(request: APIRequest):
    if not is_authorized(request):
        return 401

    return {"name": "",
            "id": ""}


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
    if not is_authorized(request):
        return 401

    if request.method == "POST":
        return 201, {"ID": ""}

    if request.method == "GET":
        return {"messages": [{"id": "", "content": "", "author": {"id": "", "name": ""}},
                             {"id": "", "content": "", "author": {"id": "", "name": ""}}]}


api(debug=True, reload=True)
