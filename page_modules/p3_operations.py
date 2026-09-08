"""Operations & Trips"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from page_modules._shared import (
    inject, get_data, fmt, kpi, sec, alert_box, dark_layout,
    BRAND, NAVY, STEEL, GREEN, AMBER, ORANGE, TEXT, GRID, BG, COLORS
)

inject()
dfs = get_data()
trips = dfs["trips"]

st.markdown(f'<div style="font-size:1.5rem;font-weight:800;color:{BRAND};margin-bottom:4px;">🚗 Operations & Trips</div>', unsafe_allow_html=True)
st.markdown(f'<div style="font-size:.8rem;color:#5a7a96;">Booking patterns, route analytics and demand intelligence</div>', unsafe_allow_html=True)
st.markdown("<hr style='border-color:#1e2f44;margin:6px 0 14px 0'>", unsafe_allow_html=True)

# ── Filters ────────────────────────────────────────────────────────────
cf = st.columns(4)
years = ["All"] + sorted(trips["pickup_year"].dropna().unique().astype(int).tolist(), reverse=True)
sel_yr  = cf[0].selectbox("Year",         years,   key="ops_yr")
btypes  = ["All"] + sorted(trips["booking_type"].unique().tolist())
sel_bt  = cf[1].selectbox("Booking Type", btypes,  key="ops_bt")
cities  = ["All"] + sorted(trips["pickup_city"].unique().tolist())
sel_ci  = cf[2].selectbox("City",         cities,  key="ops_ci")
stats   = ["All"] + trips["status"].unique().tolist()
sel_st  = cf[3].selectbox("Status",       stats,   key="ops_st")

t = trips.copy()
if sel_yr != "All": t = t[t["pickup_year"]==int(sel_yr)]
if sel_bt != "All": t = t[t["booking_type"]==sel_bt]
if sel_ci != "All": t = t[t["pickup_city"]==sel_ci]
if sel_st != "All": t = t[t["status"]==sel_st]

comp = t[t["status"]=="Completed"]

# ── KPIs ───────────────────────────────────────────────────────────────
c = st.columns(6)
kpi(c[0], f"{len(t):,}",                        "Total Bookings",    "")
kpi(c[1], f"{len(comp):,}",                     "Completed",         f"{len(comp)/max(len(t),1)*100:.1f}%", True)
kpi(c[2], f"{(t['status']=='Cancelled').sum():,}","Cancelled",        f"{(t['status']=='Cancelled').sum()/max(len(t),1)*100:.1f}%", False)
kpi(c[3], f"{comp['distance_km'].mean():.0f} km","Avg Distance",      "")
kpi(c[4], fmt(comp['revenue_pkr'].mean()),       "Avg Fare",          "")
kpi(c[5], f"{comp['duration_days'].mean():.2f}d","Avg Duration",      "")

st.markdown("<hr style='border-color:#1e2f44;margin:14px 0'>", unsafe_allow_html=True)

# ── Status funnel + city demand ────────────────────────────────────────
sec("🔍 Trip Status & City Demand")
col1, col2 = st.columns(2)

with col1:
    sc = t["status"].value_counts().reset_index(); sc.columns=["status","n"]
    cmap = {"Completed":GREEN,"Cancelled":ORANGE,"In Progress":AMBER,"No Show":STEEL}
    fig = go.Figure(go.Funnel(y=sc["status"], x=sc["n"],
        marker=dict(color=[cmap.get(s,BRAND) for s in sc["status"]]),
        textinfo="value+percent initial", textfont=dict(color="#fff")))
    dark_layout(fig, "Trip Status Funnel", height=320)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    cg = t.groupby("pickup_city").size().reset_index(name="n").sort_values("n",ascending=False).head(12)
    fig2 = go.Figure(go.Bar(x=cg["pickup_city"], y=cg["n"], marker_color=BRAND, opacity=.85))
    dark_layout(fig2, "Trips by Pickup City", height=320)
    st.plotly_chart(fig2, use_container_width=True)

# ── Demand heatmap ─────────────────────────────────────────────────────
sec("⏰ Demand Heatmap — Hour × Day of Week")
dow_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
pv = t.groupby(["pickup_dow","pickup_hour"]).size().reset_index(name="n")
pv["pickup_dow"] = pd.Categorical(pv["pickup_dow"], categories=dow_order, ordered=True)
mx = pv.pivot(index="pickup_dow", columns="pickup_hour", values="n").fillna(0)
fig3 = go.Figure(go.Heatmap(
    z=mx.values, x=[f"{h:02d}:00" for h in mx.columns], y=mx.index.tolist(),
    colorscale=[[0,"#0f1117"],[0.4,NAVY],[0.75,STEEL],[1,BRAND]], showscale=True))
dark_layout(fig3, "Bookings by Hour & Day", height=280)
st.plotly_chart(fig3, use_container_width=True)

# ── Booking type monthly trend ─────────────────────────────────────────
sec("📊 Booking Type Trend")
col3, col4 = st.columns(2)
with col3:
    g = t.groupby(["pickup_month","booking_type"]).size().reset_index(name="n")
    fig4 = go.Figure()
    for i,bt in enumerate(g["booking_type"].unique()):
        sub = g[g["booking_type"]==bt]
        fig4.add_trace(go.Scatter(x=sub["pickup_month"], y=sub["n"], name=bt,
            stackgroup="one", fill="tonexty", line=dict(color=COLORS[i%len(COLORS)],width=1)))
    dark_layout(fig4, "Monthly Bookings by Type", xangle=-45)
    st.plotly_chart(fig4, use_container_width=True)

with col4:
    gr = comp.groupby("booking_type")["revenue_pkr"].sum().reset_index().sort_values("revenue_pkr")
    fig5 = go.Figure(go.Bar(x=gr["revenue_pkr"]/1e6, y=gr["booking_type"], orientation="h",
        marker_color=BRAND, text=[f"{v:.1f}M" for v in gr["revenue_pkr"]/1e6],
        textposition="outside", textfont=dict(color=TEXT, size=9)))
    dark_layout(fig5, "Revenue by Booking Type (PKR M)")
    st.plotly_chart(fig5, use_container_width=True)

# ── Intercity routes ───────────────────────────────────────────────────
sec("🛣️ Top Intercity Routes")
ic = comp[(comp["pickup_city"]!=comp["dropoff_city"])].copy()
ic["route"] = ic["pickup_city"] + " → " + ic["dropoff_city"]
rts = ic.groupby("route").agg(trips=("trip_id","count"),avg_fare=("revenue_pkr","mean"),
    avg_km=("distance_km","mean")).reset_index().sort_values("trips",ascending=False).head(15)
fig6 = go.Figure(go.Bar(x=rts["trips"], y=rts["route"], orientation="h",
    marker_color=BRAND, text=rts["trips"].astype(str), textposition="outside",
    textfont=dict(color=TEXT, size=9)))
fig6.update_layout(margin=dict(l=160,r=60,t=44,b=12))
dark_layout(fig6, "Top 15 Routes by Trip Count", height=420)
fig6.update_yaxes(autorange="reversed")
st.plotly_chart(fig6, use_container_width=True)

# ── Distance & duration histograms ─────────────────────────────────────
sec("📏 Distance & Duration Distribution")
col5, col6 = st.columns(2)
with col5:
    fig7 = go.Figure(go.Histogram(x=comp["distance_km"], nbinsx=40, marker_color=BRAND, opacity=.8))
    dark_layout(fig7, "Trip Distance Distribution (km)", height=280)
    st.plotly_chart(fig7, use_container_width=True)
with col6:
    fig8 = go.Figure(go.Histogram(x=comp["duration_days"].clip(0,15), nbinsx=30, marker_color=STEEL, opacity=.8))
    dark_layout(fig8, "Trip Duration Distribution (days)", height=280)
    st.plotly_chart(fig8, use_container_width=True)

# ── Raw trips table ────────────────────────────────────────────────────
sec("📋 Trip Records")
show = ["trip_id","booking_type","pickup_city","dropoff_city","pickup_datetime",
        "duration_days","distance_km","revenue_pkr","status","with_driver"]
st.dataframe(t[show].head(500).reset_index(drop=True), use_container_width=True, height=300)
