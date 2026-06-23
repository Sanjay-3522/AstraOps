import React from "react";

const BANDS = [
  { max: 25, label: "Low", className: "bg-risk-low/15 text-risk-low border-risk-low/30" },
  { max: 50, label: "Medium", className: "bg-risk-medium/15 text-risk-medium border-risk-medium/30" },
  { max: 75, label: "High", className: "bg-risk-high/15 text-risk-high border-risk-high/30" },
  { max: 101, label: "Critical", className: "bg-risk-critical/15 text-risk-critical border-risk-critical/30" },
];

export default function RiskBadge({ score, size = "md" }) {
  const band = BANDS.find((b) => score <= b.max) || BANDS[BANDS.length - 1];
  const sizeClass = size === "sm" ? "text-[10px] px-2 py-0.5" : "text-xs px-2.5 py-1";

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border font-mono font-medium ${sizeClass} ${band.className}`}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-current" />
      {band.label} · {score.toFixed(0)}
    </span>
  );
}
