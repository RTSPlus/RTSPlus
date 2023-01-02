import asyncio
import datetime
import pickle
from typing import Dict, List

from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import NestedCompleter

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import duckdb


from build_routes import build_routes
from data_model import Route, RoutePath, project_pdist_path
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
            marker={"size": 4},
        )
    )

    fig.add_trace(
        go.Scattermapbox(
            mode="markers+text",
            lat=stops_df["lat"],
            lon=stops_df["lon"],
            text=stops_df["combined_text"],
            marker={"size": 10, "color": "green"},
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

    return fig


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
                    "day": {
                        **{
                            date[0].strftime("%Y-%m-%d"): {"trip": {"random": None}}
                            for date in query_days
                        },
                        "random": {"trip": {"random": None}},
                    }
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
                graph_path(routes[rt].path[int(path_num)]).show()
            case ["query", "days"]:
                query_days: List[datetime.date] = con.execute(
                    f"""
                        select distinct request_date from
                        (
                            select epoch_ms(request_time_ms) as request_time, date_trunc('day', request_time) as request_date, *
                            from queries
                        )
                        """
                ).fetchall()
                for date in query_days:
                    print(date[0].strftime("%y-%m-%d"))
            case ["query", "trips", "day", day]:
                if day == "random":
                    query_days: List[datetime.date] = con.execute(
                        f"""
                            select distinct request_date from
                            (
                                select epoch_ms(request_time_ms) as request_time, date_trunc('day', request_time) as request_date, *
                                from queries
                            ) using sample 1;
                            """
                    ).fetchone()
                    day = query_days[0].strftime("%Y-%m-%d")
                query_date = con.execute(
                    f"""
                    select count(distinct tripid) from (
                        select epoch_ms(request_time_ms) as request_time, tripid
                        from queries
                        where request_time between '{day} 00:00' and '{day} 23:59:59'
                        order by request_time asc
                    );
                    """
                ).fetchone()
                print(f"{query_date[0]} trips on {day}")
            case ["query", "trips", "day", day, "trip", specific_id]:
                if day == "random":
                    query_days: List[datetime.date] = con.execute(
                        f"""
                            select distinct request_date from
                            (
                                select epoch_ms(request_time_ms) as request_time, date_trunc('day', request_time) as request_date, *
                                from queries
                            ) using sample 1;
                            """
                    ).fetchone()
                    day = query_days[0].strftime("%Y-%m-%d")

                tripid = None
                if specific_id == "random":
                    query_random = con.execute(
                        f"""
                        select distinct tripid, rt, pid from 
                        (
                            select epoch_ms(request_time_ms) as request_time, tripid, *
                            from queries
                            where request_time between '{day} 00:00' and '{day} 23:59:59'
                            order by request_time asc
                        )
                        using sample 1;
                        """
                    ).fetchone()
                    tripid, rt, pid = query_random
                else:
                    # todo, implement getting rt and pid from tripid lol
                    tripid = specific_id

                query_trip_df = con.execute(
                    f"""
                    select * from (
                        select epoch_ms(request_time_ms) as request_time, lat, lat - lag(lat, 1, 0) over () as lat_diff, *
                        from queries
                        where request_time between '{day} 00:00' and '{day} 23:59:59'
                        and tripid = '{tripid}'
                        order by request_time asc
                    ) where lat_diff != 0 and lat != 0;
                    """
                ).df()

                print(f"Route {rt} - {pid}")
                print(f"Trip {tripid}")

                path = routes[int(rt)].path[int(pid)]

                fig = graph_path(path)
                query_scatter = px.scatter_mapbox(
                    query_trip_df,
                    lat="lat",
                    lon="lon",
                    color="pdist",
                    color_continuous_scale=px.colors.sequential.dense,
                    zoom=13,
                ).data[0]

                fig.add_trace(query_scatter)

                fig.show()
            case ["test", "get", "pdist", path_num]:
                rt = path_map[int(path_num)]
                path = routes[rt].path[int(path_num)]
                print(
                    path.path[-1].projected_dist,
                    km2ft(path.path[-1].projected_dist),
                    path.reported_length,
                )
            case ["test", "pdist", path_num, pdist]:
                rt = path_map[int(path_num)]
                path = routes[rt].path[int(path_num)].path
                print(project_pdist_path(path, float(pdist)))


if __name__ == "__main__":
    asyncio.run(main())
