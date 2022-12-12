from concurrent.futures import ThreadPoolExecutor
import sqlite3
import pandas as pd
import json
import duckdb
from multiprocessing import cpu_count

print(f"{cpu_count()} cores detected")

con = sqlite3.connect("../bus_data.db", check_same_thread=False)
cur = con.cursor()

query = cur.execute("select count(*) from queries")
queries_len = query.fetchall()[0][0]
print(f"{queries_len} queries in database")

def get_data_frame(db_con, limit, offset, i):
    print(f"Calling {offset}")

    cur = db_con.cursor()
    query = cur.execute(f"select * from queries limit {limit} offset {offset}")
    res = query.fetchall()

    print(f"Fetched data in thread {i}")

    data_frame_keys = ["request_time_ms", "vid", "tmstmp", "lat", "lon", "hdg", "pid", "rt", "des", "pdist", "dly", "spd", "tatripid", "origtatripno", "tablockid", "psgld", "oid", "or", "rid", "blk", "tripid", "stst"]

    result_dict = {i: [] for i in data_frame_keys}
    for row in res:
        data = json.loads(row[1])
        for bus in data:
            for key in data_frame_keys:
                if key in bus:
                    result_dict[key].append(bus[key])
            result_dict['request_time_ms'].append(row[0])

    print(f"Created dictionary {i}")
    df = pd.DataFrame.from_dict(result_dict)
    print(f"Created data frame {i}")
    return df

with ThreadPoolExecutor() as executor:
    futures = []
    results = []

    limit = queries_len // cpu_count()
    for i in range(cpu_count()):
        offset = limit * i
        if i == cpu_count() - 1:
            limit = -1

        print("Submitting", limit, offset)
        futures.append(executor.submit(get_data_frame, con, limit, offset, i))

    for future in futures:
        results.append(future.result())

    duck_con = duckdb.connect(database='duck_data.duckdb', read_only=False)
    for result in results:
        duck_con.register('queries_view', result)
        duck_con.execute('insert into queries (select * from queries_view)');
        duck_con.unregister('queries_view')

