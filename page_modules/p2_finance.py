"""Finance & Revenue"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from page_modules._shared import (
    inject, get_data, fmt, kpi, sec, alert_box, dark_layout,
    BRAND, NAVY, STEEL, GREEN, AMBER, ORANGE, TEXT, GRID, BG, COLORS
)
from app.storytelling import insight, chart_header, revenue_insight, customer_insight

inject()
dfs = get_data()
inv   = dfs["invoices"]
trips = dfs["trips"]
opex  = dfs["operating_expenses"]
fuel  = dfs["fuel_logs"]
maint = dfs["maintenance"]
TODAY = pd.Timestamp("2026-07-01")

st.markdown(f'<div style="font-size:1.5rem;font-weight:800;color:{BRAND};margin-bottom:4px;">💰 Finance & Revenue</div>', unsafe_allow_html=True)
st.markdown(f'<div style="font-size:.8rem;color:#5a7a96;">Billing, collections, P&L and payment analytics</div>', unsafe_allow_html=True)
st.markdown("<hr style='border-color:#1e2f44;margin:6px 0 14px 0'>", unsafe_allow_html=True)

# ── Filters ────────────────────────────────────────────────────────────
cf = st.columns(3)
years = ["All"] + sorted(inv["invoice_year"].dropna().unique().astype(int).tolist(), reverse=True)
sel_yr  = cf[0].selectbox("Year",           years,    key="fin_yr")
fleet_names = ["All"] + dfs["fleets"]["fleet_name"].tolist()
sel_fl  = cf[1].selectbox("Fleet",          fleet_names, key="fin_fl")
pay_opts = ["All"] + sorted(inv["payment_method"].dropna().unique().tolist())
sel_pay = cf[2].selectbox("Payment Method", pay_opts, key="fin_pay")

inv_f = inv.copy()
if sel_yr != "All": inv_f = inv_f[inv_f["invoice_year"] == int(sel_yr)]
if sel_fl != "All":
    fid = dfs["fleets"].loc[dfs["fleets"]["fleet_name"]==sel_fl,"fleet_id"].values[0]
    inv_f = inv_f[inv_f["fleet_id"]==fid]
if sel_pay != "All": inv_f = inv_f[inv_f["payment_method"]==sel_pay]

billed    = inv_f["total_amount_pkr"].sum()
collected = inv_f["paid_amount_pkr"].sum()
outs      = billed - collected
surcharge = inv_f["total_surcharge_pkr"].sum()
discount  = inv_f["discount_pkr"].sum()
col_rate  = collected/billed*100 if billed else 0

c = st.columns(5)
kpi(c[0], fmt(billed),    "Total Billed",      "")
kpi(c[1], fmt(collected), "Collected",          f"{col_rate:.1f}% rate", col_rate>90)
kpi(c[2], fmt(outs),      "Outstanding",        f"{len(inv_f[inv_f['outstanding_pkr']>0]):,} invoices", outs==0)
kpi(c[3], fmt(surcharge), "Surcharge Revenue",  "")
kpi(c[4], fmt(discount),  "Total Discounts",    "", False)

st.markdown("<hr style='border-color:#1e2f44;margin:14px 0'>", unsafe_allow_html=True)

# ── Revenue trend ──────────────────────────────────────────────────────
sec("📈 Revenue Trend")
inv_f["_m"] = inv_f["invoice_date"].dt.to_period("M")
mr = inv_f.groupby("_m").agg(billed=("total_amount_pkr","sum"), col=("paid_amount_pkr","sum")).reset_index()
mr["_m"] = mr["_m"].astype(str); mr["outs"] = mr["billed"]-mr["col"]

col1, col2 = st.columns(2)
with col1:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=mr["_m"], y=mr["billed"]/1e6, name="Billed",
        fill="tozeroy", fillcolor="rgba(230,57,70,.15)", line=dict(color=BRAND,width=2.5), mode="lines+markers", marker=dict(size=4)))
    fig.add_trace(go.Scatter(x=mr["_m"], y=mr["col"]/1e6, name="Collected",
        fill="tozeroy", fillcolor="rgba(42,157,143,.12)", line=dict(color=GREEN,width=2), mode="lines+markers", marker=dict(size=4)))
    fig.add_trace(go.Scatter(x=mr["_m"], y=mr["outs"]/1e6, name="Outstanding",
        line=dict(color=ORANGE,width=1.5,dash="dot")))
    dark_layout(fig, "Monthly Revenue (PKR M)", xangle=-45)
    st.plotly_chart(fig, width='stretch')
    # Revenue insight below trend chart
    txt, sub, lvl = revenue_insight(inv_f)
    insight(txt, "💰", lvl, sub)

with col2:
    trips_f = trips if sel_fl=="All" else trips[trips["fleet_id"]==fid]
    g = trips_f[trips_f["status"]=="Completed"].groupby("booking_type")["revenue_pkr"].sum().reset_index().sort_values("revenue_pkr")
    fig2 = go.Figure(go.Bar(x=g["revenue_pkr"]/1e6, y=g["booking_type"], orientation="h",
        marker=dict(color=g["revenue_pkr"], colorscale=[[0,NAVY],[0.5,STEEL],[1,BRAND]]),
        text=[f"{v:.1f}M" for v in g["revenue_pkr"]/1e6], textposition="outside", textfont=dict(color=TEXT,size=9)))
    dark_layout(fig2, "Revenue by Booking Type (PKR M)")
    st.plotly_chart(fig2, width='stretch')

# ── Payment methods + Fleet share ──────────────────────────────────────
sec("💳 Payment Analytics")
col3, col4 = st.columns(2)
with col3:
    pm = inv_f.groupby("payment_method")["total_amount_pkr"].sum().reset_index().sort_values("total_amount_pkr",ascending=False)
    fig3 = go.Figure(go.Bar(x=pm["payment_method"], y=pm["total_amount_pkr"]/1e6,
        marker_color=COLORS[:len(pm)],
        text=[f"{v:.1f}M" for v in pm["total_amount_pkr"]/1e6], textposition="outside", textfont=dict(color=TEXT,size=9)))
    dark_layout(fig3, "Revenue by Payment Method (PKR M)")
    st.plotly_chart(fig3, width='stretch')

with col4:
    fleet_rev = trips[trips["status"]=="Completed"].groupby("fleet_id")["revenue_pkr"].sum().reset_index()
    fleet_rev = fleet_rev.merge(dfs["fleets"][["fleet_id","fleet_name"]], on="fleet_id", how="left")
    fig4 = go.Figure(go.Pie(labels=fleet_rev["fleet_name"], values=fleet_rev["revenue_pkr"], hole=0.52,
        marker=dict(colors=COLORS, line=dict(color="#0f1117",width=2)), textfont=dict(color="#fff",size=10)))
    dark_layout(fig4, "Revenue Share by Fleet", height=340)
    st.plotly_chart(fig4, width='stretch')

# ── P&L Waterfall ──────────────────────────────────────────────────────
sec("📊 P&L Waterfall")
fuel_c  = fuel["fuel_cost_pkr"].sum()
maint_c = maint["total_cost_pkr"].sum()
sal_c   = opex[opex["category"].isin(["Driver Salaries","Staff Salaries"])]["amount_pkr"].sum()
other_c = opex[~opex["category"].isin(["Driver Salaries","Staff Salaries"])]["amount_pkr"].sum()
profit  = billed - fuel_c - maint_c - sal_c - other_c

fig5 = go.Figure(go.Waterfall(
    orientation="v", measure=["absolute","relative","relative","relative","relative","total"],
    x=["Revenue","Fuel","Maintenance","Salaries","Other OpEx","Net Profit"],
    y=[billed, -fuel_c, -maint_c, -sal_c, -other_c, profit],
    connector=dict(line=dict(color=GRID,width=1)),
    increasing=dict(marker=dict(color=GREEN)),
    decreasing=dict(marker=dict(color=ORANGE)),
    totals=dict(marker=dict(color=STEEL)),
    text=[f"PKR {abs(v)/1e6:.1f}M" for v in [billed,-fuel_c,-maint_c,-sal_c,-other_c,profit]],
    textposition="outside", textfont=dict(color=TEXT)))
dark_layout(fig5, "Profit & Loss Waterfall (PKR)", height=380)
st.plotly_chart(fig5, width='stretch')

# P&L insight
margin = profit/billed*100 if billed else 0
fuel_pct = fuel_c/billed*100 if billed else 0
sal_pct  = sal_c/billed*100 if billed else 0
insight(
    f"Net profit margin is <strong>{margin:.1f}%</strong> of billed revenue. "
    f"Fuel costs consume <strong>{fuel_pct:.1f}%</strong> of revenue — "
    f"the single largest variable cost. Salaries represent <strong>{sal_pct:.1f}%</strong>. "
    f"A 2 km/l fuel efficiency improvement across the fleet would save "
    f"<strong>PKR {fuel_c*0.15/1e6:.1f}M</strong> annually, directly boosting margin.",
    "📊", "good" if margin > 20 else ("warn" if margin > 5 else "bad"),
    f"{'✅ Healthy margin above 20%.' if margin > 20 else f'⚠️ Margin {margin:.1f}% needs improvement — target fuel and idle reduction first.'}"
)

# ── OpEx stacked bar ───────────────────────────────────────────────────
sec("🏢 Monthly Operating Expenses")
opex_f = opex.copy()
if sel_fl != "All": opex_f = opex_f[opex_f["fleet_id"]==fid]
if sel_yr != "All": opex_f = opex_f[opex_f["year"]==int(sel_yr)]
pivot = opex_f.pivot_table(index="month_period", columns="category", values="amount_pkr", aggfunc="sum").fillna(0)
fig6 = go.Figure()
for i, col in enumerate(pivot.columns):
    fig6.add_trace(go.Bar(x=pivot.index, y=pivot[col]/1e3, name=col, marker_color=COLORS[i%len(COLORS)]))
fig6.update_layout(barmode="stack")
dark_layout(fig6, "Monthly OpEx by Category (PKR K)", xangle=-45, height=360)
st.plotly_chart(fig6, width='stretch')

# ── AR Aging ───────────────────────────────────────────────────────────
sec("📋 Accounts Receivable Aging")
unpaid = inv_f[inv_f["outstanding_pkr"]>0].copy()
unpaid["days_overdue"] = (TODAY - unpaid["due_date"]).dt.days.clip(0)
unpaid["bucket"] = pd.cut(unpaid["days_overdue"],
    bins=[-1,0,30,60,90,9999], labels=["Current","1–30d","31–60d","61–90d","90d+"])
aging = unpaid.groupby("bucket", observed=True).agg(
    invoices=("invoice_id","count"), outstanding=("outstanding_pkr","sum")).reset_index()
aging["outstanding"] = aging["outstanding"].apply(fmt)
col_a, _ = st.columns([2,1])
col_a.dataframe(aging, width='stretch', hide_index=True)

# ── Top customers ──────────────────────────────────────────────────────
sec("🏆 Top 10 Customers by Revenue")
tc = inv_f.merge(dfs["customers"][["customer_id","full_name","customer_type"]],on="customer_id",how="left") \
           .groupby(["full_name","customer_type"])["total_amount_pkr"].sum().reset_index() \
           .nlargest(10,"total_amount_pkr")
tc["total_amount_pkr"] = tc["total_amount_pkr"].apply(fmt)
tc.columns = ["Customer","Type","Revenue"]
st.dataframe(tc, width='stretch', hide_index=True)

