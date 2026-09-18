import pandas as pd
from backend.app.db import conn


df = pd.read_csv("data/road_segment_dataset.csv")


cursor = conn.cursor()


for _, row in df.iterrows():

    lanes = None if row["lanes"] == "unknown" else int(row["lanes"])

    maxspeed = None if row["maxspeed"] == "unknown" else int(row["maxspeed"])

    cursor.execute("""
        INSERT INTO road_segments (
            location,
            latitude,
            longitude,
            road_length,
            road_highway,
            lanes,
            maxspeed,
            oneway,
            u,
            v,
            key
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        row["location"],
        row["latitude"],
        row["longitude"],
        row["road_length"],
        row["road_highway"],
        lanes,
        maxspeed,
        row["oneway"],
        row["u"],
        row["v"],
        row["key"]
    ))


conn.commit()

cursor.close()

print(f"{len(df)} road segments inserted successfully!")