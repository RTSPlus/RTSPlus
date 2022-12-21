import asyncio

from build_routes import build_routes
from vincenty import vincenty
import pickle

from data_model import RoutePath

def calculate_path_len(path: RoutePath):
    print("calculating path len")
    print(f"{path.id} - {path.direction} - {path.length}")

    total_len = 0
    for i, point in enumerate(path.path):
        print(point)
        if i > 0:
            total_len += vincenty((point.lat, point.lon), (path.path[i-1].lat, path.path[i-1].lon))

    print(f"\tDistance: {total_len}km, {total_len * 0.621371}mi, {total_len * 0.621371 * 5280}ft")


async def main():
    # routes = await build_routes()
    routes = pickle.load( open( "routes.p", "rb" ) )

    for route_num, route in routes.items():
        print("--------")
        print(f"Route {route_num} - {route.name}")
        print("Paths:")
        for path in route.path.values():
            print(f"\tpid: {path.id} - {path.direction}")
            print(f"\tlength: {path.length}")
            print(f"\tStart: {path.path[0].lat}, {path.path[0].lon}")
            print(f"\tEnd: {path.path[-1].lat}, {path.path[-1].lon}")
            dist = vincenty((path.path[0].lat, path.path[0].lon), (path.path[-1].lat, path.path[-1].lon))
            print(f"\tDistance: {dist}km, {dist * 0.621371}mi, {dist * 0.621371 * 5280}ft")
            print()

    calculate_path_len(routes[1].path[500500])

asyncio.run(main())
