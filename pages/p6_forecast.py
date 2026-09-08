"""
Page 6 – Forecasting & Trends
Revenue forecast, demand prediction, dynamic pricing AI.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from app.style import inject_css, kpi_card, section_header
from app.charts import forecast_chart
from app.ml_models import (
    forecast_revenue_statsmodels,
    train_demand_model, forecast_demand,
    train_pricing_model, suggest_price,
)
from app.style import BRAND_COLOR, SUCCESS_COLOR, BRAND_ACCENT, PLOTLY_COLORS


def render(dfs: dict):
    inject_css()

    st.markdown('<div style="font-size:1.6rem;font-weight:800;color:#E63946;margin-bottom:4px;">📈 Forecasting & Trends</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:0.82rem;color:#5a7a96;">AI-powered revenue, demand, and pricing forecasts</div>', unsafe_allow_html=True)
    st.markdown("---")

    trips = dfs["trips"]
    inv   = dfs["invoices"]

    tabs = st.tabs(["📊 Revenue Forecast", "🚗 Demand Forecast", "💡 Dynamic Pricing AI", "📉 Trend Analysis"])

    # ──────────────────────────────────────────────────────────────────
    with tabs[0]:
        st.markdown(section_header("6-Month Revenue Forecast"), unsafe_allow_html=True)
        st.markdown('<div style="font-size:0.83rem;color:#7a9ab4;margin-bottom:12px;">Exponential Smoothing with trend + seasonality. 95% confidence band shown.</div>', unsafe_allow_html=True)

        periods = st.slider("Forecast Horizon (months)", 3, 12, 6)

        with st.spinner("Running forecast model …"):
            hist, fc, lo, hi = forecast_revenue_statsmodels(inv, periods=periods)

        # Chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=[str(i) for i in hist.index],
            y=hist.values / 1e6,
            name="Historical Revenue (PKR M)",
            line=dict(color=BRAND_ACCENT, width=2),
            mode="lines+markers", marker=dict(size=4),
        ))
        fig.add_trace(go.Scatter(
            x=[str(i) for i in fc.index],
            y=fc.values / 1e6,
            name="Forecast",
            line=dict(color=BRAND_COLOR, width=2.5, dash="dot"),
            mode="lines+markers", marker=dict(size=6, symbol="diamond"),
        ))
        # CI band
        x_ci = [str(i) for i in fc.index] + [str(i) for i in fc.index][::-1]
        y_ci = list(hi.values / 1e6) + list(lo.values / 1e6)[::-1]
        fig.add_trace(go.Scatter(
            x=x_ci, y=y_ci,
            fill="toself",
            fillcolor="rgba(230,57,70,0.10)",
            line=dict(color="rgba(0,0,0,0)"),
            name="95% Confidence Interval",
        ))
        _apply_dark(fig, "Monthly Revenue Forecast (PKR Millions)")
        fig.update_xaxes(tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

        # Forecast table
        fc_df = pd.DataFrame({
            "Month": [str(i) for i in fc.index],
            "Forecast (PKR)": fc.values.round(0),
            "Lower CI": lo.values.round(0),
            "Upper CI": hi.values.round(0),
        })
        fc_df["Forecast (PKR)"] = fc_df["Forecast (PKR)"].apply(lambda v: f"PKR {v/1e6:.2f}M")
        fc_df["Lower CI"]       = fc_df["Lower CI"].apply(lambda v: f"PKR {v/1e6:.2f}M")
        fc_df["Upper CI"]       = fc_df["Upper CI"].apply(lambda v: f"PKR {v/1e6:.2f}M")
        st.dataframe(fc_df, use_container_width=True, hide_index=True)

    # ──────────────────────────────────────────────────────────────────
    with tabs[1]:
        st.markdown(section_header("Daily Demand Forecast by City"), unsafe_allow_html=True)
        st.markdown('<div style="font-size:0.83rem;color:#7a9ab4;margin-bottom:12px;">Gradient Boosting model — predicts daily trip count per city.</div>', unsafe_allow_html=True)

        with st.spinner("Training demand model …"):
            gbm, le_city, feat_d, mae, r2 = train_demand_model(trips)

        st.info(f"Model performance: MAE = **{mae:.2f}** trips/day | R² = **{r2:.3f}**")

        city_list = trips["pickup_city"].unique().tolist()
        sel_city  = st.selectbox("City to Forecast", city_list)
        days_fwd  = st.slider("Days Ahead", 7, 90, 30)

        with st.spinner("Forecasting …"):
            fc_dem = forecast_demand(gbm, le_city, feat_d, sel_city, days_fwd)

        fig_dem = go.Figure()
        # Historical rolling avg
        hist_dem = trips[trips["pickup_city"] == sel_city].copy()
        hist_dem["date"] = pd.to_datetime(hist_dem["pickup_datetime"]).dt.date
        daily_hist = hist_dem.groupby("date").size().reset_index(name="trips")
        daily_hist["date"] = pd.to_datetime(daily_hist["date"])
        rolling = daily_hist.set_index("date")["trips"].rolling(7).mean()

        fig_dem.add_trace(go.Scatter(
            x=rolling.index.astype(str), y=rolling.values,
            name="7-Day Rolling Avg (Historical)",
            line=dict(color=BRAND_ACCENT, width=1.5),
            mode="lines",
        ))
        fig_dem.add_trace(go.Scatter(
            x=fc_dem["date"].astype(str), y=fc_dem["predicted_trips"].round(1),
            name="Forecast",
            line=dict(color=BRAND_COLOR, width=2.5, dash="dot"),
            mode="lines+markers", marker=dict(size=5, symbol="diamond"),
            fill="tozeroy", fillcolor="rgba(230,57,70,0.08)",
        ))
        _apply_dark(fig_dem, f"Daily Demand Forecast – {sel_city}")
        st.plotly_chart(fig_dem, use_container_width=True)

        # Weekend vs weekday breakdown
        fc_dem["is_weekend"] = pd.to_datetime(fc_dem["date"]).dt.dayofweek >= 5
        we_avg  = fc_dem[fc_dem["is_weekend"]]["predicted_trips"].mean()
        wd_avg  = fc_dem[~fc_dem["is_weekend"]]["predicted_trips"].mean()
        peak_dt = fc_dem.loc[fc_dem["predicted_trips"].idxmax(), "date"]

        c1, c2, c3 = st.columns(3)
        c1.markdown(kpi_card(f"{wd_avg:.1f}", "Avg Weekday Demand", "trips/day"), unsafe_allow_html=True)
        c2.markdown(kpi_card(f"{we_avg:.1f}", "Avg Weekend Demand",  "trips/day"), unsafe_allow_html=True)
        c3.markdown(kpi_card(str(peak_dt), "Peak Demand Date", ""), unsafe_allow_html=True)

    # ──────────────────────────────────────────────────────────────────
    with tabs[2]:
        st.markdown(section_header("💡 Dynamic Pricing AI"), unsafe_allow_html=True)
        st.markdown('<div style="font-size:0.83rem;color:#7a9ab4;margin-bottom:12px;">AI-recommended daily rental rate based on market conditions and demand signals.</div>', unsafe_allow_html=True)

        with st.spinner("Training pricing model …"):
            price_model, le_pc, le_pt, feat_p, mae_p, r2_p = train_pricing_model(trips)

        st.info(f"Pricing model: MAE = **PKR {mae_p:,.0f}** | R² = **{r2_p:.3f}**")

        pp1, pp2, pp3, pp4 = st.columns(4)
        months = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
                  7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}
        sel_mo  = pp1.selectbox("Month", list(months.keys()), format_func=lambda x: months[x], index=6)
        dow_map = {0:"Mon",1:"Tue",2:"Wed",3:"Thu",4:"Fri",5:"Sat",6:"Sun"}
        sel_dow = pp2.selectbox("Day of Week", list(dow_map.keys()), format_func=lambda x: dow_map[x])
        cities  = trips["pickup_city"].unique().tolist()
        sel_cit = pp3.selectbox("City", cities)
        btypes  = trips["booking_type"].unique().tolist()
        sel_bt  = pp4.selectbox("Booking Type", btypes)

        sel_dist = st.slider("Expected Distance (km)", 10, 1500, 150)

        if st.button("💡 Get Recommended Rate", type="primary"):
            recommended = suggest_price(price_model, le_pc, le_pt, feat_p,
                                        sel_mo, sel_dow, sel_cit, sel_bt, sel_dist)
            # Show rate with a ±10% range
            lo_r = recommended * 0.90
            hi_r = recommended * 1.10

            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#1e2a3a,#162030);
                        border:2px solid #E63946;border-radius:14px;
                        padding:24px;text-align:center;margin:12px 0;">
                <div style="font-size:0.85rem;color:#8eaac4;margin-bottom:6px;">AI Recommended Daily Rate</div>
                <div style="font-size:3rem;font-weight:800;color:#E63946;">PKR {recommended:,.0f}</div>
                <div style="font-size:0.82rem;color:#5a7a96;margin-top:6px;">
                    Suggested range: PKR {lo_r:,.0f} – PKR {hi_r:,.0f}
                </div>
                <div style="font-size:0.75rem;color:#4a6a84;margin-top:4px;">
                    {sel_cit} | {months[sel_mo]} | {dow_map[sel_dow]} | {sel_bt}
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Price surface by month
        st.markdown(section_header("Seasonal Pricing Heatmap"), unsafe_allow_html=True)
        price_surface = []
        for city in cities[:6]:
            row = []
            for m in range(1, 13):
                try:
                    p = suggest_price(price_model, le_pc, le_pt, feat_p, m, 2, city, "City Ride", 50)
                except Exception:
                    p = 0
                row.append(p)
            price_surface.append(row)

        fig_heat = go.Figure(go.Heatmap(
            z=price_surface,
            x=[months[m] for m in range(1,13)],
            y=cities[:6],
            colorscale=[[0, "#1D3557"], [0.5, "#457B9D"], [1, BRAND_COLOR]],
            text=[[f"PKR {v:,.0f}" for v in row] for row in price_surface],
            hovertemplate="%{y} – %{x}: %{text}<extra></extra>",
        ))
        _apply_dark(fig_heat, "Recommended Daily Rate by City & Month")
        st.plotly_chart(fig_heat, use_container_width=True)

    # ──────────────────────────────────────────────────────────────────
    with tabs[3]:
        st.markdown(section_header("Long-Term Business Trends"), unsafe_allow_html=True)

        # Year-over-year revenue
        inv_yoy = inv.groupby("invoice_year")["total_amount_pkr"].sum().reset_index()
        inv_yoy["yoy_growth"] = inv_yoy["total_amount_pkr"].pct_change() * 100

        c1, c2 = st.columns(2)
        with c1:
            fig_yoy = go.Figure(go.Bar(
                x=inv_yoy["invoice_year"].astype(str),
                y=inv_yoy["total_amount_pkr"] / 1e6,
                marker_color=[BRAND_COLOR if not pd.isna(g) and g > 0 else "#457B9D"
                              for g in inv_yoy["yoy_growth"]],
                text=[f"{v:.1f}M" for v in inv_yoy["total_amount_pkr"]/1e6],
                textposition="outside", textfont=dict(color="#c8dff0"),
            ))
            _apply_dark(fig_yoy, "Annual Revenue (PKR Millions)")
            st.plotly_chart(fig_yoy, use_container_width=True)

        with c2:
            # YoY trips
            trips_yoy = trips.groupby("pickup_year").size().reset_index(name="trips")
            fig_ty = go.Figure(go.Scatter(
                x=trips_yoy["pickup_year"].astype(str),
                y=trips_yoy["trips"],
                mode="lines+markers",
                line=dict(color=BRAND_ACCENT, width=2.5),
                fill="tozeroy", fillcolor="rgba(69,123,157,0.15)",
                marker=dict(size=8),
            ))
            _apply_dark(fig_ty, "Annual Trip Volume")
            st.plotly_chart(fig_ty, use_container_width=True)

        # Monthly seasonality
        trips["mo"] = pd.to_datetime(trips["pickup_datetime"]).dt.month
        season = trips.groupby("mo").size().reset_index(name="avg_trips")
        month_names = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
                       7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}
        season["month_name"] = season["mo"].map(month_names)

        fig_sea = go.Figure(go.Bar(
            x=season["month_name"],
            y=season["avg_trips"],
            marker_color=[BRAND_COLOR if m in [7,8,12,6] else "#457B9D" for m in season["mo"]],
            text=season["avg_trips"],
            textposition="outside", textfont=dict(color="#c8dff0", size=10),
        ))
        _apply_dark(fig_sea, "Seasonal Demand Pattern (All Years Combined)")
        st.plotly_chart(fig_sea, use_container_width=True)


def _apply_dark(fig, title=""):
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color="#c8dff0", size=12),
        margin=dict(l=14, r=14, t=44, b=14),
        title=dict(text=title, font=dict(color="#c8dff0", size=13)),
        xaxis=dict(gridcolor="rgba(255,255,255,0.06)", tickfont=dict(color="#c8dff0")),
        yaxis=dict(gridcolor="rgba(255,255,255,0.06)", tickfont=dict(color="#c8dff0")),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#c8dff0", size=11),
                    orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
