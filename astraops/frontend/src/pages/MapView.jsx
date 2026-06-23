import React, { useEffect, useMemo, useState } from "react";
import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet";
import { useNavigate } from "react-router-dom";
import { getIncidents } from "../api/client.js";

const BENGALURU_CENTER = [12.9716, 77.5946];

function riskColor(score) {
  if (score >= 75) return "#E5484D";
  if (score >= 50) return "#FF6A3D";
  if (score >= 25) return "#F5A623";
  return "#2DD4BF";
}

export default function MapView() {
  const [incidents, setIncidents] = useState([]);
  const [causeFilter, setCauseFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    setLoading(true);
    const params = { limit: 600 };
    if (causeFilter) params.event_cause = causeFilter;
    getIncidents(params)
      .then((res) => setIncidents(res.incidents))
      .finally(() => setLoading(false));
  }, [causeFilter]);

  const causes = useMemo(
    () => [
      "vehicle_breakdown", "others", "pot_holes", "construction",
      "water_logging", "accident", "tree_fall", "road_conditions",
      "congestion", "public_event", "procession", "vip_movement", "protest",
    ],
    []
  );

  return (
    <div className="h-full flex flex-col">
      <div className="px-6 py-4 border-b border-border bg-panel flex items-center justify-between">
        <div>
          <h1 className="font-display font-bold text-lg">Live Map</h1>
          <p className="text-xs text-gray-500">{incidents.length} incidents shown {loading && "· loading..."}</p>
        </div>
        <select
          value={causeFilter}
          onChange={(e) => setCauseFilter(e.target.value)}
          className="bg-panel2 border border-border rounded-lg px-3 py-2 text-sm text-gray-300"
        >
          <option value="">All causes</option>
          {causes.map((c) => (
            <option key={c} value={c}>
              {c.replace(/_/g, " ")}
            </option>
          ))}
        </select>
      </div>

      <div className="flex-1">
        <MapContainer center={BENGALURU_CENTER} zoom={11} style={{ height: "100%", width: "100%" }}>
          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            attribution='&copy; <a href="https://carto.com/attributions">CARTO</a>'
          />
          {incidents.map((inc) => (
            <CircleMarker
              key={inc.id}
              center={[inc.latitude, inc.longitude]}
              radius={6}
              pathOptions={{
                color: riskColor(inc.impact_score ?? 0),
                fillColor: riskColor(inc.impact_score ?? 0),
                fillOpacity: 0.6,
                weight: 1.5,
              }}
              eventHandlers={{ click: () => navigate(`/event/${inc.id}`) }}
            >
              <Popup>
                <div className="font-mono text-xs">
                  <div className="font-semibold capitalize mb-1">
                    {inc.event_cause?.replace(/_/g, " ")}
                  </div>
                  <div>{inc.corridor}</div>
                  <div>{inc.police_station}</div>
                  <div className="mt-1">Impact: {inc.impact_score?.toFixed(0)}/100</div>
                  <div>Status: {inc.status}</div>
                </div>
              </Popup>
            </CircleMarker>
          ))}
        </MapContainer>
      </div>
    </div>
  );
}
