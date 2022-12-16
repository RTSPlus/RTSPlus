# api calls:

## Useful

- gettime
  - returns unix time. unsure of what specifically. i believe server time for syncing purposes
  - https://riderts.app/bustime/api/v3/gettime?requestType=gettime&unixTime=true&key=[key]&format=json&xtime=[unix_time]
- app?xtime
  - returns a bunch of initial data. see `app_response.md` for details
  - https://riderts.app/bustime/api/restricted/v2/properties/app?xtime=[unix_time]
- getservicebulletins
  - returns service bulletins
  - https://riderts.app/bustime/api/v3/getservicebulletins?requestType=getservicebulletins&destination=WEB&locale=en&key=[key]&format=json&xtime=[unix_time]
- getroutes
  - returns routes + names + colors
  - https://riderts.app/bustime/api/v3/getroutes?requestType=getroutes&locale=en&key=[key]&format=json&xtime=[unix_time]
- getpatterns
  - returns "patterns" for a route
    - pid? idk what this exactly is
    - ln = length?
    - dtrid = ?
    - inbound/outbound + coordinates
      - dtrpt: array of points
        - lat/lon
        - name
        - typ: "s" = stop?, "w" = waypoint?
          - only "s" has a name. "w" is just a coordinate
  - https://riderts.app/bustime/api/v3/getpatterns?requestType=getpatterns&rtpidatafeed=bustime&rt=[route_number]&locale=en&key=[key]&format=json&xtime=[unix_time]

## Not useful

- getlocalelist
  - just returns locale string keys
  - https://riderts.app/bustime/api/v3/getlocalelist?requestType=getlocalelist&inLocaleLanguage=true&key={key}&format=json&xtime={unix time}
- config.json main
  - see config_json_main for response
  - https://riderts.app/assets/config/config.json?v=2.3.1.2a
- config.json gainesville
  - see config_json_gainesvile for reponse
  - https://riderts.app/assets/ta/gainesville/config.json?v=2.3.1.2a
- en.json main
  - Just a bunch of strings for localization
  - https://riderts.app/assets/i18n/en.json?v=2.3.1.2a
- en.json gainesville
  - Just a bunch of strings for localization
  - https://riderts.app/assets/ta/gainesville/en.json?v=2.3.1.2a
- getrtpidatafeeds
  - doesnt seem very useful
  - https://riderts.app/bustime/api/v3/getrtpidatafeeds?requestType=getrtpidatafeeds&locale=en&key={key}&format=json&xtime={unix time}

# bus payload:

vid = vehicle id
tmstmp = timestamp

- useless tbh. only has minute level precision
  lat = latitude
  lon = longitude
  hdg = heading ?
- seems to return values 0-360
  pid = ?
  rt = route number
  des = destination
  pdist = ?
- distance to something
  dly = delay?
  spd = speed?
- unused
  tatripid = ?
- trip designator?
  origtatripno = ?
- unused
  tablockid = ?
- unused
  zone = ?
  mode = ?
  psgld = ?
  srvtmstmp = timestamp
- unused
- idk why this is different from tmstmp
  oid = ?
- unused
  or = ?
  rid = ?
- unused
- some values of rid are "MAN" for some reason?
  blk = ?
- unused
  tripid = ?
- can make a request to query tripid
  tripdyn = ?
- unused
  stst = ?
- unused
  stds = date
- unused
- superfluous

```json
{'vid': '708',
'tmstmp': '20221117 16:06',
'lat': '29.642243214970772',
'lon': '-82.33926',
'hdg': '0',
'pid': 500219,
'rt': '1',
'des': 'Rosa Parks/Downtown',
'pdist': 19699,
'dly': False,
'spd': 20,
'tatripid': '14188',
'origtatripno': '710014',
'tablockid': '10011',
'zone': '',
'mode': 0,
'psgld': 'HALF_EMPTY',
'srvtmstmp': '20221117 16:06',
'oid': '21208',
'or': False,
'rid': '82',
'blk': 2913002,
'tripid': 936020,
'tripdyn': 0,
'stst': 56760,
'stsd': '2022-11-17'}
```

# Bus coordinate bounds

select max(lat), min(lat), max(lon), min(lon) from (select lat,lon from queries where lat != 0 and lon != 0);

lat/lon returns 0 in some cases

max lon: -82.24136916824027
min lon: -82.446655
max lat: 29.715481941424365
min lat: 29.589633295601942

map.jpg bounds (square ratio):
max lon: -82.2413
min lon: -82.4467
max lat: 29.7418
min lat: 29.5633
