"""
AstraOps - Data cleaning module
--------------------------------
Takes the raw Astram incident export and produces a cleaned dataframe
that the feature engineering and modeling steps can rely on.

Design notes (grounded in the actual dataset, not assumptions):
- map_file, meta_data, comment are 100% empty -> dropped.
- closed_datetime is missing on ~62% of rows -> clearance time is only
  computed on the subset where it's present and sane (closed > start,
  and not absurdly long, which would indicate a data entry error).
- start_datetime has a small number of nulls (~1.4%) -> rows with no
  start time are unusable for time-based features and are dropped from
  the modeling set, but kept (flagged) in the raw cleaned set if the
  caller wants them for inspection.
- veh_type/veh_no are missing on ~40% of rows -> treated as optional
  signals, not required features.
"""

import re
import numpy as np
import pandas as pd

RAW_COLUMNS_TO_DROP = [
    "map_file", "meta_data", "comment",            # 100% empty
    "direction", "route_path", "age_of_truck",       # >95% empty / not useful for MVP
    "cargo_material", "reason_breakdown",            # >95% empty
    "citizen_accident_id", "assigned_to_police_id",  # >98% empty
    "client_id", "created_by_id", "last_modified_by_id",
    "closed_by_id", "resolved_by_id", "kgid", "gba_identifier",
]

CAUSE_NORMALIZE_MAP = {
    "debris": "debris",
    "Debris": "debris",
}


def _normalize_text_col(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip()


def load_raw(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path, low_memory=False)
    return df


def clean_events(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # ---- 1. Parse timestamps (all source columns are UTC ISO-ish strings) ----
    for col in ["start_datetime", "end_datetime", "modified_datetime",
                "created_date", "closed_datetime", "resolved_datetime"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce", utc=True)

    # ---- 2. Normalize categorical text fields ----
    for col in ["event_type", "event_cause", "status", "priority",
                "corridor", "police_station", "zone", "veh_type", "authenticated"]:
        if col in df.columns:
            df[col] = _normalize_text_col(df[col])

    # Fix inconsistent casing in event_cause (e.g. "Debris" vs "debris")
    df["event_cause"] = df["event_cause"].str.lower().replace(CAUSE_NORMALIZE_MAP)

    # priority has 2 missing values -> impute with the mode ("High")
    if "priority" in df.columns:
        mode_priority = df["priority"].mode(dropna=True)
        fill_val = mode_priority.iloc[0] if len(mode_priority) else "High"
        df["priority"] = df["priority"].fillna(fill_val)

    # corridor / police_station / zone missing -> explicit "Unknown" bucket
    for col in ["corridor", "police_station", "zone"]:
        if col in df.columns:
            df[col] = df[col].fillna("Unknown")

    # ---- 3. Validate coordinates ----
    # Bengaluru bounding box (generous) - anything outside is bad data.
    lat_ok = df["latitude"].between(12.4, 13.6)
    lon_ok = df["longitude"].between(77.0, 78.2)
    df["coords_valid"] = lat_ok & lon_ok & df["latitude"].notna() & df["longitude"].notna()

    # ---- 4. Boolean cleanup ----
    df["requires_road_closure"] = df["requires_road_closure"].astype(bool)

    # ---- 5. Drop unusable / empty columns ----
    drop_cols = [c for c in RAW_COLUMNS_TO_DROP if c in df.columns]
    df = df.drop(columns=drop_cols)

    # ---- 6. Flag rows usable for time-based modeling ----
    df["has_valid_start"] = df["start_datetime"].notna()

    # ---- 7. Compute clearance time where defensible ----
    # Valid iff: closed_datetime present, start_datetime present,
    # duration > 0, and duration < 24 hours.
    #
    # Why 24h and not 30 days: the raw closed-minus-start gap is heavily
    # bimodal -- about 75% of valid rows clear in under ~2.5 hours, but
    # ~17% report durations of multiple days to weeks. Manual inspection
    # suggests these long tails are mostly record-keeping lag (an admin
    # closing the ticket much later), not the road actually staying shut
    # that whole time. Capping at 24h keeps the regression target tied to
    # genuine on-ground clearance time instead of backend housekeeping
    # delay. Rows beyond this cap are excluded from has_valid_clearance
    # (they still exist in the row, just unlabeled for this target).
    has_close = df["closed_datetime"].notna() & df["start_datetime"].notna()
    duration_hr = (df["closed_datetime"] - df["start_datetime"]).dt.total_seconds() / 3600.0
    sane = (duration_hr > 0) & (duration_hr <= 24)
    df["clearance_time_hr"] = np.where(has_close & sane, duration_hr, np.nan)
    df["has_valid_clearance"] = df["clearance_time_hr"].notna()
    df["clearance_time_excluded_long_tail"] = has_close & (duration_hr > 24)

    return df


def save_clean(df: pd.DataFrame, out_path: str) -> None:
    df.to_csv(out_path, index=False)


if __name__ == "__main__":
    import os
    base = os.path.dirname(__file__)
    raw = load_raw(os.path.join(base, "..", "..", "data_raw", "astram_events.csv"))
    cleaned = clean_events(raw)
    out_path = os.path.join(base, "..", "..", "data_processed", "events_clean.csv")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    save_clean(cleaned, out_path)
    print(f"Raw rows: {len(raw)} | Cleaned rows: {len(cleaned)}")
    print(f"Rows with valid start_datetime: {cleaned['has_valid_start'].sum()}")
    print(f"Rows with valid clearance time: {cleaned['has_valid_clearance'].sum()}")
    print(f"Rows with valid coordinates: {cleaned['coords_valid'].sum()}")
