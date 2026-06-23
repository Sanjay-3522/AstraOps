import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import { getIncidents, getHotspots } from "../api/client.js";
import StatCard from "../components/StatCard.jsx";
import RiskBadge from "../components/RiskBadge.jsx";

export default function Dashboard() {
  const [incidents, setIncidents] = useState([]);
  const [hotspots, setHotspots] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    Promise.all([getIncidents({ limit: 12 }), getHotspots()])
      .then(([incRes, hsRes]) => {
        setIncidents(incRes.incidents);
        setHotspots(hsRes);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const activeCount = incidents.filter((i) => i.status === "active").length;
  const highImpactCount = incidents.filter((i) => i.impact_score >= 50).length;

  if (error) {
    return (
      <div className="p-8">
        <div className="bg-risk-critical/10 border border-risk-critical/30 rounded-xl p-4 text-risk-critical text-sm">
          Couldn't reach the AstraOps API at <code className="font-mono">localhost:8000</code>.
          Make sure the Flask backend is running ({"`"}python3 backend/app/api/server.py{"`"}).
          <div className="text-gray-500 mt-1 text-xs">{error}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-7xl">
      <header className="mb-8">
        <h1 className="font-display font-bold text-2xl mb-1">Command Center</h1>
        <p className="text-gray-500 text-sm">
          Live incident summary and immediate action suggestions for Bengaluru traffic operations.
        </p>
      </header>

      <div className="flex gap-4 mb-8 flex-wrap">
        <StatCard label="Active Incidents" value={loading ? "—" : activeCount} sublabel="currently unresolved" accent />
        <StatCard label="High Impact" value={loading ? "—" : highImpactCount} sublabel="impact score ≥ 50" />
        <StatCard label="Loaded History" value={loading ? "—" : "8,057"} sublabel="historical records" />
        <StatCard
          label="Top Corridor"
          value={loading ? "—" : hotspots?.by_corridor?.[1]?.corridor ?? "—"}
          sublabel="busiest named corridor"
        />
      </div>

      <div className="grid grid-cols-3 gap-6 mb-8">
        <div className="col-span-2 bg-panel border border-border rounded-xl p-5">
          <div className="flex items-center justify-between mb-4">
            <div className="text-xs font-mono text-gray-500 uppercase tracking-wider">
              Recent Incidents
            </div>
            <Link to="/map" className="text-xs text-accent hover:underline">
              View on map →
            </Link>
          </div>
          <div className="space-y-2">
            {loading && <div className="text-gray-500 text-sm py-8 text-center">Loading...</div>}
            {!loading &&
              incidents.map((inc) => (
                <Link
                  key={inc.id}
                  to={`/event/${inc.id}`}
                  className="flex items-center justify-between px-3 py-2.5 rounded-lg hover:bg-panel2 border border-transparent hover:border-border transition-colors group"
                >
                  <div className="flex items-center gap-3">
                    <span
                      className={`w-2 h-2 rounded-full ${
                        inc.status === "active" ? "bg-risk-high" : "bg-gray-600"
                      }`}
                    />
                    <div>
                      <div className="text-sm font-medium capitalize">
                        {inc.event_cause?.replace(/_/g, " ")}
                      </div>
                      <div className="text-[11px] text-gray-500">
                        {inc.corridor} · {inc.police_station}
                      </div>
                    </div>
                  </div>
                  <RiskBadge score={inc.impact_score ?? 0} size="sm" />
                </Link>
              ))}
          </div>
        </div>

        <div className="bg-panel border border-border rounded-xl p-5">
          <div className="text-xs font-mono text-gray-500 uppercase tracking-wider mb-4">
            Closure Rate by Cause
          </div>
          {hotspots && (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart
                data={hotspots.by_cause.slice(0, 8)}
                layout="vertical"
                margin={{ left: 0, right: 10, top: 0, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#26303F" horizontal={false} />
                <XAxis type="number" stroke="#5A6577" fontSize={11} />
                <YAxis
                  type="category"
                  dataKey="event_cause"
                  stroke="#5A6577"
                  fontSize={10}
                  width={90}
                  tickFormatter={(v) => v.replace(/_/g, " ")}
                />
                <Tooltip
                  contentStyle={{ background: "#121821", border: "1px solid #26303F", borderRadius: 8, fontSize: 12 }}
                  formatter={(v) => [`${v}%`, "Closure rate"]}
                />
                <Bar dataKey="closure_rate" fill="#FF6A3D" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      <div className="bg-panel border border-border rounded-xl p-5">
        <div className="text-xs font-mono text-gray-500 uppercase tracking-wider mb-4">
          Top Corridors by Incident Volume
        </div>
        {hotspots && (
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={hotspots.by_corridor.slice(0, 10)} margin={{ left: 0, right: 10, top: 10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#26303F" vertical={false} />
              <XAxis dataKey="corridor" stroke="#5A6577" fontSize={10} angle={-25} textAnchor="end" height={60} />
              <YAxis stroke="#5A6577" fontSize={11} />
              <Tooltip
                contentStyle={{ background: "#121821", border: "1px solid #26303F", borderRadius: 8, fontSize: 12 }}
              />
              <Bar dataKey="incident_count" fill="#2DD4BF" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
