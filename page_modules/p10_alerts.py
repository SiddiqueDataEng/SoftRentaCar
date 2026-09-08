"""Alerts & Watchlist"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from page_modules._shared import (
    inject, get_data, fmt, kpi, sec, alert_box, dark_layout,
    BRAND, NAVY, STEEL, GREEN, AMBER, ORANGE, TEXT, GRID, BG, COLORS
)

inject()
dfs = get_data()
TODAY = pd.Timestamp("2026-07-01")

veh   = dfs["vehicles"]
drv   = dfs["drivers"]
maint = dfs["maintenance"]
inv   = dfs["invoices"]
trips = dfs["trips"]
tel   = dfs["telematics"]

# ── Helper ────────────────────────────────────────────────────────────
def _tbl(df, title, cols, level, empty_msg):
    st.markdown(f'<div class="sec-hdr">{title}</div>', unsafe_allow_html=True)
    if len(df)==0:
        alert_box(empty_msg, "success" if "✅" in empty_msg else "info")
    else:
        avail = [c for c in cols if c in df.columns]
        st.dataframe(df[avail].reset_index(drop=True), use_container_width=True, height=200)


st.markdown(f'<div style="font-size:1.5rem;font-weight:800;color:{BRAND};margin-bottom:4px;">⚠️ Alerts & Watchlist</div>', unsafe_allow_html=True)
st.markdown(f'<div style="font-size:.8rem;color:#5a7a96;">Compliance monitoring, risk radar and operational alerts</div>', unsafe_allow_html=True)
st.markdown("<hr style='border-color:#1e2f44;margin:6px 0 14px 0'>", unsafe_allow_html=True)

# ── Compute alerts ─────────────────────────────────────────────────────
expired_ins   = veh[veh["insurance_expiry"]  < TODAY]
expired_fit   = veh[veh["fitness_cert_expiry"] < TODAY]
expired_lic   = drv[drv["license_expiry"] < TODAY]
dangerous_drv = drv[drv["behavior_profile"]=="dangerous"]
poor_drv      = drv[drv["behavior_profile"]=="poor"]
overdue_inv   = inv[(inv["due_date"] < TODAY) & (inv["outstanding_pkr"]>0)]
overdue_maint = maint[(maint["next_due_date"] < TODAY) & (maint["status"]=="Scheduled")]
exp_ins_soon  = veh[(veh["insurance_expiry"]>=TODAY) & (veh["insurance_expiry"]<TODAY+pd.Timedelta(days=30))]
exp_lic_soon  = drv[(drv["license_expiry"]>=TODAY) & (drv["license_expiry"]<TODAY+pd.Timedelta(days=30))]

total_critical = len(expired_ins)+len(expired_fit)+len(expired_lic)+len(dangerous_drv)
total_warn     = len(exp_ins_soon)+len(exp_lic_soon)+len(poor_drv)
total_out      = overdue_inv["outstanding_pkr"].sum()

# ── KPIs ───────────────────────────────────────────────────────────────
c = st.columns(4)
kpi(c[0], str(total_critical),              "Critical Alerts",       "Immediate action", total_critical==0)
kpi(c[1], str(total_warn),                  "Warnings",              "Within 30 days",   total_warn==0)
kpi(c[2], fmt(total_out),                   "Overdue Receivables",   f"{len(overdue_inv):,} invoices", total_out==0)
kpi(c[3], str(len(overdue_maint)),          "Overdue Services",      "Scheduled pending",len(overdue_maint)==0)

st.markdown("<hr style='border-color:#1e2f44;margin:14px 0'>", unsafe_allow_html=True)

tabs = st.tabs(["🔴 Critical","🟠 Warnings","💰 Finance","🚦 Driver Risk","🔧 Maintenance","📊 Overview"])

# ── CRITICAL ──────────────────────────────────────────────────────────
with tabs[0]:
    sec("🔴 Critical — Immediate Action Required")
    _tbl(expired_ins,   f"Expired Insurance ({len(expired_ins)})",
         ["vehicle_id","make","model","registration_no","insurance_expiry","status"], "critical",
         "✅ All insurance current.")
    _tbl(expired_fit,   f"Expired Fitness Cert ({len(expired_fit)})",
         ["vehicle_id","make","model","registration_no","fitness_cert_expiry"], "critical",
         "✅ All fitness certs current.")
    _tbl(expired_lic,   f"Expired Driver Licences ({len(expired_lic)})",
         ["driver_id","full_name","license_no","license_expiry","behavior_profile"], "critical",
         "✅ All licences valid.")
    _tbl(dangerous_drv, f"Dangerous Drivers ({len(dangerous_drv)})",
         ["driver_id","full_name","behavior_profile","accidents_count","complaints_count"], "critical",
         "✅ No dangerous drivers.")

# ── WARNINGS ─────────────────────────────────────────────────────────
with tabs[1]:
    sec("🟠 Warnings — Action Within 30 Days")
    _tbl(exp_ins_soon,  f"Insurance Expiring Soon ({len(exp_ins_soon)})",
         ["vehicle_id","make","model","registration_no","insurance_expiry"], "warning",
         "✅ None expiring in 30 days.")
    _tbl(exp_lic_soon,  f"Licences Expiring Soon ({len(exp_lic_soon)})",
         ["driver_id","full_name","license_no","license_expiry"], "warning",
         "✅ None expiring in 30 days.")
    _tbl(poor_drv,      f"Poor Behavior Drivers ({len(poor_drv)})",
         ["driver_id","full_name","behavior_profile","harsh_brake_rate","speeding_pct"], "warning",
         "✅ No poor-profile drivers.")

# ── FINANCE ──────────────────────────────────────────────────────────
with tabs[2]:
    sec("💰 Finance Alerts")
    if len(overdue_inv):
        alert_box(f"🟡 {len(overdue_inv):,} invoices past due — {fmt(total_out)} outstanding.", "warning")
        show_inv = overdue_inv.sort_values("outstanding_pkr",ascending=False).head(50) \
                              .merge(dfs["customers"][["customer_id","full_name","customer_type"]],
                                     on="customer_id",how="left")
        st.dataframe(show_inv[["invoice_id","full_name","customer_type","invoice_date","due_date",
                                "total_amount_pkr","outstanding_pkr","payment_method"]]
                     .reset_index(drop=True), use_container_width=True, height=300)
    else:
        alert_box("✅ No overdue invoices.", "success")

    ps = inv["payment_status"].value_counts().reset_index(); ps.columns=["s","n"]
    fig1 = go.Figure(go.Pie(labels=ps["s"], values=ps["n"], hole=0.5,
        marker=dict(colors=[GREEN,AMBER,ORANGE], line=dict(color="#0f1117",width=2))))
    dark_layout(fig1, "Invoice Payment Status", height=300)
    st.plotly_chart(fig1, use_container_width=True)

# ── DRIVER RISK ────────────────────────────────────────────────────────
with tabs[3]:
    sec("🚦 Driver Risk Radar")
    dr = drv.copy()
    dr["risk_score"] = (
        dr["harsh_brake_rate"]*30 + dr["harsh_accel_rate"]*25 +
        dr["idle_time_pct"]*20    + dr["speeding_pct"]*25
    )*100
    dr["risk_score"] = dr["risk_score"].clip(0,100).round(1)
    dr = dr.sort_values("risk_score", ascending=False)

    col1, col2 = st.columns(2)
    with col1:
        top15 = dr.head(15)
        fig2 = go.Figure(go.Bar(x=top15["full_name"], y=top15["risk_score"],
            marker_color=[ORANGE if r>60 else (AMBER if r>35 else GREEN) for r in top15["risk_score"]],
            text=[f"{r:.0f}" for r in top15["risk_score"]],
            textposition="outside", textfont=dict(color=TEXT,size=9)))
        dark_layout(fig2, "Top 15 Highest Risk Drivers", xangle=-45, height=360)
        st.plotly_chart(fig2, use_container_width=True)
    with col2:
        at = tel[tel["accident_occurred"]==True].copy()
        if len(at):
            at["month"] = pd.to_datetime(at["trip_date"]).dt.to_period("M").astype(str)
            am = at.groupby("month").size().reset_index(name="n")
            fig3 = go.Figure(go.Bar(x=am["month"], y=am["n"], marker_color=ORANGE))
            dark_layout(fig3, "Accidents by Month", xangle=-45, height=360)
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("No accident events in telematics.")

    st.dataframe(dr[["driver_id","full_name","behavior_profile","risk_score",
                      "harsh_brake_rate","harsh_accel_rate","speeding_pct","accidents_count"]]
                 .head(30).reset_index(drop=True), use_container_width=True, height=260)

# ── MAINTENANCE ────────────────────────────────────────────────────────
with tabs[4]:
    sec("🔧 Maintenance Watchlist")
    _tbl(overdue_maint, f"Overdue / Pending Services ({len(overdue_maint)})",
         ["maint_id","vehicle_id","maintenance_type","maintenance_date",
          "next_due_date","total_cost_pkr","status"], "warning",
         "✅ No overdue services.")

    mt = maint.copy()
    mt["maint_month"] = mt["maintenance_date"].dt.to_period("M").astype(str)
    mt_trend = mt.groupby("maint_month")["total_cost_pkr"].sum().reset_index()
    fig4 = go.Figure(go.Scatter(x=mt_trend["maint_month"], y=mt_trend["total_cost_pkr"]/1e3,
        fill="tozeroy", fillcolor="rgba(231,111,81,.12)", line=dict(color=ORANGE,width=2),
        mode="lines+markers", marker=dict(size=4)))
    dark_layout(fig4, "Monthly Maintenance Cost (PKR K)", xangle=-45, height=300)
    st.plotly_chart(fig4, use_container_width=True)

# ── OVERVIEW ──────────────────────────────────────────────────────────
with tabs[5]:
    sec("📊 Risk Overview")
    cats = ["Insurance","Licences","Dangerous Drivers","Overdue Payments","Pending Maint."]
    crits = [len(expired_ins),len(expired_lic),len(dangerous_drv),
             len(overdue_inv[overdue_inv["outstanding_pkr"]>50000]), len(overdue_maint)]
    warns = [len(exp_ins_soon),len(exp_lic_soon),len(poor_drv),
             len(overdue_inv[overdue_inv["outstanding_pkr"].between(1,50000)]), 0]
    fig5 = go.Figure()
    fig5.add_trace(go.Bar(name="Critical", x=cats, y=crits, marker_color=ORANGE))
    fig5.add_trace(go.Bar(name="Warning",  x=cats, y=warns, marker_color=AMBER))
    fig5.update_layout(barmode="stack")
    dark_layout(fig5, "Risk Summary by Category", height=340)
    st.plotly_chart(fig5, use_container_width=True)
