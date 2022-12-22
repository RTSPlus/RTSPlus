from typing import Dict, List
import aiohttp
import asyncio
from vincenty import vincenty

from bus_api import API_Call, async_api_call

from data_model import PathPoint, PathStopPoint, Route, RoutePath

async def build_routes(proj_dist_scaling_factor=1):
    async def add_rt_to_await(rt, method):
        return rt, await method

    async with aiohttp.ClientSession() as session:
        route_pattern_futures = []

        # Get routes
        routes = (await async_api_call(session, call_type=API_Call.GET_ROUTES))['bustime-response']['routes']
        
        # Get route patterns
        for route in routes:
            route_pattern_futures.append(
                asyncio.ensure_future(
                    add_rt_to_await(
                        route,
                        async_api_call(
                            session, 
                            call_type=API_Call.GET_ROUTE_PATTERNS, 
                            params={'rt': route['rt'], 'rtpidatafeed': 'bustime'}
                        )
                    )
                )
            )

        pattern_responses = await asyncio.gather(*route_pattern_futures)
        
        # Get route paths
        built_routes: Dict[int, Route] = {}
        for rt, pattern in pattern_responses:
            built_paths = {}
            for ptr in pattern['bustime-response']['ptr']:
                # build path
                paths: List[List[PathPoint]] = [[], []]
                for path, pts in zip(paths, [ptr['pt'], ptr.get('dtrpt', [])]):
                    # Sort so we can ensure accuracy with projected distance
                    pts.sort(key=lambda x: x['seq'])

                    for i, pt in enumerate(pts):
                        # Skip duplicate points and prefer stop points over regular points
                        # De-dupe points within 1 meter
                        if path and vincenty((pt['lat'], pt['lon']), (path[-1].lat, path[-1].lon)) <= 1.0/1000:
                            if pt['typ'] == 'S':
                                path.pop()
                            else:
                                continue

                        # Find distance difference between current and last point
                        # Only count waypoints for distance
                        if path and pt['typ'] == "W":
                            dist_diff = vincenty((pt['lat'], pt['lon']), (path[-1].lat, path[-1].lon))
                            proj_dist = path[-1].projected_dist + (dist_diff * proj_dist_scaling_factor)

                            path.append(PathPoint(pt['seq'], pt['lat'], pt['lon'], projected_dist=proj_dist))
                        elif pt['typ'] == "S":
                            # Snap projected distance to closest stop point (only check last and next point)
                            last_point = path[-1] if path else None
                            next_point = pts[i + 1] if i + 1 < len(pts) else None

                            # This logic assumes that there will no two stop points in a row
                            if last_point:
                                assert last_point.type == 'W'
                            if next_point:
                                assert next_point['typ'] == 'W'

                            last_distance = last_point.projected_dist if last_point else float('inf')

                            # Next point is 0 if there is no last_point
                            # Next point is inf if there is no next_point
                            # Next point is the distance to the next point if there is a last_point and a next_point
                            next_distance = float('inf')
                            if next_point:
                                if last_point:
                                    next_distance = path[-1].projected_dist + vincenty((last_point.lat, last_point.lon), (next_point['lat'], next_point['lon'])) * proj_dist_scaling_factor
                                else:
                                    next_distance = 0
                            
                            proj_dist = min(last_distance, next_distance)

                            path.append(PathStopPoint(
                                seq=pt['seq'],
                                lat=pt['lat'],
                                lon=pt['lon'],

                                name=pt['stpnm'],
                                id=pt['stpid'],
                                dist=pt['pdist'],
                                projected_dist=proj_dist
                            ))
                            
                path, dtrpath = paths
                route_path = RoutePath(
                    id=ptr['pid'],
                    length=ptr['ln'], 
                    direction=ptr['rtdir'],
                    path=path,
                    dtrid=ptr.get('dtrid', None),
                    dtrpt=dtrpath
                )

                built_paths[route_path.id] = route_path
                
            built_routes[int(rt['rt'])] = Route(int(rt['rt']), rt['rtnm'], rt['rtclr'], built_paths)

        return built_routes
