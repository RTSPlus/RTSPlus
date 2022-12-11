import sqlite3
import json
import csv

EXPORT_VID = "1103"

con = sqlite3.connect("bus_data.db")
cur = con.cursor()
cur.execute("SELECT * FROM queries")
res = cur.fetchone()

vid_map = {}  # vid: { rt: int, path: [(time, lat, lng)] }
# for row in cur.fetchall():
for row in cur.fetchall():
    data = json.loads(row[1])
    for vehicle in data:
        vid = vehicle["vid"]
        if vid not in vid_map:
            vid_map[vid] = {
                "rt": vehicle["rt"],
                "path": [],
            }
        vid_map[vid]["path"].append((row[0], vehicle["lat"], vehicle["lon"]))

with open(f"bus_data_{EXPORT_VID}.csv", "w") as f:
    writer = csv.writer(f)
    writer.writerow(["time", "lat", "lng"])
    for time, lat, lng in vid_map[EXPORT_VID]["path"]:
        writer.writerow([time, lat, lng])

import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("bus_data_1103.csv")
plt.scatter(x=df["lng"], y=df["lat"])
plt.show()
