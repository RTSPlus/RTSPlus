import pickle
import asyncio

from build_routes import build_routes


async def main():
    routes = await build_routes(proj_dist_scaling_factor=0.98)
    pickle.dump(routes, open("routes.p", "wb"))


# favorite_color = pickle.load( open( "save.p", "rb" ) )

asyncio.run(main())
