import asyncio
import pickle
from typing import Dict
import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv

from build_routes import build_routes, snap_route_path_google_api
from data_model import Route, RoutePath
from util import km2ft

load_dotenv()


def experiment_with_path(path: RoutePath):
    # print("calculating path len")
    # print(f"{path.id} - {path.direction} - {path.length}")

    # for point in path.path:
    #     if point.type == "S":
    #         proj_dist_ft = point.projected_dist * 0.621371 * 5280
    #         print(
    #             f"{point.reported_dist}ft {proj_dist_ft}ft error: {abs(point.reported_dist - proj_dist_ft) / point.reported_dist if point.reported_dist else 0}%"
    #         )

    # print()
    # print(
    #     f"Distance: {path.path[-1].projected_dist}km, {path.path[-1].projected_dist * 0.621371}mi, {path.path[-1].projected_dist * 0.621371 * 5280}ft"
    # )
    # print(
    #     "|".join(
    #         [
    #             f"{point.lat},{point.lon}"
    #             for point in path.path[:100]
    #             if point.type == "W"
    #         ]
    #     )
    # )
    # for point in path.path:
    # print(point.lat

    snap_route_path_google_api(path, os.environ.get("GOOGLE_API_KEY"))


async def main():
    # routes = await build_routes(proj_dist_scaling_factor=0.98)
    routes: Dict[int, Route] = pickle.load(open("routes.p", "rb"))

    for route_num, route in routes.items():
        print("--------")
        print(f"Route {route_num} - {route.name}")
        print("Paths:")
        for path in route.path.values():
            print(f"\tpid: {path.id} - {path.direction}")
            print(f"\treported length: {path.length}ft")
            print(f"\tprojected length: {km2ft(path.path[-1].projected_dist)}ft")
            print(f"\tStart: {path.path[0].lat}, {path.path[0].lon}")
            print(f"\tEnd: {path.path[-1].lat}, {path.path[-1].lon}")
            print()

    # to inspect
    route_num = 1
    path_num = 500500

    experiment_with_path(routes[route_num].path[path_num])

    path = routes[route_num].path[path_num]
    to_waypoints_df = {"lat": [], "lon": [], "typ": []}
    to_stops_df = {
        "lat": [],
        "lon": [],
        "typ": [],
        "name": [],
        "id": [],
        "dist": [],
        "combined_text": [],
    }

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
            to_stops_df["dist"].append(point.reported_dist)

            to_stops_df["combined_text"].append(
                f"{point.name} - {point.id} - {point.reported_dist}ft"
            )

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
            text=stops_df["combined_text"],
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
            # "style": "open-street-map",
            # "style": "stamen-terrain",
            "zoom": 13,
        },
    )

    # fig.show()


asyncio.run(main())
