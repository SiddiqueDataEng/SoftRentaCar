"""Driver Safety & AI"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from page_modules._shared import (
    inject, get_data, fmt, kpi, sec, alert_box, dark_layout,
    BRAND, NAVY, STEEL, GREEN, AMBER, ORANGE, TEXT, GRID, BG, COLORS
)

inject()
dfs = get_data()
tel  = dfs["telematics"]
drv  = dfs["drivers"]

st.markdown(f'<div style="font-size:1.5rem;font-weight:800;color:{BRAND};margin-bottom:4px;">🚦 Driver Safety & AI</div>', unsafe_allow_html=True)
st.markdown(f'<div style="font-size:.8rem;color:#5a7a96;">Telematics, behavior analytics and AI-powered safety scoring</div>', unsafe_allow_html=True)
st.markdown("<hr style='border-color:#1e2f44;margin:6px 0 14px 0'>", unsafe_allow_html=True)

# ── KPIs ───────────────────────────────────────────────────────────────
avg_score = tel["safety_score"].mean()
accidents = int(tel["accident_occurred"].sum())
complaints= int(tel["complaint_filed"].sum())
risky     = (drv["behavior_profile"].isin(["poor","dangerous"])).sum()
avg_rating= tel["customer_rating"].mean()
idle_hrs  = tel["idle_time_minutes"].sum() / 60

c = st.columns(6)
kpi(c[0], f"{avg_score:.1f}/100", "Avg Safety Score",    "Target ≥ 70",      avg_score>=70)
kpi(c[1], str(accidents),         "Accident Events",      "Total recorded",   accidents==0)
kpi(c[2], str(complaints),        "Customer Complaints",  "",                 complaints<50)
kpi(c[3], str(risky),             "High-Risk Drivers",    "poor + dangerous", risky==0)
kpi(c[4], f"{avg_rating:.2f}/5",  "Avg Rating",           "",                 avg_rating>=4)
kpi(c[5], f"{idle_hrs:,.0f}h",    "Idle Engine Hours",    "Fuel waste",       False)

st.markdown("<hr style='border-color:#1e2f44;margin:14px 0'>", unsafe_allow_html=True)

# ── Build driver summary ────────────────────────────────────────────────
summary = tel.groupby("driver_id").agg(
    avg_safety_score=("safety_score","mean"),
    total_trips=("trip_id","count"),
    total_km=("distance_km","sum"),
    harsh_brakes=("harsh_brake_events","sum"),
    harsh_accels=("harsh_accel_events","sum"),
    idle_min=("idle_time_minutes","sum"),
    speeding_km=("speeding_km","sum"),
    accidents=("accident_occurred","sum"),
    complaints=("complaint_filed","sum"),
    avg_rating=("customer_rating","mean"),
).reset_index().merge(drv[["driver_id","full_name","behavior_profile","fleet_id"]], on="driver_id", how="left")

# ── Scatter: safety vs km ───────────────────────────────────────────────
sec("🎯 Safety Score vs KM Driven")
col1, col2 = st.columns(2)
prof_colors = {"excellent":GREEN,"good":STEEL,"average":AMBER,"poor":ORANGE,"dangerous":"#ff2244"}

with col1:
    fig = go.Figure()
    for prof, grp in summary.groupby("behavior_profile"):
        fig.add_trace(go.Scatter(
            x=grp["total_km"], y=grp["avg_safety_score"],
            mode="markers", name=prof.capitalize(),
            marker=dict(size=(grp["total_trips"]/30).clip(5,20),
                        color=prof_colors.get(prof,BRAND), opacity=.8,
                        line=dict(width=1,color="#0f1117")),
            text=grp["full_name"],
            hovertemplate="<b>%{text}</b><br>Score:%{y:.1f} KM:%{x:,.0f}<extra></extra>"))
    fig.add_hline(y=70, line_dash="dash", line_color=GREEN,
                  annotation_text="Target 70", annotation_font_color=GREEN)
    dark_layout(fig, "Safety Score vs KM (bubble = trip count)", height=360)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig2 = go.Figure(go.Histogram(x=tel["safety_score"], nbinsx=30,
        marker_color=BRAND, opacity=.8))
    fig2.add_vline(x=70, line_dash="dash", line_color=GREEN,
                   annotation_text="Target 70", annotation_font_color=GREEN)
    fig2.add_vline(x=avg_score, line_dash="dot", line_color=AMBER,
                   annotation_text=f"Mean {avg_score:.1f}", annotation_font_color=AMBER)
    dark_layout(fig2, "Safety Score Distribution", height=360)
    st.plotly_chart(fig2, use_container_width=True)

# ── Profile breakdown ───────────────────────────────────────────────────
sec("👤 Behavior Profile Breakdown")
col3, col4 = st.columns(2)

with col3:
    pc = drv["behavior_profile"].value_counts().reset_index()
    pc.columns = ["profile","count"]
    fig3 = go.Figure(go.Bar(x=pc["profile"], y=pc["count"],
        marker_color=[prof_colors.get(p,BRAND) for p in pc["profile"]],
        text=pc["count"], textposition="outside", textfont=dict(color=TEXT)))
    dark_layout(fig3, "Driver Behavior Profile Count", height=320)
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    merged = tel.merge(drv[["driver_id","behavior_profile"]], on="driver_id", how="left")
    fig4 = go.Figure()
    for prof, grp in merged.groupby("behavior_profile"):
        fig4.add_trace(go.Box(y=grp["safety_score"], name=prof.capitalize(),
            marker_color=prof_colors.get(prof,BRAND), boxmean=True))
    dark_layout(fig4, "Safety Score by Profile", height=320)
    st.plotly_chart(fig4, use_container_width=True)

# ── Individual driver detail ────────────────────────────────────────────
sec("🔍 Individual Driver Deep-Dive")
driver_list = summary["full_name"].dropna().tolist()
sel_drv = st.selectbox("Select Driver", sorted(driver_list))
row = summary[summary["full_name"]==sel_drv]

if len(row):
    row = row.iloc[0]
    dc = st.columns(4)
    kpi(dc[0], f"{row['avg_safety_score']:.1f}", "Safety Score",   "", row["avg_safety_score"]>=70)
    kpi(dc[1], f"{int(row['total_trips'])}",      "Total Trips",    "")
    kpi(dc[2], f"{row['total_km']:,.0f} km",      "KM Driven",      "")
    kpi(dc[3], f"{row['avg_rating']:.2f}/5",      "Avg Rating",     "")

    dc2 = st.columns(4)
    kpi(dc2[0], str(int(row['accidents'])),  "Accidents",       "", row["accidents"]==0)
    kpi(dc2[1], str(int(row['complaints'])), "Complaints",      "")
    kpi(dc2[2], str(int(row['harsh_brakes'])),"Harsh Brakes",   "")
    kpi(dc2[3], str(int(row['harsh_accels'])),"Harsh Accels",   "")

    # Radar
    cats = ["Safe Braking","Smooth Accel","Low Idle","Speed Comply","Happy Customers"]
    vals = [
        max(0, min(100, 100 - row["harsh_brakes"]*0.5)),
        max(0, min(100, 100 - row["harsh_accels"]*0.5)),
        max(0, min(100, 100 - row["idle_min"]*0.01)),
        max(0, min(100, 100 - row["speeding_km"]*0.3)),
        row["avg_rating"]*20,
    ]
    cats_c = cats + [cats[0]]; vals_c = vals + [vals[0]]
    fig5 = go.Figure(go.Scatterpolar(r=vals_c, theta=cats_c, fill="toself",
        fillcolor="rgba(230,57,70,.2)", line=dict(color=BRAND,width=2), marker=dict(size=6,color=BRAND)))
    fig5.update_layout(
        polar=dict(bgcolor="rgba(30,42,58,.8)",
                   radialaxis=dict(visible=True,range=[0,100],gridcolor=GRID,tickfont=dict(color=TEXT,size=9)),
                   angularaxis=dict(gridcolor=GRID,tickfont=dict(color=TEXT,size=10))),
        paper_bgcolor=BG, font=dict(color=TEXT), margin=dict(l=40,r=40,t=60,b=40),
        showlegend=False, title=dict(text=f"KPI Radar — {sel_drv}", font=dict(color=TEXT,size=12)), height=380)
    st.plotly_chart(fig5, use_container_width=True)

    # Safety trend for this driver
    drv_tel = tel[tel["driver_id"]==row["driver_id"]].sort_values("trip_date")
    if len(drv_tel) > 1:
        sec("📉 Safety Score Trend")
        fig6 = go.Figure(go.Scatter(x=drv_tel["trip_date"], y=drv_tel["safety_score"],
            mode="lines+markers", line=dict(color=BRAND,width=2),
            fill="tozeroy", fillcolor="rgba(230,57,70,.10)"))
        fig6.add_hline(y=70, line_dash="dash", line_color=GREEN,
                       annotation_text="Target 70", annotation_font_color=GREEN)
        dark_layout(fig6, "Trip-by-Trip Safety Score", height=280)
        st.plotly_chart(fig6, use_container_width=True)

# ── AI Risk Predictor ─────────────────────────────────────────────────
st.markdown("<hr style='border-color:#1e2f44;margin:14px 0'>", unsafe_allow_html=True)
sec("🤖 AI Driver Risk Predictor")
st.markdown('<div style="font-size:.83rem;color:#7a9ab4;margin-bottom:10px;">Enter trip telematics to predict the driver\'s behavior profile.</div>', unsafe_allow_html=True)

with st.spinner("Training model …"):
    from app.ml_models import train_driver_safety_model, predict_driver_safety
    clf, le, feat_imp, report, features = train_driver_safety_model(tel, drv)

pp = st.columns(4)
harsh_b = pp[0].slider("Harsh Brakes",   0, 50, 5)
harsh_a = pp[1].slider("Harsh Accels",   0, 50, 4)
idle_m  = pp[2].slider("Idle Time (min)",0, 300, 60)
speed_k = pp[3].slider("Speeding KM",    0, 200, 15)
pp2 = st.columns(4)
dist_km = pp2[0].slider("Distance KM",    1, 1500, 150)
dur_hrs = pp2[1].slider("Duration (hrs)", 0.5, 48.0, 5.0)
max_spd = pp2[2].slider("Max Speed kmh",  40, 200, 110)
avg_spd = pp2[3].slider("Avg Speed kmh",  5, 130, 55)

if st.button("🔍 Predict Profile", type="primary"):
    result = predict_driver_safety(clf, le, features, dict(
        harsh_brake_events=harsh_b, harsh_accel_events=harsh_a,
        idle_time_minutes=idle_m, speeding_km=speed_k,
        distance_km=dist_km, duration_hours=dur_hrs,
        max_speed_kmh=max_spd, avg_speed_kmh=avg_spd))
    profile = result["predicted_profile"]
    probs   = result["probabilities"]
    c = prof_colors.get(profile, BRAND)
    st.markdown(f"""
<div style="background:rgba(30,42,58,.9);border:2px solid {c};border-radius:14px;
            padding:20px;text-align:center;margin:10px 0;">
  <div style="font-size:1.8rem;font-weight:800;color:{c};">{profile.upper()}</div>
  <div style="font-size:.82rem;color:#8eaac4;margin-top:4px;">Predicted Behavior Profile</div>
</div>""", unsafe_allow_html=True)
    prob_df = pd.DataFrame(list(probs.items()), columns=["Profile","Probability %"]).sort_values("Probability %",ascending=False)
    st.dataframe(prob_df, use_container_width=True, hide_index=True)

# Feature importance
sec("📊 Model Feature Importance")
fig_fi = go.Figure(go.Bar(x=feat_imp.values, y=feat_imp.index, orientation="h",
    marker_color=BRAND, text=[f"{v:.3f}" for v in feat_imp.values],
    textposition="outside", textfont=dict(color=TEXT,size=9)))
dark_layout(fig_fi, f"Feature Importance — Accuracy {report.get('accuracy',0)*100:.1f}%", height=300)
fig_fi.update_yaxes(autorange="reversed")
st.plotly_chart(fig_fi, use_container_width=True)
