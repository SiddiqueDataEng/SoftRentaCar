"""Forecasting & Trends"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from page_modules._shared import (
    inject, get_data, fmt, kpi, sec, alert_box, dark_layout,
    BRAND, NAVY, STEEL, GREEN, AMBER, ORANGE, TEXT, GRID, BG, COLORS
)

inject()
dfs   = get_data()
trips = dfs["trips"]
inv   = dfs["invoices"]

st.markdown(f'<div style="font-size:1.5rem;font-weight:800;color:{BRAND};margin-bottom:4px;">📈 Forecasting & Trends</div>', unsafe_allow_html=True)
st.markdown(f'<div style="font-size:.8rem;color:#5a7a96;">AI-powered revenue, demand and pricing forecasts</div>', unsafe_allow_html=True)
st.markdown("<hr style='border-color:#1e2f44;margin:6px 0 14px 0'>", unsafe_allow_html=True)

tabs = st.tabs(["📊 Revenue Forecast", "🚗 Demand Forecast", "💡 Dynamic Pricing", "📉 Trend Analysis"])

# ── Tab 1: Revenue Forecast ────────────────────────────────────────────
with tabs[0]:
    sec("6-Month Revenue Forecast")
    st.markdown('<div style="font-size:.82rem;color:#7a9ab4;margin-bottom:10px;">Exponential Smoothing with trend + seasonality and 95% CI.</div>', unsafe_allow_html=True)

    periods = st.slider("Forecast Horizon (months)", 3, 12, 6, key="fc_rev_periods")

    with st.spinner("Running forecast …"):
        from app.ml_models import forecast_revenue_statsmodels
        hist, fc, lo, hi = forecast_revenue_statsmodels(inv, periods=periods)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[str(i) for i in hist.index], y=hist.values / 1e6,
        name="Historical", line=dict(color=STEEL, width=2),
        mode="lines+markers", marker=dict(size=4)))
    fig.add_trace(go.Scatter(
        x=[str(i) for i in fc.index], y=fc.values / 1e6,
        name="Forecast", line=dict(color=BRAND, width=2.5, dash="dot"),
        mode="lines+markers", marker=dict(size=6, symbol="diamond")))
    x_ci = [str(i) for i in fc.index] + [str(i) for i in fc.index][::-1]
    y_ci = list(hi.values / 1e6) + list(lo.values / 1e6)[::-1]
    fig.add_trace(go.Scatter(
        x=x_ci, y=y_ci, fill="toself",
        fillcolor="rgba(230,57,70,.10)",
        line=dict(color="rgba(0,0,0,0)"), name="95% CI"))
    dark_layout(fig, "Monthly Revenue Forecast (PKR M)", xangle=-45, height=400)
    st.plotly_chart(fig, use_container_width=True)

    fc_df = pd.DataFrame({
        "Month":    [str(i) for i in fc.index],
        "Forecast": fc.values.round(0),
        "Lower CI": lo.values.round(0),
        "Upper CI": hi.values.round(0),
    })
    for col in ["Forecast", "Lower CI", "Upper CI"]:
        fc_df[col] = fc_df[col].apply(fmt)
    st.dataframe(fc_df, use_container_width=True, hide_index=True)


# ── Tab 2: Demand Forecast ─────────────────────────────────────────────
with tabs[1]:
    sec("Daily Demand Forecast by City")
    with st.spinner("Training demand model …"):
        from app.ml_models import train_demand_model, forecast_demand
        gbm, le_c, feats_d, mae, r2 = train_demand_model(trips)

    st.info(f"Model: MAE = **{mae:.2f}** trips/day | R² = **{r2:.3f}**")

    city_list = sorted(trips["pickup_city"].unique().tolist())
    sel_ci_dem = st.selectbox("City to Forecast", city_list, key="fc_dem_city")
    days_ahead = st.slider("Days Ahead", 7, 90, 30, key="fc_dem_days")

    with st.spinner("Forecasting …"):
        fc_dem = forecast_demand(gbm, le_c, feats_d, sel_ci_dem, days_ahead)

    hist_d = trips[trips["pickup_city"] == sel_ci_dem].copy()
    hist_d["date"] = pd.to_datetime(hist_d["pickup_datetime"]).dt.date
    dh = hist_d.groupby("date").size().reset_index(name="n")
    dh["date"] = pd.to_datetime(dh["date"])
    rolling = dh.set_index("date")["n"].rolling(7).mean()

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=rolling.index.astype(str), y=rolling.values,
        name="7-Day Rolling Avg", line=dict(color=STEEL, width=1.5)))
    fig2.add_trace(go.Scatter(
        x=fc_dem["date"].astype(str), y=fc_dem["predicted_trips"].round(1),
        name="Forecast", line=dict(color=BRAND, width=2.5, dash="dot"),
        mode="lines+markers", marker=dict(size=5, symbol="diamond"),
        fill="tozeroy", fillcolor="rgba(230,57,70,.08)"))
    dark_layout(fig2, f"Daily Demand Forecast — {sel_ci_dem}", height=380)
    st.plotly_chart(fig2, use_container_width=True)

    fc_dem["is_weekend"] = pd.to_datetime(fc_dem["date"]).dt.dayofweek >= 5
    we   = fc_dem[fc_dem["is_weekend"]]["predicted_trips"].mean()
    wd   = fc_dem[~fc_dem["is_weekend"]]["predicted_trips"].mean()
    peak = fc_dem.loc[fc_dem["predicted_trips"].idxmax(), "date"]
    dc   = st.columns(3)
    kpi(dc[0], f"{wd:.1f}", "Avg Weekday Demand", "trips/day")
    kpi(dc[1], f"{we:.1f}", "Avg Weekend Demand",  "trips/day")
    kpi(dc[2], str(peak),   "Peak Demand Date",    "")


# ── Tab 3: Dynamic Pricing ─────────────────────────────────────────────
with tabs[2]:
    sec("Dynamic Pricing AI")
    with st.spinner("Training pricing model …"):
        from app.ml_models import train_pricing_model, suggest_price
        pm, le_pc, le_pt, feats_p, mae_p, r2_p = train_pricing_model(trips)

    st.info(f"Model: MAE = **PKR {mae_p:,.0f}** | R² = **{r2_p:.3f}**")

    months_map = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
                  7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}
    dows_map   = {0:"Mon",1:"Tue",2:"Wed",3:"Thu",4:"Fri",5:"Sat",6:"Sun"}

    pp = st.columns(4)
    sel_mo  = pp[0].selectbox("Month",   list(months_map.keys()),
                               format_func=lambda x: months_map[x], index=6, key="fc_pr_mo")
    sel_dow = pp[1].selectbox("Day",     list(dows_map.keys()),
                               format_func=lambda x: dows_map[x],   key="fc_pr_dow")
    sel_cit = pp[2].selectbox("City",    sorted(trips["pickup_city"].unique().tolist()),   key="fc_pr_city")
    sel_bt  = pp[3].selectbox("Booking", sorted(trips["booking_type"].unique().tolist()),  key="fc_pr_bt")
    sel_dist = st.slider("Expected Distance (km)", 10, 1500, 150, key="fc_pr_dist")

    if st.button("💡 Get Recommended Rate", type="primary", key="fc_pr_btn"):
        rate = suggest_price(pm, le_pc, le_pt, feats_p,
                             sel_mo, sel_dow, sel_cit, sel_bt, sel_dist)
        st.markdown(f"""
<div style="background:linear-gradient(135deg,#1e2a3a,#162030);
            border:2px solid {BRAND};border-radius:14px;
            padding:24px;text-align:center;margin:12px 0;">
  <div style="font-size:.85rem;color:#8eaac4;margin-bottom:4px;">AI Recommended Daily Rate</div>
  <div style="font-size:3rem;font-weight:800;color:{BRAND};">PKR {rate:,.0f}</div>
  <div style="font-size:.8rem;color:#5a7a96;margin-top:4px;">
    Range: PKR {rate*.9:,.0f} – PKR {rate*1.1:,.0f}
  </div>
  <div style="font-size:.72rem;color:#4a6a84;margin-top:3px;">
    {sel_cit} · {months_map[sel_mo]} · {dows_map[sel_dow]} · {sel_bt}
  </div>
</div>""", unsafe_allow_html=True)

    sec("Seasonal Pricing Heatmap")
    cities6 = sorted(trips["pickup_city"].unique().tolist())[:6]
    surface = []
    for city in cities6:
        row = []
        for m in range(1, 13):
            try:
                p = suggest_price(pm, le_pc, le_pt, feats_p, m, 2, city, "City Ride", 50)
            except Exception:
                p = 0
            row.append(p)
        surface.append(row)

    fig3 = go.Figure(go.Heatmap(
        z=surface,
        x=[months_map[m] for m in range(1, 13)],
        y=cities6,
        colorscale=[[0, NAVY], [0.5, STEEL], [1, BRAND]],
        text=[[f"PKR {v:,.0f}" for v in row] for row in surface],
        hovertemplate="%{y} – %{x}: %{text}<extra></extra>"))
    dark_layout(fig3, "Recommended Rate by City & Month", height=320)
    st.plotly_chart(fig3, use_container_width=True)


# ── Tab 4: Trend Analysis ──────────────────────────────────────────────
with tabs[3]:
    sec("Year-over-Year Performance")
    col1, col2 = st.columns(2)

    with col1:
        yoy = inv.groupby("invoice_year")["total_amount_pkr"].sum().reset_index()
        fig4 = go.Figure(go.Bar(
            x=yoy["invoice_year"].astype(str),
            y=yoy["total_amount_pkr"] / 1e6,
            marker_color=BRAND,
            text=[f"{v:.1f}M" for v in yoy["total_amount_pkr"] / 1e6],
            textposition="outside", textfont=dict(color=TEXT)))
        dark_layout(fig4, "Annual Revenue (PKR M)", height=320)
        st.plotly_chart(fig4, use_container_width=True)

    with col2:
        ty = trips.groupby("pickup_year").size().reset_index(name="n")
        fig5 = go.Figure(go.Scatter(
            x=ty["pickup_year"].astype(str), y=ty["n"],
            mode="lines+markers", line=dict(color=STEEL, width=2.5),
            fill="tozeroy", fillcolor="rgba(69,123,157,.15)",
            marker=dict(size=8)))
        dark_layout(fig5, "Annual Trip Volume", height=320)
        st.plotly_chart(fig5, use_container_width=True)

    sec("Seasonal Demand Pattern")
    trips["_mo"] = pd.to_datetime(trips["pickup_datetime"]).dt.month
    mn = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
          7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}
    sea = trips.groupby("_mo").size().reset_index(name="n")
    sea["month_name"] = sea["_mo"].map(mn)
    fig6 = go.Figure(go.Bar(
        x=sea["month_name"], y=sea["n"],
        marker_color=[BRAND if m in [7, 8, 12, 6] else STEEL for m in sea["_mo"]],
        text=sea["n"], textposition="outside", textfont=dict(color=TEXT, size=10)))
    dark_layout(fig6, "Bookings by Month (All Years)", height=320)
    st.plotly_chart(fig6, use_container_width=True)
