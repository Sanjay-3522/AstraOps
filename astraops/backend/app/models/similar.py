"""
AstraOps - Similar incidents finder
--------------------------------------
Implements the /similar-events endpoint logic: given a new event
(cause, location, time), find the nearest historical incidents so an
operator can see "why" the system recommended what it did.

Distance combines: geographic distance (haversine, dominant factor),
same cause (bonus), same corridor (bonus).
"""

import numpy as np
import pandas as pd

EARTH_RADIUS_KM = 6371.0


def haversine_km(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(a))


def find_similar(
    history: pd.DataFrame,
    lat: float,
    lon: float,
    event_cause: str,
    corridor: str | None = None,
    top_k: int = 5,
):
    df = history.copy()
    df["distance_km"] = haversine_km(lat, lon, df["latitude"], df["longitude"])

    # Composite similarity score: closer + same cause + same corridor = more similar.
    # Distance is the dominant term (in km), cause/corridor match subtract a bonus
    # so they sort ahead of an equally-close but unrelated incident.
    same_cause_bonus = (df["event_cause"].str.lower() == (event_cause or "").lower()) * 2.0
    same_corridor_bonus = (df["corridor"] == corridor) * 1.0 if corridor else 0.0

    df["similarity_rank_score"] = df["distance_km"] - same_cause_bonus - same_corridor_bonus
    nearest = df.nsmallest(top_k, "similarity_rank_score")

    cols = ["id", "event_cause", "corridor", "police_station", "priority",
            "requires_road_closure", "clearance_time_hr", "status",
            "distance_km", "start_datetime"]
    cols = [c for c in cols if c in nearest.columns]
    result = nearest[cols].copy()
    if "start_datetime" in result.columns:
        result["start_datetime"] = result["start_datetime"].astype(str)
    records = result.to_dict(orient="records")
    # Replace float NaN with JSON-safe None (pandas keeps float dtype on
    # .where(), so the substitution has to happen after to_dict, on the
    # plain Python floats).
    for rec in records:
        for k, v in rec.items():
            if isinstance(v, float) and pd.isna(v):
                rec[k] = None
    return records


if __name__ == "__main__":
    import os
    import sys
    base = os.path.dirname(__file__)
    sys.path.append(os.path.join(base, "..", "data"))
    from clean import load_raw, clean_events
    from features import build_features

    raw = load_raw(os.path.join(base, "..", "..", "data_raw", "astram_events.csv"))
    cleaned = clean_events(raw)
    feats, _ = build_features(cleaned)

    results = find_similar(feats, lat=13.04, lon=77.518, event_cause="vehicle_breakdown",
                            corridor="Tumkur Road", top_k=5)
    for r in results:
        print(r)
