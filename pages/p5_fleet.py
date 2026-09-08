"""
Page 5 – Fleet Health
Vehicle status, maintenance costs, fuel efficiency, anomaly detection.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from app.style import inject_css, kpi_card, section_header, alert
from app.charts import (
    vehicle_status_donut, maintenance_cost_waterfall, fuel_efficiency_trend,
)
from app.data_loader import vehicle_health_summary
from app.ml_models import detect_fuel_anomalies, train_maintenance_model
from app.style import BRAND_COLOR, SUCCESS_COLOR, DANGER_COLOR, WARNING_COLOR, PLOTLY_COLORS


def render(dfs: dict):
    inject_css()

    st.markdown('<div style="font-size:1.6rem;font-weight:800;color:#E63946;margin-bottom:4px;">🔧 Fleet Health</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:0.82rem;color:#5a7a96;">Vehicle status, maintenance tracking, fuel efficiency, and predictive alerts</div>', unsafe_allow_html=True)
    st.markdown("---")

    vehicles = dfs["vehicles"]
    maint    = dfs["maintenance"]
    fuel     = dfs["fuel_logs"]
    vtypes   = dfs["vehicle_types"]

    health = vehicle_health_summary(dfs)

    # ── KPIs ─────────────────────────────────────────────────────────
    total_veh      = len(vehicles)
    available      = (vehicles["status"] == "Available").sum()
    on_trip        = (vehicles["status"] == "On Trip").sum()
    under_maint    = (vehicles["status"] == "Under Maintenance").sum()
    total_maint_cost = maint["total_cost_pkr"].sum()
    avg_fuel_eff   = fuel["fuel_efficiency_kmpl"].mean()
    total_fuel     = fuel["fuel_cost_pkr"].sum()
    scheduled      = (maint["status"] == "Scheduled").sum()

    cols = st.columns(5)
    kpis = [
        (f"{total_veh}",          "Total Vehicles",      f"{available} available", True),
        (f"{on_trip}",            "On Trip",             f"{under_maint} in maint.", True),
        (f"PKR {total_maint_cost/1e6:.1f}M", "Maint. Spend", "Lifetime total", True),
        (f"{avg_fuel_eff:.1f} km/l","Avg Fuel Efficiency","Fleet average", avg_fuel_eff > 10),
        (f"{scheduled}",          "Scheduled Services",  "Pending", scheduled == 0),
    ]
    for col, (v, l, d, pos) in zip(cols, kpis):
        col.markdown(kpi_card(v, l, d, pos), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")

    # ── Filters ──────────────────────────────────────────────────────
    cf1, cf2, cf3 = st.columns(3)
    status_opts = ["All"] + vehicles["status"].unique().tolist()
    sel_st   = cf1.selectbox("Status Filter", status_opts)
    make_opts = ["All"] + vehicles["make"].unique().tolist()
    sel_make  = cf2.selectbox("Make", make_opts)
    fleet_opts = ["All"] + dfs["fleets"]["fleet_name"].tolist()
    sel_fleet  = cf3.selectbox("Fleet", fleet_opts)

    veh_f = vehicles.copy()
    if sel_st   != "All": veh_f = veh_f[veh_f["status"] == sel_st]
    if sel_make != "All": veh_f = veh_f[veh_f["make"]   == sel_make]
    if sel_fleet!= "All":
        fid = dfs["fleets"][dfs["fleets"]["fleet_name"] == sel_fleet]["fleet_id"].values[0]
        veh_f = veh_f[veh_f["fleet_id"] == fid]

    # ── Row 1: Status donut + Maintenance waterfall ──────────────────
    st.markdown(section_header("Fleet Status & Maintenance"), unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(vehicle_status_donut(veh_f), use_container_width=True)
    with c2:
        maint_f = maint[maint["vehicle_id"].isin(veh_f["vehicle_id"])]
        st.plotly_chart(maintenance_cost_waterfall(maint_f), use_container_width=True)

    # ── Row 2: Fuel efficiency trend + Cost by fuel type ────────────
    st.markdown(section_header("Fuel Performance"), unsafe_allow_html=True)
    c3, c4 = st.columns(2)
    with c3:
        fuel_f = fuel[fuel["vehicle_id"].isin(veh_f["vehicle_id"])]
        st.plotly_chart(fuel_efficiency_trend(fuel_f), use_container_width=True)
    with c4:
        ft_group = fuel_f.groupby("fuel_type").agg(
            total_cost=("fuel_cost_pkr","sum"),
            total_litres=("litres_filled","sum"),
            avg_eff=("fuel_efficiency_kmpl","mean"),
        ).reset_index()
        fig_ft = go.Figure(go.Bar(
            x=ft_group["fuel_type"],
            y=ft_group["total_cost"],
            marker_color=[BRAND_COLOR, SUCCESS_COLOR, WARNING_COLOR][:len(ft_group)],
            text=[f"PKR {v/1e6:.1f}M" for v in ft_group["total_cost"]],
            textposition="outside", textfont=dict(color="#c8dff0"),
        ))
        fig_ft.update_layout(
            template="plotly_white", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#c8dff0"), margin=dict(l=14,r=14,t=40,b=14),
            title="Total Fuel Cost by Fuel Type",
            xaxis=dict(gridcolor="rgba(255,255,255,0.06)", tickfont=dict(color="#c8dff0")),
            yaxis=dict(gridcolor="rgba(255,255,255,0.06)", tickfont=dict(color="#c8dff0")),
        )
        st.plotly_chart(fig_ft, use_container_width=True)

    # ── Row 3: Odometer distribution ────────────────────────────────
    st.markdown(section_header("Vehicle Age & Mileage"), unsafe_allow_html=True)
    c5, c6 = st.columns(2)
    with c5:
        fig_odo = go.Figure(go.Histogram(
            x=veh_f["odometer_km"], nbinsx=20,
            marker_color=BRAND_COLOR, opacity=0.8,
        ))
        fig_odo.add_vline(x=100000, line_dash="dash", line_color=WARNING_COLOR,
                          annotation_text="100K KM mark", annotation_font_color=WARNING_COLOR)
        fig_odo.update_layout(
            template="plotly_white", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#c8dff0"), margin=dict(l=14,r=14,t=40,b=14),
            title="Odometer Reading Distribution (km)",
            xaxis=dict(gridcolor="rgba(255,255,255,0.06)", tickfont=dict(color="#c8dff0")),
            yaxis=dict(gridcolor="rgba(255,255,255,0.06)", tickfont=dict(color="#c8dff0")),
        )
        st.plotly_chart(fig_odo, use_container_width=True)
    with c6:
        age_grp = veh_f.groupby("year").size().reset_index(name="count")
        fig_age = go.Figure(go.Bar(
            x=age_grp["year"].astype(str), y=age_grp["count"],
            marker_color=BRAND_COLOR, opacity=0.85,
        ))
        fig_age.update_layout(
            template="plotly_white", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#c8dff0"), margin=dict(l=14,r=14,t=40,b=14),
            title="Fleet Age Profile (by Model Year)",
            xaxis=dict(gridcolor="rgba(255,255,255,0.06)", tickfont=dict(color="#c8dff0")),
            yaxis=dict(gridcolor="rgba(255,255,255,0.06)", tickfont=dict(color="#c8dff0")),
        )
        st.plotly_chart(fig_age, use_container_width=True)

    # ── Fuel Anomaly Detection ────────────────────────────────────────
    st.markdown(section_header("⚡ Fuel Anomaly Detection (AI)"), unsafe_allow_html=True)
    st.markdown('<div style="font-size:0.83rem;color:#7a9ab4;margin-bottom:10px;">Trips where fuel efficiency deviates >2σ from vehicle baseline (potential fuel theft or sensor issues).</div>', unsafe_allow_html=True)

    with st.spinner("Running anomaly detection …"):
        anomalies = detect_fuel_anomalies(fuel_f)

    if len(anomalies) > 0:
        st.markdown(alert(f"⚠️ {len(anomalies)} fuel anomalies detected across your fleet.", "warning"), unsafe_allow_html=True)
        show_anom = anomalies[["vehicle_id","trip_id","fill_date","fuel_type",
                                "fuel_efficiency_kmpl","veh_mean_eff","z_score","km_driven"]].head(50)
        st.dataframe(show_anom.reset_index(drop=True), use_container_width=True, height=280)
    else:
        st.markdown(alert("✅ No fuel anomalies detected.", "info"), unsafe_allow_html=True)

    # ── Predictive Maintenance ────────────────────────────────────────
    st.markdown(section_header("🤖 Predictive Maintenance (AI)"), unsafe_allow_html=True)
    with st.spinner("Training maintenance predictor …"):
        clf_m, le_type, feat_m, report_m, feat_imp_m = train_maintenance_model(maint, vehicles)

    acc_m = report_m.get("accuracy", 0)
    st.info(f"Maintenance classifier accuracy: **{acc_m*100:.1f}%** — predicts vehicles likely needing service within 14 days.")

    # Vehicles at risk
    veh_risk = vehicles.copy()
    veh_risk["vehicle_age"] = 2026 - veh_risk["year"]
    last_maint = maint.groupby("vehicle_id")["maintenance_date"].max().reset_index()
    last_maint["maintenance_date"] = pd.to_datetime(last_maint["maintenance_date"])
    last_maint["days_since_last"]  = (pd.Timestamp("2026-07-01") - last_maint["maintenance_date"]).dt.days
    veh_risk = veh_risk.merge(last_maint[["vehicle_id","days_since_last"]], on="vehicle_id", how="left")
    veh_risk["days_since_last"] = veh_risk["days_since_last"].fillna(180)

    try:
        common_type = le_type.transform([maint["maintenance_type"].mode()[0]])[0]
    except Exception:
        common_type = 0

    X_risk = veh_risk[["vehicle_age","odometer_km","days_since_last"]].copy()
    X_risk["type_enc"] = common_type
    X_risk = X_risk[feat_m].fillna(X_risk.median())
    veh_risk["maint_risk_pct"] = (clf_m.predict_proba(X_risk)[:, 1] * 100).round(1)
    high_risk_veh = veh_risk[veh_risk["maint_risk_pct"] > 60].sort_values("maint_risk_pct", ascending=False)

    if len(high_risk_veh) > 0:
        st.markdown(alert(f"🔴 {len(high_risk_veh)} vehicles flagged as high-risk for upcoming maintenance.", "critical"), unsafe_allow_html=True)
        st.dataframe(
            high_risk_veh[["vehicle_id","make","model","year","odometer_km","days_since_last","maint_risk_pct","status"]]
            .reset_index(drop=True), use_container_width=True, height=260
        )
    else:
        st.markdown(alert("✅ No vehicles flagged as high-risk right now.", "info"), unsafe_allow_html=True)

    # ── Vehicle table ────────────────────────────────────────────────
    st.markdown(section_header("Vehicle Register"), unsafe_allow_html=True)
    show_cols = ["vehicle_id","make","model","year","registration_no","status",
                 "condition_rating","odometer_km","fuel_type","gps_enabled","telematics_enabled"]
    st.dataframe(veh_f[show_cols].reset_index(drop=True), use_container_width=True, height=320)
