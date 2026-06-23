import React from "react";
import { Users, ShieldAlert, Route as RouteIcon, ArrowUpCircle } from "lucide-react";

const LEVEL_COLORS = {
  none: "text-gray-500",
  light: "text-risk-low",
  standard: "text-risk-medium",
  heavy: "text-risk-high",
  local_reroute: "text-risk-low",
  corridor_diversion: "text-risk-medium",
  full_closure_diversion: "text-risk-critical",
  field_team: "text-gray-400",
  shift_supervisor: "text-risk-low",
  traffic_control_room: "text-risk-medium",
  senior_command: "text-risk-critical",
};

function prettify(s) {
  return s.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function ActionCard({ recommendation }) {
  if (!recommendation) return null;
  const { manpower, barricade_level, diversion_severity, escalation_level, rationale } = recommendation;

  const items = [
    { icon: Users, label: "Manpower", value: `${manpower} personnel`, colorKey: null },
    { icon: ShieldAlert, label: "Barricading", value: prettify(barricade_level), colorKey: barricade_level },
    { icon: RouteIcon, label: "Diversion", value: prettify(diversion_severity), colorKey: diversion_severity },
    { icon: ArrowUpCircle, label: "Escalate to", value: prettify(escalation_level), colorKey: escalation_level },
  ];

  return (
    <div className="bg-panel border border-border rounded-xl p-5">
      <div className="text-xs font-mono text-gray-500 uppercase tracking-wider mb-4">
        Recommended Response
      </div>
      <div className="grid grid-cols-2 gap-4 mb-4">
        {items.map(({ icon: Icon, label, value, colorKey }) => (
          <div key={label} className="bg-panel2 border border-border rounded-lg p-3">
            <div className="flex items-center gap-2 text-gray-500 text-[11px] mb-1.5">
              <Icon size={13} />
              {label}
            </div>
            <div
              className={`font-display font-semibold text-sm ${
                colorKey ? LEVEL_COLORS[colorKey] || "text-white" : "text-white"
              }`}
            >
              {value}
            </div>
          </div>
        ))}
      </div>

      {rationale && rationale.length > 0 && (
        <div className="pt-3 border-t border-border">
          <div className="text-[10px] font-mono text-gray-500 uppercase tracking-wider mb-2">
            Why this recommendation
          </div>
          <ul className="space-y-1.5">
            {rationale.map((r, i) => (
              <li key={i} className="text-xs text-gray-400 flex gap-2 leading-relaxed">
                <span className="text-accent mt-0.5">›</span>
                {r}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
