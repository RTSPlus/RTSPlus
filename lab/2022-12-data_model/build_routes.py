from typing import Dict, List, Tuple
import asyncio
import pickle
import os

import aiohttp
from urllib.parse import urlencode
from vincenty import vincenty
from dotenv import load_dotenv

from bus_api import API_Call, async_api_call
from data_model import PathPoint, PathStopPoint, Route, RoutePath
from util import chunks

load_dotenv()


async def build_routes(proj_dist_scaling_factor=1):
    async def add_rt_to_await(rt, method):
        return rt, await method

    async with aiohttp.ClientSession() as session:
        route_pattern_futures = []

        # Get routes
        routes = (await async_api_call(session, call_type=API_Call.GET_ROUTES))[
            "bustime-response"
        ]["routes"]

        # Get route patterns
        for route in routes:
            route_pattern_futures.append(
                asyncio.ensure_future(
                    add_rt_to_await(
                        route,
                        async_api_call(
                            session,
                            call_type=API_Call.GET_ROUTE_PATTERNS,
                            params={"rt": route["rt"], "rtpidatafeed": "bustime"},
                        ),
                    )
                )
            )

        pattern_responses = await asyncio.gather(*route_pattern_futures)

        # Get route paths
        built_routes: Dict[int, Route] = {}
        for rt, pattern in pattern_responses:
            built_paths = {}
            for ptr in pattern["bustime-response"]["ptr"]:
                # build path
                paths: List[List[PathPoint]] = [[], []]
                for path, pts in zip(paths, [ptr["pt"], ptr.get("dtrpt", [])]):
                    # Sort so we can ensure accuracy with projected distance
                    pts.sort(key=lambda x: x["seq"])

                    for i, pt in enumerate(pts):
                        # Skip duplicate points and prefer stop points over regular points
                        # De-dupe points within 1 meter
                        if (
                            path
                            and vincenty(
                                (pt["lat"], pt["lon"]), (path[-1].lat, path[-1].lon)
                            )
                            <= 1.0 / 1000
                        ):
                            if pt["typ"] == "S":
                                path.pop()
                            else:
                                continue

                        # Find distance difference between current and last point
                        # Only count waypoints for distance
                        if path and pt["typ"] == "W":
                            dist_diff = vincenty(
                                (pt["lat"], pt["lon"]), (path[-1].lat, path[-1].lon)
                            )
                            proj_dist = path[-1].projected_dist + (
                                dist_diff * proj_dist_scaling_factor
                            )

                            path.append(
                                PathPoint(
                                    pt["lat"],
                                    pt["lon"],
                                    projected_dist=proj_dist,
                                )
                            )
                        elif pt["typ"] == "S":
                            # Snap projected distance to closest stop point (only check last and next point)
                            last_point = path[-1] if path else None
                            next_point = pts[i + 1] if i + 1 < len(pts) else None

                            # This logic assumes that there will no two stop points in a row
                            if last_point:
                                assert last_point.type == "W"
                            if next_point:
                                assert next_point["typ"] == "W"

                            last_distance = (
                                last_point.projected_dist
                                if last_point
                                else float("inf")
                            )

                            # Next point is 0 if there is no last_point
                            # Next point is inf if there is no next_point
                            # Next point is the distance to the next point if there is a last_point and a next_point
                            next_distance = float("inf")
                            if next_point:
                                if last_point:
                                    next_distance = (
                                        path[-1].projected_dist
                                        + vincenty(
                                            (last_point.lat, last_point.lon),
                                            (next_point["lat"], next_point["lon"]),
                                        )
                                        * proj_dist_scaling_factor
                                    )
                                else:
                                    next_distance = 0

                            proj_dist = min(last_distance, next_distance)

                            path.append(
                                PathStopPoint(
                                    lat=pt["lat"],
                                    lon=pt["lon"],
                                    name=pt["stpnm"],
                                    id=pt["stpid"],
                                    reported_dist=pt["pdist"],
                                    projected_dist=proj_dist,
                                )
                            )

                path, dtrpath = paths
                snap_path = await snap_path_google_api(
                    path, os.environ.get("GOOGLE_API_KEY"), proj_dist_scaling_factor
                )

                route_path = RoutePath(
                    id=ptr["pid"],
                    reported_length=ptr["ln"],
                    direction=ptr["rtdir"],
                    path=snap_path,
                    path_orig=path,
                    dtrid=ptr.get("dtrid", None),
                    dtrpt=dtrpath,
                )

                built_paths[route_path.id] = route_path

            built_routes[int(rt["rt"])] = Route(
                int(rt["rt"]), rt["rtnm"], rt["rtclr"], built_paths
            )

        return built_routes


async def async_google_snap_to_road_paginated(
    path: List[Tuple[float, float]],
    google_api_key: str,
    pagination_limit=100,
    pagination_overlap=5,
):
    # Google Roads API only allows 100 points per request
    # This function will split a request into multiple requests if necessary
    async def google_snap_to_road_api_call(api_path, session, google_api_key):
        base_url = "https://roads.googleapis.com/v1/snapToRoads?"
        query_params = {
            "path": api_path,
            "interpolate": "true",
            "key": google_api_key,
        }
        url = f"{base_url}{urlencode(query_params)}"

        async with session.get(url) as response:
            return await response.json()

    async with aiohttp.ClientSession() as session:
        request_futures = []
        chunked = list(chunks(path, pagination_limit, pagination_overlap))
        for chunk in chunked:
            request_futures.append(
                asyncio.ensure_future(
                    google_snap_to_road_api_call(
                        "|".join(f"{c[0]},{c[1]}" for c in chunk),
                        session,
                        google_api_key,
                    )
                )
            )

        responses = await asyncio.gather(*request_futures)

        last_point = 0
        points_non_overlapping = []
        for i, response, chunk_len in zip(
            range(len(responses)), responses, (len(chunk) for chunk in chunked)
        ):
            if i == 0:
                points_non_overlapping.extend(response["snappedPoints"])
                last_point = chunk_len - 1
                continue

            reading = False
            for point in response["snappedPoints"]:
                if "originalIndex" in point:
                    orig_index = int(point["originalIndex"])
                    if orig_index >= pagination_overlap:
                        reading = True

                if reading:
                    if "originalIndex" in point:
                        last_point += 1
                        point["originalIndex"] = last_point

                    points_non_overlapping.append(point)
    return points_non_overlapping


async def snap_path_google_api(
    path: List[PathPoint], google_api_key: str, proj_dist_scaling_factor=1.0
):
    # new_route_coords = await async_google_snap_to_road_paginated(
    #     [[pt.lat, pt.lon] for pt in path if pt.type == "W"],
    #     google_api_key,
    # )

    # # pickle.dump(new_route_coords, open("new_route_coords.p", "wb"))

    new_route_coords = pickle.load(open("new_route_coords.p", "rb"))
    new_path: List[PathPoint] = []

    old_path_index = 0
    for point in new_route_coords:
        lat = float(point["location"]["latitude"])
        lon = float(point["location"]["longitude"])

        new_proj_dist = 0
        if new_path:
            new_proj_dist = (
                vincenty((lat, lon), (new_path[-1].lat, new_path[-1].lon))
                * proj_dist_scaling_factor
            )

        if "originalIndex" in point:
            while old_path_index < len(path) and path[old_path_index].type == "S":
                new_path.append(path[old_path_index])
                old_path_index += 1

            new_path.append(
                PathPoint(
                    lat,
                    lon,
                    projected_dist=new_path[-1].projected_dist + new_proj_dist,
                )
            )
            old_path_index += 1
        else:
            new_path.append(
                PathPoint(
                    lat,
                    lon,
                    projected_dist=new_path[-1].projected_dist + new_proj_dist,
                    interpolated=True,
                )
            )
    if old_path_index < len(path):
        new_path.append(path[-1])

    return new_path
