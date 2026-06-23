import React from "react";
import { Routes, Route, NavLink } from "react-router-dom";
import { LayoutGrid, Map, Radio, FlaskConical, History } from "lucide-react";
import Dashboard from "./pages/Dashboard.jsx";
import MapView from "./pages/MapView.jsx";
import EventDetail from "./pages/EventDetail.jsx";
import Simulator from "./pages/Simulator.jsx";
import LearningLog from "./pages/LearningLog.jsx";

const NAV_ITEMS = [
  { to: "/", label: "Dashboard", icon: LayoutGrid },
  { to: "/map", label: "Map View", icon: Map },
  { to: "/simulator", label: "Planning Simulator", icon: FlaskConical },
  { to: "/learning", label: "Post-Event Learning", icon: History },
];

export default function App() {
  return (
    <div className="flex h-screen w-screen overflow-hidden bg-ink text-[#E6EAF0]">
      <aside className="w-60 shrink-0 border-r border-border bg-panel flex flex-col">
        <div className="px-5 py-5 border-b border-border">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-md bg-accent flex items-center justify-center">
              <Radio size={16} className="text-ink" strokeWidth={2.5} />
            </div>
            <div>
              <div className="font-display font-semibold text-sm tracking-wide">ASTRAOPS</div>
              <div className="text-[10px] text-gray-500 font-mono">EVENT RESPONSE INTEL</div>
            </div>
          </div>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1">
          {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                  isActive
                    ? "bg-panel2 text-white border border-border"
                    : "text-gray-400 hover:text-gray-200 hover:bg-panel2/50"
                }`
              }
            >
              <Icon size={16} />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="px-5 py-4 border-t border-border text-[10px] text-gray-500 font-mono leading-relaxed">
          Bengaluru Traffic Ops
          <br />
          Prototype build · v0.1
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/map" element={<MapView />} />
          <Route path="/event/:id" element={<EventDetail />} />
          <Route path="/simulator" element={<Simulator />} />
          <Route path="/learning" element={<LearningLog />} />
        </Routes>
      </main>
    </div>
  );
}
