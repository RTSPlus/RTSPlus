import hashlib
import hmac
import time
import datetime
import urllib.request
from urllib.parse import urlencode
import json
import os

hash_key = os.getenv('RTS_HASH_KEY')
api_key = os.getenv('RTS_API_KEY')

req_xtime = round(time.time() * 1000)

fmt_time = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")

query_params = {
    "requestType": "getvehicles",
    "rt": "20",
    "key": api_key,
    "format": "json",
    "xtime": req_xtime,
}

hash_data = f"/api/v3/getvehicles?{urlencode(query_params)}{fmt_time}"
headers = {
    "X-Date": fmt_time,
    "X-Request-ID": hmac.new(
        hash_key.encode("utf-8"), hash_data.encode("utf-8"), hashlib.sha256
    ).hexdigest(),
}
print(urlencode(query_params))
print(headers)
req = urllib.request.Request(
    "https://riderts.app/bustime/api/v3/getvehicles?" + urlencode(query_params),
    headers=headers,
)
with urllib.request.urlopen(req) as response:
    res = response.read()
    print(json.loads(res))
