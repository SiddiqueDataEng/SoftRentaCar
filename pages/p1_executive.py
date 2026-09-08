"""
Page 1 – Executive Dashboard
Top-level KPIs, revenue snapshot, fleet status, quick alerts.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from app.style import inject_css, kpi_card, section_header, alert
from app.charts import (
    revenue_trend, fleet_revenue_pie, vehicle_status_donut,
    vehicle_utilisation_gauge, trips_heatmap, booking_type_trend,
)
from app.data_loader import monthly_revenue


def render(dfs: dict):
    inject_css()

    # ── Header ──────────────────────────────────────────────────────
    st.markdown("""
    <div style="display:flex;align-items:center;gap:14px;margin-bottom:8px;">
        <span style="font-size:2.2rem;">🏠</span>
        <div>
            <div style="font-size:1.6rem;font-weight:800;color:#E63946;">Executive Dashboard</div>
            <div style="font-size:0.82rem;color:#5a7a96;">Real-time fleet intelligence for Soft Rent a Car leadership</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    trips    = dfs["trips"]
    inv      = dfs["invoices"]
    vehicles = dfs["vehicles"]
    drivers  = dfs["drivers"]
    tel      = dfs["telematics"]
    fuel     = dfs["fuel_logs"]

    # ── KPI Row ──────────────────────────────────────────────────────
    total_rev       = inv["total_amount_pkr"].sum()
    collected       = inv["paid_amount_pkr"].sum()
    outstanding     = total_rev - collected
    completed_trips = (trips["status"] == "Completed").sum()
    cancel_rate     = (trips["status"] == "Cancelled").sum() / len(trips) * 100
    fleet_active    = (vehicles["status"] != "Retired").sum()
    avg_safety      = tel["safety_score"].mean()
    total_fuel_cost = fuel["fuel_cost_pkr"].sum()
    total_maint     = dfs["maintenance"]["total_cost_pkr"].sum()

    cols = st.columns(5)
    kpis = [
        (_fmt(total_rev),    "Total Billed Revenue",    "↑ 12% YoY", True),
        (_fmt(collected),    "Collected Revenue",       f"{collected/total_rev*100:.1f}% rate", True),
        (f"{completed_trips:,}", "Completed Trips",     f"Cancel: {cancel_rate:.1f}%", True),
        (f"{avg_safety:.1f}/100","Fleet Safety Score",  "Target ≥ 70", avg_safety >= 70),
        (f"{fleet_active}",  "Active Vehicles",         f"{(vehicles['status']=='On Trip').sum()} on trip", True),
    ]
    for col, (val, label, delta, pos) in zip(cols, kpis):
        col.markdown(kpi_card(val, label, delta, pos), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    cols2 = st.columns(5)
    kpis2 = [
        (_fmt(outstanding),          "Outstanding Balance",    "Unpaid invoices", outstanding < total_rev * 0.08),
        (_fmt(total_fuel_cost),      "Total Fuel Cost",        f"Avg {fuel['fuel_efficiency_kmpl'].mean():.1f} km/l", True),
        (_fmt(total_maint),          "Maintenance Spend",      "Fleet lifetime", True),
        (f"{len(drivers)}",          "Active Drivers",         f"{(drivers['behavior_profile']=='dangerous').sum()} high-risk", True),
        (f"{len(dfs['customers']):,}","Customers Served",      "All time", True),
    ]
    for col, (val, label, delta, pos) in zip(cols2, kpis2):
        col.markdown(kpi_card(val, label, delta, pos), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")

    # ── Row 2: Revenue trend + Fleet pie ────────────────────────────
    st.markdown(section_header("Revenue Overview"), unsafe_allow_html=True)
    c1, c2 = st.columns([2, 1])
    with c1:
        mr = monthly_revenue(dfs)
        st.plotly_chart(revenue_trend(mr), use_container_width=True)
    with c2:
        st.plotly_chart(fleet_revenue_pie(trips, dfs["fleets"]), use_container_width=True)

    # ── Row 3: Fleet status + Utilisation gauge ─────────────────────
    st.markdown(section_header("Fleet Status"), unsafe_allow_html=True)
    c3, c4, c5 = st.columns([1, 1, 1])
    with c3:
        st.plotly_chart(vehicle_status_donut(vehicles), use_container_width=True)
    with c4:
        util_pct = min(100, trips[trips["status"]=="Completed"]["duration_days"].sum() /
                       (fleet_active * max(1, (trips["pickup_datetime"].dt.date.max() -
                                               trips["pickup_datetime"].dt.date.min()).days)) * 100)
        st.plotly_chart(vehicle_utilisation_gauge(round(util_pct, 1)), use_container_width=True)
    with c5:
        # Safety score gauge
        st.plotly_chart(vehicle_utilisation_gauge(round(avg_safety, 1), "Avg Safety Score"), use_container_width=True)

    # ── Row 4: Booking heatmap ───────────────────────────────────────
    st.markdown(section_header("Demand Heatmap — Hour × Day"), unsafe_allow_html=True)
    st.plotly_chart(trips_heatmap(trips), use_container_width=True)

    # ── Quick Alerts ─────────────────────────────────────────────────
    st.markdown(section_header("⚠️ Active Alerts"), unsafe_allow_html=True)
    _render_quick_alerts(dfs)

    # ── Booking trend ────────────────────────────────────────────────
    st.markdown(section_header("Booking Volume by Type"), unsafe_allow_html=True)
    st.plotly_chart(booking_type_trend(trips), use_container_width=True)


def _render_quick_alerts(dfs: dict):
    veh = dfs["vehicles"].copy()
    today = pd.Timestamp("2026-07-01")
    veh["insurance_expiry"] = pd.to_datetime(veh["insurance_expiry"], errors="coerce")
    expired_ins = veh[veh["insurance_expiry"] < today]

    overdue_m  = dfs["maintenance"][dfs["maintenance"]["status"] == "Scheduled"]
    risky_drv  = dfs["drivers"][dfs["drivers"]["behavior_profile"].isin(["poor", "dangerous"])]
    unpaid_inv = dfs["invoices"][dfs["invoices"]["outstanding_pkr"] > 10000]
    total_out  = unpaid_inv["outstanding_pkr"].sum()

    alerts = []
    if len(expired_ins) > 0:
        alerts.append(("critical", f"🔴 {len(expired_ins)} vehicles have expired insurance — immediate action required."))
    if len(risky_drv) > 0:
        alerts.append(("critical", f"🔴 {len(risky_drv)} high-risk drivers (poor/dangerous profile) active on fleet."))
    if len(overdue_m) > 0:
        alerts.append(("warning",  f"🟠 {len(overdue_m)} scheduled maintenance jobs pending."))
    if total_out > 1_000_000:
        alerts.append(("warning",  f"🟡 PKR {total_out/1e6:.1f}M outstanding across {len(unpaid_inv):,} invoices."))

    if not alerts:
        st.markdown(alert("✅ No critical alerts. Fleet operating normally.", "info"), unsafe_allow_html=True)
    else:
        cols = st.columns(min(4, len(alerts)))
        for i, (level, msg) in enumerate(alerts):
            with cols[i % len(cols)]:
                st.markdown(alert(msg, level), unsafe_allow_html=True)


def _fmt(v: float) -> str:
    if v >= 1e9: return f"PKR {v/1e9:.2f}B"
    if v >= 1e6: return f"PKR {v/1e6:.1f}M"
    if v >= 1e3: return f"PKR {v/1e3:.0f}K"
    return f"PKR {v:,.0f}"
