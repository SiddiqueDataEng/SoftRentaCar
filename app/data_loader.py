"""
Centralised, cached data loader for all Streamlit pages.
Reads Parquet files for speed; falls back to CSV if needed.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import streamlit as st

DATA_DIR = Path(__file__).parent.parent / "data" / "parquet"
CSV_DIR  = Path(__file__).parent.parent / "data" / "csv"


def _load(name: str) -> pd.DataFrame:
    pq = DATA_DIR / f"{name}.parquet"
    cs = CSV_DIR  / f"{name}.csv"
    if pq.exists():
        return pd.read_parquet(pq)
    return pd.read_csv(cs)


@st.cache_data(ttl=3600, show_spinner=False)
def load_all() -> dict[str, pd.DataFrame]:
    """Load and lightly pre-process all tables. Cached for 1 hour."""
    dfs = {}
    tables = [
        "fleets", "vehicle_types", "vehicles", "vehicle_attributes",
        "drivers", "staff", "customers",
        "trips", "trip_legs", "telematics",
        "invoices", "billing_line_items",
        "fuel_logs", "operating_expenses",
        "maintenance", "rate_cards",
    ]
    for t in tables:
        df = _load(t)
        dfs[t] = df

    # ── Date parsing ───────────────────────────────────────────────
    date_cols = {
        "trips":    ["booking_datetime", "pickup_datetime", "dropoff_datetime"],
        "invoices": ["invoice_date", "due_date"],
        "fuel_logs":["fill_date"],
        "maintenance": ["maintenance_date"],
        "operating_expenses": ["expense_month"],
        "telematics": ["trip_date"],
    }
    for tbl, cols in date_cols.items():
        for c in cols:
            if c in dfs[tbl].columns:
                dfs[tbl][c] = pd.to_datetime(dfs[tbl][c], errors="coerce")

    # ── Derived columns ────────────────────────────────────────────
    t = dfs["trips"]
    t["pickup_month"]  = t["pickup_datetime"].dt.to_period("M").astype(str)
    t["pickup_week"]   = t["pickup_datetime"].dt.to_period("W").astype(str)
    t["pickup_year"]   = t["pickup_datetime"].dt.year
    t["pickup_hour"]   = t["pickup_datetime"].dt.hour
    t["pickup_dow"]    = t["pickup_datetime"].dt.day_name()
    t["is_weekend"]    = t["pickup_datetime"].dt.dayofweek >= 5
    t["revenue_pkr"]   = pd.to_numeric(t["trip_fare_pkr"], errors="coerce").fillna(0)

    inv = dfs["invoices"]
    inv["invoice_month"] = inv["invoice_date"].dt.to_period("M").astype(str)
    inv["invoice_year"]  = inv["invoice_date"].dt.year

    fl = dfs["fuel_logs"]
    fl["fill_month"] = fl["fill_date"].dt.to_period("M").astype(str)
    fl["fill_year"]  = fl["fill_date"].dt.year

    op = dfs["operating_expenses"]
    op["month_period"] = op["expense_month"].dt.to_period("M").astype(str)
    op["year"]         = op["expense_month"].dt.year

    dfs["trips"]               = t
    dfs["invoices"]            = inv
    dfs["fuel_logs"]           = fl
    dfs["operating_expenses"]  = op

    return dfs


# ── Aggregation helpers ────────────────────────────────────────────────

def monthly_revenue(dfs: dict) -> pd.DataFrame:
    inv = dfs["invoices"].copy()
    inv["month"] = inv["invoice_date"].dt.to_period("M")
    g = inv.groupby("month").agg(
        total_billed=("total_amount_pkr", "sum"),
        total_collected=("paid_amount_pkr", "sum"),
        invoice_count=("invoice_id", "count"),
    ).reset_index()
    g["month"] = g["month"].astype(str)
    g["outstanding"] = g["total_billed"] - g["total_collected"]
    return g.sort_values("month")


def fleet_utilisation(dfs: dict) -> pd.DataFrame:
    trips = dfs["trips"][dfs["trips"]["status"] == "Completed"].copy()
    vehicles = dfs["vehicles"].copy()
    trips["pickup_month"] = trips["pickup_datetime"].dt.to_period("M")
    trip_days = trips.groupby(["vehicle_id", "pickup_month"])["duration_days"].sum().reset_index()
    trip_days["utilisation_pct"] = (trip_days["duration_days"] / 30 * 100).clip(0, 100)
    return trip_days


def driver_safety_summary(dfs: dict) -> pd.DataFrame:
    tel = dfs["telematics"].copy()
    drv = dfs["drivers"][["driver_id", "full_name", "behavior_profile", "fleet_id"]].copy()
    summary = tel.groupby("driver_id").agg(
        avg_safety_score=("safety_score", "mean"),
        total_trips=("trip_id", "count"),
        total_km=("distance_km", "sum"),
        harsh_brakes=("harsh_brake_events", "sum"),
        harsh_accels=("harsh_accel_events", "sum"),
        idle_min=("idle_time_minutes", "sum"),
        speeding_km=("speeding_km", "sum"),
        accidents=("accident_occurred", "sum"),
        complaints=("complaint_filed", "sum"),
        avg_rating=("customer_rating", "mean"),
    ).reset_index()
    return summary.merge(drv, on="driver_id", how="left")


def vehicle_health_summary(dfs: dict) -> pd.DataFrame:
    maint = dfs["maintenance"].copy()
    veh   = dfs["vehicles"][["vehicle_id", "make", "model", "year",
                              "fleet_id", "odometer_km", "status"]].copy()
    cost_per_v = maint.groupby("vehicle_id")["total_cost_pkr"].sum().reset_index()
    cost_per_v.columns = ["vehicle_id", "total_maint_cost_pkr"]
    fuel_per_v = dfs["fuel_logs"].groupby("vehicle_id").agg(
        total_fuel_cost=("fuel_cost_pkr", "sum"),
        avg_efficiency=("fuel_efficiency_kmpl", "mean"),
    ).reset_index()
    out = veh.merge(cost_per_v, on="vehicle_id", how="left") \
             .merge(fuel_per_v, on="vehicle_id", how="left")
    out["total_maint_cost_pkr"] = out["total_maint_cost_pkr"].fillna(0)
    return out
