"""
DWH / ETL Academy -- Full Interactive Tutorial
OLTP vs OLAP . ETL/ELT Pipeline . Star Schema . Facts & Dims
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
    "acad_gen_log":   [],
    "acad_etl_log":   [],
    "acad_conn":      None,
    "acad_catalog":   {},       # {name: sql} user-saved queries
    "acad_editor_sql": "",      # current editor content
    "acad_editor_result": None, # last query result DataFrame
    "acad_editor_err":  "",     # last query error
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
    f'Full interactive guide -- OLTP -> ETL/ELT -> Star Schema -> Facts &amp; Dims -> '
    f'Analytical SQL . Live runnable examples on real Rent-A-Car data</div>',
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
    "✏️ SQL Editor",
    "🐍 Python Editor",
    "🗺️ Data Lineage",
    "🔍 Schema Browser",
    "🏋️ Exercises",
    "⚡ Query Explain",
    "📈 Data Profiling",
    "📖 Documentation",
])


# ═══════════════════════════════════════════════════════════════════════
# TAB 0 -- ARCHITECTURE
# ═══════════════════════════════════════════════════════════════════════
with T[0]:
    st.markdown(_h2("OLTP vs OLAP vs Data Warehouse", "🏗️"), unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    _boxes = [
        (c1, "📥", "OLTP", "Online Transaction Processing",
         "Optimised for <b>writes</b>. Normalised 3NF schema. Row-level operations. "
         "High concurrency, ms latency. <b>Our CSV source tables.</b>", BRAND),
        (c2, "🔄", "ETL / ELT", "Extract . Transform . Load",
         "Bridges OLTP -> OLAP. Cleans, validates, deduplicates. "
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
        f'&nbsp;&nbsp;&nbsp;&nbsp;│ read_csv_auto() -- zero-copy DuckDB views<br>'
        f'&nbsp;&nbsp;&nbsp;&nbsp;▼<br>'
        f'🔍 <b style="color:{AMBER};">raw.*</b> -- raw.v_trips, raw.v_customers, …<br>'
        f'&nbsp;&nbsp;&nbsp;&nbsp;│ DQ checks -> meta.dq_issues<br>'
        f'&nbsp;&nbsp;&nbsp;&nbsp;▼<br>'
        f'🧹 <b style="color:{STEEL};">staging.*</b> -- TRY_CAST, COALESCE, TRIM, QUALIFY dedup<br>'
        f'&nbsp;&nbsp;&nbsp;&nbsp;▼<br>'
        f'🌟 <b style="color:{TEAL};">dwh.*</b> -- dim_date . dim_customer (SCD2) . dim_vehicle .<br>'
        f'&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;dim_driver . dim_fleet . dim_location<br>'
        f'&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;fact_trips . fact_invoices . fact_payments .<br>'
        f'&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;fact_fuel_logs . fact_maintenance . fact_telematics<br>'
        f'&nbsp;&nbsp;&nbsp;&nbsp;▼<br>'
        f'📈 <b style="color:{PUR};">mart.*</b> -- daily_revenue . monthly_pnl . customer_ltv . …</div>',
        left=STEEL,
    ), unsafe_allow_html=True)

    st.markdown(_h3("🔑 Key Concepts", STEEL), unsafe_allow_html=True)
    _pairs = [
        ("Normalisation (3NF)", "OLTP avoids redundancy -- a booking stores customer_id, not the name. Name lives once in customers. Every update is safe.", "🔗", BRAND),
        ("Denormalisation", "DWH pre-joins everything into dim_vehicle (vehicle + fleet + type). Analysts query once with no joins needed.", "📦", AMBER),
        ("Surrogate Key", "Integer PK generated by the DWH (customer_sk=1,2,3). Stable even when the source system's natural key changes.", "🔢", TEAL),
        ("SCD Type 2", "Slowly Changing Dimension. Customer moves city -> old row gets valid_to set, new row inserted with is_current=true. Full history preserved.", "📅", PUR),
        ("Grain", "What ONE row represents. fact_trips grain = 1 completed trip. fact_billing_lines grain = 1 invoice line. Always define grain first.", "🎯", ORANGE),
        ("Conformed Dimension", "dim_date is joined by fact_trips, fact_invoices AND fact_maintenance. Enables cross-fact queries: revenue vs maint cost same period.", "🔄", STEEL),
        ("Watermark", "Timestamp of the last successfully loaded row. Incremental ETL uses WHERE created_at > watermark to avoid reprocessing.", "⏱️", BRAND),
        ("ELT vs ETL", "ETL transforms outside the DB (Python/Spark). ELT loads raw data first then transforms inside the DWH with SQL -- our approach.", "⚡", AMBER),
    ]
    r1, r2 = st.columns(2)
    for i, (t, b, ic, c) in enumerate(_pairs):
        col = r1 if i % 2 == 0 else r2
        with col:
            st.markdown(_concept(t, b, ic, c), unsafe_allow_html=True)

    st.markdown(_h3("🔬 Live Demo: OLTP Join vs DWH Query", BRAND), unsafe_allow_html=True)
    d1, d2 = st.columns(2)
    with d1:
        st.markdown(f'<div style="font-size:.78rem;font-weight:700;color:{BRAND};">OLTP -- 4 JOINs every query</div>', unsafe_allow_html=True)
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
        st.markdown(f'<div style="font-size:.78rem;font-weight:700;color:{TEAL};">DWH -- same result, pre-joined dims</div>', unsafe_allow_html=True)
        _SQL_DWH = """
-- In the DWH star schema, dims are pre-joined --
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
# TAB 1 -- DATA GENERATOR  (full lifecycle: batch . stream . append . replace)
# ═══════════════════════════════════════════════════════════════════════
with T[1]:
    from app.dwh_engine import (
        ETLPipeline, load_state, save_state, get_file_sizes,
        detect_new_files, list_archives, run_dq_summary,
        OLTP_DIR, ARCHIVE, STREAM_DIR,
    )

    st.markdown(_h2("Data Generator & File Lifecycle", "⚙️"), unsafe_allow_html=True)

    # ── shared terminal CSS (reused in Tab 2) ───────────────────────────
    st.markdown("""<style>
.gen-terminal{background:#0d1117;border:1px solid #30363d;border-radius:0 0 8px 8px;
    padding:14px 16px;font-family:'Consolas','Courier New',monospace;font-size:.76rem;
    line-height:1.7;max-height:480px;overflow-y:auto;color:#58a6ff;
    white-space:pre-wrap;word-break:break-all;}
.gen-terminal .ok  {color:#3fb950;}
.gen-terminal .warn{color:#e3b341;}
.gen-terminal .err {color:#f85149;}
.gen-terminal .dim {color:#8b949e;}
.gen-terminal .hdr {color:#e63946;font-weight:700;}
.gen-terminal .inf {color:#79c0ff;}
.term-bar{background:#161b22;border:1px solid #30363d;border-bottom:none;
    border-radius:8px 8px 0 0;padding:7px 14px;font-size:.72rem;color:#8b949e;
    display:flex;align-items:center;gap:8px;}
.term-dot{width:11px;height:11px;border-radius:50%;display:inline-block;}
.pipeline-step{display:flex;align-items:center;gap:10px;padding:7px 12px;
    border-radius:8px;margin:3px 0;font-size:.79rem;}
.step-done {background:#0d2818;border:1px solid #3fb950;color:#3fb950;}
.step-run  {background:#1c1400;border:1px solid #e3b341;color:#e3b341;}
.step-wait {background:#141e2b;border:1px solid #30363d;color:#8b949e;}
.step-err  {background:#2d0a0a;border:1px solid #f85149;color:#f85149;}
.file-badge{display:inline-block;padding:2px 8px;border-radius:12px;
    font-size:.68rem;font-weight:700;margin:1px;}
</style>""", unsafe_allow_html=True)

    # ── Pipeline lifecycle explainer ────────────────────────────────────
    st.markdown(_h3("📐 File Lifecycle Architecture", STEEL), unsafe_allow_html=True)
    st.markdown(_card(
        '<div style="font-family:monospace;font-size:.77rem;color:#a0c0dc;line-height:2.1;">'
        f'📡 <b style="color:{AMBER};">Generator</b> -> writes CSV files<br>'
        f'&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;│<br>'
        f'&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;▼<br>'
        f'📂 <b style="color:{BRAND};">data/csv/oltp/</b> &nbsp; <- LANDING ZONE (raw CSV files live here)<br>'
        f'&nbsp;&nbsp;&nbsp;&nbsp;│&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;┌─ Row count watermark stored in pipeline_state.json<br>'
        f'&nbsp;&nbsp;&nbsp;&nbsp;│&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;└─ New rows detected: current_rows &gt; watermark<br>'
        f'&nbsp;&nbsp;&nbsp;&nbsp;▼<br>'
        f'⚙️ <b style="color:{STEEL};">ETL Pipeline</b><br>'
        f'&nbsp;&nbsp;&nbsp;&nbsp;├─ <b style="color:{TEAL};">Full Load</b>: rebuild everything + archive CSVs after<br>'
        f'&nbsp;&nbsp;&nbsp;&nbsp;├─ <b style="color:{AMBER};">Incremental</b>: process only new rows (no archive)<br>'
        f'&nbsp;&nbsp;&nbsp;&nbsp;└─ <b style="color:{PUR};">Stream Batch</b>: drain data/csv/stream/ -> append -> incremental<br>'
        f'&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;│<br>'
        f'&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;▼<br>'
        f'📦 <b style="color:{TEAL};">data/csv/archive/YYYY-MM-DD_HH-MM-SS/</b><br>'
        f'&nbsp;&nbsp;&nbsp;&nbsp;└─ Timestamped folder per run + _manifest.json<br>'
        f'&nbsp;&nbsp;&nbsp;&nbsp;└─ Original CSVs preserved, DWH rebuilt from archive if needed',
        left=STEEL,
    ), unsafe_allow_html=True)

    # ── Controls: batch + stream side by side ───────────────────────────
    g1, g2 = st.columns(2)

    with g1:
        st.markdown(_h3("📦 Batch Generator", BRAND), unsafe_allow_html=True)
        _mode_choice = st.radio(
            "Write mode",
            ["🔄 Replace existing files (full rebuild)",
             "➕ Append to existing files (incremental add)"],
            key="gen_mode",
        )
        _append = "Append" in _mode_choice

        n_trips = st.slider("Trips to generate", 500, 20000, 3000, 500, key="gen_n")
        g_start = st.date_input("Start date", value=date(2022, 1, 1), key="gen_s")
        g_end   = st.date_input("End date",   value=date(2026, 9, 26), key="gen_e")
        _dq_rate = st.slider("DQ issue injection %", 0, 10, 3, 1, key="gen_dq")

        _gen_btn = st.button(
            "🚀 Generate Batch Data",
            type="primary", use_container_width=True, key="btn_batch",
        )

    with g2:
        st.markdown(_h3("📡 Streaming Mode", TEAL), unsafe_allow_html=True)
        st.markdown(_card(
            f'Appends one booking event every N seconds directly to existing CSVs.<br>'
            f'Run from terminal -- Streamlit will detect new rows on next ETL incremental run.',
            left=TEAL, pad="10px 14px",
        ), unsafe_allow_html=True)
        g_iv = st.slider("Interval (seconds)", 5, 60, 10, 5, key="gen_iv")
        st.code(
            f'python "{GEN_PY}" --mode stream --interval {g_iv} --output "{DATA_DIR}"',
            language="bash",
        )
        st.markdown(_card(
            f'<b style="color:{TEAL};">Stream -> Micro-Batch flow:</b><br>'
            f'<div style="font-size:.76rem;color:{TEXT};line-height:1.8;margin-top:4px;">'
            f'1. Generator appends rows to <code>data/csv/oltp/*.csv</code><br>'
            f'2. Row count increases -> watermark detects new rows<br>'
            f'3. Click <b>Incremental Load</b> in ETL tab to process them<br>'
            f'4. DWH updated with only the new rows -- no full rebuild</div>',
            left=TEAL, pad="10px 14px",
        ), unsafe_allow_html=True)

    # ── Live generator terminal ─────────────────────────────────────────
    if _gen_btn:
        if not GEN_PY.exists():
            st.error(f"Generator not found at `{GEN_PY}`")
        else:
            st.session_state.acad_gen_log = []
            cmd = [
                sys.executable, str(GEN_PY),
                "--mode",   "batch",
                "--start",  str(g_start),
                "--end",    str(g_end),
                "--trips",  str(n_trips),
                "--output", str(DATA_DIR),
            ]

            _mode_label = "APPEND" if _append else "REPLACE"
            st.markdown(
                f'<div class="term-bar">'
                f'<span class="term-dot" style="background:#ff5f57;"></span>'
                f'<span class="term-dot" style="background:#febc2e;"></span>'
                f'<span class="term-dot" style="background:#28c840;"></span>'
                f'&nbsp; data_generator.py &nbsp;.&nbsp; {_mode_label} &nbsp;.&nbsp;'
                f'{n_trips:,} trips &nbsp;.&nbsp; DQ {_dq_rate}%</div>',
                unsafe_allow_html=True,
            )
            _term  = st.empty()
            _prog  = st.progress(0)
            _lines: list[str] = [
                f"$ python data_generator.py --mode batch --trips {n_trips}",
                f"  Mode: {_mode_label} | DQ rate: {_dq_rate}% | {g_start} -> {g_end}",
                "",
            ]

            _STEPS_KW = [
                "fleet","vehicle_type","vehicle","customer","driver",
                "booking","trip","fuel","maintenance","telematics",
                "expense","invoice","payment","billing","writing","done",
            ]

            def _clr(ln: str) -> str:
                s = ln.strip()
                if s.startswith("✅"):  return f'<span class="ok">{ln}</span>'
                if s.startswith("⚠️"):  return f'<span class="warn">{ln}</span>'
                if s.startswith("❌"):  return f'<span class="err">{ln}</span>'
                if s.startswith(("$","  Mode")):return f'<span class="hdr">{ln}</span>'
                if s.startswith("📄") or s.startswith("  ✅"): return f'<span class="inf">{ln}</span>'
                return f'<span class="dim">{ln}</span>'

            def _render():
                body = "\n".join(_clr(ln) for ln in _lines[-70:])
                _term.markdown(f'<div class="gen-terminal">{body}</div>', unsafe_allow_html=True)

            _render()

            try:
                import os as _os
                _env = {**_os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
                proc = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT, text=True, bufsize=1,
                    encoding="utf-8", errors="replace", env=_env,
                )
                _sidx = 0
                for raw in proc.stdout:
                    ln = raw.rstrip()
                    if not ln:
                        continue
                    _lines.append(ln)
                    st.session_state.acad_gen_log.append(ln)
                    for _kw in _STEPS_KW[_sidx:]:
                        if _kw in ln.lower():
                            _sidx = min(_STEPS_KW.index(_kw) + 1, len(_STEPS_KW))
                            _prog.progress(
                                int(_sidx / len(_STEPS_KW) * 90),
                                text=f"⏳ {ln[:55]}…",
                            )
                            break
                    _render()

                proc.wait()
                _prog.progress(100, text="✅ Generation complete!")
                _done = f"✅ Done (exit {proc.returncode}) -- {datetime.now():%H:%M:%S}"
                _lines.append(_done)
                st.session_state.acad_gen_log.append(_done)

                # Update pipeline state row counts
                try:
                    _state = load_state()
                    for _f in OLTP_DIR.glob("*.csv"):
                        _tbl = _f.stem
                        _state["total_rows_loaded"][_tbl] = \
                            sum(1 for _ in open(_f, encoding="utf-8")) - 1
                    save_state(_state)
                    _lines.append(f"📊 Watermarks reset -- {len(list(OLTP_DIR.glob('*.csv')))} tables tracked")
                except Exception:
                    pass

                _render()

            except Exception as _ex:
                _lines.append(f"❌ Error: {_ex}")
                _render()

    elif st.session_state.acad_gen_log:
        st.markdown(
            f'<div class="term-bar">'
            f'<span class="term-dot" style="background:#ff5f57;"></span>'
            f'<span class="term-dot" style="background:#febc2e;"></span>'
            f'<span class="term-dot" style="background:#28c840;"></span>'
            f'&nbsp; data_generator.py &nbsp;.&nbsp; last run</div>',
            unsafe_allow_html=True,
        )

        def _clr_s(ln):
            s = ln.strip()
            if s.startswith("✅"):   return f'<span class="ok">{ln}</span>'
            if s.startswith("⚠️"):   return f'<span class="warn">{ln}</span>'
            if s.startswith("❌"):   return f'<span class="err">{ln}</span>'
            if s.startswith(("$","  Mode")): return f'<span class="hdr">{ln}</span>'
            return f'<span class="dim">{ln}</span>'

        _body = "\n".join(_clr_s(ln) for ln in st.session_state.acad_gen_log[-60:])
        st.markdown(f'<div class="gen-terminal">{_body}</div>', unsafe_allow_html=True)
        if st.button("🗑 Clear Generator Log", key="clr_gen"):
            st.session_state.acad_gen_log = []
            st.rerun()

    # ── DQ pills ────────────────────────────────────────────────────────
    st.markdown(_h3("🐛 Injected DQ Issue Types (~3% of rows)", AMBER), unsafe_allow_html=True)
    _dq_cols = st.columns(5)
    for _dcol, (_iss, _det, _clr2) in zip(_dq_cols, [
        ("Null Field",        "full_name / email = ''", BRAND),
        ("Bad Email",         "Missing @ symbol",       AMBER),
        ("Timeline Reversed", "dropoff < pickup",       ORANGE),
        ("Fuel Outlier",      "< 2 or > 40 kmpl",       PUR),
        ("Zero Fare",         "trip_fare_pkr = 0",      STEEL),
    ]):
        with _dcol:
            st.markdown(_card(
                f'<div style="font-size:.74rem;font-weight:700;color:{_clr2};">{_iss}</div>'
                f'<div style="font-size:.68rem;color:{M};margin-top:2px;">{_det}</div>',
                left=_clr2, pad="10px 12px",
            ), unsafe_allow_html=True)

    # ── File status ─────────────────────────────────────────────────────
    st.markdown(_h3("📂 Live File Status", STEEL), unsafe_allow_html=True)
    _rfr1, _rfr2, _ = st.columns([1, 1, 4])
    with _rfr1:
        if st.button("🔄 Refresh", key="refresh_files"):
            st.rerun()
    with _rfr2:
        _show_all = st.checkbox("Show all tables", key="show_all_tables")

    _fs = get_file_sizes()
    _table_rows = []
    for _fname, _info in _fs.items():
        if not _show_all and _info["status"] == "❌ Missing":
            continue
        _table_rows.append({
            "File":      _fname,
            "Rows":      f"{_info['rows']:,}" if _info['rows'] else "--",
            "KB":        f"{_info['kb']:,}" if _info['kb'] else "--",
            "Modified":  _info["modified"],
            "Location":  _info["status"],
        })
    if _table_rows:
        st.dataframe(pd.DataFrame(_table_rows), use_container_width=True,
                     hide_index=True, height=340)
    else:
        st.info("No CSV files found. Run the generator to create data.")

    # ── Incremental detection preview ───────────────────────────────────
    st.markdown(_h3("🆕 New Row Detection (Watermark Preview)", TEAL), unsafe_allow_html=True)
    if st.button("🔍 Scan for New Rows", key="scan_new"):
        _new = detect_new_files()
        if _new:
            _nd = []
            for _tbl, _inf in _new.items():
                _nd.append({
                    "Table":       _tbl,
                    "Total Rows":  f"{_inf['total_rows']:,}",
                    "New Rows":    f"{_inf['new_rows']:,}",
                    "Watermark":   str(_inf['watermark'] or "none -- first load"),
                    "Action":      "⚡ Incremental" if _inf['new_rows'] < _inf['total_rows'] else "🔄 Full Load",
                })
            st.dataframe(pd.DataFrame(_nd), use_container_width=True,
                         hide_index=True, height=280)
        else:
            st.success("✅ No new rows. DWH is up to date.")

    # ── Archive history ─────────────────────────────────────────────────
    st.markdown(_h3("📦 Archive History", STEEL), unsafe_allow_html=True)
    _arcs = list_archives()
    if _arcs:
        _ad = []
        for _a in _arcs[:10]:
            _ad.append({
                "Run Timestamp": _a.get("folder","--"),
                "Files Archived": _a.get("count", 0),
                "File List": ", ".join(_a.get("files", [])[:3]) + ("…" if len(_a.get("files",[]))>3 else ""),
            })
        st.dataframe(pd.DataFrame(_ad), use_container_width=True, hide_index=True, height=240)
    else:
        st.info("No archives yet. Run a Full ETL Load to create the first archive.")


# ═══════════════════════════════════════════════════════════════════════
# TAB 2 -- ETL PIPELINE  (full . incremental . stream . DQ . archive)
# ═══════════════════════════════════════════════════════════════════════
with T[2]:
    from app.dwh_engine import ETLPipeline, load_state, detect_new_files, run_dq_summary

    st.markdown(_h2("ETL / ELT Pipeline", "🔄"), unsafe_allow_html=True)

    # ── Mode cards ──────────────────────────────────────────────────────
    _mc1, _mc2, _mc3 = st.columns(3)
    with _mc1:
        st.markdown(_card(
            f'<div style="font-size:.88rem;font-weight:800;color:{BRAND};">🔄 Full Load</div>'
            f'<div style="font-size:.75rem;color:{TEXT};line-height:1.65;margin-top:6px;">'
            f'Rebuilds entire DWH from scratch.<br>'
            f'Archives source CSVs after load.<br>'
            f'<b style="color:{AMBER};">Use:</b> first run or schema change.</div>',
            left=BRAND,
        ), unsafe_allow_html=True)
    with _mc2:
        st.markdown(_card(
            f'<div style="font-size:.88rem;font-weight:800;color:{TEAL};">⚡ Incremental</div>'
            f'<div style="font-size:.75rem;color:{TEXT};line-height:1.65;margin-top:6px;">'
            f'Detects new rows via watermark.<br>'
            f'Re-runs only staging + facts.<br>'
            f'<b style="color:{AMBER};">Use:</b> daily / after generator runs.</div>',
            left=TEAL,
        ), unsafe_allow_html=True)
    with _mc3:
        st.markdown(_card(
            f'<div style="font-size:.88rem;font-weight:800;color:{PUR};">📡 Stream Batch</div>'
            f'<div style="font-size:.75rem;color:{TEXT};line-height:1.65;margin-top:6px;">'
            f'Drains data/csv/stream/ -> appends.<br>'
            f'Then runs incremental load.<br>'
            f'<b style="color:{AMBER};">Use:</b> streaming micro-batch.</div>',
            left=PUR,
        ), unsafe_allow_html=True)

    # ── Pipeline stage visual ────────────────────────────────────────────
    st.markdown(_h3("📋 Pipeline Stages", STEEL), unsafe_allow_html=True)
    _STAGE_DEFS = [
        ("1 . Extract",        "read_csv_auto() -> raw.v_* views. Zero-copy, always reads latest CSV.", "📥", BRAND),
        ("2 . DQ Audit",       "6 checks: nulls, dupes, format, range, ref integrity, biz rules -> meta.dq_issues.", "🔍", AMBER),
        ("3 . Stage & Clean",  "TRY_CAST . COALESCE . TRIM . QUALIFY dedup . _dq_* flags preserved.", "🧹", STEEL),
        ("4 . Load Dims",      "dim_date . dim_customer(SCD2) . dim_vehicle . dim_driver . dim_fleet . dim_location.", "🌟", TEAL),
        ("5 . Load Facts",     "fact_trips . fact_invoices . fact_payments . fact_fuel_logs . fact_maintenance . fact_telematics.", PUR, PUR),
        ("6 . Archive",        "Source CSVs moved to data/csv/archive/YYYY-MM-DD_HH-MM-SS/ with manifest.json.", "📦", ORANGE),
    ]
    for _sname, _sdesc, _sic, _scol in _STAGE_DEFS:
        st.markdown(_concept(_sname, _sdesc, _sic, _scol), unsafe_allow_html=True)

    # ── ETL Run buttons ─────────────────────────────────────────────────
    st.markdown(_h3("▶ Run Pipeline", BRAND), unsafe_allow_html=True)

    _archive_opt = st.checkbox(
        "📦 Archive source CSVs after Full Load", value=True, key="etl_archive"
    )

    _eb1, _eb2, _eb3 = st.columns(3)
    _btn_full  = _eb1.button("🔄 Full Load",        type="primary",   use_container_width=True, key="btn_full")
    _btn_incr  = _eb2.button("⚡ Incremental Load", type="secondary", use_container_width=True, key="btn_incr")
    _btn_strm  = _eb3.button("📡 Stream Batch",     type="secondary", use_container_width=True, key="btn_strm")

    def _etl_terminal(log_lines: list[str], label: str) -> None:
        """Render an ETL terminal block from a list of log lines."""
        st.markdown(
            f'<div class="term-bar">'
            f'<span class="term-dot" style="background:#ff5f57;"></span>'
            f'<span class="term-dot" style="background:#febc2e;"></span>'
            f'<span class="term-dot" style="background:#28c840;"></span>'
            f'&nbsp; {label}</div>',
            unsafe_allow_html=True,
        )
        def _c(ln):
            s = ln.strip()
            if s.startswith("✅"):  return f'<span class="ok">{ln}</span>'
            if s.startswith("⚠️"):  return f'<span class="warn">{ln}</span>'
            if s.startswith("❌"):  return f'<span class="err">{ln}</span>'
            if s.startswith("⏭"):  return f'<span class="dim">{ln}</span>'
            if s.startswith(("$","  Mode","  Found")): return f'<span class="hdr">{ln}</span>'
            if s.startswith("  ──"): return f'<span class="inf">{ln}</span>'
            return ln
        body = "\n".join(_c(ln) for ln in log_lines)
        st.markdown(f'<div class="gen-terminal">{body}</div>', unsafe_allow_html=True)

    def _run_etl_with_ui(mode: str) -> None:
        """Run an ETL pipeline mode with live terminal + progress bar."""
        _etl_prog = st.progress(0, text="⏳ Initialising…")
        _etl_live = st.empty()
        _live_log: list[str] = []

        def _on_log(msg: str) -> None:
            _live_log.append(msg)
            # Re-render
            def _c(ln):
                s = ln.strip()
                if s.startswith("✅"):  return f'<span class="ok">{ln}</span>'
                if s.startswith("⚠️"):  return f'<span class="warn">{ln}</span>'
                if s.startswith("❌"):  return f'<span class="err">{ln}</span>'
                if s.startswith("⏭"):  return f'<span class="dim">{ln}</span>'
                if s.startswith(("$","  Mode","  Found")): return f'<span class="hdr">{ln}</span>'
                if s.startswith("  ──"): return f'<span class="inf">{ln}</span>'
                return ln
            body = "\n".join(_c(ln) for ln in _live_log[-80:])
            _etl_live.markdown(f'<div class="gen-terminal">{body}</div>', unsafe_allow_html=True)

        def _on_progress(pct: int, text: str) -> None:
            _etl_prog.progress(pct, text=text)

        pipe = ETLPipeline(on_log=_on_log, on_progress=_on_progress)

        if mode == "full":
            result = pipe.run_full(archive_after=_archive_opt)
        elif mode == "incremental":
            result = pipe.run_incremental()
        else:
            result = pipe.run_stream_batch()

        st.session_state.acad_etl_log = _live_log

        if result.get("success"):
            _etl_prog.progress(100, text="✅ Complete!")
            if mode == "full" and result.get("archive"):
                st.success(f"✅ Full load done. Archived to: `{result['archive']}`")
            elif mode == "incremental":
                st.success(
                    f"✅ Incremental done. "
                    f"{result.get('tables_updated', 0)} tables updated, "
                    f"{result.get('new_rows_total', 0):,} new rows."
                )
        else:
            st.error("❌ Pipeline failed -- see terminal above.")

    # Label for the terminal header
    if _btn_full:
        _etl_terminal_label = "etl_pipeline.sql . Full Load"
        st.markdown(
            f'<div class="term-bar">'
            f'<span class="term-dot" style="background:#ff5f57;"></span>'
            f'<span class="term-dot" style="background:#febc2e;"></span>'
            f'<span class="term-dot" style="background:#28c840;"></span>'
            f'&nbsp; etl_pipeline.sql &nbsp;.&nbsp; <b>FULL LOAD</b> &nbsp;.&nbsp; '
            f'archive={_archive_opt}</div>',
            unsafe_allow_html=True,
        )
        _run_etl_with_ui("full")

    elif _btn_incr:
        st.markdown(
            f'<div class="term-bar">'
            f'<span class="term-dot" style="background:#ff5f57;"></span>'
            f'<span class="term-dot" style="background:#febc2e;"></span>'
            f'<span class="term-dot" style="background:#28c840;"></span>'
            f'&nbsp; etl_pipeline.sql &nbsp;.&nbsp; <b>INCREMENTAL LOAD</b></div>',
            unsafe_allow_html=True,
        )
        _run_etl_with_ui("incremental")

    elif _btn_strm:
        st.markdown(
            f'<div class="term-bar">'
            f'<span class="term-dot" style="background:#ff5f57;"></span>'
            f'<span class="term-dot" style="background:#febc2e;"></span>'
            f'<span class="term-dot" style="background:#28c840;"></span>'
            f'&nbsp; etl_pipeline.sql &nbsp;.&nbsp; <b>STREAM MICRO-BATCH</b></div>',
            unsafe_allow_html=True,
        )
        _run_etl_with_ui("stream")

    elif st.session_state.acad_etl_log:
        _etl_terminal(st.session_state.acad_etl_log, "etl_pipeline.sql . previous run")

    # ── Pipeline state summary ──────────────────────────────────────────
    st.markdown(_h3("📊 Pipeline State", TEAL), unsafe_allow_html=True)
    _ps_col1, _ps_col2 = st.columns([2, 1])
    with _ps_col1:
        _pstate = load_state()
        _ps_rows = [
            {"Key": "Last Full Load",    "Value": str(_pstate.get("last_full_load") or "Never")},
            {"Key": "Last Incremental",  "Value": str(_pstate.get("last_incremental") or "Never")},
            {"Key": "Last Stream Event", "Value": str(_pstate.get("last_stream_event") or "Never")},
            {"Key": "Total ETL Runs",    "Value": str(_pstate.get("run_count", 0))},
            {"Key": "Archive Runs",      "Value": str(len(_pstate.get("archive_runs", [])))},
            {"Key": "Tables Tracked",    "Value": str(len(_pstate.get("total_rows_loaded", {})))},
        ]
        st.dataframe(pd.DataFrame(_ps_rows), use_container_width=True,
                     hide_index=True, height=250)
    with _ps_col2:
        if st.button("🗑 Reset State", key="reset_state"):
            from app.dwh_engine import STATE_FILE
            if STATE_FILE.exists():
                STATE_FILE.unlink()
            st.success("State reset.")
            st.rerun()
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Reload Dashboard Data", key="reload_dashboard",
                     help="Clears the data cache so all KPIs, charts and pages show the latest ETL results",
                     type="primary", use_container_width=True):
            # Clear Streamlit's cache so get_data() re-reads from updated parquet/csv
            st.cache_data.clear()
            # Also reset the in-memory DuckDB connection so SQL Editor uses fresh data
            st.session_state.acad_conn = None
            st.success("✅ Cache cleared! All pages will reload with the latest data.")
            st.rerun()

    # ── Live DQ demo ────────────────────────────────────────────────────
    st.markdown(_h3("🔬 Live DQ Check", AMBER), unsafe_allow_html=True)
    _dq_opt1, _dq_opt2 = st.columns([2, 1])
    with _dq_opt1:
        _DQ_QUERIES = {
            "Null Rate Summary": """
SELECT 'trips' AS tbl, COUNT(*) AS total,
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
            "Timeline Violations": """
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
            "Duplicate Customers": """
SELECT email, COUNT(*) AS cnt
FROM customers
WHERE email IS NOT NULL AND TRIM(email) != ''
GROUP BY email HAVING COUNT(*) > 1
ORDER BY cnt DESC LIMIT 15""",
            "Orphan Trips": """
SELECT t.trip_id, t.customer_id
FROM trips t LEFT JOIN customers c ON t.customer_id = c.customer_id
WHERE c.customer_id IS NULL AND t.customer_id IS NOT NULL
LIMIT 15""",
        }
        _dq_sel = st.selectbox("Select DQ check:", list(_DQ_QUERIES.keys()), key="dq_sel")
    with _dq_opt2:
        st.markdown("<br>", unsafe_allow_html=True)
        _run_dq_btn = st.button("▶ Run Check", key="run_dq", type="secondary", use_container_width=True)
    _sql(_DQ_QUERIES[_dq_sel])
    if _run_dq_btn:
        _show(_run(_DQ_QUERIES[_dq_sel], conn))

    # ── Quick DQ scan ───────────────────────────────────────────────────
    st.markdown(_h3("📋 Quick DQ Scan (all CSV files)", AMBER), unsafe_allow_html=True)
    if st.button("🔍 Run Full DQ Scan", key="run_full_dq"):
        with st.spinner("Scanning CSV files…"):
            _dq_df = run_dq_summary()
        if not _dq_df.empty:
            st.dataframe(_dq_df, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════════════
# TAB 3 -- STAR SCHEMA
# ═══════════════════════════════════════════════════════════════════════
with T[3]:
    st.markdown(_h2("Kimball Star Schema", "🌟"), unsafe_allow_html=True)
    st.markdown(_card(
        f'One central <b style="color:{BRAND};">FACT table</b> (many rows, measures + FK refs) surrounded by '
        f'<b style="color:{TEAL};">DIMENSION tables</b> (fewer rows, descriptive attributes).<br>'
        f'Query pattern: JOIN fact -> dims -> filter on dim attributes -> aggregate measures.',
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
        '&nbsp;make, model, year&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;pickup_date_key -> dim_date&nbsp;&nbsp;full_name, safety_tier<br>'
        '&nbsp;category, fleet_name&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;customer_sk -> dim_customer&nbsp;experience_band<br>'
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
            "dim_date -- The most important dimension",
            "Every fact table JOINs to dim_date via an integer key (YYYYMMDD: e.g. 20240315). "
            "Pre-computed attributes (is_weekend, quarter_label, is_pk_holiday) allow instant filtering "
            "without date functions at query time. Built from a date spine -- no source data needed.",
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
            "SCD Type 2 -- Track history of attribute changes",
            "When a customer moves city or upgrades type, we <b>don't overwrite</b> the old record.<br>"
            "Instead: set old row's <code>valid_to = yesterday, is_current = false</code> -> "
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

-- Point-in-time query: customer city AT TIME OF BOOKING
SELECT t.trip_id, t.pickup_datetime, dc.city AS city_at_booking
FROM fact_trips t
JOIN dim_customer dc
  ON  t.customer_id = dc.customer_id
 AND  t.pickup_datetime::DATE BETWEEN dc.valid_from AND dc.valid_to;""")

    with _dt[2]:
        st.markdown(_concept(
            "Conformed Dimension -- reused across multiple facts",
            "dim_vehicle is joined by fact_trips, fact_fuel_logs, AND fact_maintenance. "
            "Because all three use the same dim, you can cross-fact query: "
            "'Show maintenance cost vs revenue for each vehicle this quarter' -- in one SQL.",
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
            "fact_trips -- Core Revenue Fact (grain: 1 row = 1 trip)",
            "Contains FK references to all dimensions + all measurable facts.<br>"
            "Pre-computed derived metrics (revenue_per_day, revenue_per_km) avoid repeated calc at query time.<br>"
            "DQ flag columns (_dq_zero_fare, _dq_timeline_reversed) let analysts filter bad rows.",
            "📊", BRAND,
        ), unsafe_allow_html=True)
        _sql("""-- fact_trips key columns
-- trip_sk             surrogate PK (integer, stable)
-- trip_id             natural key from source
-- pickup_date_key     FK to dim_date (YYYYMMDD integer)
-- customer_sk         FK -> dim_customer
-- vehicle_sk          FK -> dim_vehicle
-- driver_sk           FK -> dim_driver
-- fleet_sk            FK -> dim_fleet
-- booking_type_sk     FK -> dim_booking_type
-- pickup_location_sk  FK -> dim_location
-- MEASURES:
-- trip_fare_pkr       revenue (PKR)
-- distance_km         operational
-- duration_days       operational
-- revenue_per_day     derived at load time
-- revenue_per_km      derived at load time
-- is_intercity        flag
-- _dq_zero_fare       data quality flag""")


# ═══════════════════════════════════════════════════════════════════════
# TAB 4 -- JOINS
# ═══════════════════════════════════════════════════════════════════════
with T[4]:
    st.markdown(_h2("SQL Joins -- Complete Guide", "🔗"), unsafe_allow_html=True)

    _JOINS = {
        "INNER JOIN -- matching rows only": {
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
        "LEFT JOIN -- all left + optional right": {
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
        "LEFT JOIN Anti-join -- rows with NO match": {
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
        "SELF JOIN -- table joined to itself": {
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
        "CROSS JOIN -- every row x every row": {
            "desc": "Cartesian product -- every left row paired with every right row. Use to build all combinations of reference data.",
            "sql": """
-- All fleet x vehicle_type combinations
-- Shows which types each fleet offers (and which it does not)
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
        "FULL OUTER JOIN -- all rows from both sides": {
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
# TAB 5 -- AGGREGATIONS
# ═══════════════════════════════════════════════════════════════════════
with T[5]:
    st.markdown(_h2("Aggregations -- GROUP BY, ROLLUP, CUBE, PERCENTILE", "📊"), unsafe_allow_html=True)

    _AGGS = {
        "Basic GROUP BY -- COUNT, SUM, AVG, MIN, MAX, STDDEV": """
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

        "HAVING -- filter after aggregation (not WHERE)": """
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

        "FILTER clause -- conditional aggregation (pivot-style)": """
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

        "ROLLUP -- hierarchical subtotals": """
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

        "CUBE -- all subtotal combinations": """
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

        "PERCENTILE -- median, quartiles, IQR": """
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

        "STDDEV / CV -- pricing consistency check": """
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
# TAB 6 -- WINDOW FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════
with T[6]:
    st.markdown(_h2("Window Functions -- Complete Guide", "🪟"), unsafe_allow_html=True)
    st.markdown(_card(
        f'Window functions compute across <b>a set of rows related to the current row</b> '
        f'<i>without collapsing them</i> (unlike GROUP BY).<br>'
        f'Syntax: <code>fn() OVER (PARTITION BY … ORDER BY … ROWS/RANGE …)</code>',
        left=STEEL,
    ), unsafe_allow_html=True)

    _WF = {
        "ROW_NUMBER -- unique sequential number per partition": """
-- Number each customer\'s trips chronologically
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

        "RANK vs DENSE_RANK -- tie handling": """
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

        "NTILE -- divide rows into N equal buckets": """
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

        "LAG & LEAD -- access previous / next row": """
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

        "Running Total -- UNBOUNDED PRECEDING": """
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

        "Moving Average -- sliding window": """
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

        "QUALIFY -- filter on window result (DuckDB)": """
-- Get ONLY each vehicle's single best trip using QUALIFY
-- Without QUALIFY you'd need a subquery WHERE rn = 1
SELECT
    vehicle_id, trip_id, pickup_datetime, trip_fare_pkr,
    ROW_NUMBER() OVER (PARTITION BY vehicle_id ORDER BY trip_fare_pkr DESC) AS rn
FROM trips WHERE status = 'Completed'
QUALIFY rn = 1          -- DuckDB / Snowflake: filter on window result inline
ORDER BY trip_fare_pkr DESC
LIMIT 20""",

        "PERCENT_RANK & CUME_DIST -- relative position": """
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
            "All rows from start -> current row (running total)",
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
# TAB 7 -- ANALYTICAL SQL
# ═══════════════════════════════════════════════════════════════════════
with T[7]:
    st.markdown(_h2("Analytical SQL -- CTEs, Subqueries, Date/String", "🧠"), unsafe_allow_html=True)

    _ANAL = {
        "CTE -- WITH clause (multi-step readable query)": """
-- 3-step funnel: trips per customer -> completed -> conversion rate
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

        "Recursive CTE -- date spine / gap detection": """
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

        "EXISTS / NOT EXISTS -- semi-join": """
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

        "PIVOT-style -- years as columns": """
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

        "DATE functions -- comprehensive reference": """
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

        "STRING functions -- comprehensive reference": """
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

        "COALESCE / NULLIF / IIF -- null handling": """
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
# TAB 8 -- STREAMING
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
        ("Micro-Batch",    "Buffer 1-5 minutes of events then process as a mini-batch. Good compromise between pure batch and true streaming.", "⚡", PUR),
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
# TAB 9 -- CHEATSHEET
# ═══════════════════════════════════════════════════════════════════════
with T[9]:
    st.markdown(_h2("SQL Cheatsheet -- Quick Reference", "📋"), unsafe_allow_html=True)

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

-- CROSS: every row x every row
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

-- QUALIFY (DuckDB/Snowflake) -- filter on window result
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

-- QUALIFY (DuckDB) -- filter window without subquery
SELECT * FROM t QUALIFY ROW_NUMBER() OVER (...) = 1""",

        "⚙️ ETL / Upsert Patterns": """\
-- Incremental insert (skip existing)
INSERT INTO target
SELECT * FROM source
WHERE id NOT IN (SELECT id FROM target)

-- Upsert (DuckDB)
INSERT OR REPLACE INTO target SELECT * FROM source

-- Deduplication -- keep latest record per key
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
        "Download Full Cheatsheet (.sql)",
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
                    f"{_fname}",
                    data=_fpath.read_text(encoding="utf-8"),
                    file_name=_fname,
                    mime="text/plain",
                    key=f"dl_{_idx}_{_fname}",
                )
            else:
                st.markdown(
                    f'<div style="font-size:.68rem;color:{M};">Missing: {_fname}</div>',
                    unsafe_allow_html=True,
                )


# ═══════════════════════════════════════════════════════════════════════
# TAB 10 — LIVE SQL EDITOR  (write, run, save, catalog)
# ═══════════════════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════════════════════════
# TAB 10 — LIVE SQL EDITOR
# ══════════════════════════════════════════════════════════════════════════════
with T[10]:
    import json as _json
    from pathlib import Path as _Path

    # Catalog persistence path
    _CATALOG_FILE = _Path("data/sql_catalog.json")
    _CATALOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    # ── Load / save catalog ────────────────────────────────────────────
    def _load_catalog() -> dict:
        if "acad_catalog" in st.session_state and st.session_state.acad_catalog:
            return st.session_state.acad_catalog
        if _CATALOG_FILE.exists():
            try:
                return _json.loads(_CATALOG_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {}

    def _save_catalog(cat: dict) -> None:
        st.session_state.acad_catalog = cat
        try:
            _CATALOG_FILE.write_text(_json.dumps(cat, indent=2), encoding="utf-8")
        except Exception:
            pass

    _catalog = _load_catalog()

    # ── Pre-built starter queries (Academy examples + DWH queries) ─────
    _STARTER_QUERIES = {
        # ── General ──────────────────────────────────────────────────────
        "Show all tables": """SELECT table_name
FROM information_schema.tables
WHERE table_schema NOT IN ('information_schema','pg_catalog')
ORDER BY table_name""",

        "Table row counts": """SELECT 'trips'      AS tbl, COUNT(*) AS rows FROM trips
UNION ALL SELECT 'customers',  COUNT(*) FROM customers
UNION ALL SELECT 'vehicles',   COUNT(*) FROM vehicles
UNION ALL SELECT 'drivers',    COUNT(*) FROM drivers
UNION ALL SELECT 'fleets',     COUNT(*) FROM fleets
UNION ALL SELECT 'invoices',   COUNT(*) FROM invoices
UNION ALL SELECT 'fuel_logs',  COUNT(*) FROM fuel_logs
UNION ALL SELECT 'maintenance',COUNT(*) FROM maintenance
UNION ALL SELECT 'telematics', COUNT(*) FROM telematics
ORDER BY rows DESC""",

        # ── Revenue ───────────────────────────────────────────────────────
        "Monthly revenue trend": """SELECT
    DATE_TRUNC('month', pickup_datetime::DATE)   AS month,
    COUNT(*)                                     AS trips,
    ROUND(SUM(trip_fare_pkr), 0)                 AS revenue_pkr,
    ROUND(AVG(trip_fare_pkr), 0)                 AS avg_fare,
    ROUND(SUM(trip_fare_pkr) - LAG(SUM(trip_fare_pkr))
        OVER (ORDER BY DATE_TRUNC('month', pickup_datetime::DATE)),0) AS mom_change
FROM trips
WHERE status = 'Completed'
GROUP BY 1 ORDER BY 1""",

        "Revenue by fleet": """SELECT
    f.fleet_name,
    COUNT(t.trip_id)                AS trips,
    ROUND(SUM(t.trip_fare_pkr), 0)  AS revenue_pkr,
    ROUND(AVG(t.trip_fare_pkr), 0)  AS avg_fare,
    ROUND(SUM(t.trip_fare_pkr) * 100.0
        / SUM(SUM(t.trip_fare_pkr)) OVER (), 1) AS pct_share
FROM trips t
JOIN fleets f ON t.fleet_id = f.fleet_id
WHERE t.status = 'Completed'
GROUP BY f.fleet_name
ORDER BY revenue_pkr DESC""",

        "Revenue by booking type": """SELECT
    booking_type,
    COUNT(*)                         AS trips,
    ROUND(SUM(trip_fare_pkr), 0)     AS revenue_pkr,
    ROUND(AVG(trip_fare_pkr), 0)     AS avg_fare,
    ROUND(MIN(trip_fare_pkr), 0)     AS min_fare,
    ROUND(MAX(trip_fare_pkr), 0)     AS max_fare
FROM trips
WHERE status = 'Completed'
GROUP BY booking_type
ORDER BY revenue_pkr DESC""",

        "Customer lifetime value": """SELECT
    c.customer_id,
    c.full_name,
    c.customer_type,
    c.city,
    COUNT(t.trip_id)                 AS total_trips,
    ROUND(SUM(t.trip_fare_pkr), 0)   AS total_spend_pkr,
    ROUND(AVG(t.trip_fare_pkr), 0)   AS avg_fare,
    MAX(t.pickup_datetime::DATE)     AS last_trip
FROM customers c
JOIN trips t ON c.customer_id = t.customer_id AND t.status = 'Completed'
GROUP BY c.customer_id, c.full_name, c.customer_type, c.city
HAVING COUNT(t.trip_id) >= 2
ORDER BY total_spend_pkr DESC
LIMIT 30""",

        "Invoice aging (AR)": """WITH aging AS (
    SELECT
        invoice_id, customer_id, total_amount_pkr,
        outstanding_pkr, due_date,
        DATE_DIFF('day', due_date, CURRENT_DATE) AS days_overdue
    FROM invoices WHERE outstanding_pkr > 0
)
SELECT
    CASE
        WHEN days_overdue <= 0  THEN 'Current'
        WHEN days_overdue <= 30 THEN '1-30 Days'
        WHEN days_overdue <= 60 THEN '31-60 Days'
        WHEN days_overdue <= 90 THEN '61-90 Days'
        ELSE '90+ Days'
    END                              AS bucket,
    COUNT(*)                         AS invoices,
    ROUND(SUM(outstanding_pkr), 0)   AS outstanding_pkr
FROM aging
GROUP BY 1
ORDER BY MIN(days_overdue)""",

        # ── Operations ────────────────────────────────────────────────────
        "Vehicle utilisation %": """WITH usage AS (
    SELECT vehicle_id,
           DATE_TRUNC('month', pickup_datetime::DATE) AS month,
           SUM(duration_days) AS days_used
    FROM trips WHERE status = 'Completed'
    GROUP BY 1, 2
)
SELECT
    v.make || ' ' || v.model  AS vehicle,
    u.month,
    ROUND(u.days_used, 2)     AS days_in_use,
    ROUND(u.days_used / 30.0 * 100, 1) AS utilisation_pct
FROM usage u
JOIN vehicles v ON u.vehicle_id = v.vehicle_id
ORDER BY u.month DESC, utilisation_pct DESC
LIMIT 50""",

        "Driver performance scorecard": """SELECT
    d.driver_id,
    d.full_name,
    d.behavior_profile,
    COUNT(t.trip_id)                 AS trips,
    ROUND(AVG(tl.safety_score), 1)   AS avg_safety_score,
    ROUND(AVG(tl.customer_rating), 2) AS avg_rating,
    SUM(CAST(tl.accident_occurred AS INT)) AS accidents,
    SUM(CAST(tl.complaint_filed AS INT))   AS complaints,
    RANK() OVER (ORDER BY AVG(tl.safety_score) DESC) AS safety_rank
FROM drivers d
JOIN trips t      ON d.driver_id = t.driver_id AND t.status = 'Completed'
JOIN telematics tl ON t.trip_id = tl.trip_id
GROUP BY d.driver_id, d.full_name, d.behavior_profile
HAVING COUNT(t.trip_id) >= 3
ORDER BY avg_safety_score DESC""",

        "Fuel efficiency by vehicle": """SELECT
    v.make || ' ' || v.model         AS vehicle,
    v.fuel_type,
    COUNT(f.fuel_id)                  AS fill_events,
    ROUND(AVG(f.fuel_efficiency_kmpl), 2) AS avg_efficiency_kmpl,
    ROUND(SUM(f.fuel_cost_pkr), 0)   AS total_fuel_cost,
    ROUND(SUM(f.km_driven), 0)       AS total_km
FROM fuel_logs f
JOIN vehicles v ON f.vehicle_id = v.vehicle_id
WHERE CAST(f.fuel_efficiency_kmpl AS DOUBLE) BETWEEN 3 AND 35
GROUP BY v.make, v.model, v.fuel_type
ORDER BY avg_efficiency_kmpl DESC""",

        "Maintenance cost analysis": """SELECT
    v.make || ' ' || v.model          AS vehicle,
    COUNT(m.maint_id)                  AS services,
    ROUND(SUM(m.total_cost_pkr), 0)   AS total_cost_pkr,
    ROUND(AVG(m.total_cost_pkr), 0)   AS avg_cost,
    STRING_AGG(DISTINCT m.maintenance_type, ', ') AS types
FROM maintenance m
JOIN vehicles v ON m.vehicle_id = v.vehicle_id
GROUP BY v.make, v.model
ORDER BY total_cost_pkr DESC
LIMIT 20""",

        # ── Window functions ──────────────────────────────────────────────
        "MoM revenue with LAG": """WITH monthly AS (
    SELECT
        fleet_id,
        DATE_TRUNC('month', pickup_datetime::DATE) AS month,
        SUM(trip_fare_pkr) AS revenue
    FROM trips WHERE status = 'Completed'
    GROUP BY 1, 2
)
SELECT
    fleet_id, month,
    ROUND(revenue, 0) AS revenue_pkr,
    ROUND(LAG(revenue) OVER (PARTITION BY fleet_id ORDER BY month), 0) AS prev_month,
    ROUND((revenue - LAG(revenue) OVER (PARTITION BY fleet_id ORDER BY month))
        * 100.0 / NULLIF(LAG(revenue) OVER (PARTITION BY fleet_id ORDER BY month), 0),
    1) AS mom_pct
FROM monthly
ORDER BY fleet_id, month""",

        "Running total revenue": """SELECT
    customer_id, trip_id, pickup_datetime, trip_fare_pkr,
    ROUND(SUM(trip_fare_pkr) OVER (
        PARTITION BY customer_id
        ORDER BY pickup_datetime
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ), 0) AS cumulative_spend,
    ROW_NUMBER() OVER (
        PARTITION BY customer_id ORDER BY pickup_datetime
    ) AS trip_seq
FROM trips
WHERE status = 'Completed'
ORDER BY customer_id, trip_seq
LIMIT 40""",

        "Top vehicle per fleet (QUALIFY)": """SELECT
    fleet_id, vehicle_id,
    ROUND(SUM(trip_fare_pkr), 0) AS revenue_pkr,
    COUNT(*) AS trips,
    ROW_NUMBER() OVER (PARTITION BY fleet_id ORDER BY SUM(trip_fare_pkr) DESC) AS rn
FROM trips
WHERE status = 'Completed'
GROUP BY fleet_id, vehicle_id
QUALIFY rn = 1
ORDER BY revenue_pkr DESC""",

        "Fare quartile buckets (NTILE)": """SELECT
    trip_id, booking_type, trip_fare_pkr,
    NTILE(4)  OVER (ORDER BY trip_fare_pkr) AS quartile,
    CASE NTILE(4) OVER (ORDER BY trip_fare_pkr)
        WHEN 1 THEN 'Budget'   WHEN 2 THEN 'Economy'
        WHEN 3 THEN 'Standard' WHEN 4 THEN 'Premium'
    END AS fare_tier,
    ROUND(PERCENT_RANK() OVER (ORDER BY trip_fare_pkr) * 100, 1) AS percentile
FROM trips WHERE status = 'Completed'
ORDER BY trip_fare_pkr
LIMIT 40""",

        # ── DQ checks ─────────────────────────────────────────────────────
        "DQ: null rate summary": """SELECT
    'trips'     AS tbl, COUNT(*) AS total,
    COUNT(*) FILTER (WHERE customer_id IS NULL OR customer_id = '')   AS null_key,
    COUNT(*) FILTER (WHERE CAST(trip_fare_pkr AS DOUBLE) <= 0)        AS bad_value,
    ROUND(COUNT(*) FILTER (WHERE CAST(trip_fare_pkr AS DOUBLE) <= 0)
        * 100.0 / NULLIF(COUNT(*), 0), 2) AS issue_pct
FROM trips
UNION ALL
SELECT 'customers', COUNT(*),
    COUNT(*) FILTER (WHERE full_name IS NULL OR TRIM(full_name) = ''),
    COUNT(*) FILTER (WHERE email NOT LIKE '%@%'),
    ROUND(COUNT(*) FILTER (WHERE email NOT LIKE '%@%')*100.0/NULLIF(COUNT(*),0),2)
FROM customers
UNION ALL
SELECT 'invoices', COUNT(*),
    COUNT(*) FILTER (WHERE total_amount_pkr IS NULL),
    COUNT(*) FILTER (WHERE total_amount_pkr <= 0),
    ROUND(COUNT(*) FILTER (WHERE total_amount_pkr <= 0)*100.0/NULLIF(COUNT(*),0),2)
FROM invoices
ORDER BY issue_pct DESC""",

        "DQ: timeline violations": """SELECT
    trip_id, pickup_datetime, dropoff_datetime,
    DATE_DIFF('hour', pickup_datetime, dropoff_datetime) AS dur_hours
FROM trips
WHERE CAST(dropoff_datetime AS TIMESTAMP) < CAST(pickup_datetime AS TIMESTAMP)
LIMIT 20""",

        "DQ: fuel efficiency outliers": """SELECT
    fuel_id, vehicle_id, trip_id,
    km_driven, litres_filled, fuel_efficiency_kmpl
FROM fuel_logs
WHERE CAST(fuel_efficiency_kmpl AS DOUBLE) < 3
   OR CAST(fuel_efficiency_kmpl AS DOUBLE) > 35
ORDER BY fuel_efficiency_kmpl
LIMIT 20""",

        # ── ETL patterns ─────────────────────────────────────────────────
        "Watermark: detect new rows": """-- Simulate watermark: rows that would be new since a given timestamp
SELECT
    COUNT(*) FILTER (WHERE pickup_datetime::DATE >= '2025-01-01') AS rows_since_2025,
    COUNT(*) FILTER (WHERE pickup_datetime::DATE >= '2026-01-01') AS rows_since_2026,
    COUNT(*) AS total
FROM trips""",

        "Incremental dedup pattern": """-- Keep only the latest record per trip_id (deduplication)
SELECT * FROM (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY trip_id
            ORDER BY pickup_datetime DESC
        ) AS rn
    FROM trips
)
WHERE rn = 1
ORDER BY pickup_datetime DESC
LIMIT 20""",
    }

    # Merge starter queries with user-saved catalog
    _full_catalog = {**_STARTER_QUERIES, **{f"[Saved] {k}": v for k, v in _catalog.items()}}

    # ── Header ─────────────────────────────────────────────────────────
    st.markdown(_h2("Live SQL Editor", "✏️"), unsafe_allow_html=True)
    st.markdown(_card(
        f'Write any SQL, run it live against the real data, save to your personal catalog.<br>'
        f'<b style="color:{TEAL};">Available tables:</b> trips, customers, vehicles, fleets, '
        f'drivers, invoices, fuel_logs, maintenance, telematics, billing_line_items, '
        f'operating_expenses, vehicle_types, rate_cards, staff, trip_legs',
        left=TEAL,
    ), unsafe_allow_html=True)

    # ── Layout: sidebar catalog | editor | results ─────────────────────
    _ec1, _ec2 = st.columns([1, 2])

    with _ec1:
        st.markdown(_h3("📚 Query Catalog", STEEL), unsafe_allow_html=True)

        # Search / filter catalog
        _cat_search = st.text_input("Search queries", placeholder="e.g. revenue, DQ, window", key="cat_search")

        _filtered = {k: v for k, v in _full_catalog.items()
                     if not _cat_search or _cat_search.lower() in k.lower()
                     or _cat_search.lower() in v.lower()}

        # Group by category prefix
        _groups: dict[str, list] = {}
        for _qname in _filtered:
            if _qname.startswith("[Saved]"):
                _grp = "My Saved Queries"
            elif "revenue" in _qname.lower() or "LTV" in _qname or "invoice" in _qname.lower():
                _grp = "Revenue & Finance"
            elif "DQ" in _qname or "null" in _qname.lower() or "timeline" in _qname.lower() or "outlier" in _qname.lower():
                _grp = "Data Quality"
            elif any(x in _qname.lower() for x in ["window","lag","running","ntile","qualify","percentile"]):
                _grp = "Window Functions"
            elif any(x in _qname.lower() for x in ["etl","watermark","dedup","incremental"]):
                _grp = "ETL Patterns"
            elif any(x in _qname.lower() for x in ["vehicle","driver","fuel","maintenance","utilisation","performance"]):
                _grp = "Operations"
            else:
                _grp = "General"
            _groups.setdefault(_grp, []).append(_qname)

        _grp_order = ["My Saved Queries","Revenue & Finance","Operations",
                      "Window Functions","Data Quality","ETL Patterns","General"]

        for _grp in _grp_order:
            if _grp not in _groups:
                continue
            st.markdown(
                f'<div style="font-size:.68rem;font-weight:700;color:{AMBER};'
                f'text-transform:uppercase;letter-spacing:.06em;margin:8px 0 2px;">'
                f'{_grp}</div>',
                unsafe_allow_html=True,
            )
            for _qname in _groups[_grp]:
                # Shorten name for button display
                _btn_label = _qname.replace("[Saved] ", "* ")
                if st.button(_btn_label, key=f"cat_{_qname}", use_container_width=True):
                    # Set BOTH the widget key AND the backup key so the editor updates
                    st.session_state["sql_editor_area"] = _filtered[_qname]
                    st.session_state.acad_editor_sql    = _filtered[_qname]
                    st.rerun()

        # Delete saved query
        if any(k.startswith("[Saved]") for k in _full_catalog):
            st.markdown("---")
            _del_sel = st.selectbox(
                "Delete saved query:",
                [""] + [k.replace("[Saved] ", "") for k in _full_catalog if k.startswith("[Saved]")],
                key="del_sel",
            )
            if _del_sel and st.button("🗑 Delete", key="del_query"):
                _catalog.pop(_del_sel, None)
                _save_catalog(_catalog)
                st.success(f"Deleted: {_del_sel}")
                st.rerun()

    with _ec2:
        st.markdown(_h3("✏️ SQL Editor", BRAND), unsafe_allow_html=True)

        # Initialize widget state on first load only (don't overwrite if already set)
        _SQL_DEFAULT = """-- Write your SQL here and click Run
-- All tables: trips, customers, vehicles, fleets, drivers, invoices, fuel_logs...

SELECT
    booking_type,
    COUNT(*)                        AS trips,
    ROUND(SUM(trip_fare_pkr), 0)    AS revenue_pkr,
    ROUND(AVG(trip_fare_pkr), 0)    AS avg_fare
FROM trips
WHERE status = 'Completed'
GROUP BY booking_type
ORDER BY revenue_pkr DESC"""

        if "sql_editor_area" not in st.session_state:
            st.session_state["sql_editor_area"] = _SQL_DEFAULT

        # ── ACE editor: SQL with syntax highlighting ───────────────────
        from streamlit_ace import st_ace as _st_ace
        _editor_val = _st_ace(
            value=st.session_state["sql_editor_area"],
            language="sql",
            theme="monokai",
            key="sql_ace_editor",
            height=300,
            font_size=14,
            tab_size=4,
            show_gutter=True,
            show_print_margin=False,
            wrap=False,
            auto_update=True,
            placeholder="-- Write your SQL here...",
        )
        # Keep session state in sync with editor content
        if _editor_val is not None:
            st.session_state["sql_editor_area"] = _editor_val

        # Row limit
        _rlim_col, _run_col, _save_col, _fmt_col = st.columns([1, 1, 1, 1])
        with _rlim_col:
            _row_limit = st.selectbox("Rows", [50, 100, 500, 1000, 5000, "All"], index=1, key="row_limit")
        with _run_col:
            _run_btn = st.button("▶ Run Query", type="primary", use_container_width=True, key="run_editor")
        with _save_col:
            _save_btn = st.button("💾 Save to Catalog", type="secondary", use_container_width=True, key="save_query")
        with _fmt_col:
            _dl_btn = st.button("⬇ Download SQL", type="secondary", use_container_width=True, key="dl_sql")

        # Save dialog
        if _save_btn:
            _save_name = st.text_input(
                "Query name (for catalog):",
                placeholder="e.g. My Revenue Analysis",
                key="save_name_input",
            )
            if _save_name and _save_name.strip():
                _catalog[_save_name.strip()] = _editor_val
                _save_catalog(_catalog)
                st.success(f"Saved: {_save_name}")
                st.rerun()

        # Download SQL
        if _dl_btn:
            st.download_button(
                "Download .sql",
                data=_editor_val,
                file_name="my_query.sql",
                mime="text/plain",
                key="dl_editor_sql",
            )

        # Run query
        if _run_btn:
            _sql_to_run = _editor_val.strip()
            if not _sql_to_run:
                st.warning("Enter a SQL query first.")
            else:
                # Apply row limit
                _apply_limit = ""
                if _row_limit != "All":
                    # Add LIMIT if not already present
                    if "LIMIT" not in _sql_to_run.upper().split()[-10:]:
                        _apply_limit = f"\nLIMIT {_row_limit}"

                _full_sql = _sql_to_run + _apply_limit
                st.session_state.acad_editor_sql = _editor_val

                with st.spinner("Running..."):
                    _result = _run(_full_sql, conn)

                if _result is not None:
                    st.session_state.acad_editor_result = _result
                    st.session_state.acad_editor_err    = ""
                else:
                    st.session_state.acad_editor_result = None

        # ── Results panel ───────────────────────────────────────────────
        if st.session_state.acad_editor_result is not None:
            _res = st.session_state.acad_editor_result
            if not _res.empty:
                _rcols = st.columns([3, 1, 1])
                with _rcols[0]:
                    st.markdown(
                        f'<div style="font-size:.78rem;color:{TEAL};margin:4px 0;">'
                        f'✅ {len(_res):,} rows x {len(_res.columns)} columns</div>',
                        unsafe_allow_html=True,
                    )
                with _rcols[1]:
                    # Download results as CSV
                    st.download_button(
                        "⬇ CSV",
                        data=_res.to_csv(index=False),
                        file_name="query_result.csv",
                        mime="text/csv",
                        key="dl_result_csv",
                    )
                with _rcols[2]:
                    _chart_types = ["None", "Bar", "Line", "Area", "Scatter"]
                    _chart_sel = st.selectbox("Chart", _chart_types, key="res_chart_type")

                # Data table
                st.dataframe(_res, use_container_width=True, height=320, hide_index=True)

                # Auto chart
                if _chart_sel != "None":
                    _num_cols = _res.select_dtypes("number").columns.tolist()
                    _str_cols = _res.select_dtypes("object").columns.tolist()
                    if _num_cols and (_str_cols or _res.index.dtype != "object"):
                        _x_opts = _str_cols + list(_res.columns[:3])
                        _x_ax = st.selectbox("X axis", list(dict.fromkeys(_x_opts)), key="chart_x")
                        _y_ax = st.selectbox("Y axis", _num_cols, key="chart_y")
                        try:
                            if _chart_sel == "Bar":
                                fig = px.bar(_res.head(30), x=_x_ax, y=_y_ax,
                                             template="plotly_dark",
                                             color_discrete_sequence=[BRAND])
                            elif _chart_sel == "Line":
                                fig = px.line(_res, x=_x_ax, y=_y_ax,
                                              template="plotly_dark",
                                              color_discrete_sequence=[TEAL])
                            elif _chart_sel == "Area":
                                fig = px.area(_res, x=_x_ax, y=_y_ax,
                                              template="plotly_dark",
                                              color_discrete_sequence=[AMBER])
                            else:
                                fig = px.scatter(_res, x=_x_ax, y=_y_ax,
                                                 template="plotly_dark",
                                                 color_discrete_sequence=[ORANGE])
                            fig.update_layout(
                                margin=dict(t=30, b=0, l=0, r=0), height=300,
                                paper_bgcolor="rgba(0,0,0,0)",
                                plot_bgcolor="rgba(0,0,0,0)",
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        except Exception as _ce:
                            st.warning(f"Chart error: {_ce}")
            else:
                st.info("Query returned 0 rows.")

        # ── Schema reference (collapsible) ──────────────────────────────
        with st.expander("📋 Table Schema Reference", expanded=False):
            _schema_info = {
                "trips":           "trip_id, booking_id, fleet_id, vehicle_id, driver_id, customer_id, booking_type_id, pickup_datetime, dropoff_datetime, duration_days, pickup_city, dropoff_city, distance_km, trip_fare_pkr, driver_allowance_pkr, with_driver, self_drive, status",
                "customers":       "customer_id, full_name, gender, dob, cnic, nationality, phone, email, city, customer_type, license_no, has_own_license, loyalty_points, total_bookings, registration_date",
                "vehicles":        "vehicle_id, fleet_id, vehicle_type_id, make, model, year, registration_no, color, fuel_type, transmission, seats, odometer_km, purchase_date, daily_rate_pkr, hourly_rate_pkr, insurance_expiry, status, condition_rating, gps_enabled",
                "drivers":         "driver_id, fleet_id, full_name, gender, dob, cnic, phone, license_no, license_expiry, hire_date, experience_years, base_salary_pkr, behavior_profile, harsh_brake_rate, harsh_accel_rate, idle_time_pct, speeding_pct, ratings_avg, active",
                "fleets":          "fleet_id, fleet_name, city, website, secp_registered, ntn_registered, established_year, focus_segment, total_vehicles, active",
                "invoices":        "invoice_id, trip_id, customer_id, fleet_id, invoice_date, due_date, base_fare_pkr, total_surcharge_pkr, discount_pkr, driver_allowance_pkr, tax_pkr, total_amount_pkr, paid_amount_pkr, outstanding_pkr, payment_method, payment_status",
                "fuel_logs":       "fuel_id, trip_id, vehicle_id, fleet_id, driver_id, fill_date, fuel_type, litres_filled, price_per_litre_pkr, fuel_cost_pkr, km_driven, fuel_efficiency_kmpl, odometer_at_fill, fill_station, paid_by",
                "maintenance":     "maint_id, vehicle_id, fleet_id, maintenance_type, maintenance_date, odometer_km, workshop, parts_cost_pkr, labour_cost_pkr, total_cost_pkr, status, next_due_km, next_due_date",
                "telematics":      "telem_id, trip_id, driver_id, vehicle_id, trip_date, distance_km, duration_hours, avg_speed_kmh, max_speed_kmh, harsh_brake_events, harsh_accel_events, idle_time_minutes, speeding_km, safety_score, accident_occurred, customer_rating, complaint_filed",
                "billing_line_items": "line_id, invoice_id, charge_type, description, qty, unit_price, amount_pkr, charge_type_id",
                "operating_expenses": "expense_id, fleet_id, expense_month, category, amount_pkr, description, approved_by",
                "vehicle_types":   "vehicle_type_id, category, sub_type, make, seats, fuel_type, transmission, daily_rate_min_pkr, daily_rate_max_pkr, fuel_eff_min_kmpl, fuel_eff_max_kmpl",
            }
            for _tbl, _cols in _schema_info.items():
                st.markdown(
                    f'<div style="margin:4px 0;">'
                    f'<span style="color:{BRAND};font-weight:700;font-size:.78rem;">{_tbl}</span>'
                    f'<span style="color:{M};font-size:.72rem;"> — {_cols}</span></div>',
                    unsafe_allow_html=True,
                )


# ═══════════════════════════════════════════════════════════════════════
# TAB 11 — PYTHON EDITOR
# ═══════════════════════════════════════════════════════════════════════
with T[11]:
    import io as _io
    import traceback as _tb
    import contextlib as _cl

    st.markdown(_h2("Python Editor", "🐍"), unsafe_allow_html=True)
    st.markdown(_card(
        f'Write and run Python code live against the real data.<br>'
        f'<b style="color:{TEAL};">Pre-loaded:</b> '
        f'<code>dfs</code> (dict of all DataFrames), '
        f'<code>pd</code> (pandas), '
        f'<code>np</code> (numpy), '
        f'<code>px</code> (plotly.express), '
        f'<code>conn</code> (DuckDB in-memory connection).<br>'
        f'<b style="color:{AMBER};">Output:</b> print() shows below, '
        f'DataFrames auto-display, Plotly figs auto-render.',
        left=TEAL,
    ), unsafe_allow_html=True)

    # Session state for python editor
    if "py_editor_code" not in st.session_state:
        st.session_state.py_editor_code = ""
    if "py_editor_out" not in st.session_state:
        st.session_state.py_editor_out = None
    if "py_catalog" not in st.session_state:
        st.session_state.py_catalog = {}

    # Load python catalog from disk
    _PY_CATALOG_FILE = _Path("data/py_catalog.json")
    if _PY_CATALOG_FILE.exists() and not st.session_state.py_catalog:
        try:
            st.session_state.py_catalog = _json.loads(_PY_CATALOG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass

    _PY_STARTERS = {
        "Hello — basic pandas": '''# Basic pandas operations on trips
print(f"Trips table: {dfs['trips'].shape}")
print(f"Columns: {list(dfs['trips'].columns)}")
print()
print(dfs['trips'].head(3).to_string())
''',
        "Revenue summary (pandas)": '''import pandas as pd
trips = dfs["trips"].copy()
trips["trip_fare_pkr"] = pd.to_numeric(trips["trip_fare_pkr"], errors="coerce")
completed = trips[trips["status"] == "Completed"]

summary = (completed
    .groupby("booking_type")
    .agg(
        trips=("trip_id","count"),
        revenue=("trip_fare_pkr","sum"),
        avg_fare=("trip_fare_pkr","mean"),
    )
    .round(0)
    .sort_values("revenue", ascending=False)
)
print(summary.to_string())
result = summary.reset_index()
''',
        "Plot revenue by month": '''import pandas as pd
import plotly.express as px

trips = dfs["trips"].copy()
trips["pickup_datetime"] = pd.to_datetime(trips["pickup_datetime"], errors="coerce")
trips["trip_fare_pkr"] = pd.to_numeric(trips["trip_fare_pkr"], errors="coerce")
trips = trips[trips["status"] == "Completed"]
trips["month"] = trips["pickup_datetime"].dt.to_period("M").astype(str)

monthly = trips.groupby("month")["trip_fare_pkr"].sum().reset_index()
monthly.columns = ["month", "revenue"]

fig = px.bar(monthly, x="month", y="revenue",
             title="Monthly Revenue (PKR)",
             template="plotly_dark",
             color_discrete_sequence=["#E63946"])
fig.update_layout(height=350)
print(f"Months: {len(monthly)} | Total: PKR {monthly.revenue.sum():,.0f}")
''',
        "Data cleaning pipeline": '''import pandas as pd
import numpy as np

raw = dfs["customers"].copy()
print(f"Raw: {raw.shape}")

# Step 1: flag issues
raw["email_valid"] = raw["email"].str.contains("@", na=False)
raw["name_missing"] = raw["full_name"].isna() | (raw["full_name"].str.strip() == "")

# Step 2: clean
cleaned = raw.copy()
cleaned["full_name"] = cleaned["full_name"].str.strip().str.title()
cleaned["email"] = cleaned["email"].str.lower().str.strip()
cleaned["city"] = cleaned["city"].str.strip()

# Step 3: report
print(f"Issues found:")
print(f"  Bad emails:    {(~raw.email_valid).sum()}")
print(f"  Missing names: {raw.name_missing.sum()}")
print(f"Cleaned shape: {cleaned.shape}")
result = cleaned.head(10)
''',
        "Statistical analysis": '''import pandas as pd
import numpy as np

trips = dfs["trips"].copy()
trips["trip_fare_pkr"] = pd.to_numeric(trips["trip_fare_pkr"], errors="coerce")
c = trips[trips["status"] == "Completed"]["trip_fare_pkr"].dropna()

print("=== Fare Distribution ===")
print(f"Count:    {len(c):,}")
print(f"Mean:     PKR {c.mean():,.0f}")
print(f"Median:   PKR {c.median():,.0f}")
print(f"Std Dev:  PKR {c.std():,.0f}")
print(f"P25:      PKR {c.quantile(0.25):,.0f}")
print(f"P75:      PKR {c.quantile(0.75):,.0f}")
print(f"P95:      PKR {c.quantile(0.95):,.0f}")
print(f"IQR:      PKR {c.quantile(0.75)-c.quantile(0.25):,.0f}")
print(f"Skewness: {c.skew():.3f}")
print(f"Kurtosis: {c.kurtosis():.3f}")
''',
        "ETL transform in Python": '''import pandas as pd
import numpy as np

# Replicate what the SQL ETL does — in Python
raw_trips = dfs["trips"].copy()
print(f"Raw trips: {raw_trips.shape}")

# Type casting
raw_trips["pickup_datetime"] = pd.to_datetime(raw_trips["pickup_datetime"], errors="coerce")
raw_trips["dropoff_datetime"] = pd.to_datetime(raw_trips["dropoff_datetime"], errors="coerce")
raw_trips["trip_fare_pkr"] = pd.to_numeric(raw_trips["trip_fare_pkr"], errors="coerce").fillna(0)
raw_trips["distance_km"] = pd.to_numeric(raw_trips["distance_km"], errors="coerce").clip(lower=0)

# Derived columns
raw_trips["duration_hours"] = (
    (raw_trips["dropoff_datetime"] - raw_trips["pickup_datetime"])
    .dt.total_seconds() / 3600
)
raw_trips["revenue_per_km"] = (
    raw_trips["trip_fare_pkr"] / raw_trips["distance_km"].replace(0, np.nan)
).round(2)

# DQ flags
raw_trips["_dq_timeline_reversed"] = (
    raw_trips["dropoff_datetime"] < raw_trips["pickup_datetime"]
)
raw_trips["_dq_zero_fare"] = raw_trips["trip_fare_pkr"] <= 0

# Deduplication
staged = raw_trips.sort_values("pickup_datetime", ascending=False).drop_duplicates("trip_id")

print(f"Staged trips: {staged.shape}")
print(f"DQ issues: timeline={raw_trips._dq_timeline_reversed.sum()}, zero_fare={raw_trips._dq_zero_fare.sum()}")
result = staged.head(5)
''',
        "RFM customer segmentation": '''import pandas as pd
import numpy as np
from datetime import datetime

trips = dfs["trips"].copy()
trips["pickup_datetime"] = pd.to_datetime(trips["pickup_datetime"], errors="coerce")
trips["trip_fare_pkr"] = pd.to_numeric(trips["trip_fare_pkr"], errors="coerce").fillna(0)
completed = trips[trips["status"] == "Completed"]

snapshot = completed["pickup_datetime"].max()

rfm = completed.groupby("customer_id").agg(
    recency=("pickup_datetime", lambda x: (snapshot - x.max()).days),
    frequency=("trip_id", "count"),
    monetary=("trip_fare_pkr", "sum"),
).reset_index()

# Score 1-5
for col in ["recency","frequency","monetary"]:
    ascending = col == "recency"  # lower recency = better
    rfm[f"{col}_score"] = pd.qcut(rfm[col], 5,
        labels=[5,4,3,2,1] if ascending else [1,2,3,4,5],
        duplicates="drop")

rfm["rfm_score"] = (rfm["recency_score"].astype(int)
                  + rfm["frequency_score"].astype(int)
                  + rfm["monetary_score"].astype(int))

rfm["segment"] = pd.cut(rfm["rfm_score"], bins=[0,5,8,11,15],
    labels=["At Risk","Regular","Loyal","Champion"])

print(rfm["segment"].value_counts().to_string())
result = rfm.sort_values("rfm_score", ascending=False).head(10)
''',
        "Matplotlib chart": '''import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import io, base64
import streamlit as st

trips = dfs["trips"].copy()
trips["trip_fare_pkr"] = pd.to_numeric(trips["trip_fare_pkr"], errors="coerce")
c = trips[trips["status"]=="Completed"]

fig, axes = plt.subplots(1, 2, figsize=(12, 4))
fig.patch.set_facecolor("#0d1117")

# Histogram
axes[0].hist(c["trip_fare_pkr"].dropna(), bins=30, color="#E63946", alpha=0.8)
axes[0].set_title("Fare Distribution", color="white")
axes[0].set_facecolor("#161b22")
axes[0].tick_params(colors="white")

# Revenue by booking type
rev = c.groupby("booking_type")["trip_fare_pkr"].sum().sort_values()
axes[1].barh(rev.index, rev.values, color="#2A9D8F")
axes[1].set_title("Revenue by Type", color="white")
axes[1].set_facecolor("#161b22")
axes[1].tick_params(colors="white")

plt.tight_layout()
buf = io.BytesIO()
plt.savefig(buf, format="png", dpi=100, facecolor=fig.get_facecolor())
buf.seek(0)
st.image(buf, use_container_width=True)
plt.close()
print("Matplotlib chart rendered above.")
''',
    }

    _all_py = {**_PY_STARTERS, **{f"[Saved] {k}": v for k, v in st.session_state.py_catalog.items()}}

    _pyc1, _pyc2 = st.columns([1, 2])

    with _pyc1:
        st.markdown(_h3("📚 Python Snippets", STEEL), unsafe_allow_html=True)
        _py_search = st.text_input("Search", key="py_search", placeholder="pandas, plot, ETL...")
        _py_filtered = {k: v for k, v in _all_py.items()
                        if not _py_search or _py_search.lower() in k.lower() or _py_search.lower() in v.lower()}

        for _pname in _py_filtered:
            _lbl = _pname.replace("[Saved] ", "* ")
            if st.button(_lbl, key=f"py_{hash(_pname)}", use_container_width=True):
                # Set the widget's own session state key directly so it updates immediately
                st.session_state["py_code_area"]  = _py_filtered[_pname]
                st.session_state.py_editor_code   = _py_filtered[_pname]
                st.session_state.py_editor_out    = None
                st.rerun()

        if any(k.startswith("[Saved]") for k in _all_py):
            st.markdown("---")
            _py_del = st.selectbox("Delete saved:", [""] + [k.replace("[Saved] ","") for k in _all_py if k.startswith("[Saved]")], key="py_del")
            if _py_del and st.button("🗑 Delete", key="py_del_btn"):
                st.session_state.py_catalog.pop(_py_del, None)
                _PY_CATALOG_FILE.write_text(_json.dumps(st.session_state.py_catalog, indent=2), encoding="utf-8")
                st.rerun()

    with _pyc2:
        st.markdown(_h3("✏️ Code Editor", BRAND), unsafe_allow_html=True)

        # Initialize widget state on first load only
        _PY_DEFAULT = _PY_STARTERS["Hello — basic pandas"]
        if "py_code_area" not in st.session_state:
            st.session_state["py_code_area"] = _PY_DEFAULT

        # ── ACE editor: Python with syntax highlighting ─────────────────
        from streamlit_ace import st_ace as _st_ace_py
        _py_code = _st_ace_py(
            value=st.session_state["py_code_area"],
            language="python",
            theme="monokai",
            key="py_ace_editor",
            height=320,
            font_size=14,
            tab_size=4,
            show_gutter=True,
            show_print_margin=False,
            wrap=False,
            auto_update=True,
            placeholder="# Write Python here...",
        )
        # Keep session state in sync
        if _py_code is not None:
            st.session_state["py_code_area"] = _py_code

        _py_r1, _py_r2, _py_r3, _py_r4 = st.columns(4)
        _py_run  = _py_r1.button("▶ Run", type="primary", use_container_width=True, key="py_run")
        _py_save = _py_r2.button("💾 Save", type="secondary", use_container_width=True, key="py_save")
        _py_clr  = _py_r3.button("🗑 Clear", type="secondary", use_container_width=True, key="py_clr")
        _py_dl   = _py_r4.button("⬇ Download", type="secondary", use_container_width=True, key="py_dl")

        if _py_clr:
            st.session_state["py_code_area"] = ""
            st.session_state.py_editor_code  = ""
            st.session_state.py_editor_out   = None
            st.rerun()

        if _py_dl:
            st.download_button("Download .py", data=_py_code, file_name="my_script.py",
                               mime="text/plain", key="dl_py_file")

        if _py_save:
            _py_sname = st.text_input("Script name:", key="py_save_name")
            if _py_sname:
                st.session_state.py_catalog[_py_sname] = _py_code
                _PY_CATALOG_FILE.write_text(_json.dumps(st.session_state.py_catalog, indent=2), encoding="utf-8")
                st.success(f"Saved: {_py_sname}")

        if _py_run:
            st.session_state.py_editor_code = _py_code
            _stdout_buf = _io.StringIO()
            _result_ns  = {}

            # Pre-load namespace with all data
            import numpy as _np
            _exec_globals = {
                "dfs":    dfs,
                "conn":   conn,
                "pd":     pd,
                "np":     _np,
                "px":     px,
                "go":     go,
                "st":     st,
                "result": None,
            }

            with _cl.redirect_stdout(_stdout_buf):
                try:
                    exec(compile(_py_code, "<editor>", "exec"), _exec_globals)
                    _exec_globals["_run_ok"] = True
                except Exception:
                    _exec_globals["_run_ok"] = False
                    _exec_globals["_err"] = _tb.format_exc()

            _output = _stdout_buf.getvalue()
            st.session_state.py_editor_out = {
                "stdout": _output,
                "ok":     _exec_globals.get("_run_ok", False),
                "err":    _exec_globals.get("_err", ""),
                "result": _exec_globals.get("result"),
            }

        if st.session_state.py_editor_out:
            _out = st.session_state.py_editor_out
            if _out["ok"]:
                if _out["stdout"]:
                    st.markdown(_h3("📤 Output", TEAL), unsafe_allow_html=True)
                    st.code(_out["stdout"], language="text")
                if _out["result"] is not None:
                    if isinstance(_out["result"], pd.DataFrame):
                        st.markdown(_h3(f"📋 result DataFrame ({len(_out['result'])} rows)", TEAL), unsafe_allow_html=True)
                        st.dataframe(_out["result"], use_container_width=True, height=280, hide_index=True)
                    else:
                        st.write(_out["result"])
            else:
                st.markdown(
                    f'<div style="background:#2d0a0a;border:1px solid #f85149;border-radius:8px;'
                    f'padding:12px;font-family:monospace;font-size:.76rem;color:#f85149;'
                    f'white-space:pre-wrap;">{_out["err"]}</div>',
                    unsafe_allow_html=True,
                )


# ═══════════════════════════════════════════════════════════════════════
# TAB 12 — DATA LINEAGE
# ═══════════════════════════════════════════════════════════════════════
with T[12]:
    st.markdown(_h2("Data Lineage", "🗺️"), unsafe_allow_html=True)
    st.markdown(_card(
        f'Trace how any table or metric flows through the pipeline: '
        f'CSV source -> raw view -> staging table -> DWH dimension/fact -> mart view -> dashboard.',
        left=TEAL,
    ), unsafe_allow_html=True)

    # Lineage graph data
    _LINEAGE = {
        "nodes": [
            # Source CSVs
            {"id": "csv_trips",      "label": "oltp_trips.csv",       "layer": "CSV",     "color": "#E63946"},
            {"id": "csv_customers",  "label": "oltp_customers.csv",    "layer": "CSV",     "color": "#E63946"},
            {"id": "csv_vehicles",   "label": "oltp_vehicles.csv",     "layer": "CSV",     "color": "#E63946"},
            {"id": "csv_drivers",    "label": "oltp_drivers.csv",      "layer": "CSV",     "color": "#E63946"},
            {"id": "csv_fleets",     "label": "oltp_fleets.csv",       "layer": "CSV",     "color": "#E63946"},
            {"id": "csv_invoices",   "label": "oltp_invoices.csv",     "layer": "CSV",     "color": "#E63946"},
            {"id": "csv_fuel",       "label": "oltp_fuel_logs.csv",    "layer": "CSV",     "color": "#E63946"},
            {"id": "csv_maint",      "label": "oltp_maintenance.csv",  "layer": "CSV",     "color": "#E63946"},
            {"id": "csv_telem",      "label": "oltp_telematics.csv",   "layer": "CSV",     "color": "#E63946"},
            # Raw views
            {"id": "raw_trips",      "label": "raw.v_trips",           "layer": "Raw",     "color": "#E9C46A"},
            {"id": "raw_customers",  "label": "raw.v_customers",       "layer": "Raw",     "color": "#E9C46A"},
            {"id": "raw_vehicles",   "label": "raw.v_vehicles",        "layer": "Raw",     "color": "#E9C46A"},
            {"id": "raw_drivers",    "label": "raw.v_drivers",         "layer": "Raw",     "color": "#E9C46A"},
            {"id": "raw_fleets",     "label": "raw.v_fleets",          "layer": "Raw",     "color": "#E9C46A"},
            {"id": "raw_invoices",   "label": "raw.v_invoices",        "layer": "Raw",     "color": "#E9C46A"},
            {"id": "raw_fuel",       "label": "raw.v_fuel_logs",       "layer": "Raw",     "color": "#E9C46A"},
            {"id": "raw_maint",      "label": "raw.v_maintenance",     "layer": "Raw",     "color": "#E9C46A"},
            {"id": "raw_telem",      "label": "raw.v_telematics",      "layer": "Raw",     "color": "#E9C46A"},
            # Staging
            {"id": "stg_trips",      "label": "staging.stg_trips",     "layer": "Staging", "color": "#457B9D"},
            {"id": "stg_customers",  "label": "stg_customers",         "layer": "Staging", "color": "#457B9D"},
            {"id": "stg_vehicles",   "label": "stg_vehicles",          "layer": "Staging", "color": "#457B9D"},
            {"id": "stg_drivers",    "label": "stg_drivers",           "layer": "Staging", "color": "#457B9D"},
            {"id": "stg_fleets",     "label": "stg_fleets",            "layer": "Staging", "color": "#457B9D"},
            {"id": "stg_invoices",   "label": "stg_invoices",          "layer": "Staging", "color": "#457B9D"},
            {"id": "stg_fuel",       "label": "stg_fuel_logs",         "layer": "Staging", "color": "#457B9D"},
            {"id": "stg_maint",      "label": "stg_maintenance",       "layer": "Staging", "color": "#457B9D"},
            {"id": "stg_telem",      "label": "stg_telematics",        "layer": "Staging", "color": "#457B9D"},
            # Dimensions
            {"id": "dim_date",       "label": "dim_date",              "layer": "DWH Dim", "color": "#2A9D8F"},
            {"id": "dim_customer",   "label": "dim_customer",          "layer": "DWH Dim", "color": "#2A9D8F"},
            {"id": "dim_vehicle",    "label": "dim_vehicle",           "layer": "DWH Dim", "color": "#2A9D8F"},
            {"id": "dim_driver",     "label": "dim_driver",            "layer": "DWH Dim", "color": "#2A9D8F"},
            {"id": "dim_fleet",      "label": "dim_fleet",             "layer": "DWH Dim", "color": "#2A9D8F"},
            # Facts
            {"id": "fact_trips",     "label": "fact_trips",            "layer": "DWH Fact","color": "#E76F51"},
            {"id": "fact_invoices",  "label": "fact_invoices",         "layer": "DWH Fact","color": "#E76F51"},
            {"id": "fact_fuel",      "label": "fact_fuel_logs",        "layer": "DWH Fact","color": "#E76F51"},
            {"id": "fact_maint",     "label": "fact_maintenance",      "layer": "DWH Fact","color": "#E76F51"},
            {"id": "fact_telem",     "label": "fact_telematics",       "layer": "DWH Fact","color": "#E76F51"},
            # Marts
            {"id": "mart_revenue",   "label": "mart.daily_revenue",    "layer": "Mart",    "color": "#6A4C93"},
            {"id": "mart_pnl",       "label": "mart.monthly_pnl",      "layer": "Mart",    "color": "#6A4C93"},
            {"id": "mart_ltv",       "label": "mart.customer_ltv",     "layer": "Mart",    "color": "#6A4C93"},
            {"id": "mart_driver",    "label": "mart.driver_scorecard", "layer": "Mart",    "color": "#6A4C93"},
        ],
        "edges": [
            # CSV -> Raw
            ("csv_trips","raw_trips"),("csv_customers","raw_customers"),
            ("csv_vehicles","raw_vehicles"),("csv_drivers","raw_drivers"),
            ("csv_fleets","raw_fleets"),("csv_invoices","raw_invoices"),
            ("csv_fuel","raw_fuel"),("csv_maint","raw_maint"),("csv_telem","raw_telem"),
            # Raw -> Staging
            ("raw_trips","stg_trips"),("raw_customers","stg_customers"),
            ("raw_vehicles","stg_vehicles"),("raw_drivers","stg_drivers"),
            ("raw_fleets","stg_fleets"),("raw_invoices","stg_invoices"),
            ("raw_fuel","stg_fuel"),("raw_maint","stg_maint"),("raw_telem","stg_telem"),
            # Staging -> Dims
            ("stg_customers","dim_customer"),("stg_vehicles","dim_vehicle"),
            ("stg_drivers","dim_driver"),("stg_fleets","dim_fleet"),
            # Staging -> Facts
            ("stg_trips","fact_trips"),("stg_invoices","fact_invoices"),
            ("stg_fuel","fact_fuel"),("stg_maint","fact_maint"),("stg_telem","fact_telem"),
            # Dims -> Facts
            ("dim_customer","fact_trips"),("dim_vehicle","fact_trips"),
            ("dim_driver","fact_trips"),("dim_fleet","fact_trips"),("dim_date","fact_trips"),
            ("dim_customer","fact_invoices"),("dim_fleet","fact_invoices"),
            # Facts -> Marts
            ("fact_trips","mart_revenue"),("fact_trips","mart_pnl"),
            ("fact_trips","mart_ltv"),("fact_telem","mart_driver"),
            ("fact_fuel","mart_pnl"),("fact_maint","mart_pnl"),
        ],
    }

    # Interactive lineage — filter by table
    _lin_sel = st.selectbox(
        "Trace lineage for:",
        ["(show full pipeline)"] + [n["label"] for n in _LINEAGE["nodes"]],
        key="lin_sel",
    )

    # Build Plotly Sankey diagram
    _node_ids  = [n["id"]    for n in _LINEAGE["nodes"]]
    _node_lbls = [n["label"] for n in _LINEAGE["nodes"]]
    _node_clrs = [n["color"] for n in _LINEAGE["nodes"]]

    _id_idx = {nid: i for i, nid in enumerate(_node_ids)}

    # Filter edges if a specific table selected
    _edges = _LINEAGE["edges"]
    if _lin_sel != "(show full pipeline)":
        _sel_id = next((n["id"] for n in _LINEAGE["nodes"] if n["label"] == _lin_sel), None)
        if _sel_id:
            # Show upstream (ancestors) and downstream (descendants) of selected node
            _ancestors, _descendants = set(), set()
            _q = [_sel_id]
            while _q:
                _cur = _q.pop()
                for _src, _dst in _edges:
                    if _dst == _cur and _src not in _ancestors:
                        _ancestors.add(_src); _q.append(_src)
            _q = [_sel_id]
            while _q:
                _cur = _q.pop()
                for _src, _dst in _edges:
                    if _src == _cur and _dst not in _descendants:
                        _descendants.add(_dst); _q.append(_dst)
            _related = _ancestors | {_sel_id} | _descendants
            _edges = [(_s,_d) for _s,_d in _edges if _s in _related and _d in _related]

    _src_idx = [_id_idx[s] for s,d in _edges if s in _id_idx and d in _id_idx]
    _dst_idx = [_id_idx[d] for s,d in _edges if s in _id_idx and d in _id_idx]

    fig_lin = go.Figure(go.Sankey(
        node=dict(
            pad=15, thickness=18, line=dict(color="#30363d", width=0.5),
            label=_node_lbls, color=_node_clrs,
        ),
        link=dict(
            source=_src_idx, target=_dst_idx,
            value=[1]*len(_src_idx),
            color=["rgba(255,255,255,0.07)"]*len(_src_idx),
        ),
    ))
    fig_lin.update_layout(
        height=550, paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#c8dff0", size=11),
        margin=dict(l=0,r=0,t=20,b=0),
    )
    st.plotly_chart(fig_lin, use_container_width=True)

    # Layer legend
    st.markdown(_h3("📋 Pipeline Layer Reference", STEEL), unsafe_allow_html=True)
    _layers = [
        ("CSV Landing Zone", "data/csv/oltp/*.csv — raw source files, append-only", "#E63946"),
        ("Raw Views",        "raw.v_* — DuckDB views pointing at CSVs, zero-copy", "#E9C46A"),
        ("Staging Tables",   "staging.stg_* — cleaned, typed, deduplicated, DQ-flagged", "#457B9D"),
        ("DWH Dimensions",   "dwh.dim_* — conformed dimensions (SCD2 for customer)", "#2A9D8F"),
        ("DWH Facts",        "dwh.fact_* — grain-level fact tables with FK refs to dims", "#E76F51"),
        ("Data Marts",       "mart.* — pre-aggregated views for BI tools and dashboards", "#6A4C93"),
    ]
    _ll1, _ll2 = st.columns(2)
    for i, (lname, ldesc, lclr) in enumerate(_layers):
        col = _ll1 if i % 2 == 0 else _ll2
        with col:
            st.markdown(_card(
                f'<div style="display:flex;align-items:center;gap:10px;">'
                f'<div style="width:12px;height:12px;border-radius:3px;background:{lclr};flex-shrink:0;"></div>'
                f'<div><b style="color:{lclr};font-size:.82rem;">{lname}</b><br>'
                f'<span style="font-size:.74rem;color:{M};">{ldesc}</span></div></div>',
                left=lclr, pad="10px 12px",
            ), unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════
# TAB 13 — SCHEMA BROWSER / ERD
# ═══════════════════════════════════════════════════════════════════════
with T[13]:
    st.markdown(_h2("Schema Browser & ERD", "🔍"), unsafe_allow_html=True)

    _SCHEMA = {
        "trips": {
            "pk": "trip_id", "fks": ["customer_id->customers","vehicle_id->vehicles","driver_id->drivers","fleet_id->fleets"],
            "cols": [
                ("trip_id","VARCHAR","PK — unique trip identifier"),
                ("booking_id","VARCHAR","FK — links to booking"),
                ("fleet_id","VARCHAR","FK -> fleets"),
                ("vehicle_id","VARCHAR","FK -> vehicles"),
                ("driver_id","VARCHAR","FK -> drivers (nullable if self-drive)"),
                ("customer_id","VARCHAR","FK -> customers"),
                ("booking_type","VARCHAR","City Ride / Airport Transfer / Intercity / Wedding"),
                ("pickup_datetime","TIMESTAMP","When the trip started"),
                ("dropoff_datetime","TIMESTAMP","When the trip ended"),
                ("duration_days","DOUBLE","Actual trip duration in days"),
                ("pickup_city","VARCHAR","Origin city"),
                ("dropoff_city","VARCHAR","Destination city (same = intracity)"),
                ("distance_km","DOUBLE","GPS-measured trip distance"),
                ("trip_fare_pkr","DOUBLE","Base fare charged (PKR)"),
                ("driver_allowance_pkr","DOUBLE","Extra allowance for driver (PKR)"),
                ("with_driver","BOOLEAN","True if chauffeur-driven"),
                ("self_drive","BOOLEAN","True if customer drove"),
                ("status","VARCHAR","Completed / Cancelled / In Progress"),
            ],
            "grain": "1 row = 1 trip",
            "rows": "~18,000",
        },
        "customers": {
            "pk": "customer_id", "fks": [],
            "cols": [
                ("customer_id","VARCHAR","PK — e.g. CU00001"),
                ("full_name","VARCHAR","Customer full name"),
                ("gender","VARCHAR","M / F"),
                ("dob","DATE","Date of birth"),
                ("cnic","VARCHAR","Pakistani national ID (13 digits)"),
                ("nationality","VARCHAR","Usually Pakistani"),
                ("phone","VARCHAR","Mobile number"),
                ("email","VARCHAR","Email address"),
                ("city","VARCHAR","Home city"),
                ("customer_type","VARCHAR","Tourist / Business / Local / Corporate"),
                ("license_no","VARCHAR","Driving licence (nullable)"),
                ("has_own_license","BOOLEAN","Whether customer holds a valid licence"),
                ("loyalty_points","INTEGER","Accumulated loyalty points"),
                ("total_bookings","INTEGER","Lifetime booking count"),
                ("registration_date","DATE","When customer registered"),
            ],
            "grain": "1 row = 1 customer",
            "rows": "~2,000",
        },
        "vehicles": {
            "pk": "vehicle_id", "fks": ["fleet_id->fleets","vehicle_type_id->vehicle_types"],
            "cols": [
                ("vehicle_id","VARCHAR","PK — e.g. VH00001"),
                ("fleet_id","VARCHAR","FK -> fleets"),
                ("vehicle_type_id","VARCHAR","FK -> vehicle_types"),
                ("make","VARCHAR","Manufacturer e.g. Toyota"),
                ("model","VARCHAR","Model e.g. Corolla GLI"),
                ("year","INTEGER","Manufacturing year"),
                ("registration_no","VARCHAR","Government registration plate"),
                ("color","VARCHAR","Vehicle colour"),
                ("fuel_type","VARCHAR","Petrol / Diesel / Hybrid"),
                ("transmission","VARCHAR","Manual / Automatic"),
                ("seats","INTEGER","Seating capacity"),
                ("odometer_km","INTEGER","Current odometer reading"),
                ("daily_rate_pkr","DOUBLE","Daily rental rate in PKR"),
                ("insurance_expiry","DATE","Insurance validity date"),
                ("status","VARCHAR","Available / On Trip / Maintenance"),
                ("condition_rating","VARCHAR","Excellent / Good / Fair / Poor"),
                ("gps_enabled","BOOLEAN","Whether vehicle has GPS tracker"),
            ],
            "grain": "1 row = 1 vehicle",
            "rows": "~120",
        },
        "invoices": {
            "pk": "invoice_id", "fks": ["trip_id->trips","customer_id->customers","fleet_id->fleets"],
            "cols": [
                ("invoice_id","VARCHAR","PK — e.g. INV000001"),
                ("trip_id","VARCHAR","FK -> trips"),
                ("customer_id","VARCHAR","FK -> customers"),
                ("fleet_id","VARCHAR","FK -> fleets"),
                ("invoice_date","DATE","Date invoice was issued"),
                ("due_date","DATE","Payment due date"),
                ("base_fare_pkr","DOUBLE","Core rental charge"),
                ("total_surcharge_pkr","DOUBLE","Airport pickup, night, extra km etc."),
                ("discount_pkr","DOUBLE","Discount applied"),
                ("driver_allowance_pkr","DOUBLE","Chauffeur fee"),
                ("tax_pkr","DOUBLE","Tax amount (usually 0)"),
                ("total_amount_pkr","DOUBLE","Grand total"),
                ("paid_amount_pkr","DOUBLE","Amount actually received"),
                ("outstanding_pkr","DOUBLE","Still owed (total - paid)"),
                ("payment_method","VARCHAR","Cash / Bank Transfer / Card / JazzCash"),
                ("payment_status","VARCHAR","Paid / Partial / Unpaid"),
            ],
            "grain": "1 row = 1 invoice (= 1 trip)",
            "rows": "~15,000",
        },
        "drivers": {
            "pk": "driver_id", "fks": ["fleet_id->fleets"],
            "cols": [
                ("driver_id","VARCHAR","PK — e.g. DR0001"),
                ("fleet_id","VARCHAR","FK -> fleets"),
                ("full_name","VARCHAR","Driver full name"),
                ("license_no","VARCHAR","Driving licence number"),
                ("license_expiry","DATE","Licence expiry date"),
                ("hire_date","DATE","Date hired"),
                ("experience_years","INTEGER","Years of professional driving experience"),
                ("base_salary_pkr","DOUBLE","Monthly base salary"),
                ("behavior_profile","VARCHAR","good / aggressive / distracted"),
                ("harsh_brake_rate","DOUBLE","Rate of harsh braking events (0-1)"),
                ("harsh_accel_rate","DOUBLE","Rate of harsh acceleration (0-1)"),
                ("idle_time_pct","DOUBLE","Proportion of time idling (0-1)"),
                ("speeding_pct","DOUBLE","Proportion of distance spent speeding (0-1)"),
                ("ratings_avg","DOUBLE","Average customer rating (0-5)"),
                ("active","BOOLEAN","Currently employed and driving"),
            ],
            "grain": "1 row = 1 driver",
            "rows": "~60",
        },
        "fleets": {
            "pk": "fleet_id", "fks": [],
            "cols": [
                ("fleet_id","VARCHAR","PK — e.g. FL001"),
                ("fleet_name","VARCHAR","Company name e.g. Hassan Rent a Car"),
                ("city","VARCHAR","Primary operating city"),
                ("website","VARCHAR","Company website"),
                ("secp_registered","BOOLEAN","SECP company registration"),
                ("ntn_registered","BOOLEAN","Tax registration (NTN)"),
                ("established_year","INTEGER","Year company was founded"),
                ("focus_segment","VARCHAR","economy / luxury / chauffeur / corporate"),
                ("total_vehicles","INTEGER","Current fleet size"),
                ("active","BOOLEAN","Currently operating"),
            ],
            "grain": "1 row = 1 fleet company",
            "rows": "~5",
        },
        "telematics": {
            "pk": "telem_id", "fks": ["trip_id->trips","driver_id->drivers","vehicle_id->vehicles"],
            "cols": [
                ("telem_id","VARCHAR","PK"),
                ("trip_id","VARCHAR","FK -> trips"),
                ("driver_id","VARCHAR","FK -> drivers"),
                ("vehicle_id","VARCHAR","FK -> vehicles"),
                ("trip_date","DATE","Date of trip"),
                ("distance_km","DOUBLE","GPS-tracked distance"),
                ("duration_hours","DOUBLE","Trip duration in hours"),
                ("avg_speed_kmh","DOUBLE","Average speed"),
                ("max_speed_kmh","INTEGER","Maximum speed recorded"),
                ("harsh_brake_events","INTEGER","Count of hard braking events"),
                ("harsh_accel_events","INTEGER","Count of hard acceleration events"),
                ("idle_time_minutes","INTEGER","Minutes engine on but stationary"),
                ("speeding_km","DOUBLE","Distance driven above speed limit"),
                ("safety_score","DOUBLE","Composite score 0-100 (higher = safer)"),
                ("accident_occurred","BOOLEAN","Whether accident happened"),
                ("customer_rating","DOUBLE","Customer rating for this trip (0-5)"),
                ("complaint_filed","BOOLEAN","Whether customer filed a complaint"),
            ],
            "grain": "1 row = 1 trip telematics record",
            "rows": "~15,000",
        },
        "fuel_logs": {
            "pk": "fuel_id", "fks": ["trip_id->trips","vehicle_id->vehicles","fleet_id->fleets"],
            "cols": [
                ("fuel_id","VARCHAR","PK"),
                ("trip_id","VARCHAR","FK -> trips"),
                ("vehicle_id","VARCHAR","FK -> vehicles"),
                ("fleet_id","VARCHAR","FK -> fleets"),
                ("driver_id","VARCHAR","FK -> drivers (nullable)"),
                ("fill_date","DATE","Date of fuel fill"),
                ("fuel_type","VARCHAR","Petrol / Diesel / CNG"),
                ("litres_filled","DOUBLE","Volume filled in litres"),
                ("price_per_litre_pkr","DOUBLE","Fuel price at time of fill"),
                ("fuel_cost_pkr","DOUBLE","Total cost of fill"),
                ("km_driven","DOUBLE","KM driven on this tank"),
                ("fuel_efficiency_kmpl","DOUBLE","Calculated km per litre"),
                ("odometer_at_fill","INTEGER","Odometer reading at fill"),
                ("fill_station","VARCHAR","Petrol station name and city"),
                ("paid_by","VARCHAR","Petty Cash / Card / Driver"),
            ],
            "grain": "1 row = 1 fuelling event",
            "rows": "~13,500",
        },
        "maintenance": {
            "pk": "maint_id", "fks": ["vehicle_id->vehicles","fleet_id->fleets"],
            "cols": [
                ("maint_id","VARCHAR","PK"),
                ("vehicle_id","VARCHAR","FK -> vehicles"),
                ("fleet_id","VARCHAR","FK -> fleets"),
                ("maintenance_type","VARCHAR","Oil Change / Tyre / AC Service etc."),
                ("maintenance_date","DATE","When service was performed"),
                ("odometer_km","INTEGER","Odometer at time of service"),
                ("workshop","VARCHAR","Workshop name"),
                ("parts_cost_pkr","DOUBLE","Cost of parts"),
                ("labour_cost_pkr","DOUBLE","Labour charges"),
                ("total_cost_pkr","DOUBLE","Total maintenance bill"),
                ("status","VARCHAR","Completed / In Progress"),
                ("next_due_km","INTEGER","Next service due at this odometer"),
                ("next_due_date","DATE","Next service due date"),
            ],
            "grain": "1 row = 1 maintenance event",
            "rows": "~800",
        },
    }

    _sb_col1, _sb_col2 = st.columns([1, 2])

    with _sb_col1:
        st.markdown(_h3("📋 Tables", STEEL), unsafe_allow_html=True)
        _sel_tbl = st.radio(
            "Select table:",
            list(_SCHEMA.keys()),
            key="schema_sel",
            label_visibility="collapsed",
        )

    with _sb_col2:
        if _sel_tbl and _sel_tbl in _SCHEMA:
            _tbl_info = _SCHEMA[_sel_tbl]
            st.markdown(_h3(f"📊 {_sel_tbl}", BRAND), unsafe_allow_html=True)
            _m1, _m2, _m3 = st.columns(3)
            _m1.metric("Rows", _tbl_info["rows"])
            _m2.metric("Columns", str(len(_tbl_info["cols"])))
            _m3.metric("Grain", _tbl_info["grain"])

            # FK references
            if _tbl_info["fks"]:
                st.markdown(
                    _card(
                        f'<b style="font-size:.78rem;color:{AMBER};">Foreign Keys:</b> '
                        + " &nbsp;|&nbsp; ".join(
                            f'<code style="color:{TEAL};">{fk}</code>'
                            for fk in _tbl_info["fks"]
                        ),
                        left=AMBER, pad="8px 14px",
                    ), unsafe_allow_html=True
                )

            # Columns table
            _col_df = pd.DataFrame(_tbl_info["cols"], columns=["Column","Type","Description"])
            _col_df["PK/FK"] = _col_df["Column"].apply(
                lambda c: "🔑 PK" if c == _tbl_info["pk"]
                else ("🔗 FK" if any(c in fk.split("->")[0] for fk in _tbl_info["fks"])
                      else "")
            )
            st.dataframe(_col_df[["PK/FK","Column","Type","Description"]],
                         use_container_width=True, height=350, hide_index=True)

            # Live sample data
            if st.button(f"👁 Preview {_sel_tbl} (10 rows)", key="preview_tbl"):
                _prev = _run(f"SELECT * FROM {_sel_tbl} LIMIT 10", conn)
                if _prev is not None and not _prev.empty:
                    st.dataframe(_prev, use_container_width=True, height=220, hide_index=True)

    # ERD diagram
    st.markdown(_h3("📐 Entity Relationship Diagram", BRAND), unsafe_allow_html=True)
    _erd_html = """
<div style="background:#0d1117;border:1px solid #30363d;border-radius:8px;padding:20px;overflow-x:auto;">
<svg viewBox="0 0 1000 500" style="width:100%;font-family:monospace;font-size:11px;">
  <!-- trips (center) -->
  <rect x="400" y="190" width="140" height="120" rx="6" fill="#1c0f0f" stroke="#E63946" stroke-width="2"/>
  <text x="470" y="210" fill="#E63946" text-anchor="middle" font-weight="bold">trips</text>
  <text x="470" y="228" fill="#8b949e" text-anchor="middle">PK: trip_id</text>
  <text x="470" y="244" fill="#c8dff0" text-anchor="middle">FK: customer_id</text>
  <text x="470" y="260" fill="#c8dff0" text-anchor="middle">FK: vehicle_id</text>
  <text x="470" y="276" fill="#c8dff0" text-anchor="middle">FK: driver_id</text>
  <text x="470" y="292" fill="#c8dff0" text-anchor="middle">FK: fleet_id</text>
  <!-- customers -->
  <rect x="50" y="50" width="130" height="80" rx="6" fill="#0d1a0f" stroke="#2A9D8F" stroke-width="1.5"/>
  <text x="115" y="70" fill="#2A9D8F" text-anchor="middle" font-weight="bold">customers</text>
  <text x="115" y="88" fill="#8b949e" text-anchor="middle">PK: customer_id</text>
  <text x="115" y="104" fill="#c8dff0" text-anchor="middle">full_name, city</text>
  <!-- vehicles -->
  <rect x="50" y="190" width="130" height="80" rx="6" fill="#0d1a0f" stroke="#2A9D8F" stroke-width="1.5"/>
  <text x="115" y="210" fill="#2A9D8F" text-anchor="middle" font-weight="bold">vehicles</text>
  <text x="115" y="228" fill="#8b949e" text-anchor="middle">PK: vehicle_id</text>
  <text x="115" y="244" fill="#c8dff0" text-anchor="middle">make, model, rate</text>
  <!-- drivers -->
  <rect x="50" y="330" width="130" height="80" rx="6" fill="#0d1a0f" stroke="#2A9D8F" stroke-width="1.5"/>
  <text x="115" y="350" fill="#2A9D8F" text-anchor="middle" font-weight="bold">drivers</text>
  <text x="115" y="368" fill="#8b949e" text-anchor="middle">PK: driver_id</text>
  <text x="115" y="384" fill="#c8dff0" text-anchor="middle">name, behavior</text>
  <!-- fleets -->
  <rect x="220" y="50" width="130" height="80" rx="6" fill="#0d1a0f" stroke="#2A9D8F" stroke-width="1.5"/>
  <text x="285" y="70" fill="#2A9D8F" text-anchor="middle" font-weight="bold">fleets</text>
  <text x="285" y="88" fill="#8b949e" text-anchor="middle">PK: fleet_id</text>
  <text x="285" y="104" fill="#c8dff0" text-anchor="middle">name, city</text>
  <!-- invoices -->
  <rect x="620" y="50" width="130" height="80" rx="6" fill="#1a0f0f" stroke="#E76F51" stroke-width="1.5"/>
  <text x="685" y="70" fill="#E76F51" text-anchor="middle" font-weight="bold">invoices</text>
  <text x="685" y="88" fill="#8b949e" text-anchor="middle">PK: invoice_id</text>
  <text x="685" y="104" fill="#c8dff0" text-anchor="middle">total, paid, status</text>
  <!-- telematics -->
  <rect x="620" y="190" width="130" height="80" rx="6" fill="#1a0f0f" stroke="#E76F51" stroke-width="1.5"/>
  <text x="685" y="210" fill="#E76F51" text-anchor="middle" font-weight="bold">telematics</text>
  <text x="685" y="228" fill="#8b949e" text-anchor="middle">PK: telem_id</text>
  <text x="685" y="244" fill="#c8dff0" text-anchor="middle">safety, rating</text>
  <!-- fuel_logs -->
  <rect x="620" y="330" width="130" height="80" rx="6" fill="#1a0f0f" stroke="#E76F51" stroke-width="1.5"/>
  <text x="685" y="350" fill="#E76F51" text-anchor="middle" font-weight="bold">fuel_logs</text>
  <text x="685" y="368" fill="#8b949e" text-anchor="middle">PK: fuel_id</text>
  <text x="685" y="384" fill="#c8dff0" text-anchor="middle">litres, cost, eff</text>
  <!-- maintenance -->
  <rect x="820" y="190" width="130" height="80" rx="6" fill="#1a0f0f" stroke="#E76F51" stroke-width="1.5"/>
  <text x="885" y="210" fill="#E76F51" text-anchor="middle" font-weight="bold">maintenance</text>
  <text x="885" y="228" fill="#8b949e" text-anchor="middle">PK: maint_id</text>
  <text x="885" y="244" fill="#c8dff0" text-anchor="middle">cost, type, date</text>
  <!-- Relationship lines -->
  <line x1="180" y1="90"  x2="400" y2="230" stroke="#E9C46A" stroke-width="1" stroke-dasharray="4,3"/>
  <line x1="180" y1="230" x2="400" y2="250" stroke="#E9C46A" stroke-width="1" stroke-dasharray="4,3"/>
  <line x1="180" y1="370" x2="400" y2="270" stroke="#E9C46A" stroke-width="1" stroke-dasharray="4,3"/>
  <line x1="350" y1="90"  x2="420" y2="190" stroke="#E9C46A" stroke-width="1" stroke-dasharray="4,3"/>
  <line x1="540" y1="230" x2="620" y2="90"  stroke="#E9C46A" stroke-width="1" stroke-dasharray="4,3"/>
  <line x1="540" y1="250" x2="620" y2="230" stroke="#E9C46A" stroke-width="1" stroke-dasharray="4,3"/>
  <line x1="540" y1="270" x2="620" y2="370" stroke="#E9C46A" stroke-width="1" stroke-dasharray="4,3"/>
  <line x1="750" y1="230" x2="820" y2="230" stroke="#E9C46A" stroke-width="1" stroke-dasharray="4,3"/>
  <!-- Cardinality labels -->
  <text x="390" y="175" fill="#E9C46A" font-size="9">1:N</text>
  <text x="390" y="255" fill="#E9C46A" font-size="9">1:N</text>
  <text x="390" y="285" fill="#E9C46A" font-size="9">1:N</text>
</svg>
</div>"""
    st.markdown(_erd_html, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════
# TAB 14 — EXERCISES
# ═══════════════════════════════════════════════════════════════════════
with T[14]:
    import hashlib as _hl

    st.markdown(_h2("SQL & Python Exercises", "🏋️"), unsafe_allow_html=True)
    st.markdown(_card(
        f'Practice data engineering and analytics skills on real Rent-A-Car data.<br>'
        f'Write your answer in the editor, run it, then click <b style="color:{TEAL};">Check Answer</b>.',
        left=TEAL,
    ), unsafe_allow_html=True)

    _EXERCISES = [
        {
            "id": "ex01", "level": "Beginner", "topic": "Basic SELECT",
            "title": "Count completed trips",
            "question": "Write a query that returns the total number of trips with status = 'Completed'.",
            "hint": "Use COUNT(*) with a WHERE clause.",
            "answer_check": lambda df: (
                df is not None and len(df) == 1
                and df.iloc[0, 0] > 0
                and df.shape[1] == 1
            ),
            "answer_sql": "SELECT COUNT(*) AS completed_trips FROM trips WHERE status = 'Completed'",
            "expected": "Single row with a count > 0",
        },
        {
            "id": "ex02", "level": "Beginner", "topic": "GROUP BY",
            "title": "Revenue by booking type",
            "question": "Write a query showing total revenue (trip_fare_pkr) per booking_type for completed trips, ordered by revenue descending.",
            "hint": "Use GROUP BY booking_type, SUM(trip_fare_pkr), WHERE status = 'Completed'.",
            "answer_check": lambda df: (
                df is not None and len(df) > 1
                and any("booking_type" in c.lower() for c in df.columns)
                and df.shape[1] >= 2
            ),
            "answer_sql": """SELECT booking_type,
    COUNT(*) AS trips,
    ROUND(SUM(trip_fare_pkr), 0) AS revenue_pkr
FROM trips
WHERE status = 'Completed'
GROUP BY booking_type
ORDER BY revenue_pkr DESC""",
            "expected": "Multiple rows, one per booking type, with revenue column",
        },
        {
            "id": "ex03", "level": "Beginner", "topic": "JOIN",
            "title": "Customer names on trips",
            "question": "Write a query joining trips to customers to show trip_id, customer full_name, and trip_fare_pkr for completed trips. Order by fare descending, limit 10.",
            "hint": "INNER JOIN customers ON trips.customer_id = customers.customer_id",
            "answer_check": lambda df: (
                df is not None and len(df) == 10
                and any("name" in c.lower() for c in df.columns)
            ),
            "answer_sql": """SELECT t.trip_id, c.full_name, t.trip_fare_pkr
FROM trips t
JOIN customers c ON t.customer_id = c.customer_id
WHERE t.status = 'Completed'
ORDER BY t.trip_fare_pkr DESC
LIMIT 10""",
            "expected": "10 rows with customer name and fare",
        },
        {
            "id": "ex04", "level": "Intermediate", "topic": "LEFT JOIN Anti-join",
            "title": "Vehicles never used",
            "question": "Find vehicle_ids that have never appeared in any completed trip. Use a LEFT JOIN anti-join pattern.",
            "hint": "LEFT JOIN trips ON vehicle_id, then WHERE trips.trip_id IS NULL",
            "answer_check": lambda df: (
                df is not None
                and any("vehicle_id" in c.lower() for c in df.columns)
            ),
            "answer_sql": """SELECT v.vehicle_id, v.make, v.model
FROM vehicles v
LEFT JOIN trips t ON v.vehicle_id = t.vehicle_id AND t.status = 'Completed'
WHERE t.trip_id IS NULL""",
            "expected": "Rows containing vehicle_id (may be empty if all vehicles have been used)",
        },
        {
            "id": "ex05", "level": "Intermediate", "topic": "Window Function",
            "title": "Month-over-month revenue change",
            "question": "Using a CTE and LAG(), calculate monthly revenue and the change vs the previous month.",
            "hint": "DATE_TRUNC('month', pickup_datetime::DATE), then LAG(revenue) OVER (ORDER BY month)",
            "answer_check": lambda df: (
                df is not None and len(df) > 2
                and df.shape[1] >= 3
            ),
            "answer_sql": """WITH monthly AS (
    SELECT DATE_TRUNC('month', pickup_datetime::DATE) AS month,
           SUM(trip_fare_pkr) AS revenue
    FROM trips WHERE status = 'Completed'
    GROUP BY 1
)
SELECT month,
    ROUND(revenue, 0) AS revenue_pkr,
    ROUND(revenue - LAG(revenue) OVER (ORDER BY month), 0) AS mom_change
FROM monthly
ORDER BY month""",
            "expected": "Monthly rows with revenue and change column",
        },
        {
            "id": "ex06", "level": "Intermediate", "topic": "HAVING",
            "title": "High-value customers",
            "question": "Find customers who have completed more than 3 trips AND have total spend over PKR 50,000. Show customer_id, trip count, and total spend.",
            "hint": "GROUP BY customer_id, then HAVING COUNT(*) > 3 AND SUM(trip_fare_pkr) > 50000",
            "answer_check": lambda df: (
                df is not None
                and df.shape[1] >= 3
                and len(df) >= 0
            ),
            "answer_sql": """SELECT customer_id,
    COUNT(*) AS trips,
    ROUND(SUM(trip_fare_pkr), 0) AS total_spend
FROM trips
WHERE status = 'Completed'
GROUP BY customer_id
HAVING COUNT(*) > 3 AND SUM(trip_fare_pkr) > 50000
ORDER BY total_spend DESC""",
            "expected": "Rows with customer_id, trip count > 3, spend > 50000",
        },
        {
            "id": "ex07", "level": "Advanced", "topic": "CTE + Window",
            "title": "Top vehicle per fleet",
            "question": "For each fleet, find the single vehicle that has generated the most revenue. Use a CTE and QUALIFY (or ROW_NUMBER).",
            "hint": "CTE: SUM revenue by fleet+vehicle. Then ROW_NUMBER() OVER (PARTITION BY fleet_id ORDER BY revenue DESC). QUALIFY rn = 1.",
            "answer_check": lambda df: (
                df is not None
                and any("fleet" in c.lower() for c in df.columns)
                and len(df) <= 10
            ),
            "answer_sql": """WITH rev AS (
    SELECT fleet_id, vehicle_id,
           ROUND(SUM(trip_fare_pkr), 0) AS revenue
    FROM trips WHERE status = 'Completed'
    GROUP BY fleet_id, vehicle_id
)
SELECT fleet_id, vehicle_id, revenue,
       ROW_NUMBER() OVER (PARTITION BY fleet_id ORDER BY revenue DESC) AS rn
FROM rev
QUALIFY rn = 1
ORDER BY revenue DESC""",
            "expected": "One row per fleet showing the highest-revenue vehicle",
        },
        {
            "id": "ex08", "level": "Advanced", "topic": "Data Quality",
            "title": "Find timeline violations",
            "question": "Write a DQ check query that finds trips where dropoff_datetime is BEFORE pickup_datetime. Show trip_id and the calculated duration in hours.",
            "hint": "DATE_DIFF('hour', pickup_datetime, dropoff_datetime) < 0",
            "answer_check": lambda df: (
                df is not None
                and df.shape[1] >= 2
            ),
            "answer_sql": """SELECT trip_id,
    pickup_datetime,
    dropoff_datetime,
    DATE_DIFF('hour', pickup_datetime, dropoff_datetime) AS dur_hours
FROM trips
WHERE CAST(dropoff_datetime AS TIMESTAMP) < CAST(pickup_datetime AS TIMESTAMP)
LIMIT 20""",
            "expected": "Rows where duration is negative (bad data)",
        },
        {
            "id": "ex09", "level": "Advanced", "topic": "ROLLUP",
            "title": "Revenue subtotals with ROLLUP",
            "question": "Write a query using GROUP BY ROLLUP to show revenue by fleet AND booking_type, with subtotals for each fleet and a grand total.",
            "hint": "GROUP BY ROLLUP(fleet_id, booking_type)",
            "answer_check": lambda df: (
                df is not None and len(df) > 5
                and df.shape[1] >= 3
                and df.isnull().any().any()  # ROLLUP produces NULLs
            ),
            "answer_sql": """SELECT
    COALESCE(fleet_id, 'ALL FLEETS') AS fleet,
    COALESCE(booking_type, 'ALL TYPES') AS booking_type,
    ROUND(SUM(trip_fare_pkr), 0) AS revenue_pkr,
    COUNT(*) AS trips
FROM trips
WHERE status = 'Completed'
GROUP BY ROLLUP(fleet_id, booking_type)
ORDER BY fleet NULLS LAST, booking_type NULLS LAST""",
            "expected": "Rows with NULL values (subtotals) from ROLLUP",
        },
        {
            "id": "ex10", "level": "Python", "topic": "pandas",
            "title": "Driver safety ranking (Python)",
            "question": "Using Python + pandas, calculate each driver's average safety_score from telematics, rank them, and print the top 5 safest drivers.",
            "hint": "Use dfs['telematics'].groupby('driver_id')['safety_score'].mean(), then sort_values(ascending=False)",
            "answer_check": lambda df: df is not None and len(df) <= 5,
            "answer_sql": None,
            "answer_py": """telem = dfs["telematics"].copy()
safety = (telem.groupby("driver_id")["safety_score"]
          .mean().round(1).reset_index()
          .sort_values("safety_score", ascending=False))

drivers = dfs["drivers"][["driver_id","full_name","behavior_profile"]]
result = safety.merge(drivers, on="driver_id").head(5)
print("Top 5 Safest Drivers:")
print(result[["full_name","safety_score","behavior_profile"]].to_string(index=False))
""",
            "expected": "Top 5 drivers by average safety score",
        },
    ]

    # Exercise navigation
    if "ex_idx" not in st.session_state:
        st.session_state.ex_idx = 0
    if "ex_answers" not in st.session_state:
        st.session_state.ex_answers = {}
    if "ex_results" not in st.session_state:
        st.session_state.ex_results = {}

    _ex_levels = ["All"] + sorted(set(e["level"] for e in _EXERCISES))
    _ex_topics = ["All"] + sorted(set(e["topic"] for e in _EXERCISES))

    _ef1, _ef2 = st.columns(2)
    with _ef1:
        _lvl_f = st.selectbox("Level:", _ex_levels, key="ex_level_filter")
    with _ef2:
        _top_f = st.selectbox("Topic:", _ex_topics, key="ex_topic_filter")

    _filtered_ex = [
        e for e in _EXERCISES
        if (_lvl_f == "All" or e["level"] == _lvl_f)
        and (_top_f == "All" or e["topic"] == _top_f)
    ]

    if not _filtered_ex:
        st.info("No exercises match filter.")
    else:
        # Exercise list
        _ex_names = [f"{e['level']} — {e['title']}" for e in _filtered_ex]
        _ex_sel_idx = st.selectbox("Exercise:", range(len(_ex_names)),
                                   format_func=lambda i: _ex_names[i], key="ex_sel")
        _ex = _filtered_ex[_ex_sel_idx]
        _solved = st.session_state.ex_results.get(_ex["id"], {}).get("passed", False)

        # Exercise card
        _lvl_colors = {"Beginner": TEAL, "Intermediate": AMBER, "Advanced": BRAND, "Python": PUR}
        _lvl_clr = _lvl_colors.get(_ex["level"], STEEL)
        st.markdown(_card(
            f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">'
            f'<span style="font-size:.88rem;font-weight:800;color:{TEXT};">{_ex["title"]}</span>'
            f'<span style="background:{_lvl_clr}33;color:{_lvl_clr};padding:2px 10px;'
            f'border-radius:12px;font-size:.7rem;font-weight:700;">{_ex["level"]}</span></div>'
            f'<div style="font-size:.82rem;color:{TEXT};margin-bottom:8px;">{_ex["question"]}</div>'
            f'<div style="font-size:.76rem;color:{M};">Topic: <b style="color:{STEEL};">{_ex["topic"]}</b>'
            f' &nbsp;|&nbsp; Expected: <i>{_ex["expected"]}</i></div>',
            left=_lvl_clr,
        ), unsafe_allow_html=True)

        _hint_shown = st.checkbox("Show hint", key=f"hint_{_ex['id']}")
        if _hint_shown:
            st.markdown(_card(
                f'<span style="font-size:.78rem;color:{AMBER};">💡 Hint: {_ex["hint"]}</span>',
                left=AMBER, pad="8px 14px",
            ), unsafe_allow_html=True)

        # Saved answer or default
        _saved_ans = st.session_state.ex_answers.get(_ex["id"], "")
        _default_ans = _saved_ans if _saved_ans else (
            "-- Write your SQL query here\n\n" if _ex["answer_sql"] is not None
            else "# Write your Python code here\n\n"
        )
        _lang = "sql" if _ex["answer_sql"] is not None else "python"

        # ACE editor for exercises — SQL or Python depending on exercise type
        from streamlit_ace import st_ace as _st_ace_ex
        _ace_key = f"ex_ace_{_ex['id']}"
        if _ace_key not in st.session_state:
            st.session_state[_ace_key] = _default_ans
        # Reset if exercise changed and saved answer is different
        if _saved_ans and st.session_state[_ace_key] != _saved_ans:
            pass  # keep what user typed

        _ex_code = _st_ace_ex(
            value=st.session_state[_ace_key],
            language=_lang,
            theme="monokai",
            key=_ace_key + "_widget",
            height=220,
            font_size=14,
            tab_size=4,
            show_gutter=True,
            show_print_margin=False,
            wrap=False,
            auto_update=True,
            placeholder=f"-- Write your {_lang.upper()} answer here...",
        )
        if _ex_code is not None:
            st.session_state[_ace_key] = _ex_code

        _chk1, _chk2, _chk3 = st.columns(3)
        _run_ex  = _chk1.button("▶ Run", key=f"run_ex_{_ex['id']}", use_container_width=True)
        _check   = _chk2.button("✅ Check Answer", key=f"check_{_ex['id']}", type="primary", use_container_width=True)
        _reveal  = _chk3.button("👁 Reveal Answer", key=f"reveal_{_ex['id']}", use_container_width=True)

        st.session_state.ex_answers[_ex["id"]] = _ex_code

        if _reveal:
            ans_code = _ex.get("answer_py") or _ex.get("answer_sql", "")
            if ans_code:
                st.code(ans_code.strip(), language=_lang)

        _ex_result_df = None
        if _run_ex or _check:
            if _ex["answer_sql"] is not None:
                _ex_result_df = _run(_ex_code, conn)
                if _ex_result_df is not None:
                    _show(_ex_result_df, 200)
            else:
                # Python exercise
                _py_buf = _io.StringIO()
                _py_ns  = {"dfs": dfs, "pd": pd, "conn": conn, "result": None}
                import numpy as _np2
                _py_ns["np"] = _np2
                with _cl.redirect_stdout(_py_buf):
                    try:
                        exec(compile(_ex_code, "<exercise>", "exec"), _py_ns)
                        _py_ns["_ok"] = True
                    except Exception:
                        _py_ns["_ok"] = False
                        _py_ns["_err"] = _tb.format_exc()
                _out_txt = _py_buf.getvalue()
                if _out_txt:
                    st.code(_out_txt, language="text")
                if not _py_ns.get("_ok", True):
                    st.error(_py_ns.get("_err",""))
                _ex_result_df = _py_ns.get("result")
                if isinstance(_ex_result_df, pd.DataFrame):
                    _show(_ex_result_df, 200)

        if _check and _ex_result_df is not None:
            try:
                _passed = _ex["answer_check"](_ex_result_df)
            except Exception:
                _passed = False

            st.session_state.ex_results[_ex["id"]] = {"passed": _passed}
            if _passed:
                st.success("✅ Correct! Well done.")
                st.balloons()
            else:
                st.error(f"❌ Not quite right. Expected: {_ex['expected']}")
                st.info("Tip: Click 'Show hint' or 'Reveal Answer' if stuck.")
        elif _check and _ex_result_df is None:
            st.warning("Run your query first, then check.")

        # Progress bar
        st.markdown(_h3("📊 Exercise Progress", STEEL), unsafe_allow_html=True)
        _total = len(_EXERCISES)
        _solved_count = sum(1 for v in st.session_state.ex_results.values() if v.get("passed"))
        st.progress(_solved_count / _total, text=f"{_solved_count}/{_total} completed")

        _prog_rows = []
        for _e in _EXERCISES:
            _r = st.session_state.ex_results.get(_e["id"], {})
            _prog_rows.append({
                "Exercise": _e["title"],
                "Level":    _e["level"],
                "Topic":    _e["topic"],
                "Status":   "✅ Passed" if _r.get("passed") else ("🔄 Attempted" if _e["id"] in st.session_state.ex_answers and st.session_state.ex_answers[_e["id"]] not in ["","-- Write your SQL query here\n\n","# Write your Python code here\n\n"] else "⬜ Not started"),
            })
        st.dataframe(pd.DataFrame(_prog_rows), use_container_width=True, height=280, hide_index=True)


# ═══════════════════════════════════════════════════════════════════════
# TAB 15 — QUERY EXPLAIN (execution plan)
# ═══════════════════════════════════════════════════════════════════════
with T[15]:
    st.markdown(_h2("Query Execution Plan", "⚡"), unsafe_allow_html=True)
    st.markdown(_card(
        f'Paste any SQL query and see DuckDB\'s execution plan — learn how the query engine '
        f'scans, joins, aggregates and sorts data. Understanding query plans is essential for '
        f'query optimisation and performance tuning.',
        left=TEAL,
    ), unsafe_allow_html=True)

    _EXPLAIN_EXAMPLES = {
        "Simple SELECT with WHERE": "SELECT * FROM trips WHERE status = 'Completed' LIMIT 100",
        "GROUP BY aggregation": "SELECT fleet_id, COUNT(*), SUM(trip_fare_pkr) FROM trips WHERE status='Completed' GROUP BY fleet_id",
        "JOIN two tables": "SELECT t.trip_id, c.full_name, t.trip_fare_pkr FROM trips t JOIN customers c ON t.customer_id = c.customer_id WHERE t.status='Completed'",
        "CTE + Window function": """WITH monthly AS (
    SELECT DATE_TRUNC('month', pickup_datetime::DATE) AS month, SUM(trip_fare_pkr) AS revenue
    FROM trips WHERE status='Completed' GROUP BY 1
)
SELECT month, revenue, LAG(revenue) OVER (ORDER BY month) AS prev
FROM monthly ORDER BY month""",
        "Subquery": "SELECT * FROM trips WHERE trip_fare_pkr > (SELECT AVG(trip_fare_pkr) FROM trips WHERE status='Completed')",
        "QUALIFY dedup": "SELECT vehicle_id, trip_id, trip_fare_pkr FROM trips QUALIFY ROW_NUMBER() OVER (PARTITION BY vehicle_id ORDER BY trip_fare_pkr DESC) = 1",
    }

    _xp_sel = st.selectbox("Load example:", ["(write your own)"] + list(_EXPLAIN_EXAMPLES.keys()), key="xp_sel")
    _xp_default = _EXPLAIN_EXAMPLES.get(_xp_sel, "-- Paste your SQL query here\nSELECT * FROM trips LIMIT 10")

    if "xp_code" not in st.session_state:
        st.session_state.xp_code = _xp_default
    if _xp_sel != "(write your own)":
        st.session_state.xp_code = _xp_default

    from streamlit_ace import st_ace as _st_ace_xp
    _xp_sql = _st_ace_xp(
        value=st.session_state.xp_code,
        language="sql",
        theme="monokai",
        key="xp_ace_editor",
        height=200,
        font_size=14,
        tab_size=4,
        show_gutter=True,
        show_print_margin=False,
        wrap=False,
        auto_update=True,
        placeholder="-- Paste your SQL query here...",
    )
    if _xp_sql is not None:
        st.session_state.xp_code = _xp_sql

    _xp_c1, _xp_c2, _xp_c3 = st.columns(3)
    _run_explain   = _xp_c1.button("⚡ EXPLAIN",            type="primary",   key="run_explain",  use_container_width=True)
    _run_explain_a = _xp_c2.button("📊 EXPLAIN ANALYZE",    type="secondary", key="run_explain_a",use_container_width=True)
    _run_actual    = _xp_c3.button("▶ Run Query",           type="secondary", key="run_xp_actual",use_container_width=True)

    if _run_explain:
        try:
            _plan = conn.execute(f"EXPLAIN {_xp_sql}").fetchdf()
            st.markdown(_h3("📋 Execution Plan (EXPLAIN)", TEAL), unsafe_allow_html=True)
            if not _plan.empty:
                _plan_text = "\n".join(str(v) for v in _plan.iloc[:, -1])
                st.code(_plan_text, language="text")

            # Parse and explain the plan
            st.markdown(_h3("🔍 Plan Breakdown", STEEL), unsafe_allow_html=True)
            _plan_ops = {
                "SEQ_SCAN":        ("Sequential Scan", "Reads every row in the table. Fast for small tables or when most rows are needed. Add an index for large filtered scans.", AMBER),
                "FILTER":          ("Filter", "Applies WHERE conditions to rows. Runs after the scan — push filters earlier in the query for efficiency.", STEEL),
                "HASH_JOIN":       ("Hash Join", "Builds a hash table on the smaller side, probes with the larger. Efficient for large joins. Used when no index exists.", TEAL),
                "HASH_GROUP_BY":   ("Hash Aggregation", "Groups rows by building a hash table. Memory-intensive for many groups.", TEAL),
                "PROJECTION":      ("Projection", "Selects only the needed columns. Reduces data volume early.", TEAL),
                "ORDER_BY":        ("Sort / Order By", "Sorts rows. Expensive on large datasets — avoid when possible or use indexes.", AMBER),
                "LIMIT":           ("Limit", "Stops execution after N rows. Very fast — always add LIMIT when exploring.", TEAL),
                "WINDOW":          ("Window Function", "Computes over a partition of rows. Requires a sort step internally.", AMBER),
                "CTE":             ("Common Table Expression", "Materialises an intermediate result. DuckDB may inline it automatically.", STEEL),
            }

            _plan_str = _plan_text.upper()
            _found_ops = [(op, desc, hint, clr) for op, (desc, hint, clr) in _plan_ops.items() if op in _plan_str]
            if _found_ops:
                for _op, _desc, _hint, _clr in _found_ops:
                    st.markdown(_concept(f"{_op} — {_desc}", _hint, "⚙️", _clr), unsafe_allow_html=True)
            else:
                st.info("No specific operators detected in plan.")

        except Exception as _ex:
            st.error(f"EXPLAIN error: {_ex}")

    if _run_explain_a:
        try:
            _plan_a = conn.execute(f"EXPLAIN ANALYZE {_xp_sql}").fetchdf()
            st.markdown(_h3("📊 Execution Plan with Timing (EXPLAIN ANALYZE)", BRAND), unsafe_allow_html=True)
            if not _plan_a.empty:
                _plan_text_a = "\n".join(str(v) for v in _plan_a.iloc[:, -1])
                st.code(_plan_text_a, language="text")
                st.markdown(_card(
                    f'<b style="color:{TEAL};">EXPLAIN ANALYZE</b> actually executes the query and shows real timings per operator.<br>'
                    f'Look for operators with high "actual time" — these are bottlenecks to optimise.',
                    left=TEAL, pad="10px 14px",
                ), unsafe_allow_html=True)
        except Exception as _ex:
            st.error(f"EXPLAIN ANALYZE error: {_ex}")

    if _run_actual:
        _res_xp = _run(_xp_sql, conn)
        if _res_xp is not None:
            _show(_res_xp, 280)

    # Explain concepts
    st.markdown(_h3("📚 Reading Query Plans", STEEL), unsafe_allow_html=True)
    _explain_tips = [
        ("Read bottom-up", "Query plans execute from the innermost (bottom) node outward. The first thing that runs is at the bottom of the plan.", "📖", STEEL),
        ("Watch for SEQ_SCAN on large tables", "A sequential scan on millions of rows is slow. Add a WHERE clause with an indexed column to get a range scan instead.", "⚠️", AMBER),
        ("Hash Join vs Nested Loop", "Hash Join = efficient for large tables. Nested Loop = good when one side is tiny. DuckDB picks automatically.", "🔗", TEAL),
        ("EXPLAIN vs EXPLAIN ANALYZE", "EXPLAIN shows the plan without running. EXPLAIN ANALYZE runs the query and shows actual row counts and timings.", "⚡", BRAND),
        ("Projection pushdown", "DuckDB automatically pushes column selection (SELECT) down to the scan to avoid reading unnecessary columns.", "📊", TEAL),
        ("Filter pushdown", "DuckDB pushes WHERE conditions as close to the source scan as possible — you can help by writing specific WHERE clauses.", "🎯", ORANGE),
    ]
    _et1, _et2 = st.columns(2)
    for i, (t, b, ic, c) in enumerate(_explain_tips):
        with (_et1 if i % 2 == 0 else _et2):
            st.markdown(_concept(t, b, ic, c), unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════
# TAB 16 — DATA PROFILING
# ═══════════════════════════════════════════════════════════════════════
with T[16]:
    st.markdown(_h2("Data Profiling", "📈"), unsafe_allow_html=True)
    st.markdown(_card(
        f'Automatic column-level profiling: null rates, distinct counts, min/max/mean, '
        f'top values, data type distribution, and outlier detection.',
        left=TEAL,
    ), unsafe_allow_html=True)

    _PROFILE_TABLES = ["trips","customers","vehicles","drivers","fleets",
                       "invoices","fuel_logs","maintenance","telematics"]

    _pf_col1, _pf_col2, _pf_col3 = st.columns(3)
    with _pf_col1:
        _pf_tbl = st.selectbox("Table:", _PROFILE_TABLES, key="pf_table")
    with _pf_col2:
        _pf_sample = st.selectbox("Sample rows:", [1000, 5000, 10000, "All"], index=1, key="pf_sample")
    with _pf_col3:
        st.markdown("<br>", unsafe_allow_html=True)
        _pf_run = st.button("🔍 Profile Table", type="primary", key="pf_run", use_container_width=True)

    if _pf_run:
        with st.spinner(f"Profiling {_pf_tbl}..."):
            _limit_clause = f"LIMIT {_pf_sample}" if _pf_sample != "All" else ""
            _pf_df = _run(f"SELECT * FROM {_pf_tbl} {_limit_clause}", conn)

        if _pf_df is not None and not _pf_df.empty:
            _n = len(_pf_df)
            st.markdown(_h3(f"📊 {_pf_tbl} — {_n:,} rows × {len(_pf_df.columns)} columns", BRAND), unsafe_allow_html=True)

            # Summary metrics
            _pm1, _pm2, _pm3, _pm4 = st.columns(4)
            _pm1.metric("Rows",       f"{_n:,}")
            _pm2.metric("Columns",    str(len(_pf_df.columns)))
            _pm3.metric("Memory (KB)", f"{_pf_df.memory_usage(deep=True).sum()//1024:,}")
            _pm4.metric("Null cells", f"{_pf_df.isnull().sum().sum():,}")

            # Column profile
            _profile_rows = []
            for _col in _pf_df.columns:
                _series = _pf_df[_col]
                _null_n = int(_series.isnull().sum())
                _null_p = round(_null_n * 100 / _n, 1)
                _distinct = int(_series.nunique())
                _dtype = str(_series.dtype)

                _profile_row = {
                    "Column":    _col,
                    "Type":      _dtype,
                    "Nulls":     f"{_null_n:,} ({_null_p}%)",
                    "Distinct":  f"{_distinct:,}",
                    "Health":    "✅" if _null_p <= 1 else ("⚠️" if _null_p <= 5 else "❌"),
                }

                if _dtype in ("object", "string", "category"):
                    _top = _series.value_counts().head(3)
                    _profile_row["Min/Top values"] = ", ".join(str(v) for v in _top.index[:3])
                    _profile_row["Max/Bottom"] = f"{_distinct} unique"
                elif "int" in _dtype or "float" in _dtype:
                    _num = pd.to_numeric(_series, errors="coerce").dropna()
                    if len(_num) > 0:
                        _profile_row["Min/Top values"] = f"{_num.min():,.1f}"
                        _profile_row["Max/Bottom"] = f"{_num.max():,.1f}"
                        _profile_row["Mean"] = f"{_num.mean():,.1f}"
                    else:
                        _profile_row["Min/Top values"] = "—"
                        _profile_row["Max/Bottom"] = "—"
                        _profile_row["Mean"] = "—"
                elif "datetime" in _dtype or "timestamp" in _dtype.lower():
                    _dt = pd.to_datetime(_series, errors="coerce").dropna()
                    if len(_dt):
                        _profile_row["Min/Top values"] = str(_dt.min().date())
                        _profile_row["Max/Bottom"]     = str(_dt.max().date())
                    else:
                        _profile_row["Min/Top values"] = "—"
                        _profile_row["Max/Bottom"] = "—"
                else:
                    _profile_row["Min/Top values"] = "—"
                    _profile_row["Max/Bottom"] = "—"

                _profile_rows.append(_profile_row)

            _profile_df = pd.DataFrame(_profile_rows)
            st.dataframe(_profile_df, use_container_width=True, height=380, hide_index=True)

            # Distribution charts for numeric columns
            _num_cols_pf = [c for c in _pf_df.columns
                            if _pf_df[c].dtype in ("int64","float64","int32","float32")]
            if _num_cols_pf:
                st.markdown(_h3("📊 Numeric Distribution", STEEL), unsafe_allow_html=True)
                _dist_col = st.selectbox("Column:", _num_cols_pf, key="dist_col")
                _dist_data = pd.to_numeric(_pf_df[_dist_col], errors="coerce").dropna()
                if len(_dist_data) > 0:
                    _dc1, _dc2 = st.columns(2)
                    with _dc1:
                        fig_hist = px.histogram(_dist_data, nbins=30,
                                                title=f"Distribution: {_dist_col}",
                                                template="plotly_dark",
                                                color_discrete_sequence=[BRAND])
                        fig_hist.update_layout(height=260, showlegend=False,
                                               margin=dict(t=35,b=0,l=0,r=0),
                                               paper_bgcolor="rgba(0,0,0,0)",
                                               plot_bgcolor="rgba(0,0,0,0)")
                        st.plotly_chart(fig_hist, use_container_width=True)
                    with _dc2:
                        fig_box = px.box(_pf_df, y=_dist_col, template="plotly_dark",
                                         title=f"Box Plot: {_dist_col}",
                                         color_discrete_sequence=[TEAL])
                        fig_box.update_layout(height=260, margin=dict(t=35,b=0,l=0,r=0),
                                              paper_bgcolor="rgba(0,0,0,0)",
                                              plot_bgcolor="rgba(0,0,0,0)")
                        st.plotly_chart(fig_box, use_container_width=True)

                    # Outlier detection (IQR method)
                    _q1, _q3 = _dist_data.quantile(0.25), _dist_data.quantile(0.75)
                    _iqr = _q3 - _q1
                    _outliers = _dist_data[(_dist_data < _q1 - 1.5*_iqr) | (_dist_data > _q3 + 1.5*_iqr)]
                    if len(_outliers) > 0:
                        st.markdown(_card(
                            f'<b style="color:{AMBER};">Outliers detected:</b> {len(_outliers):,} rows '
                            f'({len(_outliers)*100/len(_dist_data):.1f}%) outside IQR fences '
                            f'[{_q1-1.5*_iqr:,.1f}, {_q3+1.5*_iqr:,.1f}]',
                            left=AMBER, pad="8px 14px",
                        ), unsafe_allow_html=True)

            # Categorical top values
            _cat_cols_pf = [c for c in _pf_df.columns if _pf_df[c].dtype == "object"]
            if _cat_cols_pf:
                st.markdown(_h3("📊 Categorical Top Values", STEEL), unsafe_allow_html=True)
                _cat_col = st.selectbox("Column:", _cat_cols_pf, key="cat_col_pf")
                _vc = _pf_df[_cat_col].value_counts().head(10).reset_index()
                _vc.columns = ["Value", "Count"]
                _vc["Pct"] = (_vc["Count"] / _n * 100).round(1).astype(str) + "%"
                _cpc1, _cpc2 = st.columns(2)
                with _cpc1:
                    st.dataframe(_vc, use_container_width=True, height=260, hide_index=True)
                with _cpc2:
                    fig_cat = px.bar(_vc, x="Value", y="Count",
                                     template="plotly_dark",
                                     color_discrete_sequence=[AMBER])
                    fig_cat.update_layout(height=260, margin=dict(t=10,b=0,l=0,r=0),
                                          paper_bgcolor="rgba(0,0,0,0)",
                                          plot_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(fig_cat, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════
# TAB 17 — DBT-STYLE DOCUMENTATION
# ═══════════════════════════════════════════════════════════════════════
with T[17]:
    st.markdown(_h2("Data Documentation", "📖"), unsafe_allow_html=True)
    st.markdown(_card(
        f'dbt-style documentation: table descriptions, column definitions, '
        f'data tests, lineage notes, and business definitions. '
        f'Everything a new analyst needs to understand the data.',
        left=TEAL,
    ), unsafe_allow_html=True)

    _DOCS = {
        "trips": {
            "description": "The central transactional table. Each row represents one vehicle rental trip from pickup to dropoff. This is the primary source of revenue data and operational metrics.",
            "owner": "Operations Team",
            "freshness": "Updated every ETL run (batch or incremental)",
            "grain": "One row per trip",
            "tests": [
                ("trip_id is unique",          "SELECT COUNT(*) = COUNT(DISTINCT trip_id) FROM trips",   "uniqueness"),
                ("pickup_datetime not null",   "SELECT COUNT(*) FILTER (WHERE pickup_datetime IS NULL) = 0 FROM trips", "not_null"),
                ("trip_fare_pkr >= 0",         "SELECT COUNT(*) FILTER (WHERE trip_fare_pkr < 0) = 0 FROM trips",  "range"),
                ("status in valid values",     "SELECT COUNT(*) FILTER (WHERE status NOT IN ('Completed','Cancelled','In Progress','Confirmed')) = 0 FROM trips", "accepted_values"),
                ("customer_id refs customers", "SELECT COUNT(*) = 0 FROM trips t LEFT JOIN customers c ON t.customer_id=c.customer_id WHERE c.customer_id IS NULL AND t.customer_id IS NOT NULL", "referential_integrity"),
            ],
            "columns": {
                "trip_id":             "Unique identifier for this trip. Format: TR000001. Used to join to invoices and telematics.",
                "customer_id":         "References customers.customer_id. Identifies who rented the vehicle.",
                "vehicle_id":          "References vehicles.vehicle_id. Identifies which vehicle was rented.",
                "driver_id":           "References drivers.driver_id. NULL when customer drives themselves (self_drive=True).",
                "fleet_id":            "References fleets.fleet_id. Which rental company owns this vehicle.",
                "booking_type":        "Category of rental: City Ride, Airport Transfer, Intercity, Wedding, Corporate, Tourism.",
                "pickup_datetime":     "When the customer took possession of the vehicle. Used as the primary date dimension key.",
                "dropoff_datetime":    "When the vehicle was returned. Used with pickup_datetime to calculate actual duration.",
                "duration_days":       "Actual rental duration in days. Calculated from timestamps. May differ from requested duration.",
                "trip_fare_pkr":       "The base rental charge in Pakistani Rupees. Excludes driver allowance and surcharges.",
                "driver_allowance_pkr":"Additional fee paid to the driver. Only non-zero when with_driver=True.",
                "with_driver":         "True if the rental includes a chauffeur. Affects fare calculation and driver assignment.",
                "status":              "Current trip status. Completed = finished. Cancelled = customer cancelled. In Progress = active.",
                "distance_km":         "GPS-measured distance of the trip. Used for km-rate billing on outstation trips.",
            },
            "metrics": {
                "Total Revenue":       "SUM(trip_fare_pkr) WHERE status='Completed'",
                "Avg Fare":            "AVG(trip_fare_pkr) WHERE status='Completed'",
                "Cancellation Rate":   "COUNT(*) FILTER (WHERE status='Cancelled') / COUNT(*)",
                "Revenue per KM":      "SUM(trip_fare_pkr) / SUM(distance_km) WHERE status='Completed'",
            },
        },
        "customers": {
            "description": "Customer master data. One record per registered customer. Contains demographic, contact, and behavioural attributes.",
            "owner": "CRM Team",
            "freshness": "Updated on full load or when new registrations arrive",
            "grain": "One row per customer",
            "tests": [
                ("customer_id is unique",     "SELECT COUNT(*) = COUNT(DISTINCT customer_id) FROM customers", "uniqueness"),
                ("email format valid",        "SELECT COUNT(*) FILTER (WHERE email NOT LIKE '%@%') = 0 FROM customers", "format"),
                ("registration_date not null","SELECT COUNT(*) FILTER (WHERE registration_date IS NULL) = 0 FROM customers", "not_null"),
            ],
            "columns": {
                "customer_id":     "Unique customer identifier. Format: CU00001.",
                "full_name":       "Customer full name. May be null in ~3% of rows (injected DQ issue).",
                "gender":          "M or F. Used for demographic analysis.",
                "dob":             "Date of birth. Used to calculate age at time of booking.",
                "cnic":            "Pakistani Computerized National Identity Card number. 13 digits. PII.",
                "customer_type":   "Tourist / Business / Local / Corporate. Drives pricing and loyalty treatment.",
                "loyalty_points":  "Accumulated rewards points. 100 points = PKR 100 discount on next booking.",
                "registration_date": "Date customer first registered in the system.",
            },
            "metrics": {
                "Active Customers":    "COUNT(DISTINCT customer_id) WHERE last trip < 90 days ago",
                "Avg LTV":             "AVG(total_spend_pkr) per customer over lifetime",
                "Churn Rate":          "Customers with no trip in 90 days / total customers",
            },
        },
        "dim_customer": {
            "description": "SCD Type 2 customer dimension in the DWH. Tracks changes to customer attributes over time. Each row represents a customer during a specific valid period.",
            "owner": "Data Engineering",
            "freshness": "Updated on every ETL run",
            "grain": "One row per customer version (may have multiple rows per customer_id if attributes changed)",
            "tests": [
                ("customer_sk is unique",           "SELECT COUNT(*) = COUNT(DISTINCT customer_sk) FROM dwh.dim_customer", "uniqueness"),
                ("only one is_current=True per customer_id", "SELECT COUNT(*) = 0 FROM (SELECT customer_id, SUM(CAST(is_current AS INT)) AS cnt FROM dwh.dim_customer GROUP BY customer_id HAVING cnt > 1)", "scd2_integrity"),
            ],
            "columns": {
                "customer_sk":    "Surrogate key (integer). Stable even if source customer_id changes. Used in fact table JOINs.",
                "customer_id":    "Natural key from OLTP system. Used to link back to source.",
                "valid_from":     "Date this version of the record became active.",
                "valid_to":       "Date this version expired. '9999-12-31' = currently active.",
                "is_current":     "True for the most recent version of each customer. Use WHERE is_current=True for current state.",
                "rfm_segment":    "RFM classification: Champion / Loyal / Regular / One-Time / Prospect.",
            },
            "metrics": {},
        },
        "fact_trips": {
            "description": "Core revenue and operational fact table in the DWH. Grain: one row per completed trip. Contains all dimension FK references and pre-computed metrics.",
            "owner": "Data Engineering",
            "freshness": "Updated on every ETL run",
            "grain": "One row per trip",
            "tests": [
                ("trip_sk is unique", "SELECT COUNT(*) = COUNT(DISTINCT trip_sk) FROM dwh.fact_trips", "uniqueness"),
                ("all FKs resolve",   "SELECT COUNT(*) FILTER (WHERE customer_sk = -1) < 100 FROM dwh.fact_trips", "ref_integrity_threshold"),
            ],
            "columns": {
                "trip_sk":          "Surrogate PK (integer). Generated by DWH, stable across reloads.",
                "pickup_date_key":  "FK to dim_date. Integer YYYYMMDD. Use for all date-based filtering.",
                "customer_sk":      "FK to dim_customer. -1 = unknown (late-arriving or bad data).",
                "vehicle_sk":       "FK to dim_vehicle. -1 = unknown.",
                "driver_sk":        "FK to dim_driver. -1 = self-drive or unknown.",
                "fleet_sk":         "FK to dim_fleet.",
                "trip_fare_pkr":    "Revenue measure. Same as trips.trip_fare_pkr after DQ cleaning.",
                "revenue_per_day":  "Pre-computed: trip_fare_pkr / duration_days. Avoids repeated calculation.",
                "revenue_per_km":   "Pre-computed: trip_fare_pkr / distance_km.",
                "is_intercity":     "True when pickup_city != dropoff_city. Pre-computed flag.",
                "_dq_zero_fare":    "DQ flag: True when trip_fare_pkr <= 0. These rows should be reviewed.",
                "_dq_timeline_reversed": "DQ flag: True when dropoff < pickup. Bad source data.",
            },
            "metrics": {
                "Gross Revenue":  "SUM(trip_fare_pkr)",
                "Avg Revenue/Day": "AVG(revenue_per_day)",
                "Intercity Rate":  "COUNT(*) FILTER(WHERE is_intercity) / COUNT(*)",
                "DQ Issue Rate":   "COUNT(*) FILTER(WHERE _dq_zero_fare OR _dq_timeline_reversed) / COUNT(*)",
            },
        },
    }

    _doc_tabs = st.tabs(["📊 Table Docs", "✅ Data Tests", "📐 Metrics Glossary", "📝 Business Terms"])

    with _doc_tabs[0]:
        _doc_sel = st.selectbox("Select table:", list(_DOCS.keys()), key="doc_sel")
        _doc = _DOCS[_doc_sel]

        # Header card
        st.markdown(_card(
            f'<div style="display:flex;justify-content:space-between;align-items:flex-start;">'
            f'<div><div style="font-size:1rem;font-weight:800;color:{BRAND};">{_doc_sel}</div>'
            f'<div style="font-size:.78rem;color:{TEXT};margin-top:4px;">{_doc["description"]}</div></div>'
            f'</div>'
            f'<div style="margin-top:10px;font-size:.76rem;color:{M};">'
            f'Owner: <b style="color:{STEEL};">{_doc["owner"]}</b> &nbsp;|&nbsp; '
            f'Grain: <b style="color:{STEEL};">{_doc["grain"]}</b> &nbsp;|&nbsp; '
            f'Freshness: <b style="color:{STEEL};">{_doc["freshness"]}</b></div>',
            left=BRAND,
        ), unsafe_allow_html=True)

        # Column definitions
        if _doc.get("columns"):
            st.markdown(_h3("📋 Column Definitions", STEEL), unsafe_allow_html=True)
            _col_doc_rows = [
                {"Column": col, "Description": desc}
                for col, desc in _doc["columns"].items()
            ]
            st.dataframe(pd.DataFrame(_col_doc_rows), use_container_width=True,
                         height=min(350, 36 * len(_col_doc_rows) + 40), hide_index=True)

    with _doc_tabs[1]:
        st.markdown(_h3("✅ Data Quality Tests", STEEL), unsafe_allow_html=True)
        _all_tests = []
        for _tname, _td in _DOCS.items():
            for _test_name, _test_sql, _test_type in _td.get("tests", []):
                _all_tests.append({
                    "Table":     _tname,
                    "Test":      _test_name,
                    "Type":      _test_type,
                    "SQL":       _test_sql,
                    "Status":    "—",
                })

        _run_all_tests = st.button("▶ Run All Tests", type="primary", key="run_all_tests")
        if _run_all_tests:
            for i, _t in enumerate(_all_tests):
                try:
                    _res_t = conn.execute(_t["SQL"]).fetchone()
                    _passed_t = bool(_res_t[0]) if _res_t else False
                    _all_tests[i]["Status"] = "✅ Pass" if _passed_t else "❌ FAIL"
                except Exception as _te:
                    _all_tests[i]["Status"] = f"⚠️ Error"

        _test_df = pd.DataFrame(_all_tests)[["Table","Test","Type","Status"]]
        st.dataframe(_test_df, use_container_width=True, height=400, hide_index=True)

    with _doc_tabs[2]:
        st.markdown(_h3("📐 Business Metrics Glossary", STEEL), unsafe_allow_html=True)
        _all_metrics = []
        for _tname, _td in _DOCS.items():
            for _mname, _mdef in _td.get("metrics", {}).items():
                _all_metrics.append({
                    "Metric":      _mname,
                    "Source Table": _tname,
                    "Definition":  _mdef,
                })
        if _all_metrics:
            st.dataframe(pd.DataFrame(_all_metrics), use_container_width=True,
                         height=300, hide_index=True)

        # Live metric calculator
        st.markdown(_h3("🧮 Live Metric Calculator", TEAL), unsafe_allow_html=True)
        _metric_sql = {
            "Gross Revenue (all time)": "SELECT ROUND(SUM(trip_fare_pkr),0) AS gross_revenue FROM trips WHERE status='Completed'",
            "Avg Fare per Trip":        "SELECT ROUND(AVG(trip_fare_pkr),0) AS avg_fare FROM trips WHERE status='Completed'",
            "Cancellation Rate %":      "SELECT ROUND(COUNT(*) FILTER (WHERE status='Cancelled')*100.0/COUNT(*),2) AS cancel_pct FROM trips",
            "Unique Active Customers":  "SELECT COUNT(DISTINCT customer_id) AS active_customers FROM trips WHERE status='Completed'",
            "Fleet Utilisation %":      "SELECT ROUND(AVG(days_used/30.0)*100,1) AS avg_util_pct FROM (SELECT vehicle_id, SUM(duration_days) AS days_used FROM trips WHERE status='Completed' GROUP BY vehicle_id)",
        }
        _met_sel = st.selectbox("Metric:", list(_metric_sql.keys()), key="met_sel")
        if st.button("Calculate", key="calc_metric"):
            _mr = _run(_metric_sql[_met_sel], conn)
            if _mr is not None and not _mr.empty:
                _val = _mr.iloc[0, 0]
                st.metric(_met_sel, f"{_val:,.1f}" if isinstance(_val, float) else f"{_val:,}")

    with _doc_tabs[3]:
        st.markdown(_h3("📝 Business Terms Dictionary", STEEL), unsafe_allow_html=True)
        _TERMS = {
            "Trip":              "A single vehicle rental from pickup to dropoff. The atomic unit of revenue.",
            "Booking":           "A reservation request that may or may not result in a completed trip. A booking that is not cancelled becomes a trip.",
            "Fleet":             "A rent-a-car company (e.g. Hassan Rent a Car). Owns vehicles and employs drivers.",
            "Fare (PKR)":        "The monetary charge for a rental in Pakistani Rupees. Base fare excludes driver allowance and surcharges.",
            "SCD Type 2":        "Slowly Changing Dimension. A technique to track how dimension attributes (e.g. customer city) change over time by keeping both old and new versions.",
            "Watermark":         "The timestamp of the last successfully processed row. Used by incremental ETL to load only new data.",
            "Grain":             "What one row represents in a table. Always define grain first before designing a fact table.",
            "Surrogate Key":     "A system-generated integer primary key (e.g. customer_sk). Stable, independent of source data changes.",
            "Natural Key":       "The original identifier from the source system (e.g. customer_id = CU00042). May change.",
            "ELT":               "Extract, Load, Transform. Data is loaded raw first, then transformed inside the warehouse using SQL.",
            "Conformed Dimension": "A dimension shared across multiple fact tables (e.g. dim_date joins fact_trips AND fact_invoices).",
            "DQ Flag":           "A boolean column (e.g. _dq_zero_fare) marking rows with suspected data quality issues. These rows are loaded but flagged for review.",
            "Churn":             "A customer who has not made a trip in 90+ days. At risk of permanently leaving.",
            "LTV":               "Lifetime Value. Total revenue generated by a customer over their entire relationship.",
            "RFM":               "Recency + Frequency + Monetary. A customer segmentation model using these three dimensions.",
            "Outstation":        "A trip where pickup and dropoff cities differ. Typically charged at higher per-km rates.",
            "Utilisation":       "The percentage of a vehicle's available days that it was actually on a trip. 70%+ is considered high.",
        }
        _terms_df = pd.DataFrame(
            [{"Term": k, "Definition": v} for k, v in sorted(_TERMS.items())]
        )
        _search_terms = st.text_input("Search terms:", key="terms_search", placeholder="e.g. RFM, LTV, SCD...")
        if _search_terms:
            _terms_df = _terms_df[
                _terms_df["Term"].str.lower().str.contains(_search_terms.lower()) |
                _terms_df["Definition"].str.lower().str.contains(_search_terms.lower())
            ]
        st.dataframe(_terms_df, use_container_width=True, height=450, hide_index=True)
