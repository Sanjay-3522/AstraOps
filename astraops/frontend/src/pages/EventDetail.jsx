import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { getIncidents, predictEvent } from "../api/client.js";
import RiskBadge from "../components/RiskBadge.jsx";
import ActionCard from "../components/ActionCard.jsx";

export default function EventDetail() {
  const { id } = useParams();
  const [incident, setIncident] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [recommendation, setRecommendation] = useState(null);
  const [similar, setSimilar] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getIncidents({ limit: 8173 })
      .then((res) => {
        const found = res.incidents.find((i) => i.id === id);
        setIncident(found || null);
        if (found) {
          return predictEvent({
            event_cause: found.event_cause,
            corridor: found.corridor,
            police_station: found.police_station,
            zone: found.zone,
            priority: found.priority,
            event_type: found.event_type,
            latitude: found.latitude,
            longitude: found.longitude,
          });
        }
      })
      .then((predRes) => {
        if (predRes) {
          setPrediction(predRes.prediction);
          setRecommendation(predRes.recommendation);
          setSimilar(predRes.similar_incidents);
        }
      })
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return <div className="p-8 text-gray-500 text-sm">Loading incident details...</div>;
  }

  if (!incident) {
    return (
      <div className="p-8">
        <Link to="/" className="text-sm text-accent flex items-center gap-1 mb-4">
          <ArrowLeft size={14} /> Back to dashboard
        </Link>
        <div className="text-gray-500 text-sm">Incident {id} not found in loaded history.</div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-5xl">
      <Link to="/" className="text-sm text-gray-500 hover:text-accent flex items-center gap-1 mb-6">
        <ArrowLeft size={14} /> Back to dashboard
      </Link>

      <header className="flex items-start justify-between mb-6">
        <div>
          <div className="text-xs font-mono text-gray-500 mb-1">{incident.id}</div>
          <h1 className="font-display font-bold text-2xl capitalize">
            {incident.event_cause?.replace(/_/g, " ")}
          </h1>
          <p className="text-gray-500 text-sm mt-1">
            {incident.corridor} · {incident.police_station} · {incident.zone}
          </p>
        </div>
        {prediction && <RiskBadge score={prediction.impact_score} />}
      </header>

      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-panel border border-border rounded-xl p-4">
          <div className="text-[11px] font-mono text-gray-500 uppercase mb-1">Closure Risk</div>
          <div className="font-display font-bold text-xl">
            {prediction ? `${(prediction.closure_probability * 100).toFixed(0)}%` : "—"}
          </div>
        </div>
        <div className="bg-panel border border-border rounded-xl p-4">
          <div className="text-[11px] font-mono text-gray-500 uppercase mb-1">Est. Clearance</div>
          <div className="font-display font-bold text-xl">
            {prediction ? `${prediction.eta_hours.toFixed(1)} hrs` : "—"}
          </div>
        </div>
        <div className="bg-panel border border-border rounded-xl p-4">
          <div className="text-[11px] font-mono text-gray-500 uppercase mb-1">Status</div>
          <div className="font-display font-bold text-xl capitalize">{incident.status}</div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6 mb-6">
        <ActionCard recommendation={recommendation} />

        <div className="bg-panel border border-border rounded-xl p-5">
          <div className="text-xs font-mono text-gray-500 uppercase tracking-wider mb-4">
            Similar Past Incidents
          </div>
          <div className="space-y-2 max-h-80 overflow-y-auto">
            {similar.map((s) => (
              <div key={s.id} className="border border-border rounded-lg p-3 bg-panel2">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm capitalize font-medium">
                    {s.event_cause?.replace(/_/g, " ")}
                  </span>
                  <span className="text-[10px] font-mono text-gray-500">
                    {s.distance_km.toFixed(2)} km away
                  </span>
                </div>
                <div className="text-[11px] text-gray-500">
                  {s.corridor} · {s.police_station} · {s.status}
                </div>
                <div className="text-[11px] text-gray-500 mt-1">
                  Closure: {s.requires_road_closure ? "Yes" : "No"}
                  {s.clearance_time_hr != null && ` · Cleared in ${s.clearance_time_hr.toFixed(1)}h`}
                </div>
              </div>
            ))}
            {similar.length === 0 && (
              <div className="text-gray-500 text-sm py-4 text-center">No similar incidents found.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
