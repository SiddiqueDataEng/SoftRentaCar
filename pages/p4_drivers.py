"""
Page 4 – Driver Safety & AI
Telematics, safety scoring, behavior profiles, ML prediction.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from app.style import inject_css, kpi_card, section_header, alert
from app.charts import (
    driver_safety_scatter, telematics_radar, safety_score_distribution,
)
from app.data_loader import driver_safety_summary
from app.ml_models import train_driver_safety_model, predict_driver_safety
from app.style import PLOTLY_COLORS, BRAND_COLOR, SUCCESS_COLOR, DANGER_COLOR, WARNING_COLOR


def render(dfs: dict):
    inject_css()

    st.markdown('<div style="font-size:1.6rem;font-weight:800;color:#E63946;margin-bottom:4px;">🚦 Driver Safety & AI</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:0.82rem;color:#5a7a96;">Telematics, behavior analytics, and AI-powered safety scoring</div>', unsafe_allow_html=True)
    st.markdown("---")

    drivers = dfs["drivers"]
    tel     = dfs["telematics"]

    summary = driver_safety_summary(dfs)

    # ── KPIs ─────────────────────────────────────────────────────────
    avg_score   = tel["safety_score"].mean()
    accidents   = int(tel["accident_occurred"].sum())
    complaints  = int(tel["complaint_filed"].sum())
    risky_count = (drivers["behavior_profile"].isin(["poor","dangerous"])).sum()
    avg_rating  = tel["customer_rating"].mean()
    idle_hrs    = tel["idle_time_minutes"].sum() / 60

    cols = st.columns(6)
    kpis = [
        (f"{avg_score:.1f}", "Avg Safety Score",   "Target ≥ 70", avg_score >= 70),
        (f"{accidents}",     "Accidents",           "Total reported", accidents == 0),
        (f"{complaints}",    "Complaints",          "Customer filed",  complaints < 50),
        (f"{risky_count}",   "High-Risk Drivers",   "Poor + Dangerous", risky_count == 0),
        (f"{avg_rating:.2f}","Avg Customer Rating", "Out of 5.0",       avg_rating >= 4),
        (f"{idle_hrs:,.0f}h","Engine Idle Hours",   "Fuel waste proxy", False),
    ]
    for col, (v, l, d, pos) in zip(cols, kpis):
        col.markdown(kpi_card(v, l, d, pos), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")

    # ── Row 1: Scatter + Distribution ────────────────────────────────
    st.markdown(section_header("Fleet Safety Overview"), unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(driver_safety_scatter(summary), use_container_width=True)
    with c2:
        st.plotly_chart(safety_score_distribution(tel), use_container_width=True)

    # ── Row 2: Profile breakdown ─────────────────────────────────────
    st.markdown(section_header("Behavior Profile Breakdown"), unsafe_allow_html=True)
    c3, c4 = st.columns(2)
    with c3:
        prof_counts = drivers["behavior_profile"].value_counts().reset_index()
        prof_counts.columns = ["profile", "count"]
        colors_map = {
            "excellent": SUCCESS_COLOR, "good": "#457B9D",
            "average": WARNING_COLOR, "poor": DANGER_COLOR, "dangerous": "#ff2244"
        }
        fig_prof = go.Figure(go.Bar(
            x=prof_counts["profile"],
            y=prof_counts["count"],
            marker_color=[colors_map.get(p, BRAND_COLOR) for p in prof_counts["profile"]],
            text=prof_counts["count"],
            textposition="outside",
            textfont=dict(color="#c8dff0"),
        ))
        fig_prof.update_layout(
            template="plotly_white", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#c8dff0"), margin=dict(l=14,r=14,t=40,b=14),
            title="Driver Behavior Profile Distribution",
            xaxis=dict(gridcolor="rgba(255,255,255,0.06)", tickfont=dict(color="#c8dff0")),
            yaxis=dict(gridcolor="rgba(255,255,255,0.06)", tickfont=dict(color="#c8dff0")),
        )
        st.plotly_chart(fig_prof, use_container_width=True)

    with c4:
        # Safety score by behavior profile
        fig_box = go.Figure()
        for prof, grp in tel.merge(drivers[["driver_id","behavior_profile"]], on="driver_id", how="left").groupby("behavior_profile"):
            fig_box.add_trace(go.Box(
                y=grp["safety_score"],
                name=prof.capitalize(),
                marker_color=colors_map.get(prof, BRAND_COLOR),
                boxmean=True,
            ))
        fig_box.update_layout(
            template="plotly_white", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#c8dff0"), margin=dict(l=14,r=14,t=40,b=14),
            title="Safety Score by Behavior Profile",
            xaxis=dict(gridcolor="rgba(255,255,255,0.06)", tickfont=dict(color="#c8dff0")),
            yaxis=dict(gridcolor="rgba(255,255,255,0.06)", tickfont=dict(color="#c8dff0")),
        )
        st.plotly_chart(fig_box, use_container_width=True)

    # ── Driver Detail + Radar ────────────────────────────────────────
    st.markdown(section_header("Individual Driver Analysis"), unsafe_allow_html=True)
    driver_list = summary["full_name"].dropna().tolist()
    sel_driver  = st.selectbox("Select Driver", driver_list)
    driver_row  = summary[summary["full_name"] == sel_driver].iloc[0] if sel_driver in summary["full_name"].values else None

    if driver_row is not None:
        cc1, cc2, cc3 = st.columns([1, 1, 1])
        with cc1:
            st.markdown(kpi_card(f"{driver_row.get('avg_safety_score', 0):.1f}", "Safety Score", "", driver_row.get('avg_safety_score', 0) >= 70), unsafe_allow_html=True)
            st.markdown(kpi_card(f"{driver_row.get('total_trips', 0):,}", "Total Trips", ""), unsafe_allow_html=True)
            st.markdown(kpi_card(f"{driver_row.get('total_km', 0):,.0f} km", "KM Driven", ""), unsafe_allow_html=True)
        with cc2:
            st.markdown(kpi_card(f"{int(driver_row.get('accidents', 0))}", "Accidents",  "", driver_row.get('accidents', 0) == 0), unsafe_allow_html=True)
            st.markdown(kpi_card(f"{int(driver_row.get('complaints', 0))}", "Complaints", ""), unsafe_allow_html=True)
            st.markdown(kpi_card(f"{driver_row.get('avg_rating', 0):.2f}/5", "Avg Rating", ""), unsafe_allow_html=True)
        with cc3:
            behavior_label = str(driver_row.get("behavior_profile", "N/A")).capitalize()
            color_map_html = {"Excellent": SUCCESS_COLOR, "Good": "#457B9D",
                              "Average": WARNING_COLOR, "Poor": DANGER_COLOR, "Dangerous": "#ff2244"}
            c = color_map_html.get(behavior_label, BRAND_COLOR)
            st.markdown(f"""
            <div style="background:rgba(30,42,58,0.9);border:1px solid {c};border-radius:12px;
                        padding:20px;text-align:center;margin-top:6px;">
                <div style="font-size:1.1rem;font-weight:700;color:{c};">{behavior_label}</div>
                <div style="font-size:0.75rem;color:#8eaac4;margin-top:4px;">Behavior Profile</div>
            </div>""", unsafe_allow_html=True)

        st.plotly_chart(telematics_radar(driver_row), use_container_width=True)

    # ── Telematics trend for selected driver ─────────────────────────
    if driver_row is not None:
        driver_id = driver_row.get("driver_id")
        if driver_id:
            drv_tel = tel[tel["driver_id"] == driver_id].copy()
            drv_tel["trip_date"] = pd.to_datetime(drv_tel["trip_date"])
            drv_tel = drv_tel.sort_values("trip_date")
            if len(drv_tel) > 1:
                st.markdown(section_header("Safety Score Trend"), unsafe_allow_html=True)
                fig_trend = go.Figure(go.Scatter(
                    x=drv_tel["trip_date"], y=drv_tel["safety_score"],
                    mode="lines+markers",
                    line=dict(color=BRAND_COLOR, width=2),
                    fill="tozeroy", fillcolor="rgba(230,57,70,0.10)",
                ))
                fig_trend.add_hline(y=70, line_dash="dash", line_color=SUCCESS_COLOR,
                                    annotation_text="Target 70", annotation_font_color=SUCCESS_COLOR)
                fig_trend.update_layout(
                    template="plotly_white", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#c8dff0"), margin=dict(l=14,r=14,t=40,b=14),
                    xaxis=dict(gridcolor="rgba(255,255,255,0.06)", tickfont=dict(color="#c8dff0")),
                    yaxis=dict(gridcolor="rgba(255,255,255,0.06)", tickfont=dict(color="#c8dff0")),
                )
                st.plotly_chart(fig_trend, use_container_width=True)

    # ── AI: Predict Driver Risk ──────────────────────────────────────
    st.markdown("---")
    st.markdown(section_header("🤖 AI Driver Risk Predictor"), unsafe_allow_html=True)
    st.markdown('<div style="font-size:0.85rem;color:#7a9ab4;margin-bottom:12px;">Enter a trip\'s telematics data to predict the driver\'s behavior profile.</div>', unsafe_allow_html=True)

    with st.spinner("Training ML model …"):
        clf, le, feat_imp, report, features = train_driver_safety_model(tel, drivers)

    pp1, pp2, pp3, pp4 = st.columns(4)
    harsh_b = pp1.slider("Harsh Brake Events", 0, 50, 5)
    harsh_a = pp2.slider("Harsh Accel Events",  0, 50, 4)
    idle_m  = pp3.slider("Idle Time (min)",      0, 300, 60)
    speed_k = pp4.slider("Speeding KM",          0, 200, 15)

    pp5, pp6, pp7, pp8 = st.columns(4)
    dist_km  = pp5.slider("Distance KM",   1, 1500, 150)
    dur_hrs  = pp6.slider("Duration (hrs)", 0.5, 48.0, 5.0)
    max_spd  = pp7.slider("Max Speed (kmh)",40, 200, 110)
    avg_spd  = pp8.slider("Avg Speed (kmh)", 5, 130, 55)

    if st.button("🔍 Predict Driver Profile", type="primary"):
        result = predict_driver_safety(clf, le, features, {
            "harsh_brake_events": harsh_b,
            "harsh_accel_events": harsh_a,
            "idle_time_minutes":  idle_m,
            "speeding_km":        speed_k,
            "distance_km":        dist_km,
            "duration_hours":     dur_hrs,
            "max_speed_kmh":      max_spd,
            "avg_speed_kmh":      avg_spd,
        })
        profile = result["predicted_profile"]
        probs   = result["probabilities"]
        color_p = {"excellent": SUCCESS_COLOR, "good": "#457B9D",
                   "average": WARNING_COLOR, "poor": DANGER_COLOR, "dangerous": "#ff2244"}
        c = color_p.get(profile, BRAND_COLOR)
        st.markdown(f"""
        <div style="background:rgba(30,42,58,0.9);border:2px solid {c};border-radius:14px;padding:20px;text-align:center;margin:10px 0;">
            <div style="font-size:1.8rem;font-weight:800;color:{c};">{profile.upper()}</div>
            <div style="font-size:0.85rem;color:#8eaac4;margin-top:6px;">Predicted Behavior Profile</div>
        </div>""", unsafe_allow_html=True)

        prob_df = pd.DataFrame(list(probs.items()), columns=["Profile","Probability %"]).sort_values("Probability %", ascending=False)
        st.dataframe(prob_df, use_container_width=True, hide_index=True)

    # ── Feature importance ───────────────────────────────────────────
    st.markdown(section_header("ML Model – Feature Importance"), unsafe_allow_html=True)
    fig_fi = go.Figure(go.Bar(
        x=feat_imp.values,
        y=feat_imp.index,
        orientation="h",
        marker_color=BRAND_COLOR,
        text=[f"{v:.3f}" for v in feat_imp.values],
        textposition="outside",
        textfont=dict(color="#c8dff0", size=10),
    ))
    fig_fi.update_layout(
        template="plotly_white", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#c8dff0"), margin=dict(l=14,r=14,t=40,b=14),
        title="Feature Importance – Driver Safety Classifier",
        xaxis=dict(gridcolor="rgba(255,255,255,0.06)", tickfont=dict(color="#c8dff0")),
        yaxis=dict(gridcolor="rgba(255,255,255,0.06)", tickfont=dict(color="#c8dff0"), autorange="reversed"),
        height=350,
    )
    st.plotly_chart(fig_fi, use_container_width=True)

    # Accuracy
    acc = report.get("accuracy", 0)
    st.info(f"✅ Model Accuracy: **{acc*100:.1f}%** | Random Forest, 150 trees, 80/20 split")
