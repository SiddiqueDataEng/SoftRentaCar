"""Demand Map"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from page_modules._shared import (
    inject, get_data, fmt, kpi, sec, dark_layout,
    BRAND, NAVY, STEEL, GREEN, AMBER, ORANGE, TEXT, GRID, BG, COLORS
)

inject()
dfs = get_data()
trips = dfs["trips"]

st.markdown(f'<div style="font-size:1.5rem;font-weight:800;color:{BRAND};margin-bottom:4px;">🗺️ Demand Map</div>', unsafe_allow_html=True)
st.markdown(f'<div style="font-size:.8rem;color:#5a7a96;">Geographic demand intelligence and fleet deployment insights</div>', unsafe_allow_html=True)
st.markdown("<hr style='border-color:#1e2f44;margin:6px 0 14px 0'>", unsafe_allow_html=True)

# ── Filters ────────────────────────────────────────────────────────────
cf = st.columns(3)
yrs = ["All"]+sorted(trips["pickup_year"].dropna().unique().astype(int).tolist(),reverse=True)
sel_yr = cf[0].selectbox("Year", yrs)
bts = ["All"]+sorted(trips["booking_type"].unique().tolist())
sel_bt = cf[1].selectbox("Booking Type", bts)
sel_st = cf[2].selectbox("Status", ["All","Completed","Cancelled"])

t = trips.copy()
if sel_yr!="All": t = t[t["pickup_year"]==int(sel_yr)]
if sel_bt!="All": t = t[t["booking_type"]==sel_bt]
if sel_st!="All": t = t[t["status"]==sel_st]

# ── Demand bubble map ──────────────────────────────────────────────────
sec("📍 Trip Density — Pakistan")
comp = t[t["status"]=="Completed"]
cg = comp.groupby(["pickup_city","pickup_lat","pickup_lon"]).size().reset_index(name="trips")

fig1 = go.Figure(go.Scattermapbox(
    lat=cg["pickup_lat"], lon=cg["pickup_lon"], mode="markers",
    marker=go.scattermapbox.Marker(
        size=cg["trips"].apply(lambda x: min(50,max(10,x/50))),
        color=cg["trips"],
        colorscale=[[0,NAVY],[0.5,STEEL],[1,BRAND]],
        showscale=True, opacity=0.85),
    text=cg.apply(lambda r: f"{r['pickup_city']}: {r['trips']:,} trips",axis=1),
    hoverinfo="text"))
fig1.update_layout(mapbox=dict(style="carto-darkmatter",
    center=dict(lat=30.3753,lon=69.3451), zoom=4.5),
    margin=dict(l=0,r=0,t=30,b=0), paper_bgcolor=BG, height=440,
    title=dict(text="Demand Heat Map — Pakistan", font=dict(color=TEXT,size=13)))
st.plotly_chart(fig1, use_container_width=True)

# ── City KPI grid ──────────────────────────────────────────────────────
sec("🏙️ City Breakdown")
city_stats = comp.groupby("pickup_city").agg(
    trips=("trip_id","count"), revenue=("revenue_pkr","sum"),
    avg_fare=("revenue_pkr","mean")).reset_index().sort_values("trips",ascending=False)

cols = st.columns(4)
for i,(_, r) in enumerate(city_stats.head(8).iterrows()):
    with cols[i%4]:
        st.markdown(f"""
<div class="kpi-card" style="margin-bottom:10px;">
  <div style="font-size:1rem;font-weight:700;color:{BRAND};">{r['pickup_city']}</div>
  <div style="font-size:.8rem;color:#8eaac4;margin-top:3px;">{r['trips']:,} trips</div>
  <div style="font-size:.75rem;color:#5a7a96;">PKR {r['revenue']/1e6:.1f}M revenue</div>
  <div style="font-size:.72rem;color:#4a6a84;">Avg PKR {r['avg_fare']:,.0f}</div>
</div>""", unsafe_allow_html=True)

# ── Sankey intercity flow ──────────────────────────────────────────────
sec("🔀 Intercity Flow")
ic = comp[(comp["pickup_city"]!=comp["dropoff_city"])]
top_cities = ic["pickup_city"].value_counts().head(8).index.tolist()
flow = ic[ic["pickup_city"].isin(top_cities) & ic["dropoff_city"].isin(top_cities)]
mx   = flow.groupby(["pickup_city","dropoff_city"]).size().reset_index(name="n")

fig2 = go.Figure(go.Sankey(
    node=dict(pad=15, thickness=20,
              label=top_cities+top_cities,
              color=[BRAND]*len(top_cities)+[STEEL]*len(top_cities)),
    link=dict(
        source=[top_cities.index(r) for _,r in mx.iterrows() if r["pickup_city"] in top_cities],
        target=[len(top_cities)+top_cities.index(r) for _,r in mx.iterrows() if r["dropoff_city"] in top_cities],
        value=mx["n"].tolist(), color="rgba(230,57,70,.25)")))
fig2.update_layout(paper_bgcolor=BG, font=dict(color=TEXT,size=11),
    margin=dict(l=14,r=14,t=40,b=14), height=400,
    title=dict(text="Intercity Trip Flow (Top 8 Cities)", font=dict(color=TEXT,size=13)))
st.plotly_chart(fig2, use_container_width=True)

# ── Pickup vs dropoff balance ──────────────────────────────────────────
sec("⚖️ Pickup vs Dropoff Balance")
pu = t.groupby("pickup_city").size().reset_index(name="pickups")
do = t.groupby("dropoff_city").size().reset_index(name="dropoffs")
bal = pu.merge(do,left_on="pickup_city",right_on="dropoff_city",how="outer")
bal["city"] = bal["pickup_city"].fillna(bal["dropoff_city"])
bal = bal.fillna(0).sort_values("pickups",ascending=False).head(12)

fig3 = go.Figure()
fig3.add_trace(go.Bar(name="Pickups",  x=bal["city"], y=bal["pickups"],  marker_color=BRAND,  opacity=.85))
fig3.add_trace(go.Bar(name="Dropoffs", x=bal["city"], y=bal["dropoffs"], marker_color=STEEL,  opacity=.85))
fig3.update_layout(barmode="group")
dark_layout(fig3, "Pickup vs Dropoff by City", height=320)
st.plotly_chart(fig3, use_container_width=True)

# ── GPS scatter (sample) ───────────────────────────────────────────────
sec("📡 GPS Pickup Scatter (2,000 sample)")
sample = comp.dropna(subset=["pickup_lat","pickup_lon"]).sample(min(2000,len(comp)),random_state=42)
fig4 = go.Figure(go.Scattermapbox(
    lat=sample["pickup_lat"], lon=sample["pickup_lon"], mode="markers",
    marker=go.scattermapbox.Marker(size=5,color=BRAND,opacity=.4),
    text=sample["pickup_city"], hoverinfo="text"))
fig4.update_layout(mapbox=dict(style="carto-darkmatter",
    center=dict(lat=30.3753,lon=69.3451), zoom=4.8),
    margin=dict(l=0,r=0,t=30,b=0), paper_bgcolor=BG, height=400,
    title=dict(text="GPS Pickup Points", font=dict(color=TEXT,size=13)))
st.plotly_chart(fig4, use_container_width=True)
