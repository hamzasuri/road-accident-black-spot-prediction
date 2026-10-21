import os
import osmnx as ox
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
GRAPH_PATH = "data/bengaluru_road_network.graphml"

print("Loading road network...")
G = ox.load_graphml(GRAPH_PATH)

print("Extracting geometries...")
edges = ox.graph_to_gdfs(
    G,
    nodes=False,
    edges=True
).reset_index()

# Build a lookup:
# (u, v, key) -> geometry WKT
geometry_lookup = {}

for _, row in edges.iterrows():

    geometry = row["geometry"]

    if geometry is not None:
        geometry_lookup[
            (
                int(row["u"]),
                int(row["v"]),
                int(row["key"])
            )
        ] = geometry.wkt

print("Geometries available:", len(geometry_lookup))

print("Connecting to PostgreSQL...")
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

# Get the roads we actually need
cursor.execute("""
    SELECT id, u, v, key
    FROM road_segments
    ORDER BY id;
""")

roads = cursor.fetchall()

print("Database roads:", len(roads))

updated = 0
missing = 0

print("Updating geometries...")

for road_id, u, v, key in roads:

    lookup_key = (int(u), int(v), int(key))

    geometry_wkt = geometry_lookup.get(lookup_key)

    if geometry_wkt is None:
        missing += 1
        continue

    cursor.execute(
        """
        UPDATE road_segments
        SET geometry = ST_GeomFromText(%s, 4326)
        WHERE id = %s;
        """,
        (geometry_wkt, road_id)
    )

    updated += cursor.rowcount

    if updated % 100 == 0:
        print(f"Updated: {updated}")

conn.commit()

cursor.close()
conn.close()

print("\n========== COMPLETE ==========")
print("Database roads:", len(roads))
print("Geometries updated:", updated)
print("Missing geometries:", missing)
print("==============================")