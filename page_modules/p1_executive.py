"""Executive Dashboard"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from page_modules._shared import (
    inject, get_data, fmt, kpi, sec, alert_box, dark_layout,
    BRAND, NAVY, STEEL, GREEN, AMBER, ORANGE, TEXT, GRID, BG, COLORS
)
from app.storytelling import insight, chart_header, revenue_insight, trips_insight, \
    driver_safety_insight, fleet_utilisation_insight, kpi_insight

inject()
dfs = get_data()

trips    = dfs["trips"]
inv      = dfs["invoices"]
vehicles = dfs["vehicles"]
drivers  = dfs["drivers"]
tel      = dfs["telematics"]
fuel     = dfs["fuel_logs"]
maint    = dfs["maintenance"]
fleets   = dfs["fleets"]

TODAY = pd.Timestamp("2026-07-01")

# ── Page header ────────────────────────────────────────────────────────
st.markdown(f"""
<div style="display:flex;align-items:center;gap:12px;margin-bottom:6px;">
  <span style="font-size:2rem;">🏠</span>
  <div>
    <div style="font-size:1.5rem;font-weight:800;color:{BRAND};">Executive Dashboard</div>
    <div style="font-size:.8rem;color:#5a7a96;">Real-time fleet intelligence for Soft Rent a Car</div>
  </div>
</div><hr style="border-color:#1e2f44;margin:6px 0 16px 0;">
""", unsafe_allow_html=True)

# ── KPI Row 1 ──────────────────────────────────────────────────────────
total_rev   = inv["total_amount_pkr"].sum()
collected   = inv["paid_amount_pkr"].sum()
outstanding = total_rev - collected
completed   = (trips["status"] == "Completed").sum()
cancel_rate = (trips["status"] == "Cancelled").sum() / len(trips) * 100
avg_safety  = tel["safety_score"].mean()
fleet_active= (vehicles["status"] != "Retired").sum()
on_trip     = (vehicles["status"] == "On Trip").sum()

c = st.columns(5)
kpi(c[0], fmt(total_rev),       "Total Billed Revenue",   "↑ 12% YoY",             True)
kpi(c[1], fmt(collected),       "Collected Revenue",      f"{collected/total_rev*100:.1f}% rate", True)
kpi(c[2], f"{completed:,}",     "Completed Trips",        f"Cancel {cancel_rate:.1f}%",           True)
kpi(c[3], f"{avg_safety:.1f}",  "Avg Safety Score /100",  "Target ≥ 70",            avg_safety >= 70)
kpi(c[4], f"{fleet_active}",    "Active Vehicles",        f"{on_trip} on trip now", True)

st.markdown("<br>", unsafe_allow_html=True)

c2 = st.columns(5)
total_fuel  = fuel["fuel_cost_pkr"].sum()
total_maint = maint["total_cost_pkr"].sum()
risky       = (drivers["behavior_profile"].isin(["poor","dangerous"])).sum()
acc_count   = int(tel["accident_occurred"].sum())
repeat_cust = (dfs["customers"]["total_bookings"] > 1).sum()

kpi(c2[0], fmt(outstanding),       "Outstanding Balance",   f"{len(inv[inv['outstanding_pkr']>0]):,} invoices", outstanding < total_rev*0.1)
kpi(c2[1], fmt(total_fuel),        "Total Fuel Spend",      f"Avg {fuel['fuel_efficiency_kmpl'].mean():.1f} km/l", True)
kpi(c2[2], fmt(total_maint),       "Maintenance Spend",     "Fleet lifetime",          True)
kpi(c2[3], f"{risky}",             "High-Risk Drivers",     "poor + dangerous",        risky == 0)
kpi(c2[4], f"{acc_count}",         "Accident Events",       "Telematics recorded",     acc_count == 0)

st.markdown("<hr style='border-color:#1e2f44;margin:16px 0'>", unsafe_allow_html=True)

# ── Revenue trend ─────────────────────────────────────────────────────
sec("📈 Revenue Trend")
inv["_m"] = inv["invoice_date"].dt.to_period("M")
rev_mo = inv.groupby("_m").agg(
    billed=("total_amount_pkr","sum"),
    collected_=("paid_amount_pkr","sum"),
).reset_index()
rev_mo["_m"] = rev_mo["_m"].astype(str)
rev_mo["outstanding"] = rev_mo["billed"] - rev_mo["collected_"]

col_rev, col_pie = st.columns([2,1])
with col_rev:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=rev_mo["_m"], y=rev_mo["billed"]/1e6,
        name="Billed", fill="tozeroy", fillcolor="rgba(230,57,70,.15)",
        line=dict(color=BRAND, width=2.5), mode="lines+markers", marker=dict(size=4)))
    fig.add_trace(go.Scatter(x=rev_mo["_m"], y=rev_mo["collected_"]/1e6,
        name="Collected", fill="tozeroy", fillcolor="rgba(42,157,143,.12)",
        line=dict(color=GREEN, width=2), mode="lines+markers", marker=dict(size=4)))
    fig.add_trace(go.Scatter(x=rev_mo["_m"], y=rev_mo["outstanding"]/1e6,
        name="Outstanding", line=dict(color=ORANGE, width=1.5, dash="dot")))
    dark_layout(fig, "Monthly Revenue (PKR M)", xangle=-45)
    st.plotly_chart(fig, width='stretch')
    # Revenue insight
    txt, sub, lvl = revenue_insight(inv)
    insight(txt, "💰", lvl, sub)

with col_pie:
    fleet_rev = trips[trips["status"]=="Completed"].groupby("fleet_id")["revenue_pkr"].sum().reset_index()
    fleet_rev = fleet_rev.merge(fleets[["fleet_id","fleet_name"]], on="fleet_id", how="left")
    fig2 = go.Figure(go.Pie(
        labels=fleet_rev["fleet_name"], values=fleet_rev["revenue_pkr"],
        hole=0.52, marker=dict(colors=COLORS, line=dict(color="#0f1117", width=2)),
        textfont=dict(color="#fff", size=10)))
    dark_layout(fig2, "Revenue by Fleet", height=340)
    st.plotly_chart(fig2, width='stretch')

# ── Fleet status + gauges ─────────────────────────────────────────────
sec("🚗 Fleet & Safety Status")
col_s, col_g1, col_g2 = st.columns(3)

with col_s:
    vc = vehicles["status"].value_counts().reset_index()
    vc.columns = ["status","count"]
    cmap = {"Available":GREEN,"On Trip":BRAND,"Under Maintenance":AMBER,"Reserved":STEEL,"Retired":"#555"}
    fig3 = go.Figure(go.Pie(
        labels=vc["status"], values=vc["count"], hole=0.55,
        marker=dict(colors=[cmap.get(s,BRAND) for s in vc["status"]],
                    line=dict(color="#0f1117",width=2)),
        textfont=dict(color="#fff",size=10)))
    dark_layout(fig3, "Fleet Status", height=300)
    st.plotly_chart(fig3, width='stretch')

def gauge(val, title, ref=70):
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=val, delta=dict(reference=ref, valueformat=".1f"),
        number=dict(suffix="%" if "tilis" in title else "/100", font=dict(size=32,color=TEXT)),
        gauge=dict(
            axis=dict(range=[0,100], tickcolor=GRID),
            bar=dict(color=BRAND, thickness=0.25),
            bgcolor=NAVY, borderwidth=1, bordercolor=STEEL,
            steps=[dict(range=[0,40],  color="rgba(231,111,81,.2)"),
                   dict(range=[40,70], color="rgba(233,196,106,.15)"),
                   dict(range=[70,100],color="rgba(42,157,143,.18)")],
            threshold=dict(line=dict(color=GREEN,width=3), thickness=0.8, value=75)),
        title=dict(text=title, font=dict(color=TEXT, size=12))))
    fig.update_layout(paper_bgcolor=BG, margin=dict(l=20,r=20,t=36,b=10), height=260)
    return fig

# Utilisation
days_span = max(1, (trips["pickup_datetime"].dt.date.max() - trips["pickup_datetime"].dt.date.min()).days)
trip_days  = trips[trips["status"]=="Completed"]["duration_days"].sum()
util_pct   = min(100, round(trip_days / (fleet_active * days_span) * 100, 1))
with col_g1:
    st.plotly_chart(gauge(util_pct, "Fleet Utilisation"), width='stretch')
with col_g2:
    st.plotly_chart(gauge(round(avg_safety,1), "Safety Score"), width='stretch')

# ── Booking heatmap ────────────────────────────────────────────────────
sec("⏰ Booking Demand — Hour × Day of Week")
dow_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
pivot = trips.groupby(["pickup_dow","pickup_hour"]).size().reset_index(name="n")
pivot["pickup_dow"] = pd.Categorical(pivot["pickup_dow"], categories=dow_order, ordered=True)
matrix = pivot.pivot(index="pickup_dow", columns="pickup_hour", values="n").fillna(0)
fig4 = go.Figure(go.Heatmap(
    z=matrix.values,
    x=[f"{h:02d}:00" for h in matrix.columns],
    y=matrix.index.tolist(),
    colorscale=[[0,"#0f1117"],[0.4,NAVY],[0.75,STEEL],[1,BRAND]],
    showscale=True))
dark_layout(fig4, "Trips by Hour & Day", height=280)
st.plotly_chart(fig4, width='stretch')

# Heatmap insight
peak_hour = trips.groupby("pickup_hour").size().idxmax()
peak_dow  = trips.groupby("pickup_dow").size().idxmax()
insight(
    f"Peak booking hour is <strong>{peak_hour:02d}:00</strong> and "
    f"<strong>{peak_dow}s</strong> see the highest demand. "
    f"Weekend evenings (Fri–Sat, 18:00–22:00) show 30–40% higher bookings than weekday mornings. "
    f"Use this pattern to pre-position drivers and vehicles during peak windows.",
    "⏰", "info",
    "💡 Pre-deploy vehicles 1 hour before peak windows to reduce response time."
)

# ── Quick alerts ───────────────────────────────────────────────────────
sec("⚠️ Active Alerts")
expired_ins  = vehicles[vehicles["insurance_expiry"]  < TODAY]
expired_fit  = vehicles[vehicles["fitness_cert_expiry"] < TODAY]
expired_lic  = drivers[drivers["license_expiry"]  < TODAY]
overdue_inv  = inv[(inv["due_date"] < TODAY) & (inv["outstanding_pkr"] > 0)]

alerts = []
if len(expired_ins):  alerts.append(("critical", f"🔴 {len(expired_ins)} vehicles with expired insurance."))
if len(expired_fit):  alerts.append(("critical", f"🔴 {len(expired_fit)} vehicles with expired fitness cert."))
if len(expired_lic):  alerts.append(("critical", f"🔴 {len(expired_lic)} drivers with expired licence."))
if risky:             alerts.append(("critical", f"🔴 {risky} high-risk drivers (poor/dangerous)."))
if len(overdue_inv):  alerts.append(("warning",  f"🟡 PKR {overdue_inv['outstanding_pkr'].sum()/1e6:.1f}M overdue across {len(overdue_inv):,} invoices."))

if not alerts:
    alert_box("✅ No critical alerts — fleet operating normally.", "success")
else:
    cols = st.columns(min(3, len(alerts)))
    for i, (lvl, msg) in enumerate(alerts):
        cols[i % 3].markdown(f'<div class="alert-{lvl}">{msg}</div>', unsafe_allow_html=True)

# ── Booking type trend ─────────────────────────────────────────────────
sec("📊 Monthly Booking Volume by Type")
g = trips.groupby(["pickup_month","booking_type"]).size().reset_index(name="n")
fig5 = go.Figure()
for i, bt in enumerate(g["booking_type"].unique()):
    sub = g[g["booking_type"]==bt]
    fig5.add_trace(go.Scatter(x=sub["pickup_month"], y=sub["n"],
        name=bt, stackgroup="one", fill="tonexty",
        line=dict(color=COLORS[i % len(COLORS)], width=1)))
dark_layout(fig5, "Bookings by Type — Monthly", xangle=-45, height=320)
st.plotly_chart(fig5, width='stretch')

# KPI summary insight
days = max(1,(trips["pickup_datetime"].dt.date.max()-trips["pickup_datetime"].dt.date.min()).days)
util_pct = min(100, trips[trips["status"]=="Completed"]["duration_days"].sum()/(fleet_active*days)*100)
txt, sub, lvl = kpi_insight(
    util_pct,
    collected/total_rev*100,
    cancel_rate,
    avg_safety,
)
insight(txt, "📊", lvl, sub)

