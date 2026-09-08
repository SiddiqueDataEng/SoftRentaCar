"""Quick smoke-test for all ML models."""
import sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, ".")

from app.data_loader import load_all
dfs = load_all()

from app.ml_models import (
    train_driver_safety_model, forecast_revenue_statsmodels,
    train_demand_model, detect_fuel_anomalies, train_pricing_model,
    train_maintenance_model,
)

print("1. Driver safety model...")
clf, le, fi, rep, feats = train_driver_safety_model(dfs["telematics"], dfs["drivers"])
acc = rep.get("accuracy", 0)
print(f"   Accuracy: {acc*100:.1f}%  |  Top feature: {fi.index[0]}")

print("2. Revenue forecast...")
hist, fc, lo, hi = forecast_revenue_statsmodels(dfs["invoices"], 6)
print(f"   Historical={len(hist)} months, Forecast={len(fc)} months")
print(f"   Next month forecast: PKR {fc.values[0]:,.0f}")

print("3. Demand model...")
gbm, le_c, feats_d, mae, r2 = train_demand_model(dfs["trips"])
print(f"   MAE={mae:.2f} trips/day  |  R2={r2:.3f}")

print("4. Fuel anomaly detection...")
anoms = detect_fuel_anomalies(dfs["fuel_logs"])
print(f"   Anomalies detected: {len(anoms)}")

print("5. Dynamic pricing model...")
pm, le_pc, le_pt, feats_p, mae_p, r2_p = train_pricing_model(dfs["trips"])
print(f"   MAE=PKR {mae_p:,.0f}  |  R2={r2_p:.3f}")

print("6. Maintenance predictor...")
clf_m, le_t, feats_m, rep_m, fi_m = train_maintenance_model(dfs["maintenance"], dfs["vehicles"])
acc_m = rep_m.get("accuracy", 0)
print(f"   Accuracy: {acc_m*100:.1f}%")

print("\nAll models passed!")
