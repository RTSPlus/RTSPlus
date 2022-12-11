from math import floor
from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

import urllib.request
from urllib.parse import parse_qs, urlencode

import time
import json
import os

x_date = ""
x_request_id = ""
api_key = os.getenv('RTS_API_KEY') 
req_xtime = ""
rt = ""

chrome_options = Options()
chrome_options.add_argument("--headless")
driver = webdriver.Chrome(options=chrome_options)

driver.get("https://riderts.app/map")

try:
    maptool_btn = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.ID, "maptool-routes"))
    )
    maptool_btn.click()

    map_route_select = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, '[labelforid="bt-map-route-select"]')
        )
    )
    map_route_select.click()
    elemns = map_route_select.find_elements(By.CLASS_NAME, "ng-option")
    # elemns[0].click()
    # elemns[1].click()
    for elem in map_route_select.find_elements(By.CLASS_NAME, "ng-option"):
        elem.click()

    requests_found = False
    while not requests_found:
        for request in driver.requests:
            if request.url.startswith("https://riderts.app/bustime/api/v3/getvehicles"):
                requests_found = True

                x_date = request.headers["X-Date"]
                x_request_id = request.headers["X-Request-ID"]
                # api_key = parse_qs(request.querystring)["key"][0]
                req_xtime = parse_qs(request.querystring)["xtime"][0]
                rt = parse_qs(request.querystring)["rt"][0]
                break
finally:
    driver.quit()

print(int(round(time.time() * 1000)))
print(req_xtime)
query_params = {
    "requestType": "getvehicles",
    "rt": rt,
    "key": api_key,
    "format": "json",
    "xtime": req_xtime,
}

headers = {
    "X-Date": x_date,
    "X-Request-ID": x_request_id,
}
req = urllib.request.Request(
    "https://riderts.app/bustime/api/v3/getvehicles?" + urlencode(query_params),
    headers=headers,
)
with urllib.request.urlopen(req) as response:
    res = response.read()
    print(json.loads(res))
