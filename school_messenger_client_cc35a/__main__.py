import requests
from json import loads
import sys
import time

ip = '127.0.0.1'
port = 3333

headers = {
    'User-Agent': 'SchoolMessengerClientCC35A xy',
    'Authorization': ':D'
}
while True:
    r = requests.get(f"http://{ip}:{port}/messages", headers=headers)
    print(r)
    print(r.text)

