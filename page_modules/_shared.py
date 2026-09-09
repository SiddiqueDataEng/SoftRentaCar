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

GLOBAL_CSS = ""   # Theme CSS now injected globally by streamlit_app.py


def inject():
    """No-op — theme CSS is injected globally in streamlit_app.py."""
    pass


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
    # Pull accent colour from active theme if available
    try:
        from app.themes import THEMES
        import streamlit as _st
        theme_name = _st.session_state.get("selected_theme", "🌑 Dark Navy (Default)")
        theme = THEMES.get(theme_name, THEMES["🌑 Dark Navy (Default)"])
        colorway = theme["plotly_colors"]
        txt_col  = theme["text"]
        grid_col = "rgba(255,255,255,0.06)"
        bg_col   = "rgba(0,0,0,0)"
    except Exception:
        colorway = COLORS
        txt_col  = TEXT
        grid_col = GRID
        bg_col   = BG

    fig.update_layout(
        template="plotly_white",
        paper_bgcolor=bg_col, plot_bgcolor=bg_col,
        font=dict(family="Inter", color=txt_col, size=11),
        margin=dict(l=12, r=12, t=44 if title else 20, b=12),
        height=height,
        title=dict(text=title, font=dict(color=txt_col, size=13)) if title else None,
        xaxis=dict(gridcolor=grid_col, linecolor=grid_col,
                   tickfont=dict(color=txt_col), tickangle=xangle),
        yaxis=dict(gridcolor=grid_col, linecolor=grid_col,
                   tickfont=dict(color=txt_col)),
        legend=dict(bgcolor=bg_col, font=dict(color=txt_col, size=10),
                    orientation="h", yanchor="bottom", y=1.02,
                    xanchor="right", x=1) if legend else dict(visible=False),
        colorway=colorway,
    )
    return fig
