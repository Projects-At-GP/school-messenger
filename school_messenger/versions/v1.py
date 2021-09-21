from NAA import APIRequest
from NAA.web import API

from school_messenger.utils import has_user_agent, is_authorized, generate_id


class V1:
    def __init__(self, api: API):
        api.add_global_request_check(401)(has_user_agent)

        ...
