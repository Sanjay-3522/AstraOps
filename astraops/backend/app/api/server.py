"""
AstraOps - API layer (Flask)
------------------------------
Exposes the endpoints called out in the blueprint:
  GET  /api/health
  GET  /api/incidents            - list/filter incidents (for map + dashboard)
  GET  /api/hotspots             - corridor / zone / station hotspot summary
  POST /predict/event            - score an incoming event
  POST /simulate                 - what-if planning for a proposed event
  GET  /similar-events           - nearest past incidents for explanation
  POST /feedback                 - record predicted-vs-actual outcome (learning loop)
  GET  /api/learning-log         - list recorded feedback entries

Note: the blueprint suggests FastAPI; this environment doesn't have
network access to install it, so the same API contract is implemented
in Flask (already available, zero extra installs). Routes, payloads,
and behavior match what FastAPI would have served -- swapping
frameworks later is a thin layer change, not a redesign.
"""

import os
import sys
import json
import uuid
from datetime import datetime, timezone

import pandas as pd
from flask import Flask, request, jsonify

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "data"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "models"))

from clean import load_raw, clean_events
from features import build_features
from inference import InferenceService
from recommend import recommend
from similar import find_similar

BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..")
RAW_CSV = os.path.join(BASE_DIR, "data_raw", "astram_events.csv")
FEEDBACK_LOG = os.path.join(BASE_DIR, "data_processed", "feedback_log.jsonl")

app = Flask(__name__)


# ---------------------------------------------------------------------------
# Startup: load history once, build features once, load trained models once.
# ---------------------------------------------------------------------------
print("Loading and preparing historical data...")
_raw = load_raw(RAW_CSV)
_cleaned = clean_events(_raw)
HISTORY, _LOOKUP = build_features(_cleaned)
HISTORY = HISTORY.copy()
HISTORY["start_datetime_iso"] = HISTORY["start_datetime"].astype(str)

print("Loading trained models...")
INFER = InferenceService()
print(f"Ready. {len(HISTORY)} historical rows loaded.")


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "rows_loaded": int(len(HISTORY))})


@app.route("/api/incidents", methods=["GET"])
def list_incidents():
    """Returns incidents for the map/list view. Supports optional filters:
    ?status=active&event_cause=vehicle_breakdown&corridor=Mysore%20Road&limit=200
    """
    df = HISTORY

    status = request.args.get("status")
    if status:
        df = df[df["status"] == status]

    cause = request.args.get("event_cause")
    if cause:
        df = df[df["event_cause"].str.lower() == cause.lower()]

    corridor = request.args.get("corridor")
    if corridor:
        df = df[df["corridor"] == corridor]

    limit = int(request.args.get("limit", 500))
    df = df.sort_values("start_datetime", ascending=False).head(limit)

    cols = [
        "id", "event_type", "event_cause", "latitude", "longitude",
        "corridor", "police_station", "zone", "priority", "status",
        "requires_road_closure", "impact_score", "hotspot_score",
        "start_datetime_iso",
    ]
    cols = [c for c in cols if c in df.columns]
    records = df[cols].to_dict(orient="records")
    for rec in records:
        for k, v in rec.items():
            if isinstance(v, float) and pd.isna(v):
                rec[k] = None
    return jsonify({"count": len(records), "incidents": records})


@app.route("/api/hotspots", methods=["GET"])
def hotspots():
    """Aggregated hotspot view by corridor / zone / police_station,
    used to drive the dashboard's hotspot charts and map clusters."""
    def agg(col):
        g = HISTORY.groupby(col).agg(
            incident_count=("id", "count"),
            closure_rate=("requires_road_closure", "mean"),
            avg_impact=("impact_score", "mean"),
        ).reset_index()
        g["closure_rate"] = (g["closure_rate"] * 100).round(1)
        g["avg_impact"] = g["avg_impact"].round(1)
        return g.sort_values("incident_count", ascending=False).head(15).to_dict(orient="records")

    return jsonify({
        "by_corridor": agg("corridor"),
        "by_zone": agg("zone"),
        "by_police_station": agg("police_station"),
        "by_cause": agg("event_cause"),
    })


@app.route("/predict/event", methods=["POST"])
def predict_event():
    """Body: { event_cause, corridor, police_station, zone, priority,
    event_type, latitude, longitude, start_datetime (optional) }
    Returns: impact score, closure risk, ETA, and recommendation card."""
    payload = request.get_json(force=True) or {}

    required = ["event_cause", "latitude", "longitude"]
    missing = [f for f in required if f not in payload]
    if missing:
        return jsonify({"error": f"Missing required fields: {missing}"}), 400

    prediction = INFER.predict(payload)
    card = recommend(
        event_cause=prediction["resolved_inputs"]["event_cause"],
        priority=prediction["resolved_inputs"]["priority"],
        impact_score=prediction["impact_score"],
        closure_probability=prediction["closure_probability"],
        hotspot_score=prediction["hotspot_score"],
        eta_hours=prediction["eta_hours"],
    )

    similar = find_similar(
        HISTORY, lat=payload["latitude"], lon=payload["longitude"],
        event_cause=payload["event_cause"], corridor=payload.get("corridor"), top_k=5,
    )

    return jsonify({
        "prediction": prediction,
        "recommendation": {
            "manpower": card.manpower,
            "barricade_level": card.barricade_level,
            "diversion_severity": card.diversion_severity,
            "escalation_level": card.escalation_level,
            "rationale": card.rationale,
        },
        "similar_incidents": similar,
    })


@app.route("/simulate", methods=["POST"])
def simulate():
    """Same contract as /predict/event -- used by the planning simulator
    screen for a hypothetical/proposed event rather than a live incident."""
    return predict_event()


@app.route("/similar-events", methods=["GET"])
def similar_events():
    lat = float(request.args.get("lat"))
    lon = float(request.args.get("lon"))
    cause = request.args.get("event_cause", "")
    corridor = request.args.get("corridor")
    top_k = int(request.args.get("top_k", 5))

    results = find_similar(HISTORY, lat=lat, lon=lon, event_cause=cause,
                            corridor=corridor, top_k=top_k)
    return jsonify({"similar_incidents": results})


@app.route("/feedback", methods=["POST"])
def feedback():
    """Post-event learning loop (blueprint step 7): record predicted vs
    actual closure outcome and clearance time for a resolved incident.
    Appended to a JSONL log -- in a production system this would write
    to the database table backing the post-event learning screen."""
    payload = request.get_json(force=True) or {}
    required = ["incident_id", "predicted_closure_probability", "actual_required_closure"]
    missing = [f for f in required if f not in payload]
    if missing:
        return jsonify({"error": f"Missing required fields: {missing}"}), 400

    entry = {
        "feedback_id": str(uuid.uuid4()),
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        **payload,
    }
    os.makedirs(os.path.dirname(FEEDBACK_LOG), exist_ok=True)
    with open(FEEDBACK_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")

    return jsonify({"status": "recorded", "feedback_id": entry["feedback_id"]})


@app.route("/api/learning-log", methods=["GET"])
def learning_log():
    if not os.path.exists(FEEDBACK_LOG):
        return jsonify({"entries": []})
    entries = []
    with open(FEEDBACK_LOG) as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return jsonify({"entries": entries[::-1]})  # most recent first


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
