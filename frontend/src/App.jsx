import { useEffect, useMemo, useState } from "react";

import {
  MapContainer,
  TileLayer,
  Polyline,
  Popup,
  Circle,
  useMap,
} from "react-leaflet";

import "leaflet/dist/leaflet.css";

import "./App.css";

const API_URL = "http://127.0.0.1:8000";

const RISK_LEVELS = ["Low", "Medium", "High", "Critical"];

const RISK_COLORS = {
  Low: "#22c55e",

  Medium: "#eab308",

  High: "#f97316",

  Critical: "#ef4444",
};

function getWeatherRiskAdjustment(weatherData) {
  if (!weatherData) return { points: 0, reason: "Weather unavailable" };
  const code = Number(weatherData.weather_code);
  const precipitation = Number(weatherData.precipitation || 0);
  if ([95, 96, 99].includes(code))
    return { points: 20, reason: "Thunderstorm rule (+20)" };
  if ([45, 48].includes(code)) return { points: 10, reason: "Fog rule (+10)" };
  if (
    [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82].includes(code) ||
    precipitation > 0
  )
    return { points: 10, reason: "Rain/drizzle rule (+10)" };
  return { points: 0, reason: "No weather adjustment" };
}

function getAdjustedRiskScore(baseScore, adjustment) {
  const score = Number(baseScore);
  if (!Number.isFinite(score)) return null;
  return Math.min(100, Math.max(0, score + adjustment));
}

function describeWeatherCode(code) {
  if (code === 0) return "Clear sky";
  if ([1, 2, 3].includes(code)) return "Partly cloudy";
  if ([45, 48].includes(code)) return "Fog";
  if ([51, 53, 55, 56, 57].includes(code)) return "Drizzle";
  if ([61, 63, 65, 66, 67, 80, 81, 82].includes(code)) return "Rain";
  if ([71, 73, 75, 77, 85, 86].includes(code)) return "Snow";
  if ([95, 96, 99].includes(code)) return "Thunderstorm";
  return "Conditions unavailable";
}

function App() {
  const [roads, setRoads] = useState([]);

  const [searchTerm, setSearchTerm] = useState("");
  const [areaQuery, setAreaQuery] = useState("");
  const [selectedArea, setSelectedArea] = useState(null);
  const [areaLoading, setAreaLoading] = useState(false);
  const [areaError, setAreaError] = useState("");
  const [weather, setWeather] = useState(null);
  const [weatherLoading, setWeatherLoading] = useState(true);
  const [weatherError, setWeatherError] = useState("");

  const weatherRiskAdjustment = getWeatherRiskAdjustment(weather);

  const [selectedRisk, setSelectedRisk] = useState("All");

  const [selectedRoad, setSelectedRoad] = useState(null);

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();

    async function fetchRoads() {
      try {
        setLoading(true);

        setError("");

        const response = await fetch(`${API_URL}/roads`, {
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(`API returned ${response.status}`);
        }

        const data = await response.json();

        if (!Array.isArray(data)) {
          throw new Error("Unexpected road data format");
        }

        setRoads(data);
      } catch (err) {
        if (err.name !== "AbortError") {
          console.error("Error fetching roads:", err);

          setError(
            "Unable to load road data. Check that FastAPI and your database are available.",
          );
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    fetchRoads();

    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();

    async function fetchWeather() {
      const latitude = selectedArea?.lat ?? 12.9716;
      const longitude = selectedArea?.lon ?? 77.5946;
      try {
        setWeatherLoading(true);
        setWeatherError("");
        const params = new URLSearchParams({
          latitude: String(latitude),
          longitude: String(longitude),
          current:
            "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m",
          hourly: "precipitation_probability,precipitation,weather_code",
          forecast_hours: "6",
          timezone: "Asia/Kolkata",
        });
        const response = await fetch(
          `https://api.open-meteo.com/v1/forecast?${params.toString()}`,
          { signal: controller.signal },
        );
        if (!response.ok) throw new Error("Weather service returned an error.");
        const data = await response.json();
        if (!data.current)
          throw new Error("Current weather data is unavailable.");
        // Keep current observations separate from the short-term forecast.
        // Compare hourly timestamps to the current observation time so we only
        // consider the next three forecast hours for the upcoming-rain advisory.
        const currentTime = data.current.time;
        const hourlyTimes = data.hourly?.time || [];
        const currentHourIndex = hourlyTimes.findIndex(
          (time) => time >= currentTime,
        );
        const forecastIndices =
          currentHourIndex >= 0
            ? hourlyTimes
                .map((_, index) => index)
                .filter(
                  (index) =>
                    index >= currentHourIndex && index <= currentHourIndex + 3,
                )
            : [];
        const upcomingRain = forecastIndices.some((index) => {
          const code = Number(data.hourly?.weather_code?.[index]);
          const probability = Number(
            data.hourly?.precipitation_probability?.[index] ?? 0,
          );
          const amount = Number(data.hourly?.precipitation?.[index] ?? 0);
          const rainCode = [
            51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82,
          ].includes(code);
          return rainCode || amount > 0 || probability >= 50;
        });
        setWeather({
          ...data.current,
          upcomingRain,
          forecastRainProbability: forecastIndices.length
            ? Math.max(
                ...forecastIndices.map((index) =>
                  Number(data.hourly?.precipitation_probability?.[index] ?? 0),
                ),
              )
            : null,
          locationName: selectedArea?.name || "Bengaluru",
          timezone: data.timezone || "Asia/Kolkata",
        });
      } catch (err) {
        if (err.name !== "AbortError") {
          setWeatherError("Live weather is temporarily unavailable.");
          setWeather(null);
        }
      } finally {
        if (!controller.signal.aborted) setWeatherLoading(false);
      }
    }

    fetchWeather();
    return () => controller.abort();
  }, [selectedArea]);

  const riskCounts = useMemo(() => {
    return RISK_LEVELS.reduce((counts, level) => {
      counts[level] = roads.filter((road) => road.risk_level === level).length;

      return counts;
    }, {});
  }, [roads]);

  const averageRisk = useMemo(() => {
    const scores = roads

      .map((road) => Number(road.risk_score))

      .filter((score) => Number.isFinite(score));

    if (!scores.length) return null;

    return scores.reduce((total, score) => total + score, 0) / scores.length;
  }, [roads]);

  const filteredRoads = useMemo(() => {
    const query = searchTerm.trim().toLowerCase();

    return roads.filter((road) => {
      const matchesRisk =
        selectedRisk === "All" || road.risk_level === selectedRisk;

      const matchesSearch =
        !query ||
        String(road.id ?? "")
          .toLowerCase()

          .includes(query) ||
        String(road.highway ?? "")
          .toLowerCase()

          .includes(query) ||
        String(road.risk_level ?? "")
          .toLowerCase()

          .includes(query);

      return matchesRisk && matchesSearch;
    });
  }, [roads, selectedRisk, searchTerm]);

  const AREA_RADIUS_METERS = 1500;

  function distanceMeters(lat1, lon1, lat2, lon2) {
    const toRadians = (degrees) => (degrees * Math.PI) / 180;
    const earthRadius = 6371000;
    const dLat = toRadians(lat2 - lat1);
    const dLon = toRadians(lon2 - lon1);
    const a =
      Math.sin(dLat / 2) ** 2 +
      Math.cos(toRadians(lat1)) *
        Math.cos(toRadians(lat2)) *
        Math.sin(dLon / 2) ** 2;
    return 2 * earthRadius * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  }

  function roadIsNearArea(road, area) {
    const coordinates = road.geometry?.coordinates;
    if (!Array.isArray(coordinates)) return false;
    return coordinates.some(
      ([longitude, latitude]) =>
        Number.isFinite(latitude) &&
        Number.isFinite(longitude) &&
        distanceMeters(area.lat, area.lon, latitude, longitude) <=
          AREA_RADIUS_METERS,
    );
  }

  const areaRoads = useMemo(() => {
    if (!selectedArea) return filteredRoads;
    return filteredRoads.filter((road) => roadIsNearArea(road, selectedArea));
  }, [filteredRoads, selectedArea]);

  const areaRiskSummary = useMemo(() => {
    const scores = areaRoads
      .map((road) => Number(road.risk_score))
      .filter((score) => Number.isFinite(score));
    return {
      total: areaRoads.length,
      high: areaRoads.filter((road) => road.risk_level === "High").length,
      critical: areaRoads.filter((road) => road.risk_level === "Critical")
        .length,
      average: scores.length
        ? scores.reduce((sum, score) => sum + score, 0) / scores.length
        : null,
    };
  }, [areaRoads]);

  async function searchArea(event) {
    event.preventDefault();
    const query = areaQuery.trim();
    if (!query) {
      setAreaError("Enter a Bengaluru area name first.");
      return;
    }
    try {
      setAreaLoading(true);
      setAreaError("");
      const params = new URLSearchParams({
        q: `${query}, Bengaluru, Karnataka, India`,
        format: "jsonv2",
        limit: "1",
        countrycodes: "in",
      });
      const response = await fetch(
        `https://nominatim.openstreetmap.org/search?${params.toString()}`,
        { headers: { Accept: "application/json" } },
      );
      if (!response.ok)
        throw new Error("Area lookup is unavailable. Please try again.");
      const results = await response.json();
      if (!results.length)
        throw new Error(
          "Area not found. Try another Bengaluru locality or landmark.",
        );
      const result = results[0];
      const area = {
        name: result.name || query,
        lat: Number(result.lat),
        lon: Number(result.lon),
      };
      if (!Number.isFinite(area.lat) || !Number.isFinite(area.lon)) {
        throw new Error("The area lookup returned invalid coordinates.");
      }
      setSelectedArea(area);
      setSelectedRoad(null);
    } catch (err) {
      setAreaError(err.message || "Could not search for that area.");
    } finally {
      setAreaLoading(false);
    }
  }

  function clearAreaSearch() {
    setSelectedArea(null);
    setAreaError("");
    setAreaQuery("");
  }

  const roadsWithGeometry = areaRoads.filter(
    (road) =>
      road.geometry?.type === "LineString" &&
      Array.isArray(road.geometry.coordinates) &&
      road.geometry.coordinates.length >= 2,
  );

  function selectRisk(level) {
    setSelectedRisk(level);

    setSelectedRoad(null);
  }

  return (
    <main className="dashboard">
      <header className="topbar">
        <div className="brand">
          <div className="brand-icon">R</div>

          <div>
            <h1>Road Accident Black Spot Prediction</h1>

            <p>ROAD SAFETY INTELLIGENCE</p>
          </div>
        </div>

        <div className="header-right">
          <div className="location-label">
            <span className="status-dot" />
            Bengaluru, Karnataka
          </div>

          <span className="header-tag">ML-POWERED RISK ANALYSIS</span>
        </div>
      </header>

      <section className="dashboard-content">
        <div className="page-heading">
          <div>
            <p className="eyebrow">ROAD NETWORK MONITORING</p>

            <h2>Accident Risk Dashboard</h2>

            <p className="page-description">
              Explore predicted road risk across mapped Bengaluru road segments.
            </p>
          </div>

          <div className="data-status">
            <span className={`status-dot ${error ? "offline" : ""}`} />

            {loading
              ? "Loading data"
              : error
                ? "Connection issue"
                : "Road data loaded"}
          </div>
        </div>

        <section className="live-weather-panel" aria-label="Live weather">
          <div className="live-weather-heading">
            <div>
              <p className="eyebrow">LIVE CONDITIONS</p>
              <h3>Current weather · {selectedArea?.name || "Bengaluru"}</h3>
              <p>
                Current conditions from Open-Meteo. The weather-adjusted score
                is a separate rule-based estimate; the original ML score remains
                unchanged.
              </p>
            </div>
            <span
              className={`weather-status ${weatherError ? "weather-offline" : ""}`}
            >
              {weatherLoading
                ? "Updating…"
                : weatherError
                  ? "Unavailable"
                  : "Live data"}
            </span>
          </div>
          {weatherLoading ? (
            <p className="weather-message">Loading current weather…</p>
          ) : weatherError ? (
            <p className="weather-message weather-error" role="status">
              {weatherError} Check your internet connection and try again.
            </p>
          ) : weather ? (
            <div className="weather-metrics">
              <div className="weather-primary">
                <span className="weather-symbol" aria-hidden="true">
                  ☁
                </span>
                <div>
                  <strong>
                    {Number.isFinite(Number(weather.temperature_2m))
                      ? `${Number(weather.temperature_2m).toFixed(1)}°C`
                      : "N/A"}
                  </strong>
                  <span>{describeWeatherCode(weather.weather_code)}</span>
                </div>
              </div>
              <div className="weather-metric">
                <span>Feels like</span>
                <strong>
                  {weather.apparent_temperature == null
                    ? "N/A"
                    : `${Number(weather.apparent_temperature).toFixed(1)}°C`}
                </strong>
              </div>
              <div className="weather-metric">
                <span>Humidity</span>
                <strong>
                  {weather.relative_humidity_2m == null
                    ? "N/A"
                    : `${weather.relative_humidity_2m}%`}
                </strong>
              </div>
              <div className="weather-metric">
                <span>Wind</span>
                <strong>
                  {weather.wind_speed_10m == null
                    ? "N/A"
                    : `${weather.wind_speed_10m} km/h`}
                </strong>
              </div>
              <div className="weather-metric">
                <span>Precipitation</span>
                <strong>
                  {weather.precipitation == null
                    ? "N/A"
                    : `${weather.precipitation} mm`}
                </strong>
              </div>
              <div className="weather-updated">
                <span>Observation time</span>
                <strong>
                  {weather.time ? weather.time.replace("T", " ") : "N/A"} ·{" "}
                  {weather.timezone}
                </strong>
              </div>
            </div>
          ) : null}
        </section>

        {!weatherLoading &&
          !weatherError &&
          weather &&
          (() => {
            const code = Number(weather.weather_code);
            const isThunderstorm = [95, 96, 99].includes(code);
            const isRain =
              [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82].includes(
                code,
              ) || Number(weather.precipitation) > 0;
            const isFog = [45, 48].includes(code);
            const rainExpectedSoon =
              !isThunderstorm && !isRain && Boolean(weather.upcomingRain);
            const alertType = isThunderstorm
              ? "danger"
              : isRain || isFog || rainExpectedSoon
                ? "caution"
                : "clear";
            const title = isThunderstorm
              ? "Thunderstorm caution"
              : isRain
                ? "Rain-related road safety caution"
                : rainExpectedSoon
                  ? "Rain possible soon — drive cautiously"
                  : isFog
                    ? "Low-visibility caution"
                    : "No current weather alert";
            const message = isThunderstorm
              ? "Thunderstorms are reported near this area. If travelling, slow down, increase following distance, avoid flooded roads, and stop in a safe place if conditions become severe."
              : isRain
                ? "Rain or precipitation is reported near this area. Wet roads can reduce grip and increase stopping distance. Slow down, leave extra space, and avoid waterlogged roads."
                : rainExpectedSoon
                  ? `The hourly forecast indicates possible rain within the next few hours (maximum reported probability: ${weather.forecastRainProbability ?? "N/A"}%). Rain is not necessarily falling now. Reduce speed if conditions change and leave extra following distance.`
                  : isFog
                    ? "Fog is reported near this area and may reduce visibility. Use appropriate lights, reduce speed, and increase following distance."
                    : "Current reported conditions do not trigger the rain, thunderstorm, or fog warning rules. Always follow local conditions and traffic guidance.";
            return (
              <section
                className={`weather-safety-alert weather-alert-${alertType}`}
                aria-live="polite"
              >
                <div className="weather-alert-icon" aria-hidden="true">
                  {alertType === "danger"
                    ? "⚡"
                    : alertType === "caution"
                      ? "⚠"
                      : "✓"}
                </div>
                <div className="weather-alert-copy">
                  <p className="eyebrow">
                    WEATHER SAFETY ADVISORY ·{" "}
                    {selectedArea?.name || "Bengaluru"}
                  </p>
                  <h3>{title}</h3>
                  <p>{message}</p>
                  <small>
                    The base ML prediction remains unchanged. The separate
                    weather-adjusted score adds a transparent rule-based
                    allowance: {weatherRiskAdjustment.reason}. This is an
                    illustrative heuristic, not a validated accident
                    probability.
                  </small>
                </div>
              </section>
            );
          })()}

        {error && (
          <div className="error-banner" role="alert">
            {error}
          </div>
        )}

        <section className="stats-grid" aria-label="Road risk statistics">
          <article className="stat-card">
            <div className="stat-top">
              <span>Total road segments</span>

              <span className="stat-icon blue">↗</span>
            </div>

            <strong>{loading ? "—" : roads.length.toLocaleString()}</strong>

            <p>Road records from the API</p>
          </article>

          <article className="stat-card">
            <div className="stat-top">
              <span>High risk</span>

              <span className="stat-icon orange">!</span>
            </div>

            <strong>{loading ? "—" : riskCounts.High.toLocaleString()}</strong>

            <p>Predicted high-risk segments</p>
          </article>

          <article className="stat-card critical-card">
            <div className="stat-top">
              <span>Critical risk</span>

              <span className="stat-icon red">!</span>
            </div>

            <strong>
              {loading ? "—" : riskCounts.Critical.toLocaleString()}
            </strong>

            <p>Segments in the critical category</p>
          </article>

          <article className="stat-card">
            <div className="stat-top">
              <span>Average risk score</span>

              <span className="stat-icon purple">◈</span>
            </div>

            <strong>
              {loading || averageRisk === null ? "—" : averageRisk.toFixed(2)}
            </strong>

            <p>Average of returned risk scores</p>
          </article>
        </section>

        <section className="workspace">
          <div className="map-panel">
            <div className="panel-header">
              <div>
                <h3>Road risk map</h3>

                <p>Click a colored road segment to inspect its details.</p>
              </div>

              <span className="segment-count">
                {roadsWithGeometry.length.toLocaleString()} segments
              </span>
            </div>

            <form className="area-search" onSubmit={searchArea}>
              <div className="area-search-copy">
                <strong>Explore a Bengaluru area</strong>
                <span>
                  Find road-risk records within 1.5 km of a searched locality or
                  landmark.
                </span>
              </div>
              <div className="area-search-controls">
                <input
                  type="search"
                  value={areaQuery}
                  onChange={(event) => setAreaQuery(event.target.value)}
                  placeholder="Try Indiranagar or Koramangala..."
                  aria-label="Search Bengaluru area"
                />
                <button type="submit" disabled={areaLoading}>
                  {areaLoading ? "Searching..." : "Find area"}
                </button>
                {selectedArea && (
                  <button
                    type="button"
                    className="area-clear-button"
                    onClick={clearAreaSearch}
                  >
                    Show all
                  </button>
                )}
              </div>
              {areaError && (
                <p className="area-search-error" role="alert">
                  {areaError}
                </p>
              )}
              {selectedArea && (
                <div className="area-summary">
                  <div className="area-summary-heading">
                    <strong>{selectedArea.name}</strong>
                    <span>Approx. 1.5 km radius · current filters applied</span>
                  </div>
                  <div className="area-metrics">
                    <div>
                      <span>Road segments</span>
                      <strong>{areaRiskSummary.total.toLocaleString()}</strong>
                    </div>
                    <div>
                      <span>High risk</span>
                      <strong className="area-high">
                        {areaRiskSummary.high.toLocaleString()}
                      </strong>
                    </div>
                    <div>
                      <span>Critical</span>
                      <strong className="area-critical">
                        {areaRiskSummary.critical.toLocaleString()}
                      </strong>
                    </div>
                    <div>
                      <span>Average score</span>
                      <strong>
                        {areaRiskSummary.average === null
                          ? "N/A"
                          : areaRiskSummary.average.toFixed(2)}
                      </strong>
                    </div>
                  </div>
                </div>
              )}
            </form>

            <div className="export-row">
              <button
                type="button"
                className="export-button"
                onClick={() => {
                  const headers = [
                    "Road ID",

                    "Risk Level",

                    "Risk Score",

                    "Prediction Confidence",

                    "Road Type",

                    "Road Length",

                    "Lanes",

                    "Max Speed",

                    "One Way",
                  ];

                  const escapeCsv = (value) =>
                    `"${String(value ?? "").replace(/"/g, '""')}"`;

                  const rows = areaRoads.map((road) => [
                    road.id,

                    road.risk_level,

                    road.risk_score,

                    road.prediction_confidence,

                    road.highway,

                    road.road_length,

                    road.lanes,

                    road.maxspeed,

                    road.oneway,
                  ]);

                  const csv = [headers, ...rows]

                    .map((row) => row.map(escapeCsv).join(","))

                    .join("\r\n");

                  const blob = new Blob(["\uFEFF" + csv], {
                    type: "text/csv;charset=utf-8;",
                  });

                  const url = URL.createObjectURL(blob);

                  const link = document.createElement("a");

                  link.href = url;

                  link.download = `road-risk-${selectedRisk.toLowerCase()}.csv`;

                  link.click();

                  URL.revokeObjectURL(url);
                }}
                disabled={
                  loading || Boolean(error) || filteredRoads.length === 0
                }
              >
                ↓ Export CSV ({filteredRoads.length.toLocaleString()})
              </button>
            </div>

            <div className="road-search">
              <span className="search-icon" aria-hidden="true">
                ⌕
              </span>

              <input
                type="search"
                value={searchTerm}
                onChange={(event) => setSearchTerm(event.target.value)}
                placeholder="Search by road ID, road type, or risk level..."
                aria-label="Search road segments"
              />

              {searchTerm && (
                <button
                  type="button"
                  className="clear-search"
                  onClick={() => setSearchTerm("")}
                  aria-label="Clear search"
                >
                  Clear
                </button>
              )}
            </div>

            <div className="map-filters">
              <span className="filter-label">RISK LEVEL</span>

              {["All", ...RISK_LEVELS].map((level) => (
                <button
                  key={level}
                  type="button"
                  className={`risk-filter ${selectedRisk === level ? "active" : ""}`}
                  onClick={() => selectRisk(level)}
                  aria-pressed={selectedRisk === level}
                >
                  {level !== "All" && (
                    <span
                      className="filter-dot"
                      style={{ backgroundColor: RISK_COLORS[level] }}
                    />
                  )}

                  {level}

                  {level !== "All" && (
                    <span className="filter-count">{riskCounts[level]}</span>
                  )}
                </button>
              ))}
            </div>

            <div className="map-canvas">
              {loading && (
                <div className="map-overlay">
                  <div className="spinner" />

                  <span>Loading road network…</span>
                </div>
              )}

              {!loading && !error && roadsWithGeometry.length === 0 && (
                <div className="map-overlay">
                  No road geometry is available for this filter.
                </div>
              )}

              <MapContainer
                center={[12.9716, 77.5946]}
                zoom={12}
                scrollWheelZoom
                className="risk-map"
              >
                <TileLayer
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                <MapAreaController area={selectedArea} road={selectedRoad} />
                {selectedArea && (
                  <Circle
                    center={[selectedArea.lat, selectedArea.lon]}
                    radius={AREA_RADIUS_METERS}
                    interactive={false}
                    pathOptions={{
                      color: "#60a5fa",
                      fillColor: "#60a5fa",
                      fillOpacity: 0.08,
                      weight: 2,
                      dashArray: "6 6",
                    }}
                  />
                )}

                {roadsWithGeometry.map((road) => {
                  const positions = road.geometry.coordinates.map(
                    ([lng, lat]) => [lat, lng],
                  );

                  return (
                    <Polyline
                      key={road.id}
                      positions={positions}
                      pathOptions={{
                        color: RISK_COLORS[road.risk_level] || "#94a3b8",

                        weight: selectedRoad?.id === road.id ? 7 : 4,

                        opacity: selectedRoad?.id === road.id ? 1 : 0.85,
                      }}
                      eventHandlers={{
                        click: () => setSelectedRoad(road),
                      }}
                      bubblingMouseEvents={false}
                    >
                      <Popup>
                        <div className="map-popup">
                          <strong>Road segment #{road.id}</strong>

                          <span
                            className="popup-level"
                            style={{
                              color: RISK_COLORS[road.risk_level] || "#64748b",
                            }}
                          >
                            {road.risk_level || "Unknown"} risk
                          </span>

                          <div className="popup-score">
                            {road.risk_score == null
                              ? "N/A"
                              : Number(road.risk_score).toFixed(2)}

                            <small> base ML / 100</small>
                          </div>
                          <div className="weather-adjusted-inline">
                            Weather-adjusted:{" "}
                            <strong>
                              {getAdjustedRiskScore(
                                road.risk_score,
                                weatherRiskAdjustment.points,
                              ) == null
                                ? "N/A"
                                : getAdjustedRiskScore(
                                    road.risk_score,
                                    weatherRiskAdjustment.points,
                                  ).toFixed(2)}
                            </strong>{" "}
                            / 100
                            <small>Rule-based estimate</small>
                          </div>

                          <p>Road type: {road.highway || "N/A"}</p>

                          <p>
                            Confidence:{" "}
                            {road.prediction_confidence == null
                              ? "N/A"
                              : `${Number(road.prediction_confidence).toFixed(2)}%`}
                          </p>
                        </div>
                      </Popup>
                    </Polyline>
                  );
                })}
              </MapContainer>
            </div>

            <div className="map-footer">
              <span>RISK LEGEND</span>

              {RISK_LEVELS.map((level) => (
                <span className="legend-item" key={level}>
                  <i style={{ backgroundColor: RISK_COLORS[level] }} />

                  {level}
                </span>
              ))}
            </div>
          </div>

          <aside className="details-column">
            <section className="detail-panel selected-road-panel">
              <div className="panel-header">
                <div>
                  <h3>Road details</h3>

                  <p>Selected segment information</p>
                </div>

                <span className="detail-icon">⌖</span>
              </div>

              {selectedRoad ? (
                <>
                  <div className="selected-road-title">
                    <span>SEGMENT ID</span>

                    <strong>#{selectedRoad.id}</strong>
                  </div>

                  <div className="risk-score-display">
                    <span>Predicted risk score</span>

                    <strong
                      style={{
                        color:
                          RISK_COLORS[selectedRoad.risk_level] || "#94a3b8",
                      }}
                    >
                      {selectedRoad.risk_score == null
                        ? "N/A"
                        : Number(selectedRoad.risk_score).toFixed(2)}

                      <small>/100</small>
                    </strong>

                    <span
                      className="risk-level-badge"
                      style={{
                        color:
                          RISK_COLORS[selectedRoad.risk_level] || "#94a3b8",

                        backgroundColor: `${RISK_COLORS[selectedRoad.risk_level] || "#94a3b8"}18`,
                      }}
                    >
                      {selectedRoad.risk_level || "Unknown"}
                    </span>
                  </div>

                  <div className="weather-adjusted-score-card">
                    <span>Weather-adjusted risk score</span>
                    <strong>
                      {getAdjustedRiskScore(
                        selectedRoad.risk_score,
                        weatherRiskAdjustment.points,
                      ) == null
                        ? "N/A"
                        : getAdjustedRiskScore(
                            selectedRoad.risk_score,
                            weatherRiskAdjustment.points,
                          ).toFixed(2)}
                      <small>/100</small>
                    </strong>
                    <p>
                      Base ML score{" "}
                      {selectedRoad.risk_score == null
                        ? "N/A"
                        : Number(selectedRoad.risk_score).toFixed(2)}{" "}
                      + {weatherRiskAdjustment.points} weather points, capped at
                      100.
                    </p>
                    <small>
                      Rule-based demonstration only; not a validated prediction.
                    </small>
                  </div>

                  <div className="detail-list">
                    <Detail label="Road type" value={selectedRoad.highway} />

                    <Detail
                      label="Road length"
                      value={
                        selectedRoad.road_length == null
                          ? "N/A"
                          : `${Number(selectedRoad.road_length).toFixed(2)} m`
                      }
                    />

                    <Detail label="Lanes" value={selectedRoad.lanes} />

                    <Detail
                      label="Max speed"
                      value={
                        selectedRoad.maxspeed == null
                          ? "N/A"
                          : `${selectedRoad.maxspeed} km/h`
                      }
                    />

                    <Detail
                      label="Model confidence"
                      value={
                        selectedRoad.prediction_confidence == null
                          ? "N/A"
                          : `${Number(selectedRoad.prediction_confidence).toFixed(2)}%`
                      }
                    />

                    <Detail
                      label="One-way"
                      value={
                        selectedRoad.oneway == null
                          ? "N/A"
                          : selectedRoad.oneway
                            ? "Yes"
                            : "No"
                      }
                    />
                  </div>

                  <div className="road-actions">
                    <button
                      type="button"
                      onClick={() => setSelectedRoad(null)}
                      className="road-action-secondary"
                    >
                      Clear selection
                    </button>
                  </div>

                  <div className="risk-explanation">
                    <h4>Risk interpretation</h4>
                    <p>
                      This is a model-generated road-segment risk score, not a
                      confirmed accident probability. Use it as a screening
                      signal alongside local evidence and road-safety expertise.
                    </p>
                    <h4>Suggested safety review</h4>
                    <ul>
                      {(selectedRoad.risk_level === "Critical" ||
                      selectedRoad.risk_level === "High"
                        ? [
                            "Prioritize this segment for an on-site safety assessment.",
                            "Review speed management, visibility, signage, and crossing facilities.",
                            "Check available local crash records before deciding on interventions.",
                          ]
                        : selectedRoad.risk_level === "Medium"
                          ? [
                              "Review road markings, lighting, and pedestrian visibility.",
                              "Compare the model score with local traffic and crash evidence.",
                            ]
                          : [
                              "Maintain routine inspection of signs, markings, and road surface.",
                              "Reassess if new crash or traffic information becomes available.",
                            ]
                      ).map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  </div>
                </>
              ) : (
                <div className="empty-selection">
                  <div className="empty-icon">⌖</div>

                  <strong>No road selected</strong>

                  <p>
                    Click any colored road on the map to see its risk score and
                    road attributes.
                  </p>
                </div>
              )}
            </section>

            <section className="detail-panel distribution-panel">
              <div className="panel-header">
                <div>
                  <h3>Risk distribution</h3>

                  <p>
                    {selectedArea
                      ? `Road records near ${selectedArea.name}`
                      : "All road records by risk category"}
                  </p>
                </div>
              </div>

              <div className="distribution-total">
                <strong>
                  {loading
                    ? "—"
                    : (selectedArea
                        ? areaRoads.length
                        : roads.length
                      ).toLocaleString()}
                </strong>

                <span>
                  {selectedArea ? "matching segments" : "total segments"}
                </span>
              </div>

              <div className="distribution-bars">
                {RISK_LEVELS.map((level) => {
                  const count = (selectedArea ? areaRoads : roads).filter(
                    (road) => road.risk_level === level,
                  ).length;

                  const distributionTotal = selectedArea
                    ? areaRoads.length
                    : roads.length;

                  const percent = distributionTotal
                    ? (count / distributionTotal) * 100
                    : 0;

                  return (
                    <div className="distribution-row" key={level}>
                      <div className="distribution-label">
                        <span>
                          <i style={{ backgroundColor: RISK_COLORS[level] }} />

                          {level}
                        </span>

                        <strong>{count.toLocaleString()}</strong>
                      </div>

                      <div className="bar-track">
                        <div
                          className="bar-fill"
                          style={{
                            width: `${percent}%`,

                            backgroundColor: RISK_COLORS[level],
                          }}
                        />
                      </div>

                      <span className="distribution-percent">
                        {percent.toFixed(1)}%
                      </span>
                    </div>
                  );
                })}
              </div>
            </section>

            <section className="data-note">
              <span className="note-icon">i</span>

              <p>
                Risk levels are model predictions based on available project
                data. They should not be interpreted as guaranteed accident
                probabilities.
              </p>
            </section>
          </aside>
        </section>

        <footer className="dashboard-footer">
          <span>RoadGuard · Road Accident Black Spot Prediction</span>

          <span>FastAPI · PostgreSQL/PostGIS · React Leaflet</span>
        </footer>
      </section>
    </main>
  );
}

function MapAreaController({ area, road }) {
  const map = useMap();

  useEffect(() => {
    if (
      road?.geometry?.type === "LineString" &&
      road.geometry.coordinates?.length >= 2
    ) {
      const bounds = road.geometry.coordinates.map(([lng, lat]) => [lat, lng]);
      map.fitBounds(bounds, { padding: [48, 48], maxZoom: 17, animate: true });
      return;
    }

    if (area) {
      map.setView([area.lat, area.lon], 14, { animate: true });
    } else {
      map.setView([12.9716, 77.5946], 12, { animate: true });
    }
  }, [area, road, map]);

  return null;
}

function Detail({ label, value }) {
  const displayValue =
    value === null || value === undefined || value === "" ? "N/A" : value;

  return (
    <div className="detail-row">
      <span>{label}</span>

      <strong>{displayValue}</strong>
    </div>
  );
}

export default App;
