"""Demand Map — with Carto authenticated tiles"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from page_modules._shared import (
    inject, get_data, fmt, kpi, sec, dark_layout,
    BRAND, NAVY, STEEL, GREEN, AMBER, ORANGE, TEXT, GRID, BG, COLORS,
)
from app.carto import get_carto_key, CARTO_STYLES

inject()
dfs   = get_data()
trips = dfs["trips"]

# ── Resolve Carto key ──────────────────────────────────────────────────
CARTO_KEY = get_carto_key()

st.markdown(
    f'<div style="font-size:1.5rem;font-weight:800;color:{BRAND};margin-bottom:4px;">🗺️ Demand Map</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div style="font-size:.8rem;color:#5a7a96;">Geographic demand intelligence — powered by Carto</div>',
    unsafe_allow_html=True,
)
st.markdown("<hr style='border-color:#1e2f44;margin:6px 0 12px 0'>", unsafe_allow_html=True)

# ── Filters + map style ────────────────────────────────────────────────
cf = st.columns(4)
yrs    = ["All"] + sorted(trips["pickup_year"].dropna().unique().astype(int).tolist(), reverse=True)
sel_yr = cf[0].selectbox("Year",         yrs,                             key="map_yr")
bts    = ["All"] + sorted(trips["booking_type"].unique().tolist())
sel_bt = cf[1].selectbox("Booking Type", bts,                             key="map_bt")
sel_st = cf[2].selectbox("Status",       ["All","Completed","Cancelled"], key="map_st")
sel_style = cf[3].selectbox("🗺️ Map Style", list(CARTO_STYLES.keys()),    key="map_style")

map_style = CARTO_STYLES[sel_style]   # e.g. "carto-darkmatter"

# ── Filter data ────────────────────────────────────────────────────────
t = trips.copy()
if sel_yr != "All": t = t[t["pickup_year"] == int(sel_yr)]
if sel_bt != "All": t = t[t["booking_type"] == sel_bt]
if sel_st != "All": t = t[t["status"] == sel_st]
comp = t[t["status"] == "Completed"]


# ── Helper: apply mapbox layout ────────────────────────────────────────
def _mapbox_layout(fig, title, zoom=4.5, height=460):
    fig.update_layout(
        mapbox=dict(
            accesstoken=CARTO_KEY,
            style=map_style,
            center=dict(lat=30.3753, lon=69.3451),
            zoom=zoom,
        ),
        margin=dict(l=0, r=0, t=36, b=0),
        paper_bgcolor=BG,
        font=dict(family="Inter", color=TEXT, size=12),
        height=height,
        title=dict(text=title, font=dict(color=TEXT, size=13)),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=TEXT, size=10)),
    )


# ── 1. Demand Bubble Map ───────────────────────────────────────────────
sec("📍 Trip Density — Pakistan")

cg = (
    comp.groupby(["pickup_city", "pickup_lat", "pickup_lon"])
    .size()
    .reset_index(name="trips")
)
cg["revenue"] = (
    comp.groupby(["pickup_city", "pickup_lat", "pickup_lon"])["revenue_pkr"]
    .sum()
    .values
)

fig1 = go.Figure(go.Scattermapbox(
    lat=cg["pickup_lat"],
    lon=cg["pickup_lon"],
    mode="markers",
    marker=go.scattermapbox.Marker(
        size=cg["trips"].apply(lambda x: min(55, max(12, x / 40))),
        color=cg["trips"],
        colorscale=[[0, NAVY], [0.4, STEEL], [0.75, AMBER], [1, BRAND]],
        showscale=True,
        opacity=0.88,
        colorbar=dict(
            title=dict(text="Trips", font=dict(color=TEXT, size=11)),
            tickfont=dict(color=TEXT, size=9),
            bgcolor="rgba(15,17,23,.7)",
            bordercolor=GRID,
        ),
    ),
    text=cg.apply(
        lambda r: f"<b>{r['pickup_city']}</b><br>{r['trips']:,} trips<br>PKR {r['revenue']/1e6:.1f}M",
        axis=1,
    ),
    hoverinfo="text",
))
_mapbox_layout(fig1, f"Demand Heat Map — Pakistan ({sel_style})", zoom=4.5, height=480)
st.plotly_chart(fig1, use_container_width=True)

# ── 2. City KPI grid ───────────────────────────────────────────────────
sec("🏙️ City Performance")
city_stats = (
    comp.groupby("pickup_city")
    .agg(trips=("trip_id","count"), revenue=("revenue_pkr","sum"), avg_fare=("revenue_pkr","mean"))
    .reset_index()
    .sort_values("trips", ascending=False)
)

cols = st.columns(4)
for i, (_, r) in enumerate(city_stats.head(8).iterrows()):
    with cols[i % 4]:
        st.markdown(f"""
<div class="kpi-card" style="margin-bottom:10px;">
  <div style="font-size:.95rem;font-weight:700;color:{BRAND};">{r['pickup_city']}</div>
  <div style="font-size:.78rem;color:#8eaac4;margin-top:3px;">{r['trips']:,} trips</div>
  <div style="font-size:.74rem;color:#5a7a96;">PKR {r['revenue']/1e6:.1f}M revenue</div>
  <div style="font-size:.7rem;color:#4a6a84;">Avg PKR {r['avg_fare']:,.0f}</div>
</div>""", unsafe_allow_html=True)

# ── 3. Route Lines Map (intercity) ─────────────────────────────────────
sec("✈️ Intercity Route Map")

ic = comp[comp["pickup_city"] != comp["dropoff_city"]].copy()
route_stats = (
    ic.groupby(["pickup_city","pickup_lat","pickup_lon",
                "dropoff_city","dropoff_lat","dropoff_lon"])
    .agg(trips=("trip_id","count"), revenue=("revenue_pkr","sum"))
    .reset_index()
    .sort_values("trips", ascending=False)
    .head(20)
)

fig_routes = go.Figure()
for _, row in route_stats.iterrows():
    opacity = min(0.9, max(0.2, row["trips"] / route_stats["trips"].max()))
    width   = max(1.5, min(6, row["trips"] / route_stats["trips"].max() * 6))
    fig_routes.add_trace(go.Scattermapbox(
        lat=[row["pickup_lat"],  row["dropoff_lat"]],
        lon=[row["pickup_lon"],  row["dropoff_lon"]],
        mode="lines",
        line=dict(width=width, color=BRAND),
        opacity=opacity,
        hoverinfo="text",
        text=f"{row['pickup_city']} → {row['dropoff_city']}: {row['trips']:,} trips",
        showlegend=False,
    ))

# Add city dots on top
fig_routes.add_trace(go.Scattermapbox(
    lat=cg["pickup_lat"], lon=cg["pickup_lon"],
    mode="markers+text",
    marker=go.scattermapbox.Marker(size=9, color=AMBER, opacity=0.9),
    text=cg["pickup_city"],
    textfont=dict(size=9, color=TEXT),
    textposition="top right",
    hoverinfo="text",
    name="Cities",
))
_mapbox_layout(fig_routes, "Top 20 Intercity Routes", zoom=4.5, height=460)
st.plotly_chart(fig_routes, use_container_width=True)

# ── 4. Sankey intercity flow ───────────────────────────────────────────
sec("🔀 Intercity Flow (Sankey)")
top_cities = ic["pickup_city"].value_counts().head(8).index.tolist()
flow       = ic[ic["pickup_city"].isin(top_cities) & ic["dropoff_city"].isin(top_cities)]
mx         = flow.groupby(["pickup_city","dropoff_city"]).size().reset_index(name="n")
valid      = mx[mx["pickup_city"].isin(top_cities) & mx["dropoff_city"].isin(top_cities)].copy()

if len(valid) > 0:
    s_vals = [top_cities.index(r) for r in valid["pickup_city"]]
    t_vals = [len(top_cities) + top_cities.index(r) for r in valid["dropoff_city"]]
    fig2 = go.Figure(go.Sankey(
        node=dict(pad=15, thickness=20,
                  label=top_cities + top_cities,
                  color=[BRAND]*len(top_cities) + [STEEL]*len(top_cities)),
        link=dict(source=s_vals, target=t_vals, value=valid["n"].tolist(),
                  color="rgba(230,57,70,.25)"),
    ))
    fig2.update_layout(
        paper_bgcolor=BG, font=dict(color=TEXT, size=11),
        margin=dict(l=14,r=14,t=40,b=14), height=400,
        title=dict(text="Intercity Trip Flow — Top 8 Cities", font=dict(color=TEXT, size=13)),
    )
    st.plotly_chart(fig2, use_container_width=True)

# ── 5. Pickup vs Dropoff balance ───────────────────────────────────────
sec("⚖️ Pickup vs Dropoff Balance")
pu  = t.groupby("pickup_city").size().reset_index(name="pickups")
do  = t.groupby("dropoff_city").size().reset_index(name="dropoffs")
bal = pu.merge(do, left_on="pickup_city", right_on="dropoff_city", how="outer")
bal["city"]     = bal["pickup_city"].fillna(bal["dropoff_city"])
bal["pickups"]  = bal["pickups"].fillna(0)
bal["dropoffs"] = bal["dropoffs"].fillna(0)
bal             = bal.sort_values("pickups", ascending=False).head(12)

fig3 = go.Figure()
fig3.add_trace(go.Bar(name="Pickups",  x=bal["city"], y=bal["pickups"],  marker_color=BRAND, opacity=.85))
fig3.add_trace(go.Bar(name="Dropoffs", x=bal["city"], y=bal["dropoffs"], marker_color=STEEL, opacity=.85))
fig3.update_layout(barmode="group")
dark_layout(fig3, "Pickup vs Dropoff by City", height=320)
st.plotly_chart(fig3, use_container_width=True)

# ── 6. GPS density scatter (sample) ────────────────────────────────────
sec("📡 GPS Pickup Density")
sample = (
    comp.dropna(subset=["pickup_lat","pickup_lon"])
    .sample(min(3000, len(comp)), random_state=42)
)

# Colour by booking type
btype_colors = {bt: COLORS[i % len(COLORS)]
                for i, bt in enumerate(sample["booking_type"].unique())}

fig4 = go.Figure()
for btype, grp in sample.groupby("booking_type"):
    fig4.add_trace(go.Scattermapbox(
        lat=grp["pickup_lat"],
        lon=grp["pickup_lon"],
        mode="markers",
        name=btype,
        marker=go.scattermapbox.Marker(
            size=5,
            color=btype_colors.get(btype, BRAND),
            opacity=0.45,
        ),
        text=grp["pickup_city"],
        hoverinfo="text+name",
    ))

_mapbox_layout(fig4, "GPS Pickup Points by Booking Type (sample 3,000)", zoom=4.8, height=460)
fig4.update_layout(legend=dict(
    bgcolor="rgba(20,32,46,.85)", font=dict(color=TEXT, size=10),
    bordercolor=GRID, borderwidth=1,
))
st.plotly_chart(fig4, use_container_width=True)

# ── 7. Revenue choropleth by city (bubble) ─────────────────────────────
sec("💰 Revenue Bubble Map")
rev_city = (
    comp.groupby(["pickup_city","pickup_lat","pickup_lon"])["revenue_pkr"]
    .sum().reset_index()
)
rev_city["rev_m"] = (rev_city["revenue_pkr"] / 1e6).round(2)

fig5 = go.Figure(go.Scattermapbox(
    lat=rev_city["pickup_lat"],
    lon=rev_city["pickup_lon"],
    mode="markers+text",
    marker=go.scattermapbox.Marker(
        size=rev_city["rev_m"].apply(lambda x: min(60, max(15, x * 3))),
        color=rev_city["rev_m"],
        colorscale=[[0, NAVY], [0.5, AMBER], [1, BRAND]],
        showscale=True,
        opacity=0.82,
        colorbar=dict(
            title=dict(text="PKR M", font=dict(color=TEXT, size=11)),
            tickfont=dict(color=TEXT, size=9),
            bgcolor="rgba(15,17,23,.7)",
        ),
    ),
    text=rev_city["pickup_city"],
    textfont=dict(size=9, color="#ffffff"),
    hovertext=rev_city.apply(
        lambda r: f"<b>{r['pickup_city']}</b><br>PKR {r['rev_m']:.1f}M", axis=1
    ),
    hoverinfo="text",
))
_mapbox_layout(fig5, "Revenue Bubble Map (PKR M per City)", zoom=4.3, height=460)
st.plotly_chart(fig5, use_container_width=True)
