import pandas as pd
import plotly.express as px
import json

route_data_frame = {}

route_json = json.load(open('getpatterns_sample.json'))
for ptr in route_json['bustime-response']['ptr']:
    pts = {
        'typ': [],
        'lat': [],
        'lon': [],
        'pdist': [],
        'seq': [],
        'stpid': [],
        'stpnm': [],
    }

    json_pts = ptr['pt']
    for i in range(len(ptr['pt'])):
        pt = json_pts[i]
        
        if pt['typ'] == 'W':
            continue
        for key in pts.keys():
            if key in pt:
                pts[key].append(pt[key])
            else:
                pts[key].append(None)
    route_data_frame[ptr['rtdir']] = pd.DataFrame.from_dict(pts)

fig = px.scatter_mapbox(route_data_frame['INBOUND'], lat="lat", lon="lon", color="typ", zoom=13, hover_name="stpnm")
fig.update_layout(mapbox_style="carto-positron")
fig.show()