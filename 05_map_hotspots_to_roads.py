import osmnx as ox
import pandas as pd

print("Loading Bengaluru road network...")

# Load road network
G = ox.load_graphml("data/bengaluru_road_network.graphml")

print("Road network loaded!")
print("Nodes:", len(G.nodes))
print("Edges:", len(G.edges))

# Load hotspot dataset
hotspots = pd.read_csv("data/bangalore_accident_data.csv")

print("Hotspots loaded:", len(hotspots))

# Make sure coordinates are numeric
hotspots["latitude"] = pd.to_numeric(hotspots["latitude"])
hotspots["longitude"] = pd.to_numeric(hotspots["longitude"])

# Find nearest road node for each hotspot
print("Finding nearest roads...")

nearest_nodes = ox.distance.nearest_nodes(
    G,
    X=hotspots["longitude"].values,
    Y=hotspots["latitude"].values
)

hotspots["nearest_node"] = nearest_nodes

# Save result
hotspots.to_csv(
    "data/hotspots_mapped_to_roads.csv",
    index=False
)

print("Hotspots successfully mapped!")
print("Saved to: data/hotspots_mapped_to_roads.csv")

print("\nSample results:")
print(
    hotspots[
        ["location", "latitude", "longitude", "incidents", "severity", "nearest_node"]
    ].head(10)
)

