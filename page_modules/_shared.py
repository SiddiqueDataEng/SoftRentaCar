"""
Shared utilities imported by every page module.
Provides: get_data(), fmt_pkr(), apply_dark_layout(), kpi(), sec_header(), alert_box()
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# ── Brand colours ─────────────────────────────────────────────────────
BRAND    = "#E63946"
NAVY     = "#1D3557"
STEEL    = "#457B9D"
GREEN    = "#2A9D8F"
AMBER    = "#E9C46A"
ORANGE   = "#E76F51"
TEXT     = "#c8dff0"
GRID     = "rgba(255,255,255,0.06)"
BG       = "rgba(0,0,0,0)"
COLORS   = [BRAND, NAVY, STEEL, GREEN, AMBER, ORANGE, "#6A4C93", "#1982C4", "#8AC926"]

GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
html,body,[class*="css"]{ font-family:'Inter',sans-serif!important; }
#MainMenu,footer,header{ visibility:hidden; }
.stApp{ background:#0f1117; color:#e8eaf0; }
[data-testid="stSidebar"]{ background:linear-gradient(160deg,#1D3557 0%,#0f1a2b 100%); border-right:1px solid #2d4a6b; }
[data-testid="stSidebar"] *{ color:#d0dff0!important; }

.kpi-card{ background:linear-gradient(135deg,#1e2a3a 0%,#162030 100%); border:1px solid #2d4a6b;
           border-radius:12px; padding:16px 18px; text-align:center; }
.kpi-val { font-size:1.75rem; font-weight:800; color:#E63946; line-height:1.1; }
.kpi-lbl { font-size:0.72rem; color:#6a8aaa; margin-top:3px; text-transform:uppercase; letter-spacing:.06em; }
.kpi-delta-up   { font-size:0.78rem; color:#2A9D8F; margin-top:4px; }
.kpi-delta-down { font-size:0.78rem; color:#E76F51; margin-top:4px; }
.kpi-delta-neu  { font-size:0.78rem; color:#8eaac4; margin-top:4px; }

.sec-hdr{ font-size:1rem; font-weight:700; color:#c8dff0; border-left:3px solid #E63946;
          padding-left:10px; margin:18px 0 10px 0; }

.alert-critical{ background:rgba(231,111,81,.15); border:1px solid #E76F51; border-radius:8px;
                 padding:10px 14px; margin:5px 0; color:#f0a090; font-size:.85rem; }
.alert-warning { background:rgba(233,196,106,.12); border:1px solid #E9C46A; border-radius:8px;
                 padding:10px 14px; margin:5px 0; color:#f0d88a; font-size:.85rem; }
.alert-info    { background:rgba(69,123,157,.15);  border:1px solid #457B9D; border-radius:8px;
                 padding:10px 14px; margin:5px 0; color:#90bdd4; font-size:.85rem; }
.alert-success { background:rgba(42,157,143,.15);  border:1px solid #2A9D8F; border-radius:8px;
                 padding:10px 14px; margin:5px 0; color:#7dd8cc; font-size:.85rem; }

.story-card{ background:linear-gradient(135deg,#1a2840,#1e2f44); border-radius:14px;
             border:1px solid #2a3f58; padding:20px 24px; margin:10px 0; }
.story-num { font-size:2.8rem; font-weight:800; color:#E63946; line-height:1; }
.story-ttl { font-size:1rem; font-weight:700; color:#b8d4e8; margin-top:4px; }
.story-bdy { font-size:.86rem; color:#7a9ab4; margin-top:8px; line-height:1.6; }

.chat-user{ background:linear-gradient(135deg,#E63946,#c0272e); color:#fff;
            padding:10px 15px; border-radius:18px 18px 4px 18px; max-width:75%;
            margin-left:auto; font-size:.9rem; }
.chat-ai  { background:linear-gradient(135deg,#1e2a3a,#253344); color:#d8eaf6;
            padding:10px 15px; border-radius:18px 18px 18px 4px; max-width:82%;
            border:1px solid #2d4a6b; font-size:.9rem; }
.chat-ts  { font-size:.65rem; color:#4a6a84; margin-top:3px; }

::-webkit-scrollbar{ width:5px; height:5px; }
::-webkit-scrollbar-track{ background:#0f1117; }
::-webkit-scrollbar-thumb{ background:#2d4a6b; border-radius:4px; }
</style>
"""


def inject():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


@st.cache_data(ttl=3600, show_spinner=False)
def get_data() -> dict:
    """
    Load all tables. On Streamlit Cloud the data/ folder won't exist,
    so we generate it on first run and cache it in session.
    """
    from pathlib import Path
    import pandas as pd
    import random, numpy as np

    root = Path(__file__).parent.parent
    base = root / "data" / "parquet"
    csv  = root / "data" / "csv"

    tables = [
        "fleets", "vehicle_types", "vehicles", "vehicle_attributes",
        "drivers", "staff", "customers", "trips", "trip_legs", "telematics",
        "invoices", "billing_line_items", "fuel_logs", "operating_expenses",
        "maintenance", "rate_cards",
    ]

    # ── Auto-generate if data is missing (Streamlit Cloud) ────────────
    first_table_csv = csv / "trips.csv"
    if not first_table_csv.exists():
        import sys
        sys.path.insert(0, str(root))
        random.seed(42)
        np.random.seed(42)

        (root / "data" / "csv").mkdir(parents=True, exist_ok=True)
        (root / "data" / "parquet").mkdir(parents=True, exist_ok=True)

        from generators.fleets      import generate_fleets, generate_vehicle_types, generate_vehicles
        from generators.staff       import generate_drivers, generate_staff
        from generators.customers   import generate_customers
        from generators.trips       import generate_trips
        from generators.billing     import generate_billing
        from generators.fuel        import generate_fuel_logs, generate_operating_expenses
        from generators.maintenance import generate_maintenance
        from generators.rates       import generate_rate_cards

        fleets_raw  = generate_fleets()
        vtype_rows  = generate_vehicle_types()
        vehicles_raw, vattrs_raw, fleets_raw = generate_vehicles(fleets_raw)
        drivers_raw = generate_drivers()
        staff_raw   = generate_staff()
        customers_raw = generate_customers()
        trips_raw, legs_raw, telem_raw = generate_trips(vehicles_raw, drivers_raw, customers_raw)
        invoices_raw, lines_raw = generate_billing(trips_raw)
        fuel_raw    = generate_fuel_logs(trips_raw, vehicles_raw)
        opex_raw    = generate_operating_expenses(fleets_raw, drivers_raw, staff_raw)
        maint_raw   = generate_maintenance(vehicles_raw)
        rates_raw   = generate_rate_cards()

        generated = {
            "fleets": fleets_raw, "vehicle_types": vtype_rows,
            "vehicles": vehicles_raw, "vehicle_attributes": vattrs_raw,
            "drivers": drivers_raw, "staff": staff_raw,
            "customers": customers_raw, "trips": trips_raw,
            "trip_legs": legs_raw, "telematics": telem_raw,
            "invoices": invoices_raw, "billing_line_items": lines_raw,
            "fuel_logs": fuel_raw, "operating_expenses": opex_raw,
            "maintenance": maint_raw, "rate_cards": rates_raw,
        }
        for name, rows in generated.items():
            df = pd.DataFrame(rows)
            df.to_csv(csv / f"{name}.csv", index=False)
            df.to_parquet(base / f"{name}.parquet", index=False)

    # ── Load ──────────────────────────────────────────────────────────
    def _load(name):
        pq = base / f"{name}.parquet"
        return pd.read_parquet(pq) if pq.exists() else pd.read_csv(csv / f"{name}.csv")

    dfs = {t: _load(t) for t in tables}

    # ── Date parsing ──────────────────────────────────────────────────
    for col in ["booking_datetime", "pickup_datetime", "dropoff_datetime"]:
        dfs["trips"][col] = pd.to_datetime(dfs["trips"][col], errors="coerce")
    for col in ["invoice_date", "due_date"]:
        dfs["invoices"][col] = pd.to_datetime(dfs["invoices"][col], errors="coerce")
    dfs["fuel_logs"]["fill_date"]               = pd.to_datetime(dfs["fuel_logs"]["fill_date"],               errors="coerce")
    dfs["maintenance"]["maintenance_date"]       = pd.to_datetime(dfs["maintenance"]["maintenance_date"],       errors="coerce")
    dfs["maintenance"]["next_due_date"]          = pd.to_datetime(dfs["maintenance"]["next_due_date"],          errors="coerce")
    dfs["operating_expenses"]["expense_month"]   = pd.to_datetime(dfs["operating_expenses"]["expense_month"],   errors="coerce")
    dfs["telematics"]["trip_date"]               = pd.to_datetime(dfs["telematics"]["trip_date"],               errors="coerce")
    dfs["vehicles"]["insurance_expiry"]          = pd.to_datetime(dfs["vehicles"]["insurance_expiry"],          errors="coerce")
    dfs["vehicles"]["fitness_cert_expiry"]       = pd.to_datetime(dfs["vehicles"]["fitness_cert_expiry"],       errors="coerce")
    dfs["drivers"]["license_expiry"]             = pd.to_datetime(dfs["drivers"]["license_expiry"],             errors="coerce")

    # ── Derived columns ───────────────────────────────────────────────
    t = dfs["trips"]
    t["pickup_year"]  = t["pickup_datetime"].dt.year
    t["pickup_month"] = t["pickup_datetime"].dt.to_period("M").astype(str)
    t["pickup_hour"]  = t["pickup_datetime"].dt.hour
    t["pickup_dow"]   = t["pickup_datetime"].dt.day_name()
    t["revenue_pkr"]  = pd.to_numeric(t["trip_fare_pkr"], errors="coerce").fillna(0)

    inv = dfs["invoices"]
    inv["invoice_year"]  = inv["invoice_date"].dt.year
    inv["invoice_month"] = inv["invoice_date"].dt.to_period("M").astype(str)

    fl = dfs["fuel_logs"]
    fl["fill_month"] = fl["fill_date"].dt.to_period("M").astype(str)

    op = dfs["operating_expenses"]
    op["month_period"] = op["expense_month"].dt.to_period("M").astype(str)
    op["year"]         = op["expense_month"].dt.year

    return dfs


# ── UI helpers ─────────────────────────────────────────────────────────

def fmt(v: float) -> str:
    v = float(v)
    if v >= 1e9:  return f"PKR {v/1e9:.2f}B"
    if v >= 1e6:  return f"PKR {v/1e6:.1f}M"
    if v >= 1e3:  return f"PKR {v/1e3:.0f}K"
    return f"PKR {v:,.0f}"


def kpi(col, value: str, label: str, delta: str = "", pos: bool = True):
    dc = "kpi-delta-up" if pos else "kpi-delta-down"
    if delta == "": dc = "kpi-delta-neu"
    col.markdown(f"""
<div class="kpi-card">
  <div class="kpi-val">{value}</div>
  <div class="kpi-lbl">{label}</div>
  <div class="{dc}">{delta}</div>
</div>""", unsafe_allow_html=True)


def sec(title: str):
    st.markdown(f'<div class="sec-hdr">{title}</div>', unsafe_allow_html=True)


def alert_box(msg: str, level: str = "info"):
    st.markdown(f'<div class="alert-{level}">{msg}</div>', unsafe_allow_html=True)


# ── Plotly dark layout helper ──────────────────────────────────────────

def dark_layout(fig: go.Figure, title: str = "", height: int = 380,
                xangle: int = 0, legend: bool = True):
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor=BG, plot_bgcolor=BG,
        font=dict(family="Inter", color=TEXT, size=11),
        margin=dict(l=12, r=12, t=44 if title else 20, b=12),
        height=height,
        title=dict(text=title, font=dict(color=TEXT, size=13)) if title else None,
        xaxis=dict(gridcolor=GRID, linecolor=GRID, tickfont=dict(color=TEXT), tickangle=xangle),
        yaxis=dict(gridcolor=GRID, linecolor=GRID, tickfont=dict(color=TEXT)),
        legend=dict(bgcolor=BG, font=dict(color=TEXT, size=10),
                    orientation="h", yanchor="bottom", y=1.02,
                    xanchor="right", x=1) if legend else dict(visible=False),
        colorway=COLORS,
    )
    return fig
