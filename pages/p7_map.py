"""
Page 7 – Demand Map
Interactive Pakistan heatmap with city-level drill-down.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from app.style import inject_css, kpi_card, section_header
from app.charts import demand_map
from app.style import BRAND_COLOR, BRAND_ACCENT, PLOTLY_COLORS


def render(dfs: dict):
    inject_css()

    st.markdown('<div style="font-size:1.6rem;font-weight:800;color:#E63946;margin-bottom:4px;">🗺️ Demand Map</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:0.82rem;color:#5a7a96;">Geographic demand intelligence and fleet deployment insights</div>', unsafe_allow_html=True)
    st.markdown("---")

    trips = dfs["trips"]
    veh   = dfs["vehicles"]

    # ── Filters ──────────────────────────────────────────────────────
    c1, c2, c3 = st.columns(3)
    years = ["All"] + sorted(trips["pickup_year"].dropna().unique().astype(int).tolist(), reverse=True)
    sel_yr = c1.selectbox("Year", years)
    btypes = ["All"] + sorted(trips["booking_type"].unique().tolist())
    sel_bt = c2.selectbox("Booking Type", btypes)
    status_opts = ["All", "Completed", "Cancelled"]
    sel_st = c3.selectbox("Status", status_opts)

    t = trips.copy()
    if sel_yr != "All": t = t[t["pickup_year"] == int(sel_yr)]
    if sel_bt != "All": t = t[t["booking_type"] == sel_bt]
    if sel_st != "All": t = t[t["status"] == sel_st]

    # ── Main demand map ───────────────────────────────────────────────
    st.markdown(section_header("Trip Density – Pakistan"), unsafe_allow_html=True)
    st.plotly_chart(demand_map(t), use_container_width=True)

    # ── City KPI cards ────────────────────────────────────────────────
    st.markdown(section_header("City Breakdown"), unsafe_allow_html=True)
    city_stats = t[t["status"]=="Completed"].groupby("pickup_city").agg(
        trips=("trip_id","count"),
        revenue=("revenue_pkr","sum"),
        avg_fare=("revenue_pkr","mean"),
        avg_km=("distance_km","mean"),
    ).reset_index().sort_values("trips", ascending=False)

    cols = st.columns(4)
    for i, (_, row) in enumerate(city_stats.head(8).iterrows()):
        with cols[i % 4]:
            st.markdown(
                f"""<div class="kpi-card" style="margin-bottom:10px;">
                    <div style="font-size:1.1rem;font-weight:700;color:#E63946;">{row['pickup_city']}</div>
                    <div style="font-size:0.82rem;color:#8eaac4;margin-top:4px;">{row['trips']:,} trips</div>
                    <div style="font-size:0.78rem;color:#5a7a96;">PKR {row['revenue']/1e6:.1f}M revenue</div>
                    <div style="font-size:0.75rem;color:#4a6a84;">Avg fare PKR {row['avg_fare']:,.0f}</div>
                </div>""",
                unsafe_allow_html=True,
            )

    # ── Intercity flow matrix (chord-like) ───────────────────────────
    st.markdown(section_header("Intercity Flow Analysis"), unsafe_allow_html=True)
    intercity = t[(t["pickup_city"] != t["dropoff_city"]) & (t["status"] == "Completed")].copy()
    top_cities = intercity["pickup_city"].value_counts().head(8).index.tolist()
    flow = intercity[intercity["pickup_city"].isin(top_cities) & intercity["dropoff_city"].isin(top_cities)]
    matrix = flow.groupby(["pickup_city","dropoff_city"]).size().reset_index(name="count")

    fig_flow = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15, thickness=20,
            line=dict(color="black", width=0.5),
            label=top_cities + top_cities,
            color=[BRAND_COLOR] * len(top_cities) + [BRAND_ACCENT] * len(top_cities),
        ),
        link=dict(
            source=[top_cities.index(r) for r in matrix["pickup_city"]  if r in top_cities],
            target=[len(top_cities) + top_cities.index(r) for r in matrix["dropoff_city"] if r in top_cities],
            value=matrix["count"].tolist(),
            color="rgba(230,57,70,0.25)",
        ),
    )])
    fig_flow.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#c8dff0", size=11),
        margin=dict(l=14, r=14, t=40, b=14),
        title=dict(text="Intercity Trip Flow (Top 8 Cities)", font=dict(color="#c8dff0", size=13)),
    )
    st.plotly_chart(fig_flow, use_container_width=True)

    # ── Pickup vs Dropoff comparison ──────────────────────────────────
    st.markdown(section_header("Pickup vs Dropoff Balance"), unsafe_allow_html=True)
    pickup_cnt  = t.groupby("pickup_city").size().reset_index(name="pickups")
    dropoff_cnt = t.groupby("dropoff_city").size().reset_index(name="dropoffs")
    bal = pickup_cnt.merge(dropoff_cnt, left_on="pickup_city", right_on="dropoff_city", how="outer")
    bal["city"]     = bal["pickup_city"].fillna(bal["dropoff_city"])
    bal["pickups"]  = bal["pickups"].fillna(0)
    bal["dropoffs"] = bal["dropoffs"].fillna(0)
    bal["imbalance"]= bal["pickups"] - bal["dropoffs"]
    bal = bal.sort_values("pickups", ascending=False).head(12)

    fig_bal = go.Figure()
    fig_bal.add_trace(go.Bar(name="Pickups",  x=bal["city"], y=bal["pickups"],  marker_color=BRAND_COLOR,   opacity=0.85))
    fig_bal.add_trace(go.Bar(name="Dropoffs", x=bal["city"], y=bal["dropoffs"], marker_color=BRAND_ACCENT,  opacity=0.85))
    fig_bal.update_layout(
        barmode="group",
        template="plotly_white", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#c8dff0"), margin=dict(l=14,r=14,t=40,b=14),
        title=dict(text="Pickup vs Dropoff by City", font=dict(color="#c8dff0",size=13)),
        xaxis=dict(gridcolor="rgba(255,255,255,0.06)", tickfont=dict(color="#c8dff0")),
        yaxis=dict(gridcolor="rgba(255,255,255,0.06)", tickfont=dict(color="#c8dff0")),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#c8dff0")),
    )
    st.plotly_chart(fig_bal, use_container_width=True)

    # ── GPS heatmap (scatter based on lat/lon) ────────────────────────
    st.markdown(section_header("GPS Pickup Density (Sample)"), unsafe_allow_html=True)
    sample = t[t["status"]=="Completed"].dropna(subset=["pickup_lat","pickup_lon"]).sample(min(2000, len(t)), random_state=42)

    fig_gps = go.Figure(go.Scattermapbox(
        lat=sample["pickup_lat"],
        lon=sample["pickup_lon"],
        mode="markers",
        marker=go.scattermapbox.Marker(
            size=5, color=BRAND_COLOR, opacity=0.4,
        ),
        text=sample["pickup_city"],
        hoverinfo="text",
    ))
    fig_gps.update_layout(
        mapbox=dict(
            style="carto-darkmatter",
            center=dict(lat=30.3753, lon=69.3451),
            zoom=4.8,
        ),
        margin=dict(l=0, r=0, t=30, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        title=dict(text="GPS Pickup Points (Sample 2,000)", font=dict(color="#c8dff0", size=13)),
        height=420,
    )
    st.plotly_chart(fig_gps, use_container_width=True)
