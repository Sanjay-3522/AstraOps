import React, { useState } from "react";
import { FlaskConical, MapPin } from "lucide-react";
import { simulateEvent } from "../api/client.js";
import RiskBadge from "../components/RiskBadge.jsx";
import ActionCard from "../components/ActionCard.jsx";

const CAUSES = [
  "vehicle_breakdown", "others", "pot_holes", "construction", "water_logging",
  "accident", "tree_fall", "road_conditions", "congestion", "public_event",
  "procession", "vip_movement", "protest",
];

const CORRIDORS = [
  "Non-corridor", "Mysore Road", "Bellary Road 1", "Tumkur Road", "Bellary Road 2",
  "Hosur Road", "ORR North 1", "Old Madras Road", "Magadi Road", "ORR East 1",
];

const ZONES = [
  "Central Zone 1", "Central Zone 2", "North Zone 1", "North Zone 2",
  "South Zone 1", "South Zone 2", "East Zone 1", "East Zone 2",
  "West Zone 1", "West Zone 2",
];

const DEFAULT_FORM = {
  event_cause: "public_event",
  corridor: "Mysore Road",
  police_station: "Yelahanka",
  zone: "North Zone 1",
  priority: "High",
  event_type: "planned",
  latitude: 13.04,
  longitude: 77.518,
};

export default function Simulator() {
  const [form, setForm] = useState(DEFAULT_FORM);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const update = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }));

  const runSimulation = async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = {
        ...form,
        latitude: parseFloat(form.latitude),
        longitude: parseFloat(form.longitude),
      };
      const res = await simulateEvent(payload);
      setResult(res);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-6xl">
      <header className="mb-8 flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-accent/15 border border-accent/30 flex items-center justify-center">
          <FlaskConical size={18} className="text-accent" />
        </div>
        <div>
          <h1 className="font-display font-bold text-2xl">Planning Simulator</h1>
          <p className="text-gray-500 text-sm">
            Enter a proposed event and see predicted impact before it happens.
          </p>
        </div>
      </header>

      <div className="grid grid-cols-5 gap-6">
        <div className="col-span-2 bg-panel border border-border rounded-xl p-5 space-y-4">
          <div>
            <label className="text-[11px] font-mono text-gray-500 uppercase mb-1.5 block">
              Event Cause
            </label>
            <select
              value={form.event_cause}
              onChange={update("event_cause")}
              className="w-full bg-panel2 border border-border rounded-lg px-3 py-2 text-sm"
            >
              {CAUSES.map((c) => (
                <option key={c} value={c}>{c.replace(/_/g, " ")}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-[11px] font-mono text-gray-500 uppercase mb-1.5 block">
              Event Type
            </label>
            <div className="flex gap-2">
              {["planned", "unplanned"].map((t) => (
                <button
                  key={t}
                  onClick={() => setForm((f) => ({ ...f, event_type: t }))}
                  className={`flex-1 py-2 rounded-lg text-sm capitalize border ${
                    form.event_type === t
                      ? "bg-accent/15 border-accent/40 text-accent"
                      : "bg-panel2 border-border text-gray-400"
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="text-[11px] font-mono text-gray-500 uppercase mb-1.5 block">
              Priority
            </label>
            <div className="flex gap-2">
              {["Low", "High"].map((p) => (
                <button
                  key={p}
                  onClick={() => setForm((f) => ({ ...f, priority: p }))}
                  className={`flex-1 py-2 rounded-lg text-sm border ${
                    form.priority === p
                      ? "bg-accent/15 border-accent/40 text-accent"
                      : "bg-panel2 border-border text-gray-400"
                  }`}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="text-[11px] font-mono text-gray-500 uppercase mb-1.5 block">
              Corridor
            </label>
            <select
              value={form.corridor}
              onChange={update("corridor")}
              className="w-full bg-panel2 border border-border rounded-lg px-3 py-2 text-sm"
            >
              {CORRIDORS.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-[11px] font-mono text-gray-500 uppercase mb-1.5 block">
              Zone
            </label>
            <select
              value={form.zone}
              onChange={update("zone")}
              className="w-full bg-panel2 border border-border rounded-lg px-3 py-2 text-sm"
            >
              {ZONES.map((z) => (
                <option key={z} value={z}>{z}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-[11px] font-mono text-gray-500 uppercase mb-1.5 block">
              Police Station
            </label>
            <input
              type="text"
              value={form.police_station}
              onChange={update("police_station")}
              className="w-full bg-panel2 border border-border rounded-lg px-3 py-2 text-sm"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-[11px] font-mono text-gray-500 uppercase mb-1.5 flex items-center gap-1">
                <MapPin size={11} /> Latitude
              </label>
              <input
                type="number"
                step="0.0001"
                value={form.latitude}
                onChange={update("latitude")}
                className="w-full bg-panel2 border border-border rounded-lg px-3 py-2 text-sm font-mono"
              />
            </div>
            <div>
              <label className="text-[11px] font-mono text-gray-500 uppercase mb-1.5 block">
                Longitude
              </label>
              <input
                type="number"
                step="0.0001"
                value={form.longitude}
                onChange={update("longitude")}
                className="w-full bg-panel2 border border-border rounded-lg px-3 py-2 text-sm font-mono"
              />
            </div>
          </div>

          <button
            onClick={runSimulation}
            disabled={loading}
            className="w-full bg-accent text-ink font-display font-semibold py-2.5 rounded-lg mt-2 hover:opacity-90 transition-opacity disabled:opacity-50"
          >
            {loading ? "Running simulation..." : "Run Simulation"}
          </button>

          {error && <div className="text-risk-critical text-xs">{error}</div>}
        </div>

        <div className="col-span-3 space-y-4">
          {!result && (
            <div className="bg-panel border border-border rounded-xl p-10 text-center text-gray-500 text-sm">
              Configure a proposed event on the left and run the simulation to see predicted impact,
              closure risk, and recommended response.
            </div>
          )}

          {result && (
            <>
              <div className="bg-panel border border-border rounded-xl p-5 flex items-center justify-between">
                <div>
                  <div className="text-[11px] font-mono text-gray-500 uppercase mb-1">
                    Predicted Impact
                  </div>
                  <RiskBadge score={result.prediction.impact_score} />
                </div>
                <div className="text-right">
                  <div className="text-[11px] font-mono text-gray-500 uppercase mb-1">
                    Closure Probability
                  </div>
                  <div className="font-display font-bold text-xl">
                    {(result.prediction.closure_probability * 100).toFixed(0)}%
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-[11px] font-mono text-gray-500 uppercase mb-1">
                    Est. Clearance
                  </div>
                  <div className="font-display font-bold text-xl">
                    {result.prediction.eta_hours.toFixed(1)} hrs
                  </div>
                </div>
              </div>

              <ActionCard recommendation={result.recommendation} />

              <div className="bg-panel border border-border rounded-xl p-5">
                <div className="text-xs font-mono text-gray-500 uppercase tracking-wider mb-3">
                  Similar Historical Incidents
                </div>
                <div className="space-y-2">
                  {result.similar_incidents.slice(0, 4).map((s) => (
                    <div
                      key={s.id}
                      className="flex items-center justify-between text-sm py-2 px-3 bg-panel2 rounded-lg"
                    >
                      <span className="capitalize text-gray-300">
                        {s.event_cause?.replace(/_/g, " ")} · {s.corridor}
                      </span>
                      <span className="text-[11px] font-mono text-gray-500">
                        {s.distance_km.toFixed(2)} km
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
