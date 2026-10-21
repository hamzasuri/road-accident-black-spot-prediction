import os
import osmnx as ox
import psycopg2
from dotenv import load_dotenv

load_dotenv()

GRAPH_PATH = "data/bengaluru_road_network.graphml"
DATABASE_URL = os.getenv("DATABASE_URL")

print("Loading GraphML...")
G = ox.load_graphml(GRAPH_PATH)

print("Connecting to database...")
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

cursor.execute("""
    SELECT u, v, key
    FROM road_segments
    LIMIT 5
""")

db_rows = cursor.fetchall()

print("\n========== CHECK ==========")

for u, v, key in db_rows:

    print(f"\nDatabase: {u}, {v}, {key}")

    found = False

    for graph_u, graph_v, graph_key in G.edges(keys=True):

        if (
            int(graph_u) == int(u)
            and int(graph_v) == int(v)
            and int(graph_key) == int(key)
        ):
            found = True
            break

    print("Found in GraphML:", found)

print("\n===========================")

cursor.close()
conn.close()