"""
AstraOps - Production Feature Engineering Module
--------------------------------------------------
Legitimately builds geometric coordinate sectors, continuous cyclical 
time transformations, and target-risk smoothing equations.
"""

import numpy as np
import pandas as pd

RUSH_HOURS = set([8, 9, 10, 18, 19, 20])  # Peak operational hours


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    dt = df["start_datetime"]

    df["hour"] = dt.dt.hour
    df["weekday"] = dt.dt.dayofweek  
    df["is_weekend"] = df["weekday"].isin([5, 6]).astype(int)
    df["is_rush_hour"] = df["hour"].isin(RUSH_HOURS).astype(int)
    df["month"] = dt.dt.month

    # CYCLICAL TIME EMBEDDINGS (Sine/Cosine Waves)
    df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24.0)
    df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24.0)
    df["weekday_sin"] = np.sin(2 * np.pi * df["weekday"] / 7.0)
    df["weekday_cos"] = np.cos(2 * np.pi * df["weekday"] / 7.0)

    # Context interactions & Continuous Timeline Index
    df["rush_X_weekday"] = df["is_rush_hour"].astype(str) + "_" + df["weekday"].astype(str)
    df["time_index"] = df["weekday"] * 24 + df["hour"]  # Continuous 168-hour tracking axis
    return df


def add_spatial_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    
    # Safely convert and clean coordinate inputs
    lat = pd.to_numeric(df["latitude"], errors='coerce').fillna(12.97)
    lon = pd.to_numeric(df["longitude"], errors='coerce').fillna(77.59)
    
    # Establish high-resolution geographic quadrant tracking (110-meter accuracy blocks)
    df["lat_grid"] = (lat * 1000).round().astype(int)
    df["lon_grid"] = (lon * 1000).round().astype(int)
    df["geo_sector"] = df["lat_grid"].astype(str) + "_" + df["lon_grid"].astype(str)
    
    return df


def add_frequency_features(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    df = df.copy()
    
    corridor_counts = df["corridor"].value_counts(normalize=True).to_dict()
    station_counts = df["police_station"].value_counts(normalize=True).to_dict()
    zone_counts = df["zone"].value_counts(normalize=True).to_dict()
    cause_counts = df["event_cause"].value_counts(normalize=True).to_dict()
    geo_counts = df["geo_sector"].value_counts(normalize=True).to_dict()

    df["corridor_freq"] = df["corridor"].map(corridor_counts).fillna(0)
    df["station_freq"] = df["police_station"].map(station_counts).fillna(0)
    df["zone_freq"] = df["zone"].map(zone_counts).fillna(0)
    df["cause_freq"] = df["event_cause"].map(cause_counts).fillna(0)
    df["geo_freq"] = df["geo_sector"].map(geo_counts).fillna(0)

    # Complex structural interaction string flags
    df["cause_X_corridor"] = df["event_cause"].astype(str) + "_" + df["corridor"].astype(str)
    df["rush_X_zone"] = df["is_rush_hour"].astype(str) + "_" + df["zone"].astype(str)
    df["priority_X_cause"] = df["priority"].astype(str) + "_" + df["event_cause"].astype(str)

    cause_corr_counts = df["cause_X_corridor"].value_counts(normalize=True).to_dict()
    rush_zone_counts = df["rush_X_zone"].value_counts(normalize=True).to_dict()
    prior_cause_counts = df["priority_X_cause"].value_counts(normalize=True).to_dict()

    df["cause_corridor_freq"] = df["cause_X_corridor"].map(cause_corr_counts).fillna(0)
    df["rush_zone_freq"] = df["rush_X_zone"].map(rush_zone_counts).fillna(0)
    df["priority_cause_freq"] = df["priority_X_cause"].map(prior_cause_counts).fillna(0)

    freq_tables = {
        "corridor_freq": corridor_counts, "station_freq": station_counts,
        "zone_freq": zone_counts, "cause_freq": cause_counts, "geo_freq": geo_counts,
        "cause_corridor_freq": cause_corr_counts, "rush_zone_freq": rush_zone_counts,
        "priority_cause_freq": prior_cause_counts
    }
    return df, freq_tables


def add_historical_closure_rate(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    df = df.copy()
    target = "requires_road_closure"
    df["_target_int"] = df[target].fillna(0).astype(int)

    global_mean = df["_target_int"].mean()
    m = 12  # M-estimate smoothing factor threshold to stabilize rare parameters safely

    def get_smooth_rates(col_name):
        stats = df.groupby(col_name)["_target_int"].agg(["count", "mean"])
        smooth = (stats["count"] * stats["mean"] + m * global_mean) / (stats["count"] + m)
        return smooth.to_dict()

    cause_rates = get_smooth_rates("event_cause")
    corridor_rates = get_smooth_rates("corridor")
    geo_rates = get_smooth_rates("geo_sector")
    cause_corridor_rates = get_smooth_rates("cause_X_corridor")
    priority_cause_rates = get_smooth_rates("priority_X_cause")

    df["cause_closure_rate"] = df["event_cause"].map(cause_rates).fillna(global_mean)
    df["corridor_closure_rate"] = df["corridor"].map(corridor_rates).fillna(global_mean)
    df["geo_closure_rate"] = df["geo_sector"].map(geo_rates).fillna(global_mean)
    df["cause_corridor_closure_rate"] = df["cause_X_corridor"].map(cause_corridor_rates).fillna(global_mean)
    df["priority_cause_closure_rate"] = df["priority_X_cause"].map(priority_cause_rates).fillna(global_mean)

    df = df.drop(columns=["_target_int"])
    rate_tables = {
        "cause_closure_rate": cause_rates, "corridor_closure_rate": corridor_rates,
        "geo_closure_rate": geo_rates, "cause_corridor_closure_rate": cause_corridor_rates,
        "priority_cause_closure_rate": priority_cause_rates
    }
    return df, rate_tables


def add_hotspot_score(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    alpha, beta, gamma = 0.4, 0.4, 0.2
    df["_raw_hotspot"] = (
        alpha * df["cause_corridor_closure_rate"] +
        beta * df["geo_closure_rate"] +
        gamma * df["priority_cause_closure_rate"]
    )
    return df


def add_impact_score(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    max_val = df["_raw_hotspot"].max() if df["_raw_hotspot"].max() > 0 else 1.0
    score = (df["_raw_hotspot"] / max_val) * (
        df["priority"].apply(lambda x: 2.0 if str(x).upper() == "HIGH" else 1.0)
    )
    df["impact_score"] = (score * 100).round(1)
    df["hotspot_score"] = (df["_raw_hotspot"] / max_val * 10.0).round(2)
    return df


def build_features(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    df = df[df["has_valid_start"]].copy()

    df = add_time_features(df)
    df = add_spatial_features(df)
    df, freq_tables = add_frequency_features(df)
    df, rate_tables = add_historical_closure_rate(df)
    df = add_hotspot_score(df)
    
    hotspot_max_ref = float(df["_raw_hotspot"].max()) if df["_raw_hotspot"].max() > 0 else 1.0
    df = add_impact_score(df)
    df = df.drop(columns=["_raw_hotspot"])

    lookup = {**freq_tables, **rate_tables, "hotspot_max_ref": hotspot_max_ref}
    return df, lookup