import asyncio
import pickle
from typing import Dict
import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv

from build_routes import build_routes
from data_model import Route, RoutePath
from util import km2ft

load_dotenv()


async def main():
    # routes = await build_routes(proj_dist_scaling_factor=0.98)
    routes: Dict[int, Route] = pickle.load(open("routes.p", "rb"))

    for route_num, route in routes.items():
        print("--------")
        print(f"Route {route_num} - {route.name}")
        print("Paths:")
        for path in route.path.values():
            print(f"\tpid: {path.id} - {path.direction}")
            print(f"\treported length: {path.reported_length}ft")
            print(f"\tprojected length: {km2ft(path.path[-1].projected_dist)}ft")
            print(f"\tStart: {path.path[0].lat}, {path.path[0].lon}")
            print(f"\tEnd: {path.path[-1].lat}, {path.path[-1].lon}")
            print()

    # to inspect
    route_num = 20
    path_num = 500354

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
        to_waypoints_df["lat"].append(point.lat)
        to_waypoints_df["lon"].append(point.lon)
        to_waypoints_df["typ"].append(point.type)

    for point in path.stops:
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

    fig.show()


asyncio.run(main())
