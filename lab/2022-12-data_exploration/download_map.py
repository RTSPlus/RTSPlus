import urllib.parse
import subprocess
from math import sin, pi

image_file_name = "map.jpg"

max_lat = 29.715481941424365
min_lat = 29.589633295601942
max_lon = -82.24136916824027
min_lon = -82.446655

size = 640, 640
format = "jpg"

params = {
    "key": "AIzaSyCU1pMXd8rnm3W8r4w5H0ylMnnPS2atJ4g",
    "size": f"{size[0]}x{size[1]}",
    "scale": 2,
    "markers": f"color:blue|{max_lat},{max_lon}|{min_lat},{min_lon}",
    "format": format,
}
url = f"https://maps.googleapis.com/maps/api/staticmap?{urllib.parse.urlencode(params)}"

print(url)
# print(subprocess.getoutput(f"curl {url} > {image_file_name}"))