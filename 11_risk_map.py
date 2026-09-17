import osmnx as ox
import pandas as pd
import folium


print("======================================")
print("CREATING BENGALURU RISK MAP")
print("======================================")


# --------------------------------------------------
# 1. LOAD ROAD NETWORK
# --------------------------------------------------

print("\nLoading Bengaluru road network...")

G = ox.load_graphml(
    "data/bengaluru_road_network.graphml"
)

print("Road network loaded!")


# --------------------------------------------------
# 2. LOAD RISK PREDICTIONS
# --------------------------------------------------

print("\nLoading risk predictions...")

predictions = pd.read_csv(
    "data/road_risk_predictions.csv"
)

print(
    "Predictions loaded:",
    len(predictions)
)


# --------------------------------------------------
# 3. CONVERT ROAD NETWORK TO GEODATAFRAME
# --------------------------------------------------

print("\nConverting road network to GeoDataFrame...")

edges = ox.graph_to_gdfs(
    G,
    nodes=False,
    edges=True
).reset_index()


# --------------------------------------------------
# 4. MATCH DATA TYPES
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
# 5. MERGE RISK PREDICTIONS WITH ROAD GEOMETRY
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
    "Road segments matched:",
    len(risk_edges)
)


# --------------------------------------------------
# 6. CREATE MAP
# --------------------------------------------------

print("\nCreating Bengaluru map...")


center_lat = 12.9716
center_lon = 77.5946


m = folium.Map(
    location=[
        center_lat,
        center_lon
    ],
    zoom_start=11,
    tiles=None
)


# --------------------------------------------------
# 7. ESRI STREET MAP
# --------------------------------------------------

folium.TileLayer(
    tiles=(
        "https://server.arcgisonline.com/"
        "ArcGIS/rest/services/"
        "World_Street_Map/"
        "MapServer/tile/{z}/{y}/{x}"
    ),
    attr="Esri",
    name="Esri World Street Map",
    overlay=False,
    control=True
).add_to(m)


# --------------------------------------------------
# 8. RISK COLORS
# --------------------------------------------------

risk_colors = {
    "Low": "green",
    "Medium": "orange",
    "High": "red",
    "Critical": "darkred"
}


# --------------------------------------------------
# 9. ADD RISK ROAD SEGMENTS
# --------------------------------------------------

print("\nAdding risk segments...")


for _, row in risk_edges.iterrows():

    level = row[
        "predicted_risk_level"
    ]

    score = row[
        "predicted_risk_score"
    ]

    confidence = row[
        "prediction_confidence"
    ]

    road_type = row[
        "highway"
    ]

    color = risk_colors.get(
        level,
        "gray"
    )


    geometry = row[
        "geometry"
    ]


    if geometry is None:
        continue


    # Handle LineString
    if geometry.geom_type == "LineString":

        coordinates = [
            [
                lat,
                lon
            ]
            for lon, lat
            in geometry.coords
        ]

        popup_text = f"""
        <b>Road Risk Prediction</b><br><br>
        Risk Level: <b>{level}</b><br>
        Risk Score: <b>{score:.2f}/100</b><br>
        Confidence: <b>{confidence:.2f}%</b><br>
        Road Type: {road_type}
        """

        folium.PolyLine(
            locations=coordinates,
            color=color,
            weight=4,
            opacity=0.8,
            popup=folium.Popup(
                popup_text,
                max_width=300
            )
        ).add_to(m)


    # Handle MultiLineString
    elif geometry.geom_type == "MultiLineString":

        for line in geometry.geoms:

            coordinates = [
                [
                    lat,
                    lon
                ]
                for lon, lat
                in line.coords
            ]

            popup_text = f"""
            <b>Road Risk Prediction</b><br><br>
            Risk Level: <b>{level}</b><br>
            Risk Score: <b>{score:.2f}/100</b><br>
            Confidence: <b>{confidence:.2f}%</b><br>
            Road Type: {road_type}
            """

            folium.PolyLine(
                locations=coordinates,
                color=color,
                weight=4,
                opacity=0.8,
                popup=folium.Popup(
                    popup_text,
                    max_width=300
                )
            ).add_to(m)


# --------------------------------------------------
# 10. ADD LEGEND
# --------------------------------------------------

legend_html = """
<div style="
position: fixed;
bottom: 30px;
left: 30px;
width: 190px;
background-color: white;
border: 2px solid grey;
z-index: 9999;
padding: 12px;
font-size: 14px;
box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
">

<b>Road Accident Risk</b>

<br><br>

<span style="color:green; font-size:20px;">
●
</span>
Low

<br>

<span style="color:orange; font-size:20px;">
●
</span>
Medium

<br>

<span style="color:red; font-size:20px;">
●
</span>
High

<br>

<span style="color:darkred; font-size:20px;">
●
</span>
Critical

</div>
"""


m.get_root().html.add_child(
    folium.Element(
        legend_html
    )
)


# --------------------------------------------------
# 11. ADD LAYER CONTROL
# --------------------------------------------------

folium.LayerControl().add_to(m)


# --------------------------------------------------
# 12. SAVE MAP
# --------------------------------------------------

output_file = (
    "data/bengaluru_risk_map.html"
)

m.save(
    output_file
)


print("\n======================================")
print("RISK MAP CREATED SUCCESSFULLY!")
print("======================================")

print(
    "Mapped road segments:",
    len(risk_edges)
)

print("\nSaved to:")

print(
    output_file
)