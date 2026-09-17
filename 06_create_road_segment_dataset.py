import osmnx as ox
import pandas as pd

print("Loading Bengaluru road network...")

# Load road network
G = ox.load_graphml("data/bengaluru_road_network.graphml")

print("Road network loaded!")
print("Nodes:", len(G.nodes))
print("Edges:", len(G.edges))

# Load hotspot data
hotspots = pd.read_csv("data/bangalore_accident_data.csv")

hotspots["latitude"] = pd.to_numeric(hotspots["latitude"])
hotspots["longitude"] = pd.to_numeric(hotspots["longitude"])

print("Hotspots loaded:", len(hotspots))

# Find nearest road edges
print("Finding nearest road segments...")

nearest_edges = ox.distance.nearest_edges(
    G,
    X=hotspots["longitude"].values,
    Y=hotspots["latitude"].values
)

# Store edge information
hotspots["u"] = [edge[0] for edge in nearest_edges]
hotspots["v"] = [edge[1] for edge in nearest_edges]
hotspots["key"] = [edge[2] for edge in nearest_edges]

print("Road segments identified!")

# Extract useful road information
road_features = []

for _, row in hotspots.iterrows():

    u = row["u"]
    v = row["v"]
    key = row["key"]

    edge_data = G[u][v][key]

    road_features.append({
        "location": row["location"],
        "latitude": row["latitude"],
        "longitude": row["longitude"],
        "incidents": row["incidents"],
        "severity": row["severity"],
        "accident_type": row["accident_type"],
        "peak_hours": row["peak_hours"],
        "road_condition": row["road_condition"],
        "weather_factor": row["weather_factor"],
        "road_length": edge_data.get("length", 0),
        "road_highway": edge_data.get("highway", "unknown"),
        "lanes": edge_data.get("lanes", "unknown"),
        "maxspeed": edge_data.get("maxspeed", "unknown"),
        "oneway": edge_data.get("oneway", False),
        "u": u,
        "v": v,
        "key": key
    })

# Create DataFrame
road_segments = pd.DataFrame(road_features)

# Save dataset
road_segments.to_csv(
    "data/road_segment_dataset.csv",
    index=False
)

print("\nRoad segment dataset created!")
print("Rows:", len(road_segments))
print("Columns:", len(road_segments.columns))

print("\nSample:")
print(road_segments.head())

print("\nSaved to:")
print("data/road_segment_dataset.csv")