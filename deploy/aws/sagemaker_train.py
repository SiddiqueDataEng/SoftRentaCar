"""
Soft Rent a Car — SageMaker Training Script
Trains all 6 ML models and registers them in SageMaker Model Registry.
Run locally with boto3 or submit as a SageMaker Training Job.
"""

import os
import sys
import json
import boto3
import pickle
import warnings
import pandas as pd
import numpy as np
warnings.filterwarnings("ignore")

# ── Configuration ──────────────────────────────────────────────────────
AWS_REGION     = os.getenv("AWS_REGION", "us-east-1")
S3_DATA_BUCKET = os.getenv("S3_DATA_BUCKET", "softrentacar-data-processed")
S3_MODEL_PATH  = os.getenv("S3_MODEL_PATH", "models/")
MODEL_PACKAGE_GROUP = "SoftRentaCarModels"

s3 = boto3.client("s3", region_name=AWS_REGION)
sm = boto3.client("sagemaker", region_name=AWS_REGION)


def load_parquet(table: str) -> pd.DataFrame:
    """Load table from S3 Parquet."""
    path   = f"{S3_DATA_BUCKET}/parquet/{table}/"
    objs   = s3.list_objects_v2(Bucket=S3_DATA_BUCKET, Prefix=f"parquet/{table}/")
    frames = []
    for obj in objs.get("Contents", []):
        if obj["Key"].endswith(".parquet"):
            response = s3.get_object(Bucket=S3_DATA_BUCKET, Key=obj["Key"])
            frames.append(pd.read_parquet(response["Body"]))
    return pd.concat(frames) if frames else pd.DataFrame()


def save_model_to_s3(model_obj, model_name: str, metrics: dict):
    """Pickle model and upload to S3."""
    local_path = f"/tmp/{model_name}.pkl"
    with open(local_path, "wb") as f:
        pickle.dump(model_obj, f)

    s3_key = f"{S3_MODEL_PATH}{model_name}/model.pkl"
    s3.upload_file(local_path, S3_DATA_BUCKET, s3_key)

    # Save metrics
    metrics_key = f"{S3_MODEL_PATH}{model_name}/metrics.json"
    s3.put_object(
        Bucket=S3_DATA_BUCKET,
        Key=metrics_key,
        Body=json.dumps(metrics, indent=2),
    )
    print(f"  ✅ {model_name}: saved to s3://{S3_DATA_BUCKET}/{s3_key}")
    return f"s3://{S3_DATA_BUCKET}/{s3_key}"


# ── Load data ──────────────────────────────────────────────────────────
print("Loading data from S3...")
sys.path.insert(0, "/opt/ml/code")  # SageMaker training container path
sys.path.insert(0, ".")

telem_df  = load_parquet("telematics")
driver_df = load_parquet("drivers")
trips_df  = load_parquet("trips")
inv_df    = load_parquet("invoices")
maint_df  = load_parquet("maintenance")
veh_df    = load_parquet("vehicles")
fuel_df   = load_parquet("fuel_logs")

# Parse dates
for col in ["pickup_datetime","dropoff_datetime"]:
    if col in trips_df.columns:
        trips_df[col] = pd.to_datetime(trips_df[col], errors="coerce")
for col in ["invoice_date","due_date"]:
    if col in inv_df.columns:
        inv_df[col] = pd.to_datetime(inv_df[col], errors="coerce")
if "fill_date" in fuel_df.columns:
    fuel_df["fill_date"] = pd.to_datetime(fuel_df["fill_date"], errors="coerce")
if "maintenance_date" in maint_df.columns:
    maint_df["maintenance_date"] = pd.to_datetime(maint_df["maintenance_date"], errors="coerce")

print(f"Loaded: {len(telem_df):,} telematics, {len(trips_df):,} trips")

from app.ml_models import (
    train_driver_safety_model,
    train_demand_model,
    train_pricing_model,
    train_maintenance_model,
    forecast_revenue_statsmodels,
    detect_fuel_anomalies,
)

results = {}

# ── Model 1: Driver Safety ────────────────────────────────────────────
print("\n[1/5] Training Driver Safety Classifier...")
clf, le, feat_imp, report, features = train_driver_safety_model(telem_df, driver_df)
acc = report.get("accuracy", 0)
metrics = {"accuracy": acc, "features": features, "classes": list(le.classes_)}
save_model_to_s3({"clf": clf, "le": le, "features": features}, "driver_safety", metrics)
results["driver_safety"] = {"accuracy": f"{acc*100:.1f}%"}

# ── Model 2: Demand Forecaster ────────────────────────────────────────
print("[2/5] Training Demand Forecaster...")
trips_df["pickup_year"]  = trips_df["pickup_datetime"].dt.year
trips_df["revenue_pkr"]  = pd.to_numeric(trips_df.get("trip_fare_pkr", 0), errors="coerce").fillna(0)
gbm, le_city, feats_d, mae, r2 = train_demand_model(trips_df)
metrics = {"mae": mae, "r2": r2, "features": feats_d}
save_model_to_s3({"gbm": gbm, "le_city": le_city, "features": feats_d}, "demand_forecast", metrics)
results["demand_forecast"] = {"mae": f"{mae:.2f}", "r2": f"{r2:.3f}"}

# ── Model 3: Dynamic Pricing ──────────────────────────────────────────
print("[3/5] Training Dynamic Pricing Model...")
pm, le_pc, le_pt, feats_p, mae_p, r2_p = train_pricing_model(trips_df)
metrics = {"mae_pkr": mae_p, "r2": r2_p, "features": feats_p}
save_model_to_s3({"model": pm, "le_city": le_pc, "le_type": le_pt, "features": feats_p}, "dynamic_pricing", metrics)
results["dynamic_pricing"] = {"mae_pkr": f"{mae_p:,.0f}", "r2": f"{r2_p:.3f}"}

# ── Model 4: Maintenance Predictor ────────────────────────────────────
print("[4/5] Training Maintenance Predictor...")
clf_m, le_t, feats_m, rep_m, fi_m = train_maintenance_model(maint_df, veh_df)
acc_m = rep_m.get("accuracy", 0)
metrics = {"accuracy": acc_m, "features": list(feats_m)}
save_model_to_s3({"clf": clf_m, "le_type": le_t, "features": feats_m}, "maintenance_predictor", metrics)
results["maintenance_predictor"] = {"accuracy": f"{acc_m*100:.1f}%"}

# ── Model 5: Revenue Forecast ─────────────────────────────────────────
print("[5/5] Running Revenue Forecast...")
inv_df["invoice_date"] = pd.to_datetime(inv_df["invoice_date"], errors="coerce")
hist, fc, lo, hi = forecast_revenue_statsmodels(inv_df, periods=6)
fc_data = {
    "forecast_months":  [str(i) for i in fc.index],
    "forecast_values":  fc.values.tolist(),
    "lower_ci":         lo.values.tolist(),
    "upper_ci":         hi.values.tolist(),
}
s3.put_object(
    Bucket=S3_DATA_BUCKET,
    Key=f"{S3_MODEL_PATH}revenue_forecast/forecast.json",
    Body=json.dumps(fc_data, indent=2),
)
results["revenue_forecast"] = {"periods": 6, "next_month": f"PKR {fc.values[0]:,.0f}"}
print(f"  ✅ revenue_forecast: next month PKR {fc.values[0]:,.0f}")

# ── Summary ────────────────────────────────────────────────────────────
print("\n" + "="*50)
print("TRAINING COMPLETE — Model Results:")
for model, metrics in results.items():
    print(f"  {model}: {metrics}")

# Save summary
s3.put_object(
    Bucket=S3_DATA_BUCKET,
    Key=f"{S3_MODEL_PATH}_training_summary.json",
    Body=json.dumps({"models": results}, indent=2),
)
print(f"\nAll models saved to s3://{S3_DATA_BUCKET}/{S3_MODEL_PATH}")
