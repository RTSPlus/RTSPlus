import asyncio

from build_routes import build_routes
from vincenty import vincenty
import pickle

from data_model import RoutePath

def calculate_path_len(path: RoutePath):
    print("calculating path len")
    print(f"{path.id} - {path.direction} - {path.length}")

    for point in path.path:
        if point.type == 'S':
            proj_dist_ft = point.projected_dist * 0.621371 * 5280
            print(f"{point.dist}m {proj_dist_ft}ft error: {abs(point.dist - proj_dist_ft) / point.dist if point.dist else 0}%")


    print()
    print(f"Distance: {path.path[-1].projected_dist}km, {path.path[-1].projected_dist * 0.621371}mi, {path.path[-1].projected_dist * 0.621371 * 5280}ft")

async def main():
    routes = await build_routes(proj_dist_scaling_factor=0.9585)
    # routes = pickle.load( open( "routes.p", "rb" ) )

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

    # to inspect
    route = 1
    path = 500500

    calculate_path_len(routes[route].path[path])


asyncio.run(main())
