"""
p21_observability.py — Pipeline Observability & Monitoring
Pipeline health · Run history · Row count trends
Anomaly detection · SLA tracking · Data freshness alerts
"""
from datetime import datetime, timedelta
import random
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from pathlib import Path
from page_modules._shared import inject, get_data, BRAND, STEEL, GREEN, AMBER, ORANGE, TEXT
inject()
M="#5a7a96"; CB="#141e2b"; BD="#1e2f44"; TEAL="#2A9D8F"; PUR="#6A4C93"
def _card(b,l=BRAND,p="14px 16px"): return f'<div style="background:{CB};border:1px solid {BD};border-left:3px solid {l};border-radius:10px;padding:{p};margin:6px 0;">{b}</div>'
def _h2(t,i=""): return f'<div style="font-size:1.22rem;font-weight:800;color:{TEXT};margin:16px 0 4px;"><span style="color:{BRAND};">{i} </span>{t}</div>'
def _h3(t,c=STEEL): return f'<div style="font-size:.9rem;font-weight:700;color:{c};border-left:3px solid {c};padding-left:8px;margin:10px 0 6px;">{t}</div>'

dfs = get_data()
STATE_FILE = Path("data/csv/pipeline_state.json")

st.markdown(f'<div style="font-size:1.6rem;font-weight:900;color:{BRAND};">👁️ Pipeline Observability</div>'
            f'<div style="font-size:.8rem;color:{M};">Pipeline health · Run history · Anomaly detection · SLA tracking · Data freshness · Alerts</div>',
            unsafe_allow_html=True)
st.markdown(f"<hr style='border-color:{BD};margin:6px 0 10px'>",unsafe_allow_html=True)

TAB = st.tabs(["🏥 Pipeline Health","📈 Run History","🚨 Anomaly Detection","⏱️ SLA Tracking","💧 Data Freshness","📚 Concepts"])

# ── TAB 0: PIPELINE HEALTH ───────────────────────────────────────────────────
with TAB[0]:
    st.markdown(_h2("Pipeline Health Dashboard","🏥"), unsafe_allow_html=True)

    # Read real pipeline state
    import json as _json
    _state = {}
    if STATE_FILE.exists():
        try: _state = _json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except: pass

    _last_full  = _state.get("last_full_load","Never")
    _last_incr  = _state.get("last_incremental","Never")
    _run_count  = _state.get("run_count",0)
    _arcs       = len(_state.get("archive_runs",[]))
    _wm         = _state.get("total_rows_loaded",{})

    k1,k2,k3,k4 = st.columns(4)
    k1.metric("Last Full Load", str(_last_full)[:16] if _last_full != "Never" else "Never")
    k2.metric("Last Incremental", str(_last_incr)[:16] if _last_incr != "Never" else "Never")
    k3.metric("Total ETL Runs", str(_run_count))
    k4.metric("Archives Created", str(_arcs))

    # Table row counts from state
    if _wm:
        st.markdown(_h3("📊 Table Row Counts (from last ETL run)",STEEL), unsafe_allow_html=True)
        _wm_df = pd.DataFrame([{"Table":k,"Rows Loaded":f"{v:,}"} for k,v in sorted(_wm.items())])
        st.dataframe(_wm_df, use_container_width=True, height=320, hide_index=True)
    else:
        st.info("Run the ETL pipeline in the Academy tab to see real pipeline state here.")

    # Mock pipeline step timings
    st.markdown(_h3("⏱️ Last Run Step Timings (simulated)",TEAL), unsafe_allow_html=True)
    _steps = ["Schema Setup","Raw Ingest","DQ Checks","Staging ETL","dim_date","dim_customer","dim_vehicle","dim_driver","dim_fleet","fact_trips","fact_payments","fact_operations","Export"]
    _times = [0.1,0.3,2.1,4.2,0.8,1.2,0.9,0.7,0.5,3.1,1.8,2.3,0.4]
    _step_df = pd.DataFrame({"Step":_steps,"Duration (s)":_times,"Status":["✅"]*len(_steps)})
    fig_steps = px.bar(_step_df, x="Step", y="Duration (s)", template="plotly_dark",
                       color="Duration (s)", color_continuous_scale=["#2A9D8F","#E9C46A","#E63946"],
                       title="ETL Step Duration (seconds)")
    fig_steps.update_layout(height=280,paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",margin=dict(t=40,b=60,l=0,r=0),showlegend=False)
    st.plotly_chart(fig_steps, use_container_width=True)

# ── TAB 1: RUN HISTORY ───────────────────────────────────────────────────────
with TAB[1]:
    st.markdown(_h2("ETL Run History","📈"), unsafe_allow_html=True)
    random.seed(42)
    now = datetime.now()
    _hist_rows = []
    for i in range(30):
        _dt = now - timedelta(days=i, hours=random.randint(0,3))
        _rows = random.randint(17000,18500)
        _dur  = random.uniform(8,22)
        _errs = random.choices([0,0,0,0,1,2,3], k=1)[0]
        _hist_rows.append({"Run #":30-i,"Timestamp":_dt.strftime("%Y-%m-%d %H:%M"),"Type":random.choice(["Full","Incremental","Incremental"]),
                           "Rows Loaded":f"{_rows:,}","Duration (s)":round(_dur,1),"DQ Errors":_errs,
                           "Status":"✅ Success" if _errs<3 else "⚠️ Warning"})
    _hist_df = pd.DataFrame(_hist_rows)
    st.dataframe(_hist_df, use_container_width=True, height=350, hide_index=True)

    # Row count trend
    _trend = [{"Run":r["Run #"],"Rows":int(r["Rows Loaded"].replace(",","")),"Errors":r["DQ Errors"]} for r in _hist_rows]
    _trend_df = pd.DataFrame(_trend)
    fig_trend = px.line(_trend_df, x="Run", y="Rows", title="Row Count Trend Across Runs", template="plotly_dark", color_discrete_sequence=[TEAL])
    fig_trend.add_scatter(x=_trend_df["Run"], y=_trend_df["Errors"]*1000+17000, mode="markers", marker=dict(color=BRAND, size=8), name="DQ Errors (×1000)")
    fig_trend.update_layout(height=280,paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",margin=dict(t=40,b=0,l=0,r=0))
    st.plotly_chart(fig_trend, use_container_width=True)

# ── TAB 2: ANOMALY DETECTION ─────────────────────────────────────────────────
with TAB[2]:
    st.markdown(_h2("Anomaly Detection","🚨"), unsafe_allow_html=True)
    st.markdown(_card("Data anomalies = unexpected changes in row counts, null rates, or metric values. Detect them before they reach dashboards.",l=BRAND), unsafe_allow_html=True)

    trips_df = dfs["trips"].copy()
    trips_df["pickup_datetime"] = pd.to_datetime(trips_df["pickup_datetime"], errors="coerce")
    trips_df["trip_fare_pkr"]   = pd.to_numeric(trips_df["trip_fare_pkr"], errors="coerce").fillna(0)

    _monthly = trips_df.groupby(trips_df["pickup_datetime"].dt.to_period("M")).agg(
        trips=("trip_id","count"), revenue=("trip_fare_pkr","sum")).reset_index()
    _monthly["month"] = _monthly["pickup_datetime"].astype(str)
    _monthly = _monthly[_monthly["trips"]>0]

    if len(_monthly) > 3:
        _mean = _monthly["trips"].mean(); _std = _monthly["trips"].std()
        _monthly["z_score"] = (_monthly["trips"] - _mean) / _std
        _monthly["anomaly"] = _monthly["z_score"].abs() > 2
        fig_anom = px.line(_monthly, x="month", y="trips", title="Monthly Trip Count — Anomaly Detection", template="plotly_dark", color_discrete_sequence=[TEAL])
        _anom = _monthly[_monthly["anomaly"]]
        if len(_anom): fig_anom.add_scatter(x=_anom["month"], y=_anom["trips"], mode="markers", marker=dict(color=BRAND,size=12,symbol="x"), name="Anomaly (|z|>2)")
        fig_anom.add_hline(y=_mean+2*_std, line_dash="dash", line_color=AMBER, annotation_text="+2σ")
        fig_anom.add_hline(y=max(0,_mean-2*_std), line_dash="dash", line_color=AMBER, annotation_text="-2σ")
        fig_anom.update_layout(height=300,paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",margin=dict(t=40,b=60,l=0,r=0))
        st.plotly_chart(fig_anom, use_container_width=True)
        if len(_anom): st.warning(f"⚠️ {len(_anom)} anomalous month(s) detected (|z-score| > 2)")
        else: st.success("✅ No statistical anomalies detected in trip counts")

    st.markdown(_h3("📝 Anomaly Detection SQL Pattern",STEEL), unsafe_allow_html=True)
    st.code("""-- Z-score anomaly detection: flag months where row count is >2σ from mean
WITH monthly_counts AS (
    SELECT DATE_TRUNC('month', pickup_datetime::DATE) AS month,
           COUNT(*) AS trip_count
    FROM trips GROUP BY 1
),
stats AS (
    SELECT AVG(trip_count) AS mean_count,
           STDDEV(trip_count) AS std_count
    FROM monthly_counts
)
SELECT month, trip_count,
    ROUND((trip_count - s.mean_count) / NULLIF(s.std_count, 0), 2) AS z_score,
    CASE WHEN ABS((trip_count - s.mean_count) / NULLIF(s.std_count, 0)) > 2
         THEN '⚠️ ANOMALY' ELSE '✅ Normal' END AS status
FROM monthly_counts, stats s
ORDER BY month;""", language="sql")

# ── TAB 3: SLA TRACKING ──────────────────────────────────────────────────────
with TAB[3]:
    st.markdown(_h2("SLA Tracking","⏱️"), unsafe_allow_html=True)
    SLAS = [
        {"Pipeline":"Full ETL Load","SLA":"Complete by 06:00 daily","Target (min)":25,"Actual (min)":18,"Status":"✅ Within SLA"},
        {"Pipeline":"Incremental Load","SLA":"Complete within 5 mins","Target (min)":5,"Actual (min)":3,"Status":"✅ Within SLA"},
        {"Pipeline":"DQ Checks","SLA":"Complete by 06:30","Target (min)":10,"Actual (min)":7,"Status":"✅ Within SLA"},
        {"Pipeline":"Dashboard Refresh","SLA":"Data < 1 hour old by 7am","Target (min)":60,"Actual (min)":45,"Status":"✅ Within SLA"},
        {"Pipeline":"Stream Batch","SLA":"Process within 2 minutes","Target (min)":2,"Actual (min)":2.8,"Status":"⚠️ SLA Breach"},
    ]
    sla_df = pd.DataFrame(SLAS)
    st.dataframe(sla_df, use_container_width=True, height=200, hide_index=True)
    _breach = len(sla_df[sla_df["Status"].str.contains("Breach")])
    if _breach: st.error(f"⚠️ {_breach} SLA breach(es) detected!")
    else: st.success("✅ All pipelines within SLA")

# ── TAB 4: DATA FRESHNESS ────────────────────────────────────────────────────
with TAB[4]:
    st.markdown(_h2("Data Freshness Monitor","💧"), unsafe_allow_html=True)
    _tables = ["trips","customers","vehicles","invoices","fuel_logs","maintenance","telematics"]
    _fresh_rows = []
    for tbl in _tables:
        df = dfs.get(tbl, pd.DataFrame())
        _dt_cols = [c for c in df.columns if "date" in c.lower() or "time" in c.lower()]
        if _dt_cols:
            _latest = pd.to_datetime(df[_dt_cols[0]], errors="coerce").max()
            if pd.notna(_latest):
                _hrs = (datetime.now() - _latest.to_pydatetime().replace(tzinfo=None)).total_seconds()/3600
                _fresh_rows.append({"Table":tbl,"Latest Record":str(_latest)[:16],"Age (hrs)":round(_hrs,1),"Status":"✅ Fresh" if _hrs<25 else "⚠️ Stale" if _hrs<168 else "❌ Very Stale"})
    if _fresh_rows:
        st.dataframe(pd.DataFrame(_fresh_rows), use_container_width=True, height=280, hide_index=True)

# ── TAB 5: CONCEPTS ──────────────────────────────────────────────────────────
with TAB[5]:
    st.markdown(_h2("Observability Concepts","📚"), unsafe_allow_html=True)
    obs_concepts = [
        ("Data Observability","The ability to fully understand, monitor, and resolve data quality issues across the data pipeline. The '4 pillars': Freshness, Volume, Schema, Distribution.",BRAND),
        ("Data Contracts","Formal agreement between data producer and consumer: 'This table will always have these columns, these types, and these constraints.' Enables autonomous pipelines.",TEAL),
        ("Circuit Breaker","Stop the pipeline if DQ drops below threshold. Don't propagate bad data downstream. Fail fast, fix at source.",AMBER),
        ("Idempotency","Running a pipeline multiple times gives the same result. Essential for safe retries. Use INSERT OR REPLACE, not INSERT.",STEEL),
        ("Lineage Tracking","Know exactly which upstream source caused a downstream metric to change. 'Why is revenue lower today?' → trace to source.",PUR),
        ("Alerting Thresholds","Row count drops >20% → alert. Null rate increases >5% → alert. SLA missed → page on-call. Set thresholds based on historical data.",ORANGE),
    ]
    c1,c2 = st.columns(2)
    for i,(t,d,c) in enumerate(obs_concepts):
        (c1 if i%2==0 else c2).markdown(_card(f'<b style="color:{c};font-size:.82rem;">{t}</b><br><span style="font-size:.74rem;color:{TEXT};">{d}</span>',l=c,p="10px 14px"), unsafe_allow_html=True)
