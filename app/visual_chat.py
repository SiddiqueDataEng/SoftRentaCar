"""
Visual Chat Engine — Soft Rent a Car
Detects which questions warrant charts/tables and returns
(text_answer, visual_payload) where visual_payload is a dict
describing what to render, or None if no visual is needed.

visual_payload keys:
    type        : "bar" | "line" | "area" | "horizontal_bar" |
                  "grouped_bar" | "pie" | "table" | "kpi_cards" |
                  "waterfall" | "scatter"
    title       : chart title string
    df          : pandas DataFrame with the data
    x           : column name for x-axis  (charts)
    y           : column name(s) for y-axis — str or list
    color_col   : optional column for colour grouping
    fmt_pkr     : list of column names to format as PKR
    insight     : one-line insight string shown below chart
"""

import re
import pandas as pd
import numpy as np
from app.ai_chat import chat as _text_chat, _fmt, _detect_intent


# ── Visual intent patterns ─────────────────────────────────────────────
# Each entry: (regex pattern, handler function name)
VISUAL_PATTERNS = [
    # Top N vehicles / cars
    (r"top\s*(\d+)?\s*(vehicle|car|auto)",           "top_vehicles"),
    (r"best\s*(performing)?\s*(vehicle|car)",         "top_vehicles"),
    (r"highest\s*revenue\s*(vehicle|car)",            "top_vehicles"),

    # Month comparison
    (r"(current|this)\s*month.*(last|prev)",          "month_comparison"),
    (r"(last|prev)\s*month.*vs",                      "month_comparison"),
    (r"month\s*(over|on)\s*month",                    "month_comparison"),
    (r"(current|this)\s*month",                       "current_month"),
    (r"compare.*month",                               "month_comparison"),
    (r"year.*same.*month",                            "yoy_month"),
    (r"same.*month.*last.*year",                      "yoy_month"),

    # Revenue trends
    (r"revenue\s*(trend|over\s*time|monthly|growth)", "revenue_trend"),
    (r"monthly\s*revenue",                            "revenue_trend"),
    (r"revenue\s*by\s*(month|year)",                  "revenue_trend"),

    # Top drivers
    (r"top\s*(\d+)?\s*driver",                       "top_drivers"),
    (r"best\s*(performing)?\s*driver",                "top_drivers"),
    (r"safest\s*driver",                              "top_drivers"),
    (r"worst\s*(driver|performing)",                  "worst_drivers"),
    (r"risky\s*driver",                               "worst_drivers"),

    # City demand
    (r"(city|cities).*(demand|trip|revenue|busiest)", "city_demand"),
    (r"(demand|trip).*(city|cities)",                 "city_demand"),
    (r"busiest\s*cit",                                "city_demand"),

    # Booking type
    (r"booking\s*type",                               "booking_type"),
    (r"type\s*of\s*booking",                          "booking_type"),
    (r"popular\s*(booking|trip|service)",             "booking_type"),

    # Fleet utilisation
    (r"utilis(a|e)tion",                              "utilisation"),
    (r"fleet\s*(usage|occupancy|performance)",        "utilisation"),

    # Fuel
    (r"fuel\s*(efficiency|consumption|cost)",         "fuel_efficiency"),
    (r"fuel",                                          "fuel_efficiency"),
    (r"efficiency\s*(trend|by)",                       "fuel_efficiency"),

    # Maintenance
    (r"maintenance\s*(cost|spend|type)",              "maintenance_cost"),
    (r"service\s*(cost|spend)",                       "maintenance_cost"),

    # Revenue by fleet
    (r"fleet\s*(revenue|earning|performance)",        "fleet_revenue"),
    (r"revenue\s*by\s*fleet",                         "fleet_revenue"),

    # KPIs
    (r"\bkpi\b",                                      "kpi_cards"),
    (r"key\s*performance",                            "kpi_cards"),
    (r"all\s*(metric|kpi|indicator)",                 "kpi_cards"),

    # Safety scores
    (r"safety\s*(score|rating|summary)",              "safety_summary"),
    (r"driver\s*(safety|behavior|behaviour)",         "safety_summary"),

    # Customer segments
    (r"customer\s*(segment|type|breakdown|split)",    "customer_segments"),
    (r"customer\s*insigh",                            "customer_segments"),

    # Payment methods
    (r"payment\s*(method|mode|channel)",              "payment_methods"),
    (r"how.*(paid|pay)",                              "payment_methods"),
]


def _match_visual(question: str) -> str | None:
    """Return handler name if question warrants a visual, else None."""
    tl = question.lower()
    for pattern, handler in VISUAL_PATTERNS:
        if re.search(pattern, tl):
            return handler
    return None


# ── Data builders ──────────────────────────────────────────────────────

def _top_vehicles(dfs: dict, question: str) -> dict:
    n = 10
    m = re.search(r"top\s*(\d+)", question.lower())
    if m:
        n = min(int(m.group(1)), 20)

    t  = dfs["trips"]
    v  = dfs["vehicles"]
    vt = dfs["vehicle_types"]

    stats = (
        t[t["status"] == "Completed"]
        .groupby("vehicle_id")
        .agg(
            revenue=("revenue_pkr", "sum"),
            trips=("trip_id", "count"),
            avg_fare=("revenue_pkr", "mean"),
            avg_km=("distance_km", "mean"),
        )
        .reset_index()
        .nlargest(n, "revenue")
    )
    stats = (
        stats
        .merge(v[["vehicle_id", "make", "model", "year", "vehicle_type_id"]], on="vehicle_id", how="left")
        .merge(vt[["vehicle_type_id", "category"]], on="vehicle_type_id", how="left")
    )
    stats["label"]   = stats["make"] + " " + stats["model"] + " (" + stats["year"].astype(str) + ")"
    stats["revenue"] = stats["revenue"].round(0)
    stats["avg_fare"]= stats["avg_fare"].round(0)

    return {
        "type":    "horizontal_bar",
        "title":   f"Top {n} Vehicles by Revenue",
        "df":      stats[["label", "revenue", "trips", "avg_fare", "category"]],
        "x":       "revenue",
        "y":       "label",
        "fmt_pkr": ["revenue", "avg_fare"],
        "insight": f"Top vehicle: {stats['label'].iloc[0]} — {_fmt(stats['revenue'].iloc[0])}",
    }


def _current_month(dfs: dict, question: str) -> dict:
    inv = dfs["invoices"].copy()
    inv["month"] = inv["invoice_date"].dt.to_period("M")
    latest = inv["month"].max()

    cur = inv[inv["month"] == latest]
    summary = pd.DataFrame([{
        "Metric":  "Billed",
        "Amount":  cur["total_amount_pkr"].sum(),
    }, {
        "Metric":  "Collected",
        "Amount":  cur["paid_amount_pkr"].sum(),
    }, {
        "Metric":  "Outstanding",
        "Amount":  cur["outstanding_pkr"].sum(),
    }])

    return {
        "type":    "bar",
        "title":   f"Revenue — {latest}",
        "df":      summary,
        "x":       "Metric",
        "y":       "Amount",
        "fmt_pkr": ["Amount"],
        "insight": f"{latest}: PKR {cur['total_amount_pkr'].sum()/1e6:.1f}M billed, {cur['paid_amount_pkr'].sum()/cur['total_amount_pkr'].sum()*100:.1f}% collected",
    }


def _month_comparison(dfs: dict, question: str) -> dict:
    inv = dfs["invoices"].copy()
    inv["month"] = inv["invoice_date"].dt.to_period("M")
    monthly = (
        inv.groupby("month")
        .agg(billed=("total_amount_pkr", "sum"), collected=("paid_amount_pkr", "sum"))
        .reset_index()
        .sort_values("month")
    )
    monthly["month_str"] = monthly["month"].astype(str)
    monthly["mom_growth"] = monthly["billed"].pct_change().mul(100).round(2)
    last12 = monthly.tail(12).copy()

    return {
        "type":    "grouped_bar",
        "title":   "Month-over-Month Revenue Comparison",
        "df":      last12,
        "x":       "month_str",
        "y":       ["billed", "collected"],
        "fmt_pkr": ["billed", "collected"],
        "insight": f"Latest MoM growth: {last12['mom_growth'].iloc[-1]:+.1f}%",
    }


def _yoy_month(dfs: dict, question: str) -> dict:
    inv = dfs["invoices"].copy()
    inv["year"]  = inv["invoice_date"].dt.year
    inv["month_num"] = inv["invoice_date"].dt.month

    # Current month number
    latest_month = inv["invoice_date"].dt.month.iloc[-1]

    same_months = inv[inv["month_num"] == latest_month].copy()
    yoy = (
        same_months.groupby("year")
        .agg(billed=("total_amount_pkr", "sum"), collected=("paid_amount_pkr", "sum"))
        .reset_index()
        .sort_values("year")
    )
    yoy["year_str"] = yoy["year"].astype(str)
    yoy["yoy_growth"] = yoy["billed"].pct_change().mul(100).round(2)

    mn = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
          7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}
    month_name = mn.get(latest_month, "")

    return {
        "type":    "grouped_bar",
        "title":   f"Year-over-Year: {month_name} Revenue Across All Years",
        "df":      yoy,
        "x":       "year_str",
        "y":       ["billed", "collected"],
        "fmt_pkr": ["billed", "collected"],
        "insight": f"YoY growth last year: {yoy['yoy_growth'].iloc[-1]:+.1f}%",
    }


def _revenue_trend(dfs: dict, question: str) -> dict:
    inv = dfs["invoices"].copy()
    inv["month"] = inv["invoice_date"].dt.to_period("M")
    monthly = (
        inv.groupby("month")
        .agg(billed=("total_amount_pkr", "sum"), collected=("paid_amount_pkr", "sum"))
        .reset_index()
        .sort_values("month")
    )
    monthly["month_str"]  = monthly["month"].astype(str)
    monthly["outstanding"] = monthly["billed"] - monthly["collected"]
    monthly["rolling_3m"]  = monthly["billed"].rolling(3).mean().round(0)

    return {
        "type":    "area",
        "title":   "Monthly Revenue Trend",
        "df":      monthly,
        "x":       "month_str",
        "y":       ["billed", "collected"],
        "fmt_pkr": ["billed", "collected"],
        "insight": f"Peak month: {monthly.loc[monthly['billed'].idxmax(),'month_str']} — {_fmt(monthly['billed'].max())}",
    }


def _top_drivers(dfs: dict, question: str) -> dict:
    n = 10
    m = re.search(r"top\s*(\d+)", question.lower())
    if m:
        n = min(int(m.group(1)), 20)

    tel = dfs["telematics"]
    drv = dfs["drivers"]
    summary = (
        tel.groupby("driver_id")
        .agg(
            avg_score=("safety_score", "mean"),
            trips=("trip_id", "count"),
            accidents=("accident_occurred", "sum"),
            avg_rating=("customer_rating", "mean"),
        )
        .reset_index()
        .merge(drv[["driver_id", "full_name", "behavior_profile"]], on="driver_id", how="left")
        .nlargest(n, "avg_score")
    )
    summary["avg_score"]  = summary["avg_score"].round(1)
    summary["avg_rating"] = summary["avg_rating"].round(2)

    return {
        "type":    "horizontal_bar",
        "title":   f"Top {n} Drivers by Safety Score",
        "df":      summary[["full_name", "avg_score", "trips", "accidents", "avg_rating", "behavior_profile"]],
        "x":       "avg_score",
        "y":       "full_name",
        "fmt_pkr": [],
        "insight": f"Best driver: {summary['full_name'].iloc[0]} — score {summary['avg_score'].iloc[0]}",
    }


def _worst_drivers(dfs: dict, question: str) -> dict:
    n = 10
    m = re.search(r"(\d+)", question.lower())
    if m:
        n = min(int(m.group(1)), 20)

    tel = dfs["telematics"]
    drv = dfs["drivers"]
    summary = (
        tel.groupby("driver_id")
        .agg(
            avg_score=("safety_score", "mean"),
            trips=("trip_id", "count"),
            accidents=("accident_occurred", "sum"),
            harsh_brakes=("harsh_brake_events", "sum"),
        )
        .reset_index()
        .merge(drv[["driver_id", "full_name", "behavior_profile"]], on="driver_id", how="left")
        .nsmallest(n, "avg_score")
    )
    summary["avg_score"] = summary["avg_score"].round(1)

    return {
        "type":    "horizontal_bar",
        "title":   f"Bottom {n} Drivers — Needs Coaching",
        "df":      summary[["full_name", "avg_score", "trips", "accidents", "harsh_brakes", "behavior_profile"]],
        "x":       "avg_score",
        "y":       "full_name",
        "fmt_pkr": [],
        "insight": f"Lowest score: {summary['full_name'].iloc[0]} — {summary['avg_score'].iloc[0]}/100",
    }


def _city_demand(dfs: dict, question: str) -> dict:
    t = dfs["trips"]
    comp = t[t["status"] == "Completed"]
    g = (
        comp.groupby("pickup_city")
        .agg(trips=("trip_id", "count"), revenue=("revenue_pkr", "sum"), avg_fare=("revenue_pkr", "mean"))
        .reset_index()
        .sort_values("revenue", ascending=False)
        .head(12)
    )
    g["revenue"]  = g["revenue"].round(0)
    g["avg_fare"] = g["avg_fare"].round(0)

    return {
        "type":    "grouped_bar",
        "title":   "City Demand — Trips & Revenue",
        "df":      g,
        "x":       "pickup_city",
        "y":       ["trips", "revenue"],
        "fmt_pkr": ["revenue", "avg_fare"],
        "insight": f"Top city: {g['pickup_city'].iloc[0]} — {g['trips'].iloc[0]:,} trips, {_fmt(g['revenue'].iloc[0])}",
    }


def _booking_type(dfs: dict, question: str) -> dict:
    t = dfs["trips"]
    comp = t[t["status"] == "Completed"]
    g = (
        comp.groupby("booking_type")
        .agg(trips=("trip_id", "count"), revenue=("revenue_pkr", "sum"), avg_fare=("revenue_pkr", "mean"))
        .reset_index()
        .sort_values("revenue", ascending=False)
    )
    g["revenue"]  = g["revenue"].round(0)
    g["avg_fare"] = g["avg_fare"].round(0)

    return {
        "type":    "grouped_bar",
        "title":   "Booking Type — Revenue & Volume",
        "df":      g,
        "x":       "booking_type",
        "y":       ["revenue", "trips"],
        "fmt_pkr": ["revenue", "avg_fare"],
        "insight": f"Top type: {g['booking_type'].iloc[0]} — {_fmt(g['revenue'].iloc[0])}",
    }


def _utilisation(dfs: dict, question: str) -> dict:
    trips = dfs["trips"]
    veh   = dfs["vehicles"]
    trips["pickup_month"] = trips["pickup_datetime"].dt.to_period("M")
    comp = trips[trips["status"] == "Completed"]
    monthly = (
        comp.groupby("pickup_month")["duration_days"]
        .sum()
        .reset_index()
    )
    fleet_size = len(veh[veh["status"] != "Retired"])
    monthly["util_pct"] = (monthly["duration_days"] / (fleet_size * 30) * 100).clip(0, 100).round(2)
    monthly["month_str"] = monthly["pickup_month"].astype(str)

    return {
        "type":    "area",
        "title":   "Monthly Fleet Utilisation %",
        "df":      monthly,
        "x":       "month_str",
        "y":       "util_pct",
        "fmt_pkr": [],
        "insight": f"Avg utilisation: {monthly['util_pct'].mean():.1f}% | Peak: {monthly['util_pct'].max():.1f}%",
    }


def _fuel_efficiency(dfs: dict, question: str) -> dict:
    fuel = dfs["fuel_logs"]
    veh  = dfs["vehicles"]
    g = (
        fuel.merge(veh[["vehicle_id", "make", "fuel_type"]], on="vehicle_id", how="left")
        .groupby(["fill_month", "fuel_type"])
        .agg(avg_eff=("fuel_efficiency_kmpl", "mean"), total_cost=("fuel_cost_pkr", "sum"))
        .reset_index()
        .sort_values("fill_month")
    )

    monthly = (
        fuel.groupby("fill_month")
        .agg(avg_eff=("fuel_efficiency_kmpl", "mean"), total_cost=("fuel_cost_pkr", "sum"))
        .reset_index()
        .sort_values("fill_month")
    )
    monthly["avg_eff"]    = monthly["avg_eff"].round(2)
    monthly["total_cost"] = monthly["total_cost"].round(0)

    return {
        "type":    "area",
        "title":   "Monthly Fuel Efficiency (km/l) & Cost",
        "df":      monthly,
        "x":       "fill_month",
        "y":       ["avg_eff", "total_cost"],
        "fmt_pkr": ["total_cost"],
        "insight": f"Avg efficiency: {monthly['avg_eff'].mean():.2f} km/l | Total spend: {_fmt(monthly['total_cost'].sum())}",
    }


def _maintenance_cost(dfs: dict, question: str) -> dict:
    maint = dfs["maintenance"]
    g = (
        maint.groupby("maintenance_type")["total_cost_pkr"]
        .sum()
        .reset_index()
        .sort_values("total_cost_pkr", ascending=False)
        .head(12)
    )
    g["total_cost_pkr"] = g["total_cost_pkr"].round(0)

    return {
        "type":    "horizontal_bar",
        "title":   "Maintenance Spend by Type",
        "df":      g,
        "x":       "total_cost_pkr",
        "y":       "maintenance_type",
        "fmt_pkr": ["total_cost_pkr"],
        "insight": f"Highest cost: {g['maintenance_type'].iloc[0]} — {_fmt(g['total_cost_pkr'].iloc[0])}",
    }


def _fleet_revenue(dfs: dict, question: str) -> dict:
    inv    = dfs["invoices"]
    fleets = dfs["fleets"]
    g = (
        inv.merge(fleets[["fleet_id", "fleet_name"]], on="fleet_id", how="left")
        .groupby("fleet_name")
        .agg(billed=("total_amount_pkr", "sum"), collected=("paid_amount_pkr", "sum"),
             invoices=("invoice_id", "count"))
        .reset_index()
        .sort_values("billed", ascending=False)
    )
    g["billed"]    = g["billed"].round(0)
    g["collected"] = g["collected"].round(0)
    g["collection_rate"] = (g["collected"] / g["billed"] * 100).round(1)

    return {
        "type":    "grouped_bar",
        "title":   "Revenue by Fleet",
        "df":      g,
        "x":       "fleet_name",
        "y":       ["billed", "collected"],
        "fmt_pkr": ["billed", "collected"],
        "insight": f"Top fleet: {g['fleet_name'].iloc[0]} — {_fmt(g['billed'].iloc[0])}",
    }


def _kpi_cards(dfs: dict, question: str) -> dict:
    t    = dfs["trips"]
    inv  = dfs["invoices"]
    v    = dfs["vehicles"]
    fuel = dfs["fuel_logs"]
    tel  = dfs["telematics"]
    comp = t[t["status"] == "Completed"]
    fs   = len(v[v["status"] != "Retired"])
    days = max(1, (t["pickup_datetime"].dt.date.max() - t["pickup_datetime"].dt.date.min()).days)

    kpis = pd.DataFrame([
        {"KPI": "Total Revenue",          "Value": _fmt(inv["total_amount_pkr"].sum()),                    "Raw": inv["total_amount_pkr"].sum()},
        {"KPI": "Collection Rate",        "Value": f"{inv['paid_amount_pkr'].sum()/inv['total_amount_pkr'].sum()*100:.1f}%", "Raw": 0},
        {"KPI": "Fleet Utilisation",      "Value": f"{min(100,comp['duration_days'].sum()/(fs*days)*100):.1f}%",             "Raw": 0},
        {"KPI": "Completed Trips",        "Value": f"{len(comp):,}",                                       "Raw": len(comp)},
        {"KPI": "Avg Trip Value",         "Value": _fmt(comp["revenue_pkr"].mean()),                       "Raw": comp["revenue_pkr"].mean()},
        {"KPI": "Avg Safety Score",       "Value": f"{tel['safety_score'].mean():.1f}/100",                "Raw": tel["safety_score"].mean()},
        {"KPI": "Avg Fuel Efficiency",    "Value": f"{fuel['fuel_efficiency_kmpl'].mean():.1f} km/l",      "Raw": fuel["fuel_efficiency_kmpl"].mean()},
        {"KPI": "Total Fuel Cost",        "Value": _fmt(fuel["fuel_cost_pkr"].sum()),                      "Raw": fuel["fuel_cost_pkr"].sum()},
        {"KPI": "Active Vehicles",        "Value": str(fs),                                                "Raw": fs},
        {"KPI": "Cancellation Rate",      "Value": f"{(t['status']=='Cancelled').mean()*100:.1f}%",        "Raw": 0},
    ])

    return {
        "type":    "kpi_table",
        "title":   "Key Performance Indicators",
        "df":      kpis[["KPI", "Value"]],
        "x":       "KPI",
        "y":       "Value",
        "fmt_pkr": [],
        "insight": "",
    }


def _safety_summary(dfs: dict, question: str) -> dict:
    tel = dfs["telematics"]
    drv = dfs["drivers"]
    summary = (
        tel.groupby("driver_id")
        .agg(avg_score=("safety_score", "mean"), trips=("trip_id", "count"),
             accidents=("accident_occurred", "sum"), complaints=("complaint_filed", "sum"))
        .reset_index()
        .merge(drv[["driver_id", "full_name", "behavior_profile"]], on="driver_id", how="left")
        .sort_values("avg_score", ascending=False)
    )
    profile_rev = (
        summary.groupby("behavior_profile")["avg_score"]
        .mean()
        .reset_index()
        .sort_values("avg_score", ascending=False)
    )
    profile_rev.columns = ["Profile", "Avg Score"]
    profile_rev["Avg Score"] = profile_rev["Avg Score"].round(1)

    return {
        "type":    "bar",
        "title":   "Avg Safety Score by Driver Profile",
        "df":      profile_rev,
        "x":       "Profile",
        "y":       "Avg Score",
        "fmt_pkr": [],
        "insight": f"Fleet avg: {tel['safety_score'].mean():.1f}/100 | Accidents: {int(tel['accident_occurred'].sum())}",
    }


def _customer_segments(dfs: dict, question: str) -> dict:
    inv  = dfs["invoices"]
    cust = dfs["customers"]
    g = (
        inv.merge(cust[["customer_id", "customer_type"]], on="customer_id", how="left")
        .groupby("customer_type")
        .agg(revenue=("total_amount_pkr", "sum"), customers=("customer_id", "nunique"),
             invoices=("invoice_id", "count"))
        .reset_index()
        .sort_values("revenue", ascending=False)
    )
    g["revenue"]  = g["revenue"].round(0)
    g["avg_spend"] = (g["revenue"] / g["customers"]).round(0)

    return {
        "type":    "grouped_bar",
        "title":   "Revenue & Customers by Segment",
        "df":      g,
        "x":       "customer_type",
        "y":       ["revenue", "customers"],
        "fmt_pkr": ["revenue", "avg_spend"],
        "insight": f"Top segment: {g['customer_type'].iloc[0]} — {_fmt(g['revenue'].iloc[0])}",
    }


def _payment_methods(dfs: dict, question: str) -> dict:
    inv = dfs["invoices"]
    g = (
        inv.groupby("payment_method")
        .agg(revenue=("total_amount_pkr", "sum"), count=("invoice_id", "count"),
             collected=("paid_amount_pkr", "sum"))
        .reset_index()
        .sort_values("revenue", ascending=False)
    )
    g["revenue"]   = g["revenue"].round(0)
    g["collected"] = g["collected"].round(0)
    g["collection_rate"] = (g["collected"] / g["revenue"] * 100).round(1)

    return {
        "type":    "grouped_bar",
        "title":   "Revenue by Payment Method",
        "df":      g,
        "x":       "payment_method",
        "y":       ["revenue", "collected"],
        "fmt_pkr": ["revenue", "collected"],
        "insight": f"Top method: {g['payment_method'].iloc[0]} — {_fmt(g['revenue'].iloc[0])}",
    }


# ── Handler dispatch ───────────────────────────────────────────────────
_HANDLERS = {
    "top_vehicles":      _top_vehicles,
    "current_month":     _current_month,
    "month_comparison":  _month_comparison,
    "yoy_month":         _yoy_month,
    "revenue_trend":     _revenue_trend,
    "top_drivers":       _top_drivers,
    "worst_drivers":     _worst_drivers,
    "city_demand":       _city_demand,
    "booking_type":      _booking_type,
    "utilisation":       _utilisation,
    "fuel_efficiency":   _fuel_efficiency,
    "maintenance_cost":  _maintenance_cost,
    "fleet_revenue":     _fleet_revenue,
    "kpi_cards":         _kpi_cards,
    "safety_summary":    _safety_summary,
    "customer_segments": _customer_segments,
    "payment_methods":   _payment_methods,
}


# ── Public API ─────────────────────────────────────────────────────────

def chat_with_visual(question: str, dfs: dict, history: list = None):
    """
    Returns (text: str, visual: dict | None)
    Callers render text first, then the visual below it.
    """
    text = _text_chat(question, dfs, history=history or [])

    handler_name = _match_visual(question)
    visual = None
    if handler_name and handler_name in _HANDLERS:
        try:
            visual = _HANDLERS[handler_name](dfs, question)
        except Exception:
            visual = None   # silent fail — text answer still shown

    return text, visual
