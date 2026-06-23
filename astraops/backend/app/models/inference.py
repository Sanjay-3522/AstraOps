"""
AstraOps - Advanced Multi-Model Ensemble Inference Service (Fixed Scalars)
-------------------------------------------------------------------------
Scores live operational traffic incidents using your trained premium ensemble.
Guarantees clean string extraction for lookup tables to prevent unhashable errors.
"""

import numpy as np
import pandas as pd
import joblib
import json
from datetime import datetime, timezone
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "data"))
from features import RUSH_HOURS  

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "saved_models")
CATEGORICAL_FEATURES = [
    "event_cause", "corridor", "police_station", "zone", "priority", "event_type",
    "cause_X_corridor", "rush_X_zone", "priority_X_cause", "rush_X_weekday", "geo_sector"
]
NUMERIC_FEATURES = [
    "hour", "weekday", "is_weekend", "is_rush_hour", "month",
    "hour_sin", "hour_cos", "weekday_sin", "weekday_cos",
    "corridor_freq", "station_freq", "zone_freq", "cause_freq", "geo_freq",
    "cause_corridor_freq", "rush_zone_freq", "priority_cause_freq",
    "cause_closure_rate", "corridor_closure_rate", "geo_closure_rate",
    "cause_corridor_closure_rate", "priority_cause_closure_rate", "hotspot_score"
]


class InferenceService:
    def __init__(self, model_dir: str = MODEL_DIR):
        self.model_dir = model_dir
        
        print("[AstraOps Engine] Initializing Stacking Inference Stack...")
        self.clf = joblib.load(f"{model_dir}/closure_classifier.joblib")
        self.clf_encoder = joblib.load(f"{model_dir}/closure_encoder.joblib")
        self.reg = joblib.load(f"{model_dir}/clearance_regressor.joblib")
        self.reg_encoder = joblib.load(f"{model_dir}/clearance_encoder.joblib")
        self.lookup = joblib.load(f"{model_dir}/lookup_tables.joblib")
        
        self.threshold = 0.5  
        metrics_path = f"{model_dir}/metrics.json"
        if os.path.exists(metrics_path):
            try:
                with open(metrics_path) as f:
                    data = json.load(f)
                    self.threshold = data["closure_classifier"].get("optimal_threshold", 0.5)
            except Exception:
                pass

    def _build_row(self, event: dict):
        now = datetime.now(timezone.utc)
        
        lat = float(event.get("latitude", 12.97))
        lon = float(event.get("longitude", 77.59))
        lat_grid = int(round(lat * 1000))
        lon_grid = int(round(lon * 1000))
        geo_sector = f"{lat_grid}_{lon_grid}"

        hour = int(event.get("hour", now.hour))
        weekday = int(event.get("weekday", now.weekday()))
        is_rush_hour = 1 if hour in RUSH_HOURS else 0

        row = pd.DataFrame([{
            "event_cause": event.get("event_cause", "vehicle_breakdown"),
            "corridor": event.get("corridor", "Non-corridor"),
            "police_station": event.get("police_station", "Unknown"),
            "zone": event.get("zone", "Unknown"),
            "priority": event.get("priority", "Low"),
            "event_type": event.get("event_type", "unplanned"),
            "geo_sector": geo_sector,
            "hour": hour,
            "weekday": weekday,
            "is_weekend": 1 if weekday >= 5 else 0,
            "is_rush_hour": is_rush_hour,
            "month": int(event.get("month", now.month)),
            "hour_sin": np.sin(2 * np.pi * hour / 24.0),
            "hour_cos": np.cos(2 * np.pi * hour / 24.0),
            "weekday_sin": np.sin(2 * np.pi * weekday / 7.0),
            "weekday_cos": np.cos(2 * np.pi * weekday / 7.0),
            "rush_X_weekday": f"{is_rush_hour}_{weekday}"
        }])

        # FIX: Extract raw strings from the DataFrame row BEFORE passing them into lookup keys
        c = str(row["corridor"].iloc[0])
        s = str(row["police_station"].iloc[0])
        z = str(row["zone"].iloc[0])
        cause = str(row["event_cause"].iloc[0])
        g = str(row["geo_sector"].iloc[0])

        row["corridor_freq"] = self.lookup["corridor_freq"].get(c, 0.0)
        row["station_freq"] = self.lookup["station_freq"].get(s, 0.0)
        row["zone_freq"] = self.lookup["zone_freq"].get(z, 0.0)
        row["cause_freq"] = self.lookup["cause_freq"].get(cause, 0.0)
        row["geo_freq"] = self.lookup["geo_freq"].get(g, 0.0)

        df_cx_corr = f"{cause}_{c}"
        df_rx_zone = f"{is_rush_hour}_{z}"
        df_px_cause = f"{row['priority'].iloc[0]}_{cause}"

        row["cause_X_corridor"] = df_cx_corr
        row["rush_X_zone"] = df_rx_zone
        row["priority_X_cause"] = df_px_cause

        row["cause_corridor_freq"] = self.lookup["cause_corridor_freq"].get(df_cx_corr, 0.0)
        row["rush_zone_freq"] = self.lookup["rush_zone_freq"].get(df_rx_zone, 0.0)
        row["priority_cause_freq"] = self.lookup["priority_cause_freq"].get(df_px_cause, 0.0)

        row["cause_closure_rate"] = self.lookup["cause_closure_rate"].get(cause, 0.0)
        row["corridor_closure_rate"] = self.lookup["corridor_closure_rate"].get(c, 0.0)
        row["geo_closure_rate"] = self.lookup["geo_closure_rate"].get(g, 0.0)
        row["cause_corridor_closure_rate"] = self.lookup["cause_corridor_closure_rate"].get(df_cx_corr, 0.0)
        row["priority_cause_closure_rate"] = self.lookup["priority_cause_closure_rate"].get(df_px_cause, 0.0)

        alpha, beta, gamma = 0.4, 0.4, 0.2
        raw_hotspot = (
            alpha * row["cause_corridor_closure_rate"].iloc[0] + 
            beta * row["geo_closure_rate"].iloc[0] + 
            gamma * row["priority_cause_closure_rate"].iloc[0]
        )
        
        max_val = self.lookup.get("hotspot_max_ref", 1.0)
        row["hotspot_score"] = round((raw_hotspot / max_val * 10.0), 2)
        
        priority_comp = 2.0 if str(event.get("priority")).upper() == "HIGH" else 1.0
        row["impact_score"] = round(((raw_hotspot / max_val) * priority_comp * 100.0), 1)

        return row

    def predict(self, event: dict) -> dict:
        row = self._build_row(event)

        # 1. Classification
        X_clf = row[CATEGORICAL_FEATURES + NUMERIC_FEATURES].copy()
        X_clf[CATEGORICAL_FEATURES] = self.clf_encoder.transform(X_clf[CATEGORICAL_FEATURES])
        closure_prob = float(self.clf.predict_proba(X_clf)[0, 1])
        
        will_close_bool = bool(closure_prob >= self.threshold)
        will_close_int = 1 if will_close_bool else 0

        # 2. Regression
        X_reg = row[CATEGORICAL_FEATURES + NUMERIC_FEATURES].copy()
        X_reg[CATEGORICAL_FEATURES] = self.reg_encoder.transform(X_reg[CATEGORICAL_FEATURES])
        eta_log = self.reg.predict(X_reg)[0]
        eta_hours = float(np.expm1(eta_log))

        # DIRECT FRONTEND COMPATIBILITY MAPPING
        return {
            "impact_score": float(row["impact_score"].values[0]),
            "closure_probability": round(float(closure_prob), 4),
            "requires_road_closure_prediction": "yes" if will_close_bool else "no",
            "eta_hours": round(float(eta_hours), 2),
            "hotspot_score": float(row["hotspot_score"].values[0]),
            
            "requires_road_closure": will_close_bool,
            "requires_road_closure_int": will_close_int,
            "clearance_time_hours": round(float(eta_hours), 2),
            "predicted_hours": round(float(eta_hours), 2),
            "risk_score": float(row["impact_score"].values[0]),
            
            "resolved_inputs": event
        }