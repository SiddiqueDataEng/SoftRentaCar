"""
MLOps — Model & Data Drift Monitor
Computes Population Stability Index (PSI) for key features.
PSI < 0.1: No drift | 0.1-0.2: Moderate | > 0.2: Significant drift
"""

import sys
import json
import warnings
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import date, datetime

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).parent.parent))

REPORTS = Path("mlops/reports")
REPORTS.mkdir(parents=True, exist_ok=True)

PSI_WARNING  = 0.10
PSI_CRITICAL = 0.20


def load(name: str) -> pd.DataFrame:
    pq = Path(f"data/parquet/{name}.parquet")
    cs = Path(f"data/csv/{name}.csv")
    return pd.read_parquet(pq) if pq.exists() else pd.read_csv(cs)


def psi(expected: np.ndarray, actual: np.ndarray, buckets: int = 10) -> float:
    """Population Stability Index between two distributions."""
    expected = np.array(expected, dtype=float)
    actual   = np.array(actual,   dtype=float)

    # Remove NaN
    expected = expected[~np.isnan(expected)]
    actual   = actual[~np.isnan(actual)]

    if len(expected) == 0 or len(actual) == 0:
        return 0.0

    breakpoints = np.percentile(expected, np.linspace(0, 100, buckets + 1))
    breakpoints = np.unique(breakpoints)
    if len(breakpoints) < 2:
        return 0.0

    exp_pct = np.histogram(expected, bins=breakpoints)[0] / len(expected)
    act_pct = np.histogram(actual,   bins=breakpoints)[0] / len(actual)

    # Avoid log(0)
    exp_pct = np.where(exp_pct == 0, 0.0001, exp_pct)
    act_pct = np.where(act_pct == 0, 0.0001, act_pct)

    return float(np.sum((act_pct - exp_pct) * np.log(act_pct / exp_pct)))


def drift_level(score: float) -> str:
    if score < PSI_WARNING:  return "stable"
    if score < PSI_CRITICAL: return "warning"
    return "critical"


print("=" * 55)
print("MLOps — Drift Monitor")
print("=" * 55)

telem_df = load("telematics")
trips_df = load("trips")
fuel_df  = load("fuel_logs")

for col in ["pickup_datetime"]:
    if col in trips_df.columns:
        trips_df[col] = pd.to_datetime(trips_df[col], errors="coerce")
if "fill_date" in fuel_df.columns:
    fuel_df["fill_date"] = pd.to_datetime(fuel_df["fill_date"], errors="coerce")
if "pickup_year" not in trips_df.columns:
    trips_df["pickup_year"] = trips_df["pickup_datetime"].dt.year

# Split data: first 60% = "production baseline", last 40% = "recent"
n = len(telem_df)
split = int(n * 0.6)
baseline_telem = telem_df.iloc[:split]
recent_telem   = telem_df.iloc[split:]

# ── Telematics features ───────────────────────────────────────────────
telem_features = [
    "safety_score", "harsh_brake_events", "harsh_accel_events",
    "idle_time_minutes", "speeding_km", "distance_km", "avg_speed_kmh",
]

drift_results = {}
print(f"\nTelematics Drift (baseline n={split:,}, recent n={n-split:,})")
print(f"{'Feature':<28} {'PSI':>6}  Status")
print("-" * 45)

for feat in telem_features:
    if feat not in baseline_telem.columns:
        continue
    score = psi(
        baseline_telem[feat].dropna().values,
        recent_telem[feat].dropna().values,
    )
    level  = drift_level(score)
    icon   = {"stable":"✅","warning":"⚠️","critical":"🔴"}[level]
    drift_results[f"telematics.{feat}"] = {"psi": round(score, 4), "level": level}
    print(f"  {feat:<26} {score:>6.4f}  {icon} {level}")

# ── Trip fare distribution ────────────────────────────────────────────
trips_df["revenue_pkr"] = pd.to_numeric(trips_df.get("trip_fare_pkr", 0), errors="coerce").fillna(0)
n_t = len(trips_df)
split_t = int(n_t * 0.6)
base_trips = trips_df.iloc[:split_t]
rec_trips  = trips_df.iloc[split_t:]

trip_features = ["revenue_pkr", "distance_km", "duration_days"]
print(f"\nTrip Features Drift (baseline n={split_t:,}, recent n={n_t-split_t:,})")
print(f"{'Feature':<28} {'PSI':>6}  Status")
print("-" * 45)

for feat in trip_features:
    if feat not in base_trips.columns:
        continue
    score = psi(
        base_trips[feat].dropna().values,
        rec_trips[feat].dropna().values,
    )
    level = drift_level(score)
    icon  = {"stable":"✅","warning":"⚠️","critical":"🔴"}[level]
    drift_results[f"trips.{feat}"] = {"psi": round(score, 4), "level": level}
    print(f"  {feat:<26} {score:>6.4f}  {icon} {level}")

# ── Fuel efficiency ────────────────────────────────────────────────────
if "fill_date" in fuel_df.columns and "fuel_efficiency_kmpl" in fuel_df.columns:
    fuel_df = fuel_df.sort_values("fill_date")
    n_f = len(fuel_df)
    split_f = int(n_f * 0.6)
    score_f = psi(
        fuel_df["fuel_efficiency_kmpl"].iloc[:split_f].dropna().values,
        fuel_df["fuel_efficiency_kmpl"].iloc[split_f:].dropna().values,
    )
    level_f = drift_level(score_f)
    icon_f  = {"stable":"✅","warning":"⚠️","critical":"🔴"}[level_f]
    drift_results["fuel.fuel_efficiency_kmpl"] = {"psi": round(score_f, 4), "level": level_f}
    print(f"\nFuel Efficiency Drift")
    print(f"  {'fuel_efficiency_kmpl':<26} {score_f:>6.4f}  {icon_f} {level_f}")

# ── Summary ────────────────────────────────────────────────────────────
critical = [k for k,v in drift_results.items() if v["level"] == "critical"]
warnings_ = [k for k,v in drift_results.items() if v["level"] == "warning"]
stable    = [k for k,v in drift_results.items() if v["level"] == "stable"]

print("\n" + "=" * 55)
print(f"DRIFT SUMMARY: {len(stable)} stable | {len(warnings_)} warning | {len(critical)} critical")

if critical:
    print(f"\n🔴 Critical drift — consider retraining:")
    for f in critical:
        print(f"   • {f} (PSI={drift_results[f]['psi']:.4f})")

# ── Save report ────────────────────────────────────────────────────────
report = {
    "run_timestamp": datetime.utcnow().isoformat(),
    "summary": {"stable": len(stable), "warning": len(warnings_), "critical": len(critical)},
    "features": drift_results,
    "recommendation": "Retrain models" if critical else ("Monitor closely" if warnings_ else "No action needed"),
}
report_path = REPORTS / f"drift_{date.today().isoformat()}.json"
report_path.write_text(json.dumps(report, indent=2))
print(f"\nReport: {report_path}")

# Exit 1 only if critical drift
sys.exit(1 if critical else 0)
