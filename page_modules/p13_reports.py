"""
Advanced Dynamic Reports — p13_reports.py

International-standard business reports with full contextual narrative prose.
Structure follows conventions used in US/SEC filings, UK FRC reporting,
KSA SAMA/CMA frameworks, and GCC board packs.

Report Types : Executive Summary | Financial | Operational | Maintenance | Driver Safety | Fleet
Periods      : Hourly | Daily | Weekly | Monthly | Quarterly | Bi-Annual | Annual | Custom
Export       : HTML→PDF (narrative report) + Excel (data) + CSV (raw)
"""

import io
from datetime import datetime, date
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st

from page_modules._shared import (
    inject, get_data, fmt, kpi, sec, alert_box, dark_layout,
    BRAND, NAVY, STEEL, GREEN, AMBER, ORANGE, TEXT, GRID, BG, COLORS,
)

inject()
dfs   = get_data()
TODAY = pd.Timestamp("2026-09-10")

# ══════════════════════════════════════════════════════════════════════
#  PAGE HEADER
# ══════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div style="display:flex;align-items:center;gap:12px;margin-bottom:6px;">
  <span style="font-size:2rem;">📊</span>
  <div>
    <div style="font-size:1.5rem;font-weight:800;color:{BRAND};">Advanced Dynamic Reports</div>
    <div style="font-size:.78rem;color:#5a7a96;">
      International-standard reports with narrative analysis ·
      Executive · Financial · Operational · Maintenance · Safety · Fleet
    </div>
  </div>
</div><hr style="border-color:#1e2f44;margin:6px 0 14px 0;">
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
#  CONFIGURATION
# ══════════════════════════════════════════════════════════════════════
sec("⚙️  Report Configuration")

REPORT_TYPES = {
    "🏆 Executive Summary":    "executive",
    "💰 Financial Report":     "financial",
    "🚗 Operational Report":   "operational",
    "🔧 Maintenance Report":   "maintenance",
    "🚦 Driver Safety Report": "safety",
    "🚘 Fleet Status Report":  "fleet",
}

PERIODS = [
    "⏱️ Hourly", "📅 Daily", "📆 Weekly", "🗓️ Monthly",
    "📊 Quarterly", "📈 Bi-Annual", "🗂️ Annual", "📌 Custom Range",
]

ca, cb, cc = st.columns(3)
report_label = ca.selectbox("Report Type", list(REPORT_TYPES.keys()), key="rpt_type")
period_label = cb.selectbox("Period",      PERIODS,                   key="rpt_period")
fleet_opts   = ["All Fleets"] + dfs["fleets"]["fleet_name"].tolist()
sel_fleet    = cc.selectbox("Fleet",       fleet_opts,                key="rpt_fleet")
report_type  = REPORT_TYPES[report_label]
period_key   = period_label.split(" ", 1)[1].lower()

# ── Date selectors ─────────────────────────────────────────────────────
if period_key == "custom range":
    d1, d2 = st.columns(2)
    start_dt = pd.Timestamp(d1.date_input("Start Date", value=date(2026, 8, 1),
                             min_value=date(2022,1,1), max_value=date(2026,9,10), key="rpt_sd"))
    end_dt   = pd.Timestamp(d2.date_input("End Date",   value=date(2026, 9, 10),
                             min_value=date(2022,1,1), max_value=date(2026,9,10), key="rpt_ed"))
elif period_key == "hourly":
    d1, d2 = st.columns(2)
    ref_day  = d1.date_input("Date", value=date(2026,9,9),
                              min_value=date(2022,1,1), max_value=date(2026,9,10), key="rpt_hr_day")
    hr_range = d2.select_slider("Hour range", options=list(range(24)),
                                 value=(0,23), key="rpt_hr_range")
    start_dt = pd.Timestamp(datetime(ref_day.year, ref_day.month, ref_day.day, hr_range[0]))
    end_dt   = pd.Timestamp(datetime(ref_day.year, ref_day.month, ref_day.day, hr_range[1], 59, 59))
elif period_key == "daily":
    ref_day  = st.date_input("Date", value=date(2026,9,9),
                              min_value=date(2022,1,1), max_value=date(2026,9,10), key="rpt_dy")
    start_dt = pd.Timestamp(ref_day)
    end_dt   = start_dt + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
elif period_key == "weekly":
    ref_day  = st.date_input("Any day within the week", value=date(2026,9,1),
                              min_value=date(2022,1,1), max_value=date(2026,9,10), key="rpt_wk")
    ref_ts   = pd.Timestamp(ref_day)
    start_dt = ref_ts - pd.Timedelta(days=ref_ts.weekday())
    end_dt   = start_dt + pd.Timedelta(days=6, hours=23, minutes=59, seconds=59)
elif period_key == "monthly":
    my, mm = st.columns(2)
    yr_m = my.selectbox("Year",  list(range(2022,2027)), index=4, key="rpt_my")
    mo_m = mm.selectbox("Month", list(range(1,13)),      index=7, key="rpt_mm")
    start_dt = pd.Timestamp(year=yr_m, month=mo_m, day=1)
    end_dt   = (start_dt + pd.DateOffset(months=1)) - pd.Timedelta(seconds=1)
elif period_key == "quarterly":
    qy, qq = st.columns(2)
    yr_q   = qy.selectbox("Year",    list(range(2022,2027)), index=4, key="rpt_qy")
    sel_q  = qq.selectbox("Quarter", ["Q1 (Jan-Mar)","Q2 (Apr-Jun)",
                                       "Q3 (Jul-Sep)","Q4 (Oct-Dec)"], index=2, key="rpt_qq")
    qmap   = {"Q1 (Jan-Mar)":(1,3),"Q2 (Apr-Jun)":(4,6),
               "Q3 (Jul-Sep)":(7,9),"Q4 (Oct-Dec)":(10,12)}
    qs, qe = qmap[sel_q]
    start_dt = pd.Timestamp(year=yr_q, month=qs, day=1)
    end_dt   = pd.Timestamp(year=yr_q, month=qe, day=1) \
               + pd.DateOffset(months=1) - pd.Timedelta(seconds=1)
elif period_key == "bi-annual":
    by, bh = st.columns(2)
    yr_b   = by.selectbox("Year", list(range(2022,2027)), index=4, key="rpt_by")
    sel_h  = bh.selectbox("Half", ["H1 (Jan-Jun)","H2 (Jul-Dec)"], index=1, key="rpt_bh")
    if sel_h.startswith("H1"):
        start_dt = pd.Timestamp(year=yr_b, month=1,  day=1)
        end_dt   = pd.Timestamp(year=yr_b, month=6,  day=30, hour=23, minute=59)
    else:
        start_dt = pd.Timestamp(year=yr_b, month=7,  day=1)
        end_dt   = pd.Timestamp(year=yr_b, month=12, day=31, hour=23, minute=59)
else:  # annual
    yr_a     = st.selectbox("Year", list(range(2022,2027)), index=4, key="rpt_ay")
    start_dt = pd.Timestamp(year=yr_a, month=1,  day=1)
    end_dt   = pd.Timestamp(year=yr_a, month=12, day=31, hour=23, minute=59)

period_str = f"{start_dt.strftime('%d %b %Y %H:%M')} → {end_dt.strftime('%d %b %Y %H:%M')}"
st.markdown(f'<div style="font-size:.76rem;color:#5a7a96;margin:4px 0 8px 0;">'
            f'⏱ Period: <strong style="color:{TEXT};">{period_str}</strong></div>',
            unsafe_allow_html=True)

gen_btn = st.button("🚀  Generate Report", type="primary", key="rpt_gen")
if not gen_btn and "_rpt_ready" not in st.session_state:
    st.info("Configure the report above and click **Generate Report**.")
    st.stop()

if gen_btn:
    st.session_state._rpt_ready  = True
    st.session_state._rpt_s      = start_dt
    st.session_state._rpt_e      = end_dt
    st.session_state._rpt_type   = report_type
    st.session_state._rpt_plbl   = period_label
    st.session_state._rpt_fleet  = sel_fleet
    st.session_state._rpt_rlbl   = report_label

start_dt     = st.session_state._rpt_s
end_dt       = st.session_state._rpt_e
report_type  = st.session_state._rpt_type
report_label = st.session_state._rpt_rlbl
sel_fleet    = st.session_state._rpt_fleet
period_label = st.session_state._rpt_plbl

# ══════════════════════════════════════════════════════════════════════
#  DATA SLICING
# ══════════════════════════════════════════════════════════════════════
def _fleet_filt(df, col="fleet_id"):
    if sel_fleet == "All Fleets":
        return df
    fid = dfs["fleets"].loc[dfs["fleets"]["fleet_name"]==sel_fleet, "fleet_id"]
    return df[df[col].isin(fid.values)] if len(fid) else df

trips = _fleet_filt(dfs["trips"])
inv   = _fleet_filt(dfs["invoices"])
fuel  = _fleet_filt(dfs["fuel_logs"])
maint = _fleet_filt(dfs["maintenance"])
tel   = dfs["telematics"]
veh   = _fleet_filt(dfs["vehicles"])
drv   = _fleet_filt(dfs["drivers"])
opex  = _fleet_filt(dfs["operating_expenses"])

t_p   = trips[(trips["pickup_datetime"]>=start_dt)&(trips["pickup_datetime"]<=end_dt)]
i_p   = inv[(inv["invoice_date"]>=start_dt)&(inv["invoice_date"]<=end_dt)]
f_p   = fuel[(fuel["fill_date"]>=start_dt)&(fuel["fill_date"]<=end_dt)]
m_pd  = pd.to_datetime(maint["maintenance_date"], errors="coerce")
m_p   = maint[(m_pd>=start_dt)&(m_pd<=end_dt)]
t_pd  = pd.to_datetime(tel["trip_date"], errors="coerce")
tel_p = tel[(t_pd>=start_dt)&(t_pd<=end_dt)]
tc_p  = t_p[t_p["status"]=="Completed"]

# ── trend granularity ─────────────────────────────────────────────────
_xfn_map = {
    "hourly":       lambda df: df["pickup_datetime"].dt.hour.astype(str).str.zfill(2)+":00",
    "daily":        lambda df: df["pickup_datetime"].dt.hour.astype(str).str.zfill(2)+":00",
    "weekly":       lambda df: df["pickup_datetime"].dt.day_name().str[:3],
    "monthly":      lambda df: df["pickup_datetime"].dt.day.astype(str),
    "quarterly":    lambda df: df["pickup_datetime"].dt.strftime("%b"),
    "bi-annual":    lambda df: df["pickup_datetime"].dt.strftime("%b"),
    "annual":       lambda df: df["pickup_datetime"].dt.strftime("%b"),
    "custom range": lambda df: df["pickup_datetime"].dt.strftime("%d %b"),
}
_xfn = _xfn_map.get(period_key, _xfn_map["custom range"])

# ── helpers ───────────────────────────────────────────────────────────
def pct(n, d):   return round(n/d*100, 1) if d else 0.0
def na(v, u=""): return f"{v:,.0f}{u}" if pd.notna(v) and v else "N/A"

def trend_series(df, dt_col, val_col, agg="sum"):
    if df.empty: return pd.DataFrame(columns=["period", val_col])
    tmp = df.copy()
    tmp["pickup_datetime"] = pd.to_datetime(tmp[dt_col], errors="coerce")
    tmp["period"] = _xfn(tmp)
    return tmp.groupby("period")[val_col].agg(agg).reset_index()

def no_data_msg():
    st.warning("⚠️  No data for the selected period and fleet. Try a wider range.")

# ── narrative box ─────────────────────────────────────────────────────
def narrative(title, paragraphs, icon="📝", level="info"):
    colour_map = {
        "info":    ("#1e3a5f", "#3b82f6", "#dbeafe"),
        "good":    ("#14532d", "#16a34a", "#dcfce7"),
        "warning": ("#78350f", "#d97706", "#fef3c7"),
        "danger":  ("#7f1d1d", "#dc2626", "#fee2e2"),
    }
    bg, border, text_c = colour_map.get(level, colour_map["info"])
    body = "".join(f'<p style="margin:0 0 8px 0;line-height:1.65;">{p}</p>' for p in paragraphs)
    st.markdown(f"""
<div style="background:{bg}22;border-left:4px solid {border};
            border-radius:0 8px 8px 0;padding:14px 18px;margin:12px 0;">
  <div style="font-weight:700;color:{border};font-size:.9rem;margin-bottom:8px;">
    {icon} {title}
  </div>
  <div style="font-size:.82rem;color:{text_c}cc;">
    {body}
  </div>
</div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════
#  REPORT HEADER BLOCK
# ═══════════════════════════════════════════════════════════════════════
period_days = max((end_dt - start_dt).days, 1)
st.markdown(f"""
<div style="background:linear-gradient(135deg,{NAVY}cc,#0a1525 100%);
            border:1px solid {BRAND}55;border-radius:12px;
            padding:18px 24px 14px;margin:14px 0 20px;">
  <div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px;">
    <div>
      <div style="font-size:1.2rem;font-weight:800;color:{BRAND};">{report_label}</div>
      <div style="font-size:.78rem;color:{TEXT};margin-top:4px;">
        🏢 {sel_fleet} &nbsp;|&nbsp; ⏱ {period_label}
        &nbsp;|&nbsp; 📅 {start_dt.strftime("%d %b %Y %H:%M")}
        → {end_dt.strftime("%d %b %Y %H:%M")}
        &nbsp;|&nbsp; {period_days:,} day(s)
      </div>
    </div>
    <div style="text-align:right;font-size:.7rem;color:#5a7a96;">
      <strong style="color:{TEXT};">Soft Rent a Car</strong><br>
      Fleet Intelligence Platform<br>
      Generated: {TODAY.strftime("%d %B %Y")}<br>
      <span style="color:{STEEL};">Muhammad Siddique · datawithms.top</span>
    </div>
  </div>
</div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════
#  EXECUTIVE SUMMARY REPORT
# ═══════════════════════════════════════════════════════════════════════
if report_type == "executive":

    billed     = i_p["total_amount_pkr"].sum()
    collected  = i_p["paid_amount_pkr"].sum()
    outstanding= i_p["outstanding_pkr"].sum()
    col_rate   = pct(collected, billed)
    n_trips    = len(t_p)
    n_comp     = (t_p["status"]=="Completed").sum()
    n_canc     = (t_p["status"]=="Cancelled").sum()
    n_noshow   = (t_p["status"]=="No Show").sum()
    comp_rate  = pct(n_comp, n_trips)
    canc_rate  = pct(n_canc, n_trips)
    avg_fare   = tc_p["trip_fare_pkr"].mean() if not tc_p.empty else 0
    avg_dist   = tc_p["distance_km"].mean()   if not tc_p.empty else 0
    avg_ss     = tel_p["safety_score"].mean() if not tel_p.empty else 0
    fuel_cost  = f_p["fuel_cost_pkr"].sum()
    maint_cost = m_p["total_cost_pkr"].sum()
    n_avail    = (veh["status"]=="Available").sum()
    n_on_trip  = (veh["status"]=="On Trip").sum()
    util_rate  = pct(n_on_trip, len(veh[veh["status"]!="Retired"]))
    n_danger   = int(drv["behavior_profile"].isin(["dangerous","poor"]).sum())

    # ── KPIs ────────────────────────────────────────────────────────────
    sec("📌 Key Performance Indicators")
    r1 = st.columns(4)
    kpi(r1[0], fmt(billed),          "Gross Revenue",       f"Collected {col_rate}%", True)
    kpi(r1[1], fmt(outstanding),     "Outstanding",          f"{len(i_p[i_p['outstanding_pkr']>0]):,} invoices", outstanding==0)
    kpi(r1[2], f"{n_trips:,}",       "Total Bookings",       f"{n_comp:,} completed", True)
    kpi(r1[3], f"{comp_rate}%",      "Completion Rate",      "Target ≥ 85%", comp_rate>=85)
    r2 = st.columns(4)
    kpi(r2[0], fmt(avg_fare),        "Avg Fare / Trip",      "Completed trips")
    kpi(r2[1], f"{avg_dist:.0f} km", "Avg Distance",         "Per completed trip")
    kpi(r2[2], f"{avg_ss:.1f}/100",  "Fleet Safety Score",   "Target ≥ 70", avg_ss>=70)
    kpi(r2[3], f"{util_rate}%",      "Fleet Utilisation",    f"{n_on_trip} on trip now", util_rate>=60)

    st.markdown("<hr style='border-color:#1e2f44;margin:14px 0'>", unsafe_allow_html=True)

    # ── MANAGEMENT COMMENTARY ────────────────────────────────────────────
    sec("📝 Management Commentary")

    # Revenue narrative
    rev_level = "strong" if col_rate >= 90 else ("satisfactory" if col_rate >= 75 else "below target")
    out_risk   = "low" if pct(outstanding, billed) < 10 else ("moderate" if pct(outstanding, billed) < 25 else "elevated")
    narrative(
        "Revenue & Collections Overview",
        [
            f"During the period {start_dt.strftime('%d %B %Y')} to {end_dt.strftime('%d %B %Y')}, "
            f"{sel_fleet} generated gross revenue of <strong>{fmt(billed)}</strong> PKR across "
            f"<strong>{len(i_p):,}</strong> invoices. Collections totalled <strong>{fmt(collected)}</strong> PKR, "
            f"representing a collection rate of <strong>{col_rate}%</strong> — "
            f"classified as <em>{rev_level}</em> against an industry benchmark of 90%.",
            f"Outstanding receivables stand at <strong>{fmt(outstanding)}</strong> PKR "
            f"({pct(outstanding,billed):.1f}% of gross revenue), presenting an <em>{out_risk}</em> credit risk. "
            f"Management should prioritise follow-up on invoices overdue beyond 30 days to maintain "
            f"healthy cash flow and working capital ratios.",
        ],
        "💰", "good" if col_rate >= 85 else "warning"
    )

    # Operations narrative
    ops_health = "healthy" if comp_rate >= 85 else ("adequate" if comp_rate >= 70 else "concerning")
    narrative(
        "Operational Performance Summary",
        [
            f"The fleet recorded <strong>{n_trips:,}</strong> bookings during the period, of which "
            f"<strong>{n_comp:,} ({comp_rate}%)</strong> were completed successfully. "
            f"This completion rate is <em>{ops_health}</em> relative to the 85% industry benchmark.",
            f"Cancellations accounted for <strong>{n_canc:,} ({canc_rate}%)</strong> of bookings, "
            f"while <strong>{n_noshow:,}</strong> bookings resulted in no-shows. "
            f"The average completed trip generated <strong>{fmt(avg_fare)}</strong> PKR over "
            f"<strong>{avg_dist:.0f} km</strong>. "
            f"Management should investigate the primary cancellation drivers to reduce revenue leakage.",
        ],
        "🚗", "good" if comp_rate >= 85 else "warning"
    )

    # Safety narrative
    ss_grade = "excellent" if avg_ss>=85 else ("good" if avg_ss>=70 else ("fair" if avg_ss>=55 else "poor"))
    narrative(
        "Safety & Compliance Assessment",
        [
            f"The fleet-wide average safety score for the period is <strong>{avg_ss:.1f}/100</strong>, "
            f"graded <em>{ss_grade}</em> under international fleet safety benchmarks "
            f"(IAM RoadSmart / OSHA / Saudi Traffic Law standards).",
            f"<strong>{n_danger}</strong> driver(s) are currently classified as 'poor' or 'dangerous', "
            f"representing a direct liability and insurance risk. "
            f"Immediate corrective action — including mandatory defensive driving training — "
            f"is recommended in line with KSA Ministerial Decision 30/2022 and UK DVSA operator guidance.",
        ],
        "🚦", "good" if avg_ss>=70 else "danger"
    )

    # Cost narrative
    total_cost = fuel_cost + maint_cost
    narrative(
        "Cost Management & Fleet Economics",
        [
            f"Operating costs for the period totalled <strong>{fmt(total_cost)}</strong> PKR, "
            f"comprising fuel expenditure of <strong>{fmt(fuel_cost)}</strong> PKR "
            f"and maintenance spend of <strong>{fmt(maint_cost)}</strong> PKR.",
            f"Fleet utilisation is <strong>{util_rate}%</strong> with <strong>{n_on_trip}</strong> "
            f"vehicles actively generating revenue and <strong>{n_avail}</strong> available. "
            f"A utilisation rate below 60% suggests excess capacity and an opportunity to optimise "
            f"the fleet size or intensify commercial activity.",
        ],
        "🔧", "info"
    )

    st.markdown("<hr style='border-color:#1e2f44;margin:14px 0'>", unsafe_allow_html=True)

    # ── Revenue trend chart ──────────────────────────────────────────────
    sec("📈 Revenue & Booking Trend")
    if not i_p.empty:
        rt = trend_series(i_p, "invoice_date", "total_amount_pkr")
        tt = trend_series(t_p, "pickup_datetime", "trip_id", agg="count")
        fig = go.Figure()
        if not rt.empty:
            fig.add_trace(go.Scatter(x=rt["period"].astype(str), y=rt["total_amount_pkr"],
                                      fill="tozeroy", fillcolor="rgba(230,57,70,.12)",
                                      line=dict(color=BRAND,width=2.5), name="Revenue PKR",
                                      mode="lines+markers", marker=dict(size=5)))
        if not tt.empty:
            fig.add_trace(go.Bar(x=tt["period"].astype(str), y=tt["trip_id"],
                                  name="Bookings", marker_color="rgba(69,123,157,0.53)",
                                  yaxis="y2", opacity=0.7))
        fig.update_layout(yaxis2=dict(overlaying="y", side="right", showgrid=False,
                                       tickfont=dict(color=STEEL)))
        dark_layout(fig, "Revenue (PKR) vs Booking Volume", height=320)
        st.plotly_chart(fig, use_container_width=True)

    # ── Booking mix & status ─────────────────────────────────────────────
    sec("📊 Booking Mix & Trip Status")
    if not t_p.empty:
        ca2, cb2 = st.columns(2)
        with ca2:
            bt = tc_p.groupby("booking_type")["trip_fare_pkr"].sum().reset_index().sort_values("trip_fare_pkr")
            fig_bt = go.Figure(go.Bar(x=bt["trip_fare_pkr"], y=bt["booking_type"],
                                       orientation="h", marker_color=STEEL,
                                       text=bt["trip_fare_pkr"].apply(fmt),
                                       textposition="outside", textfont=dict(color=TEXT)))
            dark_layout(fig_bt, "Revenue by Booking Type", height=320)
            st.plotly_chart(fig_bt, use_container_width=True)
        with cb2:
            sc = t_p["status"].value_counts().reset_index(); sc.columns=["status","n"]
            cmap = {"Completed":GREEN,"Cancelled":ORANGE,"In Progress":AMBER,"No Show":STEEL}
            fig_sc = go.Figure(go.Pie(labels=sc["status"], values=sc["n"], hole=0.52,
                                       marker_colors=[cmap.get(s,BRAND) for s in sc["status"]]))
            dark_layout(fig_sc, "Trip Status Distribution", height=320)
            st.plotly_chart(fig_sc, use_container_width=True)

    # ── Top customers ────────────────────────────────────────────────────
    sec("🏆 Top 10 Customers by Revenue")
    if not tc_p.empty:
        top_c = (tc_p.merge(dfs["customers"][["customer_id","full_name","customer_type"]],
                             on="customer_id", how="left")
                     .groupby(["full_name","customer_type"])["trip_fare_pkr"].sum()
                     .reset_index().sort_values("trip_fare_pkr", ascending=False).head(10))
        top_c["Revenue"] = top_c["trip_fare_pkr"].apply(fmt)
        st.dataframe(top_c[["full_name","customer_type","Revenue"]].rename(
            columns={"full_name":"Customer","customer_type":"Segment"}),
            use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════════════
#  FINANCIAL REPORT
# ═══════════════════════════════════════════════════════════════════════
elif report_type == "financial":

    billed     = i_p["total_amount_pkr"].sum()
    collected  = i_p["paid_amount_pkr"].sum()
    outstanding= i_p["outstanding_pkr"].sum()
    surcharge  = i_p["total_surcharge_pkr"].sum()
    discount   = i_p["discount_pkr"].sum()
    tax        = i_p["tax_pkr"].sum()
    col_rate   = pct(collected, billed)
    fuel_cost  = f_p["fuel_cost_pkr"].sum()
    maint_cost = m_p["total_cost_pkr"].sum()
    opex_mask  = (pd.to_datetime(opex["expense_month"],errors="coerce")>=start_dt) & \
                 (pd.to_datetime(opex["expense_month"],errors="coerce")<=end_dt)
    opex_cost  = opex[opex_mask]["amount_pkr"].sum() if not opex.empty else 0
    net_margin = billed - discount - fuel_cost - maint_cost - opex_cost

    sec("💵 Financial KPIs")
    r1 = st.columns(4)
    kpi(r1[0], fmt(billed),     "Gross Revenue",       "Invoiced total", True)
    kpi(r1[1], fmt(collected),  "Cash Collected",       f"{col_rate}% rate", col_rate>=90)
    kpi(r1[2], fmt(outstanding),"Accounts Receivable",  f"{pct(outstanding,billed):.1f}% of revenue", outstanding==0)
    kpi(r1[3], fmt(net_margin), "Estimated Net Margin", "", net_margin>0)
    r2 = st.columns(4)
    kpi(r2[0], fmt(surcharge),  "Surcharge Income",     "")
    kpi(r2[1], fmt(discount),   "Discounts Given",      "", False)
    kpi(r2[2], fmt(tax),        "Tax / GST Collected",  "")
    kpi(r2[3], fmt(fuel_cost+maint_cost), "Direct OpEx","Fuel + Maintenance")

    st.markdown("<hr style='border-color:#1e2f44;margin:14px 0'>", unsafe_allow_html=True)

    # ── Management Commentary ────────────────────────────────────────────
    sec("📝 Financial Management Commentary")

    margin_pct = pct(net_margin, billed)
    disc_pct   = pct(discount, billed)
    narrative(
        "Income Statement Overview",
        [
            f"For the period ending <strong>{end_dt.strftime('%d %B %Y')}</strong>, the fleet "
            f"generated gross revenue of <strong>{fmt(billed)}</strong> PKR. "
            f"After applying discounts of <strong>{fmt(discount)}</strong> PKR "
            f"({disc_pct}% of gross), net revenue stands at "
            f"<strong>{fmt(billed - discount)}</strong> PKR.",
            f"Direct operating expenses — fuel (<strong>{fmt(fuel_cost)}</strong> PKR) and "
            f"maintenance (<strong>{fmt(maint_cost)}</strong> PKR) — total "
            f"<strong>{fmt(fuel_cost + maint_cost)}</strong> PKR. "
            f"The estimated operating margin is <strong>{margin_pct:.1f}%</strong>. "
            f"This is benchmarked against a typical fleet operator target of 18–25% "
            f"(ICAP / GCC fleet management standards).",
        ],
        "💰", "good" if margin_pct >= 15 else "warning"
    )

    narrative(
        "Receivables & Credit Risk (IFRS 9 / GAAP ASC 310)",
        [
            f"Outstanding receivables of <strong>{fmt(outstanding)}</strong> PKR represent "
            f"<strong>{pct(outstanding,billed):.1f}%</strong> of gross billings. "
            f"Under IFRS 9 (and equivalent US GAAP ASC 310), receivables overdue beyond 90 days "
            f"should be classified as Stage 3 credit-impaired and provisioned accordingly.",
            f"The collection rate of <strong>{col_rate}%</strong> "
            + ("is within acceptable range." if col_rate >= 85 else
               "is below the 85% threshold. Management should review credit terms and "
               "escalate overdue accounts to the collections process immediately."),
        ],
        "⚠️", "good" if col_rate >= 85 else "danger"
    )

    narrative(
        "Tax & Regulatory Compliance",
        [
            f"Tax collected during the period amounts to <strong>{fmt(tax)}</strong> PKR. "
            f"Management should ensure timely remittance to the Federal Board of Revenue (FBR) "
            f"under Pakistan's Sales Tax Act, or equivalent authority in the operating jurisdiction "
            f"(HMRC – UK, Zakat and Tax Authority – KSA, IRS – US).",
            f"Surcharge income of <strong>{fmt(surcharge)}</strong> PKR should be verified against "
            f"contractual rate cards to ensure compliance with consumer protection regulations.",
        ],
        "📋", "info"
    )

    st.markdown("<hr style='border-color:#1e2f44;margin:14px 0'>", unsafe_allow_html=True)

    # ── P&L Waterfall ────────────────────────────────────────────────────
    sec("📉 Estimated Profit & Loss Waterfall")
    fig_wf = go.Figure(go.Waterfall(
        measure=["absolute","relative","relative","relative","relative","total"],
        x=["Gross Revenue","Discounts","Fuel Cost","Maintenance","Other OpEx","Net Estimate"],
        y=[billed, -discount, -fuel_cost, -maint_cost, -opex_cost,
           billed-discount-fuel_cost-maint_cost-opex_cost],
        connector=dict(line=dict(color=GRID, width=1)),
        increasing=dict(marker_color=GREEN),
        decreasing=dict(marker_color=ORANGE),
        totals=dict(marker_color=BRAND),
        text=[fmt(abs(v)) for v in [billed,-discount,-fuel_cost,-maint_cost,-opex_cost,
                                     billed-discount-fuel_cost-maint_cost-opex_cost]],
        textposition="outside", textfont=dict(color=TEXT),
    ))
    dark_layout(fig_wf, "P&L Waterfall — Period Estimate", height=380)
    st.plotly_chart(fig_wf, use_container_width=True)

    # ── Collections trend + Payment mix ──────────────────────────────────
    sec("📈 Collections Trend & Payment Methods")
    ca3, cb3 = st.columns(2)
    with ca3:
        rt = trend_series(i_p, "invoice_date", "total_amount_pkr")
        rc = trend_series(i_p, "invoice_date", "paid_amount_pkr")
        fig_ct = go.Figure()
        if not rt.empty:
            fig_ct.add_trace(go.Scatter(x=rt["period"].astype(str), y=rt["total_amount_pkr"],
                                         fill="tozeroy", fillcolor="rgba(230,57,70,.1)",
                                         line=dict(color=BRAND,width=2), name="Billed"))
        if not rc.empty:
            fig_ct.add_trace(go.Scatter(x=rc["period"].astype(str), y=rc["paid_amount_pkr"],
                                         fill="tozeroy", fillcolor="rgba(42,157,143,.1)",
                                         line=dict(color=GREEN,width=2), name="Collected"))
        dark_layout(fig_ct, "Billed vs Collected", height=300)
        st.plotly_chart(fig_ct, use_container_width=True)
    with cb3:
        pm = i_p["payment_method"].value_counts().reset_index(); pm.columns=["m","c"]
        fig_pm = go.Figure(go.Pie(labels=pm["m"], values=pm["c"], hole=0.52,
                                   marker_colors=COLORS[:len(pm)]))
        dark_layout(fig_pm, "Payment Method Split", height=300)
        st.plotly_chart(fig_pm, use_container_width=True)

    # ── AR Aging ─────────────────────────────────────────────────────────
    sec("🗓️ Accounts Receivable Aging Schedule")
    unpaid = i_p[i_p["outstanding_pkr"]>0].copy()
    if not unpaid.empty:
        unpaid["_due"] = pd.to_datetime(unpaid["due_date"], errors="coerce")
        unpaid["days_due"] = (TODAY - unpaid["_due"]).dt.days.fillna(0).astype(int)
        def _age_bucket(d):
            if d<=0:  return "Current (Not Due)"
            if d<=30: return "1–30 Days"
            if d<=60: return "31–60 Days"
            if d<=90: return "61–90 Days"
            return "Over 90 Days"
        unpaid["Aging"] = unpaid["days_due"].apply(_age_bucket)
        aging = unpaid.groupby("Aging")["outstanding_pkr"].sum().reset_index()
        order = ["Current (Not Due)","1–30 Days","31–60 Days","61–90 Days","Over 90 Days"]
        aging["Aging"] = pd.Categorical(aging["Aging"], categories=order, ordered=True)
        aging = aging.sort_values("Aging").dropna(subset=["Aging"])
        age_colours = {
            "Current (Not Due)": GREEN, "1–30 Days": AMBER,
            "31–60 Days": ORANGE, "61–90 Days": BRAND, "Over 90 Days": "#8B0000"
        }
        fig_age = go.Figure(go.Bar(
            x=aging["Aging"].astype(str), y=aging["outstanding_pkr"],
            marker_color=[age_colours.get(b, STEEL) for b in aging["Aging"].tolist()],
            text=aging["outstanding_pkr"].apply(fmt),
            textposition="outside", textfont=dict(color=TEXT)
        ))
        dark_layout(fig_age, "AR Aging — Outstanding by Bucket", height=300)
        st.plotly_chart(fig_age, use_container_width=True)

        over_90 = unpaid[unpaid["days_due"]>90]["outstanding_pkr"].sum()
        narrative(
            "Aging Analysis — Audit Note",
            [
                f"Receivables aged over 90 days total <strong>{fmt(over_90)}</strong> PKR. "
                f"Per IFRS 9 / IAS 37, these should be assessed for expected credit losses (ECL) "
                f"and appropriate provisions recognised in the financial statements.",
                f"Current (not yet due) receivables represent the healthiest portion of the book. "
                f"The 31–90 day bands require active collection follow-up. "
                f"Legal recovery processes should be initiated on Over-90 Day balances "
                f"in accordance with local contract law.",
            ],
            "⚖️", "warning" if over_90 > 0 else "good"
        )

        disp = (unpaid[["invoice_id","invoice_date","due_date",
                          "outstanding_pkr","payment_status","Aging","days_due"]]
                .sort_values("days_due", ascending=False).head(25)
                .drop(columns=["days_due"]))
        disp["outstanding_pkr"] = disp["outstanding_pkr"].apply(fmt)
        st.dataframe(disp.rename(columns={
            "invoice_id":"Invoice","invoice_date":"Date","due_date":"Due",
            "outstanding_pkr":"Outstanding","payment_status":"Status"}),
            use_container_width=True, hide_index=True)
    else:
        alert_box("✅ No outstanding receivables in this period.", "success")


# ═══════════════════════════════════════════════════════════════════════
#  OPERATIONAL REPORT
# ═══════════════════════════════════════════════════════════════════════
elif report_type == "operational":

    n_tot   = len(t_p)
    n_comp  = (t_p["status"]=="Completed").sum()
    n_canc  = (t_p["status"]=="Cancelled").sum()
    n_prog  = (t_p["status"]=="In Progress").sum()
    n_ns    = (t_p["status"]=="No Show").sum()
    comp_r  = pct(n_comp, n_tot)
    canc_r  = pct(n_canc, n_tot)
    avg_d   = tc_p["distance_km"].mean()   if not tc_p.empty else 0
    avg_dur = tc_p["duration_days"].mean() if not tc_p.empty else 0
    avg_f   = tc_p["trip_fare_pkr"].mean() if not tc_p.empty else 0
    rev     = tc_p["trip_fare_pkr"].sum()  if not tc_p.empty else 0

    sec("🚗 Operational KPIs")
    r1 = st.columns(4)
    kpi(r1[0], f"{n_tot:,}",        "Total Bookings",    "Period total")
    kpi(r1[1], f"{n_comp:,}",        "Completed",         f"{comp_r}%", comp_r>=85)
    kpi(r1[2], f"{n_canc:,}",        "Cancelled",         f"{canc_r}%", n_canc==0)
    kpi(r1[3], f"{n_ns:,}",          "No Shows",          f"{pct(n_ns,n_tot):.1f}%", n_ns==0)
    r2 = st.columns(4)
    kpi(r2[0], fmt(rev),             "Trip Revenue",      "Completed trips")
    kpi(r2[1], f"{avg_d:.0f} km",    "Avg Distance",      "Completed")
    kpi(r2[2], f"{avg_dur:.2f} days","Avg Duration",      "Completed")
    kpi(r2[3], fmt(avg_f),           "Avg Fare",          "Per completed trip")

    st.markdown("<hr style='border-color:#1e2f44;margin:14px 0'>", unsafe_allow_html=True)

    sec("📝 Operational Management Commentary")

    top_city = tc_p["pickup_city"].mode()[0] if not tc_p.empty else "N/A"
    top_type = tc_p["booking_type"].mode()[0] if not tc_p.empty else "N/A"
    top_canc = (t_p[t_p["status"]=="Cancelled"]["cancellation_reason"]
                .mode()[0] if n_canc > 0 else "none recorded")

    narrative(
        "Booking Volume & Service Delivery",
        [
            f"The fleet processed <strong>{n_tot:,}</strong> booking requests "
            f"during the period. Service delivery achieved a completion rate of "
            f"<strong>{comp_r}%</strong>, which is "
            + ("above" if comp_r >= 85 else "below") +
            f" the 85% target widely used in UK/US fleet management benchmarks.",
            f"The highest-demand city was <strong>{top_city}</strong>, and the most booked "
            f"service type was <strong>{top_type}</strong>. "
            f"Revenue from completed trips totalled <strong>{fmt(rev)}</strong> PKR at an "
            f"average of <strong>{fmt(avg_f)}</strong> PKR per trip.",
        ],
        "📦", "good" if comp_r >= 85 else "warning"
    )

    narrative(
        "Cancellation & Revenue Leakage Analysis",
        [
            f"<strong>{n_canc:,}</strong> bookings ({canc_r}%) were cancelled during the period. "
            f"The leading cancellation reason was <em>'{top_canc}'</em>. "
            f"No-shows accounted for an additional <strong>{n_ns:,}</strong> bookings. "
            f"Combined, these represent a direct revenue leakage risk.",
            f"Industry best practice (BVRLA – UK, ACRA – US) recommends maintaining "
            f"cancellation rates below 10% through advance deposit policies, "
            f"SMS/WhatsApp confirmation reminders 24 hours before pickup, "
            f"and dynamic no-show penalty enforcement.",
        ],
        "⚠️", "warning" if canc_r > 10 else "good"
    )

    st.markdown("<hr style='border-color:#1e2f44;margin:14px 0'>", unsafe_allow_html=True)

    sec("📈 Trip Volume & Revenue Trend")
    if not t_p.empty:
        vt = trend_series(t_p, "pickup_datetime", "trip_id", agg="count")
        rv = trend_series(tc_p, "pickup_datetime", "trip_fare_pkr")
        fig_v = go.Figure()
        if not vt.empty:
            fig_v.add_trace(go.Bar(x=vt["period"].astype(str), y=vt["trip_id"],
                                    name="Bookings", marker_color="rgba(69,123,157,0.6)"))
        if not rv.empty:
            fig_v.add_trace(go.Scatter(x=rv["period"].astype(str), y=rv["trip_fare_pkr"],
                                        name="Revenue", yaxis="y2",
                                        line=dict(color=BRAND,width=2.5), mode="lines+markers"))
        fig_v.update_layout(yaxis2=dict(overlaying="y",side="right",showgrid=False,
                                         tickfont=dict(color=BRAND)))
        dark_layout(fig_v, "Booking Volume vs Revenue", height=320)
        st.plotly_chart(fig_v, use_container_width=True)

    sec("📊 Booking Types & Cancellation Reasons")
    ca4, cb4 = st.columns(2)
    with ca4:
        if not t_p.empty:
            bt = t_p.groupby("booking_type")["trip_id"].count().reset_index().sort_values("trip_id")
            fig_bt = go.Figure(go.Bar(x=bt["trip_id"], y=bt["booking_type"],
                                       orientation="h", marker_color=STEEL,
                                       text=bt["trip_id"], textposition="outside",
                                       textfont=dict(color=TEXT)))
            dark_layout(fig_bt, "Trips by Booking Type", height=320)
            st.plotly_chart(fig_bt, use_container_width=True)
    with cb4:
        canc_df = t_p[t_p["status"]=="Cancelled"]
        if not canc_df.empty:
            cr = canc_df["cancellation_reason"].fillna("Unknown").value_counts().reset_index()
            cr.columns = ["reason","count"]
            fig_cr = go.Figure(go.Pie(labels=cr["reason"], values=cr["count"],
                                       hole=0.52, marker_colors=COLORS[:len(cr)]))
            dark_layout(fig_cr, "Cancellation Reasons", height=320)
            st.plotly_chart(fig_cr, use_container_width=True)
        else:
            st.info("No cancellations in this period.")

    sec("🗺️ Top Routes")
    if not tc_p.empty:
        routes = (tc_p.groupby(["pickup_city","dropoff_city"])["trip_id"]
                      .count().reset_index().rename(columns={"trip_id":"trips"})
                      .sort_values("trips", ascending=False).head(15))
        routes["route"] = routes["pickup_city"] + " → " + routes["dropoff_city"]
        fig_rt = go.Figure(go.Bar(y=routes["route"], x=routes["trips"],
                                   orientation="h", marker_color=COLORS[:len(routes)],
                                   text=routes["trips"], textposition="outside"))
        dark_layout(fig_rt, "Top 15 Routes by Completed Trips", height=420)
        st.plotly_chart(fig_rt, use_container_width=True)

    if period_key in ("hourly","daily"):
        sec("⏱️ Hourly Demand Pattern")
        if not t_p.empty:
            hr = t_p.copy()
            hr["hour"] = hr["pickup_datetime"].dt.hour
            ha = hr.groupby("hour").agg(trips=("trip_id","count"),
                                         rev=("trip_fare_pkr","sum")).reset_index()
            fig_hr = go.Figure()
            fig_hr.add_trace(go.Bar(x=ha["hour"],y=ha["trips"],name="Bookings",
                                     marker_color=STEEL))
            fig_hr.add_trace(go.Scatter(x=ha["hour"],y=ha["rev"],name="Revenue",
                                         yaxis="y2", line=dict(color=BRAND,width=2)))
            fig_hr.update_layout(
                xaxis=dict(title="Hour of Day", dtick=1),
                yaxis2=dict(overlaying="y",side="right",showgrid=False,
                            tickfont=dict(color=BRAND))
            )
            dark_layout(fig_hr, "Hourly Demand & Revenue", height=300)
            st.plotly_chart(fig_hr, use_container_width=True)

    sec("📋 Trip Detail Records")
    if not t_p.empty:
        show = t_p[["trip_id","booking_type","pickup_city","dropoff_city",
                     "pickup_datetime","distance_km","trip_fare_pkr","status"]].copy()
        show = show.sort_values("pickup_datetime", ascending=False)
        show["trip_fare_pkr"] = show["trip_fare_pkr"].apply(fmt)
        st.dataframe(show.rename(columns={"trip_id":"Trip ID","booking_type":"Type",
            "pickup_city":"From","dropoff_city":"To","pickup_datetime":"Pickup",
            "distance_km":"Dist (km)","trip_fare_pkr":"Fare","status":"Status"}),
            use_container_width=True, hide_index=True)
    else:
        no_data_msg()


# ═══════════════════════════════════════════════════════════════════════
#  MAINTENANCE REPORT
# ═══════════════════════════════════════════════════════════════════════
elif report_type == "maintenance":

    tc   = m_p["total_cost_pkr"].sum()
    pc   = m_p["parts_cost_pkr"].sum()
    lc   = m_p["labour_cost_pkr"].sum()
    ns   = len(m_p)
    avg_c = m_p["total_cost_pkr"].mean() if ns else 0
    nd_dt = pd.to_datetime(dfs["maintenance"]["next_due_date"], errors="coerce")
    overdue  = int((nd_dt < TODAY).sum())
    due_30   = int(nd_dt.between(TODAY, TODAY+pd.Timedelta(30,"d")).sum())
    in_maint = (veh["status"]=="Under Maintenance").sum()

    sec("🔧 Maintenance KPIs")
    r1 = st.columns(4)
    kpi(r1[0], fmt(tc),          "Total Maint. Cost",   "Parts + Labour")
    kpi(r1[1], fmt(pc),          "Parts Cost",           f"{pct(pc,tc):.0f}% of total")
    kpi(r1[2], fmt(lc),          "Labour Cost",          f"{pct(lc,tc):.0f}% of total")
    kpi(r1[3], f"{ns}",          "Service Events",       f"Avg {fmt(avg_c)}")
    r2 = st.columns(4)
    kpi(r2[0], f"{overdue}",     "Overdue Services",     "Past next_due_date", overdue==0)
    kpi(r2[1], f"{due_30}",      "Due in 30 Days",       "Action required", due_30==0)
    kpi(r2[2], f"{in_maint}",    "In Maintenance Now",   "Fleet vehicles")
    kpi(r2[3], f"{(veh['status']=='Available').sum()}", "Available Vehicles", "")

    st.markdown("<hr style='border-color:#1e2f44;margin:14px 0'>", unsafe_allow_html=True)

    sec("📝 Maintenance Management Commentary")

    top_type = m_p["maintenance_type"].mode()[0] if ns else "N/A"
    parts_pct = pct(pc, tc)

    narrative(
        "Fleet Maintenance Overview",
        [
            f"During the report period, <strong>{ns}</strong> maintenance events were recorded "
            f"at a total cost of <strong>{fmt(tc)}</strong> PKR. "
            f"The most frequent service type was <strong>{top_type}</strong>.",
            f"The parts-to-labour cost ratio is <strong>{parts_pct:.0f}% / "
            f"{100-parts_pct:.0f}%</strong>. "
            f"A parts ratio above 70% may indicate ageing vehicles with high component wear. "
            f"Industry benchmarks suggest a healthy fleet should target a 55:45 parts-to-labour split "
            f"(Fleet News UK, ATA TMC standards).",
        ],
        "🔧", "info"
    )

    narrative(
        "Regulatory Compliance & Roadworthiness",
        [
            f"<strong>{overdue}</strong> vehicle(s) are overdue for scheduled maintenance. "
            f"Operating vehicles past their service due dates violates operator licence conditions "
            f"under UK DVSA Operator Compliance Risk Score (OCRS) rules, "
            f"Saudi Traffic Law Article 49, and US DOT FMCSA regulations.",
            f"<strong>{due_30}</strong> vehicle(s) are due for service within 30 days. "
            f"Proactive scheduling is recommended to avoid operational disruption and "
            f"to maintain fitness certificate compliance.",
        ],
        "⚠️", "danger" if overdue > 0 else ("warning" if due_30 > 0 else "good")
    )

    if m_p.empty:
        no_data_msg()
    else:
        st.markdown("<hr style='border-color:#1e2f44;margin:14px 0'>", unsafe_allow_html=True)
        sec("📊 Cost by Maintenance Type")
        ca5, cb5 = st.columns(2)
        with ca5:
            mt = (m_p.groupby("maintenance_type")["total_cost_pkr"]
                     .sum().reset_index().sort_values("total_cost_pkr"))
            fig_mt = go.Figure(go.Bar(x=mt["total_cost_pkr"], y=mt["maintenance_type"],
                                       orientation="h", marker_color=ORANGE,
                                       text=mt["total_cost_pkr"].apply(fmt),
                                       textposition="outside"))
            dark_layout(fig_mt, "Total Cost by Type", height=320)
            st.plotly_chart(fig_mt, use_container_width=True)
        with cb5:
            mc = (m_p.groupby("maintenance_type")["maint_id"]
                     .count().reset_index().sort_values("maint_id"))
            fig_mc = go.Figure(go.Bar(x=mc["maint_id"], y=mc["maintenance_type"],
                                       orientation="h", marker_color=STEEL,
                                       text=mc["maint_id"], textposition="outside"))
            dark_layout(fig_mc, "Count by Type", height=320)
            st.plotly_chart(fig_mc, use_container_width=True)

        sec("📈 Maintenance Cost Trend")
        mt_trend = (m_p.assign(pickup_datetime=pd.to_datetime(m_p["maintenance_date"],errors="coerce"))
                       .assign(period=lambda df: _xfn(df))
                       .groupby("period")["total_cost_pkr"].sum().reset_index())
        fig_mtr = go.Figure(go.Scatter(x=mt_trend["period"].astype(str),
                                        y=mt_trend["total_cost_pkr"],
                                        fill="tozeroy", fillcolor="rgba(231,111,81,.15)",
                                        line=dict(color=ORANGE,width=2.5),
                                        mode="lines+markers"))
        dark_layout(fig_mtr, "Maintenance Cost over Period", height=260)
        st.plotly_chart(fig_mtr, use_container_width=True)

        sec("🚘 Top 10 Vehicles by Maintenance Cost")
        vc = (m_p.merge(dfs["vehicles"][["vehicle_id","make","model","year"]],
                         on="vehicle_id",how="left")
                 .groupby(["vehicle_id","make","model","year"])["total_cost_pkr"]
                 .sum().reset_index().sort_values("total_cost_pkr",ascending=False).head(10))
        vc["label"] = vc["make"]+" "+vc["model"]+" ("+vc["year"].astype(str)+")"
        fig_vc = go.Figure(go.Bar(y=vc["label"],x=vc["total_cost_pkr"],
                                   orientation="h",marker_color=BRAND,
                                   text=vc["total_cost_pkr"].apply(fmt),
                                   textposition="outside"))
        dark_layout(fig_vc, "Top 10 Costliest Vehicles", height=320)
        st.plotly_chart(fig_vc, use_container_width=True)

        sec("📋 Maintenance Records")
        dm = m_p[["maint_id","vehicle_id","maintenance_type","maintenance_date",
                   "parts_cost_pkr","labour_cost_pkr","total_cost_pkr","status"]].copy()
        for c2 in ["parts_cost_pkr","labour_cost_pkr","total_cost_pkr"]:
            dm[c2] = dm[c2].apply(fmt)
        st.dataframe(dm, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════════════
#  DRIVER SAFETY REPORT
# ═══════════════════════════════════════════════════════════════════════
elif report_type == "safety":

    avg_ss  = tel_p["safety_score"].mean()     if not tel_p.empty else 0
    n_acc   = int(tel_p["accident_occurred"].astype(int).sum()) if not tel_p.empty else 0
    n_cpl   = int(tel_p["complaint_filed"].astype(int).sum())   if not tel_p.empty else 0
    avg_rt  = tel_p["customer_rating"].mean()  if not tel_p.empty else 0
    n_tel   = len(tel_p)
    acc_r   = pct(n_acc, n_tel)
    n_hb    = int(tel_p["harsh_brake_events"].sum()) if not tel_p.empty else 0
    n_ha    = int(tel_p["harsh_accel_events"].sum()) if not tel_p.empty else 0
    n_danger= int(drv["behavior_profile"].isin(["dangerous"]).sum())
    n_poor  = int(drv["behavior_profile"].eq("poor").sum())

    sec("🚦 Safety KPIs")
    r1 = st.columns(4)
    kpi(r1[0], f"{avg_ss:.1f}/100", "Avg Safety Score",   "Target ≥ 70", avg_ss>=70)
    kpi(r1[1], f"{n_acc}",          "Accidents Recorded", f"{acc_r}% of trips", n_acc==0)
    kpi(r1[2], f"{n_cpl}",          "Complaints Filed",   f"of {n_tel:,} trips", n_cpl==0)
    kpi(r1[3], f"{avg_rt:.2f}/5",   "Avg Customer Rating","Target ≥ 4.0", avg_rt>=4)
    r2 = st.columns(4)
    kpi(r2[0], f"{n_hb:,}",         "Harsh Brake Events", "Fleet total")
    kpi(r2[1], f"{n_ha:,}",         "Harsh Accel Events", "Fleet total")
    kpi(r2[2], f"{n_danger}",        "Dangerous Drivers",  "Active",  n_danger==0)
    kpi(r2[3], f"{n_poor}",          "Poor Behavior",       "Active",  n_poor==0)

    st.markdown("<hr style='border-color:#1e2f44;margin:14px 0'>", unsafe_allow_html=True)

    sec("📝 Safety Management Commentary")

    ss_grade = ("Excellent" if avg_ss>=85 else "Good" if avg_ss>=70
                else "Requires Improvement" if avg_ss>=55 else "Critical — Immediate Action Required")
    narrative(
        "Fleet Safety Score Assessment",
        [
            f"The fleet achieved an average safety score of <strong>{avg_ss:.1f}/100</strong> "
            f"for the period, graded <em><strong>{ss_grade}</strong></em>.",
            f"This score is benchmarked against the IAM RoadSmart Fleet Standard, "
            f"OSHA 29 CFR 1910 (US), UK Highway Code operator duty-of-care obligations, "
            f"and KSA General Traffic Department fleet safety requirements. "
            f"A score below 70 triggers mandatory driver risk review under most operator licence frameworks.",
        ],
        "🛡️", "good" if avg_ss>=70 else "danger"
    )

    narrative(
        "Incident & Complaint Analysis",
        [
            f"<strong>{n_acc}</strong> accident(s) were recorded ({acc_r}% of monitored trips). "
            f"Each accident triggers mandatory reporting obligations under: "
            f"UK Road Traffic Act 1988 s.170, NHTSA crash reporting (US), "
            f"and Saudi Traffic Law Article 71.",
            f"Customer complaints totalled <strong>{n_cpl}</strong>. "
            f"The average customer rating of <strong>{avg_rt:.2f}/5</strong> should be cross-referenced "
            f"with complaint categories. Ratings below 3.5 indicate systemic service quality issues "
            f"requiring structured improvement plans (e.g., ISO 39001 Road Traffic Safety Management).",
        ],
        "⚠️", "danger" if n_acc > 0 else ("warning" if n_cpl > 5 else "good")
    )

    narrative(
        "High-Risk Driver Action Plan",
        [
            f"<strong>{n_danger}</strong> driver(s) are classified as <em>dangerous</em> and "
            f"<strong>{n_poor}</strong> as <em>poor</em>. "
            f"These drivers represent elevated insurance liability and regulatory exposure.",
            f"Recommended actions: (1) Immediate suspension pending risk assessment, "
            f"(2) Mandatory defensive driving programme (IAM, RoSPA, or equivalent), "
            f"(3) Telematics-monitored probationary period, "
            f"(4) Insurance notification as required by policy terms.",
        ],
        "🚨", "danger" if (n_danger+n_poor) > 0 else "good"
    )

    if tel_p.empty:
        no_data_msg()
    else:
        st.markdown("<hr style='border-color:#1e2f44;margin:14px 0'>", unsafe_allow_html=True)
        sec("📊 Safety Score Distribution & Accident Trend")
        ca6, cb6 = st.columns(2)
        with ca6:
            fig_d = go.Figure(go.Histogram(x=tel_p["safety_score"], nbinsx=20,
                                            marker_color=STEEL,
                                            marker_line=dict(color=NAVY,width=1)))
            fig_d.add_vline(x=70,line_dash="dash",line_color=AMBER,
                             annotation_text="Target 70",annotation_font_color=AMBER)
            dark_layout(fig_d, "Safety Score Distribution", height=300)
            st.plotly_chart(fig_d, use_container_width=True)
        with cb6:
            at = (tel_p.rename(columns={"trip_date":"pickup_datetime"})
                       .assign(period=lambda df: _xfn(df))
                       .groupby("period")["accident_occurred"]
                       .apply(lambda x: x.astype(int).sum()).reset_index())
            fig_at = go.Figure(go.Bar(x=at["period"].astype(str),
                                       y=at["accident_occurred"],
                                       marker_color=BRAND))
            dark_layout(fig_at, "Accidents by Period", height=300)
            st.plotly_chart(fig_at, use_container_width=True)

        sec("⚡ Harsh Events vs Customer Rating")
        fig_sc = go.Figure(go.Scatter(
            x=tel_p["harsh_brake_events"], y=tel_p["customer_rating"],
            mode="markers",
            marker=dict(color=tel_p["safety_score"], colorscale="RdYlGn",
                        size=5, opacity=0.6, showscale=True,
                        colorbar=dict(title="Safety Score", tickfont=dict(color=TEXT))),
        ))
        dark_layout(fig_sc, "Harsh Braking vs Customer Rating (colour = Safety Score)", height=340)
        st.plotly_chart(fig_sc, use_container_width=True)

        sec("🏅 Driver Safety Leaderboard")
        dl = (tel_p.merge(dfs["drivers"][["driver_id","full_name","behavior_profile"]],
                           on="driver_id", how="left")
                   .groupby(["driver_id","full_name","behavior_profile"])
                   .agg(trips=("trip_id","count"),
                        avg_score=("safety_score","mean"),
                        accidents=("accident_occurred",lambda x: x.astype(int).sum()),
                        complaints=("complaint_filed",lambda x: x.astype(int).sum()),
                        avg_rating=("customer_rating","mean"))
                   .reset_index()
                   .sort_values("avg_score", ascending=False))
        dl["avg_score"]  = dl["avg_score"].round(1)
        dl["avg_rating"] = dl["avg_rating"].round(2)
        st.dataframe(dl.rename(columns={"full_name":"Driver","behavior_profile":"Profile",
            "trips":"Trips","avg_score":"Avg Safety","accidents":"Accidents",
            "complaints":"Complaints","avg_rating":"Avg Rating"}),
            use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════════════
#  FLEET STATUS REPORT
# ═══════════════════════════════════════════════════════════════════════
elif report_type == "fleet":

    n_tot   = len(veh)
    n_avail = (veh["status"]=="Available").sum()
    n_trip  = (veh["status"]=="On Trip").sum()
    n_maint = (veh["status"]=="Under Maintenance").sum()
    n_retd  = (veh["status"]=="Retired").sum()
    util_r  = pct(n_trip, n_tot - n_retd)
    ins_dt  = pd.to_datetime(veh["insurance_expiry"], errors="coerce")
    fit_dt  = pd.to_datetime(veh["fitness_cert_expiry"], errors="coerce")
    exp_ins = int((ins_dt < TODAY).sum())
    exp_fit = int((fit_dt < TODAY).sum())
    avg_odo = veh["odometer_km"].mean()
    fuel_eff= f_p["fuel_efficiency_kmpl"].mean() if not f_p.empty else 0
    fuel_c  = f_p["fuel_cost_pkr"].sum()

    sec("🚘 Fleet KPIs")
    r1 = st.columns(4)
    kpi(r1[0], f"{n_tot}",          "Total Vehicles",      f"{n_retd} retired")
    kpi(r1[1], f"{n_avail}",        "Available Now",        f"{util_r}% utilised", n_avail>0)
    kpi(r1[2], f"{n_trip}",         "On Trip",              "Revenue generating")
    kpi(r1[3], f"{n_maint}",        "In Maintenance",       "", n_maint==0)
    r2 = st.columns(4)
    kpi(r2[0], f"{exp_ins}",        "Expired Insurance",    "Urgent — compliance risk", exp_ins==0)
    kpi(r2[1], f"{exp_fit}",        "Expired Fitness Cert", "Compliance risk", exp_fit==0)
    kpi(r2[2], f"{avg_odo:,.0f} km","Avg Odometer",         "Fleet average")
    kpi(r2[3], f"{fuel_eff:.2f} kmpl","Avg Fuel Efficiency","Period average", fuel_eff>=12)

    st.markdown("<hr style='border-color:#1e2f44;margin:14px 0'>", unsafe_allow_html=True)

    sec("📝 Fleet Management Commentary")

    narrative(
        "Fleet Utilisation & Availability",
        [
            f"The active fleet (excluding {n_retd} retired units) stands at "
            f"<strong>{n_tot - n_retd}</strong> vehicles. "
            f"Current utilisation is <strong>{util_r}%</strong> with <strong>{n_trip}</strong> "
            f"vehicles actively generating revenue.",
            f"Industry utilisation benchmarks for commercial rental fleets are 65–80% "
            f"(BVRLA Annual Report, ARA Fleet Outlook). "
            + ("Current utilisation is within target range." if util_r >= 65 else
               "Utilisation is below benchmark — consider intensifying commercial activity, "
               "targeted promotions, or right-sizing the fleet."),
        ],
        "🚘", "good" if util_r >= 65 else "warning"
    )

    narrative(
        "Regulatory Compliance — Insurance & Fitness Certificates",
        [
            f"<strong>{exp_ins}</strong> vehicle(s) are operating with expired insurance policies. "
            f"This is a critical compliance failure under the Motor Vehicles Act (Pakistan), "
            f"UK Road Traffic Act 1988, Saudi Traffic Law, and equivalent US state regulations. "
            f"Immediate renewal is mandatory; these vehicles must be grounded until compliant.",
            f"<strong>{exp_fit}</strong> vehicle(s) have expired fitness/roadworthiness certificates. "
            f"Operating such vehicles may result in prohibition notices, fines, and operator "
            f"licence suspension. Scheduling inspections at approved testing stations is urgent.",
        ],
        "⚖️", "danger" if (exp_ins + exp_fit) > 0 else "good"
    )

    narrative(
        "Fuel Economy & Environmental Performance",
        [
            f"Fleet average fuel efficiency is <strong>{fuel_eff:.2f} km/l</strong> for the period. "
            f"Total fuel expenditure was <strong>{fmt(fuel_c)}</strong> PKR. "
            f"A target of ≥ 12 km/l is typical for mixed-fleet rental operations.",
            f"Vehicles consistently below 8 km/l should be flagged for mechanical inspection "
            f"(possible fuel system faults) and assessed for replacement under fleet renewal policy. "
            f"This also supports GCC Vision 2030 / UK Clean Air Zone compliance objectives.",
        ],
        "⛽", "good" if fuel_eff >= 12 else "warning"
    )

    st.markdown("<hr style='border-color:#1e2f44;margin:14px 0'>", unsafe_allow_html=True)

    sec("📊 Fleet Composition")
    ca7, cb7 = st.columns(2)
    with ca7:
        sc = veh["status"].value_counts().reset_index(); sc.columns=["status","n"]
        cmap_v = {"Available":GREEN,"On Trip":BRAND,"Under Maintenance":ORANGE,
                  "Reserved":AMBER,"Retired":STEEL}
        fig_sv = go.Figure(go.Pie(labels=sc["status"], values=sc["n"], hole=0.52,
                                   marker_colors=[cmap_v.get(s,BRAND) for s in sc["status"]]))
        dark_layout(fig_sv, "Fleet Status Distribution", height=300)
        st.plotly_chart(fig_sv, use_container_width=True)
    with cb7:
        mk = veh["make"].value_counts().reset_index(); mk.columns=["make","n"]
        fig_mk = go.Figure(go.Bar(x=mk["n"], y=mk["make"], orientation="h",
                                   marker_color=COLORS[:len(mk)],
                                   text=mk["n"], textposition="outside"))
        dark_layout(fig_mk, "Vehicles by Make", height=300)
        st.plotly_chart(fig_mk, use_container_width=True)

    if not f_p.empty:
        sec("⛽ Fuel Efficiency by Vehicle")
        ev = (f_p[f_p["fuel_efficiency_kmpl"]>0]
               .groupby("vehicle_id")["fuel_efficiency_kmpl"].mean().reset_index()
               .merge(dfs["vehicles"][["vehicle_id","make","model"]], on="vehicle_id", how="left")
               .sort_values("fuel_efficiency_kmpl"))
        ev["label"] = ev["make"] + " " + ev["model"]
        ev["colour"] = ev["fuel_efficiency_kmpl"].apply(
            lambda x: GREEN if x>=14 else (AMBER if x>=10 else ORANGE))
        fig_ef = go.Figure(go.Bar(x=ev["fuel_efficiency_kmpl"], y=ev["label"],
                                   orientation="h", marker_color=ev["colour"].tolist(),
                                   text=ev["fuel_efficiency_kmpl"].round(1),
                                   textposition="outside"))
        dark_layout(fig_ef, "Avg Fuel Efficiency by Vehicle (km/l)", height=max(280,len(ev)*14))
        st.plotly_chart(fig_ef, use_container_width=True)

    sec("⚠️ Compliance Alerts")
    comp_df = veh[["vehicle_id","make","model","year","status",
                    "insurance_expiry","fitness_cert_expiry","condition_rating"]].copy()
    comp_df["ins_exp"] = pd.to_datetime(comp_df["insurance_expiry"],errors="coerce") < TODAY
    comp_df["fit_exp"] = pd.to_datetime(comp_df["fitness_cert_expiry"],errors="coerce") < TODAY
    alerts = comp_df[(comp_df["ins_exp"])|(comp_df["fit_exp"])].copy()
    if not alerts.empty:
        alerts["Issues"] = alerts.apply(
            lambda r: ("⚠️ Insurance Expired" if r["ins_exp"] else "") +
                      (" | ⚠️ Fitness Expired" if r["fit_exp"] else ""), axis=1)
        st.dataframe(alerts[["vehicle_id","make","model","year","status",
                               "insurance_expiry","fitness_cert_expiry","Issues"]],
                     use_container_width=True, hide_index=True)
    else:
        alert_box("✅ All vehicles compliant — insurance and fitness certificates valid.", "success")

    sec("📋 Full Vehicle Register")
    st.dataframe(veh[["vehicle_id","make","model","year","status","condition_rating",
                        "odometer_km","daily_rate_pkr","telematics_enabled",
                        "insurance_expiry","fitness_cert_expiry"]],
                 use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════════════
#  EXPORT SECTION — PDF (narrative HTML) + Excel + CSV
# ═══════════════════════════════════════════════════════════════════════
st.markdown("<hr style='border-color:#1e2f44;margin:20px 0 10px 0'>", unsafe_allow_html=True)
sec("📥 Export Report")

ts       = start_dt.strftime("%Y%m%d")
rtype_fn = report_label.split(" ",1)[1].strip().replace(" ","_")
per_fn   = period_label.split(" ",1)[1].strip().replace(" ","_")
base     = f"SoftRentaCar_{rtype_fn}_{per_fn}_{ts}"

ec1, ec2, ec3 = st.columns(3)

# ── Excel export ─────────────────────────────────────────────────────
with ec1:
    with st.expander("📊 Excel Workbook", expanded=False):
        buf = io.BytesIO()
        try:
            with pd.ExcelWriter(buf, engine="xlsxwriter") as xl:
                for sname, df_xl in [("Trips",t_p),("Invoices",i_p),
                                      ("Maintenance",m_p),("Telematics",tel_p),
                                      ("Vehicles",veh),("Fuel",f_p)]:
                    if not df_xl.empty:
                        df_xl.to_excel(xl, sheet_name=sname, index=False)
            buf.seek(0)
            st.download_button("⬇️ Download Excel",
                data=buf, file_name=f"{base}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True)
        except Exception as e:
            st.error(f"Excel error: {e}")

# ── CSV export ────────────────────────────────────────────────────────
with ec2:
    with st.expander("📄 CSV Data", expanded=False):
        csv_map = {"executive":(t_p,"trips"),"financial":(i_p,"invoices"),
                   "operational":(t_p,"trips"),"maintenance":(m_p,"maintenance"),
                   "safety":(tel_p,"telematics"),"fleet":(veh,"vehicles")}
        df_csv, tname = csv_map[report_type]
        if not df_csv.empty:
            st.download_button(f"⬇️ Download {tname}.csv",
                data=df_csv.to_csv(index=False).encode("utf-8"),
                file_name=f"{base}_{tname}.csv", mime="text/csv",
                use_container_width=True)
        else:
            st.info("No data to export.")

# ── PDF — full narrative HTML report ─────────────────────────────────
with ec3:
    with st.expander("🖨️ PDF Report (Narrative)", expanded=True):

        def _tbl(df, cols=None, maxr=40):
            if df is None or df.empty:
                return "<p><em>No data for this period.</em></p>"
            d = df[cols].head(maxr) if cols else df.head(maxr)
            hdr = "".join(f"<th>{c}</th>" for c in d.columns)
            rows = "".join(
                "<tr>" + "".join(f"<td>{v}</td>" for v in r) + "</tr>"
                for r in d.values.tolist()
            )
            return f"<table><thead><tr>{hdr}</tr></thead><tbody>{rows}</tbody></table>"

        def _krow(*items):
            cells = "".join(
                f'<div class="kpi"><div class="kval">{v}</div>'
                f'<div class="klbl">{l}</div></div>'
                for v,l in items
            )
            return f'<div class="kpi-row">{cells}</div>'

        # ── build narrative sections per report type ───────────────────
        if report_type == "executive":
            body = f"""
<h2>1. Key Performance Indicators</h2>
{_krow((fmt(billed),"Gross Revenue"),(fmt(collected),"Collected"),
       (f"{col_rate}%","Collection Rate"),(f"{n_trips:,}","Total Bookings"))}
{_krow((f"{n_comp:,}","Completed"),(f"{comp_rate}%","Completion Rate"),
       (f"{avg_ss:.1f}/100","Safety Score"),(f"{util_rate}%","Fleet Utilisation"))}

<h2>2. Management Commentary</h2>
<h3>2.1 Revenue &amp; Collections</h3>
<p>During the period <strong>{start_dt.strftime("%d %B %Y")}</strong> to
<strong>{end_dt.strftime("%d %B %Y")}</strong>, {sel_fleet} generated gross revenue of
<strong>{fmt(billed)}</strong> PKR across <strong>{len(i_p):,}</strong> invoices.
Collections totalled <strong>{fmt(collected)}</strong> PKR, representing a collection rate of
<strong>{col_rate}%</strong> against the 90% industry benchmark.</p>
<p>Outstanding receivables stand at <strong>{fmt(outstanding)}</strong> PKR
({pct(outstanding,billed):.1f}% of gross revenue).
{"Collection performance is satisfactory." if col_rate>=85 else
 "Management should prioritise recovery of overdue balances to preserve cash flow."}</p>

<h3>2.2 Operational Performance</h3>
<p>The fleet recorded <strong>{n_trips:,}</strong> bookings of which
<strong>{n_comp:,} ({comp_rate}%)</strong> were completed successfully.
Cancellations accounted for <strong>{n_canc:,} ({canc_rate}%)</strong>.
The average completed trip generated <strong>{fmt(avg_fare)}</strong> PKR over
<strong>{avg_dist:.0f} km</strong>.</p>

<h3>2.3 Safety &amp; Compliance</h3>
<p>Fleet-wide average safety score: <strong>{avg_ss:.1f}/100</strong>.
{"Score meets the ≥70 benchmark." if avg_ss>=70 else
 "Score is BELOW the minimum threshold of 70. Immediate corrective action is required."}
<strong>{n_danger}</strong> driver(s) classified as dangerous/poor require
mandatory intervention.</p>

<h3>2.4 Cost Management</h3>
<p>Combined fuel and maintenance costs totalled
<strong>{fmt(fuel_cost+maint_cost)}</strong> PKR.
Fleet utilisation is <strong>{util_rate}%</strong>
({"within" if util_rate>=60 else "below"} the 60–80% target range).</p>

<h2>3. Booking Mix</h2>
{_tbl(tc_p.groupby("booking_type").agg(
    trips=("trip_id","count"),revenue=("trip_fare_pkr","sum")).reset_index()
    .assign(revenue=lambda d:d["trip_fare_pkr"].apply(fmt)
            if "trip_fare_pkr" in d.columns else d["revenue"].apply(fmt))
    if not tc_p.empty else pd.DataFrame())}

<h2>4. Top 10 Customers</h2>
{_tbl(tc_p.merge(dfs["customers"][["customer_id","full_name","customer_type"]],
                  on="customer_id",how="left")
          .groupby(["full_name","customer_type"])["trip_fare_pkr"].sum()
          .reset_index().sort_values("trip_fare_pkr",ascending=False).head(10)
          .assign(**{"Revenue PKR":lambda d:d["trip_fare_pkr"].apply(fmt)})
          [["full_name","customer_type","Revenue PKR"]]
      if not tc_p.empty else pd.DataFrame(),
      cols=["full_name","customer_type","Revenue PKR"])}"""

        elif report_type == "financial":
            body = f"""
<h2>1. Financial Summary</h2>
{_krow((fmt(billed),"Gross Revenue"),(fmt(collected),"Collected"),
       (fmt(outstanding),"Outstanding"),(f"{col_rate}%","Collection Rate"))}
{_krow((fmt(surcharge),"Surcharges"),(fmt(discount),"Discounts"),
       (fmt(tax),"Tax Collected"),(fmt(net_margin),"Est. Net Margin"))}

<h2>2. Management Commentary</h2>
<h3>2.1 Income Statement Overview</h3>
<p>Gross revenue for the period is <strong>{fmt(billed)}</strong> PKR.
After discounts of <strong>{fmt(discount)}</strong> PKR ({disc_pct:.1f}% of gross),
net revenue is <strong>{fmt(billed-discount)}</strong> PKR.
Direct operating costs (fuel + maintenance) total
<strong>{fmt(fuel_cost+maint_cost)}</strong> PKR.
Estimated operating margin: <strong>{margin_pct:.1f}%</strong>
(Benchmark: 18–25% per ICAP / GCC fleet standards).</p>

<h3>2.2 Receivables &amp; Credit Risk (IFRS 9 / GAAP ASC 310)</h3>
<p>Outstanding receivables of <strong>{fmt(outstanding)}</strong> PKR represent
{pct(outstanding,billed):.1f}% of gross billings.
{"Collection rate is within acceptable range." if col_rate>=85 else
 "Collection rate is below 85% threshold — credit terms review recommended."}</p>

<h3>2.3 Tax &amp; Regulatory Compliance</h3>
<p>Tax collected: <strong>{fmt(tax)}</strong> PKR. Timely remittance to FBR (Pakistan),
HMRC (UK), ZATCA (KSA), or IRS (US) is required.</p>

<h2>3. AR Aging Schedule</h2>
{_tbl(unpaid[["invoice_id","due_date","outstanding_pkr","payment_status","Aging"]]
      .sort_values("outstanding_pkr",ascending=False).head(30)
      if not unpaid.empty else pd.DataFrame())}

<h2>4. Payment Method Distribution</h2>
{_tbl(i_p["payment_method"].value_counts().reset_index().rename(
    columns={"payment_method":"Method","count":"Invoices"})
    if not i_p.empty else pd.DataFrame())}"""

        elif report_type == "operational":
            body = f"""
<h2>1. Operational Summary</h2>
{_krow((f"{n_tot:,}","Total Bookings"),(f"{n_comp:,}","Completed"),
       (f"{comp_r}%","Completion Rate"),(f"{n_canc:,}","Cancelled"))}
{_krow((fmt(rev),"Trip Revenue"),(f"{avg_d:.0f} km","Avg Distance"),
       (f"{avg_dur:.2f} days","Avg Duration"),(fmt(avg_f),"Avg Fare"))}

<h2>2. Management Commentary</h2>
<h3>2.1 Service Delivery</h3>
<p>The fleet processed <strong>{n_tot:,}</strong> bookings with a completion rate of
<strong>{comp_r}%</strong>
({"above" if comp_r>=85 else "below"} the 85% industry benchmark per BVRLA / ARA standards).
Revenue from completed trips: <strong>{fmt(rev)}</strong> PKR.</p>
<h3>2.2 Cancellation &amp; Revenue Leakage</h3>
<p><strong>{n_canc}</strong> bookings ({canc_r}%) cancelled; <strong>{n_ns}</strong> no-shows.
Leading reason: <em>{top_canc}</em>.
{"Cancellation rate is within acceptable range." if canc_r<=10 else
 "Cancellation rate exceeds 10% — advance deposit policy recommended."}</p>

<h2>3. Top Routes</h2>
{_tbl(tc_p.groupby(["pickup_city","dropoff_city"])["trip_id"].count()
          .reset_index().rename(columns={"trip_id":"trips"})
          .sort_values("trips",ascending=False).head(15)
          .assign(route=lambda d:d["pickup_city"]+" → "+d["dropoff_city"])
          [["route","trips"]] if not tc_p.empty else pd.DataFrame())}

<h2>4. Trip Records</h2>
{_tbl(t_p,cols=["trip_id","booking_type","pickup_city","dropoff_city",
                 "pickup_datetime","distance_km","trip_fare_pkr","status"])}"""

        elif report_type == "maintenance":
            body = f"""
<h2>1. Maintenance Summary</h2>
{_krow((fmt(tc),"Total Cost"),(fmt(pc),"Parts Cost"),
       (fmt(lc),"Labour Cost"),(f"{ns}","Events"))}
{_krow((f"{overdue}","Overdue"),(f"{due_30}","Due in 30 Days"),
       (f"{in_maint}","In Maintenance"),(f"{pct(pc,tc):.0f}%","Parts Ratio"))}

<h2>2. Management Commentary</h2>
<h3>2.1 Fleet Maintenance Overview</h3>
<p><strong>{ns}</strong> maintenance events recorded; total cost
<strong>{fmt(tc)}</strong> PKR. Most frequent type: <strong>{top_type}</strong>.
Parts-to-labour ratio: <strong>{parts_pct:.0f}:{100-parts_pct:.0f}</strong>
(benchmark 55:45 per ATA TMC / Fleet News UK).</p>
<h3>2.2 Regulatory Compliance</h3>
<p><strong>{overdue}</strong> vehicle(s) overdue for service — operating these vehicles
violates DVSA OCRS (UK), DOT FMCSA (US), and Saudi Traffic Law Article 49.
<strong>{due_30}</strong> vehicle(s) due within 30 days require scheduling.</p>

<h2>3. Cost by Type</h2>
{_tbl(m_p.groupby("maintenance_type").agg(
    events=("maint_id","count"),
    total_cost=("total_cost_pkr","sum"))
    .reset_index().sort_values("total_cost",ascending=False)
    if not m_p.empty else pd.DataFrame())}

<h2>4. Service Records</h2>
{_tbl(m_p,cols=["maint_id","vehicle_id","maintenance_type",
                 "maintenance_date","total_cost_pkr","status"])}"""

        elif report_type == "safety":
            body = f"""
<h2>1. Safety Summary</h2>
{_krow((f"{avg_ss:.1f}/100","Safety Score"),(f"{n_acc}","Accidents"),
       (f"{n_cpl}","Complaints"),(f"{avg_rt:.2f}/5","Avg Rating"))}
{_krow((f"{n_hb:,}","Harsh Brakes"),(f"{n_ha:,}","Harsh Accels"),
       (f"{n_danger}","Dangerous Drivers"),(f"{n_poor}","Poor Drivers"))}

<h2>2. Management Commentary</h2>
<h3>2.1 Safety Score Assessment</h3>
<p>Average safety score: <strong>{avg_ss:.1f}/100</strong> — graded
<strong>{ss_grade}</strong>.
Benchmarked against IAM RoadSmart Fleet Standard, UK DVSA duty-of-care,
OSHA 29 CFR 1910, and KSA General Traffic Department requirements.</p>
<h3>2.2 Incidents &amp; Regulatory Obligations</h3>
<p><strong>{n_acc}</strong> accident(s) ({acc_r}% of monitored trips).
Mandatory reporting: UK Road Traffic Act 1988 s.170, NHTSA, Saudi Traffic Law Art.71.
Customer complaints: <strong>{n_cpl}</strong>. Average rating: <strong>{avg_rt:.2f}/5</strong>.</p>
<h3>2.3 High-Risk Driver Action Plan</h3>
<p><strong>{n_danger+n_poor}</strong> driver(s) classified poor/dangerous.
Recommended: (1) Suspension pending assessment, (2) Defensive driving programme
(IAM, RoSPA, or equivalent), (3) Telematics probation, (4) Insurance notification.</p>

<h2>3. Driver Safety Leaderboard</h2>
{_tbl(dl.head(20) if "dl" in dir() and not dl.empty else pd.DataFrame(),
      cols=["full_name","behavior_profile","trips","avg_score",
            "accidents","complaints","avg_rating"]
      if "dl" in dir() and not dl.empty else None)}"""

        else:  # fleet
            body = f"""
<h2>1. Fleet Summary</h2>
{_krow((f"{n_tot}","Total Vehicles"),(f"{n_avail}","Available"),
       (f"{n_trip}","On Trip"),(f"{util_r}%","Utilisation"))}
{_krow((f"{exp_ins}","Expired Insurance"),(f"{exp_fit}","Expired Fitness"),
       (f"{avg_odo:,.0f} km","Avg Odometer"),(f"{fuel_eff:.2f} kmpl","Fuel Efficiency"))}

<h2>2. Management Commentary</h2>
<h3>2.1 Utilisation &amp; Availability</h3>
<p>Active fleet: <strong>{n_tot - n_retd}</strong> vehicles ({n_retd} retired).
Utilisation: <strong>{util_r}%</strong>
({"within" if util_r>=65 else "below"} the 65–80% BVRLA benchmark).</p>
<h3>2.2 Compliance — Insurance &amp; Roadworthiness</h3>
<p><strong>{exp_ins}</strong> vehicle(s) with expired insurance — must be grounded immediately.
<strong>{exp_fit}</strong> vehicle(s) with expired fitness certificates require urgent inspection
under Motor Vehicles Act (Pakistan), UK Road Traffic Act 1988,
Saudi Traffic Law, and US state DMV regulations.</p>
<h3>2.3 Fuel Economy</h3>
<p>Average efficiency: <strong>{fuel_eff:.2f} km/l</strong>.
Total fuel spend: <strong>{fmt(fuel_c)}</strong> PKR.
{"Within acceptable range." if fuel_eff>=12 else
 "Below 12 km/l target — inspect underperforming vehicles for fuel system issues."}</p>

<h2>3. Compliance Alerts</h2>
{_tbl(alerts[["vehicle_id","make","model","year","status",
              "insurance_expiry","fitness_cert_expiry","Issues"]]
      if "alerts" in dir() and not alerts.empty else pd.DataFrame())}

<h2>4. Vehicle Register</h2>
{_tbl(veh,cols=["vehicle_id","make","model","year","status",
                 "condition_rating","odometer_km","daily_rate_pkr",
                 "insurance_expiry","fitness_cert_expiry"])}"""

        # ── Assemble full HTML document ────────────────────────────────
        html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{report_label} — Soft Rent a Car</title>
<style>
  @page {{
    size: A4; margin: 20mm 18mm 22mm;
    @top-left {{ content: "CONFIDENTIAL — Soft Rent a Car"; font-size:7pt; color:#888; }}
    @bottom-center {{ content: "Page " counter(page) " of " counter(pages); font-size:8pt; }}
  }}
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{ font-family:"Segoe UI",Arial,sans-serif; font-size:9.5pt;
          color:#1a1a2e; background:white; line-height:1.55; }}

  /* ── Report header ── */
  .rpt-cover {{
    background:linear-gradient(135deg,#1D3557,#0a1525);
    color:white; padding:22px 26px 18px; border-radius:6px; margin-bottom:22px;
  }}
  .rpt-cover h1 {{ font-size:20pt; color:#E63946; margin-bottom:6px; }}
  .rpt-cover .sub {{ font-size:9pt; color:#a0bbd0; }}
  .divider {{ border:none; border-top:2px solid #E63946;
              margin:16px 0; page-break-after:avoid; }}

  /* ── Section headings ── */
  h2 {{ font-size:12pt; font-weight:700; color:#1D3557;
        border-left:4px solid #E63946; padding-left:8px;
        margin:22px 0 10px; page-break-after:avoid; }}
  h3 {{ font-size:10.5pt; font-weight:600; color:#2c3e50; margin:14px 0 6px; }}
  p  {{ margin-bottom:8px; font-size:9.5pt; }}
  strong {{ color:#1D3557; }}
  em {{ color:#457B9D; font-style:normal; font-weight:600; }}

  /* ── KPI row ── */
  .kpi-row {{ display:flex; gap:10px; margin:10px 0 18px; flex-wrap:wrap; }}
  .kpi {{ background:#f0f5fb; border-left:4px solid #E63946;
          border-radius:0 6px 6px 0; padding:9px 14px;
          flex:1; min-width:110px; page-break-inside:avoid; }}
  .kval {{ font-size:13pt; font-weight:700; color:#1D3557; }}
  .klbl {{ font-size:7.5pt; color:#5a7a96; margin-top:3px; text-transform:uppercase;
           letter-spacing:.05em; }}

  /* ── Tables ── */
  table {{ border-collapse:collapse; width:100%; font-size:8pt;
           margin:8px 0 16px; page-break-inside:auto; }}
  thead {{ background:#1D3557; color:white; }}
  th {{ padding:6px 8px; text-align:left; font-weight:600;
        border:1px solid #2d4a6b; white-space:nowrap; }}
  td {{ padding:5px 7px; border:1px solid #d0dce8; vertical-align:top; }}
  tbody tr:nth-child(even) {{ background:#f7fafc; }}
  tbody tr:hover {{ background:#eef4fb; }}

  /* ── Narrative box ── */
  .commentary {{ background:#f0f5fb; border-left:4px solid #3b82f6;
                 border-radius:0 6px 6px 0; padding:12px 16px;
                 margin:10px 0 16px; page-break-inside:avoid; }}
  .commentary.warn {{ border-color:#d97706; background:#fffbf0; }}
  .commentary.danger {{ border-color:#dc2626; background:#fff5f5; }}
  .commentary.good {{ border-color:#16a34a; background:#f0fdf4; }}

  /* ── Footer ── */
  .report-footer {{
    margin-top:28px; padding-top:10px;
    border-top:2px solid #E63946;
    font-size:7.5pt; color:#5a7a96;
    display:flex; justify-content:space-between;
  }}
</style>
</head>
<body>

<div class="rpt-cover">
  <h1>{report_label}</h1>
  <div class="sub">
    <strong style="color:white;">{sel_fleet}</strong> &nbsp;|&nbsp;
    Period: {period_label} &nbsp;|&nbsp;
    {start_dt.strftime("%d %B %Y")} — {end_dt.strftime("%d %B %Y")}
    &nbsp;|&nbsp; {period_days:,} day(s)
  </div>
  <div style="margin-top:10px;font-size:8pt;color:#7a9ab0;">
    Generated: {TODAY.strftime("%d %B %Y")} &nbsp;|&nbsp;
    Prepared by: Muhammad Siddique &nbsp;|&nbsp;
    Soft Rent a Car — Fleet Intelligence Platform &nbsp;|&nbsp;
    <strong style="color:#a0bbd0;">CONFIDENTIAL</strong>
  </div>
</div>

{body}

<div class="report-footer">
  <div>Soft Rent a Car · Fleet Intelligence Platform · datawithms.top</div>
  <div>Muhammad Siddique · +92 322 9948042 · siddique.dea@gmail.com</div>
  <div>CONFIDENTIAL — For Internal Use Only</div>
</div>

</body>
</html>"""

        html_bytes = html_doc.encode("utf-8")
        st.download_button(
            "⬇️ Download PDF Report (HTML → Print as PDF)",
            data=html_bytes,
            file_name=f"{base}_Report.html",
            mime="text/html",
            use_container_width=True,
        )
        st.caption(
            "💡 **How to create PDF:** Open the downloaded file in Chrome/Edge → "
            "press **Ctrl+P** (or ⌘+P) → set Destination to **Save as PDF** → "
            "enable **Background graphics** → click **Save**. "
            "Result: a fully formatted, paginated, professional PDF report."
        )

        # show inline preview toggle
        if st.checkbox("👁️ Preview report in browser", key="rpt_preview"):
            import base64
            b64 = base64.b64encode(html_bytes).decode()
            st.markdown(
                f'<iframe src="data:text/html;base64,{b64}" '
                f'width="100%" height="700px" style="border:1px solid #2d4a6b;'
                f'border-radius:8px;"></iframe>',
                unsafe_allow_html=True
            )


# ══════════════════════════════════════════════════════════════════════
#  AI SECTION — Enhanced Narrative + Custom Report Generator
# ══════════════════════════════════════════════════════════════════════
st.markdown("<hr style='border-color:#1e2f44;margin:24px 0 16px 0'>", unsafe_allow_html=True)
st.markdown(f"""
<div style="display:flex;align-items:center;gap:10px;margin-bottom:4px;">
  <span style="font-size:1.6rem;">🤖</span>
  <div>
    <div style="font-size:1.1rem;font-weight:800;color:{BRAND};">AI Report Intelligence</div>
    <div style="font-size:.76rem;color:#5a7a96;">
      GPT-4o powered · Enhanced narrative · Custom report generator · Export to PDF
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── resolve key ────────────────────────────────────────────────────────
from app.ai_chat import _resolve_key
_ai_key = _resolve_key()

if not _ai_key:
    st.markdown(f"""
<div style="background:rgba(230,57,70,.08);border:1px solid {BRAND}44;
            border-radius:10px;padding:12px 16px;margin:8px 0 14px;">
  <div style="font-size:.82rem;color:{TEXT};">
    🔑 <strong>OpenAI API key required</strong> for AI features.<br>
    <span style="color:#5a7a96;font-size:.75rem;">
      Add it in <strong>⚙️ Settings &amp; API Keys</strong> or enter it below.
    </span>
  </div>
</div>""", unsafe_allow_html=True)
    tmp_key = st.text_input("Enter OpenAI API key to enable AI features",
                             type="password", placeholder="sk-...",
                             key="rpt_tmp_key", label_visibility="collapsed")
    if tmp_key and len(tmp_key) > 20:
        import os; os.environ["OPENAI_API_KEY"] = tmp_key
        _ai_key = tmp_key

_ai_available = bool(_ai_key)

badge_html = (
    '<span style="background:linear-gradient(90deg,#10a37f,#1a7f5a);color:#fff;'
    'font-size:.62rem;font-weight:700;padding:2px 8px;border-radius:12px;'
    'letter-spacing:.05em;">✦ GPT-4o ACTIVE</span>'
    if _ai_available else
    '<span style="background:rgba(90,122,150,.2);color:#8eaac4;'
    'font-size:.62rem;font-weight:600;padding:2px 8px;border-radius:12px;'
    'border:1px solid #2d4a6b;">⚡ NO KEY — AI DISABLED</span>'
)
st.markdown(badge_html, unsafe_allow_html=True)

# ── shared GPT caller ──────────────────────────────────────────────────
def _call_gpt(system_prompt: str, user_prompt: str,
              max_tokens: int = 2000, temperature: float = 0.4) -> str:
    """Call GPT-4o and return the text response."""
    try:
        import openai
        client = openai.OpenAI(api_key=_ai_key)
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system",  "content": system_prompt},
                {"role": "user",    "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ GPT error: {e}"


# ── build fleet context snapshot for AI ────────────────────────────────
def _build_context() -> str:
    """Compact but rich data snapshot passed to every AI call."""
    lines = [
        f"REPORT: {report_label}",
        f"PERIOD: {start_dt.strftime('%d %b %Y')} to {end_dt.strftime('%d %b %Y')} ({period_days} days)",
        f"FLEET: {sel_fleet}",
        "",
        "=== PERIOD DATA SUMMARY ===",
    ]

    # trips
    if not t_p.empty:
        n_t = len(t_p)
        n_c = int((t_p["status"] == "Completed").sum())
        n_x = int((t_p["status"] == "Cancelled").sum())
        avg_f = tc_p["trip_fare_pkr"].mean() if not tc_p.empty else 0
        lines += [
            f"Trips: {n_t:,} total | {n_c:,} completed ({n_c/max(n_t,1)*100:.1f}%) "
            f"| {n_x:,} cancelled ({n_x/max(n_t,1)*100:.1f}%)",
            f"Avg fare: PKR {avg_f:,.0f} | Avg distance: "
            f"{tc_p['distance_km'].mean() if not tc_p.empty else 0:.0f} km",
        ]
        top_city = (tc_p.groupby("pickup_city")["trip_fare_pkr"].sum()
                    .idxmax() if not tc_p.empty else "N/A")
        top_type = (tc_p.groupby("booking_type")["trip_fare_pkr"].sum()
                    .idxmax() if not tc_p.empty else "N/A")
        lines += [f"Top city: {top_city} | Top booking type: {top_type}"]

    # invoices
    if not i_p.empty:
        billed_c = i_p["total_amount_pkr"].sum()
        coll_c   = i_p["paid_amount_pkr"].sum()
        outs_c   = i_p["outstanding_pkr"].sum()
        lines += [
            f"Revenue: PKR {billed_c/1e6:.2f}M billed | "
            f"PKR {coll_c/1e6:.2f}M collected ({coll_c/max(billed_c,1)*100:.1f}%)",
            f"Outstanding: PKR {outs_c/1e6:.2f}M",
        ]

    # fuel
    if not f_p.empty:
        lines += [
            f"Fuel: PKR {f_p['fuel_cost_pkr'].sum()/1e3:,.0f}K total | "
            f"Avg {f_p[f_p['fuel_efficiency_kmpl']>0]['fuel_efficiency_kmpl'].mean():.1f} km/l efficiency",
        ]

    # maintenance
    if not m_p.empty:
        lines += [f"Maintenance: PKR {m_p['total_cost_pkr'].sum()/1e3:,.0f}K | "
                  f"{len(m_p)} service events"]

    # telematics
    if not tel_p.empty:
        avg_ss = tel_p["safety_score"].mean()
        n_acc  = int(tel_p["accident_occurred"].astype(int).sum())
        lines += [
            f"Safety: avg score {avg_ss:.1f}/100 | {n_acc} accidents | "
            f"{int(tel_p['complaint_filed'].astype(int).sum())} complaints",
        ]

    # fleet / vehicles
    n_avail = int((veh["status"] == "Available").sum())
    n_trip  = int((veh["status"] == "On Trip").sum())
    n_maint = int((veh["status"] == "Under Maintenance").sum())
    ins_exp = int((pd.to_datetime(veh["insurance_expiry"], errors="coerce") < TODAY).sum())
    lines += [
        f"Fleet: {len(veh)} vehicles | {n_avail} available | "
        f"{n_trip} on trip | {n_maint} in maintenance | {ins_exp} expired insurance",
    ]

    # drivers
    n_danger = int(drv["behavior_profile"].isin(["dangerous", "poor"]).sum())
    lines += [f"Drivers: {len(drv)} total | {n_danger} poor/dangerous profile"]

    return "\n".join(lines)


_SYS = """You are a senior fleet management analyst writing professional business reports for
Soft Rent a Car — a Pakistani vehicle rental company operating 4 fleets with 120 vehicles.
Write in English. Be specific, data-driven, and authoritative.
Reference international standards where relevant (IFRS, GAAP, DVSA, IAM, Saudi Traffic Law, BVRLA, ATA).
Use markdown: **bold** for numbers, *italic* for assessments, ## for sections, ### for sub-sections.
Never invent numbers not provided. Be concise but thorough. Avoid filler phrases."""


# ══════════════════════════════════════════════════════════════════════
#  TAB 1 — AI-ENHANCED NARRATIVE for current report
# ══════════════════════════════════════════════════════════════════════
st.markdown("<br>", unsafe_allow_html=True)
tab_enhance, tab_custom = st.tabs(
    ["🔬  AI-Enhanced Report Narrative", "✍️  Custom AI Report Generator"]
)

with tab_enhance:
    st.markdown(f"""
<div style="font-size:.82rem;color:#5a7a96;margin-bottom:12px;">
  GPT-4o reads your <strong>{report_label}</strong> data snapshot and writes a deeper,
  contextual narrative — management commentary, risk flags, benchmarks, and recommendations
  beyond what the static report shows.
</div>""", unsafe_allow_html=True)

    enhance_btn = st.button(
        f"🚀  Generate AI-Enhanced Narrative for {report_label}",
        type="primary", key="ai_enhance_btn",
        disabled=not _ai_available
    )

    if not _ai_available:
        st.info("Add an OpenAI API key above to enable this feature.")
    elif enhance_btn or "ai_enhanced_text" in st.session_state:
        if enhance_btn:
            ctx = _build_context()
            with st.spinner("GPT-4o is analysing your fleet data and writing the report…"):
                _prompt = f"""
You have been given a data snapshot for a {report_label}.
Write a comprehensive, professional management narrative with these sections:

## Executive Summary
One paragraph summarising the period's performance.

## Key Findings
Bullet points of the 5–7 most significant observations from the data.

## Detailed Analysis
Sub-sections for each relevant area (revenue, operations, safety, costs, fleet).
For each section: state the metric, benchmark it against industry standards, and explain the implication.

## Risk Assessment
A table: | Risk | Severity | Likelihood | Recommended Action |

## Strategic Recommendations
Numbered list of 5–7 specific, actionable recommendations with expected impact.

## Outlook
One paragraph on what to watch for in the next period.

DATA SNAPSHOT:
{ctx}
"""
                result = _call_gpt(_SYS, _prompt, max_tokens=2500, temperature=0.35)
            st.session_state.ai_enhanced_text = result

        if "ai_enhanced_text" in st.session_state:
            result = st.session_state.ai_enhanced_text
            st.markdown(f"""
<div style="background:linear-gradient(135deg,#0f1e2e,#121c2a);
            border:1px solid #1e3a55;border-radius:12px;
            padding:20px 24px;margin:10px 0;">
  <div style="font-size:.68rem;font-weight:700;color:#10a37f;
              text-transform:uppercase;letter-spacing:.08em;margin-bottom:12px;">
    ✦ GPT-4o ENHANCED NARRATIVE
  </div>
  <div style="font-size:.87rem;line-height:1.75;color:{TEXT};">
  {result.replace(chr(10), '<br>').replace('**', '<strong>').replace('##', '<br><strong style=&quot;font-size:.95rem;color:{BRAND};&quot;>').replace('###', '<br><strong style=&quot;font-size:.88rem;color:{STEEL};&quot;>')}
  </div>
</div>""", unsafe_allow_html=True)

            # raw markdown view
            with st.expander("📄 View raw markdown (for copy-paste into Word/Google Docs)"):
                st.code(result, language="markdown")

            # export enhanced narrative as HTML
            enh_html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<title>AI-Enhanced {report_label}</title>
<style>
  body{{font-family:'Segoe UI',Arial,sans-serif;max-width:860px;margin:40px auto;
        color:#1a1a2e;font-size:10.5pt;line-height:1.65;}}
  h1{{color:#E63946;font-size:20pt;border-bottom:3px solid #E63946;padding-bottom:8px;}}
  h2{{color:#1D3557;font-size:13pt;border-left:4px solid #E63946;padding-left:8px;margin-top:20px;}}
  h3{{color:#457B9D;font-size:11pt;margin-top:14px;}}
  strong{{color:#1D3557;}}
  table{{border-collapse:collapse;width:100%;margin:10px 0;font-size:9pt;}}
  th{{background:#1D3557;color:white;padding:6px 10px;text-align:left;}}
  td{{border:1px solid #ccc;padding:5px 10px;}}
  tr:nth-child(even){{background:#f5f8fc;}}
  .footer{{border-top:2px solid #E63946;margin-top:30px;padding-top:10px;
           font-size:8pt;color:#777;display:flex;justify-content:space-between;}}
</style></head><body>
<h1>AI-Enhanced {report_label}</h1>
<p style="color:#666;font-size:9pt;">
  {sel_fleet} &nbsp;|&nbsp; {period_label} &nbsp;|&nbsp;
  {start_dt.strftime('%d %b %Y')} — {end_dt.strftime('%d %b %Y')} &nbsp;|&nbsp;
  Generated by GPT-4o on {TODAY.strftime('%d %B %Y')}
</p>
<hr style="border-color:#E63946;">
{result.replace(chr(10),'<br>').replace('## ','<h2>').replace('### ','<h3>').replace('**','<strong>').replace('*','<em>')}
<div class="footer">
  <span>Soft Rent a Car · Fleet Intelligence Platform</span>
  <span>Muhammad Siddique · datawithms.top</span>
  <span>CONFIDENTIAL</span>
</div>
</body></html>"""

            st.download_button(
                "⬇️ Download AI-Enhanced Report (HTML → PDF)",
                data=enh_html.encode("utf-8"),
                file_name=f"{base}_AI_Enhanced.html",
                mime="text/html",
                use_container_width=True,
                key="dl_enhanced"
            )

        if st.button("🔄 Regenerate", key="regen_btn", disabled=not _ai_available):
            if "ai_enhanced_text" in st.session_state:
                del st.session_state["ai_enhanced_text"]
            st.rerun()


# ══════════════════════════════════════════════════════════════════════
#  TAB 2 — CUSTOM AI REPORT GENERATOR
# ══════════════════════════════════════════════════════════════════════
with tab_custom:
    st.markdown(f"""
<div style="font-size:.82rem;color:#5a7a96;margin-bottom:10px;">
  Describe any report you need in plain English. GPT-4o will generate a full,
  professional report using your fleet data — no predefined templates required.
</div>""", unsafe_allow_html=True)

    # Example prompts
    EXAMPLES = [
        "Write a board-level quarterly performance report comparing Q3 vs Q2 2026",
        "Generate a driver risk assessment report highlighting who needs immediate intervention",
        "Create a fuel economy analysis report with cost-saving recommendations",
        "Write a fleet renewal and retirement plan based on vehicle age and maintenance costs",
        "Produce a customer segmentation report showing which customer types generate the most revenue",
        "Write a cash flow and collections health report for the CFO",
        "Generate a compliance status report covering insurance, fitness certs, and driver licences",
        "Create a city-wise demand analysis report for marketing and fleet deployment",
        "Write an operational efficiency report comparing self-drive vs chauffeur-driven performance",
        "Generate a maintenance budget forecast report based on historical spending patterns",
    ]

    st.markdown('<div style="font-size:.72rem;color:#8eaac4;margin-bottom:6px;">💡 Example prompts — click to use:</div>',
                unsafe_allow_html=True)
    ex_cols = st.columns(2)
    for i, ex in enumerate(EXAMPLES):
        if ex_cols[i % 2].button(f"📋 {ex[:55]}…" if len(ex) > 55 else f"📋 {ex}",
                                  key=f"ex_{i}", use_container_width=True):
            st.session_state.custom_rpt_prompt = ex

    st.markdown("<br>", unsafe_allow_html=True)

    custom_prompt = st.text_area(
        "✍️  Describe your report",
        value=st.session_state.get("custom_rpt_prompt", ""),
        height=100,
        placeholder=(
            "e.g. Write a comprehensive quarterly performance report for Q3 2026 "
            "covering revenue, operations, safety, and fleet health with executive "
            "commentary and strategic recommendations..."
        ),
        key="custom_rpt_input",
    )

    # Options row
    oc1, oc2, oc3 = st.columns(3)
    rpt_depth   = oc1.selectbox("Report depth",
                                 ["Concise (1 page)", "Standard (2–3 pages)", "Comprehensive (4–5 pages)"],
                                 index=1, key="ai_depth")
    rpt_audience= oc2.selectbox("Audience",
                                 ["Board / C-Suite", "Operations Manager", "Finance Team",
                                  "Fleet Manager", "HR / Safety Officer"],
                                 index=0, key="ai_audience")
    rpt_tone    = oc3.selectbox("Tone",
                                 ["Formal / Corporate", "Analytical / Technical", "Concise / Bullet-focused"],
                                 index=0, key="ai_tone")

    depth_map = {
        "Concise (1 page)":       (800,  "Be concise. 1 page equivalent."),
        "Standard (2–3 pages)":   (2000, "Standard depth. 2-3 pages equivalent."),
        "Comprehensive (4–5 pages)":(3500,"Be thorough. 4-5 pages equivalent. Include all sub-sections."),
    }
    max_tok, depth_instr = depth_map[rpt_depth]

    gen_custom_btn = st.button(
        "🚀  Generate Custom AI Report",
        type="primary", key="ai_custom_btn",
        disabled=not _ai_available or not custom_prompt.strip()
    )

    if not _ai_available:
        st.info("Add an OpenAI API key above to enable this feature.")
    elif not custom_prompt.strip():
        st.info("Enter a report description above to generate.")
    elif gen_custom_btn or "ai_custom_result" in st.session_state:

        if gen_custom_btn:
            ctx = _build_context()
            sys_custom = f"""{_SYS}

AUDIENCE: {rpt_audience}
TONE: {rpt_tone}
{depth_instr}

Always include:
- An executive summary paragraph
- Key metrics with industry benchmarks
- Management commentary with specific data points
- Risk flags where applicable
- Actionable recommendations
- A professional closing statement

Format with clear ## section headers and ### sub-headers.
Use **bold** for important numbers and metrics.
"""
            user_custom = f"""USER REQUEST: {custom_prompt}

FLEET DATA SNAPSHOT:
{ctx}

Generate the complete report now. Do not include any preamble — start directly with the report content."""

            with st.spinner("GPT-4o is generating your custom report…"):
                custom_result = _call_gpt(sys_custom, user_custom,
                                          max_tokens=max_tok, temperature=0.38)
            st.session_state.ai_custom_result   = custom_result
            st.session_state.ai_custom_prompt   = custom_prompt
            st.session_state.ai_custom_audience = rpt_audience
            st.session_state.ai_custom_depth    = rpt_depth

        if "ai_custom_result" in st.session_state:
            custom_result   = st.session_state.ai_custom_result
            saved_prompt    = st.session_state.get("ai_custom_prompt", custom_prompt)
            saved_audience  = st.session_state.get("ai_custom_audience", rpt_audience)

            st.success(f"✅ Custom report generated for: *{saved_audience}*")

            st.markdown(f"""
<div style="background:linear-gradient(135deg,#0a1a14,#0f2018);
            border:1px solid #1a4a2a;border-radius:12px;
            padding:20px 24px;margin:12px 0;">
  <div style="font-size:.68rem;font-weight:700;color:#10a37f;
              text-transform:uppercase;letter-spacing:.08em;margin-bottom:4px;">
    ✦ GPT-4o CUSTOM REPORT
  </div>
  <div style="font-size:.72rem;color:#5a7a96;margin-bottom:12px;">
    Prompt: <em>"{saved_prompt[:120]}{'…' if len(saved_prompt)>120 else ''}"</em>
  </div>
</div>""", unsafe_allow_html=True)

            # render the markdown nicely
            import re as _re
            rendered = custom_result
            # h3 before h2 to avoid double-replacing
            rendered = _re.sub(r"^### (.+)$",
                r'<h3 style="color:#457B9D;font-size:.9rem;font-weight:700;'
                r'margin:14px 0 4px;border-bottom:1px solid #1e3044;padding-bottom:3px;">\1</h3>',
                rendered, flags=_re.MULTILINE)
            rendered = _re.sub(r"^## (.+)$",
                r'<h2 style="color:#E63946;font-size:1rem;font-weight:800;'
                r'margin:18px 0 6px;border-left:4px solid #E63946;padding-left:8px;">\1</h2>',
                rendered, flags=_re.MULTILINE)
            rendered = _re.sub(r"^# (.+)$",
                r'<h1 style="color:#E63946;font-size:1.15rem;font-weight:800;'
                r'margin:10px 0 8px;">\1</h1>',
                rendered, flags=_re.MULTILINE)
            rendered = _re.sub(r"\*\*(.+?)\*\*",
                r'<strong style="color:#c8dff0;">\1</strong>', rendered)
            rendered = _re.sub(r"\*(.+?)\*",
                r'<em style="color:#8eaac4;">\1</em>', rendered)
            rendered = _re.sub(r"^- (.+)$",
                r'<li style="margin:3px 0;color:#c8dff0;">\1</li>',
                rendered, flags=_re.MULTILINE)
            rendered = rendered.replace("\n\n", '<br><br>').replace("\n", "<br>")

            st.markdown(f"""
<div style="background:linear-gradient(135deg,#0f1e2e,#111c2a);
            border:1px solid #1e3044;border-radius:12px;
            padding:20px 26px;margin:0 0 14px;">
  <div style="font-size:.87rem;line-height:1.8;color:{TEXT};">
    {rendered}
  </div>
</div>""", unsafe_allow_html=True)

            with st.expander("📄 View raw markdown"):
                st.code(custom_result, language="markdown")

            # ── export ─────────────────────────────────────────────────
            cust_base = saved_prompt[:40].strip().replace(" ", "_").replace("/", "-")
            cust_html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<title>Custom Report — {saved_prompt[:60]}</title>
<style>
  body{{font-family:'Segoe UI',Arial,sans-serif;max-width:860px;margin:40px auto;
        color:#1a1a2e;font-size:10.5pt;line-height:1.7;}}
  h1{{color:#E63946;font-size:18pt;border-bottom:3px solid #E63946;padding-bottom:6px;}}
  h2{{color:#1D3557;font-size:13pt;border-left:4px solid #E63946;padding-left:8px;margin-top:22px;}}
  h3{{color:#457B9D;font-size:11pt;margin-top:16px;}}
  strong{{color:#1D3557;}}
  table{{border-collapse:collapse;width:100%;margin:10px 0;font-size:9pt;}}
  th{{background:#1D3557;color:white;padding:7px 10px;text-align:left;}}
  td{{border:1px solid #ccc;padding:5px 10px;}}
  tr:nth-child(even){{background:#f5f8fc;}}
  li{{margin:4px 0;}}
  .meta{{font-size:9pt;color:#666;margin-bottom:12px;}}
  .footer{{border-top:2px solid #E63946;margin-top:32px;padding-top:10px;
           font-size:8pt;color:#777;display:flex;justify-content:space-between;}}
</style></head><body>
<h1>Custom AI Report</h1>
<div class="meta">
  <strong>Prompt:</strong> {saved_prompt}<br>
  <strong>Audience:</strong> {saved_audience} &nbsp;|&nbsp;
  <strong>Fleet:</strong> {sel_fleet} &nbsp;|&nbsp;
  <strong>Period:</strong> {start_dt.strftime('%d %b %Y')} — {end_dt.strftime('%d %b %Y')} &nbsp;|&nbsp;
  <strong>Generated:</strong> {TODAY.strftime('%d %B %Y')} by GPT-4o
</div>
<hr style="border-color:#E63946;">
{custom_result.replace(chr(10),'<br>').replace('## ','<h2>').replace('### ','<h3>').replace('**','<strong>').replace('*','<em>')}
<div class="footer">
  <span>Soft Rent a Car · Fleet Intelligence Platform</span>
  <span>Muhammad Siddique · datawithms.top</span>
  <span>CONFIDENTIAL</span>
</div>
</body></html>"""

            dc1, dc2 = st.columns(2)
            dc1.download_button(
                "⬇️ Download Report (HTML → PDF)",
                data=cust_html.encode("utf-8"),
                file_name=f"CustomReport_{cust_base}_{ts}.html",
                mime="text/html",
                use_container_width=True,
                key="dl_custom_html",
            )
            dc2.download_button(
                "⬇️ Download Raw Markdown",
                data=custom_result.encode("utf-8"),
                file_name=f"CustomReport_{cust_base}_{ts}.md",
                mime="text/markdown",
                use_container_width=True,
                key="dl_custom_md",
            )

        if st.button("🔄 New Report", key="clear_custom"):
            for k in ["ai_custom_result", "ai_custom_prompt",
                      "ai_custom_audience", "ai_custom_depth", "custom_rpt_prompt"]:
                st.session_state.pop(k, None)
            st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

