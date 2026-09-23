import { useEffect, useState } from "react";
import { MapContainer, TileLayer, Polyline, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import "./App.css";
function getRiskColor(riskLevel) {
  switch (riskLevel) {
    case "Low":
      return "green";
    case "Medium":
      return "yellow";
    case "High":
      return "orange";
    case "Critical":
      return "red";
    default:
      return "gray";
  }
}
function App() {
  const [roads, setRoads] = useState([]);

  useEffect(() => {
    fetch("http://127.0.0.1:8000/roads")
      .then((response) => response.json())
      .then((data) => {
        console.log("Roads received:", data);
        console.log("First road geometry:", data[0]?.geometry);
        setRoads(data);
      })
      .catch((error) => {
        console.error("Error fetching roads:", error);
      });
  }, []);
  return (
    <div className="app">
      <header className="header">
        <h1>Bengaluru Road Accident Risk Map</h1>
        <p>AI-powered road risk visualization</p>
      </header>

      <main className="map-container">
        <MapContainer
          center={[12.9716, 77.5946]}
          zoom={11}
          style={{ height: "100%", width: "100%" }}
        >
          <TileLayer
            attribution="&copy; OpenStreetMap contributors"
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {roads.map((road) => {
  if (!road.geometry || !road.geometry.coordinates) {
    return null;
  }

  const positions = road.geometry.coordinates.map(
    ([lng, lat]) => [lat, lng]
  );

  return (
    <Polyline
    key={road.id}
    positions={positions}
    eventHandlers={{
      click: () => {
        console.log("ROAD CLICKED:", road);
      },
    }}
    pathOptions={{
      color: "blue",
      weight: 12,
      opacity: 0.9,
    }}
  >
    <Popup>
      <strong>Road Risk Information</strong>
      <br />
      Risk Level: {road.risk_level}
      <br />
      Risk Score: {road.risk_score}
      <br />
      Confidence: {road.prediction_confidence}%
      <br />
      Road Type: {road.highway}
      <br />
      Road Length: {road.road_length?.toFixed(2)} m
    </Popup>
  </Polyline>
  );
})}
        </MapContainer>
      </main>
    </div>
  );
}

export default App;