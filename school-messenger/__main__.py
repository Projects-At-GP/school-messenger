from NAA import APIRequest
from NAA.web import API


api = API("127.0.0.1", 2345, name="School Messenger")


@api.add(ignore_invalid_methods=True)
def users(request: APIRequest):
    return 403


@users.add("GET")
def info(request: APIRequest):
    return {"name": "",
            "id": ""}


@users.add("GET")
def whoami(request: APIRequest):
    return {"name": "",
            "id": ""}


@users.add("POST", "DELETE")
def registration(request: APIRequest):
    if request.method == "POST":
        return 201, {"Token": ""}
    if request.method == "DELETE":
        return 204


@users.add(ignore_invalid_methods=True)
def me(request: APIRequest):
    return 403


@me.add("GET")
def token(request: APIRequest):
    return {"Token": ""}


@api.add("POST", "GET")
def messages(request: APIRequest):
    if request.method == "POST":
        return 201, {"ID": ""}
    if request.method == "GET":
        return {"messages": [{"id": "", "content": "", "author": {"id": "", "name": ""}},
                             {"id": "", "content": "", "author": {"id": "", "name": ""}}]}


api(debug=True)
