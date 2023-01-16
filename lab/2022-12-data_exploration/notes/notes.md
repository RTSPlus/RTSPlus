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
      - length in feet
    - dtrid = detour route id?
    - inbound/outbound + coordinates
      - pt/dtrpt: array of points
        - pt = normal points, dtrpt = detour points
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

- vid = vehicle id
- tmstmp = timestamp
  - useless tbh. only has minute level precision
- lat = latitude
- lon = longitude
- hdg = heading ?
  - seems to return values 0-360
- pid = pattern id
  - pattern = "route"
  - read with getpatterns
  - has stops/inbound/outbound
- rt = route number
- des = destination
- pdist
  - parametric distance from the start of the route?
  - idk units
    - pretty sure meters upon further investigation?
- dly = delay?
- spd = speed?
  - unused
- tatripid = ?
  - trip designator?
- origtatripno = ?
  - unused
  - idk the difference between this and tripid
  - unique on every trip
- tablockid = ?
  - unused
- zone = ?
- mode = ?
- psgld = ?
- srvtmstmp = timestamp
  - unused
- idk why this is different from tmstmp
- oid = ?
- unused
- or = ?
- rid = ?
  - unused
  - some values of rid are "MAN" for some reason?
- blk = ?
  - unused
- tripid
  - can make a request to query tripid
    - (future noah) what did i mean by this ???
  - (wrong) unique on every trip
  - TRIP ID IS NOT UNIQUE
- tripdyn = ?
  - unused
- stst = ?
  - unused
  - unique on every trip
- stds = date
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

# SQL Commands

```sql
-- Get the dates of all the queries
select distinct date_formatted from
  (select left(epoch_ms(request_time_ms), 11) as date_formatted from queries);

-- count of queries per day
select count(*) from
  (select left(epoch_ms(request_time_ms), 11) as date_formatted, * from queries)
group by date_formatted
limit 10;

-- Select number of routes per day and list day of the week
select count(distinct rt) as rt_count, date_formatted, strftime(date_formatted::DATE, '%a')
from
  (select left(epoch_ms(request_time_ms), 11) as date_formatted, * from queries)
group by date_formatted
order by rt_count;

-- Show routes serviced per weekday
select distinct rt as rts, date_formatted, strftime(date_formatted::DATE, '%a')  from (select left(epoch_ms(request_time_ms), 11) as date_formatted, * from queries) group by date_formatted, rts order by date_formatted, rts;

-- show # of trips for each routes on a specific day
select count(*), rt from
(
  select distinct tripid, rt from
    (
      select epoch_ms(request_time_ms) as request_time, tripid, *
      from queries
      where request_time between '2022-12-05 00:00' and '2022-12-05 23:59:59'
      order by request_time asc
    )
  order by rt
)
group by rt;

-- select a random tripid and rt on a specific day
select distinct tripid, rt from
  (
    select epoch_ms(request_time_ms) as request_time, tripid, *
    from queries
    where request_time between '2022-12-05 00:00' and '2022-12-05 23:59:59'
    order by request_time asc
  )
using sample 1;
```

# Remote scraper commands

run python in background and log to file

```bash
nohup python3 -u scrape.py > scrape.log &
```

```bash
ps -aux | grep python
```
