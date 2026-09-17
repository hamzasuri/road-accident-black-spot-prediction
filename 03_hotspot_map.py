
import pandas as pd
import folium

# Load Bengaluru hotspot data
df = pd.read_csv("data/bangalore_accident_data.csv")

# Center of Bengaluru
center_lat = df["latitude"].mean()
center_lon = df["longitude"].mean()

# Create map
m = folium.Map(
    location=[center_lat, center_lon],
    zoom_start=12,
    max_zoom=16,
    tiles=None
)

folium.TileLayer(
    tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
    attr="Esri",
    name="Street Map"
).add_to(m)

# Add every hotspot
for _, row in df.iterrows():

    popup_text = f"""
    <b>Location:</b> {row['location']}<br>
    <b>Severity:</b> {row['severity']}<br>
    <b>Incidents:</b> {row['incidents']}<br>
    <b>Accident Type:</b> {row['accident_type']}<br>
    <b>Peak Hours:</b> {row['peak_hours']}<br>
    <b>Road Condition:</b> {row['road_condition']}<br>
    <b>Weather Factor:</b> {row['weather_factor']}
    """

    folium.Marker(
        location=[row["latitude"], row["longitude"]],
        popup=popup_text,
        tooltip=row["location"]
    ).add_to(m)

# Save map
m.save("bangalore_hotspots_map.html")

print("Map created successfully!")