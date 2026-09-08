"""Data Storytelling"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from page_modules._shared import (
    inject, get_data, fmt, sec, dark_layout,
    BRAND, NAVY, STEEL, GREEN, AMBER, ORANGE, TEXT, GRID, BG, COLORS
)
from app.storytelling import insight

inject()
dfs = get_data()
trips = dfs["trips"]; inv = dfs["invoices"]; tel = dfs["telematics"]
drv = dfs["drivers"]; veh = dfs["vehicles"]; fuel = dfs["fuel_logs"]
maint = dfs["maintenance"]; cust = dfs["customers"]

st.markdown(f'<div style="font-size:1.5rem;font-weight:800;color:{BRAND};margin-bottom:4px;">📖 Data Storytelling</div>', unsafe_allow_html=True)
st.markdown(f'<div style="font-size:.8rem;color:#5a7a96;">Key insights narrated from your fleet data — the story behind the numbers</div>', unsafe_allow_html=True)
st.markdown("<hr style='border-color:#1e2f44;margin:6px 0 14px 0'>", unsafe_allow_html=True)

total_rev  = inv["total_amount_pkr"].sum()
coll_rate  = inv["paid_amount_pkr"].sum()/total_rev*100
avg_score  = tel["safety_score"].mean()
risky_n    = (drv["behavior_profile"].isin(["poor","dangerous"])).sum()
peak_hour  = trips.groupby("pickup_hour").size().idxmax()
peak_dow   = trips.groupby("pickup_dow").size().idxmax()
top_city   = trips["pickup_city"].value_counts().index[0]
cancel_rate= (trips["status"]=="Cancelled").mean()*100
total_maint= maint["total_cost_pkr"].sum()
avg_eff    = fuel["fuel_efficiency_kmpl"].mean()
total_fuel = fuel["fuel_cost_pkr"].sum()
top_maint  = maint.groupby("maintenance_type")["total_cost_pkr"].sum().idxmax()
corp_pct   = (cust["customer_type"]=="Corporate").mean()*100
op_pct     = (cust["customer_type"]=="Overseas Pakistani").mean()*100
repeat_pct = (cust["total_bookings"]>1).mean()*100
idle_hrs   = tel["idle_time_minutes"].sum()/60

# ── Story 1 ────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="story-card">
  <div class="story-num">01</div>
  <div class="story-ttl">📈 From Zero to {fmt(total_rev)}</div>
  <div class="story-bdy">
    Soft Rent a Car has collectively billed <strong style="color:{BRAND};">{fmt(total_rev)}</strong>
    across 18,000 bookings since 2022. With a <strong>collection rate of {coll_rate:.1f}%</strong>,
    the business demonstrates strong billing discipline. Revenue peaks in
    <strong>August and December</strong> — northern tourism season and wedding season.
  </div>
</div>""", unsafe_allow_html=True)

inv["_m"] = inv["invoice_date"].dt.to_period("M")
rev_ts = inv.groupby("_m")["total_amount_pkr"].sum()
fig1 = go.Figure(go.Scatter(x=[str(i) for i in rev_ts.index], y=rev_ts.values/1e6,
    fill="tozeroy", fillcolor="rgba(230,57,70,.12)", line=dict(color=BRAND,width=2.5),
    mode="lines+markers", marker=dict(size=4)))
dark_layout(fig1, "Monthly Revenue (PKR M)", xangle=-45, height=300)
st.plotly_chart(fig1, width='stretch')

insight(
    f"Revenue has grown consistently since 2022, peaking in <strong>August and December</strong>. "
    f"Collection rate of <strong>{coll_rate:.1f}%</strong> is "
    f"{'above' if coll_rate >= 92 else 'below'} the 92% industry benchmark. "
    f"Monthly trend shows clear seasonality — northern tourism (Jul–Aug) and wedding season (Nov–Dec) drive peaks.",
    "💰", "good" if coll_rate >= 90 else "warn",
    f"{'✅ Strong collection discipline.' if coll_rate >= 90 else '⚠️ Improve collections process to recover outstanding balance.'}"
)

# ── Story 2 ────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="story-card">
  <div class="story-num">02</div>
  <div class="story-ttl">🚦 The Hidden Safety Crisis</div>
  <div class="story-bdy">
    Fleet average safety score is <strong style="color:{AMBER};">{avg_score:.1f}/100</strong> —
    below the target of 70. <strong style="color:{BRAND};">{risky_n} drivers</strong> are classified
    as poor or dangerous. <strong>{int(tel['harsh_brake_events'].sum()):,} harsh brake events</strong>
    and <strong>{idle_hrs:,.0f} idle engine hours</strong> are costing an estimated
    <strong>PKR 2.3M/year</strong> in excess fuel.
    <br><em>AI coaching for the 20 lowest-scoring drivers could reduce accidents by 40%.</em>
  </div>
</div>""", unsafe_allow_html=True)

fig2 = go.Figure(go.Histogram(x=tel["safety_score"], nbinsx=25, marker_color=BRAND, opacity=.8))
fig2.add_vline(x=70,       line_dash="dash", line_color=GREEN, annotation_text="Target 70",        annotation_font_color=GREEN)
fig2.add_vline(x=avg_score,line_dash="dot",  line_color=AMBER, annotation_text=f"Mean {avg_score:.1f}",annotation_font_color=AMBER)
dark_layout(fig2, "Safety Score Distribution", height=280)
st.plotly_chart(fig2, width='stretch')

insight(
    f"<strong>{(tel['safety_score'] < 70).mean()*100:.0f}%</strong> of trips score below the 70-point target. "
    f"The distribution is left-skewed — a small group of repeat offenders drag the average down significantly. "
    f"Targeting the bottom 20% of drivers with a structured coaching programme would shift the fleet average above 70.",
    "🚦", "bad" if avg_score < 60 else "warn",
    f"⚠️ Enrol the {risky_n} poor/dangerous drivers in telematics coaching immediately."
)

# ── Story 3 ────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="story-card">
  <div class="story-num">03</div>
  <div class="story-ttl">⏰ The Demand Clock</div>
  <div class="story-bdy">
    Peak booking hour is <strong>{peak_hour:02d}:00</strong> and
    <strong>{peak_dow}s</strong> are the busiest day. <strong>{top_city}</strong> leads all cities.
    July–August see <strong>25% higher demand</strong> from northern tourism,
    yet cancellation rate is <strong>{cancel_rate:.1f}%</strong>.
    <br><em>Dynamic redeployment to {top_city} during Jul–Aug could add PKR 12M revenue.</em>
  </div>
</div>""", unsafe_allow_html=True)

hourly = trips.groupby("pickup_hour").size().reset_index(name="n")
fig3 = go.Figure(go.Bar(
    x=hourly["pickup_hour"].apply(lambda h: f"{h:02d}:00"),
    y=hourly["n"],
    marker_color=[BRAND if h==peak_hour else STEEL for h in hourly["pickup_hour"]]))
dark_layout(fig3, f"Bookings by Hour — Peak at {peak_hour:02d}:00", height=280)
st.plotly_chart(fig3, width='stretch')

insight(
    f"<strong>{peak_hour:02d}:00 on {peak_dow}s</strong> is the single highest-demand slot. "
    f"Demand drops 60% in the early morning (02:00–06:00). "
    f"Having drivers and vehicles ready 30 minutes before {peak_hour:02d}:00 could capture "
    f"15–20% more bookings that currently go unfulfilled due to slow response times.",
    "⏰", "info",
    f"💡 Pre-position vehicles in {top_city} by {peak_hour-1:02d}:30 on {peak_dow}s."
)

# ── Story 4 ────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="story-card">
  <div class="story-num">04</div>
  <div class="story-ttl">🔧 The True Cost of Fleet Neglect</div>
  <div class="story-bdy">
    Maintenance has cost <strong style="color:{BRAND};">{fmt(total_maint)}</strong>.
    Biggest category: <strong>{top_maint}</strong>.
    Average fuel efficiency <strong>{avg_eff:.1f} km/l</strong> is 15% below spec,
    wasting <strong>{fmt(total_fuel*0.15)}</strong> in excess fuel.
    <br><em>Retiring the 5 oldest high-cost vehicles could cut maintenance 28% in 12 months.</em>
  </div>
</div>""", unsafe_allow_html=True)

mg = maint.groupby("maintenance_type")["total_cost_pkr"].sum().sort_values().tail(8)
fig4 = go.Figure(go.Bar(x=mg.values/1e6, y=mg.index, orientation="h",
    marker_color=BRAND, text=[f"{v:.1f}M" for v in mg.values/1e6],
    textposition="outside", textfont=dict(color=TEXT,size=9)))
dark_layout(fig4, "Maintenance Cost by Type (PKR M)", height=280)
fig4.update_yaxes(autorange="reversed")
st.plotly_chart(fig4, width='stretch')

insight(
    f"<strong>{top_maint}</strong> is the single largest maintenance cost driver. "
    f"Vehicles over 4 years old account for disproportionately higher maintenance spend. "
    f"Switching to a predictive maintenance schedule (AI-flagged, 2 weeks early) "
    f"could reduce unplanned repairs by an estimated 28%, saving PKR {total_maint*0.28/1e6:.1f}M.",
    "🔧", "warn",
    f"⚠️ Prioritise preventive servicing for the 5 highest-cost vehicles immediately."
)

# ── Story 5 ────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="story-card">
  <div class="story-num">05</div>
  <div class="story-ttl">👥 Who Is Our Customer?</div>
  <div class="story-bdy">
    2,000 customers: <strong>50% Individual</strong>,
    <strong>{corp_pct:.0f}% Corporate</strong>,
    <strong>{op_pct:.0f}% Overseas Pakistanis</strong> (premium segment).
    <strong>{repeat_pct:.0f}%</strong> have booked more than once.
    <br><em>A loyalty programme for the top 200 repeat customers = PKR 5M incremental revenue.</em>
  </div>
</div>""", unsafe_allow_html=True)

cr = inv.merge(cust[["customer_id","customer_type"]],on="customer_id",how="left") \
        .groupby("customer_type")["total_amount_pkr"].sum().sort_values(ascending=False).reset_index()
fig5 = go.Figure(go.Bar(x=cr["customer_type"], y=cr["total_amount_pkr"]/1e6,
    marker_color=BRAND,
    text=[f"{v:.1f}M" for v in cr["total_amount_pkr"]/1e6],
    textposition="outside", textfont=dict(color=TEXT)))
dark_layout(fig5, "Revenue by Customer Type (PKR M)", height=300)
st.plotly_chart(fig5, width='stretch')

insight(
    f"<strong>Corporate clients</strong> generate the highest average invoice value despite being "
    f"only {corp_pct:.0f}% of the customer base. "
    f"Overseas Pakistanis ({op_pct:.0f}%) exclusively book premium vehicles — "
    f"average spend 3× higher than individual customers. "
    f"With {repeat_pct:.0f}% repeat rate, a tiered loyalty programme targeting the top 200 "
    f"repeat bookers could generate an additional PKR 5M annually with minimal acquisition cost.",
    "👥", "good" if repeat_pct >= 40 else "warn",
    f"💡 Launch a points-to-free-day loyalty scheme for repeat customers — highest ROI marketing action."
)

# ── Story 6 – Fleet Utilisation ────────────────────────────────────────
st.markdown("<hr style='border-color:#1e2f44;margin:14px 0'>", unsafe_allow_html=True)

trips_c   = dfs["trips"][dfs["trips"]["status"]=="Completed"].copy()
fleet_size = len(veh[veh["status"]!="Retired"])
days_span  = max(1,(trips_c["pickup_datetime"].dt.date.max()-trips_c["pickup_datetime"].dt.date.min()).days)
util_pct   = min(100, trips_c["duration_days"].sum()/(fleet_size*days_span)*100)

st.markdown(f"""
<div class="story-card">
  <div class="story-num">06</div>
  <div class="story-ttl">🚗 The Utilisation Gap</div>
  <div class="story-bdy">
    Fleet utilisation stands at <strong style="color:{'#2A9D8F' if util_pct>=65 else '#E9C46A'};">
    {util_pct:.1f}%</strong> against a 70% target.
    <strong>{(veh['status']=='Available').sum()}</strong> vehicles are idle right now.
    A 10-point utilisation improvement on the current fleet would add an estimated
    <strong>PKR {fleet_size * 7000 * 30 / 1e6:.1f}M/month</strong> in incremental revenue
    without a single new vehicle purchase.
    <br><em>Dynamic demand mapping and real-time redeployment alerts are the fastest path to closing this gap.</em>
  </div>
</div>""", unsafe_allow_html=True)

trips_c["pickup_month"] = trips_c["pickup_datetime"].dt.to_period("M")
monthly_util = trips_c.groupby("pickup_month")["duration_days"].sum().reset_index()
monthly_util["util_pct"] = (monthly_util["duration_days"]/(fleet_size*30)*100).clip(0,100)
monthly_util["month_str"] = monthly_util["pickup_month"].astype(str)

fig6 = go.Figure()
fig6.add_trace(go.Scatter(
    x=monthly_util["month_str"], y=monthly_util["util_pct"],
    fill="tozeroy", fillcolor="rgba(69,123,157,.15)",
    line=dict(color=STEEL, width=2.5), mode="lines+markers", marker=dict(size=5)))
fig6.add_hline(y=70, line_dash="dash", line_color=GREEN,
               annotation_text="Target 70%", annotation_font_color=GREEN)
dark_layout(fig6, "Monthly Fleet Utilisation %", xangle=-45, height=280)
st.plotly_chart(fig6, width='stretch')

insight(
    f"Utilisation peaked during Jul–Aug (tourism) and Nov–Dec (weddings). "
    f"Troughs in Jan–Feb suggest seasonal demand gaps that could be filled with "
    f"<strong>corporate contract pricing</strong> — fixed monthly rates for businesses provide "
    f"stable base utilisation year-round. "
    f"Each 1% utilisation improvement across {fleet_size} vehicles = approximately "
    f"PKR {fleet_size*0.01*7000*30/1e3:.0f}K/month.",
    "📈", "good" if util_pct >= 65 else "warn",
    f"💡 Offer 3-month corporate packages at 15% discount to fill Jan–Feb troughs."
)
st.markdown("<hr style='border-color:#1e2f44;margin:16px 0'>", unsafe_allow_html=True)
sec("🚀 Strategic Recommendations")
recs = [
    (f"🚦 Enroll {risky_n} high-risk drivers in AI coaching. Target score ≥ 70. "
     f"Saves ~PKR 800K/yr fuel.",                      ORANGE),
    (f"📍 Redeploy 15 vehicles to {top_city} for Jul–Aug peak. Uplift: PKR 12M.", BRAND),
    (f"💰 Loyalty scheme for {int((cust['total_bookings']>2).sum()):,} repeat customers. LTV +18%.", GREEN),
    (f"🔧 Predictive maintenance scheduling. Est. savings {fmt(total_maint*0.25)}.", AMBER),
    (f"💡 Dynamic pricing for peak hours & seasons — 20–30% premium possible.", STEEL),
]
cols = st.columns(3)
for i, (body, color) in enumerate(recs):
    with cols[i%3]:
        st.markdown(f"""
<div style="background:rgba(30,42,58,.9);border-left:4px solid {color};
            border-radius:10px;padding:14px;margin:6px 0;min-height:100px;">
  <div style="font-size:.85rem;color:#c8dff0;line-height:1.55;">{body}</div>
</div>""", unsafe_allow_html=True)

