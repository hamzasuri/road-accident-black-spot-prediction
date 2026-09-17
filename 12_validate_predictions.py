import pandas as pd
import numpy as np
import osmnx as ox
import geopandas as gpd


print("======================================")
print("SPATIAL VALIDATION OF ML PREDICTIONS")
print("======================================")


# --------------------------------------------------
# 1. LOAD KNOWN HOTSPOTS
# --------------------------------------------------

print("\nLoading known Bengaluru hotspots...")

hotspots = pd.read_csv(
    "data/bangalore_accident_data.csv"
)

print(
    "Known hotspots:",
    len(hotspots)
)


# --------------------------------------------------
# 2. LOAD ML PREDICTIONS
# --------------------------------------------------

print("\nLoading ML predictions...")

predictions = pd.read_csv(
    "data/road_risk_predictions.csv"
)

print(
    "Predicted road segments:",
    len(predictions)
)


# --------------------------------------------------
# 3. LOAD ROAD NETWORK
# --------------------------------------------------

print("\nLoading Bengaluru road network...")

G = ox.load_graphml(
    "data/bengaluru_road_network.graphml"
)

print("Road network loaded!")


# --------------------------------------------------
# 4. CONVERT ROAD NETWORK TO GEODATAFRAME
# --------------------------------------------------

print("\nConverting road network to GeoDataFrame...")

edges = ox.graph_to_gdfs(
    G,
    nodes=False,
    edges=True
).reset_index()


# --------------------------------------------------
# 5. CLEAN IDENTIFIERS
# --------------------------------------------------

predictions["u"] = (
    predictions["u"].astype(str)
)

predictions["v"] = (
    predictions["v"].astype(str)
)

predictions["key"] = (
    predictions["key"].astype(str)
)


edges["u"] = (
    edges["u"].astype(str)
)

edges["v"] = (
    edges["v"].astype(str)
)

edges["key"] = (
    edges["key"].astype(str)
)


# --------------------------------------------------
# 6. MATCH PREDICTIONS TO ROAD GEOMETRY
# --------------------------------------------------

print("\nMatching predictions to road geometry...")

risk_edges = edges.merge(
    predictions[
        [
            "u",
            "v",
            "key",
            "predicted_risk_score",
            "predicted_risk_level",
            "prediction_confidence"
        ]
    ],
    on=[
        "u",
        "v",
        "key"
    ],
    how="inner"
)


print(
    "Predicted roads with geometry:",
    len(risk_edges)
)


# --------------------------------------------------
# 7. CREATE GEODATAFRAME FOR PREDICTED ROADS
# --------------------------------------------------

risk_gdf = gpd.GeoDataFrame(
    risk_edges,
    geometry="geometry",
    crs="EPSG:4326"
)


# --------------------------------------------------
# 8. CREATE GEODATAFRAME FOR HOTSPOTS
# --------------------------------------------------

hotspot_gdf = gpd.GeoDataFrame(
    hotspots.copy(),
    geometry=gpd.points_from_xy(
        hotspots["longitude"],
        hotspots["latitude"]
    ),
    crs="EPSG:4326"
)


# --------------------------------------------------
# 9. PROJECT TO METRES
# --------------------------------------------------

print("\nProjecting data to metres...")

# Bengaluru is approximately in UTM Zone 43N
projected_crs = "EPSG:32643"

risk_projected = risk_gdf.to_crs(
    projected_crs
)

hotspot_projected = hotspot_gdf.to_crs(
    projected_crs
)


# --------------------------------------------------
# 10. SPATIAL NEAREST-ROAD MATCHING
# --------------------------------------------------

print("\nFinding nearest predicted road for each hotspot...")

validation = gpd.sjoin_nearest(
    hotspot_projected,
    risk_projected[
        [
            "predicted_risk_score",
            "predicted_risk_level",
            "prediction_confidence",
            "geometry"
        ]
    ],
    how="left",
    distance_col="distance_to_predicted_road"
)


# --------------------------------------------------
# 11. CONVERT DISTANCE TO METRES
# --------------------------------------------------

validation[
    "distance_to_predicted_road"
] = validation[
    "distance_to_predicted_road"
].round(2)


# --------------------------------------------------
# 12. CHECK DISTANCE THRESHOLDS
# --------------------------------------------------

print("\n======================================")
print("SPATIAL VALIDATION RESULTS")
print("======================================")


thresholds = [
    25,
    50,
    100,
    200
]


for threshold in thresholds:

    nearby = validation[
        validation[
            "distance_to_predicted_road"
        ] <= threshold
    ]

    high_risk_nearby = nearby[
        nearby[
            "predicted_risk_level"
        ].isin(
            [
                "High",
                "Critical"
            ]
        )
    ]

    print(
        f"\nWithin {threshold} metres:"
    )

    print(
        "Hotspots matched:",
        len(nearby),
        "/",
        len(hotspots)
    )

    print(
        "High/Critical:",
        len(high_risk_nearby),
        "/",
        len(hotspots)
    )

    percentage = (
        len(high_risk_nearby)
        / len(hotspots)
        * 100
    )

    print(
        "High/Critical percentage:",
        round(
            percentage,
            2
        ),
        "%"
    )


# --------------------------------------------------
# 13. USE 100 METRES AS PRIMARY VALIDATION
# --------------------------------------------------

validation_100m = validation[
    validation[
        "distance_to_predicted_road"
    ] <= 100
].copy()


high_critical_100m = validation_100m[
    validation_100m[
        "predicted_risk_level"
    ].isin(
        [
            "High",
            "Critical"
        ]
    )
]


primary_percentage = (
    len(high_critical_100m)
    / len(hotspots)
    * 100
)


# --------------------------------------------------
# 14. DISPLAY RESULTS
# --------------------------------------------------

print("\n======================================")
print("PRIMARY VALIDATION RESULT")
print("======================================")


print(
    "Validation radius: 100 metres"
)


print(
    "Known hotspots within 100m of "
    "predicted roads:",
    len(validation_100m),
    "/",
    len(hotspots)
)


print(
    "Known hotspots near High/Critical "
    "roads:",
    len(high_critical_100m),
    "/",
    len(hotspots)
)


print(
    "Validation percentage:",
    round(
        primary_percentage,
        2
    ),
    "%"
)


# --------------------------------------------------
# 15. DISPLAY ALL HOTSPOT RESULTS
# --------------------------------------------------

print("\n======================================")
print("HOTSPOT VALIDATION DETAILS")
print("======================================")


result_columns = [
    "location",
    "severity",
    "incidents",
    "predicted_risk_score",
    "predicted_risk_level",
    "prediction_confidence",
    "distance_to_predicted_road"
]


display_data = validation[
    result_columns
].sort_values(
    "distance_to_predicted_road"
)


print(
    display_data.to_string(
        index=False
    )
)


# --------------------------------------------------
# 16. SAVE VALIDATION RESULTS
# --------------------------------------------------

# Remove geometry before saving CSV

validation_output = pd.DataFrame(
    validation.drop(
        columns="geometry",
        errors="ignore"
    )
)


validation_output.to_csv(
    "data/hotspot_validation_results.csv",
    index=False
)


print("\n======================================")
print("SPATIAL VALIDATION COMPLETE!")
print("======================================")


print("\nSaved to:")

print(
    "data/hotspot_validation_results.csv"
)