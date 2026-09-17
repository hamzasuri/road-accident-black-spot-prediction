import pandas as pd
import numpy as np
import osmnx as ox


print("======================================")
print("ENHANCED FEATURE ENGINEERING")
print("======================================")


# --------------------------------------------------
# 1. LOAD FINAL ML DATASET
# --------------------------------------------------

print("\nLoading final ML dataset...")

segments = pd.read_csv(
    "data/ml_training_dataset_final.csv"
)

print("Road segments:", len(segments))


# --------------------------------------------------
# 2. LOAD ORIGINAL ACCIDENT DATA
# --------------------------------------------------

print("\nLoading historical accident data...")

accidents = pd.read_csv(
    "data/indian_roads_dataset.csv"
)

# Bengaluru only
accidents = accidents[
    accidents["city"].astype(str).str.lower() == "bangalore"
].copy()

print("Bengaluru accidents:", len(accidents))


# --------------------------------------------------
# 3. CLEAN ACCIDENT DATA
# --------------------------------------------------

print("\nCleaning accident data...")

accidents["latitude"] = pd.to_numeric(
    accidents["latitude"],
    errors="coerce"
)

accidents["longitude"] = pd.to_numeric(
    accidents["longitude"],
    errors="coerce"
)

accidents["hour"] = pd.to_numeric(
    accidents["hour"],
    errors="coerce"
)

accidents["temperature"] = pd.to_numeric(
    accidents["temperature"],
    errors="coerce"
)

accidents["is_peak_hour"] = pd.to_numeric(
    accidents["is_peak_hour"],
    errors="coerce"
)

accidents["is_weekend"] = pd.to_numeric(
    accidents["is_weekend"],
    errors="coerce"
)


# Convert traffic signal to 0/1
accidents["traffic_signal"] = (
    accidents["traffic_signal"]
    .astype(str)
    .str.lower()
    .map({
        "yes": 1,
        "no": 0,
        "true": 1,
        "false": 0
    })
)


# Convert festival to 0/1
accidents["festival"] = (
    accidents["festival"]
    .astype(str)
    .str.lower()
    .map({
        "yes": 1,
        "no": 0,
        "true": 1,
        "false": 0
    })
)


# --------------------------------------------------
# 4. REMOVE INVALID COORDINATES
# --------------------------------------------------

accidents = accidents.dropna(
    subset=[
        "latitude",
        "longitude"
    ]
)

print(
    "Valid accident records:",
    len(accidents)
)


# --------------------------------------------------
# 5. LOAD OSM ROAD NETWORK
# --------------------------------------------------

print("\nLoading Bengaluru road network...")

G = ox.load_graphml(
    "data/bengaluru_road_network.graphml"
)

print("Road network loaded!")


# --------------------------------------------------
# 6. MAP ACCIDENTS TO ROAD SEGMENTS
# --------------------------------------------------

print("\nMapping accidents to road segments...")

nearest_edges = ox.distance.nearest_edges(
    G,
    X=accidents["longitude"].values,
    Y=accidents["latitude"].values
)

accidents["u"] = [
    edge[0] for edge in nearest_edges
]

accidents["v"] = [
    edge[1] for edge in nearest_edges
]

accidents["key"] = [
    edge[2] for edge in nearest_edges
]

print("Accidents mapped successfully.")


# --------------------------------------------------
# 7. CREATE CONTEXT VALUES
# --------------------------------------------------

print("\nCreating contextual features...")


accidents["peak_value"] = (
    accidents["is_peak_hour"]
    .fillna(0)
)

accidents["weekend_value"] = (
    accidents["is_weekend"]
    .fillna(0)
)

accidents["signal_value"] = (
    accidents["traffic_signal"]
    .fillna(0)
)

accidents["festival_value"] = (
    accidents["festival"]
    .fillna(0)
)


# --------------------------------------------------
# 8. AGGREGATE CONTEXT BY ROAD SEGMENT
# --------------------------------------------------

segment_context = (
    accidents
    .groupby(["u", "v", "key"])
    .agg(
        avg_accident_hour=("hour", "mean"),
        avg_temperature=("temperature", "mean"),
        peak_hour_ratio=("peak_value", "mean"),
        weekend_ratio=("weekend_value", "mean"),
        traffic_signal_ratio=("signal_value", "mean"),
        festival_ratio=("festival_value", "mean")
    )
    .reset_index()
)


# --------------------------------------------------
# 9. MOST COMMON WEATHER
# --------------------------------------------------

weather_mode = (
    accidents
    .groupby(["u", "v", "key"])["weather"]
    .agg(
        lambda x: (
            x.mode().iloc[0]
            if not x.mode().empty
            else "unknown"
        )
    )
    .reset_index()
)

weather_mode.rename(
    columns={
        "weather": "common_weather"
    },
    inplace=True
)


# --------------------------------------------------
# 10. MOST COMMON TRAFFIC DENSITY
# --------------------------------------------------

traffic_mode = (
    accidents
    .groupby(["u", "v", "key"])["traffic_density"]
    .agg(
        lambda x: (
            x.mode().iloc[0]
            if not x.mode().empty
            else "unknown"
        )
    )
    .reset_index()
)

traffic_mode.rename(
    columns={
        "traffic_density":
        "common_traffic_density"
    },
    inplace=True
)


# --------------------------------------------------
# 11. MOST COMMON ACCIDENT CAUSE
# --------------------------------------------------

cause_mode = (
    accidents
    .groupby(["u", "v", "key"])["cause"]
    .agg(
        lambda x: (
            x.mode().iloc[0]
            if not x.mode().empty
            else "unknown"
        )
    )
    .reset_index()
)

cause_mode.rename(
    columns={
        "cause":
        "common_accident_cause"
    },
    inplace=True
)


# --------------------------------------------------
# 12. COMBINE CONTEXTUAL DATA
# --------------------------------------------------

context_features = segment_context.merge(
    weather_mode,
    on=["u", "v", "key"],
    how="left"
)

context_features = context_features.merge(
    traffic_mode,
    on=["u", "v", "key"],
    how="left"
)

context_features = context_features.merge(
    cause_mode,
    on=["u", "v", "key"],
    how="left"
)


# --------------------------------------------------
# 13. MERGE WITH ROAD SEGMENTS
# --------------------------------------------------

print("\nCombining road and contextual features...")

df = segments.merge(
    context_features,
    on=["u", "v", "key"],
    how="left"
)


# --------------------------------------------------
# 14. HANDLE MISSING NUMERIC VALUES
# --------------------------------------------------

numeric_columns = [
    "avg_accident_hour",
    "avg_temperature",
    "peak_hour_ratio",
    "weekend_ratio",
    "traffic_signal_ratio",
    "festival_ratio"
]

for column in numeric_columns:

    median_value = df[column].median()

    if pd.isna(median_value):
        median_value = 0

    df[column] = df[column].fillna(
        median_value
    )


# --------------------------------------------------
# 15. HANDLE MISSING CATEGORICAL VALUES
# --------------------------------------------------

categorical_columns = [
    "common_weather",
    "common_traffic_density",
    "common_accident_cause"
]

for column in categorical_columns:

    df[column] = df[column].fillna(
        "unknown"
    )


# --------------------------------------------------
# 16. CLEAN OSM ROAD FEATURES
# --------------------------------------------------

print("Cleaning OSM road features...")


df["highway"] = (
    df["highway"]
    .astype(str)
)


df["lanes"] = pd.to_numeric(
    df["lanes"],
    errors="coerce"
)

lanes_median = df["lanes"].median()

if pd.isna(lanes_median):
    lanes_median = 1

df["lanes"] = df["lanes"].fillna(
    lanes_median
)


df["maxspeed"] = (
    df["maxspeed"]
    .astype(str)
    .str.extract(
        r"(\d+\.?\d*)"
    )[0]
)

df["maxspeed"] = pd.to_numeric(
    df["maxspeed"],
    errors="coerce"
)

speed_median = df["maxspeed"].median()

if pd.isna(speed_median):
    speed_median = 40

df["maxspeed"] = df["maxspeed"].fillna(
    speed_median
)


# Convert oneway
df["oneway"] = (
    df["oneway"]
    .astype(str)
    .str.lower()
    .map({
        "true": 1,
        "false": 0
    })
    .fillna(0)
)


# Road length in kilometres
df["road_length_km"] = (
    df["road_length"] / 1000
)


# --------------------------------------------------
# 17. ONE-HOT ENCODING
# --------------------------------------------------

print("Encoding categorical features...")


categorical_features = [
    "highway",
    "common_weather",
    "common_traffic_density",
    "common_accident_cause"
]


encoded = pd.get_dummies(
    df[categorical_features],
    prefix=[
        "road_type",
        "weather",
        "traffic",
        "cause"
    ],
    dtype=int
)


df = pd.concat(
    [
        df.drop(
            columns=categorical_features
        ),
        encoded
    ],
    axis=1
)


# --------------------------------------------------
# 18. SELECT MODEL FEATURES
# --------------------------------------------------

feature_columns = [

    # Road features
    "road_length",
    "road_length_km",
    "lanes",
    "maxspeed",
    "oneway",

    # Time features
    "avg_accident_hour",

    # Environmental features
    "avg_temperature",

    # Traffic/context features
    "peak_hour_ratio",
    "weekend_ratio",
    "traffic_signal_ratio",
    "festival_ratio"
]


# Add encoded categorical features
encoded_columns = [
    column
    for column in df.columns
    if (
        column.startswith("road_type_")
        or column.startswith("weather_")
        or column.startswith("traffic_")
        or column.startswith("cause_")
    )
]

feature_columns.extend(
    encoded_columns
)


# --------------------------------------------------
# 19. CREATE X AND Y
# --------------------------------------------------

X = df[
    feature_columns
].copy()

y = df[
    "risk_level"
].copy()


# Final safety check
X = X.replace(
    [np.inf, -np.inf],
    np.nan
)

X = X.fillna(0)


# --------------------------------------------------
# 20. RESULTS
# --------------------------------------------------

print("\n======================================")
print("ENHANCED FEATURE MATRIX")
print("======================================")

print(
    "Samples:",
    len(X)
)

print(
    "Features:",
    len(feature_columns)
)

print("\nTarget distribution:")

print(
    y.value_counts()
)


# --------------------------------------------------
# 21. CHECK MISSING VALUES
# --------------------------------------------------

print("\nChecking missing values...")

missing = X.isnull().sum()

missing = missing[
    missing > 0
]

if len(missing) == 0:

    print(
        "No missing values in features! ✅"
    )

else:

    print(missing)


# --------------------------------------------------
# 22. SAVE FEATURE DATASET
# --------------------------------------------------

output = X.copy()

output["risk_level"] = y

output["risk_score"] = df[
    "risk_score"
]


output.to_csv(
    "data/ml_features.csv",
    index=False
)


print("\n======================================")
print("FEATURE ENGINEERING COMPLETE!")
print("======================================")

print(
    "Number of samples:",
    len(output)
)

print(
    "Number of features:",
    len(feature_columns)
)

print("\nSaved to:")
print("data/ml_features.csv")