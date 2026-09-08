"""
Page 10 – Alerts & Watchlist
Real-time operational alerts, compliance monitoring, risk radar.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from app.style import inject_css, kpi_card, section_header, alert
from app.style import BRAND_COLOR, SUCCESS_COLOR, DANGER_COLOR, WARNING_COLOR, BRAND_ACCENT


def render(dfs: dict):
    inject_css()

    st.markdown('<div style="font-size:1.6rem;font-weight:800;color:#E63946;margin-bottom:4px;">⚠️ Alerts & Watchlist</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:0.82rem;color:#5a7a96;">Operational risk monitoring, compliance checks, and fleet watchlist</div>', unsafe_allow_html=True)
    st.markdown("---")

    TODAY = pd.Timestamp("2026-07-01")

    vehicles = dfs["vehicles"].copy()
    drivers  = dfs["drivers"].copy()
    maint    = dfs["maintenance"].copy()
    inv      = dfs["invoices"].copy()
    trips    = dfs["trips"].copy()
    tel      = dfs["telematics"].copy()

    # ── Parse dates ───────────────────────────────────────────────────
    vehicles["insurance_expiry"]    = pd.to_datetime(vehicles["insurance_expiry"],    errors="coerce")
    vehicles["fitness_cert_expiry"] = pd.to_datetime(vehicles["fitness_cert_expiry"], errors="coerce")
    drivers["license_expiry"]       = pd.to_datetime(drivers["license_expiry"],       errors="coerce")
    maint["next_due_date"]          = pd.to_datetime(maint["next_due_date"],          errors="coerce")
    inv["due_date"]                 = pd.to_datetime(inv["due_date"],                 errors="coerce")

    # ── CRITICAL alerts ───────────────────────────────────────────────
    expired_ins  = vehicles[vehicles["insurance_expiry"]  < TODAY]
    expired_fit  = vehicles[vehicles["fitness_cert_expiry"] < TODAY]
    expired_lic  = drivers[drivers["license_expiry"] < TODAY]
    dangerous_drv= drivers[drivers["behavior_profile"] == "dangerous"]
    overdue_inv  = inv[(inv["due_date"] < TODAY) & (inv["outstanding_pkr"] > 0)]
    overdue_maint= maint[(maint["next_due_date"] < TODAY) & (maint["status"] == "Scheduled")]

    # ── WARNING alerts ────────────────────────────────────────────────
    expiring_soon_ins = vehicles[
        (vehicles["insurance_expiry"] >= TODAY) &
        (vehicles["insurance_expiry"] < TODAY + pd.Timedelta(days=30))
    ]
    expiring_soon_lic = drivers[
        (drivers["license_expiry"] >= TODAY) &
        (drivers["license_expiry"] < TODAY + pd.Timedelta(days=30))
    ]
    poor_drivers = drivers[drivers["behavior_profile"] == "poor"]
    high_idle_drivers = tel.groupby("driver_id")["idle_time_minutes"].mean()
    high_idle_ids = high_idle_drivers[high_idle_drivers > 200].index.tolist()
    high_idle_drv = drivers[drivers["driver_id"].isin(high_idle_ids)]

    # ── KPI counts ────────────────────────────────────────────────────
    total_critical = len(expired_ins) + len(expired_fit) + len(expired_lic) + len(dangerous_drv)
    total_warning  = len(expiring_soon_ins) + len(expiring_soon_lic) + len(poor_drivers) + len(high_idle_drv)
    total_info     = len(overdue_maint) + len(overdue_inv.head(1))

    cols = st.columns(4)
    cols[0].markdown(kpi_card(str(total_critical), "Critical Alerts", "Immediate action", total_critical == 0), unsafe_allow_html=True)
    cols[1].markdown(kpi_card(str(total_warning),  "Warnings",        "Action within 30d", total_warning == 0),  unsafe_allow_html=True)
    cols[2].markdown(kpi_card(f"PKR {overdue_inv['outstanding_pkr'].sum()/1e6:.1f}M", "Overdue Receivables", f"{len(overdue_inv)} invoices", overdue_inv['outstanding_pkr'].sum() == 0), unsafe_allow_html=True)
    cols[3].markdown(kpi_card(str(len(overdue_maint)), "Overdue Services", "Scheduled but pending", len(overdue_maint) == 0), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")

    # ── Tabs ──────────────────────────────────────────────────────────
    tabs = st.tabs(["🔴 Critical", "🟠 Warnings", "💰 Finance", "🚦 Driver Risk", "🔧 Maintenance", "📊 Risk Overview"])

    # ── CRITICAL ──────────────────────────────────────────────────────
    with tabs[0]:
        st.markdown(section_header("🔴 Critical Alerts — Immediate Action Required"), unsafe_allow_html=True)

        _section_table(
            expired_ins,
            title=f"Expired Vehicle Insurance ({len(expired_ins)} vehicles)",
            cols=["vehicle_id","make","model","registration_no","insurance_expiry","status"],
            level="critical",
            empty_msg="✅ All vehicle insurance policies are current.",
        )

        _section_table(
            expired_fit,
            title=f"Expired Fitness Certificate ({len(expired_fit)} vehicles)",
            cols=["vehicle_id","make","model","registration_no","fitness_cert_expiry","status"],
            level="critical",
            empty_msg="✅ All fitness certificates are current.",
        )

        _section_table(
            expired_lic,
            title=f"Expired Driver Licences ({len(expired_lic)} drivers)",
            cols=["driver_id","full_name","license_no","license_expiry","behavior_profile"],
            level="critical",
            empty_msg="✅ All driver licences are valid.",
        )

        _section_table(
            dangerous_drv,
            title=f"Dangerous Driver Profile ({len(dangerous_drv)} drivers)",
            cols=["driver_id","full_name","behavior_profile","total_trips","accidents_count","complaints_count"],
            level="critical",
            empty_msg="✅ No drivers flagged as dangerous.",
        )

    # ── WARNINGS ──────────────────────────────────────────────────────
    with tabs[1]:
        st.markdown(section_header("🟠 Warnings — Action Within 30 Days"), unsafe_allow_html=True)

        _section_table(
            expiring_soon_ins,
            title=f"Insurance Expiring Soon ({len(expiring_soon_ins)} vehicles)",
            cols=["vehicle_id","make","model","registration_no","insurance_expiry"],
            level="warning",
            empty_msg="✅ No insurance expiring in next 30 days.",
        )

        _section_table(
            expiring_soon_lic,
            title=f"Licences Expiring Soon ({len(expiring_soon_lic)} drivers)",
            cols=["driver_id","full_name","license_no","license_expiry"],
            level="warning",
            empty_msg="✅ No licences expiring in next 30 days.",
        )

        _section_table(
            poor_drivers,
            title=f"Poor Behavior Drivers ({len(poor_drivers)} drivers)",
            cols=["driver_id","full_name","behavior_profile","harsh_brake_rate","speeding_pct","ratings_avg"],
            level="warning",
            empty_msg="✅ No drivers on poor profile.",
        )

        _section_table(
            high_idle_drv,
            title=f"High Idle-Time Drivers ({len(high_idle_drv)} drivers)",
            cols=["driver_id","full_name","behavior_profile","idle_time_pct"],
            level="warning",
            empty_msg="✅ No drivers with excessive idling.",
        )

    # ── FINANCE ───────────────────────────────────────────────────────
    with tabs[2]:
        st.markdown(section_header("💰 Finance Alerts"), unsafe_allow_html=True)

        if len(overdue_inv) > 0:
            st.markdown(alert(f"🟡 {len(overdue_inv):,} invoices past due — total PKR {overdue_inv['outstanding_pkr'].sum()/1e6:.1f}M", "warning"), unsafe_allow_html=True)
            show_inv = overdue_inv.sort_values("outstanding_pkr", ascending=False).head(50)
            show_inv = show_inv.merge(dfs["customers"][["customer_id","full_name","customer_type"]], on="customer_id", how="left")
            st.dataframe(show_inv[["invoice_id","full_name","customer_type","invoice_date","due_date",
                                   "total_amount_pkr","outstanding_pkr","payment_method"]].reset_index(drop=True),
                         use_container_width=True, height=320)
        else:
            st.markdown(alert("✅ No overdue invoices.", "info"), unsafe_allow_html=True)

        # Payment status pie
        pay_status = inv["payment_status"].value_counts().reset_index()
        pay_status.columns = ["status", "count"]
        fig_ps = go.Figure(go.Pie(
            labels=pay_status["status"], values=pay_status["count"],
            hole=0.5,
            marker=dict(
                colors=[SUCCESS_COLOR, WARNING_COLOR, DANGER_COLOR],
                line=dict(color="#0f1117", width=2),
            ),
        ))
        _dark(fig_ps, "Invoice Payment Status")
        st.plotly_chart(fig_ps, use_container_width=True)

    # ── DRIVER RISK ────────────────────────────────────────────────────
    with tabs[3]:
        st.markdown(section_header("🚦 Driver Risk Radar"), unsafe_allow_html=True)

        # Combined risk score
        drv_risk = drivers.copy()
        drv_risk["risk_score"] = (
            (drv_risk["harsh_brake_rate"]  * 30) +
            (drv_risk["harsh_accel_rate"]  * 25) +
            (drv_risk["idle_time_pct"]     * 20) +
            (drv_risk["speeding_pct"]      * 25)
        ) * 100
        drv_risk["risk_score"] = drv_risk["risk_score"].clip(0, 100).round(1)
        drv_risk = drv_risk.sort_values("risk_score", ascending=False)

        c1, c2 = st.columns(2)
        with c1:
            fig_risk = go.Figure(go.Bar(
                x=drv_risk.head(15)["full_name"],
                y=drv_risk.head(15)["risk_score"],
                marker_color=[
                    DANGER_COLOR if r > 60 else (WARNING_COLOR if r > 35 else SUCCESS_COLOR)
                    for r in drv_risk.head(15)["risk_score"]
                ],
                text=[f"{r:.0f}" for r in drv_risk.head(15)["risk_score"]],
                textposition="outside", textfont=dict(color="#c8dff0", size=9),
            ))
            _dark(fig_risk, "Top 15 Highest Risk Drivers")
            fig_risk.update_xaxes(tickangle=-45)
            st.plotly_chart(fig_risk, use_container_width=True)

        with c2:
            # Accidents over time
            acc_tel = tel[tel["accident_occurred"] == True].copy()
            if len(acc_tel) > 0:
                acc_tel["month"] = pd.to_datetime(acc_tel["trip_date"]).dt.to_period("M").astype(str)
                acc_by_month = acc_tel.groupby("month").size().reset_index(name="accidents")
                fig_acc = go.Figure(go.Bar(
                    x=acc_by_month["month"],
                    y=acc_by_month["accidents"],
                    marker_color=DANGER_COLOR,
                ))
                _dark(fig_acc, "Accidents by Month")
                st.plotly_chart(fig_acc, use_container_width=True)
            else:
                st.info("No accidents recorded in telematics data.")

        st.dataframe(drv_risk[["driver_id","full_name","behavior_profile","risk_score",
                                "harsh_brake_rate","harsh_accel_rate","speeding_pct","accidents_count"]]
                     .head(30).reset_index(drop=True), use_container_width=True, height=280)

    # ── MAINTENANCE ────────────────────────────────────────────────────
    with tabs[4]:
        st.markdown(section_header("🔧 Maintenance Watchlist"), unsafe_allow_html=True)
        _section_table(
            overdue_maint,
            title=f"Overdue / Pending Services ({len(overdue_maint)})",
            cols=["maint_id","vehicle_id","maintenance_type","maintenance_date","next_due_date","total_cost_pkr","status"],
            level="warning",
            empty_msg="✅ No overdue maintenance services.",
        )

        # Cost trajectory
        maint["maintenance_date"] = pd.to_datetime(maint["maintenance_date"], errors="coerce")
        maint["maint_month"] = maint["maintenance_date"].dt.to_period("M").astype(str)
        maint_trend = maint.groupby("maint_month")["total_cost_pkr"].sum().reset_index()
        fig_mt = go.Figure(go.Scatter(
            x=maint_trend["maint_month"],
            y=maint_trend["total_cost_pkr"] / 1e3,
            fill="tozeroy", fillcolor="rgba(231,111,81,0.12)",
            line=dict(color=DANGER_COLOR, width=2),
            mode="lines+markers", marker=dict(size=4),
        ))
        _dark(fig_mt, "Monthly Maintenance Cost (PKR Thousands)")
        fig_mt.update_xaxes(tickangle=-45)
        st.plotly_chart(fig_mt, use_container_width=True)

    # ── RISK OVERVIEW ──────────────────────────────────────────────────
    with tabs[5]:
        st.markdown(section_header("📊 Risk Overview Dashboard"), unsafe_allow_html=True)

        categories = ["Insurance", "Licences", "Dangerous Drivers", "Overdue Payments", "Pending Maintenance"]
        critical_vals = [len(expired_ins), len(expired_lic), len(dangerous_drv),
                         len(overdue_inv[overdue_inv["outstanding_pkr"] > 50000]),
                         len(overdue_maint)]
        warning_vals  = [len(expiring_soon_ins), len(expiring_soon_lic), len(poor_drivers),
                         len(overdue_inv[overdue_inv["outstanding_pkr"].between(1, 50000)]),
                         0]

        fig_risk_ov = go.Figure()
        fig_risk_ov.add_trace(go.Bar(
            name="Critical", x=categories, y=critical_vals,
            marker_color=DANGER_COLOR,
        ))
        fig_risk_ov.add_trace(go.Bar(
            name="Warning", x=categories, y=warning_vals,
            marker_color=WARNING_COLOR,
        ))
        fig_risk_ov.update_layout(
            barmode="stack",
            template="plotly_white", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#c8dff0"), margin=dict(l=14,r=14,t=44,b=14),
            title=dict(text="Risk Summary by Category", font=dict(color="#c8dff0",size=13)),
            xaxis=dict(gridcolor="rgba(255,255,255,0.06)", tickfont=dict(color="#c8dff0")),
            yaxis=dict(gridcolor="rgba(255,255,255,0.06)", tickfont=dict(color="#c8dff0")),
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#c8dff0")),
        )
        st.plotly_chart(fig_risk_ov, use_container_width=True)


def _section_table(df: pd.DataFrame, title: str, cols: list,
                   level: str = "warning", empty_msg: str = ""):
    st.markdown(f'<div class="section-header">{title}</div>', unsafe_allow_html=True)
    if len(df) == 0:
        st.markdown(alert(empty_msg, "info"), unsafe_allow_html=True)
    else:
        available_cols = [c for c in cols if c in df.columns]
        st.dataframe(df[available_cols].reset_index(drop=True), use_container_width=True, height=200)


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
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#c8dff0", size=11)),
    )
