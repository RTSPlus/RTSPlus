import asyncio
import datetime
import pickle
from typing import Dict, List

from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import NestedCompleter

import plotly.graph_objects as go
import pandas as pd
import duckdb


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
    con = duckdb.connect(database="../duck_data.duckdb", read_only=True)

    session = PromptSession()
    running = True

    print_help()

    # Get route paths ahead of time
    routes = await get_routes()
    path_map = {}
    for route_key, route in routes.items():
        for key in route.path.keys():
            path_map[key] = route_key

    query_days: List[datetime.date] = con.execute(
        f"""
            select distinct request_date from
            (
                select epoch_ms(request_time_ms) as request_time, date_trunc('day', request_time) as request_date, *
                from queries
            )
            """
    ).fetchall()

    # Set up completer
    completer = NestedCompleter.from_nested_dict(
        {
            "list": {"routes": None},
            "query": {
                "days": None,
                "trips": {
                    "day": {date[0].strftime("%Y-%m-%d"): None for date in query_days}
                },
            },
            "quit": None,
            "help": None,
        }
    )

    while running:
        with patch_stdout():
            command = await session.prompt_async(
                "> ", auto_suggest=AutoSuggestFromHistory(), completer=completer
            )

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
            case ["query", "days"]:
                res: List[datetime.date] = con.execute(
                    f"""
                        select distinct request_date from
                        (
                            select epoch_ms(request_time_ms) as request_time, date_trunc('day', request_time) as request_date, *
                            from queries
                        )
                        """
                ).fetchall()
                for date in res:
                    print(date[0].strftime("%y-%m-%d"))
            case ["query", "trips", "day", day]:
                print(day)
                query_date = con.execute(
                    f"""
                    select epoch_ms(request_time_ms) as request_time, tripid
                    from queries
                    where request_time between '{day} 00:00' and '{day} 23:59:59' order by request_time asc;
                """
                ).fetchall()
                print(query_date)


if __name__ == "__main__":
    asyncio.run(main())
