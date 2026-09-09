"""
Contextual Storytelling Engine — Soft Rent a Car
Generates data-driven insight captions rendered above/below every chart.
"""

import pandas as pd
import streamlit as st


# ── Renderer ───────────────────────────────────────────────────────────

def insight(
    text: str,
    icon: str = "💡",
    level: str = "info",   # info | good | warn | bad
    sub: str = "",
):
    """
    Renders a styled insight card below a chart.
    level: info=blue  good=green  warn=amber  bad=red
    """
    colors = {
        "info": ("#457B9D", "rgba(69,123,157,.12)"),
        "good": ("#2A9D8F", "rgba(42,157,143,.12)"),
        "warn": ("#E9C46A", "rgba(233,196,106,.12)"),
        "bad":  ("#E76F51", "rgba(231,111,81,.12)"),
    }
    border, bg = colors.get(level, colors["info"])
    sub_html = (
        f'<div style="font-size:.72rem;color:{border};opacity:.8;margin-top:3px;">{sub}</div>'
        if sub else ""
    )
    st.markdown(f"""
<div style="background:{bg};border-left:3px solid {border};border-radius:0 8px 8px 0;
            padding:9px 14px;margin:4px 0 14px;display:flex;align-items:flex-start;gap:8px;">
  <span style="font-size:1.1rem;line-height:1.4;flex-shrink:0;">{icon}</span>
  <div>
    <div style="font-size:.82rem;color:#c8dff0;line-height:1.55;">{text}</div>
    {sub_html}
  </div>
</div>
""", unsafe_allow_html=True)


def chart_header(title: str, description: str, icon: str = "📊"):
    """Renders a section header with a descriptive subtitle above a chart."""
    st.markdown(f"""
<div style="margin:18px 0 6px;">
  <div style="font-size:1rem;font-weight:700;color:#c8dff0;
              border-left:3px solid #E63946;padding-left:10px;">
    {icon} {title}
  </div>
  <div style="font-size:.78rem;color:#5a7a96;margin-top:3px;padding-left:13px;">
    {description}
  </div>
</div>
""", unsafe_allow_html=True)


def story_block(number: str, title: str, body: str, accent: str = "#E63946"):
    """Renders a numbered story card (used on storytelling page)."""
    st.markdown(f"""
<div style="background:linear-gradient(135deg,#1a2840,#1e2f44);border-radius:14px;
            border:1px solid #2a3f58;padding:20px 24px;margin:10px 0;">
  <div style="font-size:2.6rem;font-weight:800;color:{accent};line-height:1;">{number}</div>
  <div style="font-size:1rem;font-weight:700;color:#b8d4e8;margin-top:4px;">{title}</div>
  <div style="font-size:.86rem;color:#7a9ab4;margin-top:8px;line-height:1.6;">{body}</div>
</div>
""", unsafe_allow_html=True)


# ── Data-driven insight generators ────────────────────────────────────

def revenue_insight(inv: pd.DataFrame) -> tuple:
    total   = inv["total_amount_pkr"].sum()
    coll    = inv["paid_amount_pkr"].sum()
    rate    = coll / total * 100 if total else 0
    outs    = total - coll

    # Monthly trend
    inv["_m"] = inv["invoice_date"].dt.to_period("M")
    monthly   = inv.groupby("_m")["total_amount_pkr"].sum().sort_index()
    growth    = (monthly.iloc[-1] - monthly.iloc[-2]) / monthly.iloc[-2] * 100 if len(monthly) > 1 else 0
    peak_m    = str(monthly.idxmax())
    slow_m    = str(monthly.idxmin())

    level = "good" if rate >= 92 else ("warn" if rate >= 80 else "bad")
    text  = (
        f"Fleet has billed <strong>PKR {total/1e6:.1f}M</strong> with a "
        f"<strong>{rate:.1f}% collection rate</strong>. "
        f"Last month grew <strong>{growth:+.1f}%</strong> MoM. "
        f"Peak revenue was <strong>{peak_m}</strong>; slowest was <strong>{slow_m}</strong>. "
        f"Outstanding balance of <strong>PKR {outs/1e6:.1f}M</strong> needs follow-up."
    )
    sub = (
        "✅ Excellent collection rate — above 92% target."
        if rate >= 92 else
        f"⚠️ Collection rate {rate:.1f}% is below the 92% target — PKR {outs/1e6:.1f}M at risk."
    )
    return text, sub, level


def trips_insight(trips: pd.DataFrame) -> tuple:
    total  = len(trips)
    comp   = (trips["status"] == "Completed").sum()
    canc   = (trips["status"] == "Cancelled").sum()
    cr     = canc / total * 100 if total else 0
    top_bt = trips.groupby("booking_type").size().idxmax()
    top_ci = trips.groupby("pickup_city").size().idxmax()
    avg_km = trips[trips["status"]=="Completed"]["distance_km"].mean()

    level = "good" if cr < 8 else ("warn" if cr < 15 else "bad")
    text  = (
        f"<strong>{comp:,} of {total:,}</strong> bookings completed "
        f"({100-cr:.1f}% success rate). "
        f"Cancellation rate is <strong>{cr:.1f}%</strong> — "
        f"most common booking type is <strong>{top_bt}</strong>, "
        f"busiest city is <strong>{top_ci}</strong>. "
        f"Average trip distance: <strong>{avg_km:.0f} km</strong>."
    )
    sub = (
        f"✅ Cancellation rate {cr:.1f}% is healthy (< 8%)."
        if cr < 8 else
        f"⚠️ Cancellation rate {cr:.1f}% is elevated — investigate supply gaps in {top_ci}."
    )
    return text, sub, level


def driver_safety_insight(tel: pd.DataFrame, drv: pd.DataFrame) -> tuple:
    avg_score = tel["safety_score"].mean()
    accidents = int(tel["accident_occurred"].sum())
    risky     = drv["behavior_profile"].isin(["poor","dangerous"]).sum()
    idle_hrs  = tel["idle_time_minutes"].sum() / 60
    harsh_b   = tel["harsh_brake_events"].sum()

    level = "good" if avg_score >= 70 else ("warn" if avg_score >= 55 else "bad")
    text  = (
        f"Fleet average safety score is <strong>{avg_score:.1f}/100</strong> "
        f"(target ≥ 70). "
        f"<strong>{accidents}</strong> accidents recorded; "
        f"<strong>{risky}</strong> drivers flagged as high-risk. "
        f"Total idle engine time: <strong>{idle_hrs:,.0f} hours</strong> — "
        f"costing an estimated <strong>PKR {idle_hrs*0.5*260/1e3:.0f}K</strong> in wasted fuel. "
        f"<strong>{int(harsh_b):,}</strong> harsh braking events recorded fleet-wide."
    )
    sub = (
        f"✅ Safety score above target."
        if avg_score >= 70 else
        f"⚠️ Score {avg_score:.1f} is below 70 — enrol {risky} high-risk drivers in coaching."
    )
    return text, sub, level


def fleet_utilisation_insight(trips: pd.DataFrame, vehicles: pd.DataFrame) -> tuple:
    comp       = trips[trips["status"] == "Completed"]
    fleet_size = len(vehicles[vehicles["status"] != "Retired"])
    days       = max(1,(trips["pickup_datetime"].dt.date.max()-trips["pickup_datetime"].dt.date.min()).days)
    util       = min(100, comp["duration_days"].sum() / (fleet_size * days) * 100)
    on_trip    = (vehicles["status"] == "On Trip").sum()
    avail      = (vehicles["status"] == "Available").sum()
    maint      = (vehicles["status"] == "Under Maintenance").sum()

    level = "good" if util >= 65 else ("warn" if util >= 45 else "bad")
    text  = (
        f"Fleet utilisation stands at <strong>{util:.1f}%</strong> across "
        f"<strong>{fleet_size}</strong> active vehicles. "
        f"Currently <strong>{on_trip}</strong> on trip, "
        f"<strong>{avail}</strong> available, "
        f"<strong>{maint}</strong> under maintenance. "
        f"Target utilisation is <strong>70%</strong> for optimal revenue per asset."
    )
    sub = (
        f"✅ Utilisation {util:.1f}% near target."
        if util >= 65 else
        f"⚠️ Utilisation {util:.1f}% below 65% — consider demand redeployment."
    )
    return text, sub, level


def fuel_insight(fuel: pd.DataFrame) -> tuple:
    avg_eff   = fuel["fuel_efficiency_kmpl"].mean()
    total_cost= fuel["fuel_cost_pkr"].sum()
    waste_est = total_cost * 0.12   # ~12% wasted via idle/aggressive driving

    # Trend
    fuel["_m"] = fuel["fill_date"].dt.to_period("M")
    monthly    = fuel.groupby("_m")["fuel_efficiency_kmpl"].mean().sort_index()
    trend      = "improving" if monthly.iloc[-1] > monthly.iloc[-3] else "declining"

    level = "good" if avg_eff >= 12 else ("warn" if avg_eff >= 9 else "bad")
    text  = (
        f"Fleet average fuel efficiency is <strong>{avg_eff:.1f} km/l</strong>. "
        f"Total fuel expenditure: <strong>PKR {total_cost/1e6:.1f}M</strong>. "
        f"Efficiency trend is <strong>{trend}</strong> over the last 3 months. "
        f"Estimated waste from idle and aggressive driving: "
        f"<strong>PKR {waste_est/1e3:.0f}K</strong> — "
        f"recoverable through driver coaching."
    )
    sub = (
        f"✅ Efficiency {avg_eff:.1f} km/l is acceptable."
        if avg_eff >= 12 else
        f"⚠️ Efficiency {avg_eff:.1f} km/l is below 12 km/l target — check high-idle drivers."
    )
    return text, sub, level


def maintenance_insight(maint: pd.DataFrame) -> tuple:
    total_cost = maint["total_cost_pkr"].sum()
    top_type   = maint.groupby("maintenance_type")["total_cost_pkr"].sum().idxmax()
    scheduled  = (maint["status"] == "Scheduled").sum()
    avg_cost   = maint["total_cost_pkr"].mean()

    level = "warn" if scheduled > 5 else "good"
    text  = (
        f"Total maintenance spend: <strong>PKR {total_cost/1e6:.1f}M</strong> across "
        f"<strong>{len(maint):,}</strong> service records. "
        f"Highest cost category: <strong>{top_type}</strong>. "
        f"Average service cost: <strong>PKR {avg_cost:,.0f}</strong>. "
        f"<strong>{scheduled}</strong> jobs scheduled but not yet completed."
    )
    sub = (
        f"⚠️ {scheduled} pending jobs — schedule immediately to avoid breakdowns."
        if scheduled > 5 else
        f"✅ Maintenance backlog is manageable ({scheduled} pending)."
    )
    return text, sub, level


def city_demand_insight(trips: pd.DataFrame) -> tuple:
    comp     = trips[trips["status"] == "Completed"]
    top_city = comp.groupby("pickup_city").size().idxmax()
    top_rev  = comp.groupby("pickup_city")["revenue_pkr"].sum().idxmax()
    n_cities = comp["pickup_city"].nunique()
    isb_pct  = (comp["pickup_city"]=="Islamabad").mean() * 100
    top_n    = comp.groupby("pickup_city").size().nlargest(3).index.tolist()

    text = (
        f"Demand spans <strong>{n_cities}</strong> cities. "
        f"<strong>{top_city}</strong> leads by trip volume; "
        f"<strong>{top_rev}</strong> generates the highest revenue. "
        f"Top 3 cities: <strong>{', '.join(top_n)}</strong> account for the majority of bookings. "
        f"Islamabad contributes <strong>{isb_pct:.1f}%</strong> of all trips."
    )
    sub = f"💡 Consider adding vehicles in {top_city} — highest unmet demand city."
    return text, sub, "info"


def route_insight(trips: pd.DataFrame) -> tuple:
    ic = trips[
        (trips["status"] == "Completed") &
        (trips["pickup_city"] != trips["dropoff_city"])
    ]
    if len(ic) == 0:
        return "No intercity trips found.", "", "info"

    top_route = (
        ic.groupby(["pickup_city","dropoff_city"])
        .size().idxmax()
    )
    top_rev_route = (
        ic.groupby(["pickup_city","dropoff_city"])["revenue_pkr"]
        .sum().idxmax()
    )
    avg_km = ic["distance_km"].mean()
    pct_ic = len(ic) / len(trips) * 100

    text = (
        f"Intercity trips account for <strong>{pct_ic:.1f}%</strong> of all completed bookings. "
        f"Busiest route: <strong>{top_route[0]} → {top_route[1]}</strong>. "
        f"Highest revenue route: <strong>{top_rev_route[0]} → {top_rev_route[1]}</strong>. "
        f"Average intercity distance: <strong>{avg_km:.0f} km</strong>."
    )
    sub = f"💡 The {top_route[0]}→{top_route[1]} corridor is the top intercity opportunity."
    return text, sub, "info"


def customer_insight(customers: pd.DataFrame, invoices: pd.DataFrame) -> tuple:
    total      = len(customers)
    corp_pct   = (customers["customer_type"]=="Corporate").mean()*100
    op_pct     = (customers["customer_type"]=="Overseas Pakistani").mean()*100
    repeat_pct = (customers["total_bookings"] > 1).mean()*100
    top_city   = customers["city"].value_counts().index[0]
    avg_spend  = invoices["total_amount_pkr"].sum() / total

    text = (
        f"<strong>{total:,}</strong> customers served. "
        f"Corporate clients: <strong>{corp_pct:.0f}%</strong>; "
        f"Overseas Pakistanis: <strong>{op_pct:.0f}%</strong> (premium segment). "
        f"<strong>{repeat_pct:.0f}%</strong> have booked more than once. "
        f"Top customer city: <strong>{top_city}</strong>. "
        f"Average lifetime spend per customer: <strong>PKR {avg_spend:,.0f}</strong>."
    )
    sub = (
        f"💡 {repeat_pct:.0f}% repeat rate is strong — a loyalty programme could add 15–20% more retention."
    )
    return text, sub, "good" if repeat_pct >= 40 else "warn"


def forecast_insight(hist: pd.Series, fc: pd.Series) -> tuple:
    last_hist = hist.iloc[-1]
    first_fc  = fc.iloc[0]
    last_fc   = fc.iloc[-1]
    growth    = (last_fc - last_hist) / last_hist * 100 if last_hist else 0
    peak_m    = str(fc.idxmax())

    text = (
        f"Revenue forecast projects <strong>PKR {first_fc/1e6:.1f}M</strong> next month, "
        f"reaching <strong>PKR {last_fc/1e6:.1f}M</strong> by end of forecast period "
        f"({growth:+.1f}% vs current). "
        f"Peak forecasted month: <strong>{peak_m}</strong>. "
        f"Forecast uses Exponential Smoothing with trend and seasonality components."
    )
    sub = (
        f"📈 Positive growth trajectory — ensure fleet capacity for peak month {peak_m}."
        if growth > 0 else
        f"⚠️ Declining revenue forecast — review pricing and demand generation strategy."
    )
    level = "good" if growth > 0 else "warn"
    return text, sub, level


def kpi_insight(util: float, col_rate: float, cancel_rate: float, safety: float) -> tuple:
    issues = []
    if util < 65:      issues.append(f"utilisation at {util:.1f}% (target 70%)")
    if col_rate < 90:  issues.append(f"collection rate {col_rate:.1f}% (target 92%)")
    if cancel_rate > 10: issues.append(f"cancellation rate {cancel_rate:.1f}% (target <8%)")
    if safety < 70:    issues.append(f"safety score {safety:.1f}/100 (target 70)")

    if not issues:
        text  = "All KPIs are within target ranges. Fleet is performing optimally."
        sub   = "✅ No KPI flags — excellent overall performance."
        level = "good"
    else:
        text  = (
            f"<strong>{len(issues)} KPI(s) need attention:</strong> "
            + "; ".join(issues) + ". "
            "Focus on driver coaching and demand redeployment to address gaps."
        )
        sub   = f"⚠️ Address {len(issues)} underperforming metrics for improved profitability."
        level = "warn" if len(issues) <= 2 else "bad"
    return text, sub, level
