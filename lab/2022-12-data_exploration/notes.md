bus payload:

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

# Bus coordinate bounds
select max(lat), min(lat), max(lon), min(lon) from (select lat,lon from queries where lat != 0 and lon != 0);

lat/lon returns 0 in some cases

max lat: 29.715414315424184
min lat: 29.5993112045104
max lon: -82.26359958976886
min lon: -82.4392548