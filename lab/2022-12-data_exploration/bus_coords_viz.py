import duckdb
import pandas as pd
import plotly.express as px

vid = 708;

con = duckdb.connect(database='../duck_data.duckdb', read_only=True)

df = con.query('''
    select request_time_ms, lat, lon, lag(request_time_ms) over () as request_time_ms_prev, (request_time_ms - request_time_ms_prev) / 1000.0 as time_diff
    from (
        select request_time_ms, lat, lon, lag(lat,1,0) over () as lat_prev, lag(lon,1,0) over () as lon_prev, lat - lat_prev as lat_diff, lon - lon_prev as lon_diff
        from queries
        where vid = 708
    )
    where lat_diff != 0 and lon_diff != 0
    limit 100 offset 30
''').to_df()
print(df)
print("\nTime diff:")
print("mean:\t", df['time_diff'].mean())
print("median:\t", df['time_diff'].median())
print("std:\t", df['time_diff'].std())

df["request_time_ms"] -= df["request_time_ms_prev"].loc[0]
df["request_time_ms"] /= 1000.0

fig = px.scatter_mapbox(df, lat="lat", lon="lon", color_discrete_sequence=["fuchsia"], zoom=14, color="request_time_ms")
fig.update_layout(mapbox_style="carto-positron")
fig.show()