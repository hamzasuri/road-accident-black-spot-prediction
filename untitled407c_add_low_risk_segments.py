import osmnx as ox
import pandas as pd
import numpy as np

print("Loading Bengaluru road network...")

G = ox.load_graphml(
    "data/bengaluru_road_network.graphml"
)

print("Road network loaded!")
print("Total edges:", len(G.edges))

# --------------------------------------------------
# 1. LOAD OUR ACCIDENT-BASED DATASET
# --------------------------------------------------

print("\nLoading accident-based ML dataset...")

accident_segments = pd.read_csv(
    "data/ml_training_dataset_v2.csv"
)

print(
    "Accident-containing segments:",
    len(accident_segments)
)


# --------------------------------------------------
# 2. GET ALL OSM ROAD EDGES
# --------------------------------------------------

print("\nExtracting road segments from OSM...")

edges = ox.graph_to_gdfs(
    G,
    nodes=False,
    edges=True
).reset_index()

print("OSM road segments:", len(edges))


# --------------------------------------------------
# 3. IDENTIFY SEGMENTS THAT ALREADY HAVE ACCIDENTS
# --------------------------------------------------

accident_keys = set(
    zip(
        accident_segments["u"],
        accident_segments["v"],
        accident_segments["key"]
    )
)

print(
    "Known accident road segments:",
    len(accident_keys)
)


# --------------------------------------------------
# 4. FIND ZERO-ACCIDENT ROAD SEGMENTS
# --------------------------------------------------

edges["segment_key"] = list(
    zip(
        edges["u"],
        edges["v"],
        edges["key"]
    )
)

zero_accident = edges[
    ~edges["segment_key"].isin(accident_keys)
].copy()

print(
    "Zero-accident road segments available:",
    len(zero_accident)
)


# --------------------------------------------------
# 5. SAMPLE ZERO-ACCIDENT SEGMENTS
# --------------------------------------------------

# We don't need hundreds of thousands of examples.
# 1,000 zero-accident segments is enough for our prototype.

sample_size = min(
    1000,
    len(zero_accident)
)

zero_sample = zero_accident.sample(
    n=sample_size,
    random_state=42
).copy()

print(
    "Zero-accident segments sampled:",
    len(zero_sample)
)


# --------------------------------------------------
# 6. KEEP ROAD FEATURES
# --------------------------------------------------

zero_sample["accident_count"] = 0
zero_sample["severity_score"] = 0
zero_sample["total_casualties"] = 0

zero_sample["risk_score"] = 0
zero_sample["risk_level"] = "Low"


# Keep only the columns we need
zero_sample = zero_sample[
    [
        "u",
        "v",
        "key",
        "accident_count",
        "severity_score",
        "total_casualties",
        "risk_score",
        "risk_level",
        "length",
        "highway",
        "lanes",
        "maxspeed",
        "oneway"
    ]
].copy()


# Rename road length
zero_sample.rename(
    columns={
        "length": "road_length"
    },
    inplace=True
)


# --------------------------------------------------
# 7. PREPARE ACCIDENT SEGMENTS
# --------------------------------------------------

accident_data = accident_segments[
    [
        "u",
        "v",
        "key",
        "accident_count",
        "severity_score",
        "total_casualties",
        "risk_score",
        "risk_level",
        "road_length",
        "highway",
        "lanes",
        "maxspeed",
        "oneway"
    ]
].copy()


# --------------------------------------------------
# 8. COMBINE BOTH DATASETS
# --------------------------------------------------

final_dataset = pd.concat(
    [
        accident_data,
        zero_sample
    ],
    ignore_index=True
)


# --------------------------------------------------
# 9. CLEAN DATA
# --------------------------------------------------

# Convert road features to strings where necessary
final_dataset["highway"] = (
    final_dataset["highway"]
    .astype(str)
)

final_dataset["lanes"] = (
    final_dataset["lanes"]
    .astype(str)
)

final_dataset["maxspeed"] = (
    final_dataset["maxspeed"]
    .astype(str)
)


# --------------------------------------------------
# 10. SHUFFLE DATASET
# --------------------------------------------------

final_dataset = final_dataset.sample(
    frac=1,
    random_state=42
).reset_index(drop=True)


# --------------------------------------------------
# 11. SAVE
# --------------------------------------------------

final_dataset.to_csv(
    "data/ml_training_dataset_final.csv",
    index=False
)


# --------------------------------------------------
# 12. RESULTS
# --------------------------------------------------

print("\n======================================")
print("FINAL ML DATASET CREATED!")
print("======================================")

print(
    "Total road segments:",
    len(final_dataset)
)

print(
    "Columns:",
    len(final_dataset.columns)
)

print("\nRisk distribution:")

print(
    final_dataset["risk_level"]
    .value_counts()
)

print("\nRisk score statistics:")

print(
    final_dataset["risk_score"].describe()
)

print("\nSaved to:")
print(
    "data/ml_training_dataset_final.csv"
)