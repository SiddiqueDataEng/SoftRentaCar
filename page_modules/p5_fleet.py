"""Fleet Health"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from page_modules._shared import (
    inject, get_data, fmt, kpi, sec, alert_box, dark_layout,
    BRAND, NAVY, STEEL, GREEN, AMBER, ORANGE, TEXT, GRID, BG, COLORS
)
from app.storytelling import insight, fleet_utilisation_insight, fuel_insight, maintenance_insight

inject()
dfs = get_data()
veh   = dfs["vehicles"]
maint = dfs["maintenance"]
fuel  = dfs["fuel_logs"]

st.markdown(f'<div style="font-size:1.5rem;font-weight:800;color:{BRAND};margin-bottom:4px;">🔧 Fleet Health</div>', unsafe_allow_html=True)
st.markdown(f'<div style="font-size:.8rem;color:#5a7a96;">Vehicle status, maintenance, fuel and predictive alerts</div>', unsafe_allow_html=True)
st.markdown("<hr style='border-color:#1e2f44;margin:6px 0 14px 0'>", unsafe_allow_html=True)

# ── KPIs ───────────────────────────────────────────────────────────────
total_v    = len(veh)
available  = (veh["status"]=="Available").sum()
on_trip    = (veh["status"]=="On Trip").sum()
under_m    = (veh["status"]=="Under Maintenance").sum()
total_mc   = maint["total_cost_pkr"].sum()
avg_eff    = fuel["fuel_efficiency_kmpl"].mean()
total_fc   = fuel["fuel_cost_pkr"].sum()
scheduled  = (maint["status"]=="Scheduled").sum()

c = st.columns(5)
kpi(c[0], str(total_v),          "Total Vehicles",       f"{available} available",  True)
kpi(c[1], str(on_trip),          "On Trip Now",          f"{under_m} in maintenance",True)
kpi(c[2], fmt(total_mc),         "Maintenance Spend",    "Lifetime",                True)
kpi(c[3], f"{avg_eff:.1f} km/l", "Avg Fuel Efficiency",  "Fleet average",           avg_eff>10)
kpi(c[4], str(scheduled),        "Pending Services",     "Scheduled",               scheduled==0)

st.markdown("<hr style='border-color:#1e2f44;margin:14px 0'>", unsafe_allow_html=True)

# ── Filters ────────────────────────────────────────────────────────────
cf = st.columns(3)
st_opts = ["All"] + veh["status"].unique().tolist()
mk_opts = ["All"] + sorted(veh["make"].unique().tolist())
fl_opts = ["All"] + dfs["fleets"]["fleet_name"].tolist()
sel_st = cf[0].selectbox("Status", st_opts, key="flt_st")
sel_mk = cf[1].selectbox("Make",   mk_opts, key="flt_mk")
sel_fl = cf[2].selectbox("Fleet",  fl_opts, key="flt_fl")

vf = veh.copy()
if sel_st!="All": vf = vf[vf["status"]==sel_st]
if sel_mk!="All": vf = vf[vf["make"]==sel_mk]
if sel_fl!="All":
    fid = dfs["fleets"].loc[dfs["fleets"]["fleet_name"]==sel_fl,"fleet_id"].values[0]
    vf = vf[vf["fleet_id"]==fid]

mf = maint[maint["vehicle_id"].isin(vf["vehicle_id"])]
ff = fuel[fuel["vehicle_id"].isin(vf["vehicle_id"])]

# ── Status donut + maintenance cost ────────────────────────────────────
sec("🚗 Status & Maintenance")
col1, col2 = st.columns(2)
with col1:
    vc = vf["status"].value_counts().reset_index(); vc.columns=["status","n"]
    cmap = {"Available":GREEN,"On Trip":BRAND,"Under Maintenance":AMBER,"Reserved":STEEL,"Retired":"#555"}
    fig1 = go.Figure(go.Pie(labels=vc["status"], values=vc["n"], hole=0.55,
        marker=dict(colors=[cmap.get(s,BRAND) for s in vc["status"]],
                    line=dict(color="#0f1117",width=2)),
        textfont=dict(color="#fff",size=10)))
    dark_layout(fig1, "Vehicle Status", height=320)
    st.plotly_chart(fig1, width='stretch')

with col2:
    mg = mf.groupby("maintenance_type")["total_cost_pkr"].sum().reset_index().sort_values("total_cost_pkr").tail(10)
    fig2 = go.Figure(go.Bar(x=mg["total_cost_pkr"]/1e3, y=mg["maintenance_type"], orientation="h",
        marker_color=BRAND, text=[f"{v:.0f}K" for v in mg["total_cost_pkr"]/1e3],
        textposition="outside", textfont=dict(color=TEXT,size=9)))
    dark_layout(fig2, "Maintenance Cost by Type (PKR K)")
    st.plotly_chart(fig2, width='stretch')

# ── Fuel efficiency trend ───────────────────────────────────────────────
sec("⛽ Fuel Performance")
col3, col4 = st.columns(2)

with col3:
    fg = ff.groupby("fill_month").agg(avg_eff=("fuel_efficiency_kmpl","mean"), total_cost=("fuel_cost_pkr","sum")).reset_index()
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=fg["fill_month"], y=fg["avg_eff"], name="Avg Efficiency (km/l)",
        line=dict(color=GREEN,width=2.5), mode="lines+markers", marker=dict(size=5)))
    fig3.add_trace(go.Bar(x=fg["fill_month"], y=fg["total_cost"]/1e3, name="Fuel Cost (PKR K)",
        marker_color="rgba(230,57,70,.4)", yaxis="y2"))
    fig3.update_layout(yaxis2=dict(overlaying="y", side="right", gridcolor=GRID, tickfont=dict(color=TEXT)))
    dark_layout(fig3, "Efficiency vs Cost Trend", xangle=-45)
    st.plotly_chart(fig3, width='stretch')

with col4:
    ft = ff.groupby("fuel_type").agg(cost=("fuel_cost_pkr","sum"), litres=("litres_filled","sum")).reset_index()
    fig4 = go.Figure(go.Bar(x=ft["fuel_type"], y=ft["cost"]/1e6,
        marker_color=[GREEN,BRAND,AMBER][:len(ft)],
        text=[f"{v:.1f}M" for v in ft["cost"]/1e6],
        textposition="outside", textfont=dict(color=TEXT)))
    dark_layout(fig4, "Fuel Cost by Type (PKR M)", height=320)
    st.plotly_chart(fig4, width='stretch')

# Fuel insight
txt_f, sub_f, lvl_f = fuel_insight(ff)
insight(txt_f, "⛽", lvl_f, sub_f)

# Maintenance insight
txt_m, sub_m, lvl_m = maintenance_insight(mf)
insight(txt_m, "🔧", lvl_m, sub_m)

# Fleet utilisation insight
txt_u, sub_u, lvl_u = fleet_utilisation_insight(dfs["trips"], veh)
insight(txt_u, "🚗", lvl_u, sub_u)

# ── Age & mileage ──────────────────────────────────────────────────────
sec("📅 Fleet Age & Mileage")
col5, col6 = st.columns(2)
with col5:
    fig5 = go.Figure(go.Histogram(x=vf["odometer_km"], nbinsx=20, marker_color=BRAND, opacity=.8))
    fig5.add_vline(x=100000, line_dash="dash", line_color=AMBER,
                   annotation_text="100K mark", annotation_font_color=AMBER)
    dark_layout(fig5, "Odometer Distribution (km)", height=280)
    st.plotly_chart(fig5, width='stretch')
with col6:
    ag = vf.groupby("year").size().reset_index(name="n")
    fig6 = go.Figure(go.Bar(x=ag["year"].astype(str), y=ag["n"], marker_color=BRAND, opacity=.85))
    dark_layout(fig6, "Fleet by Model Year", height=280)
    st.plotly_chart(fig6, width='stretch')

# ── Fuel Anomaly Detection ──────────────────────────────────────────────
st.markdown("<hr style='border-color:#1e2f44;margin:14px 0'>", unsafe_allow_html=True)
sec("⚡ AI Fuel Anomaly Detection")
st.markdown('<div style="font-size:.82rem;color:#7a9ab4;margin-bottom:8px;">Trips where efficiency deviates >2σ from the vehicle baseline (potential theft or sensor faults).</div>', unsafe_allow_html=True)

from app.ml_models import detect_fuel_anomalies
anoms = detect_fuel_anomalies(ff)
if len(anoms):
    alert_box(f"⚠️ {len(anoms)} fuel anomalies detected.", "warning")
    st.dataframe(anoms[["vehicle_id","trip_id","fill_date","fuel_type","fuel_efficiency_kmpl",
                         "veh_mean_eff","z_score","km_driven"]].head(50).reset_index(drop=True),
                 width='stretch', height=260)
else:
    alert_box("✅ No fuel anomalies detected.", "success")

# ── Predictive Maintenance ──────────────────────────────────────────────
sec("🤖 Predictive Maintenance AI")
with st.spinner("Training maintenance predictor …"):
    from app.ml_models import train_maintenance_model
    clf_m, le_t, feats_m, rep_m, fi_m = train_maintenance_model(maint, veh)

acc_m = rep_m.get("accuracy",0)
st.info(f"Maintenance classifier accuracy: **{acc_m*100:.1f}%** — predicts vehicles likely needing service within 14 days.")

vr = veh.copy(); vr["vehicle_age"] = 2026 - vr["year"]
TODAY = pd.Timestamp("2026-07-01")
lm = maint.groupby("vehicle_id")["maintenance_date"].max().reset_index()
lm["days_since_last"] = (TODAY - lm["maintenance_date"]).dt.days
vr = vr.merge(lm[["vehicle_id","days_since_last"]], on="vehicle_id", how="left")
vr["days_since_last"] = vr["days_since_last"].fillna(180)

try: common_type = le_t.transform([maint["maintenance_type"].mode()[0]])[0]
except: common_type = 0

X_r = vr[["vehicle_age","odometer_km","days_since_last"]].copy()
X_r["type_enc"] = common_type
X_r = X_r[feats_m].fillna(X_r.median())
vr["risk_pct"] = (clf_m.predict_proba(X_r)[:,1]*100).round(1)
hi_risk = vr[vr["risk_pct"]>60].sort_values("risk_pct",ascending=False)

if len(hi_risk):
    alert_box(f"🔴 {len(hi_risk)} vehicles flagged for upcoming maintenance.", "critical")
    st.dataframe(hi_risk[["vehicle_id","make","model","year","odometer_km",
                           "days_since_last","risk_pct","status"]].reset_index(drop=True),
                 width='stretch', height=260)
else:
    alert_box("✅ No vehicles flagged as high-risk.", "success")

# ── Vehicle register ────────────────────────────────────────────────────
sec("📋 Vehicle Register")
show = ["vehicle_id","make","model","year","registration_no","status",
        "condition_rating","odometer_km","fuel_type","gps_enabled","telematics_enabled"]
st.dataframe(vf[show].reset_index(drop=True), width='stretch', height=300)

