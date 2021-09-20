from requests import request
import sys

TOKEN = "MySuperToken"
USER_AGENT = "SchoolMessengerClientAlbertUnruh Python{v.major}.{v.minor}".format(v=sys.version_info)
HEADERS = {
    "User-Agent": USER_AGENT,
    "Authorization": TOKEN
}
HOST = "http://127.0.0.1:3333/"

r = request("POST", HOST+"messages", headers=HEADERS)
print(r)
if r:
    print(r.json())
