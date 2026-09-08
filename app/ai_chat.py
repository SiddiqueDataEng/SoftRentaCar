"""
AI Chat engine for Soft Rent a Car.
Uses a rule-based NLP + pandas query layer (no external API key required).
Optionally upgrades to OpenAI GPT-4o when OPENAI_API_KEY is set.
"""

import re
import os
import json
import datetime
import numpy as np
import pandas as pd
from typing import Optional

# ── Intent definitions ────────────────────────────────────────────────

INTENTS = {
    "revenue":      ["revenue", "income", "billing", "invoice", "earned", "collected", "pkr", "money"],
    "trips":        ["trip", "booking", "ride", "rental", "journey", "travel"],
    "driver":       ["driver", "driving", "behavior", "behaviour", "safety", "accident", "brake", "speed"],
    "vehicle":      ["vehicle", "car", "fleet", "maintenance", "fuel", "efficiency", "status"],
    "customer":     ["customer", "client", "renter", "passenger"],
    "forecast":     ["forecast", "predict", "next month", "future", "upcoming", "trend"],
    "top":          ["top", "best", "highest", "most", "lowest", "worst", "ranking"],
    "alert":        ["alert", "issue", "problem", "risk", "overdue", "expired"],
    "city":         ["city", "islamabad", "lahore", "karachi", "rawalpindi", "peshawar", "murree"],
    "kpi":          ["kpi", "utilisation", "utilization", "rate", "occupancy", "performance"],
    "comparison":   ["compare", "comparison", "vs", "versus", "difference", "better"],
    "help":         ["help", "what can you", "what do you", "capabilities", "commands"],
}

GREETINGS = ["hello", "hi", "hey", "salam", "assalamu", "good morning", "good evening", "good afternoon"]


def _detect_intent(text: str) -> list[str]:
    text_lower = text.lower()
    found = []
    for intent, keywords in INTENTS.items():
        if any(k in text_lower for k in keywords):
            found.append(intent)
    return found if found else ["general"]


def _fmt_pkr(v: float) -> str:
    if v >= 1_000_000_000:
        return f"PKR {v/1e9:.2f}B"
    if v >= 1_000_000:
        return f"PKR {v/1e6:.1f}M"
    if v >= 1_000:
        return f"PKR {v/1e3:.1f}K"
    return f"PKR {v:,.0f}"


# ── Query functions ────────────────────────────────────────────────────

def _answer_revenue(dfs: dict, question: str) -> str:
    inv = dfs["invoices"]
    trips = dfs["trips"]

    total_billed    = inv["total_amount_pkr"].sum()
    total_collected = inv["paid_amount_pkr"].sum()
    outstanding     = total_billed - total_collected

    # This month
    latest_month = inv["invoice_date"].dt.to_period("M").max()
    this_month   = inv[inv["invoice_date"].dt.to_period("M") == latest_month]
    month_rev    = this_month["total_amount_pkr"].sum()

    # By fleet
    fleet_rev = inv.merge(dfs["fleets"][["fleet_id","fleet_name"]], on="fleet_id", how="left") \
                   .groupby("fleet_name")["total_amount_pkr"].sum().sort_values(ascending=False)
    top_fleet = fleet_rev.index[0] if len(fleet_rev) else "N/A"

    answer = f"""
📊 **Revenue Summary**

- **Total Billed:** {_fmt_pkr(total_billed)}
- **Total Collected:** {_fmt_pkr(total_collected)} ({total_collected/total_billed*100:.1f}% collection rate)
- **Outstanding:** {_fmt_pkr(outstanding)}
- **{str(latest_month)} Revenue:** {_fmt_pkr(month_rev)}
- **Top Fleet by Revenue:** {top_fleet} — {_fmt_pkr(fleet_rev.iloc[0])}

💡 *Tip: Head to the Finance Dashboard for month-by-month trends and payment breakdowns.*
"""
    return answer.strip()


def _answer_trips(dfs: dict, question: str) -> str:
    trips = dfs["trips"]
    total       = len(trips)
    completed   = (trips["status"] == "Completed").sum()
    cancelled   = (trips["status"] == "Cancelled").sum()
    avg_km      = trips[trips["status"] == "Completed"]["distance_km"].mean()
    avg_fare    = trips[trips["status"] == "Completed"]["revenue_pkr"].mean()
    top_type    = trips.groupby("booking_type").size().idxmax()
    top_city    = trips.groupby("pickup_city").size().idxmax()

    answer = f"""
🚗 **Trips & Bookings Summary**

- **Total Bookings:** {total:,}
- **Completed:** {completed:,} ({completed/total*100:.1f}%)
- **Cancelled:** {cancelled:,} ({cancelled/total*100:.1f}%)
- **Avg Distance (completed):** {avg_km:.1f} km
- **Avg Fare (completed):** {_fmt_pkr(avg_fare)}
- **Most Popular Booking Type:** {top_type}
- **Busiest City:** {top_city}

💡 *See the Operations page for demand heatmaps and booking trends.*
"""
    return answer.strip()


def _answer_driver(dfs: dict, question: str) -> str:
    tel = dfs["telematics"]
    drv = dfs["drivers"]

    avg_score = tel["safety_score"].mean()
    accidents = int(tel["accident_occurred"].sum())
    complaints = int(tel["complaint_filed"].sum())
    best_driver_id = tel.groupby("driver_id")["safety_score"].mean().idxmax()
    worst_driver_id = tel.groupby("driver_id")["safety_score"].mean().idxmin()

    def driver_name(driver_id):
        row = drv[drv["driver_id"] == driver_id]
        return row["full_name"].values[0] if len(row) else driver_id

    risky = drv[drv["behavior_profile"].isin(["poor", "dangerous"])]
    idle_waste = tel["idle_time_minutes"].sum() / 60  # hours

    answer = f"""
🚦 **Driver Behavior & Safety**

- **Avg Fleet Safety Score:** {avg_score:.1f} / 100
- **Total Accident Events:** {accidents}
- **Customer Complaints:** {complaints}
- **Best Performing Driver:** {driver_name(best_driver_id)}
- **Needs Attention:** {driver_name(worst_driver_id)}
- **High-Risk Drivers (poor/dangerous profile):** {len(risky)}
- **Total Idle Engine Time:** {idle_waste:,.0f} hours wasted

📌 *Driver coaching recommended for {len(risky)} drivers. Use the Driver Analytics page for full radar profiles.*
"""
    return answer.strip()


def _answer_vehicle(dfs: dict, question: str) -> str:
    veh   = dfs["vehicles"]
    maint = dfs["maintenance"]
    fuel  = dfs["fuel_logs"]

    status_counts = veh["status"].value_counts()
    total_maint   = maint["total_cost_pkr"].sum()
    avg_fuel_eff  = fuel["fuel_efficiency_kmpl"].mean()
    total_fuel_cost = fuel["fuel_cost_pkr"].sum()
    overdue = maint[maint["status"] == "Scheduled"]

    answer = f"""
🚙 **Fleet & Vehicle Health**

- **Total Vehicles:** {len(veh)}
- **Available:** {status_counts.get('Available', 0)}
- **On Trip:** {status_counts.get('On Trip', 0)}
- **Under Maintenance:** {status_counts.get('Under Maintenance', 0)}
- **Total Maintenance Cost:** {_fmt_pkr(total_maint)}
- **Avg Fuel Efficiency:** {avg_fuel_eff:.1f} km/l
- **Total Fuel Expenditure:** {_fmt_pkr(total_fuel_cost)}
- **Scheduled / Overdue Services:** {len(overdue)}

⚠️ *{len(overdue)} vehicles have scheduled maintenance pending. Check the Fleet Health page.*
"""
    return answer.strip()


def _answer_top(dfs: dict, question: str) -> str:
    text_lower = question.lower()

    if "driver" in text_lower:
        tel = dfs["telematics"]
        drv = dfs["drivers"]
        summary = tel.groupby("driver_id")["safety_score"].mean().reset_index()
        summary = summary.merge(drv[["driver_id","full_name","behavior_profile"]], on="driver_id", how="left")
        top5 = summary.nlargest(5, "safety_score")
        lines = "\n".join([f"  {i+1}. {r['full_name']} — Score: {r['avg_safety_score']:.1f}" if 'avg_safety_score' in r else
                           f"  {i+1}. {r['full_name']} — Score: {r['safety_score']:.1f}"
                           for i, r in top5.iterrows()])
        return f"🏆 **Top 5 Safest Drivers**\n\n{lines}"

    if "vehicle" in text_lower or "car" in text_lower:
        trips = dfs["trips"]
        veh   = dfs["vehicles"]
        top_v = trips[trips["status"]=="Completed"].groupby("vehicle_id")["revenue_pkr"].sum().nlargest(5).reset_index()
        top_v = top_v.merge(veh[["vehicle_id","make","model","year"]], on="vehicle_id", how="left")
        lines = "\n".join([f"  {i+1}. {r['make']} {r['model']} ({r['year']}) — {_fmt_pkr(r['revenue_pkr'])}"
                           for i, (_, r) in enumerate(top_v.iterrows())])
        return f"🏆 **Top 5 Revenue-Generating Vehicles**\n\n{lines}"

    if "city" in text_lower:
        trips = dfs["trips"]
        top_c = trips.groupby("pickup_city").size().nlargest(5)
        lines = "\n".join([f"  {i+1}. {city} — {cnt:,} trips" for i, (city, cnt) in enumerate(top_c.items())])
        return f"🏙️ **Top 5 Busiest Cities**\n\n{lines}"

    # Default: top booking types
    trips = dfs["trips"]
    top_bt = trips[trips["status"]=="Completed"].groupby("booking_type")["revenue_pkr"].sum().nlargest(5)
    lines = "\n".join([f"  {i+1}. {bt} — {_fmt_pkr(rev)}" for i, (bt, rev) in enumerate(top_bt.items())])
    return f"📊 **Top 5 Booking Types by Revenue**\n\n{lines}"


def _answer_alert(dfs: dict, question: str) -> str:
    alerts = []

    # Expired insurance
    veh = dfs["vehicles"]
    today = pd.Timestamp("2026-07-01")
    veh["insurance_expiry"] = pd.to_datetime(veh["insurance_expiry"], errors="coerce")
    expired_ins = veh[veh["insurance_expiry"] < today]
    if len(expired_ins):
        alerts.append(f"🔴 **{len(expired_ins)} vehicles** have expired insurance!")

    # Overdue maintenance
    overdue_m = dfs["maintenance"][dfs["maintenance"]["status"] == "Scheduled"]
    if len(overdue_m):
        alerts.append(f"🟠 **{len(overdue_m)} scheduled maintenance jobs** pending.")

    # Outstanding invoices
    inv = dfs["invoices"]
    outstanding = inv[inv["outstanding_pkr"] > 0]
    total_outstanding = outstanding["outstanding_pkr"].sum()
    if total_outstanding > 0:
        alerts.append(f"🟡 **{len(outstanding):,} invoices** have outstanding balance: {_fmt_pkr(total_outstanding)}")

    # Dangerous drivers
    risky = dfs["drivers"][dfs["drivers"]["behavior_profile"].isin(["poor", "dangerous"])]
    if len(risky):
        alerts.append(f"🔴 **{len(risky)} high-risk drivers** flagged (poor/dangerous profile).")

    if not alerts:
        return "✅ **No critical alerts** found. Fleet is operating normally."

    return "⚠️ **Active Alerts**\n\n" + "\n".join(alerts)


def _answer_kpi(dfs: dict, question: str) -> str:
    trips    = dfs["trips"]
    inv      = dfs["invoices"]
    vehicles = dfs["vehicles"]
    fuel     = dfs["fuel_logs"]

    completed = trips[trips["status"] == "Completed"]
    fleet_size = len(vehicles[vehicles["status"] != "Retired"])
    trip_days  = completed["duration_days"].sum()
    util_rate  = min(100, trip_days / (fleet_size * 30 * ((2026-2022)*12)) * 100) if fleet_size > 0 else 0

    rev_per_vehicle = inv["total_amount_pkr"].sum() / fleet_size if fleet_size else 0
    cost_per_km     = fuel["fuel_cost_pkr"].sum() / completed["distance_km"].sum() if completed["distance_km"].sum() > 0 else 0
    avg_trip_value  = completed["revenue_pkr"].mean()

    answer = f"""
📈 **Key Performance Indicators**

| KPI | Value |
|-----|-------|
| Fleet Utilisation | {util_rate:.1f}% |
| Revenue per Vehicle (lifetime) | {_fmt_pkr(rev_per_vehicle)} |
| Avg Trip Value | {_fmt_pkr(avg_trip_value)} |
| Fuel Cost per KM | PKR {cost_per_km:.1f} |
| Collection Rate | {inv['paid_amount_pkr'].sum()/inv['total_amount_pkr'].sum()*100:.1f}% |
| Trip Completion Rate | {(trips['status']=='Completed').mean()*100:.1f}% |
| Cancellation Rate | {(trips['status']=='Cancelled').mean()*100:.1f}% |
"""
    return answer.strip()


def _answer_help() -> str:
    return """
🤖 **Soft Rent a Car AI Assistant**

I can answer questions about your entire fleet operation. Try asking:

**Revenue & Finance**
- "What's our total revenue this year?"
- "Which fleet earns the most?"

**Operations & Trips**
- "How many trips were completed?"
- "What is the most popular booking type?"

**Driver Safety**
- "Who are the top 5 safest drivers?"
- "How many accidents occurred?"

**Fleet & Vehicles**
- "What is our fleet utilisation rate?"
- "Which vehicles need maintenance?"

**Forecasting**
- "Forecast revenue for next 6 months"

**Alerts**
- "Show me all active alerts"
- "Any expired insurance?"

**KPIs**
- "Show me all KPIs"
- "What is our collection rate?"

*Type any question in natural language — I'll understand!* 🚗
"""


# ── Main chat dispatcher ───────────────────────────────────────────────

def chat(question: str, dfs: dict, history: list = None) -> str:
    """
    Main entry point. Routes question to the right handler.
    Falls back to GPT-4o if OPENAI_API_KEY is set in env.
    """
    text_lower = question.lower().strip()

    # Greetings
    if any(g in text_lower for g in GREETINGS):
        return "👋 Salam! I'm your **Soft Rent a Car** AI Assistant. Ask me anything about your fleet, revenue, drivers, or forecasts!"

    # Help
    if "help" in text_lower or "what can" in text_lower or "how do" in text_lower:
        return _answer_help()

    intents = _detect_intent(question)

    # Try OpenAI GPT if key is available
    api_key = os.getenv("OPENAI_API_KEY", "")
    if api_key and len(api_key) > 10:
        try:
            return _openai_chat(question, dfs, history or [], api_key)
        except Exception:
            pass  # Fall back to rule-based

    # Rule-based routing
    if "alert" in intents:
        return _answer_alert(dfs, question)
    if "kpi" in intents:
        return _answer_kpi(dfs, question)
    if "top" in intents:
        return _answer_top(dfs, question)
    if "revenue" in intents:
        return _answer_revenue(dfs, question)
    if "trips" in intents:
        return _answer_trips(dfs, question)
    if "driver" in intents:
        return _answer_driver(dfs, question)
    if "vehicle" in intents or "fleet" in intents:
        return _answer_vehicle(dfs, question)
    if "forecast" in intents:
        return "📈 Head to the **Forecasting** page for interactive demand and revenue forecasts with confidence intervals!"
    if "customer" in intents:
        cust = dfs["customers"]
        types = cust["customer_type"].value_counts().to_dict()
        cities = cust["city"].value_counts().head(3).to_dict()
        return f"👥 **Customer Base**\n\n- Total Customers: {len(cust):,}\n- Types: {types}\n- Top Cities: {cities}"

    # Fallback with context
    return (
        "🤔 I didn't fully understand that. Here's what I can tell you:\n\n"
        + _answer_kpi(dfs, question)
        + "\n\n💬 *Try: 'show revenue', 'top drivers', 'active alerts', 'fleet status', or 'help'*"
    )


def _openai_chat(question: str, dfs: dict, history: list, api_key: str) -> str:
    """GPT-4o powered chat with fleet context injected as system prompt."""
    try:
        from openai import OpenAI
    except ImportError:
        raise RuntimeError("openai package not installed")

    client = OpenAI(api_key=api_key)

    # Build a compact context string
    inv    = dfs["invoices"]
    trips  = dfs["trips"]
    tel    = dfs["telematics"]

    context = f"""
You are the AI assistant for Soft Rent a Car, a Pakistani car rental analytics platform.
Current data snapshot (as of July 2026):
- Total vehicles: {len(dfs['vehicles'])}
- Total trips: {len(trips):,} ({(trips['status']=='Completed').sum():,} completed)
- Total billed revenue: PKR {inv['total_amount_pkr'].sum():,.0f}
- Avg safety score: {tel['safety_score'].mean():.1f}/100
- Accidents: {int(tel['accident_occurred'].sum())}
- Total customers: {len(dfs['customers']):,}
- Active fleets: {len(dfs['fleets'])}
Respond concisely in markdown. Use PKR for currency. Be professional but friendly.
"""

    messages = [{"role": "system", "content": context}]
    for h in history[-6:]:  # last 3 turns
        messages.append({"role": "user",      "content": h["user"]})
        messages.append({"role": "assistant", "content": h["ai"]})
    messages.append({"role": "user", "content": question})

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=600,
        temperature=0.4,
    )
    return response.choices[0].message.content
