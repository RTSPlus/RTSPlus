import asyncio
import pickle

from vincenty import vincenty
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from build_routes import build_routes
from data_model import RoutePath


def calculate_path_len(path: RoutePath):
    print("calculating path len")
    print(f"{path.id} - {path.direction} - {path.length}")

    for point in path.path:
        if point.type == "S":
            proj_dist_ft = point.projected_dist * 0.621371 * 5280
            print(
                f"{point.dist}m {proj_dist_ft}ft error: {abs(point.dist - proj_dist_ft) / point.dist if point.dist else 0}%"
            )

    print()
    print(
        f"Distance: {path.path[-1].projected_dist}km, {path.path[-1].projected_dist * 0.621371}mi, {path.path[-1].projected_dist * 0.621371 * 5280}ft"
    )


async def main():
    routes = await build_routes(proj_dist_scaling_factor=0.98)
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
            dist = vincenty(
                (path.path[0].lat, path.path[0].lon),
                (path.path[-1].lat, path.path[-1].lon),
            )
            print(
                f"\tDistance: {dist}km, {dist * 0.621371}mi, {dist * 0.621371 * 5280}ft"
            )
            print()

    # to inspect
    route_num = 1
    path_num = 500500

    calculate_path_len(routes[route_num].path[path_num])

    path = routes[route_num].path[path_num]
    to_waypoints_df = {"lat": [], "lon": [], "typ": []}
    to_stops_df = {"lat": [], "lon": [], "typ": [], "name": [], "id": [], "dist": []}

    for point in path.path:
        if point.type == "W":
            to_waypoints_df["lat"].append(point.lat)
            to_waypoints_df["lon"].append(point.lon)
            to_waypoints_df["typ"].append(point.type)
        if point.type == "S":
            to_stops_df["lat"].append(point.lat)
            to_stops_df["lon"].append(point.lon)
            to_stops_df["typ"].append(point.type)
            to_stops_df["name"].append(point.name)
            to_stops_df["id"].append(point.id)
            to_stops_df["dist"].append(point.dist)

    waypoints_df = pd.DataFrame(to_waypoints_df)
    stops_df = pd.DataFrame(to_stops_df)

    # Waypoints
    fig = go.Figure(
        go.Scattermapbox(
            mode="markers+lines",
            lat=waypoints_df["lat"],
            lon=waypoints_df["lon"],
            marker={"size": 10},
        )
    )

    # Stops
    fig.add_trace(
        go.Scattermapbox(
            mode="markers+text",
            lat=stops_df["lat"],
            lon=stops_df["lon"],
            text=stops_df["name"],
            marker={"size": 10},
        )
    )

    fig.update_layout(
        margin={"l": 0, "t": 0, "b": 0, "r": 0},
        mapbox={
            "center": {
                "lon": waypoints_df["lon"].median(),
                "lat": waypoints_df["lat"].median(),
            },
            "style": "carto-positron",
            "zoom": 13,
        },
    )

    # fig = px.scatter_mapbox(df, lat="lat", lon="lon", color="typ", zoom=14)
    # fig.update_layout(mapbox_style="carto-positron")
    # fig.show()


asyncio.run(main())
