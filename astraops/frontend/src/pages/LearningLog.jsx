import React, { useEffect, useState } from "react";
import { History, CheckCircle2, XCircle } from "lucide-react";
import { getLearningLog } from "../api/client.js";

export default function LearningLog() {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getLearningLog()
      .then((res) => setEntries(res.entries))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-8 max-w-5xl">
      <header className="mb-8 flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-accent2/15 border border-accent2/30 flex items-center justify-center">
          <History size={18} className="text-accent2" />
        </div>
        <div>
          <h1 className="font-display font-bold text-2xl">Post-Event Learning</h1>
          <p className="text-gray-500 text-sm">
            Predicted vs. actual outcomes recorded after each incident closes.
          </p>
        </div>
      </header>

      {loading && <div className="text-gray-500 text-sm">Loading learning log...</div>}

      {!loading && entries.length === 0 && (
        <div className="bg-panel border border-border rounded-xl p-10 text-center text-gray-500 text-sm">
          No feedback recorded yet. Once incidents are resolved and their outcomes are submitted via
          the <code className="font-mono text-xs">/feedback</code> endpoint, they'll appear here.
        </div>
      )}

      <div className="space-y-3">
        {entries.map((e) => {
          const closurePredictedRight =
            (e.predicted_closure_probability >= 0.5) === e.actual_required_closure;
          return (
            <div key={e.feedback_id} className="bg-panel border border-border rounded-xl p-4">
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-mono text-gray-400">{e.incident_id}</span>
                <span className="text-[11px] text-gray-500">
                  {new Date(e.recorded_at).toLocaleString()}
                </span>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-panel2 rounded-lg p-3">
                  <div className="text-[10px] font-mono text-gray-500 uppercase mb-1">
                    Closure Prediction
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    {closurePredictedRight ? (
                      <CheckCircle2 size={14} className="text-risk-low" />
                    ) : (
                      <XCircle size={14} className="text-risk-critical" />
                    )}
                    Predicted {(e.predicted_closure_probability * 100).toFixed(0)}% ·
                    Actual: {e.actual_required_closure ? "Closed" : "Not closed"}
                  </div>
                </div>
                <div className="bg-panel2 rounded-lg p-3">
                  <div className="text-[10px] font-mono text-gray-500 uppercase mb-1">
                    Clearance Time
                  </div>
                  <div className="text-sm">
                    Predicted {e.predicted_eta_hours?.toFixed?.(1) ?? "—"}h · Actual{" "}
                    {e.actual_clearance_hours?.toFixed?.(1) ?? "—"}h
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
