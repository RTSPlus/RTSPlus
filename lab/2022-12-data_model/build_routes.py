import aiohttp
import asyncio

from bus_api import API_Call, api_call, async_api_call

from data_model import Route

routes_data = api_call(call_type=API_Call.GET_ROUTES)['bustime-response']['routes']

routes = { int(r['rt']): Route(int(r['rt']), r['rtnm'], r['rtclr']) for r in routes_data }

async def main():
    async def add_rt_to_await(rt, method):
        return rt, await method

    async with aiohttp.ClientSession() as session:
        route_pattern_futures = []

        for route in routes:
            route_pattern_futures.append(
                asyncio.ensure_future(
                    add_rt_to_await(
                        route,
                        async_api_call(
                            session, 
                            call_type=API_Call.GET_ROUTE_PATTERNS, 
                            params={'rt': route, 'rtpidatafeed': 'bustime'}
                        )
                    )
                )
            )

        pattern_responses = await asyncio.gather(*route_pattern_futures)
        for rt, pattern in pattern_responses:
            print("-----")
            print("route:", rt)
            for ptr in pattern['bustime-response']['ptr']:
                print(ptr['pid'])

asyncio.run(main())
