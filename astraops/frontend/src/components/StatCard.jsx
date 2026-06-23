import React from "react";

export default function StatCard({ label, value, suffix, sublabel, accent = false }) {
  return (
    <div className="bg-panel border border-border rounded-xl p-4 flex-1 min-w-[160px]">
      <div className="text-[11px] font-mono text-gray-500 uppercase tracking-wider mb-2">
        {label}
      </div>
      <div className="flex items-baseline gap-1">
        <span className={`font-display font-bold text-2xl ${accent ? "text-accent" : "text-white"}`}>
          {value}
        </span>
        {suffix && <span className="text-gray-500 text-sm">{suffix}</span>}
      </div>
      {sublabel && <div className="text-[11px] text-gray-500 mt-1">{sublabel}</div>}
    </div>
  );
}
