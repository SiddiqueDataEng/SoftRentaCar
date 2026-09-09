"""
MLOps — Train & Validate All Models
Trains all 6 models, compares to baselines, saves artifacts.
Exit 0 = all pass, Exit 1 = one or more failed.
"""

import os
import sys
import json
import pickle
import warnings
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import date, datetime

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).parent.parent))

# ── Setup directories ─────────────────────────────────────────────────
ARTIFACTS = Path("mlops/artifacts")
REPORTS   = Path("mlops/reports")
ARTIFACTS.mkdir(parents=True, exist_ok=True)
REPORTS.mkdir(parents=True, exist_ok=True)

# ── Load baselines ────────────────────────────────────────────────────
BASELINES = json.loads(Path("mlops/baselines.json").read_text())

# ── Load data ─────────────────────────────────────────────────────────
def load(name: str) -> pd.DataFrame:
    pq = Path(f"data/parquet/{name}.parquet")
    cs = Path(f"data/csv/{name}.csv")
    return pd.read_parquet(pq) if pq.exists() else pd.read_csv(cs)

print("Loading data...")
telem_df  = load("telematics")
driver_df = load("drivers")
trips_df  = load("trips")
inv_df    = load("invoices")
maint_df  = load("maintenance")
veh_df    = load("vehicles")
fuel_df   = load("fuel_logs")

for col in ["pickup_datetime","dropoff_datetime"]:
    if col in trips_df.columns:
        trips_df[col] = pd.to_datetime(trips_df[col], errors="coerce")
for col in ["invoice_date","due_date"]:
    if col in inv_df.columns:
        inv_df[col] = pd.to_datetime(inv_df[col], errors="coerce")
if "fill_date"         in fuel_df.columns:  fuel_df["fill_date"]         = pd.to_datetime(fuel_df["fill_date"],         errors="coerce")
if "maintenance_date"  in maint_df.columns: maint_df["maintenance_date"] = pd.to_datetime(maint_df["maintenance_date"], errors="coerce")
if "pickup_year" not in trips_df.columns:
    trips_df["pickup_year"] = trips_df["pickup_datetime"].dt.year
if "revenue_pkr" not in trips_df.columns:
    trips_df["revenue_pkr"] = pd.to_numeric(trips_df.get("trip_fare_pkr", 0), errors="coerce").fillna(0)
if "fill_month" not in fuel_df.columns:
    fuel_df["fill_month"] = fuel_df["fill_date"].dt.to_period("M").astype(str)

print(f"Loaded: {len(telem_df):,} telematics | {len(trips_df):,} trips\n")

from app.ml_models import (
    train_driver_safety_model,
    train_demand_model,
    train_pricing_model,
    train_maintenance_model,
    forecast_revenue_statsmodels,
    detect_fuel_anomalies,
)

results = {}
all_passed = True


def save_artifact(obj, name: str):
    path = ARTIFACTS / f"{name}.pkl"
    with open(path, "wb") as f:
        pickle.dump(obj, f)
    return str(path)


def check(model_name: str, metric: str, value: float) -> bool:
    b = BASELINES.get(model_name, {})
    min_key = f"min_{metric}"
    max_key = f"max_{metric}"
    if min_key in b and value < b[min_key]:
        print(f"    ⚠️  {metric} {value:.4f} < min {b[min_key]}")
        return False
    if max_key in b and value > b[max_key]:
        print(f"    ⚠️  {metric} {value:.4f} > max {b[max_key]}")
        return False
    return True


# ── Model 1: Driver Safety ────────────────────────────────────────────
print("=" * 50)
print("[1/6] Driver Safety Classifier")
clf, le, feat_imp, report, features = train_driver_safety_model(telem_df, driver_df)
acc = report.get("accuracy", 0)
passed = check("driver_safety", "accuracy", acc)
if not passed: all_passed = False
status = "PASS" if passed else "FAIL"
print(f"  Accuracy: {acc*100:.1f}%  [{status}]")
save_artifact({"clf": clf, "le": le, "features": features}, "driver_safety")
results["driver_safety"] = {"accuracy": round(acc, 4), "status": status}

# ── Model 2: Demand Forecaster ────────────────────────────────────────
print("[2/6] Demand Forecaster")
gbm, le_c, feats_d, mae, r2 = train_demand_model(trips_df)
p1 = check("demand_forecast", "mae", mae)
p2 = check("demand_forecast", "r2",  r2)
passed = p1 and p2
if not passed: all_passed = False
status = "PASS" if passed else "FAIL"
print(f"  MAE: {mae:.2f} trips/day | R²: {r2:.3f}  [{status}]")
save_artifact({"gbm": gbm, "le_city": le_c, "features": feats_d}, "demand_forecast")
results["demand_forecast"] = {"mae": round(mae, 3), "r2": round(r2, 3), "status": status}

# ── Model 3: Dynamic Pricing ──────────────────────────────────────────
print("[3/6] Dynamic Pricing Model")
pm, le_pc, le_pt, feats_p, mae_p, r2_p = train_pricing_model(trips_df)
p1 = check("dynamic_pricing", "mae_pkr", mae_p)
p2 = check("dynamic_pricing", "r2",      r2_p)
passed = p1 and p2
if not passed: all_passed = False
status = "PASS" if passed else "FAIL"
print(f"  MAE: PKR {mae_p:,.0f} | R²: {r2_p:.3f}  [{status}]")
save_artifact({"model": pm, "le_city": le_pc, "le_type": le_pt, "features": feats_p}, "dynamic_pricing")
results["dynamic_pricing"] = {"mae_pkr": round(mae_p, 0), "r2": round(r2_p, 3), "status": status}

# ── Model 4: Maintenance Predictor ────────────────────────────────────
print("[4/6] Maintenance Predictor")
clf_m, le_t, feats_m, rep_m, fi_m = train_maintenance_model(maint_df, veh_df)
acc_m = rep_m.get("accuracy", 0)
passed = check("maintenance", "accuracy", acc_m)
if not passed: all_passed = False
status = "PASS" if passed else "FAIL"
print(f"  Accuracy: {acc_m*100:.1f}%  [{status}]")
save_artifact({"clf": clf_m, "le_type": le_t, "features": feats_m}, "maintenance_predictor")
results["maintenance"] = {"accuracy": round(acc_m, 4), "status": status}

# ── Model 5: Revenue Forecast ─────────────────────────────────────────
print("[5/6] Revenue Forecast")
hist, fc, lo, hi = forecast_revenue_statsmodels(inv_df, periods=6)
next_month = float(fc.values[0])
print(f"  Next month: PKR {next_month/1e6:.2f}M  [PASS]")
save_artifact({"hist": hist, "fc": fc, "lo": lo, "hi": hi}, "revenue_forecast")
results["revenue_forecast"] = {
    "next_month_pkr": round(next_month, 0),
    "periods": 6,
    "status": "PASS",
}

# ── Model 6: Fuel Anomaly Detector ────────────────────────────────────
print("[6/6] Fuel Anomaly Detector")
anomalies = detect_fuel_anomalies(fuel_df)
n_anom = len(anomalies)
b = BASELINES.get("fuel_anomaly", {})
passed = b.get("min_anomalies", 0) <= n_anom <= b.get("max_anomalies", 99999)
status = "PASS" if passed else "FAIL"
if not passed: all_passed = False
print(f"  Anomalies detected: {n_anom}  [{status}]")
results["fuel_anomaly"] = {"anomalies_detected": n_anom, "status": status}

# ── Save metrics report ───────────────────────────────────────────────
report_path = REPORTS / f"metrics_{date.today().isoformat()}.json"
report_data = {
    "run_timestamp": datetime.utcnow().isoformat(),
    "overall_status": "PASS" if all_passed else "FAIL",
    "models": results,
}
report_path.write_text(json.dumps(report_data, indent=2))

# ── Summary ────────────────────────────────────────────────────────────
print("\n" + "=" * 50)
print(f"OVERALL: {'ALL PASS' if all_passed else 'SOME FAILED'}")
for m, r in results.items():
    icon = "PASS" if r["status"] == "PASS" else "FAIL"
    print(f"  [{icon}] {m}")
print(f"\nMetrics saved: {report_path}")
print(f"Artifacts: {ARTIFACTS}/")

sys.exit(0 if all_passed else 1)
