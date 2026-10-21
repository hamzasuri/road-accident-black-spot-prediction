import osmnx as ox
import pandas as pd

GRAPH_PATH = "data/bengaluru_road_network.graphml"
PREDICTIONS_PATH = "data/road_risk_predictions.csv"

print("Loading road network...")
G = ox.load_graphml(GRAPH_PATH)

print("Loading predictions...")
predictions = pd.read_csv(PREDICTIONS_PATH)

# Convert prediction identifiers to strings
predictions["u"] = predictions["u"].astype(str)
predictions["v"] = predictions["v"].astype(str)
predictions["key"] = predictions["key"].astype(str)

# Extract OSM edges
edges = ox.graph_to_gdfs(
    G,
    nodes=False,
    edges=True
).reset_index()

# Convert identifiers to strings
edges["u"] = edges["u"].astype(str)
edges["v"] = edges["v"].astype(str)
edges["key"] = edges["key"].astype(str)

print("\n========== RESULTS ==========")

print("Prediction roads:", len(predictions))
print("OSM edges:", len(edges))

# Match using the exact same identifiers
matched = predictions.merge(
    edges[["u", "v", "key", "geometry"]],
    on=["u", "v", "key"],
    how="inner"
)

print("Matched roads:", len(matched))
print("Unmatched roads:", len(predictions) - len(matched))

print(
    "Match percentage:",
    round(len(matched) / len(predictions) * 100, 2),
    "%"
)

print("=============================")

if len(matched) == len(predictions):
    print("SUCCESS: Every predicted road has geometry.")
elif len(matched) > 0:
    print("PARTIAL MATCH: Some predicted roads have geometry.")
else:
    print("NO MATCH: Something is wrong with the identifiers.")