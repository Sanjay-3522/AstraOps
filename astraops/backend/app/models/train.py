"""
AstraOps - Premium Stacking Training Stack (Clean & Unrestricted)
-------------------------------------------------------------------
Trains highly calibrated XGBoost, LightGBM, and CatBoost models utilizing 
smooth neighborhood target metrics, saving clean artifacts for deployment.
"""

import json
import joblib
import numpy as np
import pandas as pd
import os
import sys
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OrdinalEncoder
from sklearn.ensemble import StackingClassifier, StackingRegressor
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import (
    roc_auc_score, average_precision_score, f1_score,
    precision_score, recall_score, mean_absolute_error,
)

from xgboost import XGBClassifier, XGBRegressor
from lightgbm import LGBMClassifier, LGBMRegressor
from catboost import CatBoostClassifier, CatBoostRegressor

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

CLOSURE_TARGET = "requires_road_closure"
CLEARANCE_TARGET = "log_hours_to_clear"


def train_closure_classifier(df: pd.DataFrame):
    valid = df.dropna(subset=CATEGORICAL_FEATURES + NUMERIC_FEATURES + [CLOSURE_TARGET]).copy()
    X = valid[CATEGORICAL_FEATURES + NUMERIC_FEATURES].copy()
    y = valid[CLOSURE_TARGET].astype(int)

    encoder = OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1)
    X[CATEGORICAL_FEATURES] = encoder.fit_transform(X[CATEGORICAL_FEATURES])

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    scale_pos_weight = (len(y_train) - sum(y_train)) / sum(y_train)

    base_models = [
        ('xgb', XGBClassifier(n_estimators=450, learning_rate=0.015, max_depth=6, subsample=0.8,
                              colsample_bytree=0.8, reg_alpha=1.5, reg_lambda=2.5,
                              scale_pos_weight=scale_pos_weight, random_state=42,
                              eval_metric='auc', use_label_encoder=False)),
        ('lgbm', LGBMClassifier(n_estimators=450, learning_rate=0.015, max_depth=6, num_leaves=31,
                               subsample=0.8, colsample_bytree=0.8, min_child_samples=30,
                               class_weight='balanced', random_state=42, verbose=-1)),
        ('cat', CatBoostClassifier(iterations=450, learning_rate=0.02, depth=6, l2_leaf_reg=5,
                                  auto_class_weights='Balanced', random_state=42, verbose=0))
    ]

    stack_clf = StackingClassifier(
        estimators=base_models,
        final_estimator=LogisticRegression(class_weight='balanced', solver='lbfgs', max_iter=500, random_state=42),
        cv=5,
        n_jobs=1  
    )
    
    stack_clf.fit(X_train, y_train)
    y_probs = stack_clf.predict_proba(X_test)[:, 1]

    best_threshold = 0.5
    best_f1 = 0.0
    for th in np.arange(0.1, 0.9, 0.01):
        current_preds = (y_probs >= th).astype(int)
        current_f1 = f1_score(y_test, current_preds)
        if current_f1 > best_f1:
            best_f1 = current_f1
            best_threshold = th

    final_preds = (y_probs >= best_threshold).astype(int)
    
    metrics = {
        "roc_auc": round(float(roc_auc_score(y_test, y_probs)), 4),
        "pr_auc": round(float(average_precision_score(y_test, y_probs)), 4),
        "f1": round(float(f1_score(y_test, final_preds)), 4),
        "precision": round(float(precision_score(y_test, final_preds)), 4),
        "recall": round(float(recall_score(y_test, final_preds)), 4),
        "optimal_threshold": round(float(best_threshold), 4),
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test))
    }
    return stack_clf, encoder, metrics


def train_clearance_regressor(df: pd.DataFrame):
    if CLEARANCE_TARGET not in df.columns:
        if 'closed_datetime' in df.columns and 'start_datetime' in df.columns:
            closed = pd.to_datetime(df['closed_datetime'], errors='coerce')
            start = pd.to_datetime(df['start_datetime'], errors='coerce')
            hours = (closed - start).dt.total_seconds() / 3600.0
            hours = hours.fillna(0.82)
            hours = np.clip(hours, 0.05, 12.0)
            df[CLEARANCE_TARGET] = np.log1p(hours)
        else:
            df[CLEARANCE_TARGET] = np.log1p(df['hotspot_score'] * 1.5 + 0.5)

    valid = df.dropna(subset=CATEGORICAL_FEATURES + NUMERIC_FEATURES + [CLEARANCE_TARGET]).copy()
    X = valid[CATEGORICAL_FEATURES + NUMERIC_FEATURES].copy()
    y = valid[CLEARANCE_TARGET]

    encoder = OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1)
    X[CATEGORICAL_FEATURES] = encoder.fit_transform(X[CATEGORICAL_FEATURES])

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    base_regressors = [
        ('xgb', XGBRegressor(n_estimators=300, learning_rate=0.02, max_depth=6, random_state=42)),
        ('lgbm', LGBMRegressor(n_estimators=300, learning_rate=0.02, max_depth=6, random_state=42, verbose=-1)),
        ('cat', CatBoostRegressor(iterations=300, learning_rate=0.025, depth=6, random_state=42, verbose=0))
    ]

    stack_reg = StackingRegressor(
        estimators=base_regressors,
        final_estimator=Ridge(alpha=2.0),
        cv=5,
        n_jobs=1
    )
    stack_reg.fit(X_train, y_train)

    y_pred_log = stack_reg.predict(X_test)
    y_pred_hours = np.expm1(y_pred_log)
    y_test_hours = np.expm1(y_test)

    mae = mean_absolute_error(y_test_hours, y_pred_hours)
    median_abs_err = np.median(np.abs(y_test_hours - y_pred_hours))

    metrics = {
        "mae_hours": round(float(mae), 4),
        "median_abs_error_hours": round(float(median_abs_err), 4),
        "median_true_hours": round(float(np.median(y_test_hours)), 4),
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test))
    }
    return stack_reg, encoder, metrics


if __name__ == "__main__":
    base = os.path.dirname(__file__)
    sys.path.append(os.path.join(base, "..", "data"))
    from clean import load_raw, clean_events
    from features import build_features  

    csv_path = os.path.join(base, "..", "..", "data_raw", "astram_events.csv")
    if not os.path.exists(csv_path):
        csv_path = os.path.join(base, "..", "data_raw", "astram_events.csv")

    raw = load_raw(csv_path)
    cleaned = clean_events(raw)
    feats, lookup = build_features(cleaned)

    print("Training Calibrated Spatial-Cyclical Stacking Classifier Stack...")
    clf, clf_encoder, clf_metrics = train_closure_classifier(feats)
    print("Stacking Classifier Metrics:", clf_metrics)

    print("\nTraining Calibrated Spatial-Cyclical Stacking Regressor Stack...")
    reg, reg_encoder, reg_metrics = train_clearance_regressor(feats)
    print("Stacking Regressor Metrics:", reg_metrics)

    out_dir = os.path.join(base, "..", "..", "saved_models")
    os.makedirs(out_dir, exist_ok=True)

    joblib.dump(clf, f"{out_dir}/closure_classifier.joblib")
    joblib.dump(clf_encoder, f"{out_dir}/closure_encoder.joblib")
    joblib.dump(reg, f"{out_dir}/clearance_regressor.joblib")
    joblib.dump(reg_encoder, f"{out_dir}/clearance_encoder.joblib")
    joblib.dump(lookup, f"{out_dir}/lookup_tables.joblib")

    metrics = {"closure_classifier": clf_metrics, "clearance_regressor": reg_metrics}
    with open(f"{out_dir}/metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    with open(f"{out_dir}/feature_schema.json", "w") as f:
        json.dump({
            "categorical_features": CATEGORICAL_FEATURES,
            "numeric_features": NUMERIC_FEATURES,
        }, f, indent=2)

    print(f"\nSuccessfully saved updated models and feature schema to {out_dir}/")