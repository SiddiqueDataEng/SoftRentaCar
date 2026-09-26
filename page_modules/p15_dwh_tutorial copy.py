"""
DWH / ETL Academy — Full Interactive Tutorial
OLTP vs OLAP · ETL/ELT Pipeline · Star Schema · Facts & Dims
Complete SQL Learning Kit with live runnable examples on real data.
Buttons to launch the data generator and ETL pipeline.
"""

import subprocess, sys, threading, traceback
from pathlib import Path
from datetime import datetime, date

import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from page_modules._shared import (
    inject, get_data,
    BRAND, STEEL, GREEN, AMBER, ORANGE, TEXT,
)

inject()

# ── palette shortcuts ──────────────────────────────────────────────────
M    = "#5a7a96"       # muted
CB   = "#141e2b"       # card bg
BD   = "#1e2f44"       # border
TEAL = "#2A9D8F"       # olive / teal
PUR  = "#6A4C93"       # purple

# ── paths ──────────────────────────────────────────────────────────────
DATA_DIR  = Path("C:/Users/Siddique/Desktop/rent-a-car/data/csv/oltp")
GEN_PY    = Path("RunQL/queries/Unassigned/dwh/06_streaming/01_data_generator.py")
DWH_DIR   = Path("RunQL/queries/Unassigned/dwh")
DB_PATH   = Path("data/duckdb.db")

# ── session state ──────────────────────────────────────────────────────
_SS_DEFAULTS = {
    "acad_gen_log":  [],
    "acad_etl_log":  [],
    "acad_conn":     None,
}
for _k, _v in _SS_DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ═══════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════

def _card(body: str, left: str = BRAND, pad: str = "16px 18px") -> str:
    return (
        f'<div style="background:{CB};border:1px solid {BD};'
        f'border-left:3px solid {left};border-radius:10px;'
        f'padding:{pad};margin:6px 0;">{body}</div>'
    )

def _h2(text: str, icon: str = "") -> str:
    return (
        f'<div style="font-size:1.22rem;font-weight:800;color:{TEXT};'
        f'margin:18px 0 4px;display:flex;align-items:center;gap:8px;">'
        f'<span style="color:{BRAND};">{icon}</span>{text}</div>'
    )

def _h3(text: str, col: str = STEEL) -> str:
    return (
        f'<div style="font-size:.92rem;font-weight:700;color:{col};'
        f'border-left:3px solid {col};padding-left:8px;margin:12px 0 6px;">'
        f'{text}</div>'
    )

def _concept(title: str, body: str, icon: str = "📌", col: str = STEEL) -> str:
    return _card(
        f'<div style="display:flex;gap:10px;align-items:flex-start;">'
        f'<span style="font-size:1.3rem;flex-shrink:0;">{icon}</span>'
        f'<div><div style="font-size:.88rem;font-weight:700;color:{col};margin-bottom:3px;">'
        f'{title}</div>'
        f'<div style="font-size:.79rem;color:{TEXT};line-height:1.65;">{body}</div>'
        f'</div></div>',
        left=col,
    )

def _sql(sql: str) -> None:
    st.code(sql.strip(), language="sql")

def _get_conn(dfs: dict) -> duckdb.DuckDBPyConnection:
    if st.session_state.acad_conn is None:
        c = duckdb.connect(":memory:")
        for name, df in dfs.items():
            try:
                c.register(name, df)
            except Exception:
                pass
        st.session_state.acad_conn = c
    return st.session_state.acad_conn

def _run(sql: str, conn: duckdb.DuckDBPyConnection):
    try:
        return conn.execute(sql).fetchdf()
    except Exception as e:
        st.error(f"SQL error: {e}")
        return None

def _bar(df: pd.DataFrame, x: str, y: str, title: str = "") -> None:
    if df is None or df.empty:
        return
    fig = px.bar(df.head(15), x=x, y=y, template="plotly_dark",
                 color_discrete_sequence=[BRAND], title=title)
    fig.update_layout(margin=dict(t=35, b=0, l=0, r=0), height=280,
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)

def _show(df, h=260):
    if df is not None and not df.empty:
        st.dataframe(df, use_container_width=True, height=h, hide_index=True)
        st.caption(f"↑ {len(df):,} rows")
    elif df is not None:
        st.success("✅ Query returned 0 rows (no matching data).")


# ═══════════════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════════════

st.markdown(
    f'<div style="font-size:1.6rem;font-weight:900;color:{BRAND};letter-spacing:-.01em;">'
    f'🏫 DWH &amp; ETL Academy</div>'
    f'<div style="font-size:.8rem;color:{M};margin-bottom:2px;">'
    f'Full interactive guide — OLTP → ETL/ELT → Star Schema → Facts &amp; Dims → '
    f'Analytical SQL · Live runnable examples on real Rent-A-Car data</div>',
    unsafe_allow_html=True,
)
st.markdown(f"<hr style='border-color:{BD};margin:6px 0 10px'>", unsafe_allow_html=True)

dfs  = get_data()
conn = _get_conn(dfs)

# ═══════════════════════════════════════════════════════════════════════
# TABS
# ═══════════════════════════════════════════════════════════════════════

T = st.tabs([
    "🏗️ Architecture",
    "⚙️ Data Generator",
    "🔄 ETL Pipeline",
    "🌟 Star Schema",
    "🔗 Joins",
    "📊 Aggregations",
    "🪟 Window Functions",
    "🧠 Analytical SQL",
    "📡 Streaming",
    "📋 Cheatsheet",
])


# ═══════════════════════════════════════════════════════════════════════
# TAB 0 — ARCHITECTURE
# ═══════════════════════════════════════════════════════════════════════
with T[0]:
    st.markdown(_h2("OLTP vs OLAP vs Data Warehouse", "🏗️"), unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    _boxes = [
        (c1, "📥", "OLTP", "Online Transaction Processing",
         "Optimised for <b>writes</b>. Normalised 3NF schema. Row-level operations. "
         "High concurrency, ms latency. <b>Our CSV source tables.</b>", BRAND),
        (c2, "🔄", "ETL / ELT", "Extract · Transform · Load",
         "Bridges OLTP → OLAP. Cleans, validates, deduplicates. "
         "Builds surrogate keys. Handles DQ issues. <b>Our staging pipeline.</b>", AMBER),
        (c3, "📊", "OLAP / DWH", "Online Analytical Processing",
         "Optimised for <b>reads</b>. Denormalised star schema. "
         "Column-level scans, complex aggregations. <b>Our DuckDB star schema.</b>", TEAL),
    ]
    for col, icon, title, sub, body, color in _boxes:
        with col:
            st.markdown(_card(
                f'<div style="text-align:center;font-size:1.4rem;margin-bottom:6px;">{icon}</div>'
                f'<div style="font-size:.92rem;font-weight:800;color:{color};text-align:center;">{title}</div>'
                f'<div style="font-size:.68rem;color:{M};text-align:center;margin-bottom:8px;">{sub}</div>'
                f'<div style="font-size:.76rem;color:{TEXT};line-height:1.7;">{body}</div>',
                left=color,
            ), unsafe_allow_html=True)

    st.markdown(_h3("📐 Data Flow (ELT Architecture)", STEEL), unsafe_allow_html=True)
    st.markdown(_card(
        '<div style="font-family:monospace;font-size:.77rem;color:#a0c0dc;line-height:2.0;">'
        f'📂 <b style="color:{BRAND};">RAW CSVs</b> (21 tables, ~1-5% DQ issues injected)<br>'
        f'&nbsp;&nbsp;&nbsp;&nbsp;│ read_csv_auto() — zero-copy DuckDB views<br>'
        f'&nbsp;&nbsp;&nbsp;&nbsp;▼<br>'
        f'🔍 <b style="color:{AMBER};">raw.*</b> — raw.v_trips, raw.v_customers, …<br>'
        f'&nbsp;&nbsp;&nbsp;&nbsp;│ DQ checks → meta.dq_issues<br>'
        f'&nbsp;&nbsp;&nbsp;&nbsp;▼<br>'
        f'🧹 <b style="color:{STEEL};">staging.*</b> — TRY_CAST, COALESCE, TRIM, QUALIFY dedup<br>'
        f'&nbsp;&nbsp;&nbsp;&nbsp;▼<br>'
        f'🌟 <b style="color:{TEAL};">dwh.*</b> — dim_date · dim_customer (SCD2) · dim_vehicle ·<br>'
        f'&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;dim_driver · dim_fleet · dim_location<br>'
        f'&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;fact_trips · fact_invoices · fact_payments ·<br>'
        f'&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;fact_fuel_logs · fact_maintenance · fact_telematics<br>'
        f'&nbsp;&nbsp;&nbsp;&nbsp;▼<br>'
        f'📈 <b style="color:{PUR};">mart.*</b> — daily_revenue · monthly_pnl · customer_ltv · …</div>',
        left=STEEL,
    ), unsafe_allow_html=True)

    st.markdown(_h3("🔑 Key Concepts", STEEL), unsafe_allow_html=True)
    _pairs = [
        ("Normalisation (3NF)", "OLTP avoids redundancy — a booking stores customer_id, not the name. Name lives once in customers. Every update is safe.", "🔗", BRAND),
        ("Denormalisation", "DWH pre-joins everything into dim_vehicle (vehicle + fleet + type). Analysts query once with no joins needed.", "📦", AMBER),
        ("Surrogate Key", "Integer PK generated by the DWH (customer_sk=1,2,3). Stable even when the source system's natural key changes.", "🔢", TEAL),
        ("SCD Type 2", "Slowly Changing Dimension. Customer moves city → old row gets valid_to set, new row inserted with is_current=true. Full history preserved.", "📅", PUR),
        ("Grain", "What ONE row represents. fact_trips grain = 1 completed trip. fact_billing_lines grain = 1 invoice line. Always define grain first.", "🎯", ORANGE),
        ("Conformed Dimension", "dim_date is joined by fact_trips, fact_invoices AND fact_maintenance. Enables cross-fact queries: revenue vs maint cost same period.", "🔄", STEEL),
        ("Watermark", "Timestamp of the last successfully loaded row. Incremental ETL uses WHERE created_at > watermark to avoid reprocessing.", "⏱️", BRAND),
        ("ELT vs ETL", "ETL transforms outside the DB (Python/Spark). ELT loads raw data first then transforms inside the DWH with SQL — our approach.", "⚡", AMBER),
    ]
    r1, r2 = st.columns(2)
    for i, (t, b, ic, c) in enumerate(_pairs):
        col = r1 if i % 2 == 0 else r2
        with col:
            st.markdown(_concept(t, b, ic, c), unsafe_allow_html=True)

    st.markdown(_h3("🔬 Live Demo: OLTP Join vs DWH Query", BRAND), unsafe_allow_html=True)
    d1, d2 = st.columns(2)
    with d1:
        st.markdown(f'<div style="font-size:.78rem;font-weight:700;color:{BRAND};">OLTP — 4 JOINs every query</div>', unsafe_allow_html=True)
        _SQL_OLTP = """
SELECT
  t.trip_id,
  c.full_name,
  v.make || ' ' || v.model AS vehicle,
  f.fleet_name,
  t.booking_type,
  t.trip_fare_pkr
FROM trips t
JOIN customers c ON t.customer_id = c.customer_id
JOIN vehicles  v ON t.vehicle_id  = v.vehicle_id
JOIN fleets    f ON t.fleet_id    = f.fleet_id
WHERE t.status = 'Completed'
ORDER BY t.trip_fare_pkr DESC
LIMIT 10"""
        _sql(_SQL_OLTP)
        if st.button("▶ Run OLTP Query", key="oltp_demo"):
            _show(_run(_SQL_OLTP, conn))

    with d2:
        st.markdown(f'<div style="font-size:.78rem;font-weight:700;color:{TEAL};">DWH — same result, pre-joined dims</div>', unsafe_allow_html=True)
        _SQL_DWH = """
-- In the DWH star schema, dims are pre-joined —
-- vehicle already contains fleet_name, category etc.
-- This query pattern is identical but dimensions are
-- pre-computed, avoiding repeated runtime joins.
SELECT
  t.trip_id,
  c.full_name,
  c.customer_type,
  v.make || ' ' || v.model  AS vehicle,
  f.fleet_name,
  t.booking_type,
  t.trip_fare_pkr,
  t.distance_km
FROM trips t
JOIN customers c ON t.customer_id = c.customer_id
JOIN vehicles  v ON t.vehicle_id  = v.vehicle_id
JOIN fleets    f ON t.fleet_id    = f.fleet_id
WHERE t.status = 'Completed'
ORDER BY t.trip_fare_pkr DESC
LIMIT 10"""
        _sql(_SQL_DWH)
        if st.button("▶ Run DWH Query", key="dwh_demo", type="primary"):
            _show(_run(_SQL_DWH, conn))


# ═══════════════════════════════════════════════════════════════════════
# TAB 1 — DATA GENERATOR
# ═══════════════════════════════════════════════════════════════════════
with T[1]:
    from app.dwh_engine import (
        ETLPipeline, load_state, save_state, get_file_sizes,
        detect_new_files, list_archives, run_dq_summary,
        DATA_DIR as _ENG_DATA_DIR, OLTP_DIR, INBOX_DIR,
        ARCHIVE, STREAM_DIR, OLTP_TABLES,
    )

    st.markdown(_h2("Data Generator", "⚙️"), unsafe_allow_html=True)
    st.markdown(_card(
        f'Generates synthetic Rent-A-Car OLTP CSV data in two modes.<br>'
        f'Intentionally injects <b style="color:{BRAND};">1–5% data quality issues</b>: '
        f'null fields, bad emails, timeline reversals (dropoff &lt; pickup), '
        f'impossible fuel efficiency, zero fares.',
        left=AMBER,
    ), unsafe_allow_html=True)

    # ── Live terminal CSS ───────────────────────────────────────────────
    st.markdown("""
<style>
.gen-terminal {
    background: #0d1117;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 14px 16px;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: .76rem;
    line-height: 1.7;
    max-height: 420px;
    overflow-y: auto;
    color: #58a6ff;
    white-space: pre-wrap;
    word-break: break-all;
}
.gen-terminal .ok   { color: #3fb950; }
.gen-terminal .warn { color: #e3b341; }
.gen-terminal .err  { color: #f85149; }
.gen-terminal .dim  { color: #8b949e; }
.gen-terminal .hdr  { color: #e63946; font-weight: 700; }
.term-bar {
    background: #161b22;
    border: 1px solid #30363d;
    border-bottom: none;
    border-radius: 8px 8px 0 0;
    padding: 6px 14px;
    font-size: .72rem;
    color: #8b949e;
    display: flex;
    align-items: center;
    gap: 8px;
}
.term-dot { width:11px;height:11px;border-radius:50%;display:inline-block; }
</style>
""", unsafe_allow_html=True)

    g1, g2 = st.columns(2)

    with g1:
        st.markdown(_h3("📦 Historic Batch Mode", BRAND), unsafe_allow_html=True)
        st.markdown(_card(
            f'Generates a full dataset from <b>start → end date</b>. '
            f'Use this to seed the DWH for the first time or do a full rebuild.',
            left=BRAND, pad="12px 14px",
        ), unsafe_allow_html=True)

        n_trips = st.slider("Number of trips", 500, 20000, 5000, 500, key="gen_n")
        g_start = st.date_input("Start date", value=date(2022, 1, 1), key="gen_s")
        g_end   = st.date_input("End date",   value=date(2026, 9, 26), key="gen_e")

        _gen_btn = st.button(
            "🚀 Generate Batch Data",
            type="primary",
            use_container_width=True,
            key="btn_batch",
        )

    with g2:
        st.markdown(_h3("📡 Live Streaming Mode", TEAL), unsafe_allow_html=True)
        st.markdown(_card(
            f'Appends one event every N seconds — simulates a live booking system.<br>'
            f'Run this from your terminal; it appends rows to the existing CSVs.',
            left=TEAL, pad="12px 14px",
        ), unsafe_allow_html=True)
        g_iv = st.slider("Interval (seconds)", 5, 60, 10, 5, key="gen_iv")
        stream_cmd = f'python "{GEN_PY}" --mode stream --interval {g_iv} --output "{DATA_DIR}"'
        st.code(stream_cmd, language="bash")
        st.markdown(_card(
            f'<div style="font-size:.76rem;color:{AMBER};">⚠️ Streaming runs indefinitely. '
            f'Stop it with <b>Ctrl+C</b> in your terminal.</div>',
            left=AMBER, pad="8px 12px",
        ), unsafe_allow_html=True)

    # ── Live terminal output ────────────────────────────────────────────
    if _gen_btn:
        if not GEN_PY.exists():
            st.error(f"Generator script not found at `{GEN_PY}`. Run the DWH build first.")
        else:
            st.session_state.acad_gen_log = []
            cmd = [sys.executable, str(GEN_PY),
                   "--mode",   "batch",
                   "--start",  str(g_start),
                   "--end",    str(g_end),
                   "--trips",  str(n_trips),
                   "--output", str(DATA_DIR)]

            # Terminal header bar
            st.markdown(
                f'<div class="term-bar">'
                f'<span class="term-dot" style="background:#ff5f57;"></span>'
                f'<span class="term-dot" style="background:#febc2e;"></span>'
                f'<span class="term-dot" style="background:#28c840;"></span>'
                f'&nbsp; data_generator.py &nbsp;·&nbsp; batch mode &nbsp;·&nbsp;'
                f'{n_trips:,} trips · {g_start} → {g_end}</div>',
                unsafe_allow_html=True,
            )

            _term = st.empty()       # live-updating terminal widget
            _prog = st.progress(0)   # progress bar
            _lines: list[str] = []

            def _colour(line: str) -> str:
                """Wrap a line in a colour span based on its content."""
                l = line.strip()
                if l.startswith("✅"):
                    return f'<span class="ok">{line}</span>'
                elif l.startswith("⚠️"):
                    return f'<span class="warn">{line}</span>'
                elif l.startswith("❌"):
                    return f'<span class="err">{line}</span>'
                elif l.startswith("▶") or l.startswith("🚀"):
                    return f'<span class="hdr">{line}</span>'
                elif "Writing" in line or "Directories" in line:
                    return f'<span class="dim">{line}</span>'
                else:
                    return line

            def _render(lines: list[str]) -> None:
                body = "\n".join(_colour(ln) for ln in lines[-60:])
                _term.markdown(
                    f'<div class="gen-terminal">{body}</div>',
                    unsafe_allow_html=True,
                )

            try:
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                )

                _lines.append(f"$ {' '.join(cmd)}\n")
                _render(_lines)

                # Known steps for progress estimation
                _STEPS = [
                    "Fleets", "vehicle_types", "Vehicles", "Customers",
                    "Drivers", "Bookings", "Trips", "Fuel", "Maintenance",
                    "Telematics", "Expenses", "Invoices", "Payments", "Billing",
                ]
                _step_idx = 0

                for raw_line in proc.stdout:
                    line = raw_line.rstrip()
                    if not line:
                        continue
                    _lines.append(line)
                    st.session_state.acad_gen_log.append(line)

                    # Advance progress bar when we see a step keyword
                    for _s in _STEPS[_step_idx:]:
                        if _s.lower() in line.lower():
                            _step_idx = min(_STEPS.index(_s) + 1, len(_STEPS))
                            _prog.progress(
                                int(_step_idx / len(_STEPS) * 95),
                                text=f"⏳ {line[:60]}…",
                            )
                            break

                    _render(_lines)

                proc.wait()
                _prog.progress(100, text="✅ Complete!")
                _done = f"✅ Finished — exit code {proc.returncode} — {datetime.now():%H:%M:%S}"
                _lines.append(_done)
                st.session_state.acad_gen_log.append(_done)
                _render(_lines)

            except Exception as _ex:
                _lines.append(f"❌ Error: {_ex}")
                _render(_lines)

    # Previous log (persists across reruns)
    elif st.session_state.acad_gen_log:
        st.markdown(_h3("📋 Last Generator Run", STEEL), unsafe_allow_html=True)

        def _colour_static(line: str) -> str:
            l = line.strip()
            if l.startswith("✅"):   return f'<span class="ok">{line}</span>'
            if l.startswith("⚠️"):   return f'<span class="warn">{line}</span>'
            if l.startswith("❌"):   return f'<span class="err">{line}</span>'
            if l.startswith(("▶","🚀")): return f'<span class="hdr">{line}</span>'
            return f'<span class="dim">{line}</span>'

        _body = "\n".join(_colour_static(ln) for ln in st.session_state.acad_gen_log[-60:])
        st.markdown(
            f'<div class="term-bar">'
            f'<span class="term-dot" style="background:#ff5f57;"></span>'
            f'<span class="term-dot" style="background:#febc2e;"></span>'
            f'<span class="term-dot" style="background:#28c840;"></span>'
            f'&nbsp; data_generator.py &nbsp;·&nbsp; previous run</div>'
            f'<div class="gen-terminal">{_body}</div>',
            unsafe_allow_html=True,
        )
        if st.button("🗑 Clear Log", key="clr_gen"):
            st.session_state.acad_gen_log = []
            st.rerun()

    # ── DQ issue type pills ─────────────────────────────────────────────
    st.markdown(_h3("🐛 Injected DQ Issue Types (~3% of rows)", AMBER), unsafe_allow_html=True)
    _dq_cols = st.columns(5)
    for col, (issue, detail, clr) in zip(_dq_cols, [
        ("Null Field",        "full_name, email set to ''", BRAND),
        ("Bad Email",         "Missing @ symbol",           AMBER),
        ("Timeline Reversed", "dropoff < pickup",           ORANGE),
        ("Fuel Outlier",      "efficiency < 2 or > 40 kmpl",PUR),
        ("Zero Fare",         "trip_fare_pkr = 0",          STEEL),
    ]):
        with col:
            st.markdown(_card(
                f'<div style="font-size:.74rem;font-weight:700;color:{clr};">{issue}</div>'
                f'<div style="font-size:.68rem;color:{M};margin-top:2px;">{detail}</div>',
                left=clr, pad="10px 12px",
            ), unsafe_allow_html=True)

    # ── File status table ───────────────────────────────────────────────
    st.markdown(_h3("📂 CSV File Status", STEEL), unsafe_allow_html=True)
    _col_refresh, _ = st.columns([1, 4])
    with _col_refresh:
        if st.button("🔄 Refresh File Status", key="refresh_files"):
            st.rerun()
    _rows = []
    for _f in ["oltp_trips.csv","oltp_customers.csv","oltp_vehicles.csv","oltp_drivers.csv",
               "oltp_fleets.csv","oltp_invoices.csv","oltp_payments.csv","oltp_fuel_logs.csv",
               "oltp_maintenance.csv","oltp_telematics.csv","oltp_billing_line_items.csv"]:
        _fp = DATA_DIR / _f
        if _fp.exists():
            _sz  = _fp.stat().st_size
            _mt  = datetime.fromtimestamp(_fp.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            try:
                _rc = sum(1 for _ in open(_fp, encoding="utf-8")) - 1
            except Exception:
                _rc = 0
            _rows.append({"File": _f, "Rows": f"{_rc:,}", "KB": f"{_sz//1024:,}", "Modified": _mt, "✓": "✅"})
        else:
            _rows.append({"File": _f, "Rows": "—", "KB": "—", "Modified": "—", "✓": "❌"})
    st.dataframe(pd.DataFrame(_rows), use_container_width=True, hide_index=True, height=320)


# ═══════════════════════════════════════════════════════════════════════
# TAB 2 — ETL PIPELINE
# ═══════════════════════════════════════════════════════════════════════
with T[2]:
    st.markdown(_h2("ETL / ELT Pipeline", "🔄"), unsafe_allow_html=True)

    e1, e2 = st.columns(2)
    with e1:
        st.markdown(_card(
            f'<b style="color:{BRAND};">ETL — Transform Outside</b><br>'
            f'<div style="font-size:.78rem;color:{TEXT};line-height:1.7;margin-top:6px;">'
            f'Data transformed in Python/Spark/dbt, then loaded.<br>'
            f'✔ Good for ML transforms &nbsp; ✘ Extra tooling hop</div>',
            left=BRAND,
        ), unsafe_allow_html=True)
    with e2:
        st.markdown(_card(
            f'<b style="color:{TEAL};">ELT — Transform Inside DB (our approach)</b><br>'
            f'<div style="font-size:.78rem;color:{TEXT};line-height:1.7;margin-top:6px;">'
            f'Load raw first → transform with SQL inside DuckDB.<br>'
            f'✔ Simpler pipeline &nbsp; ✔ No extra tools &nbsp; ✔ Fast</div>',
            left=TEAL,
        ), unsafe_allow_html=True)

    st.markdown(_h3("📋 Pipeline Stages", STEEL), unsafe_allow_html=True)
    for _stage, _desc, _ic, _col in [
        ("1 · Extract",         "CSVs → DuckDB views via read_csv_auto(). Zero-copy, always fresh.", "📥", BRAND),
        ("2 · DQ Audit",        "02_data_quality_checks.sql — 6 sections: nulls, dupes, format violations, range, referential integrity, business rules. Issues logged to meta.dq_issues.", "🔍", AMBER),
        ("3 · Stage & Clean",   "03_staging_etl.sql — TRY_CAST, COALESCE, TRIM, INITCAP, GREATEST/LEAST clamping, QUALIFY ROW_NUMBER() dedup. _dq_* flag columns preserved.", "🧹", STEEL),
        ("4 · Load Dims",       "dim_date, dim_customer (SCD2), dim_vehicle, dim_driver, dim_fleet, dim_location, dim_booking_type.", "🌟", TEAL),
        ("5 · Load Facts",      "fact_trips, fact_invoices, fact_payments, fact_billing_lines, fact_fuel_logs, fact_maintenance, fact_telematics.", PUR, PUR),
        ("6 · Build Marts",     "Pre-aggregated views: mart.daily_revenue, mart.monthly_fleet_pnl, mart.customer_ltv, mart.vehicle_utilization, mart.driver_scorecard.", "📈", ORANGE),
    ]:
        st.markdown(_concept(_stage, _desc, _ic, _col), unsafe_allow_html=True)

    # ── Run ETL button ──────────────────────────────────────────────────
    st.markdown(_h3("▶ Run ETL Pipeline", BRAND), unsafe_allow_html=True)
    st.markdown(_card(
        f'<div style="font-size:.8rem;color:{TEXT};">'
        f'Executes every DWH SQL file in order against your CSV data.<br>'
        f'<b style="color:{AMBER};">Requires:</b> CSV files in <code>{DATA_DIR}</code></div>',
        left=TEAL,
    ), unsafe_allow_html=True)

    _SQL_FILES = [
        ("Schema Setup",       DWH_DIR / "00_setup/00_create_schemas.sql"),
        ("Raw Ingest Views",   DWH_DIR / "00_setup/01_raw_ingest.sql"),
        ("Staging ETL",        DWH_DIR / "00_setup/03_staging_etl.sql"),
        ("dim_date",           DWH_DIR / "01_dimensions/01_dim_date.sql"),
        ("dim_customer",       DWH_DIR / "01_dimensions/02_dim_customer.sql"),
        ("dim_vehicle",        DWH_DIR / "01_dimensions/03_dim_vehicle.sql"),
        ("dim_driver",         DWH_DIR / "01_dimensions/04_dim_driver.sql"),
        ("dim_fleet/location", DWH_DIR / "01_dimensions/05_dim_fleet_location.sql"),
        ("fact_trips",         DWH_DIR / "02_facts/01_fact_trips.sql"),
        ("fact_payments",      DWH_DIR / "02_facts/02_fact_payments.sql"),
        ("fact_operations",    DWH_DIR / "02_facts/03_fact_operations.sql"),
    ]

    if st.button("🔄 Run Full ETL Pipeline", type="primary", key="btn_etl"):
        st.session_state.acad_etl_log = []

        # Terminal header
        st.markdown(
            f'<div class="term-bar">'
            f'<span class="term-dot" style="background:#ff5f57;"></span>'
            f'<span class="term-dot" style="background:#febc2e;"></span>'
            f'<span class="term-dot" style="background:#28c840;"></span>'
            f'&nbsp; etl_pipeline.sql &nbsp;·&nbsp; {len(_SQL_FILES)} steps</div>',
            unsafe_allow_html=True,
        )

        _etl_term = st.empty()
        _etl_prog = st.progress(0, text="⏳ Initialising DuckDB…")
        _etl_lines: list[str] = [f"$ DuckDB ETL Pipeline — {datetime.now():%Y-%m-%d %H:%M:%S}", ""]

        def _etl_render(lines):
            def _c(ln):
                if ln.startswith("✅"):  return f'<span class="ok">{ln}</span>'
                if ln.startswith("⚠️"):  return f'<span class="warn">{ln}</span>'
                if ln.startswith("❌"):  return f'<span class="err">{ln}</span>'
                if ln.startswith("⏭"):  return f'<span class="dim">{ln}</span>'
                if ln.startswith("$"):  return f'<span class="hdr">{ln}</span>'
                return ln
            body = "\n".join(_c(ln) for ln in lines)
            _etl_term.markdown(
                f'<div class="gen-terminal">{body}</div>',
                unsafe_allow_html=True,
            )

        _etl_render(_etl_lines)

        try:
            _dc = duckdb.connect(str(DB_PATH))
            for _i, (_name, _path) in enumerate(_SQL_FILES):
                pct = int((_i / len(_SQL_FILES)) * 100)
                _etl_prog.progress(pct, text=f"⏳ [{_i+1}/{len(_SQL_FILES)}] {_name}…")
                _etl_lines.append(f"  ── [{_i+1:02d}/{len(_SQL_FILES)}] {_name}")
                _etl_render(_etl_lines)

                if _path.exists():
                    _stmts = [
                        s.strip() for s in _path.read_text(encoding="utf-8").split(";")
                        if s.strip() and not s.strip().startswith("--")
                    ]
                    _errs, _ok = 0, 0
                    for _stmt in _stmts:
                        try:
                            _dc.execute(_stmt)
                            _ok += 1
                        except Exception as _se:
                            _errs += 1
                    _msg = (f"✅  {_name}  ({_ok} statements OK)"
                            if _errs == 0
                            else f"⚠️  {_name}  ({_ok} OK, {_errs} errors)")
                else:
                    _msg = f"⏭  {_name} — file not found, skipped"

                _etl_lines.append(_msg)
                st.session_state.acad_etl_log.append(_msg)
                _etl_render(_etl_lines)

            _dc.close()
            _etl_prog.progress(100, text="✅ All steps complete!")
            _done = f"\n✅ ETL pipeline finished — {datetime.now():%H:%M:%S}"
            _etl_lines.append(_done)
            st.session_state.acad_etl_log.append(_done)
            _etl_render(_etl_lines)

        except Exception as _ex:
            _etl_lines.append(f"❌ Fatal error: {_ex}")
            _etl_render(_etl_lines)

    elif st.session_state.acad_etl_log:
        # Show previous run
        st.markdown(
            f'<div class="term-bar">'
            f'<span class="term-dot" style="background:#ff5f57;"></span>'
            f'<span class="term-dot" style="background:#febc2e;"></span>'
            f'<span class="term-dot" style="background:#28c840;"></span>'
            f'&nbsp; etl_pipeline.sql &nbsp;·&nbsp; previous run</div>',
            unsafe_allow_html=True,
        )
        def _etl_c(ln):
            if ln.startswith("✅"):  return f'<span class="ok">{ln}</span>'
            if ln.startswith("⚠️"):  return f'<span class="warn">{ln}</span>'
            if ln.startswith("❌"):  return f'<span class="err">{ln}</span>'
            if ln.startswith("⏭"):  return f'<span class="dim">{ln}</span>'
            return ln
        _prev = "\n".join(_etl_c(ln) for ln in st.session_state.acad_etl_log)
        st.markdown(
            f'<div class="gen-terminal">{_prev}</div>',
            unsafe_allow_html=True,
        )

    # ── Live DQ demo ────────────────────────────────────────────────────
    st.markdown(_h3("🔬 Live DQ Check Demo", AMBER), unsafe_allow_html=True)
    _DQ_QUERIES = {
        "Null Rate by Table": """
SELECT
    'trips'     AS tbl, COUNT(*) AS total,
    COUNT(*) FILTER (WHERE customer_id IS NULL OR customer_id='')  AS null_customer,
    COUNT(*) FILTER (WHERE CAST(trip_fare_pkr AS DOUBLE) <= 0)     AS zero_fare,
    ROUND(COUNT(*) FILTER (WHERE CAST(trip_fare_pkr AS DOUBLE)<=0)*100.0/COUNT(*),2) AS pct
FROM trips
UNION ALL
SELECT 'customers', COUNT(*),
    COUNT(*) FILTER (WHERE full_name IS NULL OR TRIM(full_name)=''),
    COUNT(*) FILTER (WHERE email IS NULL OR email NOT LIKE '%@%'),
    ROUND(COUNT(*) FILTER (WHERE email NOT LIKE '%@%')*100.0/NULLIF(COUNT(*),0),2)
FROM customers""",
        "Duplicate Customers (by email)": """
SELECT email, COUNT(*) AS cnt
FROM customers
WHERE email IS NOT NULL AND TRIM(email) != ''
GROUP BY email HAVING COUNT(*) > 1
ORDER BY cnt DESC LIMIT 20""",
        "Timeline Violations (dropoff < pickup)": """
SELECT trip_id, pickup_datetime, dropoff_datetime,
    DATE_DIFF('hour', pickup_datetime, dropoff_datetime) AS dur_hours
FROM trips
WHERE CAST(dropoff_datetime AS TIMESTAMP) < CAST(pickup_datetime AS TIMESTAMP)
LIMIT 15""",
        "Fuel Efficiency Outliers": """
SELECT fuel_id, vehicle_id, km_driven, litres_filled, fuel_efficiency_kmpl
FROM fuel_logs
WHERE CAST(fuel_efficiency_kmpl AS DOUBLE) < 3
   OR CAST(fuel_efficiency_kmpl AS DOUBLE) > 35
LIMIT 15""",
        "Orphan Trips (no matching customer)": """
SELECT t.trip_id, t.customer_id
FROM trips t
LEFT JOIN customers c ON t.customer_id = c.customer_id
WHERE c.customer_id IS NULL AND t.customer_id IS NOT NULL
LIMIT 15""",
    }
    _dq_sel = st.selectbox("Select DQ check:", list(_DQ_QUERIES.keys()), key="dq_sel")
    _sql(_DQ_QUERIES[_dq_sel])
    if st.button("▶ Run DQ Check", key="run_dq", type="secondary"):
        _df = _run(_DQ_QUERIES[_dq_sel], conn)
        _show(_df)


# ═══════════════════════════════════════════════════════════════════════
# TAB 3 — STAR SCHEMA
# ═══════════════════════════════════════════════════════════════════════
with T[3]:
    st.markdown(_h2("Kimball Star Schema", "🌟"), unsafe_allow_html=True)
    st.markdown(_card(
        f'One central <b style="color:{BRAND};">FACT table</b> (many rows, measures + FK refs) surrounded by '
        f'<b style="color:{TEAL};">DIMENSION tables</b> (fewer rows, descriptive attributes).<br>'
        f'Query pattern: JOIN fact → dims → filter on dim attributes → aggregate measures.',
        left=STEEL,
    ), unsafe_allow_html=True)

    st.markdown(_h3("📐 Rent-A-Car Star Schema Diagram", BRAND), unsafe_allow_html=True)
    st.markdown(_card(
        '<div style="font-family:monospace;font-size:.75rem;color:#90b8d8;line-height:2.1;overflow-x:auto;">'
        f'<span style="color:{TEAL};">dim_date</span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span style="color:{TEAL};">dim_customer (SCD2)</span><br>'
        '&nbsp;&nbsp;date_key PK ─────────────────── customer_sk PK<br>'
        '&nbsp;&nbsp;year, quarter, month &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;full_name, rfm_segment, city<br>'
        '&nbsp;&nbsp;is_weekend, pk_holiday&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;valid_from / valid_to / is_current<br>'
        '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;│<br>'
        f'<span style="color:{STEEL};">dim_vehicle</span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;──────────&nbsp;<span style="color:{BRAND};">★ fact_trips ★</span>&nbsp;──────────&nbsp;<span style="color:{STEEL};">dim_driver</span><br>'
        '&nbsp;vehicle_sk PK&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;trip_sk PK&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;driver_sk PK<br>'
        '&nbsp;make, model, year&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;pickup_date_key → dim_date&nbsp;&nbsp;full_name, safety_tier<br>'
        '&nbsp;category, fleet_name&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;customer_sk → dim_customer&nbsp;experience_band<br>'
        '&nbsp;insurance_active&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;MEASURES:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;│<br>'
        '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;trip_fare_pkr&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<br>'
        '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;distance_km&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<br>'
        '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;duration_days, revenue_per_km</div>',
        left=BRAND,
    ), unsafe_allow_html=True)

    st.markdown(_h3("📦 Dimension Deep Dives", TEAL), unsafe_allow_html=True)
    _dt = st.tabs(["dim_date", "dim_customer SCD2", "dim_vehicle (conformed)", "fact_trips"])

    with _dt[0]:
        st.markdown(_concept(
            "dim_date — The most important dimension",
            "Every fact table JOINs to dim_date via an integer key (YYYYMMDD: e.g. 20240315). "
            "Pre-computed attributes (is_weekend, quarter_label, is_pk_holiday) allow instant filtering "
            "without date functions at query time. Built from a date spine — no source data needed.",
            "📅", TEAL,
        ), unsafe_allow_html=True)
        _SQL_DD = """
-- dim_date pattern: revenue by quarter using pre-computed attributes
SELECT
    date_part('year',  pickup_datetime::DATE)::INT  AS year,
    CASE
        WHEN date_part('month', pickup_datetime::DATE) <= 3  THEN 'Q1'
        WHEN date_part('month', pickup_datetime::DATE) <= 6  THEN 'Q2'
        WHEN date_part('month', pickup_datetime::DATE) <= 9  THEN 'Q3'
        ELSE 'Q4'
    END                                             AS quarter,
    COUNT(*)                                        AS trips,
    ROUND(SUM(trip_fare_pkr), 0)                    AS revenue_pkr
FROM trips
WHERE status = 'Completed'
GROUP BY 1, 2
ORDER BY 1, 2"""
        _sql(_SQL_DD)
        if st.button("▶ Run dim_date Demo", key="dim_date_run"):
            _df = _run(_SQL_DD, conn)
            if _df is not None and not _df.empty:
                _show(_df, 220)
                fig = px.bar(_df, x="quarter", y="revenue_pkr", color="year",
                             barmode="group", template="plotly_dark",
                             title="Revenue by Quarter & Year",
                             color_discrete_sequence=[BRAND, TEAL, AMBER, ORANGE])
                fig.update_layout(margin=dict(t=35,b=0,l=0,r=0), height=280,
                                  paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, use_container_width=True)

    with _dt[1]:
        st.markdown(_concept(
            "SCD Type 2 — Track history of attribute changes",
            "When a customer moves city or upgrades type, we <b>don't overwrite</b> the old record.<br>"
            "Instead: set old row's <code>valid_to = yesterday, is_current = false</code> → "
            "insert new row with <code>valid_from = today, is_current = true</code>.<br>"
            "Enables point-in-time queries: 'what city was this customer in <i>at the time of booking?</i>'",
            "📅", PUR,
        ), unsafe_allow_html=True)
        _sql("""
-- SCD2 update pattern
-- Step 1: expire the current record
UPDATE dim_customer
SET valid_to   = current_date - 1,
    is_current = false
WHERE customer_id = 'CU00042' AND is_current = true;

-- Step 2: insert new version with updated attributes
INSERT INTO dim_customer
  (customer_id, city, customer_type, valid_from, valid_to, is_current)
VALUES ('CU00042', 'Lahore', 'VIP', current_date, '9999-12-31', true);

-- Point-in-time query: customer's city AT TIME OF BOOKING
SELECT t.trip_id, t.pickup_datetime, dc.city AS city_at_booking
FROM fact_trips t
JOIN dim_customer dc
  ON  t.customer_id = dc.customer_id
 AND  t.pickup_datetime::DATE BETWEEN dc.valid_from AND dc.valid_to;""")

    with _dt[2]:
        st.markdown(_concept(
            "Conformed Dimension — reused across multiple facts",
            "dim_vehicle is joined by fact_trips, fact_fuel_logs, AND fact_maintenance. "
            "Because all three use the same dim, you can cross-fact query: "
            "'Show maintenance cost vs revenue for each vehicle this quarter' — in one SQL.",
            "🚗", TEAL,
        ), unsafe_allow_html=True)
        _SQL_CF = """
-- Cross-fact: revenue vs maintenance cost (conformed dim_vehicle)
SELECT
    v.vehicle_id,
    v.make || ' ' || v.model               AS vehicle,
    ROUND(SUM(t.trip_fare_pkr), 0)         AS revenue_pkr,
    ROUND(SUM(m.total_cost_pkr), 0)        AS maint_cost_pkr,
    ROUND(SUM(t.trip_fare_pkr)
         - COALESCE(SUM(m.total_cost_pkr),0), 0) AS net_contribution
FROM vehicles v
LEFT JOIN trips t       ON v.vehicle_id = t.vehicle_id
                       AND t.status = 'Completed'
LEFT JOIN maintenance m ON v.vehicle_id = m.vehicle_id
GROUP BY v.vehicle_id, v.make, v.model
HAVING SUM(t.trip_fare_pkr) > 0
ORDER BY net_contribution DESC
LIMIT 15"""
        _sql(_SQL_CF)
        if st.button("▶ Run Cross-Fact Demo", key="crossfact_run"):
            _df = _run(_SQL_CF, conn)
            if _df is not None and not _df.empty:
                _show(_df, 220)
                _bar(_df, "vehicle", "revenue_pkr", "Revenue vs Maintenance Cost")

    with _dt[3]:
        st.markdown(_concept(
            "fact_trips — Core Revenue Fact (grain: 1 row = 1 trip)",
            "Contains FK references to all dimensions + all measurable facts.<br>"
            "Pre-computed derived metrics (revenue_per_day, revenue_per_km) avoid repeated calc at query time.<br>"
            "DQ flag columns (_dq_zero_fare, _dq_timeline_reversed) let analysts filter bad rows.",
            "📊", BRAND,
        ), unsafe_allow_html=True)
        _sql("""-- fact_trips key columns
-- trip_sk             surrogate PK (integer, stable)
-- trip_id             natural key from source
-- pickup_date_key     FK → dim_date (YYYYMMDD integer)
-- customer_sk         FK → dim_customer
-- vehicle_sk          FK → dim_vehicle
-- driver_sk           FK → dim_driver
-- fleet_sk            FK → dim_fleet
-- booking_type_sk     FK → dim_booking_type
-- pickup_location_sk  FK → dim_location
-- MEASURES:
-- trip_fare_pkr       revenue (PKR)
-- distance_km         operational
-- duration_days       operational
-- revenue_per_day     derived at load time
-- revenue_per_km      derived at load time
-- is_intercity        flag
-- _dq_zero_fare       data quality flag""")


# ═══════════════════════════════════════════════════════════════════════
# TAB 4 — JOINS
# ═══════════════════════════════════════════════════════════════════════
with T[4]:
    st.markdown(_h2("SQL Joins — Complete Guide", "🔗"), unsafe_allow_html=True)

    _JOINS = {
        "INNER JOIN — matching rows only": {
            "desc": "Returns rows that exist on <b>both sides</b>. Most common join. Use when you only want complete records.",
            "sql": """
SELECT
    t.trip_id,
    c.full_name       AS customer,
    c.customer_type,
    v.make || ' ' || v.model AS vehicle,
    t.booking_type,
    t.trip_fare_pkr,
    t.distance_km
FROM trips t
INNER JOIN customers c ON t.customer_id = c.customer_id
INNER JOIN vehicles  v ON t.vehicle_id  = v.vehicle_id
WHERE t.status = 'Completed'
ORDER BY t.trip_fare_pkr DESC
LIMIT 15""",
            "col": BRAND,
        },
        "LEFT JOIN — all left + optional right": {
            "desc": "Keeps ALL rows from the left table. NULLs appear where there is no right match. Perfect for 'all X with optional Y'.",
            "sql": """
-- All customers with trip count (including customers who never tripped)
SELECT
    c.customer_id,
    c.full_name,
    c.customer_type,
    c.city,
    COUNT(t.trip_id)                    AS total_trips,
    COALESCE(SUM(t.trip_fare_pkr), 0)   AS total_revenue_pkr
FROM customers c
LEFT JOIN trips t ON c.customer_id = t.customer_id
GROUP BY c.customer_id, c.full_name, c.customer_type, c.city
ORDER BY total_trips DESC
LIMIT 20""",
            "col": TEAL,
        },
        "LEFT JOIN Anti-join — rows with NO match": {
            "desc": "Filter <code>WHERE right.key IS NULL</code> to find rows in left that have no match in right. More efficient than NOT IN on large sets.",
            "sql": """
-- Vehicles that have NEVER completed a trip (idle fleet)
SELECT
    v.vehicle_id,
    v.make || ' ' || v.model  AS vehicle,
    v.status,
    v.odometer_km
FROM vehicles v
LEFT JOIN trips t ON v.vehicle_id = t.vehicle_id
                 AND t.status = 'Completed'
WHERE t.trip_id IS NULL          -- anti-join filter
ORDER BY v.vehicle_id
LIMIT 20""",
            "col": AMBER,
        },
        "SELF JOIN — table joined to itself": {
            "desc": "Join a table to itself with different aliases. Classic use: compare rows within the same entity.",
            "sql": """
-- SELF JOIN: vehicles used by more than one customer on the same day
SELECT
    t1.trip_id    AS trip_a,
    t2.trip_id    AS trip_b,
    t1.vehicle_id,
    t1.customer_id AS customer_a,
    t2.customer_id AS customer_b,
    t1.pickup_datetime::DATE AS shared_date
FROM trips t1
JOIN trips t2
    ON  t1.vehicle_id = t2.vehicle_id
    AND t1.trip_id    < t2.trip_id          -- avoid self-match and duplicates
    AND t1.pickup_datetime::DATE
      = t2.pickup_datetime::DATE
WHERE t1.status = 'Completed'
  AND t2.status = 'Completed'
LIMIT 15""",
            "col": PUR,
        },
        "CROSS JOIN — every row × every row": {
            "desc": "Cartesian product — every left row paired with every right row. Use to build all combinations of reference data.",
            "sql": """
-- All fleet × vehicle_type combinations
-- Shows which types each fleet offers (and which it doesn't)
SELECT
    f.fleet_name,
    f.city,
    vt.category,
    vt.sub_type,
    COUNT(v.vehicle_id) AS current_count
FROM fleets f
CROSS JOIN vehicle_types vt
LEFT JOIN vehicles v
    ON  v.fleet_id        = f.fleet_id
    AND v.vehicle_type_id = vt.vehicle_type_id
GROUP BY f.fleet_name, f.city, vt.category, vt.sub_type
ORDER BY f.fleet_name, vt.category
LIMIT 30""",
            "col": STEEL,
        },
        "FULL OUTER JOIN — all rows from both sides": {
            "desc": "Returns everything from both tables. NULLs where there is no match on either side. Good for reconciliation reports.",
            "sql": """
-- Vehicles in fleet vs vehicles that have trips
-- Finds vehicles with no trips AND trips with no vehicle record
SELECT
    v.vehicle_id                       AS fleet_vehicle,
    t.vehicle_id                       AS trip_vehicle,
    CASE
        WHEN v.vehicle_id IS NULL THEN 'Orphan Trip Vehicle'
        WHEN t.vehicle_id IS NULL THEN 'Never-Used Vehicle'
        ELSE 'Matched'
    END                                AS status
FROM vehicles v
FULL OUTER JOIN (
    SELECT DISTINCT vehicle_id FROM trips WHERE status='Completed'
) t ON v.vehicle_id = t.vehicle_id
WHERE v.vehicle_id IS NULL OR t.vehicle_id IS NULL
LIMIT 20""",
            "col": ORANGE,
        },
    }

    _j_sel = st.selectbox("Select Join Type:", list(_JOINS.keys()), key="join_sel")
    _ji = _JOINS[_j_sel]
    st.markdown(_concept(_j_sel, _ji["desc"], "🔗", _ji["col"]), unsafe_allow_html=True)
    _sql(_ji["sql"])
    if st.button("▶ Run Join Demo", key="run_join", type="primary"):
        _show(_run(_ji["sql"], conn))

    st.markdown(_h3("📋 Join Quick Reference", STEEL), unsafe_allow_html=True)
    _ref = pd.DataFrame({
        "Join": ["INNER","LEFT","LEFT + IS NULL","SELF","CROSS","FULL OUTER"],
        "Returns": ["Matching rows only","All left + optional right","Left rows with no right match","Same-table row comparison","Every combo (cartesian)","All rows from both tables"],
        "NULL when": ["No match either side","No right match","N/A (filtered)","N/A","Never","No match either side"],
        "Common Use": ["Normal reporting","'All X with optional Y'","Find orphans / gaps","Hierarchy / overlap","Build combinations","Reconciliation / audit"],
    })
    st.dataframe(_ref, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════════════
# TAB 5 — AGGREGATIONS
# ═══════════════════════════════════════════════════════════════════════
with T[5]:
    st.markdown(_h2("Aggregations — GROUP BY, ROLLUP, CUBE, PERCENTILE", "📊"), unsafe_allow_html=True)

    _AGGS = {
        "Basic GROUP BY — COUNT, SUM, AVG, MIN, MAX, STDDEV": """
SELECT
    booking_type,
    COUNT(*)                                        AS trips,
    ROUND(SUM(trip_fare_pkr),   0)                  AS total_revenue,
    ROUND(AVG(trip_fare_pkr),   0)                  AS avg_fare,
    ROUND(MIN(trip_fare_pkr),   0)                  AS min_fare,
    ROUND(MAX(trip_fare_pkr),   0)                  AS max_fare,
    ROUND(STDDEV(trip_fare_pkr),0)                  AS stddev_fare,
    ROUND(SUM(distance_km),     1)                  AS total_km
FROM trips
WHERE status = 'Completed'
GROUP BY booking_type
ORDER BY total_revenue DESC""",

        "HAVING — filter after aggregation (not WHERE)": """
-- WHERE filters rows BEFORE GROUP BY
-- HAVING filters groups AFTER GROUP BY
SELECT
    pickup_city,
    COUNT(*)                                        AS trips,
    ROUND(AVG(trip_fare_pkr), 0)                    AS avg_fare
FROM trips
WHERE status = 'Completed'       -- row-level filter (runs first)
GROUP BY pickup_city
HAVING COUNT(*) > 50             -- group-level filter (runs after agg)
   AND AVG(trip_fare_pkr) > 10000
ORDER BY avg_fare DESC""",

        "FILTER clause — conditional aggregation (pivot-style)": """
-- Conditional aggregation: one pass, many breakdowns
SELECT
    fleet_id,
    COUNT(*)                                                          AS total_trips,
    SUM(trip_fare_pkr) FILTER (WHERE booking_type = 'City Ride')     AS city_revenue,
    SUM(trip_fare_pkr) FILTER (WHERE booking_type = 'Airport Transfer') AS airport_revenue,
    SUM(trip_fare_pkr) FILTER (WHERE booking_type = 'Intercity')     AS intercity_revenue,
    COUNT(*) FILTER (WHERE with_driver = true)                       AS with_driver_trips,
    COUNT(*) FILTER (WHERE status = 'Cancelled')                     AS cancellations
FROM trips
GROUP BY fleet_id
ORDER BY total_trips DESC""",

        "ROLLUP — hierarchical subtotals": """
-- ROLLUP creates a subtotal row at each level + a grand total
SELECT
    COALESCE(CAST(date_part('year', pickup_datetime::DATE) AS VARCHAR),
             'ALL YEARS')                               AS year,
    COALESCE(STRFTIME(pickup_datetime::DATE,'%B'),
             'ALL MONTHS')                              AS month,
    COUNT(*)                                            AS trips,
    ROUND(SUM(trip_fare_pkr), 0)                        AS revenue_pkr
FROM trips
WHERE status = 'Completed'
  AND date_part('year', pickup_datetime::DATE) >= 2024
GROUP BY ROLLUP(
    date_part('year', pickup_datetime::DATE),
    STRFTIME(pickup_datetime::DATE,'%B')
)
ORDER BY 1 NULLS LAST, 2 NULLS LAST""",

        "CUBE — all subtotal combinations": """
-- CUBE creates subtotals for ALL combinations of the group columns
SELECT
    COALESCE(fleet_id, '** ALL FLEETS **')          AS fleet,
    COALESCE(booking_type, '** ALL TYPES **')       AS booking_type,
    COUNT(*)                                        AS trips,
    ROUND(SUM(trip_fare_pkr), 0)                    AS revenue_pkr,
    GROUPING(fleet_id)                              AS is_fleet_total,
    GROUPING(booking_type)                          AS is_type_total
FROM trips WHERE status = 'Completed'
GROUP BY CUBE(fleet_id, booking_type)
ORDER BY fleet NULLS LAST, booking_type NULLS LAST
LIMIT 40""",

        "PERCENTILE — median, quartiles, IQR": """
SELECT
    booking_type,
    COUNT(*)                                                               AS trips,
    ROUND(AVG(trip_fare_pkr), 0)                                           AS mean_fare,
    ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY trip_fare_pkr), 0)  AS median,
    ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY trip_fare_pkr), 0)  AS p25,
    ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY trip_fare_pkr), 0)  AS p75,
    ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY trip_fare_pkr), 0)  AS p95,
    ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY trip_fare_pkr)
        - PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY trip_fare_pkr), 0)  AS iqr
FROM trips WHERE status = 'Completed'
GROUP BY booking_type ORDER BY median DESC""",

        "STDDEV / CV — pricing consistency check": """
SELECT
    f.fleet_name,
    COUNT(t.trip_id)                        AS trips,
    ROUND(AVG(t.trip_fare_pkr),  0)         AS avg_fare,
    ROUND(STDDEV(t.trip_fare_pkr), 0)       AS stddev_fare,
    ROUND(STDDEV(t.trip_fare_pkr)*100.0
          /NULLIF(AVG(t.trip_fare_pkr),0),1) AS cv_pct  -- coefficient of variation
FROM trips t
JOIN fleets f ON t.fleet_id = f.fleet_id
WHERE t.status = 'Completed'
GROUP BY f.fleet_name HAVING COUNT(*) >= 20
ORDER BY cv_pct DESC""",
    }

    _agg_sel = st.selectbox("Select Aggregation Topic:", list(_AGGS.keys()), key="agg_sel")
    _sql(_AGGS[_agg_sel])
    if st.button("▶ Run Aggregation Demo", key="run_agg", type="primary"):
        _df = _run(_AGGS[_agg_sel], conn)
        if _df is not None and not _df.empty:
            _show(_df, 280)
            _nc = _df.select_dtypes("number").columns.tolist()
            _sc = _df.select_dtypes("object").columns.tolist()
            if _sc and _nc:
                _bar(_df, _sc[0], _nc[0], f"{_nc[0]} by {_sc[0]}")


# ═══════════════════════════════════════════════════════════════════════
# TAB 6 — WINDOW FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════
with T[6]:
    st.markdown(_h2("Window Functions — Complete Guide", "🪟"), unsafe_allow_html=True)
    st.markdown(_card(
        f'Window functions compute across <b>a set of rows related to the current row</b> '
        f'<i>without collapsing them</i> (unlike GROUP BY).<br>'
        f'Syntax: <code>fn() OVER (PARTITION BY … ORDER BY … ROWS/RANGE …)</code>',
        left=STEEL,
    ), unsafe_allow_html=True)

    _WF = {
        "ROW_NUMBER — unique sequential number per partition": """
-- Number each customer's trips chronologically
SELECT
    customer_id,
    trip_id,
    pickup_datetime,
    trip_fare_pkr,
    ROW_NUMBER() OVER (
        PARTITION BY customer_id        -- restart counter per customer
        ORDER BY pickup_datetime        -- ordered chronologically
    )                                   AS trip_number
FROM trips
WHERE status = 'Completed'
ORDER BY customer_id, trip_number
LIMIT 25""",

        "RANK vs DENSE_RANK — tie handling": """
-- RANK:       gaps after ties  (1, 2, 2, 4)
-- DENSE_RANK: no gaps          (1, 2, 2, 3)
WITH fleet_rev AS (
    SELECT fleet_id, vehicle_id,
           ROUND(SUM(trip_fare_pkr),0) AS revenue
    FROM trips WHERE status='Completed'
    GROUP BY fleet_id, vehicle_id
)
SELECT fleet_id, vehicle_id, revenue,
    RANK()       OVER (PARTITION BY fleet_id ORDER BY revenue DESC) AS rnk,
    DENSE_RANK() OVER (PARTITION BY fleet_id ORDER BY revenue DESC) AS dense_rnk
FROM fleet_rev
ORDER BY fleet_id, rnk
LIMIT 25""",

        "NTILE — divide rows into N equal buckets": """
-- Split trips into 4 fare quartiles
SELECT
    trip_id, trip_fare_pkr, distance_km,
    NTILE(4)  OVER (ORDER BY trip_fare_pkr)  AS fare_quartile,
    NTILE(10) OVER (ORDER BY trip_fare_pkr)  AS fare_decile,
    CASE NTILE(4) OVER (ORDER BY trip_fare_pkr)
        WHEN 1 THEN 'Budget'    WHEN 2 THEN 'Economy'
        WHEN 3 THEN 'Standard'  WHEN 4 THEN 'Premium'
    END                                      AS fare_tier
FROM trips WHERE status = 'Completed'
ORDER BY trip_fare_pkr
LIMIT 25""",

        "LAG & LEAD — access previous / next row": """
-- Month-over-month revenue change per fleet using LAG
WITH monthly AS (
    SELECT fleet_id,
           DATE_TRUNC('month', pickup_datetime::DATE) AS month,
           SUM(trip_fare_pkr) AS revenue
    FROM trips WHERE status = 'Completed'
    GROUP BY 1, 2
)
SELECT fleet_id, month,
    ROUND(revenue, 0)                                       AS revenue_pkr,
    ROUND(LAG(revenue,1) OVER (PARTITION BY fleet_id ORDER BY month), 0) AS prev_month,
    ROUND(revenue - LAG(revenue,1) OVER (PARTITION BY fleet_id ORDER BY month), 0) AS mom_change,
    ROUND((revenue - LAG(revenue,1) OVER (PARTITION BY fleet_id ORDER BY month))
          *100.0/NULLIF(LAG(revenue,1) OVER (PARTITION BY fleet_id ORDER BY month),0),1) AS mom_pct
FROM monthly ORDER BY fleet_id, month
LIMIT 30""",

        "Running Total — UNBOUNDED PRECEDING": """
-- Cumulative revenue per customer over their trip history
SELECT
    customer_id,
    trip_id,
    pickup_datetime,
    trip_fare_pkr,
    SUM(trip_fare_pkr) OVER (
        PARTITION BY customer_id
        ORDER BY pickup_datetime
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    )                               AS cumulative_spend_pkr,
    COUNT(*) OVER (
        PARTITION BY customer_id
        ORDER BY pickup_datetime
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    )                               AS cumulative_trip_count
FROM trips WHERE status = 'Completed'
ORDER BY customer_id, pickup_datetime
LIMIT 30""",

        "Moving Average — sliding window": """
-- 3-month rolling average revenue + YTD total
WITH monthly AS (
    SELECT DATE_TRUNC('month', pickup_datetime::DATE) AS month,
           SUM(trip_fare_pkr) AS revenue
    FROM trips WHERE status = 'Completed'
    GROUP BY 1
)
SELECT month,
    ROUND(revenue, 0)                                AS monthly_rev,
    ROUND(AVG(revenue) OVER (
        ORDER BY month
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW    -- 3-month sliding window
    ), 0)                                            AS rolling_3m_avg,
    ROUND(AVG(revenue) OVER (
        ORDER BY month
        ROWS BETWEEN 5 PRECEDING AND CURRENT ROW
    ), 0)                                            AS rolling_6m_avg,
    ROUND(SUM(revenue) OVER (
        PARTITION BY date_part('year',month::DATE)::INT
        ORDER BY month
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ), 0)                                            AS ytd_revenue
FROM monthly ORDER BY month""",

        "QUALIFY — filter on window result (DuckDB)": """
-- Get ONLY each vehicle's single best trip using QUALIFY
-- Without QUALIFY you'd need a subquery WHERE rn = 1
SELECT
    vehicle_id, trip_id, pickup_datetime, trip_fare_pkr,
    ROW_NUMBER() OVER (PARTITION BY vehicle_id ORDER BY trip_fare_pkr DESC) AS rn
FROM trips WHERE status = 'Completed'
QUALIFY rn = 1          -- DuckDB / Snowflake: filter on window result inline
ORDER BY trip_fare_pkr DESC
LIMIT 20""",

        "PERCENT_RANK & CUME_DIST — relative position": """
SELECT
    trip_id, trip_fare_pkr,
    ROUND(PERCENT_RANK() OVER (ORDER BY trip_fare_pkr) * 100, 1) AS pct_rank,
    ROUND(CUME_DIST()    OVER (ORDER BY trip_fare_pkr) * 100, 1) AS cumulative_dist_pct
FROM trips WHERE status = 'Completed'
ORDER BY trip_fare_pkr DESC LIMIT 20""",
    }

    _wf_sel = st.selectbox("Select Window Function:", list(_WF.keys()), key="wf_sel")
    _sql(_WF[_wf_sel])
    if st.button("▶ Run Window Function Demo", key="run_wf", type="primary"):
        _show(_run(_WF[_wf_sel], conn))

    st.markdown(_h3("📋 Frame Quick Reference", STEEL), unsafe_allow_html=True)
    st.dataframe(pd.DataFrame({
        "Frame Spec": [
            "ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW",
            "ROWS BETWEEN 2 PRECEDING AND CURRENT ROW",
            "ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING",
            "ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING",
        ],
        "Meaning": [
            "All rows from start → current row (running total)",
            "Current + 2 previous rows (3-row moving window)",
            "Previous, current, next row (centred average)",
            "Entire partition (grand total in every row)",
        ],
        "Use Case": [
            "Cumulative sum, running count",
            "Rolling 3-month average",
            "Centred moving average",
            "% of total, FIRST_VALUE, LAST_VALUE",
        ],
    }), use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════════════
# TAB 7 — ANALYTICAL SQL
# ═══════════════════════════════════════════════════════════════════════
with T[7]:
    st.markdown(_h2("Analytical SQL — CTEs, Subqueries, Date/String", "🧠"), unsafe_allow_html=True)

    _ANAL = {
        "CTE — WITH clause (multi-step readable query)": """
-- 3-step funnel: trips per customer → completed → conversion rate
WITH total_trips AS (
    SELECT customer_id,
           COUNT(*) AS all_trips,
           SUM(trip_fare_pkr) AS total_revenue
    FROM trips GROUP BY customer_id
),
completed AS (
    SELECT customer_id,
           COUNT(*) AS done,
           SUM(trip_fare_pkr) AS done_revenue
    FROM trips WHERE status='Completed'
    GROUP BY customer_id
),
funnel AS (
    SELECT t.customer_id, t.all_trips,
           COALESCE(c.done, 0) AS completed,
           ROUND(COALESCE(c.done,0)*100.0/NULLIF(t.all_trips,0),1) AS completion_pct
    FROM total_trips t LEFT JOIN completed c ON t.customer_id = c.customer_id
)
SELECT
    CASE WHEN completion_pct = 100 THEN 'Perfect'
         WHEN completion_pct >= 75  THEN 'High'
         WHEN completion_pct >= 50  THEN 'Medium'
         ELSE 'Low' END         AS tier,
    COUNT(*)                    AS customers,
    ROUND(AVG(completion_pct),1) AS avg_pct
FROM funnel
GROUP BY 1 ORDER BY avg_pct DESC""",

        "Recursive CTE — date spine / gap detection": """
-- Build a monthly series, LEFT JOIN to find months with no trips
WITH RECURSIVE months AS (
    SELECT DATE '2022-01-01' AS m
    UNION ALL
    SELECT m + INTERVAL '1 month' FROM months WHERE m < DATE '2026-09-01'
)
SELECT
    STRFTIME(ms.m, '%Y-%m') AS year_month,
    COALESCE(t.trips, 0)    AS trip_count,
    CASE WHEN t.trips IS NULL THEN '⚠️ Gap' ELSE '✅' END AS status
FROM months ms
LEFT JOIN (
    SELECT DATE_TRUNC('month', pickup_datetime::DATE) AS m,
           COUNT(*) AS trips
    FROM trips WHERE status='Completed' GROUP BY 1
) t ON ms.m = t.m
ORDER BY ms.m""",

        "EXISTS / NOT EXISTS — semi-join": """
-- Drivers who have NOT driven in the last 180 days
SELECT d.driver_id, d.full_name, d.experience_years, d.ratings_avg
FROM drivers d
WHERE NOT EXISTS (
    SELECT 1 FROM trips t
    WHERE t.driver_id = d.driver_id
      AND t.status = 'Completed'
      AND t.pickup_datetime::DATE > (CURRENT_DATE - 180)
)
ORDER BY d.experience_years DESC
LIMIT 20""",

        "PIVOT-style — years as columns": """
SELECT
    fleet_id,
    ROUND(SUM(trip_fare_pkr) FILTER (
        WHERE date_part('year',pickup_datetime::DATE)=2022),0) AS rev_2022,
    ROUND(SUM(trip_fare_pkr) FILTER (
        WHERE date_part('year',pickup_datetime::DATE)=2023),0) AS rev_2023,
    ROUND(SUM(trip_fare_pkr) FILTER (
        WHERE date_part('year',pickup_datetime::DATE)=2024),0) AS rev_2024,
    ROUND(SUM(trip_fare_pkr) FILTER (
        WHERE date_part('year',pickup_datetime::DATE)=2025),0) AS rev_2025,
    ROUND(SUM(trip_fare_pkr) FILTER (
        WHERE date_part('year',pickup_datetime::DATE)=2026),0) AS rev_2026,
    ROUND(SUM(trip_fare_pkr), 0) AS total
FROM trips WHERE status='Completed'
GROUP BY fleet_id ORDER BY total DESC""",

        "DATE functions — comprehensive reference": """
SELECT pickup_datetime,
    date_part('year',  pickup_datetime::DATE)::INT  AS yr,
    date_part('month', pickup_datetime::DATE)::INT  AS mo,
    date_part('day',   pickup_datetime::DATE)::INT  AS dy,
    date_part('hour',  pickup_datetime)::INT        AS hr,
    date_part('dow',   pickup_datetime::DATE)::INT  AS dow,  -- 0=Sun
    DATE_TRUNC('month', pickup_datetime::DATE)      AS month_start,
    DATE_TRUNC('week',  pickup_datetime::DATE)      AS week_start,
    STRFTIME(pickup_datetime::DATE, '%d %b %Y')     AS fmt_date,
    STRFTIME(pickup_datetime::DATE, '%A')           AS weekday,
    DATE_DIFF('day', pickup_datetime::DATE, CURRENT_DATE)  AS days_ago,
    DATE_DIFF('hour', pickup_datetime, dropoff_datetime)   AS trip_hours
FROM trips WHERE status='Completed'
ORDER BY pickup_datetime DESC LIMIT 10""",

        "STRING functions — comprehensive reference": """
SELECT customer_id, full_name, email, phone,
    UPPER(full_name)               AS up,
    LOWER(full_name)               AS lo,
    INITCAP(full_name)             AS title_case,
    SPLIT_PART(full_name,' ',1)    AS first_name,
    SPLIT_PART(full_name,' ',2)    AS last_name,
    SPLIT_PART(email,'@',2)        AS email_domain,
    LENGTH(full_name)              AS name_len,
    REPLACE(phone,'-','')          AS phone_digits,
    REGEXP_REPLACE(phone,'[^0-9]','','g') AS regex_clean,
    CASE WHEN email LIKE '%@%.%' THEN 'valid' ELSE 'invalid' END AS email_ok
FROM customers LIMIT 15""",

        "COALESCE / NULLIF / IIF — null handling": """
SELECT trip_id, driver_id, trip_fare_pkr, distance_km,
    COALESCE(driver_id, 'No Driver Assigned') AS driver_display,
    trip_fare_pkr / NULLIF(distance_km, 0)    AS fare_per_km,
    IIF(with_driver, 'Chauffeur', 'Self-Drive') AS drive_mode,
    IFNULL(cancellation_reason, 'N/A')         AS cancel_reason
FROM trips LIMIT 15""",
    }

    _an_sel = st.selectbox("Select Topic:", list(_ANAL.keys()), key="anal_sel")
    _sql(_ANAL[_an_sel])
    if st.button("▶ Run Demo", key="run_anal", type="primary"):
        _show(_run(_ANAL[_an_sel], conn))


# ═══════════════════════════════════════════════════════════════════════
# TAB 8 — STREAMING
# ═══════════════════════════════════════════════════════════════════════
with T[8]:
    st.markdown(_h2("Streaming & Incremental Load Patterns", "📡"), unsafe_allow_html=True)

    for _t, _b, _ic, _c in [
        ("Batch Load",     "Process all data once (daily/weekly). Simple. Good for historical loads and full rebuilds.", "📦", BRAND),
        ("Incremental",    "Process only new rows since last run using a <b>watermark</b> timestamp. Fast and efficient for daily updates.", "⏩", TEAL),
        ("Streaming",      "Process each event as it arrives (near real-time, every few seconds). Most complex but freshest data.", "📡", AMBER),
        ("Watermark",      "The timestamp of the last successfully loaded row, stored in meta.load_log. Next run: <code>WHERE created_at &gt; watermark</code>.", "⏱️", STEEL),
        ("Idempotency",    "Running the pipeline twice gives the same result. Achieved with INSERT OR REPLACE or WHERE id NOT IN (SELECT id FROM target).", "♻️", TEAL),
        ("Late Arrivals",  "A booking from yesterday arrives in today's pipeline run. Check the event timestamp, not the load timestamp.", "🕐", ORANGE),
        ("Micro-Batch",    "Buffer 1–5 minutes of events then process as a mini-batch. Good compromise between pure batch and true streaming.", "⚡", PUR),
        ("Upsert / MERGE", "INSERT new + UPDATE existing in one statement. DuckDB: <code>INSERT OR REPLACE</code>. Postgres: <code>INSERT ... ON CONFLICT DO UPDATE</code>.", "🔄", BRAND),
    ]:
        st.markdown(_concept(_t, _b, _ic, _c), unsafe_allow_html=True)

    st.markdown(_h3("🔬 Watermark Incremental Pattern (Live Demo)", BRAND), unsafe_allow_html=True)
    _W_SQL = """
-- INCREMENTAL LOAD: only load rows newer than the last run
WITH watermark AS (
    -- In production this comes from meta.load_log
    -- Here we use the max timestamp already in the table as a proxy
    SELECT MAX(pickup_datetime)::TIMESTAMP AS last_seen
    FROM trips
    WHERE status = 'Completed'
)
SELECT
    COUNT(*)                    AS new_rows_this_run,
    MIN(pickup_datetime)        AS earliest_new,
    MAX(pickup_datetime)        AS latest_new
FROM trips, watermark
WHERE pickup_datetime::TIMESTAMP > watermark.last_seen
  AND status = 'Completed'"""
    _sql(_W_SQL)
    if st.button("▶ Show Watermark Result", key="wm_run"):
        _show(_run(_W_SQL, conn))

    st.markdown(_h3("📊 Live KPI Snapshot", TEAL), unsafe_allow_html=True)
    if st.button("🔄 Refresh KPIs Now", type="primary", key="kpi_refresh"):
        _KPI_SQL = """
SELECT
    COUNT(*)                                                     AS total_trips,
    COUNT(*) FILTER (WHERE status='Completed')                   AS completed,
    COUNT(*) FILTER (WHERE status='Cancelled')                   AS cancelled,
    ROUND(SUM(trip_fare_pkr) FILTER (WHERE status='Completed'),0) AS revenue_pkr,
    ROUND(AVG(trip_fare_pkr) FILTER (WHERE status='Completed'),0) AS avg_fare_pkr,
    MAX(pickup_datetime)                                         AS latest_trip
FROM trips"""
        _dfk = _run(_KPI_SQL, conn)
        if _dfk is not None and not _dfk.empty:
            _row = _dfk.iloc[0]
            _k1, _k2, _k3, _k4 = st.columns(4)
            _k1.metric("Total Trips",    f"{int(_row.get('total_trips',0)):,}")
            _k2.metric("Completed",      f"{int(_row.get('completed',0)):,}")
            _k3.metric("Revenue (PKR)",  f"{int(_row.get('revenue_pkr',0)):,}")
            _k4.metric("Avg Fare (PKR)", f"{int(_row.get('avg_fare_pkr',0)):,}")

    st.markdown(_h3("📊 Hourly Booking Trend (last 24h simulation)", STEEL), unsafe_allow_html=True)
    _H_SQL = """
SELECT
    date_part('hour', pickup_datetime)::INT  AS hour_of_day,
    COUNT(*)                                 AS trips,
    ROUND(SUM(trip_fare_pkr),0)              AS revenue_pkr
FROM trips
WHERE status = 'Completed'
GROUP BY 1 ORDER BY 1"""
    if st.button("▶ Show Hourly Trend", key="hourly_run"):
        _dfh = _run(_H_SQL, conn)
        if _dfh is not None and not _dfh.empty:
            fig = px.area(_dfh, x="hour_of_day", y="trips", template="plotly_dark",
                          title="Trip Volume by Hour of Day",
                          color_discrete_sequence=[BRAND])
            fig.update_layout(margin=dict(t=35,b=0,l=0,r=0), height=240,
                              paper_bgcolor="rgba(0,0,0,0)",
                              plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════
# TAB 9 — CHEATSHEET
# ═══════════════════════════════════════════════════════════════════════
with T[9]:
    st.markdown(_h2("SQL Cheatsheet — Quick Reference", "📋"), unsafe_allow_html=True)

    _CHEAT = {
        "🔗 JOIN Types": """\
-- INNER: matching rows only
SELECT * FROM a INNER JOIN b ON a.id = b.a_id

-- LEFT: all from left, NULLs where no right match
SELECT * FROM a LEFT JOIN b ON a.id = b.a_id

-- Anti-join: rows in a with NO match in b
SELECT * FROM a LEFT JOIN b ON a.id = b.a_id WHERE b.a_id IS NULL

-- FULL OUTER: all rows from both
SELECT * FROM a FULL OUTER JOIN b ON a.id = b.a_id

-- CROSS: every row × every row
SELECT * FROM a CROSS JOIN b

-- SELF: same table with alias
SELECT a1.*, a2.* FROM t a1 JOIN t a2 ON a1.parent_id = a2.id""",

        "📊 Aggregations": """\
SELECT col,
    COUNT(*), COUNT(DISTINCT col2),
    SUM(x), AVG(x), MIN(x), MAX(x),
    STDDEV(x), VARIANCE(x)
FROM t GROUP BY col HAVING COUNT(*) > 10

-- Conditional aggregate
SUM(x) FILTER (WHERE status = 'Completed')

-- ROLLUP / CUBE / GROUPING SETS
GROUP BY ROLLUP(year, month)
GROUP BY CUBE(fleet, booking_type)
GROUP BY GROUPING SETS ((a,b),(a),())

-- Percentiles
PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY col)""",

        "🪟 Window Functions": """\
-- Ranking
ROW_NUMBER()  OVER (PARTITION BY x ORDER BY y)
RANK()        OVER (PARTITION BY x ORDER BY y)
DENSE_RANK()  OVER (PARTITION BY x ORDER BY y)
NTILE(n)      OVER (ORDER BY y)
PERCENT_RANK() OVER (ORDER BY y)
CUME_DIST()   OVER (ORDER BY y)

-- Navigation
LAG(col,1)   OVER (PARTITION BY x ORDER BY y)
LEAD(col,1)  OVER (PARTITION BY x ORDER BY y)
FIRST_VALUE(col) OVER (...)
LAST_VALUE(col)  OVER (... ROWS UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)

-- Aggregation over window
SUM(col) OVER (PARTITION BY x ORDER BY y ROWS UNBOUNDED PRECEDING)
AVG(col) OVER (ORDER BY y ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)

-- QUALIFY (DuckDB/Snowflake) — filter on window result
QUALIFY ROW_NUMBER() OVER (...) = 1""",

        "📅 Date Functions (DuckDB)": """\
date_part('year',  ts)           -- extract year
date_part('month', ts)           -- extract month (1-12)
date_part('dow',   ts)           -- day of week (0=Sun)
DATE_TRUNC('month', ts)          -- first of month
DATE_DIFF('day',   d1, d2)       -- integer days between
DATE_DIFF('hour',  ts1, ts2)     -- hours between
STRFTIME(ts, '%Y-%m-%d')         -- format
EPOCH(ts)                        -- Unix seconds
ts + INTERVAL '7 days'           -- date arithmetic
CURRENT_DATE                     -- today
CURRENT_TIMESTAMP                -- now""",

        "🔤 String Functions": """\
UPPER(s), LOWER(s), INITCAP(s)
TRIM(s), LTRIM(s), RTRIM(s)
LENGTH(s)
SPLIT_PART(s, delim, n)          -- split by delimiter
POSITION(sub IN s)
SUBSTR(s, start, len)
REPLACE(s, old, new)
REGEXP_REPLACE(s, pat, rep, 'g')
s || other                       -- concatenation
LIKE '%pattern%'
TRY_CAST(s AS INTEGER)""",

        "🎯 NULL Handling": """\
COALESCE(a, b, c)       -- first non-null
NULLIF(a, b)            -- NULL if a=b  (e.g. avoid /0: x/NULLIF(y,0))
IFNULL(a, default)      -- shorthand COALESCE with 1 fallback
IIF(cond, yes, no)      -- ternary (DuckDB)
IS NULL / IS NOT NULL
CASE WHEN x IS NULL THEN ... END""",

        "📐 CTEs & Subqueries": """\
-- CTE
WITH cte AS (SELECT ...), cte2 AS (SELECT ... FROM cte)
SELECT * FROM cte2

-- Recursive CTE
WITH RECURSIVE r AS (
    SELECT start_val
    UNION ALL
    SELECT step FROM r WHERE condition
)

-- Scalar subquery (returns 1 value inline)
SELECT *, (SELECT MAX(x) FROM b WHERE b.id = a.id) FROM a

-- EXISTS / NOT EXISTS
WHERE EXISTS     (SELECT 1 FROM b WHERE b.a_id = a.id)
WHERE NOT EXISTS (SELECT 1 FROM b WHERE b.a_id = a.id)

-- QUALIFY (DuckDB) — filter window without subquery
SELECT * FROM t QUALIFY ROW_NUMBER() OVER (...) = 1""",

        "⚙️ ETL / Upsert Patterns": """\
-- Incremental insert (skip existing)
INSERT INTO target
SELECT * FROM source
WHERE id NOT IN (SELECT id FROM target)

-- Upsert (DuckDB)
INSERT OR REPLACE INTO target SELECT * FROM source

-- Deduplication — keep latest record per key
SELECT * FROM (
    SELECT *,
        ROW_NUMBER() OVER (PARTITION BY id ORDER BY updated_at DESC) rn
    FROM source
) WHERE rn = 1

-- QUALIFY dedup (DuckDB/Snowflake)
SELECT * FROM source
QUALIFY ROW_NUMBER() OVER (PARTITION BY id ORDER BY updated_at DESC) = 1

-- Watermark incremental
WHERE created_at > (SELECT MAX(created_at) FROM target)""",
    }

    _ch_sel = st.selectbox("Section:", list(_CHEAT.keys()), key="cheat_sel")
    _sql(_CHEAT[_ch_sel])

    # Download all sections as one .sql file
    _all = "\n\n".join(
        f"-- {'='*60}\n-- {s}\n-- {'='*60}\n{q}"
        for s, q in _CHEAT.items()
    )
    st.download_button(
        "⬇️ Download Full Cheatsheet (.sql)",
        data=_all,
        file_name="sql_cheatsheet_rentacar.sql",
        mime="text/plain",
        key="dl_cheat",
    )

    # Download individual DWH SQL files
    st.markdown(_h3("📁 Download DWH SQL Files", STEEL), unsafe_allow_html=True)
    _DL = {
        "00_create_schemas.sql":     DWH_DIR / "00_setup/00_create_schemas.sql",
        "01_raw_ingest.sql":         DWH_DIR / "00_setup/01_raw_ingest.sql",
        "02_dq_checks.sql":          DWH_DIR / "00_setup/02_data_quality_checks.sql",
        "03_staging_etl.sql":        DWH_DIR / "00_setup/03_staging_etl.sql",
        "01_dim_date.sql":           DWH_DIR / "01_dimensions/01_dim_date.sql",
        "02_dim_customer.sql":       DWH_DIR / "01_dimensions/02_dim_customer.sql",
        "01_fact_trips.sql":         DWH_DIR / "02_facts/01_fact_trips.sql",
        "01_joins_complete.sql":     DWH_DIR / "05_learning_kit/01_joins_complete.sql",
        "02_aggregations.sql":       DWH_DIR / "05_learning_kit/02_aggregations.sql",
        "03_window_functions.sql":   DWH_DIR / "05_learning_kit/03_window_functions.sql",
        "04_analytical_sql.sql":     DWH_DIR / "05_learning_kit/04_analytical_sql.sql",
        "05_etl_patterns.sql":       DWH_DIR / "05_learning_kit/05_etl_patterns.sql",
    }
    _dc = st.columns(4)
    for _idx, (_fname, _fpath) in enumerate(_DL.items()):
        with _dc[_idx % 4]:
            if _fpath.exists():
                st.download_button(
                    f"⬇️ {_fname}",
                    data=_fpath.read_text(encoding="utf-8"),
                    file_name=_fname,
                    mime="text/plain",
                    key=f"dl_{_idx}_{_fname}",
                )
            else:
                st.markdown(
                    f'<div style="font-size:.68rem;color:{M};">❌ {_fname}</div>',
                    unsafe_allow_html=True,
                )
