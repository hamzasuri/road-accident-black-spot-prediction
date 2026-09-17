import osmnx as ox
import pandas as pd
import numpy as np

print("Loading Bengaluru road network...")

# Load OSM road network
G = ox.load_graphml("data/bengaluru_road_network.graphml")

print("Road network loaded!")
print("Nodes:", len(G.nodes))
print("Edges:", len(G.edges))


# --------------------------------------------------
# 1. LOAD HISTORICAL ACCIDENT DATA
# --------------------------------------------------

print("\nLoading historical accident data...")

df = pd.read_csv("data/indian_roads_dataset.csv")

print("Total accident records:", len(df))

# Remove the original risk score
if "risk_score" in df.columns:
    df = df.drop(columns=["risk_score"])

print("Original risk_score removed.")


# --------------------------------------------------
# 2. SELECT BENGALURU ACCIDENTS
# --------------------------------------------------

bangalore = df[
    df["city"].astype(str).str.lower() == "bangalore"
].copy()

print("Bengaluru accident records:", len(bangalore))


# --------------------------------------------------
# 3. CLEAN COORDINATES
# --------------------------------------------------

bangalore["latitude"] = pd.to_numeric(
    bangalore["latitude"],
    errors="coerce"
)

bangalore["longitude"] = pd.to_numeric(
    bangalore["longitude"],
    errors="coerce"
)

bangalore = bangalore.dropna(
    subset=["latitude", "longitude"]
)

print("Valid coordinate records:", len(bangalore))


# --------------------------------------------------
# 4. MAP ACCIDENTS TO ROAD SEGMENTS
# --------------------------------------------------

print("\nMapping accidents to road segments...")

nearest_edges = ox.distance.nearest_edges(
    G,
    X=bangalore["longitude"].values,
    Y=bangalore["latitude"].values
)

bangalore["u"] = [x[0] for x in nearest_edges]
bangalore["v"] = [x[1] for x in nearest_edges]
bangalore["key"] = [x[2] for x in nearest_edges]

print("Accidents mapped to road segments.")


# --------------------------------------------------
# 5. CREATE HISTORICAL RISK INFORMATION
# --------------------------------------------------

print("\nCalculating historical accident risk...")


# Severity weights
severity_weights = {
    "minor": 1,
    "major": 3,
    "fatal": 5
}

bangalore["severity_weight"] = (
    bangalore["accident_severity"]
    .astype(str)
    .str.lower()
    .map(severity_weights)
    .fillna(1)
)


# Aggregate accidents by road segment
segment_accidents = (
    bangalore
    .groupby(["u", "v", "key"])
    .agg(
        accident_count=("accident_id", "count"),
        severity_score=("severity_weight", "sum"),
        total_casualties=("casualties", "sum")
    )
    .reset_index()
)


print(
    "Road segments containing accidents:",
    len(segment_accidents)
)


# --------------------------------------------------
# 6. CREATE OUR OWN RISK SCORE
# --------------------------------------------------

# Normalize each historical component
def min_max(series):

    minimum = series.min()
    maximum = series.max()

    if maximum == minimum:
        return pd.Series(0, index=series.index)

    return (series - minimum) / (maximum - minimum)


segment_accidents["frequency_norm"] = min_max(
    segment_accidents["accident_count"]
)

segment_accidents["severity_norm"] = min_max(
    segment_accidents["severity_score"]
)

segment_accidents["casualty_norm"] = min_max(
    segment_accidents["total_casualties"]
)


# Our project-defined historical risk score
segment_accidents["risk_score"] = (
    0.40 * segment_accidents["frequency_norm"]
    + 0.40 * segment_accidents["severity_norm"]
    + 0.20 * segment_accidents["casualty_norm"]
) * 100


# --------------------------------------------------
# 7. CREATE RISK CLASSES
# --------------------------------------------------

def classify_risk(score):

    if score <= 25:
        return "Low"

    elif score <= 50:
        return "Medium"

    elif score <= 75:
        return "High"

    else:
        return "Critical"


segment_accidents["risk_level"] = (
    segment_accidents["risk_score"]
    .apply(classify_risk)
)


# --------------------------------------------------
# 8. ADD ROAD NETWORK FEATURES
# --------------------------------------------------

print("\nAdding road features...")

road_data = []

for _, row in segment_accidents.iterrows():

    u = row["u"]
    v = row["v"]
    key = row["key"]

    edge = G[u][v][key]

    highway = edge.get("highway", "unknown")
    lanes = edge.get("lanes", np.nan)
    maxspeed = edge.get("maxspeed", np.nan)

    # OSM can sometimes store these as lists
    if isinstance(highway, list):
        highway = highway[0]

    if isinstance(lanes, list):
        lanes = lanes[0]

    if isinstance(maxspeed, list):
        maxspeed = maxspeed[0]

    road_data.append({
        "u": u,
        "v": v,
        "key": key,
        "road_length": edge.get("length", 0),
        "highway": highway,
        "lanes": lanes,
        "maxspeed": maxspeed,
        "oneway": edge.get("oneway", False)
    })


road_features = pd.DataFrame(road_data)


# --------------------------------------------------
# 9. COMBINE EVERYTHING
# --------------------------------------------------

ml_data = segment_accidents.merge(
    road_features,
    on=["u", "v", "key"],
    how="left"
)


# --------------------------------------------------
# 10. SAVE
# --------------------------------------------------

ml_data.to_csv(
    "data/ml_training_dataset.csv",
    index=False
)

print("\n===================================")
print("ML TRAINING DATASET CREATED!")
print("===================================")

print("Rows:", len(ml_data))
print("Columns:", len(ml_data.columns))

print("\nRisk levels:")
print(ml_data["risk_level"].value_counts())

print("\nSample:")
print(
    ml_data[
        [
            "u",
            "v",
            "accident_count",
            "severity_score",
            "total_casualties",
            "risk_score",
            "risk_level",
            "road_length",
            "highway",
            "lanes",
            "maxspeed"
        ]
    ].head(10)
)

print("\nSaved to:")
print("data/ml_training_dataset.csv")