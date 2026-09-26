"""
DataOps - Data Quality Checker
Runs automated checks on all 16 tables and produces a quality report.
Exit 0 = all critical checks pass, Exit 1 = critical failures.
"""

import sys
import io
import json
import warnings
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import date, datetime

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).parent.parent))

# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPORTS = Path("dataops/reports")
REPORTS.mkdir(parents=True, exist_ok=True)

# ASCII-safe symbols
OK   = "[OK]  "
FAIL = "[FAIL]"
WARN = "[WARN]"
SEP  = "=" * 60


def load(name: str):
    pq = Path(f"data/parquet/{name}.parquet")
    cs = Path(f"data/csv/{name}.csv")
    if pq.exists(): return pd.read_parquet(pq)
    if cs.exists(): return pd.read_csv(cs)
    return None


CHECKS = {
    "fleets": {
        "min_rows": 4,
        "pk":       "fleet_id",
        "not_null": ["fleet_id", "fleet_name", "city"],
    },
    "vehicle_types": {
        "min_rows": 18,
        "pk":       "vehicle_type_id",
        "not_null": ["vehicle_type_id", "category", "make"],
        "range":    {"daily_rate_min_pkr": (1000, 200000), "seats": (2, 50)},
    },
    "vehicles": {
        "min_rows": 100,
        "pk":       "vehicle_id",
        "not_null": ["vehicle_id", "fleet_id", "make", "model", "year"],
        "fk":       {"fleet_id": "fleets.fleet_id"},
        "range":    {"year": (2010, 2027), "odometer_km": (0, 500000)},
        "values":   {"status":    ["Available", "On Trip", "Under Maintenance", "Reserved", "Retired"],
                     "fuel_type": ["Petrol", "Diesel", "CNG"]},
    },
    "drivers": {
        "min_rows": 50,
        "pk":       "driver_id",
        "not_null": ["driver_id", "fleet_id", "full_name"],
        "fk":       {"fleet_id": "fleets.fleet_id"},
        "range":    {"base_salary_pkr": (10000, 500000)},
        "values":   {"behavior_profile": ["excellent", "good", "average", "poor", "dangerous"]},
    },
    "customers": {
        "min_rows": 1000,
        "pk":       "customer_id",
        "not_null": ["customer_id", "full_name", "customer_type"],
        "values":   {"customer_type": ["Individual", "Corporate", "Tourist",
                                        "Overseas Pakistani", "Government"]},
    },
    "trips": {
        "min_rows": 10000,
        "pk":       "trip_id",
        "not_null": ["trip_id", "fleet_id", "vehicle_id", "customer_id", "booking_type", "status"],
        "fk":       {"fleet_id": "fleets.fleet_id"},
        "range":    {"distance_km": (0, 5000), "trip_fare_pkr": (0, 10000000)},
        "values":   {"status": ["Completed", "Cancelled", "In Progress", "No Show"]},
    },
    "telematics": {
        "min_rows": 5000,
        "pk":       "telem_id",
        "not_null": ["telem_id", "trip_id", "driver_id", "vehicle_id"],
        "range":    {"safety_score": (0, 100), "avg_speed_kmh": (0, 300),
                     "harsh_brake_events": (0, 1000)},
    },
    "invoices": {
        "min_rows": 10000,
        "pk":       "invoice_id",
        "not_null": ["invoice_id", "trip_id", "customer_id", "fleet_id", "total_amount_pkr"],
        "range":    {"total_amount_pkr": (0, 100000000), "paid_amount_pkr": (0, 100000000)},
        "values":   {"payment_status": ["Paid", "Partial", "Unpaid"]},
    },
    "fuel_logs": {
        "min_rows": 5000,
        "pk":       "fuel_id",
        "not_null": ["fuel_id", "trip_id", "vehicle_id", "fleet_id"],
        "range":    {"litres_filled": (0.5, 500), "fuel_efficiency_kmpl": (0.5, 50),
                     "fuel_cost_pkr": (100, 500000)},
    },
    "maintenance": {
        "min_rows": 500,
        "pk":       "maint_id",
        "not_null": ["maint_id", "vehicle_id", "fleet_id", "maintenance_type"],
        "range":    {"total_cost_pkr": (100, 5000000)},
    },
}

# ── Run checks ────────────────────────────────────────────────────────
all_results       = {}
critical_failures = []
warnings_list     = []
passed_checks     = []

print()
print(SEP)
print("  Soft Rent a Car -- Data Quality Report")
print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(SEP)

# Pre-load FK reference tables
dfs = {}
for tname in ["fleets", "vehicles", "drivers", "customers", "trips", "invoices", "telematics"]:
    df = load(tname)
    if df is not None:
        dfs[tname] = df

for table_name, rules in CHECKS.items():
    df = load(table_name)
    table_results = {"table": table_name, "checks": [], "issues": []}
    print(f"\n  {table_name.upper()}")

    if df is None:
        msg = f"Table not found: {table_name}"
        print(f"    {FAIL} {msg}")
        critical_failures.append(msg)
        table_results["issues"].append({"level": "critical", "msg": msg})
        all_results[table_name] = table_results
        continue

    print(f"    Rows: {len(df):,}  |  Columns: {len(df.columns)}")

    # Row count
    min_rows = rules.get("min_rows", 0)
    if len(df) >= min_rows:
        print(f"    {OK} Row count >= {min_rows:,}  (got {len(df):,})")
        passed_checks.append(f"{table_name}.row_count")
    else:
        msg = f"Row count {len(df):,} < minimum {min_rows:,}"
        print(f"    {FAIL} {msg}")
        critical_failures.append(f"{table_name}: {msg}")
        table_results["issues"].append({"level": "critical", "msg": msg})

    # Primary key uniqueness
    pk = rules.get("pk")
    if pk and pk in df.columns:
        dupes = df[pk].duplicated().sum()
        if dupes == 0:
            print(f"    {OK} PK unique: {pk}")
            passed_checks.append(f"{table_name}.pk_unique")
        else:
            msg = f"PK '{pk}' has {dupes:,} duplicates"
            print(f"    {FAIL} {msg}")
            critical_failures.append(f"{table_name}: {msg}")
            table_results["issues"].append({"level": "critical", "msg": msg})

    # Not null
    for col in rules.get("not_null", []):
        if col not in df.columns:
            continue
        null_pct = df[col].isna().mean() * 100
        if null_pct == 0:
            passed_checks.append(f"{table_name}.{col}.not_null")
        elif null_pct < 5:
            msg = f"{col}: {null_pct:.1f}% nulls"
            print(f"    {WARN} {msg}")
            warnings_list.append(f"{table_name}: {msg}")
        else:
            msg = f"{col}: {null_pct:.1f}% nulls exceeds 5% threshold"
            print(f"    {FAIL} {msg}")
            critical_failures.append(f"{table_name}: {msg}")
            table_results["issues"].append({"level": "critical", "msg": msg})

    # Range checks
    for col, (lo, hi) in rules.get("range", {}).items():
        if col not in df.columns:
            continue
        vals = pd.to_numeric(df[col], errors="coerce").dropna()
        if len(vals) == 0:
            continue
        oor = ((vals < lo) | (vals > hi)).mean() * 100
        if oor == 0:
            passed_checks.append(f"{table_name}.{col}.range")
        elif oor < 1:
            msg = f"{col}: {oor:.2f}% out of range [{lo}, {hi}]"
            print(f"    {WARN} {msg}")
            warnings_list.append(f"{table_name}: {msg}")
        else:
            msg = f"{col}: {oor:.1f}% out of range [{lo}, {hi}]"
            print(f"    {FAIL} {msg}")
            critical_failures.append(f"{table_name}: {msg}")
            table_results["issues"].append({"level": "critical", "msg": msg})

    # Accepted values
    for col, accepted in rules.get("values", {}).items():
        if col not in df.columns:
            continue
        bad_pct = (~df[col].isin(accepted)).mean() * 100
        if bad_pct == 0:
            passed_checks.append(f"{table_name}.{col}.values")
        else:
            msg = f"{col}: {bad_pct:.1f}% invalid values"
            print(f"    {WARN} {msg}")
            warnings_list.append(f"{table_name}: {msg}")

    # FK referential integrity
    for fk_col, ref in rules.get("fk", {}).items():
        if fk_col not in df.columns:
            continue
        ref_table, ref_col = ref.split(".")
        if ref_table not in dfs or ref_col not in dfs[ref_table].columns:
            continue
        valid  = set(dfs[ref_table][ref_col].dropna().astype(str))
        orphan_pct = (~df[fk_col].astype(str).isin(valid)).mean() * 100
        if orphan_pct == 0:
            print(f"    {OK} FK {fk_col} -> {ref}")
            passed_checks.append(f"{table_name}.{fk_col}.fk")
        else:
            msg = f"FK {fk_col} -> {ref}: {orphan_pct:.1f}% orphans"
            print(f"    {WARN} {msg}")
            warnings_list.append(f"{table_name}: {msg}")

    all_results[table_name] = table_results

# ── Summary ────────────────────────────────────────────────────────────
print()
print(SEP)
print("  SUMMARY")
print(f"    Passed   : {len(passed_checks)} checks")
print(f"    Warnings : {len(warnings_list)}")
print(f"    Critical : {len(critical_failures)}")

if critical_failures:
    print("\n  CRITICAL FAILURES:")
    for f in critical_failures:
        print(f"    - {f}")

if warnings_list:
    print(f"\n  WARNINGS (showing first 10 of {len(warnings_list)}):")
    for w in warnings_list[:10]:
        print(f"    - {w}")

# Save report
report = {
    "run_date":          date.today().isoformat(),
    "run_timestamp":     datetime.utcnow().isoformat(),
    "summary": {
        "passed":   len(passed_checks),
        "warnings": len(warnings_list),
        "critical": len(critical_failures),
    },
    "critical_failures": critical_failures,
    "warnings":          warnings_list,
    "tables":            all_results,
}
rpath = REPORTS / f"quality_{date.today().isoformat()}.json"
rpath.write_text(json.dumps(report, indent=2, default=str))
print(f"\n  Report: {rpath}")
print(SEP)

sys.exit(1 if critical_failures else 0)
