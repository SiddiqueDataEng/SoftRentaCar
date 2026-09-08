"""
Page 3 – Operations & Trips
Trip analytics, city demand, route analysis, booking patterns.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from app.style import inject_css, kpi_card, section_header
from app.charts import (
    trips_heatmap, booking_type_trend, city_demand_bar,
    trip_status_funnel, revenue_by_booking_type,
)
from app.style import PLOTLY_COLORS, BRAND_COLOR, SUCCESS_COLOR


def render(dfs: dict):
    inject_css()

    st.markdown('<div style="font-size:1.6rem;font-weight:800;color:#E63946;margin-bottom:4px;">🚗 Operations & Trips</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:0.82rem;color:#5a7a96;">Booking patterns, route analytics, and fleet demand intelligence</div>', unsafe_allow_html=True)
    st.markdown("---")

    trips    = dfs["trips"]
    vehicles = dfs["vehicles"]

    # ── Filters ──────────────────────────────────────────────────────
    cf1, cf2, cf3, cf4 = st.columns(4)
    years = ["All"] + sorted(trips["pickup_year"].dropna().unique().astype(int).tolist(), reverse=True)
    sel_yr = cf1.selectbox("Year", years)

    btype_list = ["All"] + sorted(trips["booking_type"].unique().tolist())
    sel_bt = cf2.selectbox("Booking Type", btype_list)

    cities_list = ["All"] + sorted(trips["pickup_city"].unique().tolist())
    sel_city = cf3.selectbox("City", cities_list)

    statuses = ["All"] + trips["status"].unique().tolist()
    sel_st = cf4.selectbox("Status", statuses)

    t = trips.copy()
    if sel_yr != "All":   t = t[t["pickup_year"] == int(sel_yr)]
    if sel_bt != "All":   t = t[t["booking_type"] == sel_bt]
    if sel_city != "All": t = t[t["pickup_city"] == sel_city]
    if sel_st != "All":   t = t[t["status"] == sel_st]

    # ── KPIs ─────────────────────────────────────────────────────────
    completed = t[t["status"] == "Completed"]
    cols = st.columns(6)
    kpis = [
        (f"{len(t):,}",                   "Total Bookings"),
        (f"{len(completed):,}",           "Completed"),
        (f"{(t['status']=='Cancelled').sum():,}", "Cancelled"),
        (f"{completed['distance_km'].mean():.0f} km", "Avg Distance"),
        (f"PKR {completed['revenue_pkr'].mean():,.0f}", "Avg Fare"),
        (f"{completed['duration_days'].mean():.2f}d",   "Avg Duration"),
    ]
    for col, (v, l) in zip(cols, kpis):
        col.markdown(kpi_card(v, l), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")

    # ── Row 1: Status funnel + City demand ─────────────────────────
    st.markdown(section_header("Trip Status & City Demand"), unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(trip_status_funnel(t), use_container_width=True)
    with c2:
        st.plotly_chart(city_demand_bar(t), use_container_width=True)

    # ── Row 2: Demand heatmap ───────────────────────────────────────
    st.markdown(section_header("Booking Demand — Hour × Day"), unsafe_allow_html=True)
    st.plotly_chart(trips_heatmap(t), use_container_width=True)

    # ── Row 3: Booking type trend + Revenue ─────────────────────────
    st.markdown(section_header("Booking Type Trends"), unsafe_allow_html=True)
    c3, c4 = st.columns(2)
    with c3:
        st.plotly_chart(booking_type_trend(t), use_container_width=True)
    with c4:
        st.plotly_chart(revenue_by_booking_type(t), use_container_width=True)

    # ── Row 4: Route analysis ────────────────────────────────────────
    st.markdown(section_header("Intercity Route Analysis"), unsafe_allow_html=True)
    intercity = t[(t["pickup_city"] != t["dropoff_city"]) & (t["status"] == "Completed")].copy()
    intercity["route"] = intercity["pickup_city"] + " → " + intercity["dropoff_city"]
    route_stats = intercity.groupby("route").agg(
        trips=("trip_id", "count"),
        avg_fare=("revenue_pkr", "mean"),
        avg_km=("distance_km", "mean"),
        total_rev=("revenue_pkr", "sum"),
    ).reset_index().sort_values("trips", ascending=False).head(15)

    fig_route = go.Figure(go.Bar(
        x=route_stats["trips"],
        y=route_stats["route"],
        orientation="h",
        marker_color=BRAND_COLOR,
        text=[f"{v:,}" for v in route_stats["trips"]],
        textposition="outside",
        textfont=dict(color="#c8dff0", size=10),
    ))
    fig_route.update_layout(
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#c8dff0"),
        margin=dict(l=160, r=60, t=40, b=14),
        title=dict(text="Top 15 Intercity Routes by Trip Count", font=dict(color="#c8dff0")),
        xaxis=dict(gridcolor="rgba(255,255,255,0.06)", tickfont=dict(color="#c8dff0")),
        yaxis=dict(tickfont=dict(color="#c8dff0"), autorange="reversed"),
    )
    st.plotly_chart(fig_route, use_container_width=True)

    # ── Row 5: Distance distribution ────────────────────────────────
    st.markdown(section_header("Trip Distance Distribution"), unsafe_allow_html=True)
    c5, c6 = st.columns(2)
    with c5:
        fig_dist = go.Figure(go.Histogram(
            x=completed["distance_km"],
            nbinsx=40,
            marker_color=BRAND_COLOR,
            opacity=0.8,
        ))
        fig_dist.update_layout(
            template="plotly_white", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#c8dff0"), margin=dict(l=14,r=14,t=40,b=14),
            title="Trip Distance Distribution (km)",
            xaxis=dict(gridcolor="rgba(255,255,255,0.06)", tickfont=dict(color="#c8dff0")),
            yaxis=dict(gridcolor="rgba(255,255,255,0.06)", tickfont=dict(color="#c8dff0")),
        )
        st.plotly_chart(fig_dist, use_container_width=True)
    with c6:
        fig_dur = go.Figure(go.Histogram(
            x=completed["duration_days"].clip(0, 15),
            nbinsx=30,
            marker_color="#457B9D",
            opacity=0.8,
        ))
        fig_dur.update_layout(
            template="plotly_white", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#c8dff0"), margin=dict(l=14,r=14,t=40,b=14),
            title="Trip Duration Distribution (days)",
            xaxis=dict(gridcolor="rgba(255,255,255,0.06)", tickfont=dict(color="#c8dff0")),
            yaxis=dict(gridcolor="rgba(255,255,255,0.06)", tickfont=dict(color="#c8dff0")),
        )
        st.plotly_chart(fig_dur, use_container_width=True)

    # ── Raw data table (filtered) ────────────────────────────────────
    st.markdown(section_header("Trip Records"), unsafe_allow_html=True)
    show_cols = ["trip_id","booking_type","pickup_city","dropoff_city","pickup_datetime",
                 "duration_days","distance_km","revenue_pkr","status","with_driver"]
    st.dataframe(t[show_cols].head(500).reset_index(drop=True), use_container_width=True, height=320)
