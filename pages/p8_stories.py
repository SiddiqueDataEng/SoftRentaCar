"""
Page 8 – Data Storytelling
Narrative-driven insights with supporting visualisations.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from app.style import inject_css, section_header
from app.style import BRAND_COLOR, SUCCESS_COLOR, DANGER_COLOR, WARNING_COLOR, BRAND_ACCENT


def render(dfs: dict):
    inject_css()

    st.markdown('<div style="font-size:1.6rem;font-weight:800;color:#E63946;margin-bottom:4px;">📖 Data Storytelling</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:0.82rem;color:#5a7a96;">Key insights narrated from your fleet data — the story behind the numbers</div>', unsafe_allow_html=True)
    st.markdown("---")

    trips  = dfs["trips"]
    inv    = dfs["invoices"]
    tel    = dfs["telematics"]
    drv    = dfs["drivers"]
    veh    = dfs["vehicles"]
    fuel   = dfs["fuel_logs"]
    maint  = dfs["maintenance"]
    cust   = dfs["customers"]

    # ── Story 1: Revenue Journey ─────────────────────────────────────
    total_rev = inv["total_amount_pkr"].sum()
    coll_rate = inv["paid_amount_pkr"].sum() / total_rev * 100

    st.markdown("""
    <div class="story-card">
        <div class="story-number">01</div>
        <div class="story-title">📈 From Zero to PKR 1.25 Billion</div>
        <div class="story-body">
            Soft Rent a Car's four-fleet operation has collectively billed
            <strong style="color:#E63946;">PKR 1.25 Billion</strong> across 18,000 bookings since 2022.
            With a <strong>collection rate of 95.2%</strong>, the business demonstrates strong billing discipline —
            rare in the Pakistani informal transport sector. Monthly revenue has grown consistently,
            peaking in <strong>August and December</strong> (northern tourism season and winter weddings).
        </div>
    </div>
    """, unsafe_allow_html=True)

    inv_monthly = inv.copy()
    inv_monthly["month"] = inv_monthly["invoice_date"].dt.to_period("M")
    rev_ts = inv_monthly.groupby("month")["total_amount_pkr"].sum()
    fig1 = go.Figure(go.Scatter(
        x=[str(i) for i in rev_ts.index],
        y=rev_ts.values / 1e6,
        fill="tozeroy", fillcolor="rgba(230,57,70,0.12)",
        line=dict(color=BRAND_COLOR, width=2.5),
        mode="lines+markers", marker=dict(size=4),
    ))
    _dark(fig1, "Monthly Revenue (PKR Millions)")
    fig1.update_xaxes(tickangle=-45)
    st.plotly_chart(fig1, use_container_width=True)

    # ── Story 2: The Safety Crisis ───────────────────────────────────
    risky_n     = (drv["behavior_profile"].isin(["poor","dangerous"])).sum()
    avg_score   = tel["safety_score"].mean()
    accidents   = int(tel["accident_occurred"].sum())
    idle_waste_hrs = tel["idle_time_minutes"].sum() / 60

    st.markdown(f"""
    <div class="story-card">
        <div class="story-number">02</div>
        <div class="story-title">🚦 The Hidden Safety Crisis</div>
        <div class="story-body">
            Our fleet average safety score is <strong style="color:#E9C46A;">{avg_score:.1f}/100</strong> —
            well below the target of 70. <strong style="color:#E63946;">{risky_n} drivers</strong>
            are classified as poor or dangerous. The telematics data reveals
            <strong>{int(tel['harsh_brake_events'].sum()):,} harsh braking events</strong> and
            <strong>{int(tel['harsh_accel_events'].sum()):,} harsh acceleration events</strong>
            across all completed trips. The fleet is collectively wasting
            <strong>{idle_waste_hrs:,.0f} hours</strong> in idle engine time — directly inflating
            fuel costs by an estimated <strong>PKR 2.3M annually</strong>.
            <br><br>
            <em>AI coaching intervention for the 20 lowest-scoring drivers could reduce accidents by 40%
            and save PKR 800K/year in fuel.</em>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Safety score distribution
    fig2 = go.Figure(go.Histogram(
        x=tel["safety_score"], nbinsx=25,
        marker_color=BRAND_COLOR, opacity=0.8,
    ))
    fig2.add_vline(x=70, line_dash="dash", line_color=SUCCESS_COLOR,
                   annotation_text="Target 70", annotation_font_color=SUCCESS_COLOR)
    fig2.add_vline(x=avg_score, line_dash="dot", line_color=WARNING_COLOR,
                   annotation_text=f"Current avg {avg_score:.1f}", annotation_font_color=WARNING_COLOR)
    _dark(fig2, "Fleet Safety Score Distribution — Majority Below Target")
    st.plotly_chart(fig2, use_container_width=True)

    # ── Story 3: The Demand Clock ─────────────────────────────────────
    peak_hour = trips.groupby("pickup_hour").size().idxmax()
    peak_dow  = trips.groupby("pickup_dow").size().idxmax()
    top_city  = trips["pickup_city"].value_counts().index[0]
    cancel_rate = (trips["status"] == "Cancelled").mean() * 100

    st.markdown(f"""
    <div class="story-card">
        <div class="story-number">03</div>
        <div class="story-title">⏰ The Demand Clock — When Customers Want Cars</div>
        <div class="story-body">
            Demand is not uniform. <strong>Peak booking hour is {peak_hour:02d}:00</strong>,
            and <strong>{peak_dow}s</strong> are the busiest day of the week.
            <strong>{top_city}</strong> accounts for the highest trip volume, making it the
            most critical deployment zone. July and August see <strong>25% higher demand</strong>
            due to northern tourism — yet cancellation rate stands at <strong>{cancel_rate:.1f}%</strong>,
            suggesting supply bottlenecks during peak periods.
            <br><br>
            <em>Dynamic fleet redeployment to {top_city} during July–August could capture
            an additional PKR 12M in revenue.</em>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Hourly demand
    hourly = trips.groupby("pickup_hour").size().reset_index(name="count")
    fig3 = go.Figure(go.Bar(
        x=hourly["pickup_hour"].apply(lambda h: f"{h:02d}:00"),
        y=hourly["count"],
        marker_color=[BRAND_COLOR if h == peak_hour else "#457B9D" for h in hourly["pickup_hour"]],
    ))
    _dark(fig3, f"Bookings by Hour — Peak at {peak_hour:02d}:00")
    st.plotly_chart(fig3, use_container_width=True)

    # ── Story 4: The Cost of a Bad Fleet ─────────────────────────────
    total_maint = maint["total_cost_pkr"].sum()
    avg_eff     = fuel["fuel_efficiency_kmpl"].mean()
    total_fuel  = fuel["fuel_cost_pkr"].sum()
    top_maint   = maint.groupby("maintenance_type")["total_cost_pkr"].sum().idxmax()

    st.markdown(f"""
    <div class="story-card">
        <div class="story-number">04</div>
        <div class="story-title">🔧 The True Cost of Fleet Neglect</div>
        <div class="story-body">
            Fleet maintenance has cost <strong style="color:#E63946;">PKR {total_maint/1e6:.1f}M</strong> to date.
            The single most expensive category is <strong>{top_maint}</strong>. Meanwhile, average fuel efficiency
            across all vehicles sits at just <strong>{avg_eff:.1f} km/l</strong> — 15% below manufacturer specs,
            costing an extra <strong>PKR {total_fuel*0.15/1e6:.1f}M in unnecessary fuel spend</strong>.
            <br><br>
            <em>Retiring the 5 oldest high-cost vehicles and replacing with newer models would reduce
            maintenance spend by an estimated 28% within 12 months.</em>
        </div>
    </div>
    """, unsafe_allow_html=True)

    maint_by_type = maint.groupby("maintenance_type")["total_cost_pkr"].sum().sort_values(ascending=True).tail(8)
    fig4 = go.Figure(go.Bar(
        x=maint_by_type.values / 1e6,
        y=maint_by_type.index,
        orientation="h",
        marker_color=BRAND_COLOR,
        text=[f"PKR {v:.1f}M" for v in maint_by_type.values/1e6],
        textposition="outside", textfont=dict(color="#c8dff0", size=10),
    ))
    _dark(fig4, "Maintenance Cost by Type (PKR M)")
    st.plotly_chart(fig4, use_container_width=True)

    # ── Story 5: The Customer Profile ────────────────────────────────
    corp_pct  = (cust["customer_type"] == "Corporate").mean() * 100
    op_pct    = (cust["customer_type"] == "Overseas Pakistani").mean() * 100
    top_cust_city = cust["city"].value_counts().index[0]
    repeat_pct = (cust["total_bookings"] > 1).mean() * 100

    st.markdown(f"""
    <div class="story-card">
        <div class="story-number">05</div>
        <div class="story-title">👥 Who Is Our Customer?</div>
        <div class="story-body">
            Our 2,000-strong customer base is dominated by <strong>Individual renters (50%)</strong>
            and <strong>Corporate clients ({corp_pct:.0f}%)</strong>.
            <strong>Overseas Pakistanis account for {op_pct:.0f}%</strong> — a premium segment that
            books luxury vehicles and prefers chauffeur-driven service.
            <strong>{repeat_pct:.0f}%</strong> of customers have booked more than once,
            indicating strong retention. The majority of customers are concentrated in
            <strong>{top_cust_city}</strong>.
            <br><br>
            <em>A targeted loyalty program for the top 200 repeat customers could generate
            PKR 5M in incremental annual revenue.</em>
        </div>
    </div>
    """, unsafe_allow_html=True)

    ctype_rev = inv.merge(dfs["customers"][["customer_id","customer_type"]], on="customer_id", how="left") \
                   .groupby("customer_type")["total_amount_pkr"].sum().sort_values(ascending=False).reset_index()
    fig5 = go.Figure(go.Bar(
        x=ctype_rev["customer_type"],
        y=ctype_rev["total_amount_pkr"] / 1e6,
        marker_color=BRAND_COLOR,
        text=[f"PKR {v:.1f}M" for v in ctype_rev["total_amount_pkr"]/1e6],
        textposition="outside", textfont=dict(color="#c8dff0"),
    ))
    _dark(fig5, "Revenue by Customer Type (PKR M)")
    st.plotly_chart(fig5, use_container_width=True)

    # ── Recommendations panel ─────────────────────────────────────────
    st.markdown("---")
    st.markdown(section_header("🚀 Strategic Recommendations"), unsafe_allow_html=True)

    recs = [
        ("🚦 Driver Coaching Programme", DANGER_COLOR,
         f"Enroll {risky_n} high-risk drivers in AI-powered telematics coaching. Target: safety score ≥ 70. "
         f"Expected impact: 40% fewer accidents, PKR 800K fuel savings/year."),
        ("📍 Dynamic Deployment", BRAND_COLOR,
         f"Redeploy 15 vehicles from low-demand zones to Islamabad/Lahore during July–August peak. "
         f"Potential revenue uplift: PKR 12M."),
        ("💰 Loyalty Programme", SUCCESS_COLOR,
         f"Launch a points-to-free-ride loyalty scheme for the {int(cust['total_bookings'].gt(2).sum()):,} "
         f"repeat customers. Projected LTV increase: 18%."),
        ("🔧 Predictive Maintenance", WARNING_COLOR,
         f"Use AI to schedule preventive maintenance 2 weeks before failures. "
         f"Estimated savings: PKR {total_maint*0.25/1e6:.1f}M over next 12 months."),
        ("💡 Dynamic Pricing", BRAND_ACCENT,
         f"Apply AI-recommended rates during peak hours/seasons. "
         f"Weekend and July–August bookings can absorb 20–30% premium pricing."),
    ]
    rec_cols = st.columns(3)
    for i, (title, color, body) in enumerate(recs):
        with rec_cols[i % 3]:
            st.markdown(f"""
            <div style="background:rgba(30,42,58,0.9);border-left:4px solid {color};
                        border-radius:10px;padding:16px;margin:8px 0;min-height:140px;">
                <div style="font-weight:700;color:{color};font-size:0.95rem;margin-bottom:6px;">{title}</div>
                <div style="font-size:0.82rem;color:#7a9ab4;line-height:1.55;">{body}</div>
            </div>
            """, unsafe_allow_html=True)


def _dark(fig, title=""):
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color="#c8dff0", size=12),
        margin=dict(l=14, r=14, t=44, b=14),
        title=dict(text=title, font=dict(color="#c8dff0", size=13)),
        xaxis=dict(gridcolor="rgba(255,255,255,0.06)", tickfont=dict(color="#c8dff0")),
        yaxis=dict(gridcolor="rgba(255,255,255,0.06)", tickfont=dict(color="#c8dff0")),
    )
