import json
from functools import partial
from typing import List
from dataclasses import dataclass

import requests


@dataclass
class AddressInfo:
    address: str
    thread: int
    final_balance: float
    final_roll_count: int
    candidate_balance: float
    candidate_roll_count: int


class JsonApi:
    @staticmethod
    def get_status() -> tuple[dict[str, str], str]:
        headers = {"Content-type": "application/json"}
        payload = json.dumps(
            {"jsonrpc": "2.0", "method": "get_status", "id": 0, "params": []}
        )
        return headers, payload

    @staticmethod
    def stop_node():
        # print("stop node")
        headers = {"Content-type": "application/json"}
        payload = json.dumps(
            {"jsonrpc": "2.0", "method": "stop_node", "id": 0, "params": []}
        )
        # print(f"${headers=} - ${payload=}")
        return headers, payload

    @staticmethod
    def get_addresses(addresses: List[str]):
        headers = {"Content-type": "application/json"}
        payload = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "get_addresses",
                "id": 0,
                "params": [addresses],
            }
        )
        return headers, payload

    @staticmethod
    def send_operations(operations: List[bytes]):
        headers = {"Content-type": "application/json"}
        payload = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "send_operations",
                "id": 0,
                "params": [operations],
            }
        )
        return headers, payload

    @staticmethod
    def add_staking_secret_keys(secret_keys: List[str]):
        headers = {"Content-type": "application/json"}
        payload = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "add_staking_secret_keys",
                "id": 0,
                "params": [secret_keys],
            }
        )
        return headers, payload

    @staticmethod
    def node_peers_whitelist():
        headers = {"Content-type": "application/json"}
        payload = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "node_peers_whitelist",
                "id": 0,
                "params": [],
            }
        )
        return headers, payload

    @staticmethod
    def get_stakers():
        headers = {"Content-type": "application/json"}
        payload = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "get_stakers",
                "id": 0,
                "params": [],
            }
        )
        return headers, payload

# class Api:
#     def __init__(self, url) -> None:
#         self.url = url
#         self._api = JsonApi()
#
#     def _make_request(self, headers, payload):
#         response = requests.post(self.url, headers=headers, data=payload)
#         return response.json()
#
#     def __getattr__(self, item):
#         # Get function from json api
#         f = getattr(self._api, item)
#         headers, payload = f()
#         # Return a function (that will make the json rpc call) ready to be called
#         return partial(self._make_request, headers, payload)


class Api2:
    def __init__(self, url) -> None:
        self.url = url
        self._api = JsonApi()

    def _make_request(self, *args):
        f = getattr(self._api, args[0])
        headers, payload = f(*args[1:])
        # print(f"{headers=}")
        # print(f"{payload=}")
        response = requests.post(self.url, headers=headers, data=payload)
        return response.json()

    def __getattr__(self, item):
        if hasattr(self._api, item):
            return partial(self._make_request, item)
        else:
            raise AttributeError
