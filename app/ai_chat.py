"""
AI Chat engine — Soft Rent a Car
Priority order for OpenAI key:
  1. st.secrets["OPENAI_API_KEY"]   (Streamlit Cloud secrets)
  2. os.environ["OPENAI_API_KEY"]   (set by user in UI)
  3. Rule-based fallback
"""

import re
import os
import datetime
import numpy as np
import pandas as pd


# ── Key resolution ────────────────────────────────────────────────────

def _resolve_key() -> str:
    """Return the best available OpenAI key, or empty string."""
    # 1. Streamlit secrets (Streamlit Cloud / local secrets.toml)
    try:
        import streamlit as st
        key = st.secrets.get("OPENAI_API_KEY", "")
        if key and len(key) > 20:
            return key
    except Exception:
        pass
    # 2. Environment variable (set via UI or shell)
    key = os.getenv("OPENAI_API_KEY", "")
    if key and len(key) > 20:
        return key
    return ""


# ── Intent classifier ─────────────────────────────────────────────────

INTENTS = {
    "revenue":   ["revenue", "income", "billing", "invoice", "earned", "collected", "pkr", "money", "profit"],
    "trips":     ["trip", "booking", "ride", "rental", "journey", "travel"],
    "driver":    ["driver", "driving", "behavior", "behaviour", "safety", "accident", "brake", "speed", "idle"],
    "vehicle":   ["vehicle", "car", "fleet", "maintenance", "fuel", "efficiency", "status", "tyre"],
    "customer":  ["customer", "client", "renter", "passenger", "loyalty"],
    "forecast":  ["forecast", "predict", "next month", "future", "upcoming", "trend"],
    "top":       ["top", "best", "highest", "most", "lowest", "worst", "ranking", "list"],
    "alert":     ["alert", "issue", "problem", "risk", "overdue", "expired", "danger"],
    "city":      ["city", "islamabad", "lahore", "karachi", "rawalpindi", "peshawar", "murree"],
    "kpi":       ["kpi", "utilisation", "utilization", "rate", "occupancy", "performance", "metric"],
    "sql":       ["sql", "query", "database", "table", "select", "join", "window", "cte"],
    "help":      ["help", "what can", "what do you", "capabilities", "commands", "how to"],
}

GREETINGS = ["hello", "hi", "hey", "salam", "assalamu", "good morning", "good evening",
             "good afternoon", "howdy", "sup", "yo"]


def _detect_intent(text: str) -> list:
    tl = text.lower()
    return [k for k, words in INTENTS.items() if any(w in tl for w in words)] or ["general"]


def _fmt(v: float) -> str:
    if v >= 1e9: return f"PKR {v/1e9:.2f}B"
    if v >= 1e6: return f"PKR {v/1e6:.1f}M"
    if v >= 1e3: return f"PKR {v/1e3:.0f}K"
    return f"PKR {v:,.0f}"


# ── Rule-based handlers ───────────────────────────────────────────────

def _revenue(dfs):
    inv = dfs["invoices"]
    total = inv["total_amount_pkr"].sum()
    coll  = inv["paid_amount_pkr"].sum()
    outs  = total - coll
    latest_m = inv["invoice_date"].dt.to_period("M").max()
    month_rev = inv[inv["invoice_date"].dt.to_period("M") == latest_m]["total_amount_pkr"].sum()
    fleet_rev = inv.merge(dfs["fleets"][["fleet_id","fleet_name"]], on="fleet_id", how="left") \
                   .groupby("fleet_name")["total_amount_pkr"].sum().sort_values(ascending=False)
    return f"""📊 **Revenue Summary**

- **Total Billed:** {_fmt(total)}
- **Total Collected:** {_fmt(coll)} ({coll/total*100:.1f}% collection rate)
- **Outstanding:** {_fmt(outs)}
- **{str(latest_m)} Revenue:** {_fmt(month_rev)}
- **Top Fleet:** {fleet_rev.index[0]} — {_fmt(fleet_rev.iloc[0])}

💡 *Finance page has month-by-month trends, P&L waterfall and payment breakdowns.*"""


def _trips(dfs):
    t = dfs["trips"]
    comp = (t["status"] == "Completed").sum()
    canc = (t["status"] == "Cancelled").sum()
    total = len(t)
    avg_km   = t[t["status"]=="Completed"]["distance_km"].mean()
    avg_fare = t[t["status"]=="Completed"]["revenue_pkr"].mean()
    top_type = t.groupby("booking_type").size().idxmax()
    top_city = t.groupby("pickup_city").size().idxmax()
    return f"""🚗 **Trips & Bookings Summary**

- **Total Bookings:** {total:,}
- **Completed:** {comp:,} ({comp/total*100:.1f}%)
- **Cancelled:** {canc:,} ({canc/total*100:.1f}%)
- **Avg Distance:** {avg_km:.1f} km  |  **Avg Fare:** {_fmt(avg_fare)}
- **Top Booking Type:** {top_type}
- **Busiest City:** {top_city}

💡 *Operations page has demand heatmaps, route analysis and city comparisons.*"""


def _driver(dfs):
    tel = dfs["telematics"]; drv = dfs["drivers"]
    avg_score = tel["safety_score"].mean()
    accidents = int(tel["accident_occurred"].sum())
    complaints= int(tel["complaint_filed"].sum())
    risky = drv[drv["behavior_profile"].isin(["poor","dangerous"])]
    idle_h = tel["idle_time_minutes"].sum() / 60
    best_id  = tel.groupby("driver_id")["safety_score"].mean().idxmax()
    worst_id = tel.groupby("driver_id")["safety_score"].mean().idxmin()
    def name(did):
        r = drv[drv["driver_id"]==did]
        return r["full_name"].values[0] if len(r) else did
    return f"""🚦 **Driver Safety**

- **Avg Safety Score:** {avg_score:.1f}/100  (target ≥ 70)
- **Accidents:** {accidents}  |  **Complaints:** {complaints}
- **High-Risk Drivers:** {len(risky)} (poor/dangerous)
- **Best Driver:** {name(best_id)}
- **Needs Coaching:** {name(worst_id)}
- **Total Idle Hours:** {idle_h:,.0f} hrs wasted

📌 *Driver Safety page has individual radar profiles and AI risk predictor.*"""


def _vehicle(dfs):
    veh = dfs["vehicles"]; maint = dfs["maintenance"]; fuel = dfs["fuel_logs"]
    sc = veh["status"].value_counts()
    return f"""🚙 **Fleet & Vehicle Health**

- **Total Vehicles:** {len(veh)}
- **Available:** {sc.get('Available',0)}  |  **On Trip:** {sc.get('On Trip',0)}
- **Under Maintenance:** {sc.get('Under Maintenance',0)}
- **Total Maintenance Cost:** {_fmt(maint['total_cost_pkr'].sum())}
- **Avg Fuel Efficiency:** {fuel['fuel_efficiency_kmpl'].mean():.1f} km/l
- **Total Fuel Spend:** {_fmt(fuel['fuel_cost_pkr'].sum())}
- **Scheduled Services Pending:** {(maint['status']=='Scheduled').sum()}

⚠️ *Fleet Health page has predictive maintenance AI and anomaly detection.*"""


def _top(dfs, question):
    tl = question.lower()
    if "driver" in tl:
        tel = dfs["telematics"]; drv = dfs["drivers"]
        s = tel.groupby("driver_id")["safety_score"].mean().reset_index()
        s = s.merge(drv[["driver_id","full_name"]], on="driver_id", how="left").nlargest(5,"safety_score")
        lines = "\n".join(f"  {i+1}. {r['full_name']} — {r['safety_score']:.1f}" for i,(_,r) in enumerate(s.iterrows()))
        return f"🏆 **Top 5 Safest Drivers**\n\n{lines}"
    if any(w in tl for w in ["vehicle","car"]):
        t = dfs["trips"]; v = dfs["vehicles"]
        tv = t[t["status"]=="Completed"].groupby("vehicle_id")["revenue_pkr"].sum().nlargest(5).reset_index()
        tv = tv.merge(v[["vehicle_id","make","model","year"]], on="vehicle_id", how="left")
        lines = "\n".join(f"  {i+1}. {r['make']} {r['model']} ({r['year']}) — {_fmt(r['revenue_pkr'])}"
                          for i,(_,r) in enumerate(tv.iterrows()))
        return f"🏆 **Top 5 Revenue Vehicles**\n\n{lines}"
    if "city" in tl:
        tc = dfs["trips"].groupby("pickup_city").size().nlargest(5)
        lines = "\n".join(f"  {i+1}. {c} — {n:,} trips" for i,(c,n) in enumerate(tc.items()))
        return f"🏙️ **Top 5 Cities**\n\n{lines}"
    tb = dfs["trips"][dfs["trips"]["status"]=="Completed"].groupby("booking_type")["revenue_pkr"].sum().nlargest(5)
    lines = "\n".join(f"  {i+1}. {b} — {_fmt(r)}" for i,(b,r) in enumerate(tb.items()))
    return f"📊 **Top 5 Booking Types by Revenue**\n\n{lines}"


def _alerts(dfs):
    veh = dfs["vehicles"]; today = pd.Timestamp("2026-07-01")
    exp_ins  = veh[veh["insurance_expiry"] < today]
    overdue  = dfs["maintenance"][dfs["maintenance"]["status"]=="Scheduled"]
    inv      = dfs["invoices"]
    outs_inv = inv[inv["outstanding_pkr"] > 0]
    risky    = dfs["drivers"][dfs["drivers"]["behavior_profile"].isin(["poor","dangerous"])]
    items = []
    if len(exp_ins):  items.append(f"🔴 **{len(exp_ins)} vehicles** with expired insurance")
    if len(risky):    items.append(f"🔴 **{len(risky)} high-risk drivers** on fleet")
    if len(overdue):  items.append(f"🟠 **{len(overdue)} maintenance jobs** pending")
    if len(outs_inv): items.append(f"🟡 **{_fmt(outs_inv['outstanding_pkr'].sum())}** overdue across {len(outs_inv):,} invoices")
    return "✅ No critical alerts." if not items else "⚠️ **Active Alerts**\n\n" + "\n".join(items)


def _kpi(dfs):
    t = dfs["trips"]; inv = dfs["invoices"]; v = dfs["vehicles"]; fuel = dfs["fuel_logs"]
    comp = t[t["status"]=="Completed"]
    fs = len(v[v["status"]!="Retired"])
    days = max(1,(t["pickup_datetime"].dt.date.max()-t["pickup_datetime"].dt.date.min()).days)
    util = min(100, comp["duration_days"].sum()/(fs*days)*100)
    rpv  = inv["total_amount_pkr"].sum()/fs if fs else 0
    cpk  = fuel["fuel_cost_pkr"].sum()/comp["distance_km"].sum() if comp["distance_km"].sum()>0 else 0
    cr   = inv["paid_amount_pkr"].sum()/inv["total_amount_pkr"].sum()*100
    return f"""📈 **Key Performance Indicators**

| KPI | Value |
|-----|-------|
| Fleet Utilisation | {util:.1f}% |
| Revenue per Vehicle | {_fmt(rpv)} |
| Avg Trip Value | {_fmt(comp['revenue_pkr'].mean())} |
| Fuel Cost per KM | PKR {cpk:.1f} |
| Collection Rate | {cr:.1f}% |
| Trip Completion Rate | {(t['status']=='Completed').mean()*100:.1f}% |
| Cancellation Rate | {(t['status']=='Cancelled').mean()*100:.1f}% |
| Avg Safety Score | {dfs['telematics']['safety_score'].mean():.1f}/100 |"""


def _help():
    return """🤖 **Soft Rent a Car AI — Powered by GPT-4o**

Ask anything in plain English. Examples:

💰 *Revenue:* "total revenue", "which fleet earns most", "collection rate"
🚗 *Trips:* "completed trips", "cancellation rate", "popular routes"
🚦 *Drivers:* "top 5 safe drivers", "accidents this year", "who needs coaching"
🚙 *Fleet:* "vehicle utilisation", "maintenance due", "fuel efficiency"
📈 *Forecasting:* "revenue next 6 months", "demand in Lahore"
⚠️ *Alerts:* "expired insurance", "overdue invoices", "high risk drivers"
📊 *KPIs:* "show all KPIs", "avg trip value"
🔍 *SQL:* "show SQL for revenue by city", "window function examples"

I'm powered by **GPT-4o** for nuanced answers! 🚀"""


# ── Main entry point ──────────────────────────────────────────────────

def chat(question: str, dfs: dict, history: list = None) -> str:
    tl = question.lower().strip()

    if any(g in tl for g in GREETINGS):
        return "👋 **Salam!** I'm your Soft Rent a Car AI assistant, powered by GPT-4o. Ask me anything about your fleet, revenue, drivers, or forecasts!"

    if any(w in tl for w in ["help", "what can", "how to", "commands"]):
        return _help()

    intents = _detect_intent(question)

    # Always try GPT-4o first
    key = _resolve_key()
    if key:
        try:
            return _openai_chat(question, dfs, history or [], key)
        except Exception as e:
            pass  # Fall through to rule-based

    # Rule-based fallback
    if "alert"   in intents: return _alerts(dfs)
    if "kpi"     in intents: return _kpi(dfs)
    if "top"     in intents: return _top(dfs, question)
    if "revenue" in intents: return _revenue(dfs)
    if "trips"   in intents: return _trips(dfs)
    if "driver"  in intents: return _driver(dfs)
    if "vehicle" in intents: return _vehicle(dfs)
    if "forecast" in intents:
        return "📈 Head to the **Forecasting** page for interactive 6-month revenue forecasts, demand prediction and dynamic pricing AI!"
    if "customer" in intents:
        c = dfs["customers"]
        return f"👥 **Customers:** {len(c):,} total | Types: {c['customer_type'].value_counts().to_dict()} | Top city: {c['city'].value_counts().index[0]}"

    return "🤔 " + _kpi(dfs) + "\n\n💬 *Try: 'show revenue', 'top drivers', 'active alerts' or 'help'*"


# ── GPT-4o backend ────────────────────────────────────────────────────

def _openai_chat(question: str, dfs: dict, history: list, api_key: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=api_key)

    inv   = dfs["invoices"]
    trips = dfs["trips"]
    tel   = dfs["telematics"]
    veh   = dfs["vehicles"]
    drv   = dfs["drivers"]

    system = f"""You are the AI assistant for **Soft Rent a Car**, a Pakistani car rental analytics platform built for data engineering, ML/AI and business intelligence.

Current fleet snapshot (July 2026):
- Vehicles: {len(veh)} total | Available: {(veh['status']=='Available').sum()} | On Trip: {(veh['status']=='On Trip').sum()}
- Trips: {len(trips):,} total | {(trips['status']=='Completed').sum():,} completed | {(trips['status']=='Cancelled').sum():,} cancelled
- Revenue: PKR {inv['total_amount_pkr'].sum():,.0f} billed | PKR {inv['paid_amount_pkr'].sum():,.0f} collected
- Avg Safety Score: {tel['safety_score'].mean():.1f}/100 | Accidents: {int(tel['accident_occurred'].sum())}
- High-risk drivers: {drv['behavior_profile'].isin(['poor','dangerous']).sum()}
- Customers: {len(dfs['customers']):,} | Fleets: {len(dfs['fleets'])}
- Top city: {trips.groupby('pickup_city').size().idxmax()}
- Avg fuel efficiency: {dfs['fuel_logs']['fuel_efficiency_kmpl'].mean():.1f} km/l

Your role:
- Answer fleet, revenue, safety, and operational questions with insight
- Use PKR for all currency
- Be concise but analytical — give numbers and context
- Use markdown for formatting (bold, tables, bullet points)
- For SQL questions, provide well-formatted, commented SQL
- If asked about trends, reference the data above
- Respond in the language the user writes in (English/Urdu)
"""

    messages = [{"role": "system", "content": system}]
    for h in (history or [])[-8:]:
        messages.append({"role": "user",      "content": h["user"]})
        messages.append({"role": "assistant", "content": h["ai"]})
    messages.append({"role": "user", "content": question})

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=800,
        temperature=0.3,
    )
    return resp.choices[0].message.content
