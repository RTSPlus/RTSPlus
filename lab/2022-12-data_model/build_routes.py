from typing import Dict, List
import aiohttp
import asyncio

from bus_api import API_Call, async_api_call

from data_model import PathPoint, PathStopPoint, Route, RoutePath

async def build_routes():
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
                    pts.sort(key=lambda x: x['seq'])
                    for pt in pts:
                        # Skip duplicate points and prefer stop points over regular points
                        if path and (path[-1].lat == pt['lat'] and path[-1].lon == pt['lon']):
                            if pt['typ'] == 'S':
                                path.pop()
                            else:
                                continue

                        if pt['typ'] == 'S':
                            path.append(PathStopPoint(
                                lat=pt['lat'],
                                lon=pt['lon'],

                                name=pt['stpnm'],
                                id=pt['stpid'],
                                dist=pt['pdist']
                            ))
                        else:
                            path.append(PathPoint(pt['lat'], pt['lon']))

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
