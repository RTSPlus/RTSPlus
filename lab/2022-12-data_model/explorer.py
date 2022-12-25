import asyncio
import pickle
from typing import Dict

from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
import plotly.graph_objects as go
import pandas as pd


from build_routes import build_routes
from data_model import Route, RoutePath
from util import km2ft


def print_help():
    print()
    print("Commands: exit, help")
    print()


async def get_routes(cache=True) -> Dict[int, Route]:
    return (
        pickle.load(open("routes.p", "rb"))
        if cache
        else await build_routes(proj_dist_scaling_factor=0.98)
    )


def graph_path(path: RoutePath):
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


async def main():
    session = PromptSession()
    running = True

    print_help()

    # Get route paths ahead of time
    routes = await get_routes()
    path_map = {}
    for route_key, route in routes.items():
        for key in route.path.keys():
            path_map[key] = route_key

    while running:
        with patch_stdout():
            command = await session.prompt_async("> ")

        match command.split():
            case [("quit" | "q")]:
                running = False
            case ["help"]:
                print_help()
            case ["list", "routes", *args]:
                print("Listing routes...")
                routes = await get_routes("-clear-cache" not in args)

                format = "long" if "-long" in args else "short"

                for route_num, route in routes.items():
                    print("--------")
                    print(f"Route {route_num} - {route.name}")

                    if format == "long":
                        print("Paths:")
                        for path in route.path.values():
                            print(f"\tpid: {path.id} - {path.direction}")
                            print(f"\treported length: {path.reported_length}ft")
                            print(
                                f"\tprojected length: {km2ft(path.path[-1].projected_dist)}ft"
                            )
                            print(f"\tStart: {path.path[0].lat}, {path.path[0].lon}")
                            print(f"\tEnd: {path.path[-1].lat}, {path.path[-1].lon}")
                            print()
                    else:
                        short_str = ", ".join(
                            [
                                f"{path.id} - {path.direction}"
                                for path in route.path.values()
                            ]
                        )
                        print(f"Paths: {short_str}")
            case ["graph", "path", path_num]:
                rt = path_map[int(path_num)]
                graph_path(routes[rt].path[int(path_num)])


if __name__ == "__main__":
    asyncio.run(main())
