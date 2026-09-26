"""
p16_parking.py — Vehicle Parking Management System
Real-time parking lot monitoring across all fleet branches.
Features:
  - Live parking lot grid (visual slot map per branch)
  - Vehicle tracker (trace any vehicle: current location, history)
  - Trip route: pickup city → dropoff city → parked location
  - Mock CCTV camera view per parking slot
  - Parking duration & cost analysis
  - Alerts: over-stay, expired insurance, vehicles due for maintenance
  - Full analytics: utilisation heatmaps, turnover, dwell time
"""

import random
import hashlib
from datetime import datetime, timedelta
from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from page_modules._shared import (
    inject, get_data, fmt,
    BRAND, STEEL, GREEN, AMBER, ORANGE, TEXT,
)

inject()

# ── Colour palette ──────────────────────────────────────────────────────────
M    = "#5a7a96"
CB   = "#141e2b"
BD   = "#1e2f44"
TEAL = "#2A9D8F"
PUR  = "#6A4C93"

# ── Helper cards / headers (same style as academy page) ────────────────────
def _card(body, left=BRAND, pad="14px 16px"):
    return (f'<div style="background:{CB};border:1px solid {BD};'
            f'border-left:3px solid {left};border-radius:10px;'
            f'padding:{pad};margin:6px 0;">{body}</div>')

def _h2(text, icon=""):
    return (f'<div style="font-size:1.22rem;font-weight:800;color:{TEXT};'
            f'margin:16px 0 4px;display:flex;align-items:center;gap:8px;">'
            f'<span style="color:{BRAND};">{icon}</span>{text}</div>')

def _h3(text, col=STEEL):
    return (f'<div style="font-size:.9rem;font-weight:700;color:{col};'
            f'border-left:3px solid {col};padding-left:8px;margin:10px 0 6px;">'
            f'{text}</div>')

def _metric(col, label, value, delta="", ok=True):
    col.metric(label, value, delta)

# ── Load data ───────────────────────────────────────────────────────────────
dfs = get_data()
trips     = dfs["trips"].copy()
vehicles  = dfs["vehicles"].copy()
fleets    = dfs["fleets"].copy()

trips["pickup_datetime"]  = pd.to_datetime(trips["pickup_datetime"],  errors="coerce")
trips["dropoff_datetime"] = pd.to_datetime(trips["dropoff_datetime"], errors="coerce")
trips["trip_fare_pkr"]    = pd.to_numeric(trips["trip_fare_pkr"],     errors="coerce").fillna(0)

# ── PARKING LOT CONFIGURATION ───────────────────────────────────────────────
# Define parking lots per city / branch
PARKING_LOTS = {
    "Islamabad - Blue Area Branch":   {"city": "Islamabad",  "fleet": "FL001", "slots": 30, "lat": 33.7180, "lon": 73.0600},
    "Islamabad - F-8 Branch":         {"city": "Islamabad",  "fleet": "FL002", "slots": 20, "lat": 33.7000, "lon": 73.0400},
    "Lahore - Gulberg Branch":        {"city": "Lahore",     "fleet": "FL001", "slots": 25, "lat": 31.5204, "lon": 74.3587},
    "Lahore - DHA Branch":            {"city": "Lahore",     "fleet": "FL003", "slots": 20, "lat": 31.4697, "lon": 74.4024},
    "Karachi - Clifton Branch":       {"city": "Karachi",    "fleet": "FL002", "slots": 35, "lat": 24.8138, "lon": 67.0300},
    "Karachi - North Nazimabad":      {"city": "Karachi",    "fleet": "FL004", "slots": 18, "lat": 24.9400, "lon": 67.0620},
    "Rawalpindi - Saddar Branch":     {"city": "Rawalpindi", "fleet": "FL003", "slots": 15, "lat": 33.5970, "lon": 73.0500},
    "Peshawar - Hayatabad Branch":    {"city": "Peshawar",   "fleet": "FL004", "slots": 12, "lat": 34.0010, "lon": 71.4660},
    "Multan - Gulgasht Branch":       {"city": "Multan",     "fleet": "FL001", "slots": 15, "lat": 30.1978, "lon": 71.4711},
    "Faisalabad - Susan Road":        {"city": "Faisalabad", "fleet": "FL002", "slots": 18, "lat": 31.4700, "lon": 73.1100},
}

# ── Generate deterministic parking state ────────────────────────────────────
@st.cache_data(ttl=300)
def generate_parking_state():
    """
    Build a synthetic parking state from real vehicle + trip data.
    Each vehicle not currently on a trip is 'parked' somewhere.
    Vehicles on completed trips are parked at their dropoff city.
    """
    now = datetime.now()
    lot_names = list(PARKING_LOTS.keys())

    # Vehicles currently on an active trip (from trips table OR vehicles.status)
    active_veh = set(
        trips[trips["status"].isin(["In Progress", "Confirmed"])]["vehicle_id"].dropna().unique()
    ) | set(
        vehicles[vehicles["status"] == "On Trip"]["vehicle_id"].dropna().unique()
    )

    # For each available vehicle, assign to a parking lot
    slots = []
    veh_list = vehicles.to_dict("records")

    # Get latest trip per vehicle for context
    latest_trip = (
        trips[trips["status"] == "Completed"]
        .sort_values("dropoff_datetime", ascending=False)
        .drop_duplicates("vehicle_id")
        .set_index("vehicle_id")
    )

    slot_counters = {lot: 0 for lot in lot_names}
    lot_list = lot_names.copy()
    random.seed(42)

    for v in veh_list:
        vid = v["vehicle_id"]
        if vid in active_veh:
            status = "On Trip"
            lot    = None
            slot_n = None
            parked_since = None
            est_return   = now + timedelta(hours=random.randint(1, 12))
        else:
            # Assign to a lot — prefer same city as fleet
            fleet_city = fleets[fleets["fleet_id"] == v.get("fleet_id","")]["city"].values
            city = fleet_city[0] if len(fleet_city) else "Islamabad"
            city_lots = [l for l in lot_list if PARKING_LOTS[l]["city"] == city]
            if not city_lots:
                city_lots = lot_list

            # Pick lot with space
            chosen = None
            for lot_name in city_lots:
                if slot_counters[lot_name] < PARKING_LOTS[lot_name]["slots"]:
                    chosen = lot_name
                    break
            if chosen is None:
                chosen = random.choice(lot_list)

            slot_counters[chosen] += 1
            slot_n = slot_counters[chosen]
            lot    = chosen

            # Parked since last dropoff
            if vid in latest_trip.index:
                parked_since = latest_trip.loc[vid, "dropoff_datetime"]
                if pd.isna(parked_since):
                    parked_since = now - timedelta(hours=random.randint(1, 72))
            else:
                parked_since = now - timedelta(hours=random.randint(1, 120))

            status = "Available" if str(v.get("status","Available")) in ("Available","") else str(v.get("status","Available"))
            est_return = None

        # Last trip info
        last_city = "—"
        last_km   = 0
        if vid in latest_trip.index:
            last_city = f"{latest_trip.loc[vid,'pickup_city']} → {latest_trip.loc[vid,'dropoff_city']}"
            last_km   = latest_trip.loc[vid, "distance_km"] if not pd.isna(latest_trip.loc[vid, "distance_km"]) else 0

        # Parking duration
        if parked_since and not pd.isna(parked_since):
            dur_hrs = (now - pd.Timestamp(parked_since)).total_seconds() / 3600
        else:
            dur_hrs = 0

        slots.append({
            "vehicle_id":    vid,
            "make":          v.get("make", ""),
            "model":         v.get("model", ""),
            "year":          v.get("year", 2020),
            "color":         v.get("color", "White"),
            "registration":  v.get("registration_no", ""),
            "fuel_type":     v.get("fuel_type", "Petrol"),
            "fleet_id":      v.get("fleet_id", ""),
            "status":        status,
            "lot":           lot,
            "slot_number":   slot_n,
            "parked_since":  parked_since,
            "parking_hrs":   round(dur_hrs, 1),
            "est_return":    est_return,
            "last_route":    last_city,
            "last_km":       last_km,
            "condition":     v.get("condition_rating", "Good"),
            "gps":           v.get("gps_enabled", True),
            "insurance_exp": v.get("insurance_expiry", None),
            "odometer":      v.get("odometer_km", 0),
        })

    return pd.DataFrame(slots)


parking_df = generate_parking_state()

# ── Vehicle status colours ───────────────────────────────────────────────────
STATUS_COLOR = {
    "Available":   TEAL,
    "On Trip":     BRAND,
    "Maintenance": AMBER,
    "Reserved":    ORANGE,
    "Unavailable": M,
}

# ── PAGE HEADER ──────────────────────────────────────────────────────────────
st.markdown(
    f'<div style="font-size:1.6rem;font-weight:900;color:{BRAND};letter-spacing:-.01em;">'
    f'🅿️ Parking Management System</div>'
    f'<div style="font-size:.8rem;color:{M};margin-bottom:2px;">'
    f'Live parking lot monitoring · Vehicle tracking · Route history · CCTV view · Analytics</div>',
    unsafe_allow_html=True,
)
st.markdown(f"<hr style='border-color:{BD};margin:6px 0 10px'>", unsafe_allow_html=True)

# ── TOP KPIs ─────────────────────────────────────────────────────────────────
_total   = len(parking_df)
_parked  = len(parking_df[parking_df["status"] == "Available"])
_on_trip = len(parking_df[parking_df["status"] == "On Trip"])
_maint   = len(parking_df[parking_df["status"] == "Maintenance"])
_lots    = len(PARKING_LOTS)
_avg_dur = parking_df[parking_df["parking_hrs"] > 0]["parking_hrs"].mean()

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Total Vehicles",   f"{_total}")
k2.metric("Parked Now",       f"{_parked}",  delta=f"{_parked/_total*100:.0f}%")
k3.metric("On Trip",          f"{_on_trip}", delta=f"{_on_trip/_total*100:.0f}%")
k4.metric("Maintenance",      f"{_maint}")
k5.metric("Parking Lots",     f"{_lots}")
k6.metric("Avg Park Duration",f"{_avg_dur:.1f} hrs")

st.markdown(f"<hr style='border-color:{BD};margin:8px 0 12px'>", unsafe_allow_html=True)

# ── MAIN TABS ────────────────────────────────────────────────────────────────
PT = st.tabs([
    "🏢 Lot Overview",
    "🔍 Vehicle Tracker",
    "🗺️ Live Map",
    "📷 CCTV Monitor",
    "📊 Analytics",
    "⚠️ Alerts",
])


# ════════════════════════════════════════════════════════════════════════
# TAB 0 — LOT OVERVIEW
# ════════════════════════════════════════════════════════════════════════
with PT[0]:
    st.markdown(_h2("Parking Lot Overview", "🏢"), unsafe_allow_html=True)

    # Lot selector
    _lot_names = ["All Lots"] + list(PARKING_LOTS.keys())
    _sel_lot = st.selectbox("Select Lot:", _lot_names, key="lot_sel")

    if _sel_lot == "All Lots":
        _display_lots = PARKING_LOTS
    else:
        _display_lots = {_sel_lot: PARKING_LOTS[_sel_lot]}

    for lot_name, lot_info in _display_lots.items():
        lot_vehicles = parking_df[parking_df["lot"] == lot_name].copy()
        cap     = lot_info["slots"]
        occ     = len(lot_vehicles[lot_vehicles["status"] != "On Trip"])
        on_trip = len(lot_vehicles[lot_vehicles["status"] == "On Trip"])
        free    = cap - occ
        occ_pct = round(occ / cap * 100, 0) if cap else 0

        # Lot header
        _clr = TEAL if occ_pct < 60 else AMBER if occ_pct < 85 else BRAND
        st.markdown(_card(
            f'<div style="display:flex;justify-content:space-between;align-items:center;">'
            f'<div><b style="font-size:.95rem;color:{TEXT};">{lot_name}</b>'
            f'<span style="font-size:.72rem;color:{M};margin-left:10px;">'
            f'{lot_info["city"]} · {cap} slots</span></div>'
            f'<div style="text-align:right;">'
            f'<span style="font-size:1.1rem;font-weight:800;color:{_clr};">{occ_pct:.0f}%</span>'
            f'<span style="font-size:.7rem;color:{M};margin-left:4px;">occupied</span></div></div>'
            f'<div style="background:{BD};border-radius:4px;height:8px;margin-top:8px;">'
            f'<div style="background:{_clr};width:{occ_pct}%;height:8px;border-radius:4px;'
            f'transition:width .3s;"></div></div>'
            f'<div style="display:flex;gap:16px;margin-top:8px;font-size:.74rem;">'
            f'<span style="color:{TEAL};">🟢 Parked: {occ}</span>'
            f'<span style="color:{BRAND};">🔴 On Trip: {on_trip}</span>'
            f'<span style="color:{M};">⬜ Free: {free}</span></div>',
            left=_clr,
        ), unsafe_allow_html=True)

        # Slot grid — visual parking map
        if len(lot_vehicles) > 0:
            _cols_per_row = 8
            _slot_rows = []
            for row_start in range(0, cap, _cols_per_row):
                _slot_row_html = '<div style="display:flex;gap:4px;margin:3px 0;">'
                for slot_i in range(row_start, min(row_start + _cols_per_row, cap)):
                    slot_veh = lot_vehicles[lot_vehicles["slot_number"] == slot_i + 1]
                    if len(slot_veh) == 0:
                        # Empty slot
                        _slot_row_html += (
                            f'<div title="Slot {slot_i+1}: Empty" style="'
                            f'width:70px;height:44px;background:#0d1117;border:1px solid #30363d;'
                            f'border-radius:5px;display:flex;align-items:center;justify-content:center;'
                            f'font-size:.6rem;color:#30363d;">S{slot_i+1}</div>'
                        )
                    else:
                        v = slot_veh.iloc[0]
                        _sc = STATUS_COLOR.get(v["status"], M)
                        # Vehicle icon color based on type
                        _icon = "🚗" if "sedan" in v["model"].lower() or "corolla" in v["model"].lower() or "city" in v["model"].lower() else \
                                "🚙" if "fortuner" in v["model"].lower() or "hilux" in v["model"].lower() or "prado" in v["model"].lower() else \
                                "🚐" if "hiace" in v["model"].lower() or "coaster" in v["model"].lower() else "🚗"
                        _slot_row_html += (
                            f'<div title="Slot {slot_i+1}: {v["make"]} {v["model"]} ({v["registration"]}) - {v["status"]}" style="'
                            f'width:70px;height:44px;background:{_sc}22;border:1px solid {_sc}88;'
                            f'border-radius:5px;display:flex;flex-direction:column;align-items:center;'
                            f'justify-content:center;cursor:pointer;font-size:.58rem;color:{_sc};">'
                            f'{_icon}<br>{v["registration"][:8]}</div>'
                        )
                _slot_row_html += '</div>'
                _slot_rows.append(_slot_row_html)

            st.markdown(
                f'<div style="background:{CB};border:1px solid {BD};border-radius:8px;'
                f'padding:12px;margin:4px 0;overflow-x:auto;">'
                f'<div style="font-size:.7rem;color:{M};margin-bottom:8px;">'
                f'Slot map — hover for details</div>'
                + "".join(_slot_rows)
                + '</div>',
                unsafe_allow_html=True,
            )

        # Vehicle table for this lot
        with st.expander(f"📋 Vehicle List — {lot_name}", expanded=False):
            if len(lot_vehicles) > 0:
                _show_cols = ["vehicle_id","make","model","registration","status",
                              "parking_hrs","last_route","condition"]
                _disp = lot_vehicles[_show_cols].copy()
                _disp.columns = ["ID","Make","Model","Reg","Status",
                                  "Parked (hrs)","Last Route","Condition"]
                st.dataframe(_disp, use_container_width=True, height=220, hide_index=True)
            else:
                st.info("No vehicles assigned to this lot.")


# ════════════════════════════════════════════════════════════════════════
# TAB 1 — VEHICLE TRACKER
# ════════════════════════════════════════════════════════════════════════
with PT[1]:
    st.markdown(_h2("Vehicle Tracker", "🔍"), unsafe_allow_html=True)

    # Search by registration, vehicle_id, or make/model
    _search = st.text_input(
        "Search vehicle (ID, registration, make/model):",
        placeholder="e.g. VH00042 or KHI-ABC or Toyota",
        key="veh_search",
    )

    _search_results = parking_df.copy()
    if _search:
        _s = _search.upper().strip()
        _search_results = parking_df[
            parking_df["vehicle_id"].str.upper().str.contains(_s, na=False) |
            parking_df["registration"].str.upper().str.contains(_s, na=False) |
            parking_df["make"].str.upper().str.contains(_s, na=False) |
            parking_df["model"].str.upper().str.contains(_s, na=False)
        ]

    if len(_search_results) == 0:
        st.warning("No vehicles found.")
    else:
        # Select vehicle
        _veh_options = _search_results["vehicle_id"].tolist()
        _sel_veh = st.selectbox(
            f"{len(_veh_options)} vehicle(s) found:",
            _veh_options,
            format_func=lambda v: f"{v} — " + (
                parking_df[parking_df["vehicle_id"]==v].iloc[0]["make"] + " " +
                parking_df[parking_df["vehicle_id"]==v].iloc[0]["model"] + " (" +
                parking_df[parking_df["vehicle_id"]==v].iloc[0]["registration"] + ")"
            ) if len(parking_df[parking_df["vehicle_id"]==v]) > 0 else v,
            key="sel_veh",
        )

        _vr = parking_df[parking_df["vehicle_id"] == _sel_veh].iloc[0]

        # ── Vehicle identity card ─────────────────────────────────────
        _sc2 = STATUS_COLOR.get(_vr["status"], M)
        tc1, tc2 = st.columns([1, 2])

        with tc1:
            # Mock vehicle image using CSS
            _clr_map = {"White": "#f0f0f0","Black": "#1a1a1a","Silver": "#c0c0c0",
                        "Dark Blue": "#1a237e","Red": "#c62828","Blue": "#1565c0",
                        "Grey": "#616161","Dark Grey": "#424242"}
            _car_bg = _clr_map.get(_vr["color"], "#457B9D")
            st.markdown(
                f'<div style="background:{CB};border:2px solid {_sc2};border-radius:12px;'
                f'padding:20px;text-align:center;">'
                f'<div style="font-size:4rem;">🚗</div>'
                f'<div style="background:{_car_bg};color:#fff;padding:4px 12px;'
                f'border-radius:6px;font-size:1rem;font-weight:800;margin:8px auto;display:inline-block;">'
                f'{_vr["registration"]}</div>'
                f'<div style="font-size:.82rem;color:{TEXT};margin-top:6px;">'
                f'{_vr["make"]} {_vr["model"]} {_vr["year"]}</div>'
                f'<div style="margin-top:8px;">'
                f'<span style="background:{_sc2}33;color:{_sc2};padding:3px 12px;'
                f'border-radius:20px;font-size:.75rem;font-weight:700;">{_vr["status"]}</span>'
                f'</div></div>',
                unsafe_allow_html=True,
            )

        with tc2:
            # Detailed attributes
            _attrs = [
                ("Vehicle ID",      _vr["vehicle_id"]),
                ("Make / Model",    f"{_vr['make']} {_vr['model']}"),
                ("Year",            str(_vr["year"])),
                ("Color",           _vr["color"]),
                ("Fuel Type",       _vr["fuel_type"]),
                ("Condition",       _vr["condition"]),
                ("Odometer",        f"{int(_vr['odometer']):,} km"),
                ("GPS Enabled",     "Yes" if _vr["gps"] else "No"),
                ("Current Status",  _vr["status"]),
                ("Current Location",_vr["lot"] if _vr["lot"] else "On Trip"),
                ("Slot Number",     f"Slot {int(_vr['slot_number'])}" if pd.notna(_vr["slot_number"]) and _vr["slot_number"] else "—"),
                ("Parked Since",    str(_vr["parked_since"])[:16] if _vr["parked_since"] and not pd.isna(_vr["parked_since"]) else "—"),
                ("Parked Duration", f"{_vr['parking_hrs']:.1f} hrs" if _vr["parking_hrs"] > 0 else "—"),
                ("Last Route",      _vr["last_route"]),
                ("Last Trip KM",    f"{_vr['last_km']:.0f} km"),
                ("Insurance Exp.",  str(_vr["insurance_exp"])[:10] if _vr["insurance_exp"] and not pd.isna(str(_vr["insurance_exp"])) else "—"),
            ]
            for i in range(0, len(_attrs), 2):
                _r = st.columns(2)
                for j in range(2):
                    if i + j < len(_attrs):
                        _k, _v2 = _attrs[i + j]
                        _r[j].markdown(
                            f'<div style="background:{CB};border:1px solid {BD};border-radius:7px;'
                            f'padding:8px 12px;margin:2px 0;">'
                            f'<div style="font-size:.65rem;color:{M};text-transform:uppercase;">{_k}</div>'
                            f'<div style="font-size:.82rem;color:{TEXT};font-weight:600;">{_v2}</div>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

        # ── Trip history for this vehicle ─────────────────────────────
        st.markdown(_h3("📍 Trip History", STEEL), unsafe_allow_html=True)
        _veh_trips = trips[trips["vehicle_id"] == _sel_veh].copy()
        _veh_trips = _veh_trips.sort_values("pickup_datetime", ascending=False)

        if len(_veh_trips) == 0:
            st.info("No trip history found for this vehicle.")
        else:
            _th_cols = ["trip_id","pickup_datetime","dropoff_datetime",
                        "pickup_city","dropoff_city","distance_km","trip_fare_pkr","status"]
            _th = _veh_trips[_th_cols].head(20).copy()
            _th.columns = ["Trip ID","Pickup","Dropoff","From","To","KM","Fare (PKR)","Status"]
            _th["Pickup"]  = _th["Pickup"].dt.strftime("%Y-%m-%d %H:%M")
            _th["Dropoff"] = _th["Dropoff"].dt.strftime("%Y-%m-%d %H:%M")
            st.dataframe(_th, use_container_width=True, height=280, hide_index=True)

            # Route map for last 10 trips
            st.markdown(_h3("🗺️ Route Timeline", BRAND), unsafe_allow_html=True)
            _CITY_COORDS = {
                "Islamabad": (33.6844, 73.0479), "Rawalpindi": (33.5651, 73.0169),
                "Lahore": (31.5204, 74.3587),    "Karachi": (24.8607, 67.0011),
                "Peshawar": (34.0151, 71.5249),  "Multan": (30.1575, 71.5249),
                "Faisalabad": (31.4504, 73.1350), "Gujranwala": (32.1877, 74.1945),
                "Quetta": (30.1798, 66.9750),    "Murree": (33.9078, 73.3906),
            }
            _route_df = _veh_trips.head(10)[["pickup_city","dropoff_city","pickup_datetime","trip_fare_pkr","status"]].copy()
            _route_df = _route_df.dropna(subset=["pickup_city","dropoff_city"])

            fig_route = go.Figure()
            for _, row in _route_df.iterrows():
                p = _CITY_COORDS.get(row["pickup_city"])
                d = _CITY_COORDS.get(row["dropoff_city"])
                if p and d:
                    _rc = TEAL if row["status"] == "Completed" else BRAND if row["status"] == "Cancelled" else AMBER
                    fig_route.add_trace(go.Scattergeo(
                        lon=[p[1], d[1]], lat=[p[0], d[0]],
                        mode="lines+markers",
                        line=dict(width=2, color=_rc),
                        marker=dict(size=8, color=_rc),
                        name=f"{row['pickup_city']}→{row['dropoff_city']}",
                        showlegend=False,
                    ))
            fig_route.update_geos(
                center=dict(lat=30.5, lon=70.0), projection_scale=8,
                bgcolor="rgba(0,0,0,0)", showland=True, landcolor="#141e2b",
                showocean=True, oceancolor="#0d1117", showcountries=True,
                countrycolor="#30363d",
            )
            fig_route.update_layout(
                height=340, paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0,r=0,t=0,b=0),
                geo=dict(bgcolor="rgba(0,0,0,0)"),
            )
            st.plotly_chart(fig_route, use_container_width=True)


# ════════════════════════════════════════════════════════════════════════
# TAB 2 — LIVE MAP
# ════════════════════════════════════════════════════════════════════════
with PT[2]:
    st.markdown(_h2("Live Parking Map", "🗺️"), unsafe_allow_html=True)

    # Build map data: one dot per lot + one dot per active trip vehicle
    _map_data = []
    for lot_name, info in PARKING_LOTS.items():
        lot_veh = parking_df[parking_df["lot"] == lot_name]
        occ = len(lot_veh)
        cap = info["slots"]
        pct = round(occ / cap * 100, 0) if cap else 0
        _map_data.append({
            "name":      lot_name,
            "city":      info["city"],
            "lat":       info["lat"],
            "lon":       info["lon"],
            "occupied":  occ,
            "capacity":  cap,
            "free":      max(0, cap - occ),
            "occ_pct":   pct,
            "status":    "Full" if pct > 85 else ("Busy" if pct > 60 else "Available"),
        })

    _map_df = pd.DataFrame(_map_data)

    fig_map = px.scatter_map(
        _map_df,
        lat="lat", lon="lon",
        size="occupied",
        color="occ_pct",
        color_continuous_scale=["#2A9D8F", "#E9C46A", "#E63946"],
        range_color=[0, 100],
        hover_name="name",
        hover_data={"occupied": True, "free": True, "occ_pct": True,
                    "lat": False, "lon": False},
        map_style="carto-darkmatter",
        zoom=5,
        center={"lat": 30.5, "lon": 70.0},
        size_max=40,
        title="",
    )
    fig_map.update_traces(
        hovertemplate="<b>%{hovertext}</b><br>Occupied: %{customdata[0]}<br>"
                      "Free: %{customdata[1]}<br>Occupancy: %{customdata[2]:.0f}%<extra></extra>",
    )
    fig_map.update_layout(
        height=500, paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0,r=0,t=0,b=0),
        coloraxis_colorbar=dict(title="Occ %", tickfont=dict(color=TEXT)),
    )
    st.plotly_chart(fig_map, use_container_width=True)

    # Lot summary table
    st.markdown(_h3("📋 All Lots Summary", STEEL), unsafe_allow_html=True)
    _map_df["Occupancy"] = _map_df["occ_pct"].astype(str) + "%"
    st.dataframe(
        _map_df[["name","city","capacity","occupied","free","Occupancy","status"]].rename(columns={
            "name":"Lot","city":"City","capacity":"Capacity",
            "occupied":"Occupied","free":"Free","status":"Status",
        }),
        use_container_width=True, height=320, hide_index=True,
    )


# ════════════════════════════════════════════════════════════════════════
# TAB 3 — CCTV MONITOR
# ════════════════════════════════════════════════════════════════════════
with PT[3]:
    st.markdown(_h2("CCTV Monitor", "📷"), unsafe_allow_html=True)
    st.markdown(_card(
        f'Mock live camera feeds for each parking slot. '
        f'Select a lot and slot to view the vehicle in that space.',
        left=STEEL, pad="10px 14px",
    ), unsafe_allow_html=True)

    _cc1, _cc2 = st.columns(2)
    with _cc1:
        _cctv_lot = st.selectbox("Parking Lot:", list(PARKING_LOTS.keys()), key="cctv_lot")
    with _cc2:
        _lot_veh_cctv = parking_df[parking_df["lot"] == _cctv_lot].copy()
        _slot_opts = sorted(_lot_veh_cctv["slot_number"].dropna().astype(int).tolist())
        if _slot_opts:
            _cctv_slot = st.selectbox("Slot:", _slot_opts, key="cctv_slot",
                                      format_func=lambda s: f"Slot {s}")
        else:
            _cctv_slot = None
            st.info("No occupied slots in this lot.")

    if _cctv_slot:
        _slot_veh = _lot_veh_cctv[_lot_veh_cctv["slot_number"] == _cctv_slot]

        _cv1, _cv2 = st.columns([2, 1])

        with _cv1:
            # Generate deterministic mock camera feed using SVG
            if len(_slot_veh) > 0:
                _sv = _slot_veh.iloc[0]
                _clr_map2 = {
                    "White":     "#e8e8e8", "Black":     "#1a1a1a",
                    "Silver":    "#b0b0b0", "Dark Blue": "#1a237e",
                    "Red":       "#c62828", "Blue":      "#1565c0",
                    "Grey":      "#757575", "Dark Grey": "#424242",
                }
                _car_clr = _clr_map2.get(_sv["color"], "#457B9D")
                _ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # SVG-based mock CCTV frame
                _svg = f"""
<div style="background:#000;border:2px solid #333;border-radius:8px;
     position:relative;overflow:hidden;padding:0;">
  <svg viewBox="0 0 640 360" style="width:100%;display:block;">
    <!-- Background / floor -->
    <rect width="640" height="360" fill="#0a0a0a"/>
    <!-- Parking lines -->
    <line x1="50"  y1="50"  x2="50"  y2="310" stroke="#333" stroke-width="2"/>
    <line x1="590" y1="50"  x2="590" y2="310" stroke="#333" stroke-width="2"/>
    <line x1="50"  y1="310" x2="590" y2="310" stroke="#ffff00" stroke-width="3"/>
    <line x1="50"  y1="50"  x2="590" y2="50"  stroke="#ffff00" stroke-width="3"/>
    <!-- Slot number -->
    <text x="320" y="340" fill="#ffff00" font-size="14" text-anchor="middle"
          font-family="monospace">SLOT {int(_cctv_slot)}</text>
    <!-- Car body -->
    <rect x="180" y="160" width="280" height="120" rx="15" fill="{_car_clr}" stroke="#555" stroke-width="2"/>
    <!-- Car roof -->
    <rect x="230" y="110" width="180" height="65" rx="12" fill="{_car_clr}" stroke="#555" stroke-width="1.5"/>
    <!-- Windshield -->
    <rect x="240" y="118" width="160" height="50" rx="6" fill="#1a3a5c" opacity="0.8"/>
    <!-- Headlights -->
    <ellipse cx="200" cy="182" rx="18" ry="12" fill="#fff8e1" opacity="0.9"/>
    <ellipse cx="440" cy="182" rx="18" ry="12" fill="#fff8e1" opacity="0.9"/>
    <!-- Rear lights -->
    <rect x="178" y="230" width="22" height="16" rx="3" fill="#c62828" opacity="0.9"/>
    <rect x="440" y="230" width="22" height="16" rx="3" fill="#c62828" opacity="0.9"/>
    <!-- Wheels -->
    <circle cx="245" cy="280" r="30" fill="#222" stroke="#555" stroke-width="3"/>
    <circle cx="245" cy="280" r="18" fill="#333"/>
    <circle cx="395" cy="280" r="30" fill="#222" stroke="#555" stroke-width="3"/>
    <circle cx="395" cy="280" r="18" fill="#333"/>
    <!-- Number plate -->
    <rect x="280" y="270" width="80" height="24" rx="3" fill="#fff" stroke="#ddd"/>
    <text x="320" y="286" fill="#000" font-size="10" text-anchor="middle"
          font-family="monospace" font-weight="bold">{_sv["registration"][:9]}</text>
    <!-- CCTV overlay -->
    <rect width="640" height="360" fill="#00ff0008"/>
    <!-- Scanlines effect -->
    {"".join(f'<line x1="0" y1="{y}" x2="640" y2="{y}" stroke="#00000015" stroke-width="1"/>' for y in range(0,360,3))}
    <!-- Camera info overlay -->
    <rect x="0" y="0" width="640" height="30" fill="#00000088"/>
    <text x="8" y="20" fill="#0f0" font-size="11" font-family="monospace">
      CAM-{int(_cctv_slot):02d} | {_cctv_lot[:30]}</text>
    <text x="632" y="20" fill="#0f0" font-size="11" font-family="monospace"
          text-anchor="end">{_ts}</text>
    <!-- REC indicator -->
    <circle cx="620" cy="50" r="6" fill="#f00" opacity="0.9"/>
    <text x="608" y="54" fill="#f00" font-size="10" font-family="monospace" text-anchor="end">REC</text>
  </svg>
</div>"""
                st.markdown(_svg, unsafe_allow_html=True)
            else:
                # Empty slot
                st.markdown(
                    f'<div style="background:#000;border:2px solid #333;border-radius:8px;height:280px;'
                    f'display:flex;align-items:center;justify-content:center;flex-direction:column;">'
                    f'<div style="font-size:3rem;">⬜</div>'
                    f'<div style="color:#444;font-family:monospace;margin-top:8px;">SLOT EMPTY</div>'
                    f'<div style="color:#222;font-family:monospace;font-size:.7rem;">{_ts}</div></div>',
                    unsafe_allow_html=True,
                )
                _ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with _cv2:
            if len(_slot_veh) > 0:
                _sv = _slot_veh.iloc[0]
                st.markdown(_card(
                    f'<b style="font-size:.82rem;color:{BRAND};">Vehicle Details</b><br><br>'
                    f'<div style="font-size:.78rem;color:{TEXT};line-height:1.9;">'
                    f'<b>ID:</b> {_sv["vehicle_id"]}<br>'
                    f'<b>Make:</b> {_sv["make"]} {_sv["model"]}<br>'
                    f'<b>Year:</b> {_sv["year"]}<br>'
                    f'<b>Reg:</b> {_sv["registration"]}<br>'
                    f'<b>Color:</b> {_sv["color"]}<br>'
                    f'<b>Fuel:</b> {_sv["fuel_type"]}<br>'
                    f'<b>Status:</b> <span style="color:{STATUS_COLOR.get(_sv["status"],M)};">{_sv["status"]}</span><br>'
                    f'<b>Parked:</b> {_sv["parking_hrs"]:.1f} hrs<br>'
                    f'<b>Last Route:</b> {_sv["last_route"]}<br>'
                    f'<b>Condition:</b> {_sv["condition"]}</div>',
                    left=STEEL,
                ), unsafe_allow_html=True)

                st.download_button(
                    "⬇ Download Vehicle Report",
                    data=(
                        f"PARKING SLOT REPORT\n{'='*40}\n"
                        f"Lot: {_cctv_lot}\nSlot: {_cctv_slot}\n"
                        f"Timestamp: {datetime.now()}\n\n"
                        f"Vehicle ID:    {_sv['vehicle_id']}\n"
                        f"Registration:  {_sv['registration']}\n"
                        f"Make/Model:    {_sv['make']} {_sv['model']} ({_sv['year']})\n"
                        f"Color:         {_sv['color']}\n"
                        f"Status:        {_sv['status']}\n"
                        f"Parked Since:  {_sv['parked_since']}\n"
                        f"Duration:      {_sv['parking_hrs']:.1f} hrs\n"
                        f"Last Route:    {_sv['last_route']}\n"
                        f"Odometer:      {int(_sv['odometer']):,} km\n"
                        f"Condition:     {_sv['condition']}\n"
                    ),
                    file_name=f"parking_report_{_sv['vehicle_id']}.txt",
                    mime="text/plain",
                    key="dl_parking_report",
                )

    # Grid view of all lots
    st.markdown(_h3("📷 All Camera Feeds (Overview)", STEEL), unsafe_allow_html=True)
    _cctv_cols = st.columns(4)
    for i, (lot_name, info) in enumerate(list(PARKING_LOTS.items())[:8]):
        lot_v = parking_df[parking_df["lot"] == lot_name]
        occ   = len(lot_v)
        cap   = info["slots"]
        pct   = round(occ/cap*100,0) if cap else 0
        _cc_clr = TEAL if pct < 60 else AMBER if pct < 85 else BRAND
        with _cctv_cols[i % 4]:
            st.markdown(
                f'<div style="background:#000;border:1px solid #333;border-radius:6px;'
                f'padding:10px;margin:3px 0;text-align:center;">'
                f'<div style="font-size:.6rem;color:#0f0;font-family:monospace;">CAM-LOT-{i+1:02d}</div>'
                f'<div style="font-size:1.8rem;margin:8px 0;">🅿️</div>'
                f'<div style="font-size:.65rem;color:{TEXT};">{lot_name[:20]}...</div>'
                f'<div style="background:{_cc_clr}33;color:{_cc_clr};border-radius:4px;'
                f'padding:2px 6px;font-size:.68rem;font-weight:700;margin-top:4px;">'
                f'{occ}/{cap} — {pct:.0f}%</div></div>',
                unsafe_allow_html=True,
            )


# ════════════════════════════════════════════════════════════════════════
# TAB 4 — ANALYTICS
# ════════════════════════════════════════════════════════════════════════
with PT[4]:
    st.markdown(_h2("Parking Analytics", "📊"), unsafe_allow_html=True)

    _at1, _at2, _at3 = st.tabs(["Utilisation", "Dwell Time", "City Analysis"])

    with _at1:
        # Occupancy by lot
        _lot_stats = []
        for lot_name, info in PARKING_LOTS.items():
            lv = parking_df[parking_df["lot"] == lot_name]
            occ = len(lv)
            cap = info["slots"]
            _lot_stats.append({
                "Lot":       lot_name.split(" - ")[0] + "\n" + lot_name.split(" - ")[1] if " - " in lot_name else lot_name,
                "City":      info["city"],
                "Occupied":  occ,
                "Free":      max(0, cap - occ),
                "Capacity":  cap,
                "Occ %":     round(occ/cap*100, 1) if cap else 0,
            })
        _lot_df = pd.DataFrame(_lot_stats)

        fig_occ = px.bar(
            _lot_df, x="Lot", y=["Occupied","Free"],
            title="Parking Lot Occupancy vs Free Slots",
            template="plotly_dark",
            color_discrete_sequence=[BRAND, TEAL],
            barmode="stack",
        )
        fig_occ.update_layout(height=340, paper_bgcolor="rgba(0,0,0,0)",
                              plot_bgcolor="rgba(0,0,0,0)",
                              margin=dict(t=40,b=60,l=0,r=0))
        st.plotly_chart(fig_occ, use_container_width=True)

        # Utilisation gauge per city
        _city_stats = _lot_df.groupby("City").agg(
            total_occ=("Occupied","sum"),
            total_cap=("Capacity","sum"),
        ).reset_index()
        _city_stats["Util %"] = (_city_stats["total_occ"] / _city_stats["total_cap"] * 100).round(1)

        _gauges_per_row = 4
        _gau_cols = st.columns(_gauges_per_row)
        for i, row in _city_stats.iterrows():
            pct = row["Util %"]
            clr = TEAL if pct < 60 else AMBER if pct < 85 else BRAND
            with _gau_cols[i % _gauges_per_row]:
                fig_g = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=pct,
                    title={"text": row["City"], "font": {"size": 12, "color": TEXT}},
                    number={"suffix": "%", "font": {"color": clr}},
                    gauge={
                        "axis": {"range": [0, 100], "tickcolor": M},
                        "bar":  {"color": clr},
                        "bgcolor": CB,
                        "steps": [
                            {"range": [0, 60],  "color": "#0d2818"},
                            {"range": [60, 85], "color": "#1c1400"},
                            {"range": [85, 100],"color": "#2d0a0a"},
                        ],
                    },
                ))
                fig_g.update_layout(
                    height=180, paper_bgcolor="rgba(0,0,0,0)",
                    margin=dict(t=40, b=0, l=20, r=20),
                    font=dict(color=TEXT),
                )
                st.plotly_chart(fig_g, use_container_width=True)

    with _at2:
        # Dwell time distribution
        _parked_veh = parking_df[parking_df["parking_hrs"] > 0].copy()

        if len(_parked_veh) > 0:
            fig_dwell = px.histogram(
                _parked_veh, x="parking_hrs", nbins=30,
                title="Parking Dwell Time Distribution (hours)",
                template="plotly_dark",
                color_discrete_sequence=[AMBER],
                labels={"parking_hrs": "Dwell Time (hrs)"},
            )
            fig_dwell.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)",
                                    plot_bgcolor="rgba(0,0,0,0)",
                                    margin=dict(t=40,b=0,l=0,r=0))
            st.plotly_chart(fig_dwell, use_container_width=True)

            # Dwell time by status
            fig_box_d = px.box(
                _parked_veh, x="status", y="parking_hrs",
                title="Dwell Time by Vehicle Status",
                template="plotly_dark",
                color="status",
                color_discrete_sequence=[TEAL, BRAND, AMBER, ORANGE],
            )
            fig_box_d.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)",
                                    plot_bgcolor="rgba(0,0,0,0)",
                                    margin=dict(t=40,b=0,l=0,r=0), showlegend=False)
            st.plotly_chart(fig_box_d, use_container_width=True)

            # Stats
            _d1, _d2, _d3, _d4 = st.columns(4)
            _d1.metric("Avg Dwell",   f"{_parked_veh['parking_hrs'].mean():.1f} hrs")
            _d2.metric("Max Dwell",   f"{_parked_veh['parking_hrs'].max():.1f} hrs")
            _d3.metric("> 24 hrs",    str(len(_parked_veh[_parked_veh["parking_hrs"] > 24])))
            _d4.metric("> 72 hrs",    str(len(_parked_veh[_parked_veh["parking_hrs"] > 72])))

    with _at3:
        # Vehicles per city
        _city_veh = parking_df.copy()
        _city_veh["city"] = _city_veh["lot"].map(
            lambda l: PARKING_LOTS.get(l, {}).get("city", "Unknown") if l else "On Trip"
        )
        _cv_grp = _city_veh.groupby(["city","status"]).size().reset_index(name="count")

        fig_city = px.bar(
            _cv_grp, x="city", y="count", color="status",
            title="Vehicle Distribution by City & Status",
            template="plotly_dark",
            color_discrete_map={
                "Available": TEAL, "On Trip": BRAND,
                "Maintenance": AMBER, "Unavailable": M,
            },
            barmode="stack",
        )
        fig_city.update_layout(height=340, paper_bgcolor="rgba(0,0,0,0)",
                               plot_bgcolor="rgba(0,0,0,0)",
                               margin=dict(t=40,b=0,l=0,r=0))
        st.plotly_chart(fig_city, use_container_width=True)

        # Fleet distribution
        _fleet_grp = parking_df.groupby("fleet_id")["status"].value_counts().reset_index()
        _fleet_grp.columns = ["Fleet","Status","Count"]
        fig_fleet = px.bar(
            _fleet_grp, x="Fleet", y="Count", color="Status",
            title="Vehicle Status by Fleet",
            template="plotly_dark",
            color_discrete_map={
                "Available": TEAL, "On Trip": BRAND,
                "Maintenance": AMBER, "Unavailable": M,
            },
        )
        fig_fleet.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)",
                                plot_bgcolor="rgba(0,0,0,0)",
                                margin=dict(t=40,b=0,l=0,r=0))
        st.plotly_chart(fig_fleet, use_container_width=True)


# ════════════════════════════════════════════════════════════════════════
# TAB 5 — ALERTS
# ════════════════════════════════════════════════════════════════════════
with PT[5]:
    st.markdown(_h2("Parking Alerts & Exceptions", "⚠️"), unsafe_allow_html=True)

    now = datetime.now()
    _alerts = []

    for _, row in parking_df.iterrows():
        vid   = row["vehicle_id"]
        vname = f"{row['make']} {row['model']} ({row['registration']})"

        # 1. Over-stay alert: parked > 72 hours
        if row["parking_hrs"] > 72 and row["status"] == "Available":
            _alerts.append({
                "Level": "🔴 Critical",
                "Alert": "Over-Stay",
                "Vehicle": vname,
                "Detail": f"Parked {row['parking_hrs']:.0f} hrs — exceeds 72hr limit",
                "Lot": row["lot"] or "—",
                "Action": "Inspect & contact fleet manager",
            })

        # 2. Long dwell warning: 24-72 hrs
        elif 24 < row["parking_hrs"] <= 72 and row["status"] == "Available":
            _alerts.append({
                "Level": "🟡 Warning",
                "Alert": "Long Dwell",
                "Vehicle": vname,
                "Detail": f"Parked {row['parking_hrs']:.0f} hrs",
                "Lot": row["lot"] or "—",
                "Action": "Review availability",
            })

        # 3. Expired insurance
        try:
            ins_exp = pd.to_datetime(row["insurance_exp"], errors="coerce")
            if not pd.isna(ins_exp) and ins_exp.date() < now.date():
                _alerts.append({
                    "Level": "🔴 Critical",
                    "Alert": "Insurance Expired",
                    "Vehicle": vname,
                    "Detail": f"Expired: {ins_exp.date()}",
                    "Lot": row["lot"] or "On Trip",
                    "Action": "Do not dispatch until renewed",
                })
        except Exception:
            pass

        # 4. Maintenance status
        if row["status"] == "Maintenance":
            _alerts.append({
                "Level": "🟠 Info",
                "Alert": "In Maintenance",
                "Vehicle": vname,
                "Detail": "Vehicle currently in workshop",
                "Lot": row["lot"] or "Workshop",
                "Action": "Check estimated return date",
            })

        # 5. Poor condition
        if row["condition"] in ("Poor", "Fair") and row["status"] != "Maintenance":
            _alerts.append({
                "Level": "🟡 Warning",
                "Alert": "Poor Condition",
                "Vehicle": vname,
                "Detail": f"Condition rated: {row['condition']}",
                "Lot": row["lot"] or "On Trip",
                "Action": "Schedule maintenance check",
            })

    if not _alerts:
        st.success("✅ No active alerts — all vehicles within normal parameters.")
    else:
        _alert_df = pd.DataFrame(_alerts)

        # Summary counts
        _crit = len(_alert_df[_alert_df["Level"].str.startswith("🔴")])
        _warn = len(_alert_df[_alert_df["Level"].str.startswith("🟡")])
        _info = len(_alert_df[_alert_df["Level"].str.startswith(("🟠","🟢"))])

        _ac1, _ac2, _ac3, _ac4 = st.columns(4)
        _ac1.metric("Total Alerts",    str(len(_alert_df)))
        _ac2.metric("Critical",        str(_crit),  delta="Action needed" if _crit > 0 else "")
        _ac3.metric("Warnings",        str(_warn))
        _ac4.metric("Info",            str(_info))

        # Filter
        _lvl_filter = st.multiselect(
            "Filter by level:",
            ["🔴 Critical", "🟡 Warning", "🟠 Info"],
            default=["🔴 Critical", "🟡 Warning", "🟠 Info"],
            key="alert_lvl_filter",
        )
        _filtered_alerts = _alert_df[_alert_df["Level"].isin(_lvl_filter)]

        st.dataframe(_filtered_alerts, use_container_width=True, height=420, hide_index=True)

        # Download alerts
        st.download_button(
            "⬇ Download Alert Report (CSV)",
            data=_filtered_alerts.to_csv(index=False),
            file_name=f"parking_alerts_{now.strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            key="dl_alerts_csv",
        )
