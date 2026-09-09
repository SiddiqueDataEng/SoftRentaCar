"""
DataOps — Data Lineage Generator
Produces lineage.md and lineage.json showing table → feature → model dependencies.
"""

import json
from pathlib import Path
from datetime import date

Path("dataops").mkdir(exist_ok=True)

LINEAGE = {
    "raw_tables": {
        "trips": {
            "description": "Core rental bookings — 18,000 rows",
            "derived_columns": [
                "pickup_year (dt.year)", "pickup_month (period)", 
                "pickup_hour (dt.hour)", "pickup_dow (day_name)",
                "is_weekend (dow >= 5)", "revenue_pkr (trip_fare_pkr)",
            ],
            "feeds_models": ["demand_forecast", "dynamic_pricing"],
            "feeds_pages":  ["executive","operations","map","finance","forecast"],
        },
        "telematics": {
            "description": "Per-trip driving KPIs — 7,835 rows",
            "derived_columns": ["safety_score (composite 0-100)"],
            "feeds_models": ["driver_safety_classifier", "fuel_anomaly_detector"],
            "feeds_pages":  ["drivers","executive","alerts"],
        },
        "invoices": {
            "description": "Billing documents — 17,421 rows",
            "derived_columns": [
                "invoice_year (dt.year)", "invoice_month (period)",
                "outstanding_pkr (total - paid)",
            ],
            "feeds_models": ["revenue_forecast"],
            "feeds_pages":  ["finance","executive","alerts"],
        },
        "fuel_logs": {
            "description": "Fuel consumption per trip — 14,430 rows",
            "derived_columns": ["fill_month (period)"],
            "feeds_models": ["fuel_anomaly_detector"],
            "feeds_pages":  ["fleet","executive"],
        },
        "maintenance": {
            "description": "Vehicle service records — 800 rows",
            "derived_columns": ["days_since_last (date diff)", "vehicle_age (2026-year)"],
            "feeds_models": ["maintenance_predictor"],
            "feeds_pages":  ["fleet","alerts","executive"],
        },
        "vehicles": {
            "description": "Fleet vehicle register — 120 rows",
            "derived_columns": ["vehicle_age (2026-year)"],
            "feeds_models": ["maintenance_predictor"],
            "feeds_pages":  ["fleet","executive","map","alerts"],
        },
        "drivers": {
            "description": "Driver profiles — 60 rows",
            "derived_columns": [],
            "feeds_models": ["driver_safety_classifier"],
            "feeds_pages":  ["drivers","alerts","executive"],
        },
        "customers": {
            "description": "Customer profiles — 2,000 rows",
            "derived_columns": [],
            "feeds_models": [],
            "feeds_pages":  ["finance","executive"],
        },
    },
    "ml_models": {
        "driver_safety_classifier": {
            "input_features": [
                "harsh_brake_events", "harsh_accel_events", "idle_time_minutes",
                "speeding_km", "distance_km", "duration_hours",
                "max_speed_kmh", "avg_speed_kmh",
            ],
            "target":    "behavior_profile",
            "algorithm": "RandomForestClassifier",
            "output":    "predicted_behavior_profile, risk_probabilities",
        },
        "demand_forecast": {
            "input_features": ["dow", "month", "year", "is_weekend", "day", "city_enc"],
            "target":         "daily_trip_count",
            "algorithm":      "GradientBoostingRegressor",
            "output":         "predicted_trips_per_day",
        },
        "dynamic_pricing": {
            "input_features": ["month","dow","is_weekend","city_enc","type_enc","distance_km"],
            "target":         "daily_rate_pkr",
            "algorithm":      "GradientBoostingRegressor",
            "output":         "recommended_daily_rate_pkr",
        },
        "maintenance_predictor": {
            "input_features": ["vehicle_age","odometer_km","days_since_last","type_enc"],
            "target":         "needs_service_within_14d",
            "algorithm":      "RandomForestClassifier",
            "output":         "maintenance_risk_pct",
        },
        "revenue_forecast": {
            "input_features": ["monthly_time_series"],
            "target":         "monthly_revenue_pkr",
            "algorithm":      "ExponentialSmoothing (Holt-Winters)",
            "output":         "6_month_forecast_with_95pct_ci",
        },
        "fuel_anomaly_detector": {
            "input_features": ["fuel_efficiency_kmpl", "vehicle_baseline_mean", "vehicle_baseline_std"],
            "target":         "anomaly_flag",
            "algorithm":      "Z-score (|z| > 2.0)",
            "output":         "anomaly_flag, z_score",
        },
    },
    "sql_views": {
        "v_monthly_revenue":  {"depends_on": ["invoices"],                     "used_by": ["finance","forecast"]},
        "v_driver_safety":    {"depends_on": ["telematics","drivers"],          "used_by": ["drivers","alerts"]},
        "v_fleet_kpis":       {"depends_on": ["trips","invoices","vehicles","telematics","fuel_logs"], "used_by": ["executive"]},
        "v_route_stats":      {"depends_on": ["trips"],                         "used_by": ["operations","map"]},
        "v_ar_aging":         {"depends_on": ["invoices"],                      "used_by": ["finance","alerts"]},
        "v_vehicle_health":   {"depends_on": ["vehicles","maintenance","fuel_logs"],"used_by": ["fleet","alerts"]},
    },
}


def generate_lineage_md(lineage: dict) -> str:
    md = f"""# 🔗 Data Lineage — Soft Rent a Car
Generated: {date.today()}

## Overview

```
RAW TABLES → DERIVED COLUMNS → ML FEATURES → MODEL OUTPUTS → DASHBOARD PAGES
```

## Table → Model Dependencies

| Source Table | ML Models | Dashboard Pages |
|-------------|-----------|----------------|
"""
    for tname, tmeta in lineage["raw_tables"].items():
        models = ", ".join(tmeta["feeds_models"]) or "—"
        pages  = ", ".join(tmeta["feeds_pages"])  or "—"
        md    += f"| `{tname}` | {models} | {pages} |\n"

    md += "\n## ML Models — Feature Lineage\n\n"
    for mname, mmeta in lineage["ml_models"].items():
        md += f"### `{mname}`\n"
        md += f"- **Algorithm:** {mmeta['algorithm']}\n"
        md += f"- **Target:** `{mmeta['target']}`\n"
        md += f"- **Features:** {', '.join(f'`{f}`' for f in mmeta['input_features'])}\n"
        md += f"- **Output:** `{mmeta['output']}`\n\n"

    md += "## SQL Views — Table Dependencies\n\n"
    md += "| View | Depends On | Used By Pages |\n|------|-----------|---------------|\n"
    for vname, vmeta in lineage["sql_views"].items():
        deps = ", ".join(f"`{d}`" for d in vmeta["depends_on"])
        used = ", ".join(vmeta["used_by"])
        md  += f"| `{vname}` | {deps} | {used} |\n"

    md += "\n## Derived Column Lineage\n\n"
    for tname, tmeta in lineage["raw_tables"].items():
        if tmeta["derived_columns"]:
            md += f"### `{tname}`\n"
            for dcol in tmeta["derived_columns"]:
                md += f"- `{dcol}`\n"
            md += "\n"

    return md


lineage_md   = generate_lineage_md(LINEAGE)
lineage_json = json.dumps(LINEAGE, indent=2)

Path("dataops/lineage.md").write_text(lineage_md,   encoding="utf-8")
Path("dataops/lineage.json").write_text(lineage_json, encoding="utf-8")

print("✅ Lineage files generated:")
print("   dataops/lineage.md")
print("   dataops/lineage.json")
print(f"\nTables:    {len(LINEAGE['raw_tables'])}")
print(f"ML Models: {len(LINEAGE['ml_models'])}")
print(f"SQL Views: {len(LINEAGE['sql_views'])}")
