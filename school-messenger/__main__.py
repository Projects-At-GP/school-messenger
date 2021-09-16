from NAA import API, APIRequest


api = API("127.0.0.1", 666, name="School Messenger")


@api.add
def users(request: APIRequest):
    return {"path": "users"}


@users.add
def info(request: APIRequest):
    return {"path": "users/info"}


@users.add
def whoami(request: APIRequest):
    return {"path": "users/whoami"}


@users.add
def registration(request: APIRequest):
    return {"path": "users/registration"}


@users.add
def me(request: APIRequest):
    return {"path": "users/me"}


@me.add
def token(request: APIRequest):
    return {"path": "users/me/token"}


@api.add
def messages(request: APIRequest):
    return {"path": "massages"}


api(debug=True)
