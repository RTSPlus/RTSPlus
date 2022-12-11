from concurrent.futures import ThreadPoolExecutor
import hashlib
import hmac
import time
import datetime
import urllib.request
from urllib.parse import urlencode
import json
import os

import sqlite3
import atexit

interval = 5
con = sqlite3.connect("bus_data.db")

# Load env variables with python-dotenv

def api_call(endpoint_url, request_type, params={}, xtime=None):
    hash_key = os.getenv('RTS_HASH_KEY')
    api_key = os.getenv('RTS_API_KEY')

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
    req = urllib.request.Request(
        f"https://riderts.app/bustime/{endpoint_url}?{encoded_query_params}",
        headers=headers,
    )
    with urllib.request.urlopen(req) as response:
        res = response.read()
        return json.loads(res)


def chunk(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def exit_handler():
    con.close()


atexit.register(exit_handler)

while True:
    xtime = round(time.time() * 1000)
    print(f"Request at {xtime}")

    res_routes = api_call("/api/v3/getroutes", "getroutes")["bustime-response"][
        "routes"
    ]
    routes = [(route["rt"], route["rtnm"]) for route in res_routes]

    # TODO: Replace with aiohttp
    chunked = list(chunk(routes, 10))
    results = []
    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(
                api_call,
                "/api/v3/getvehicles",
                "getvehicles",
                {"rt": ",".join([route[0] for route in chunk])},
                xtime=xtime,
            )
            for chunk in chunked
        ]
        for future in futures:
            try:
                results.extend(future.result()["bustime-response"]["vehicle"])
            except:
                pass

    # create table queries(id integer primary key, data text);
    cur = con.cursor()
    cur.execute("insert into queries values(?, ?)", (xtime, json.dumps(results)))
    con.commit()

    time.sleep(interval)
