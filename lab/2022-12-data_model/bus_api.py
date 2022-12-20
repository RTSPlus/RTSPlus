from enum import Enum
from typing import Literal, overload

import os
import time
import datetime
import urllib.request
from urllib.parse import urlencode
import aiohttp

import hashlib
import hmac
import json

from dotenv import load_dotenv

load_dotenv()

class API_Call(Enum):
    GET_ROUTES = {
        "endpoint_url": "/api/v3/getroutes",
        "request_type": "getroutes",
    }

    GET_ROUTE_PATTERNS = {
        "endpoint_url": "/api/v3/getpatterns",
        "request_type": "getpatterns",
    }

RTS_HASH_KEY_STR = "RTS_HASH_KEY"
RTS_HASH_API_STR = "RTS_API_KEY"

def build_api_url(endpoint_url: str = None, request_type: str = None, params={}, xtime: int = None):
    hash_key = os.getenv(RTS_HASH_KEY_STR)
    api_key = os.getenv(RTS_HASH_API_STR)

    if not hash_key:
        raise Exception(f"No hash_key found in path (searching for {RTS_HASH_KEY_STR} environment variable)")
    if not api_key:
        raise Exception(f"No api_key found in path (searching for {RTS_HASH_API_STR} environment variable)")

    xtime = round(time.time() * 1000) if xtime is None else xtime
    fmt_time = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")

    query_params = {
        "requestType": request_type,
        "key": api_key,
        "xtime": xtime,
        "format": "json",
        **params,
    }
    encoded_query_params = urlencode(query_params)

    hash_data = f"{endpoint_url}?{encoded_query_params}{fmt_time}"
    headers = {
        "X-Date": fmt_time,
        "X-Request-ID": hmac.new(
            hash_key.encode("utf-8"), hash_data.encode("utf-8"), hashlib.sha256
        ).hexdigest(),
    }
    return f"https://riderts.app/bustime/{endpoint_url}?{encoded_query_params}", headers

@overload
def api_call(endpoint_url: str, request_type: str, params={}): ...

@overload
def api_call(call_type: Literal[API_Call.GET_ROUTES], params: None = None): ...

def api_call(
        endpoint_url: str = None,
        request_type: str = None,
        call_type: API_Call = None, params={},
        xtime: int = None
    ):

    if call_type:
        endpoint_url = call_type.value['endpoint_url']
        request_type = call_type.value['request_type']
    else:
        if not endpoint_url:
            raise Exception("`endpoint_url` not provided")
        if not request_type:
            raise Exception("`request_type` not provided")

    url, headers = build_api_url(endpoint_url, request_type, params, xtime)

    req = urllib.request.Request(
        url,
        headers=headers,
    )
    with urllib.request.urlopen(req) as response:
        res = response.read()
        return json.loads(res)

async def async_api_call(
        session=aiohttp.ClientSession(),
        endpoint_url: str = None,
        request_type: str = None, 
        call_type: API_Call = None,
        params={},
        xtime: int = None
    ):

    if call_type:
        endpoint_url = call_type.value['endpoint_url']
        request_type = call_type.value['request_type']
    else:
        if not endpoint_url:
            raise Exception("`endpoint_url` not provided")
        if not request_type:
            raise Exception("`request_type` not provided")

    url, headers = build_api_url(endpoint_url, request_type, params, xtime)

    # async with aiohttp.ClientSession() as session:
    async with session.get(url, headers=headers) as resp:
        return await resp.json()