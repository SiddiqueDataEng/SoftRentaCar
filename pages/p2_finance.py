"""
Page 2 – Finance & Revenue
Monthly trends, payment methods, fleet P&L, AR aging.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from app.style import inject_css, kpi_card, section_header
from app.charts import (
    revenue_trend, revenue_by_booking_type, fleet_revenue_pie,
    payment_method_bar, opex_breakdown_stacked, profit_waterfall,
)
from app.data_loader import monthly_revenue
from app.style import PLOTLY_COLORS, BRAND_COLOR, SUCCESS_COLOR, DANGER_COLOR, _TEXT


def render(dfs: dict):
    inject_css()

    st.markdown('<div style="font-size:1.6rem;font-weight:800;color:#E63946;margin-bottom:4px;">💰 Finance & Revenue</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:0.82rem;color:#5a7a96;">Billing, collections, P&L, and payment analytics</div>', unsafe_allow_html=True)
    st.markdown("---")

    inv   = dfs["invoices"]
    trips = dfs["trips"]
    opex  = dfs["operating_expenses"]
    fuel  = dfs["fuel_logs"]
    maint = dfs["maintenance"]

    # ── Filters ──────────────────────────────────────────────────────
    col_f1, col_f2, col_f3 = st.columns(3)
    years = sorted(inv["invoice_year"].dropna().unique().astype(int))
    sel_year = col_f1.selectbox("Filter Year", ["All"] + list(map(str, years)))
    fleet_names = ["All"] + dfs["fleets"]["fleet_name"].tolist()
    sel_fleet = col_f2.selectbox("Filter Fleet", fleet_names)
    pay_methods = ["All"] + inv["payment_method"].unique().tolist()
    sel_pay = col_f3.selectbox("Payment Method", pay_methods)

    inv_f = inv.copy()
    if sel_year != "All":
        inv_f = inv_f[inv_f["invoice_year"] == int(sel_year)]
    if sel_fleet != "All":
        fid = dfs["fleets"][dfs["fleets"]["fleet_name"] == sel_fleet]["fleet_id"].values[0]
        inv_f = inv_f[inv_f["fleet_id"] == fid]
    if sel_pay != "All":
        inv_f = inv_f[inv_f["payment_method"] == sel_pay]

    # ── KPIs ─────────────────────────────────────────────────────────
    total_billed    = inv_f["total_amount_pkr"].sum()
    total_collected = inv_f["paid_amount_pkr"].sum()
    outstanding     = total_billed - total_collected
    discount_total  = inv_f["discount_pkr"].sum()
    surcharge_total = inv_f["total_surcharge_pkr"].sum()
    col_rate        = total_collected / total_billed * 100 if total_billed else 0

    cols = st.columns(5)
    kpis = [
        (_f(total_billed), "Total Billed"),
        (_f(total_collected), "Collected"),
        (_f(outstanding), "Outstanding"),
        (_f(surcharge_total), "Surcharge Revenue"),
        (f"{col_rate:.1f}%", "Collection Rate"),
    ]
    for col, (v, l) in zip(cols, kpis):
        col.markdown(kpi_card(v, l), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")

    # ── Row 1: Revenue trend + Booking type ──────────────────────────
    st.markdown(section_header("Revenue Trends"), unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        mr = _monthly_rev(inv_f)
        st.plotly_chart(revenue_trend(mr), use_container_width=True)
    with c2:
        trips_f = trips
        if sel_fleet != "All":
            trips_f = trips[trips["fleet_id"] == fid]
        st.plotly_chart(revenue_by_booking_type(trips_f), use_container_width=True)

    # ── Row 2: Payment methods + Fleet share ─────────────────────────
    st.markdown(section_header("Payment Analytics"), unsafe_allow_html=True)
    c3, c4 = st.columns(2)
    with c3:
        st.plotly_chart(payment_method_bar(inv_f), use_container_width=True)
    with c4:
        st.plotly_chart(fleet_revenue_pie(trips, dfs["fleets"]), use_container_width=True)

    # ── P&L Waterfall ────────────────────────────────────────────────
    st.markdown(section_header("Profit & Loss Waterfall"), unsafe_allow_html=True)
    fuel_cost   = fuel["fuel_cost_pkr"].sum()
    maint_cost  = maint["total_cost_pkr"].sum()
    salary_cost = opex[opex["category"].isin(["Driver Salaries", "Staff Salaries"])]["amount_pkr"].sum()
    other_cost  = opex[~opex["category"].isin(["Driver Salaries", "Staff Salaries"])]["amount_pkr"].sum()
    st.plotly_chart(profit_waterfall(total_billed, fuel_cost, maint_cost, salary_cost, other_cost), use_container_width=True)

    # ── OpEx breakdown ───────────────────────────────────────────────
    st.markdown(section_header("Operating Expenses Breakdown"), unsafe_allow_html=True)
    opex_f = opex.copy()
    if sel_fleet != "All":
        opex_f = opex_f[opex_f["fleet_id"] == fid]
    if sel_year != "All":
        opex_f = opex_f[opex_f["year"] == int(sel_year)]
    st.plotly_chart(opex_breakdown_stacked(opex_f), use_container_width=True)

    # ── AR Aging Table ────────────────────────────────────────────────
    st.markdown(section_header("Accounts Receivable Aging"), unsafe_allow_html=True)
    today = pd.Timestamp("2026-07-01")
    unpaid = inv_f[inv_f["outstanding_pkr"] > 0].copy()
    unpaid["days_overdue"] = (today - unpaid["due_date"]).dt.days.clip(0)
    unpaid["aging_bucket"] = pd.cut(unpaid["days_overdue"],
        bins=[-1, 0, 30, 60, 90, 9999],
        labels=["Current", "1–30d", "31–60d", "61–90d", "90d+"])
    aging = unpaid.groupby("aging_bucket").agg(
        invoices=("invoice_id","count"),
        outstanding=("outstanding_pkr","sum"),
    ).reset_index()
    aging["outstanding"] = aging["outstanding"].apply(_f)

    col_ag, _ = st.columns([2, 1])
    with col_ag:
        st.dataframe(aging, use_container_width=True, hide_index=True)

    # ── Top customers by revenue ──────────────────────────────────────
    st.markdown(section_header("Top 10 Customers by Revenue"), unsafe_allow_html=True)
    top_cust = inv_f.merge(dfs["customers"][["customer_id","full_name","customer_type"]], on="customer_id", how="left") \
                    .groupby(["customer_id","full_name","customer_type"])["total_amount_pkr"].sum() \
                    .reset_index().nlargest(10, "total_amount_pkr")
    top_cust["total_amount_pkr"] = top_cust["total_amount_pkr"].apply(_f)
    st.dataframe(top_cust.drop(columns=["customer_id"]), use_container_width=True, hide_index=True)


def _monthly_rev(inv_df: pd.DataFrame) -> pd.DataFrame:
    inv_df["month"] = inv_df["invoice_date"].dt.to_period("M")
    g = inv_df.groupby("month").agg(
        total_billed=("total_amount_pkr","sum"),
        total_collected=("paid_amount_pkr","sum"),
    ).reset_index()
    g["month"] = g["month"].astype(str)
    g["outstanding"] = g["total_billed"] - g["total_collected"]
    return g.sort_values("month")


def _f(v):
    v = float(v)
    if v >= 1e9: return f"PKR {v/1e9:.2f}B"
    if v >= 1e6: return f"PKR {v/1e6:.1f}M"
    if v >= 1e3: return f"PKR {v/1e3:.0f}K"
    return f"PKR {v:,.0f}"
