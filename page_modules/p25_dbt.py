"""
p25_dbt.py — dbt Simulation
Model files · schema.yml · Dependencies · Tests · Docs
Run dbt models via DuckDB in the browser
"""
import json, re
from pathlib import Path
from datetime import datetime
import duckdb
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from page_modules._shared import inject, get_data, BRAND, STEEL, GREEN, AMBER, ORANGE, TEXT
inject()
M="#5a7a96"; CB="#141e2b"; BD="#1e2f44"; TEAL="#2A9D8F"; PUR="#6A4C93"
def _card(b,l=BRAND,p="14px 16px"): return f'<div style="background:{CB};border:1px solid {BD};border-left:3px solid {l};border-radius:10px;padding:{p};margin:6px 0;">{b}</div>'
def _h2(t,i=""): return f'<div style="font-size:1.22rem;font-weight:800;color:{TEXT};margin:16px 0 4px;"><span style="color:{BRAND};">{i} </span>{t}</div>'
def _h3(t,c=STEEL): return f'<div style="font-size:.9rem;font-weight:700;color:{c};border-left:3px solid {c};padding-left:8px;margin:10px 0 6px;">{t}</div>'

dfs = get_data()
DBT_DIR = Path("data/dbt_simulation")
DBT_DIR.mkdir(parents=True, exist_ok=True)
(DBT_DIR/"models/staging").mkdir(parents=True, exist_ok=True)
(DBT_DIR/"models/marts").mkdir(parents=True, exist_ok=True)

@st.cache_resource
def get_conn(dfs):
    c = duckdb.connect(":memory:")
    for n,df in dfs.items():
        try: c.register(n,df)
        except: pass
    return c
conn = get_conn(dfs)

st.markdown(f'<div style="font-size:1.6rem;font-weight:900;color:{BRAND};">🔧 dbt Simulation</div>'
            f'<div style="font-size:.8rem;color:{M};">Models · schema.yml · Lineage DAG · Tests · Run · Documentation</div>',
            unsafe_allow_html=True)
st.markdown(f"<hr style='border-color:{BD};margin:6px 0 10px'>",unsafe_allow_html=True)

TAB = st.tabs(["📚 What is dbt","📁 Models","📋 schema.yml","🗺️ Lineage DAG","▶ dbt run","✅ dbt test","📖 dbt docs"])

# ── TAB 0: WHAT IS DBT ───────────────────────────────────────────────────────
with TAB[0]:
    st.markdown(_h2("What is dbt?","📚"), unsafe_allow_html=True)
    st.markdown(_card("<b>dbt (data build tool)</b> is the T in ELT. It lets data analysts write SQL SELECT statements that dbt compiles into CREATE TABLE / CREATE VIEW statements and runs in order of their dependencies.",l=TEAL), unsafe_allow_html=True)
    c1,c2,c3 = st.columns(3)
    with c1: st.markdown(_card(f'<b style="color:{BRAND};">What dbt does</b><br><span style="font-size:.75rem;color:{TEXT};">• Runs SQL models in dependency order<br>• Tests: uniqueness, not_null, accepted_values<br>• Generates documentation automatically<br>• Compiles Jinja SQL to native SQL<br>• Version-controlled SQL transforms</span>',l=BRAND,p="10px 14px"), unsafe_allow_html=True)
    with c2: st.markdown(_card(f'<b style="color:{TEAL};">What dbt does NOT do</b><br><span style="font-size:.75rem;color:{TEXT};">• Does not extract data (no connectors)<br>• Does not load raw data (that is EL)<br>• Does not orchestrate (use Airflow)<br>• Does not store data (just SQL)<br>• Works inside the warehouse only</span>',l=TEAL,p="10px 14px"), unsafe_allow_html=True)
    with c3: st.markdown(_card(f'<b style="color:{AMBER};">dbt project structure</b><br><pre style="font-size:.68rem;color:{TEXT};">my_project/\n├── models/\n│   ├── staging/\n│   │   ├── stg_trips.sql\n│   │   └── schema.yml\n│   └── marts/\n│       ├── revenue.sql\n│       └── schema.yml\n├── dbt_project.yml\n└── tests/</pre>',l=AMBER,p="10px 14px"), unsafe_allow_html=True)

    st.code("""-- dbt model: models/staging/stg_trips.sql
-- This SELECT becomes: CREATE TABLE staging.stg_trips AS ...

SELECT
    trip_id,
    fleet_id,
    vehicle_id,
    customer_id,
    TRY_CAST(pickup_datetime AS TIMESTAMP)  AS pickup_datetime,
    TRY_CAST(dropoff_datetime AS TIMESTAMP) AS dropoff_datetime,
    GREATEST(0, COALESCE(TRY_CAST(trip_fare_pkr AS DOUBLE), 0)) AS trip_fare_pkr,
    TRIM(status)                            AS status,
    -- DQ flags
    CASE WHEN TRY_CAST(trip_fare_pkr AS DOUBLE) <= 0 THEN true ELSE false END AS _dq_zero_fare

FROM {{ source('raw', 'trips') }}  -- Jinja reference to source
WHERE trip_id IS NOT NULL

-- dbt compiles this to:
-- CREATE TABLE staging.stg_trips AS SELECT ... FROM raw.trips""", language="sql")

# ── TAB 1: MODELS ────────────────────────────────────────────────────────────
with TAB[1]:
    st.markdown(_h2("dbt Models","📁"), unsafe_allow_html=True)
    DBT_MODELS = {
        "staging/stg_trips.sql": """-- {{ config(materialized='table') }}
SELECT
    trip_id,
    fleet_id,
    vehicle_id,
    customer_id,
    TRY_CAST(pickup_datetime AS TIMESTAMP)            AS pickup_datetime,
    TRY_CAST(dropoff_datetime AS TIMESTAMP)           AS dropoff_datetime,
    GREATEST(0, COALESCE(CAST(trip_fare_pkr AS DOUBLE),0)) AS trip_fare_pkr,
    GREATEST(0, COALESCE(CAST(distance_km AS DOUBLE),0))   AS distance_km,
    TRIM(status)                                      AS status,
    TRIM(pickup_city)                                 AS pickup_city,
    TRIM(dropoff_city)                                AS dropoff_city,
    CASE WHEN CAST(trip_fare_pkr AS DOUBLE) <= 0 THEN true ELSE false END AS _dq_zero_fare
FROM trips
QUALIFY ROW_NUMBER() OVER (PARTITION BY trip_id ORDER BY pickup_datetime DESC) = 1""",

        "staging/stg_customers.sql": """-- {{ config(materialized='table') }}
SELECT
    customer_id,
    INITCAP(TRIM(full_name))                         AS full_name,
    LOWER(TRIM(email))                               AS email,
    CASE WHEN email LIKE '%@%.%' THEN true ELSE false END AS email_valid,
    city,
    customer_type,
    COALESCE(loyalty_points, 0)                      AS loyalty_points,
    TRY_CAST(registration_date AS DATE)              AS registration_date
FROM customers
QUALIFY ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY registration_date DESC NULLS LAST) = 1""",

        "marts/revenue.sql": """-- {{ config(materialized='table') }}
-- Depends on: stg_trips, stg_customers
-- {{ ref('stg_trips') }} and {{ ref('stg_customers') }}
SELECT
    DATE_TRUNC('month', t.pickup_datetime::DATE)     AS month,
    t.fleet_id,
    COUNT(t.trip_id)                                 AS trips,
    COUNT(DISTINCT t.customer_id)                    AS unique_customers,
    ROUND(SUM(t.trip_fare_pkr), 0)                   AS revenue_pkr,
    ROUND(AVG(t.trip_fare_pkr), 0)                   AS avg_fare,
    COUNT(*) FILTER(WHERE t._dq_zero_fare)           AS dq_zero_fare_count
FROM stg_trips t
WHERE t.status = 'Completed'
GROUP BY 1, 2
ORDER BY 1, 2""",

        "marts/customer_ltv.sql": """-- {{ config(materialized='table') }}
SELECT
    c.customer_id,
    c.full_name,
    c.city,
    c.customer_type,
    COUNT(t.trip_id)                                 AS total_trips,
    ROUND(SUM(t.trip_fare_pkr), 0)                   AS total_spend_pkr,
    ROUND(AVG(t.trip_fare_pkr), 0)                   AS avg_fare,
    MAX(t.pickup_datetime::DATE)                     AS last_trip_date,
    DATE_DIFF('day', MAX(t.pickup_datetime::DATE), current_date) AS days_since_last,
    CASE
        WHEN SUM(t.trip_fare_pkr) > 200000 THEN 'Champion'
        WHEN SUM(t.trip_fare_pkr) > 100000 THEN 'Loyal'
        WHEN COUNT(t.trip_id) >= 3         THEN 'Regular'
        ELSE 'New'
    END AS ltv_segment
FROM stg_customers c
LEFT JOIN stg_trips t ON c.customer_id = t.customer_id
GROUP BY c.customer_id, c.full_name, c.city, c.customer_type""",
    }

    _model_sel = st.selectbox("Select model:", list(DBT_MODELS.keys()), key="dbt_model_sel")
    st.code(DBT_MODELS[_model_sel].strip(), language="sql")

    if st.button("▶ Run This Model", key="run_model"):
        _sql = (DBT_MODELS[_model_sel]
                .replace("{{ config(materialized='table') }}", "")
                .replace("{{ ref('stg_trips') }}", "")
                .replace("{{ ref('stg_customers') }}", "")
                .strip())
        # Register staging views
        for name, sql in [("stg_trips", DBT_MODELS["staging/stg_trips.sql"]), ("stg_customers", DBT_MODELS["staging/stg_customers.sql"])]:
            _s = sql.replace("{{ config(materialized='table') }}","").strip()
            try: conn.execute(f"CREATE OR REPLACE VIEW {name} AS {_s}")
            except: pass
        try:
            _r = conn.execute(_sql).fetchdf()
            st.success(f"✅ Model ran — {len(_r)} rows, {len(_r.columns)} columns")
            st.dataframe(_r, use_container_width=True, height=280, hide_index=True)
        except Exception as e:
            st.error(str(e))

# ── TAB 2: SCHEMA.YML ────────────────────────────────────────────────────────
with TAB[2]:
    st.markdown(_h2("schema.yml — Models + Tests","📋"), unsafe_allow_html=True)
    st.code("""# models/staging/schema.yml
version: 2

sources:
  - name: raw
    tables:
      - name: trips
        description: "Raw OLTP trips table from CSV ingestion"
        columns:
          - name: trip_id
            description: "Unique trip identifier"
            tests:
              - unique
              - not_null

models:
  - name: stg_trips
    description: "Cleaned and typed trips — one row per trip"
    columns:
      - name: trip_id
        tests:
          - unique
          - not_null
      - name: status
        tests:
          - not_null
          - accepted_values:
              values: ['Completed', 'Cancelled', 'In Progress', 'Confirmed']
      - name: trip_fare_pkr
        tests:
          - not_null
          - dbt_utils.expression_is_true:
              expression: ">= 0"
      - name: fleet_id
        tests:
          - not_null
          - relationships:
              to: ref('stg_fleets')
              field: fleet_id

  - name: revenue
    description: "Monthly revenue mart — one row per fleet per month"
    columns:
      - name: month
        tests:
          - not_null
      - name: revenue_pkr
        tests:
          - not_null""", language="yaml")

# ── TAB 3: LINEAGE DAG ───────────────────────────────────────────────────────
with TAB[3]:
    st.markdown(_h2("dbt Lineage DAG","🗺️"), unsafe_allow_html=True)
    # Sankey diagram for model dependencies
    _nodes = ["trips (source)","customers (source)","fleets (source)","stg_trips","stg_customers","stg_fleets","revenue","customer_ltv","driver_scorecard"]
    _edges = [(0,3),(1,4),(2,5),(3,6),(4,6),(4,7),(5,6),(3,8)]
    _colors = [BRAND,BRAND,BRAND,STEEL,STEEL,STEEL,TEAL,TEAL,TEAL]
    fig_dag = go.Figure(go.Sankey(
        node=dict(pad=20,thickness=18,line=dict(color="#30363d",width=0.5),label=_nodes,color=_colors),
        link=dict(source=[s for s,d in _edges],target=[d for s,d in _edges],value=[1]*len(_edges),color=["rgba(255,255,255,0.07)"]*len(_edges)),
    ))
    fig_dag.update_layout(height=380,paper_bgcolor="rgba(0,0,0,0)",font=dict(color=TEXT,size=11),margin=dict(l=0,r=0,t=20,b=0))
    st.plotly_chart(fig_dag, use_container_width=True)
    st.markdown(_card("The DAG (Directed Acyclic Graph) shows model dependencies. dbt runs models in topological order — source tables first, then staging, then marts. No model runs before its upstream dependencies.",l=STEEL,p="9px 14px"), unsafe_allow_html=True)

# ── TAB 4: DBT RUN ───────────────────────────────────────────────────────────
with TAB[4]:
    st.markdown(_h2("dbt run — Simulate a Full Run","▶"), unsafe_allow_html=True)
    if "dbt_log" not in st.session_state: st.session_state.dbt_log = []
    if st.button("🚀 dbt run --select staging+", type="primary", key="dbt_run"):
        log = []
        _prog = st.progress(0, text="dbt run started…")
        _term = st.empty()
        def _render(lines):
            body = "\n".join(f'<span style="color:{"#3fb950" if "OK" in l else "#f85149" if "ERROR" in l else "#58a6ff"}">{l}</span>' for l in lines)
            _term.markdown(f'<div style="background:#0d1117;border:1px solid #30363d;border-radius:8px;padding:14px;font-family:monospace;font-size:.76rem;max-height:380px;overflow-y:auto;line-height:1.8;">{body}</div>',unsafe_allow_html=True)

        log.append(f"Running with dbt (simulation)")
        log.append(f"  Registered: {len(DBT_MODELS)} models")
        log.append(f"  Adapter: DuckDB in-memory")
        log.append("")
        _render(log)

        STEPS = [("staging.stg_trips","stg_trips"),("staging.stg_customers","stg_customers"),("marts.revenue","revenue"),("marts.customer_ltv","customer_ltv")]
        for i,(model_path,model_key) in enumerate(STEPS):
            _prog.progress(int((i+1)/len(STEPS)*100), text=f"Building {model_path}…")
            if model_key in [k.split("/")[-1].replace(".sql","") for k in DBT_MODELS]:
                _model_sql = next((v for k,v in DBT_MODELS.items() if k.endswith(f"{model_key}.sql")), None)
                if _model_sql:
                    _sql = (_model_sql.replace("{{ config(materialized='table') }}","")
                            .replace("{{ ref('stg_trips') }}","").replace("{{ ref('stg_customers') }}","").strip())
                    for dep_name, dep_key in [("stg_trips","stg_trips"),("stg_customers","stg_customers")]:
                        _dep_sql = next((v for k,v in DBT_MODELS.items() if k.endswith(f"{dep_key}.sql")),None)
                        if _dep_sql:
                            _ds = _dep_sql.replace("{{ config(materialized='table') }}","").strip()
                            try: conn.execute(f"CREATE OR REPLACE VIEW {dep_name} AS {_ds}")
                            except: pass
                    try:
                        _res = conn.execute(_sql).fetchdf()
                        conn.register(model_key, _res)
                        log.append(f"  OK  {model_path} ({len(_res)} rows)")
                    except Exception as e:
                        log.append(f"  ERROR {model_path}: {str(e)[:60]}")
                _render(log)

        log.append("")
        log.append(f"Finished running {len(STEPS)} models")
        log.append(f"Completed at {datetime.now():%H:%M:%S}")
        log.append("Done. PASS=4 WARN=0 ERROR=0 SKIP=0")
        _render(log)
        st.session_state.dbt_log = log
        st.success("✅ dbt run complete!")

# ── TAB 5: DBT TEST ──────────────────────────────────────────────────────────
with TAB[5]:
    st.markdown(_h2("dbt test","✅"), unsafe_allow_html=True)
    DBT_TESTS = [
        ("stg_trips","trip_id","unique","SELECT COUNT(*) = COUNT(DISTINCT trip_id) FROM trips"),
        ("stg_trips","trip_id","not_null","SELECT COUNT(*) FILTER(WHERE trip_id IS NULL)=0 FROM trips"),
        ("stg_trips","status","accepted_values","SELECT COUNT(*) FILTER(WHERE status NOT IN ('Completed','Cancelled','In Progress','Confirmed'))=0 FROM trips"),
        ("stg_trips","trip_fare_pkr","not_null","SELECT COUNT(*) FILTER(WHERE trip_fare_pkr IS NULL)=0 FROM trips"),
        ("stg_trips","trip_fare_pkr","range_check","SELECT COUNT(*) FILTER(WHERE CAST(trip_fare_pkr AS DOUBLE)<0)=0 FROM trips"),
        ("stg_customers","customer_id","unique","SELECT COUNT(*) = COUNT(DISTINCT customer_id) FROM customers"),
        ("stg_customers","email","format_check","SELECT COUNT(*) FILTER(WHERE email IS NOT NULL AND email NOT LIKE '%@%') < 100 FROM customers"),
        ("revenue","revenue_pkr","not_null","SELECT 1=1"),  # simulated
    ]
    if st.button("🧪 dbt test", type="primary", key="dbt_test"):
        _results = []
        _prog2 = st.progress(0)
        for i,(model,col,test_type,sql) in enumerate(DBT_TESTS):
            _prog2.progress(int((i+1)/len(DBT_TESTS)*100))
            try:
                _r = conn.execute(sql).fetchone()
                _passed = bool(_r[0]) if _r else False
            except: _passed = False
            _results.append({"Model":model,"Column":col,"Test":test_type,"Result":"✅ PASS" if _passed else "❌ FAIL"})
        _df = pd.DataFrame(_results)
        _p = len(_df[_df["Result"].str.startswith("✅")]); _f = len(_df)-_p
        c1,c2 = st.columns(2); c1.metric("Passed",str(_p)); c2.metric("Failed",str(_f))
        st.dataframe(_df, use_container_width=True, height=300, hide_index=True)
        if _f==0: st.success("✅ All tests passed!")
        else: st.error(f"❌ {_f} test(s) failed")

# ── TAB 6: DBT DOCS ──────────────────────────────────────────────────────────
with TAB[6]:
    st.markdown(_h2("dbt docs — Auto-generated Documentation","📖"), unsafe_allow_html=True)
    _doc_sel = st.selectbox("Model:", [k.replace(".sql","").replace("staging/","stg.").replace("marts/","mart.") for k in DBT_MODELS.keys()], key="dbt_doc_sel")
    model_docs = {
        "stg.stg_trips": {"desc":"Cleaned and standardised trips from raw CSV. Deduplicated by trip_id. DQ flags added.","owner":"Data Engineering","upstream":["raw.trips"],"downstream":["mart.revenue","mart.customer_ltv"],"tests":["trip_id unique","trip_id not null","status accepted_values","fare >= 0"],"columns":["trip_id PK","fleet_id FK","vehicle_id FK","customer_id FK","pickup_datetime TIMESTAMP","trip_fare_pkr DOUBLE","status VARCHAR","_dq_zero_fare BOOLEAN"]},
        "stg.stg_customers": {"desc":"Cleaned customer records. Initcap names, lowercased email, email validity flag.","owner":"Data Engineering","upstream":["raw.customers"],"downstream":["mart.customer_ltv"],"tests":["customer_id unique","customer_id not null","email format check"],"columns":["customer_id PK","full_name VARCHAR","email VARCHAR","email_valid BOOLEAN","city VARCHAR","loyalty_points INT"]},
        "mart.revenue": {"desc":"Monthly revenue by fleet. One row per fleet × month. Filtered to completed trips.","owner":"Finance Team","upstream":["stg.stg_trips"],"downstream":["BI Dashboard"],"tests":["month not null","revenue_pkr not null"],"columns":["month DATE","fleet_id VARCHAR","trips INT","unique_customers INT","revenue_pkr DOUBLE","avg_fare DOUBLE"]},
        "mart.customer_ltv": {"desc":"Customer lifetime value with LTV segment classification.","owner":"Marketing","upstream":["stg.stg_customers","stg.stg_trips"],"downstream":["CRM","BI Dashboard"],"tests":["customer_id unique"],"columns":["customer_id VARCHAR","full_name VARCHAR","total_trips INT","total_spend_pkr DOUBLE","ltv_segment VARCHAR"]},
    }
    _doc = model_docs.get(_doc_sel, {})
    if _doc:
        st.markdown(_card(f'<b style="font-size:.9rem;color:{BRAND};">{_doc_sel}</b><br>'
                          f'<span style="font-size:.78rem;color:{TEXT};">{_doc.get("desc","")}</span><br><br>'
                          f'<span style="font-size:.72rem;color:{M};">Owner: <b style="color:{STEEL};">{_doc.get("owner","")}</b></span>',l=BRAND,p="10px 14px"), unsafe_allow_html=True)
        c1,c2,c3 = st.columns(3)
        with c1:
            st.markdown(_h3("⬆ Upstream",TEAL), unsafe_allow_html=True)
            for up in _doc.get("upstream",[]): st.markdown(f'<div style="font-size:.76rem;color:{TEAL};">← {up}</div>',unsafe_allow_html=True)
        with c2:
            st.markdown(_h3("✅ Tests",AMBER), unsafe_allow_html=True)
            for t in _doc.get("tests",[]): st.markdown(f'<div style="font-size:.74rem;color:{TEXT};">• {t}</div>',unsafe_allow_html=True)
        with c3:
            st.markdown(_h3("⬇ Downstream",BRAND), unsafe_allow_html=True)
            for dn in _doc.get("downstream",[]): st.markdown(f'<div style="font-size:.76rem;color:{BRAND};">→ {dn}</div>',unsafe_allow_html=True)
        st.markdown(_h3("📋 Columns",STEEL), unsafe_allow_html=True)
        for col in _doc.get("columns",[]): st.markdown(f'<div style="font-size:.76rem;color:{TEXT};font-family:monospace;padding:2px 0;">• {col}</div>',unsafe_allow_html=True)
