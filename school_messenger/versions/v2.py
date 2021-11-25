from NAA import APIResponse
from NAA.web import API

from .base import VersionBase


__all__ = ("V2",)


# all from v1
class V2(VersionBase):
    def __init__(self, api: API):
        @api.add_global_response_check()
        def lower_all_json(response: APIResponse):
            json = {}
            for k, v in response.response.items():
                json[k.lower()] = v
            response._response = json  # noqa
            return response
