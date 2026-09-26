"""
p23_interview.py — Data Engineering Interview Prep
SQL questions · System design · Python scenarios · Scenario problems
Real answers using Rent-A-Car data
"""
import pandas as pd
import streamlit as st
import duckdb
from page_modules._shared import inject, get_data, BRAND, STEEL, GREEN, AMBER, ORANGE, TEXT
inject()
M="#5a7a96"; CB="#141e2b"; BD="#1e2f44"; TEAL="#2A9D8F"; PUR="#6A4C93"
def _card(b,l=BRAND,p="14px 16px"): return f'<div style="background:{CB};border:1px solid {BD};border-left:3px solid {l};border-radius:10px;padding:{p};margin:6px 0;">{b}</div>'
def _h2(t,i=""): return f'<div style="font-size:1.22rem;font-weight:800;color:{TEXT};margin:16px 0 4px;"><span style="color:{BRAND};">{i} </span>{t}</div>'
def _h3(t,c=STEEL): return f'<div style="font-size:.9rem;font-weight:700;color:{c};border-left:3px solid {c};padding-left:8px;margin:10px 0 6px;">{t}</div>'

dfs = get_data()

st.markdown(f'<div style="font-size:1.6rem;font-weight:900;color:{BRAND};">🎯 Interview Prep</div>'
            f'<div style="font-size:.8rem;color:{M};">SQL questions · System design · Python · Behavioural · Live answers on real data</div>',
            unsafe_allow_html=True)
st.markdown(f"<hr style='border-color:{BD};margin:6px 0 10px'>",unsafe_allow_html=True)

TAB = st.tabs(["💼 SQL Questions","🏗️ System Design","🐍 Python Questions","🧩 Scenario Problems","💬 Behavioural","📋 Study Plan"])

# ── TAB 0: SQL QUESTIONS ─────────────────────────────────────────────────────
with TAB[0]:
    st.markdown(_h2("SQL Interview Questions","💼"), unsafe_allow_html=True)
    SQL_QS = [
        {
            "q": "Find customers who made their first booking in 2025 AND have made at least 3 trips total.",
            "difficulty": "Medium",
            "concepts": ["CTE","GROUP BY","HAVING","DATE functions"],
            "answer": """WITH first_booking AS (
    SELECT customer_id,
           MIN(pickup_datetime::DATE) AS first_trip_date
    FROM trips WHERE status = 'Completed'
    GROUP BY customer_id
    HAVING MIN(pickup_datetime::DATE) >= '2025-01-01'
       AND MIN(pickup_datetime::DATE) <  '2026-01-01'
),
trip_counts AS (
    SELECT customer_id, COUNT(*) AS total_trips
    FROM trips WHERE status = 'Completed'
    GROUP BY customer_id
    HAVING COUNT(*) >= 3
)
SELECT fb.customer_id, c.full_name, fb.first_trip_date, tc.total_trips
FROM first_booking fb
JOIN trip_counts tc ON fb.customer_id = tc.customer_id
JOIN customers c    ON fb.customer_id = c.customer_id
ORDER BY tc.total_trips DESC;""",
        },
        {
            "q": "For each fleet, find the month with the highest revenue. Show fleet, month, revenue, and what % of annual revenue that month represents.",
            "difficulty": "Hard",
            "concepts": ["Window Functions","QUALIFY","CTEs","ROLLUP"],
            "answer": """WITH monthly_rev AS (
    SELECT fleet_id,
           DATE_TRUNC('month', pickup_datetime::DATE) AS month,
           SUM(trip_fare_pkr) AS revenue
    FROM trips WHERE status='Completed'
    GROUP BY 1, 2
),
annual_rev AS (
    SELECT fleet_id, DATE_PART('year',month::DATE)::INT AS yr,
           SUM(revenue) AS annual_revenue
    FROM monthly_rev GROUP BY 1, 2
)
SELECT m.fleet_id, m.month,
    ROUND(m.revenue, 0) AS monthly_revenue,
    ROUND(m.revenue * 100.0 / a.annual_revenue, 1) AS pct_of_annual,
    ROW_NUMBER() OVER (PARTITION BY m.fleet_id ORDER BY m.revenue DESC) AS rank_in_fleet
FROM monthly_rev m
JOIN annual_rev a ON m.fleet_id = a.fleet_id
                 AND DATE_PART('year',m.month::DATE) = a.yr
QUALIFY rank_in_fleet = 1
ORDER BY monthly_revenue DESC;""",
        },
        {
            "q": "Write a query to detect duplicate customer records based on email address. Show which duplicates exist and which is the oldest (to keep).",
            "difficulty": "Medium",
            "concepts": ["Window Functions","ROW_NUMBER","GROUP BY","HAVING"],
            "answer": """WITH email_dupes AS (
    SELECT email, COUNT(*) AS dupe_count
    FROM customers
    WHERE email IS NOT NULL AND email != ''
    GROUP BY email
    HAVING COUNT(*) > 1
),
ranked_dupes AS (
    SELECT c.customer_id, c.full_name, c.email,
           c.registration_date,
           ROW_NUMBER() OVER (PARTITION BY c.email ORDER BY c.registration_date ASC) AS rn,
           COUNT(*) OVER (PARTITION BY c.email) AS total_dupes
    FROM customers c
    JOIN email_dupes e ON c.email = e.email
)
SELECT customer_id, full_name, email, registration_date,
       CASE WHEN rn = 1 THEN 'KEEP (oldest)' ELSE 'DELETE (duplicate)' END AS action,
       total_dupes
FROM ranked_dupes
ORDER BY email, rn;""",
        },
        {
            "q": "Calculate a 7-day rolling average of daily revenue. Flag days where actual revenue is >20% above or below the rolling average (anomalies).",
            "difficulty": "Hard",
            "concepts": ["Window Functions","Moving Average","CASE","CTEs"],
            "answer": """WITH daily_rev AS (
    SELECT pickup_datetime::DATE AS trip_date,
           SUM(trip_fare_pkr) AS revenue
    FROM trips WHERE status='Completed'
    GROUP BY 1
),
with_rolling AS (
    SELECT trip_date, revenue,
        AVG(revenue) OVER (
            ORDER BY trip_date
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) AS rolling_7d_avg
    FROM daily_rev
)
SELECT trip_date,
    ROUND(revenue, 0) AS revenue_pkr,
    ROUND(rolling_7d_avg, 0) AS rolling_avg,
    ROUND((revenue - rolling_7d_avg) * 100.0 / NULLIF(rolling_7d_avg,0), 1) AS pct_vs_avg,
    CASE
        WHEN revenue > rolling_7d_avg * 1.20 THEN '📈 Spike (+20%)'
        WHEN revenue < rolling_7d_avg * 0.80 THEN '📉 Drop (-20%)'
        ELSE '✅ Normal'
    END AS anomaly_flag
FROM with_rolling
ORDER BY trip_date DESC;""",
        },
        {
            "q": "Implement an SCD Type 2 merge: given new customer data, expire changed records and insert new versions.",
            "difficulty": "Hard",
            "concepts": ["SCD2","CTE","INSERT","UPDATE","Data Modeling"],
            "answer": """-- STEP 1: Identify changed records
WITH incoming AS (
    SELECT customer_id, full_name, city, customer_type,
           MD5(full_name || city || customer_type) AS hash_new
    FROM staging.stg_customers
),
current_dim AS (
    SELECT customer_id, full_name, city, customer_type,
           MD5(full_name || city || customer_type) AS hash_current,
           customer_sk, valid_from
    FROM dim_customer WHERE is_current = true
),
changed AS (
    SELECT i.customer_id
    FROM incoming i
    JOIN current_dim c ON i.customer_id = c.customer_id
    WHERE i.hash_new != c.hash_current  -- attribute changed
)
-- STEP 2: Expire old records
UPDATE dim_customer
SET valid_to   = current_date - 1,
    is_current = false
WHERE customer_id IN (SELECT customer_id FROM changed)
  AND is_current = true;

-- STEP 3: Insert new versions
INSERT INTO dim_customer (customer_id, full_name, city, customer_type,
                          valid_from, valid_to, is_current)
SELECT i.customer_id, i.full_name, i.city, i.customer_type,
       current_date, '9999-12-31', true
FROM incoming i
WHERE i.customer_id IN (SELECT customer_id FROM changed);""",
        },
    ]

    @st.cache_resource
    def _get_conn(dfs):
        c = duckdb.connect(":memory:")
        for n,df in dfs.items():
            try: c.register(n,df)
            except: pass
        return c
    _conn = _get_conn(dfs)

    for i,q in enumerate(SQL_QS):
        _clr = BRAND if q["difficulty"]=="Hard" else AMBER if q["difficulty"]=="Medium" else TEAL
        with st.expander(f"Q{i+1}: {q['q'][:60]}… [{q['difficulty']}]"):
            st.markdown(_card(f'<b style="color:{_clr};">Q{i+1} [{q["difficulty"]}]</b><br>'
                              f'<span style="font-size:.82rem;color:{TEXT};">{q["q"]}</span><br>'
                              f'<span style="font-size:.7rem;color:{M};">Concepts: {", ".join(q["concepts"])}</span>',l=_clr,p="10px 14px"), unsafe_allow_html=True)
            _show = st.checkbox("Show Answer", key=f"ans_{i}")
            if _show:
                st.code(q["answer"].strip(), language="sql")
                if st.button(f"▶ Run Q{i+1}", key=f"run_q{i}"):
                    try:
                        _r = _conn.execute(q["answer"]).fetchdf()
                        st.dataframe(_r, use_container_width=True, height=240, hide_index=True)
                    except Exception as e:
                        st.error(str(e))

# ── TAB 1: SYSTEM DESIGN ─────────────────────────────────────────────────────
with TAB[1]:
    st.markdown(_h2("System Design Questions","🏗️"), unsafe_allow_html=True)
    DESIGNS = [
        ("Design a data pipeline for a ride-hailing app (like Uber/Careem)",
         """ANSWER FRAMEWORK:
1. Understand requirements:
   - Volume: 1M trips/day, 50GB/day ingestion
   - Latency: Real-time driver tracking (< 5 sec), daily analytics (< 1 hr)
   - Use cases: Live dispatch, daily reports, fraud detection

2. Architecture choice: Lambda (both real-time and batch needed)

3. Data sources:
   - Mobile apps → Kafka events (trip starts, GPS updates, payments)
   - Backend DB → CDC (Debezium) → Kafka
   - External: Weather API, traffic API

4. Batch layer:
   CSVs/Parquet → S3 → Spark/dbt → Redshift/Snowflake
   (Same as our DWH — medallion architecture)

5. Speed layer:
   Kafka → Flink/Spark Streaming → Redis (live driver positions)
   → Aggregations into real-time dashboard

6. Serving layer:
   Merge batch + speed → BI tool (Tableau/Power BI)
   REST API for mobile apps

7. Key tables:
   - fact_trips (grain: 1 trip, daily batch)
   - fact_gps_events (grain: 1 GPS ping, streaming)
   - dim_driver, dim_vehicle, dim_customer

8. Considerations: GDPR (anonymise location after trip), 
   partitioning by date, SCD2 for driver attributes"""),
        ("How would you handle late-arriving data in your pipeline?",
         """ANSWER:
Definition: Data that arrives after the window for that period has already closed.
Example: A trip completed at 11:55pm, but the event arrives at 1:05am next day.

Strategies:

1. WATERMARK APPROACH (most common):
   - Define a grace period: allow data up to 24 hours late
   - Watermark = max(event_time) - grace_period
   - Only close a window after watermark passes it

2. REPROCESSING:
   - Keep raw data forever (bronze layer)
   - When late data arrives, mark those partitions as dirty
   - Reprocess only the affected partitions (not full reload)
   - Use idempotent INSERT OR REPLACE

3. SLOWLY CHANGING FACTS:
   - For accumulating snapshots: allow updates even after "closing"
   - Add updated_at column, allow downstream marts to refresh

4. IN PRACTICE (our platform):
   - Watermark based on row counts (simpler)
   - Incremental load detects new rows regardless of event time
   - Full rebuild available for correctness when needed

Key principle: Event time (when it happened) ≠ Processing time (when we saw it)"""),
    ]
    for q_title, answer in DESIGNS:
        with st.expander(f"**{q_title[:70]}…**"):
            st.markdown(_card(f'<b style="color:{TEAL};">{q_title}</b>',l=TEAL,p="9px 14px"), unsafe_allow_html=True)
            if st.checkbox("Show Answer", key=f"design_{hash(q_title)}"):
                st.code(answer.strip(), language="text")

# ── TAB 2: PYTHON QUESTIONS ──────────────────────────────────────────────────
with TAB[2]:
    st.markdown(_h2("Python Interview Questions","🐍"), unsafe_allow_html=True)
    PY_QS = [
        ("Find the top 3 customers by revenue in each city using pandas",
         """import pandas as pd
trips = dfs["trips"].copy()
customers = dfs["customers"].copy()
trips["trip_fare_pkr"] = pd.to_numeric(trips["trip_fare_pkr"], errors="coerce").fillna(0)
merged = trips[trips["status"]=="Completed"].merge(
    customers[["customer_id","full_name","city"]], on="customer_id")
result = (merged.groupby(["city","customer_id","full_name"])["trip_fare_pkr"]
          .sum().reset_index()
          .sort_values("trip_fare_pkr", ascending=False)
          .groupby("city").head(3)
          .sort_values(["city","trip_fare_pkr"], ascending=[True,False]))
print(result.to_string(index=False))"""),
        ("Detect outliers in trip_fare_pkr using IQR method",
         """import pandas as pd
trips = dfs["trips"].copy()
fares = pd.to_numeric(trips["trip_fare_pkr"], errors="coerce").dropna()
Q1, Q3 = fares.quantile(0.25), fares.quantile(0.75)
IQR = Q3 - Q1
lower, upper = Q1 - 1.5*IQR, Q3 + 1.5*IQR
outliers = trips[(trips["trip_fare_pkr"] < lower) | (trips["trip_fare_pkr"] > upper)]
print(f"Q1={Q1:,.0f}  Q3={Q3:,.0f}  IQR={IQR:,.0f}")
print(f"Fences: [{lower:,.0f}, {upper:,.0f}]")
print(f"Outliers: {len(outliers)} ({len(outliers)/len(trips)*100:.1f}%)")
result = outliers[["trip_id","trip_fare_pkr","pickup_city","status"]].head(10)"""),
        ("Calculate RFM segments and assign customer tiers",
         """import pandas as pd
from datetime import datetime
trips = dfs["trips"].copy()
trips["pickup_datetime"] = pd.to_datetime(trips["pickup_datetime"], errors="coerce")
trips["trip_fare_pkr"]   = pd.to_numeric(trips["trip_fare_pkr"], errors="coerce").fillna(0)
completed = trips[trips["status"]=="Completed"]
snapshot  = completed["pickup_datetime"].max()
rfm = completed.groupby("customer_id").agg(
    Recency=("pickup_datetime", lambda x: (snapshot-x.max()).days),
    Frequency=("trip_id","count"),
    Monetary=("trip_fare_pkr","sum"),
).reset_index()
# Score 1-4
for col in ["Recency","Frequency","Monetary"]:
    asc = col == "Recency"
    rfm[f"{col}_Score"] = pd.qcut(rfm[col], 4,
        labels=[4,3,2,1] if asc else [1,2,3,4], duplicates="drop")
rfm["RFM_Total"] = (rfm["Recency_Score"].astype(int)
                  + rfm["Frequency_Score"].astype(int)
                  + rfm["Monetary_Score"].astype(int))
rfm["Segment"] = pd.cut(rfm["RFM_Total"], [0,4,7,10,12],
    labels=["At Risk","Regular","Loyal","Champion"])
print(rfm["Segment"].value_counts().to_string())
result = rfm.sort_values("RFM_Total", ascending=False).head(10)"""),
    ]
    for q_name, code in PY_QS:
        with st.expander(f"**{q_name}**"):
            st.code(code.strip(), language="python")
            if st.button(f"▶ Run", key=f"py_int_{hash(q_name)}"):
                import io, contextlib, numpy as np
                buf = io.StringIO()
                ns  = {"dfs":dfs,"pd":pd,"np":np,"result":None}
                with contextlib.redirect_stdout(buf):
                    try: exec(compile(code,"<q>","exec"),ns)
                    except Exception as e: print(f"Error: {e}")
                if buf.getvalue(): st.code(buf.getvalue(), language="text")
                if isinstance(ns.get("result"), pd.DataFrame):
                    st.dataframe(ns["result"], use_container_width=True, height=200, hide_index=True)

# ── TAB 3: SCENARIO PROBLEMS ─────────────────────────────────────────────────
with TAB[3]:
    st.markdown(_h2("Scenario-Based Problems","🧩"), unsafe_allow_html=True)
    SCENARIOS = [
        ("Your daily ETL job failed silently — revenue dashboard shows zeros. How do you debug?",
         """DEBUGGING FRAMEWORK:

1. Check the ETL log first:
   SELECT * FROM meta.load_log ORDER BY started_at DESC LIMIT 5;

2. Check if source data exists:
   SELECT COUNT(*) FROM trips WHERE pickup_datetime::DATE = current_date - 1;

3. Check if staging was populated:
   SELECT COUNT(*) FROM staging.stg_trips WHERE _loaded_at::DATE = current_date;

4. Check if facts were loaded:
   SELECT COUNT(*) FROM fact_trips WHERE pickup_date_key = 
   CAST(STRFTIME(current_date - 1, '%Y%m%d') AS INT);

5. Check for schema changes (most common silent failure):
   -- Did source add/remove a column? Check column counts.
   SELECT COUNT(*) FROM information_schema.columns 
   WHERE table_name = 'trips';

6. Check DQ issues:
   SELECT * FROM meta.dq_issues WHERE detected_at::DATE = current_date
   ORDER BY detected_at DESC;

PREVENTION: 
- Add row count validation after each step
- Alert if rows < expected threshold
- Never allow silent failures — log everything"""),
        ("A new data source sends customer data with different field names. How do you integrate it?",
         """INTEGRATION APPROACH:

1. Document the mapping:
   Source field → Target field
   'cust_name' → 'full_name'
   'mob_number' → 'phone'
   'id_number' → 'cnic'

2. Create a source-specific staging transform:
   CREATE OR REPLACE TABLE staging.stg_customers_source2 AS
   SELECT
       'S2-' || customer_code  AS customer_id,  -- prefix to avoid ID collision
       cust_name               AS full_name,
       mob_number              AS phone,
       email_address           AS email,
       'Source2'               AS record_source  -- audit field
   FROM raw.v_customers_source2;

3. UNION into master staging:
   INSERT INTO staging.stg_customers
   SELECT * FROM staging.stg_customers_source2
   WHERE customer_id NOT IN (SELECT customer_id FROM staging.stg_customers);

4. Handle conflicts: same customer in both sources → Master Data Management
   Use CNIC as golden key to deduplicate across sources

5. Track lineage: record_source column shows origin of each record"""),
    ]
    for scenario, answer in SCENARIOS:
        with st.expander(f"**{scenario[:70]}…**"):
            st.markdown(_card(f'<b style="color:{TEAL};">Scenario:</b><br><span style="font-size:.8rem;color:{TEXT};">{scenario}</span>',l=TEAL,p="9px 14px"), unsafe_allow_html=True)
            if st.checkbox("Show Answer", key=f"scen_{hash(scenario)}"):
                st.code(answer.strip(), language="text")

# ── TAB 4: BEHAVIOURAL ───────────────────────────────────────────────────────
with TAB[4]:
    st.markdown(_h2("Behavioural Questions & STAR Method","💬"), unsafe_allow_html=True)
    st.markdown(_card("Use the <b>STAR method</b>: <b>S</b>ituation, <b>T</b>ask, <b>A</b>ction, <b>R</b>esult. Quantify results with numbers.",l=TEAL), unsafe_allow_html=True)
    BEHAVIOURALS = [
        ("Tell me about a time you improved a slow data pipeline.","S: Monthly revenue report took 4 hours to generate.\nT: Reduce to under 30 minutes.\nA: Identified root cause (full table scan on 50M rows). Added date partitioning, pre-aggregated mart layer, replaced DISTINCT with proper dedup using ROW_NUMBER.\nR: Runtime reduced from 4 hours to 18 minutes. Dashboard available by 7am instead of 11am."),
        ("Describe a data quality issue you discovered and fixed.","S: Finance team noticed revenue figures were 15% higher than expected for Q3.\nT: Investigate and fix the discrepancy.\nA: Added DQ check — found duplicate invoices (same trip_id appearing twice due to CDC double-fire). Added QUALIFY ROW_NUMBER() dedup to staging. Implemented invoice uniqueness test.\nR: Revenue corrected. Test added to catch similar issues automatically."),
        ("How do you handle disagreements about data definitions?","S: Marketing defined 'active customer' as anyone who logged in. Data team defined it as anyone who completed a trip in 30 days.\nT: Align on a single definition.\nA: Facilitated meeting with both teams. Documented both definitions in data dictionary. Created two separate metrics: 'logged_in_users' and 'active_customers_30d'. Both available in mart layer.\nR: Both teams got what they needed. No more definitional arguments in reports."),
    ]
    for q_behav, answer in BEHAVIOURALS:
        with st.expander(f"**{q_behav}**"):
            if st.checkbox("Show STAR Answer", key=f"beh_{hash(q_behav)}"):
                st.markdown(_card(answer.replace("\n","<br>"),l=STEEL,p="10px 14px"), unsafe_allow_html=True)

# ── TAB 5: STUDY PLAN ────────────────────────────────────────────────────────
with TAB[5]:
    st.markdown(_h2("Study Plan (6 weeks to job-ready)","📋"), unsafe_allow_html=True)
    PLAN = [
        ("Week 1","SQL Fundamentals","Joins (all types), GROUP BY, HAVING, subqueries","Complete Joins + Aggregations tabs in Academy"),
        ("Week 2","Advanced SQL","Window functions, CTEs, ROLLUP, CUBE, EXPLAIN","Window Functions + Analytical SQL tabs"),
        ("Week 3","Data Modeling","3NF, Star Schema, SCD types, fact patterns","Data Modeling page + star schema tab"),
        ("Week 4","Data Engineering","ETL vs ELT, batch vs streaming, DQ, lineage","ETL Pipeline tab + Governance page"),
        ("Week 5","Architecture & Performance","Lambda/Kappa/Medallion, query optimisation","Architecture + Performance pages"),
        ("Week 6","Interview Practice","SQL challenges, system design, behavioural","Interview Prep page — all tabs"),
    ]
    plan_df = pd.DataFrame(PLAN, columns=["Week","Topic","Focus Areas","Platform Resources"])
    st.dataframe(plan_df, use_container_width=True, height=260, hide_index=True)
    st.markdown(_h3("🏆 Certifications to Target",AMBER), unsafe_allow_html=True)
    certs = [
        ("dbt Analytics Engineering","dbtlabs.com — free","SQL transforms, testing, documentation","Most in-demand for data engineers"),
        ("Databricks Data Engineer","databricks.com","Spark, Delta Lake, MLflow","Widely recognised, lakes/lakehouses"),
        ("AWS Data Engineer Associate","aws.amazon.com","S3, Glue, Redshift, Kinesis","Good for cloud data engineering"),
        ("Google Professional Data Engineer","cloud.google.com","BigQuery, Dataflow, Pub/Sub","Strong for GCP stack"),
        ("Snowflake SnowPro Core","training.snowflake.com","Snowflake SQL, DWH concepts","Popular for analytics engineering"),
    ]
    for cert,url,skills,note in certs:
        st.markdown(_card(f'<b style="color:{TEAL};">{cert}</b> <span style="font-size:.7rem;color:{M};">— {url}</span><br>'
                          f'<span style="font-size:.74rem;color:{TEXT};">Skills: {skills}</span><br>'
                          f'<span style="font-size:.7rem;color:{M};">{note}</span>',l=TEAL,p="9px 14px"), unsafe_allow_html=True)
