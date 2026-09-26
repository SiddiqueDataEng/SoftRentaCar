"""
p23_interview.py — Complete Data Engineering Interview Prep
SQL (40+ Q) · Python (20+ Q) · Concepts & Terms · System Design
Behavioural · Study Plan · AI-powered Q&A assistant
"""
import io, contextlib, traceback as _tb
import pandas as pd
import plotly.express as px
import streamlit as st
import duckdb
from page_modules._shared import inject, get_data, BRAND, STEEL, GREEN, AMBER, ORANGE, TEXT
from app.ai_chat import _resolve_key
inject()
M="#5a7a96"; CB="#141e2b"; BD="#1e2f44"; TEAL="#2A9D8F"; PUR="#6A4C93"
def _card(b,l=BRAND,p="14px 16px"): return f'<div style="background:{CB};border:1px solid {BD};border-left:3px solid {l};border-radius:10px;padding:{p};margin:6px 0;">{b}</div>'
def _h2(t,i=""): return f'<div style="font-size:1.22rem;font-weight:800;color:{TEXT};margin:16px 0 4px;"><span style="color:{BRAND};">{i} </span>{t}</div>'
def _h3(t,c=STEEL): return f'<div style="font-size:.9rem;font-weight:700;color:{c};border-left:3px solid {c};padding-left:8px;margin:10px 0 6px;">{t}</div>'
def _diff(d): colors={"Easy":TEAL,"Medium":AMBER,"Hard":BRAND,"Expert":PUR}; c=colors.get(d,M); return f'<span style="background:{c}33;color:{c};padding:1px 8px;border-radius:10px;font-size:.68rem;font-weight:700;">{d}</span>'

dfs = get_data()

@st.cache_resource
def _get_conn(dfs):
    c = duckdb.connect(":memory:")
    for n,df in dfs.items():
        try: c.register(n,df)
        except: pass
    return c
conn = _get_conn(dfs)

# ── Session state ─────────────────────────────────────────────────────────────
for k,v in {"intv_ai_hist":[], "intv_progress":{}}.items():
    if k not in st.session_state: st.session_state[k] = v

st.markdown(f'<div style="font-size:1.6rem;font-weight:900;color:{BRAND};">🎯 Interview Prep Academy</div>'
            f'<div style="font-size:.8rem;color:{M};">SQL · Python · Concepts · PySpark · System Design · AI Tutor · 100+ Questions</div>',
            unsafe_allow_html=True)
st.markdown(f"<hr style='border-color:{BD};margin:6px 0 10px'>",unsafe_allow_html=True)

TAB = st.tabs([
    "🤖 AI Tutor",
    "💼 SQL (40 Q)",
    "🐍 Python (20 Q)",
    "⚡ PySpark (15 Q)",
    "📚 Concepts & Terms",
    "🏗️ System Design",
    "🧩 Scenario Problems",
    "💬 Behavioural",
    "📊 Progress Tracker",
    "📋 Study Plan",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 0: AI TUTOR
# ══════════════════════════════════════════════════════════════════════════════
with TAB[0]:
    st.markdown(_h2("AI Interview Tutor","🤖"), unsafe_allow_html=True)
    _api_key = _resolve_key()
    if _api_key:
        st.markdown(_card(f'<span style="color:{TEAL};">✅ GPT-4o connected</span> — Ask any data engineering, SQL, Python, or PySpark interview question.',l=TEAL,p="9px 14px"), unsafe_allow_html=True)
    else:
        st.markdown(_card(f'<span style="color:{AMBER};">⚠️ No OpenAI API key</span> — Add key in Settings to enable AI answers. Questions still work with built-in answers.',l=AMBER,p="9px 14px"), unsafe_allow_html=True)

    # Quick question buttons
    st.markdown(_h3("Quick Questions",STEEL), unsafe_allow_html=True)
    _quick = [
        "Explain the difference between RANK and DENSE_RANK",
        "What is a data lakehouse?",
        "How does PySpark handle lazy evaluation?",
        "Explain SCD Type 2 with an example",
        "What is a watermark in streaming?",
        "Difference between batch, micro-batch, and streaming",
        "How do you handle NULL values in SQL joins?",
        "Explain the Medallion architecture",
        "What is idempotency in ETL?",
        "How would you optimise a slow GROUP BY query?",
    ]
    _qc = st.columns(5)
    for i,q in enumerate(_quick):
        if _qc[i%5].button(q[:30]+"…" if len(q)>30 else q, key=f"quick_{i}", use_container_width=True):
            st.session_state.intv_ai_hist.append({"role":"user","content":q})

    # Chat history display
    _hist = st.session_state.intv_ai_hist
    if _hist:
        for msg in _hist[-10:]:
            if msg["role"] == "user":
                st.markdown(f'<div style="display:flex;justify-content:flex-end;margin:8px 0;">'
                            f'<div style="background:{BRAND}33;color:{TEXT};padding:10px 14px;border-radius:18px 18px 4px 18px;max-width:70%;font-size:.84rem;">{msg["content"]}</div></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div style="background:{CB};border:1px solid {BD};border-radius:4px 18px 18px 18px;padding:12px 16px;margin:4px 0 8px 0;font-size:.84rem;color:{TEXT};max-width:88%;line-height:1.65;">{msg["content"]}</div>', unsafe_allow_html=True)

    # Input
    _user_q = st.text_area("Ask a data engineering question:", height=80, key="ai_tutor_input",
                            placeholder="e.g. Explain window functions vs GROUP BY, or design a DWH for e-commerce...")
    _ac1,_ac2,_ac3 = st.columns(3)
    _ask_btn   = _ac1.button("🤖 Ask AI", type="primary", use_container_width=True, key="ask_ai")
    _clear_btn = _ac2.button("🗑 Clear Chat", use_container_width=True, key="clear_ai")
    _ac3.markdown(f'<div style="font-size:.7rem;color:{M};padding-top:8px;">Model: gpt-4o-mini</div>', unsafe_allow_html=True)

    if _clear_btn:
        st.session_state.intv_ai_hist = []
        st.rerun()

    if _ask_btn and _user_q.strip():
        _q_text = _user_q.strip()
        st.session_state.intv_ai_hist.append({"role":"user","content":_q_text})
        if _api_key:
            with st.spinner("Thinking…"):
                try:
                    from openai import OpenAI
                    _client = OpenAI(api_key=_api_key)
                    _sys = """You are an expert data engineering tutor helping candidates prepare for interviews.
You have deep expertise in: SQL (DuckDB, PostgreSQL, T-SQL), Python (pandas, numpy), PySpark,
data modeling (Kimball, Data Vault), ETL/ELT pipelines, Kafka, Airflow, dbt, Snowflake,
Databricks, AWS/Azure data services, GDPR, data governance, and system design.

Format responses clearly with:
- Brief direct answer first (1-2 sentences)
- Code examples when relevant (use code blocks)
- Key points as bullet list
- Common interview follow-up questions at the end

Keep answers concise but complete. Use the Rent-A-Car data context when giving examples."""
                    _msgs = [{"role":"system","content":_sys}]
                    for h in st.session_state.intv_ai_hist[-8:]:
                        _msgs.append(h)
                    _resp = _client.chat.completions.create(
                        model="gpt-4o-mini", messages=_msgs,
                        max_tokens=1200, temperature=0.3,
                    )
                    _answer = _resp.choices[0].message.content
                except Exception as e:
                    _answer = f"API error: {e}. Please check your OpenAI key in Settings."
        else:
            _answer = "**No API key configured.** Add your OpenAI key in the Settings page to get AI-powered answers.\n\nMeanwhile, check the SQL/Python/PySpark tabs for curated answers to 75+ common interview questions."
        st.session_state.intv_ai_hist.append({"role":"assistant","content":_answer})
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1: SQL QUESTIONS (40)
# ══════════════════════════════════════════════════════════════════════════════
with TAB[1]:
    st.markdown(_h2("SQL Interview Questions (40)","💼"), unsafe_allow_html=True)
    _topic_f = st.selectbox("Filter by topic:", ["All","Joins","Window Functions","CTEs","Aggregation","DQ/ETL","Performance","Date Functions","Subqueries","Data Modeling"], key="sql_topic")
    _diff_f  = st.selectbox("Filter by difficulty:", ["All","Easy","Medium","Hard","Expert"], key="sql_diff")

    SQL_QS = [
        # ── JOINS ──
        {"cat":"Joins","diff":"Easy","q":"What is the difference between INNER JOIN, LEFT JOIN, and FULL OUTER JOIN?",
         "concepts":["JOIN types"],
         "sql":"""-- INNER: only matching rows
SELECT t.trip_id, c.full_name FROM trips t
INNER JOIN customers c ON t.customer_id = c.customer_id LIMIT 5;

-- LEFT: all trips, NULL if no customer match
SELECT t.trip_id, c.full_name FROM trips t
LEFT JOIN customers c ON t.customer_id = c.customer_id LIMIT 5;

-- FULL OUTER: all rows from both, NULLs where no match
SELECT t.trip_id, v.vehicle_id FROM trips t
FULL OUTER JOIN vehicles v ON t.vehicle_id = v.vehicle_id WHERE t.trip_id IS NULL OR v.vehicle_id IS NULL LIMIT 5;"""},
        {"cat":"Joins","diff":"Medium","q":"Find vehicles that have NEVER been used in any completed trip (anti-join pattern).",
         "concepts":["LEFT JOIN","IS NULL","Anti-join"],
         "sql":"""SELECT v.vehicle_id, v.make, v.model, v.status
FROM vehicles v
LEFT JOIN trips t ON v.vehicle_id = t.vehicle_id AND t.status = 'Completed'
WHERE t.trip_id IS NULL
ORDER BY v.vehicle_id;"""},
        {"cat":"Joins","diff":"Medium","q":"Find customers who have taken trips in BOTH Lahore and Karachi (intersect using self-join).",
         "concepts":["SELF JOIN","Intersect logic"],
         "sql":"""SELECT DISTINCT a.customer_id
FROM trips a
JOIN trips b ON a.customer_id = b.customer_id
WHERE a.pickup_city = 'Lahore'
  AND b.pickup_city = 'Karachi'
  AND a.status = 'Completed'
  AND b.status = 'Completed';"""},
        {"cat":"Joins","diff":"Hard","q":"For each fleet, show the top-earning vehicle and its % share of that fleet's total revenue.",
         "concepts":["JOIN","Subquery","Window Function","QUALIFY"],
         "sql":"""WITH fleet_rev AS (
    SELECT fleet_id, vehicle_id,
           SUM(trip_fare_pkr) AS veh_revenue,
           SUM(SUM(trip_fare_pkr)) OVER (PARTITION BY fleet_id) AS fleet_total
    FROM trips WHERE status = 'Completed'
    GROUP BY fleet_id, vehicle_id
)
SELECT fleet_id, vehicle_id,
    ROUND(veh_revenue,0) AS revenue,
    ROUND(veh_revenue*100.0/fleet_total,1) AS pct_of_fleet
FROM fleet_rev
QUALIFY ROW_NUMBER() OVER (PARTITION BY fleet_id ORDER BY veh_revenue DESC) = 1
ORDER BY revenue DESC;"""},
        # ── WINDOW FUNCTIONS ──
        {"cat":"Window Functions","diff":"Easy","q":"Number each customer's trips chronologically using ROW_NUMBER.",
         "concepts":["ROW_NUMBER","PARTITION BY","ORDER BY"],
         "sql":"""SELECT customer_id, trip_id, pickup_datetime, trip_fare_pkr,
    ROW_NUMBER() OVER (
        PARTITION BY customer_id
        ORDER BY pickup_datetime
    ) AS trip_number
FROM trips WHERE status = 'Completed'
ORDER BY customer_id, trip_number LIMIT 20;"""},
        {"cat":"Window Functions","diff":"Medium","q":"Calculate month-over-month revenue change using LAG().",
         "concepts":["LAG","CTE","Window Function"],
         "sql":"""WITH monthly AS (
    SELECT DATE_TRUNC('month', pickup_datetime::DATE) AS month,
           SUM(trip_fare_pkr) AS revenue
    FROM trips WHERE status = 'Completed'
    GROUP BY 1
)
SELECT month, ROUND(revenue,0) AS revenue_pkr,
    ROUND(LAG(revenue) OVER (ORDER BY month),0) AS prev_month,
    ROUND((revenue - LAG(revenue) OVER (ORDER BY month))*100.0
          / NULLIF(LAG(revenue) OVER (ORDER BY month),0), 1) AS mom_pct
FROM monthly ORDER BY month;"""},
        {"cat":"Window Functions","diff":"Medium","q":"For each vehicle, show the percentage of trips where it was above its own average fare (window + CASE).",
         "concepts":["AVG over PARTITION","CASE","Window"],
         "sql":"""SELECT vehicle_id, trip_id, trip_fare_pkr,
    ROUND(AVG(trip_fare_pkr) OVER (PARTITION BY vehicle_id),0) AS veh_avg_fare,
    CASE WHEN trip_fare_pkr > AVG(trip_fare_pkr) OVER (PARTITION BY vehicle_id)
         THEN 'Above Avg' ELSE 'Below Avg' END AS vs_avg
FROM trips WHERE status = 'Completed'
ORDER BY vehicle_id, pickup_datetime LIMIT 20;"""},
        {"cat":"Window Functions","diff":"Hard","q":"Find the longest gap (in days) between consecutive trips for each customer.",
         "concepts":["LAG","DATE_DIFF","Window Function"],
         "sql":"""WITH gaps AS (
    SELECT customer_id, pickup_datetime,
           LAG(pickup_datetime) OVER (PARTITION BY customer_id ORDER BY pickup_datetime) AS prev_trip,
           DATE_DIFF('day',
               LAG(pickup_datetime::DATE) OVER (PARTITION BY customer_id ORDER BY pickup_datetime),
               pickup_datetime::DATE
           ) AS gap_days
    FROM trips WHERE status = 'Completed'
)
SELECT customer_id, MAX(gap_days) AS longest_gap_days,
       AVG(gap_days) AS avg_gap_days
FROM gaps WHERE gap_days IS NOT NULL
GROUP BY customer_id
ORDER BY longest_gap_days DESC LIMIT 10;"""},
        {"cat":"Window Functions","diff":"Hard","q":"Calculate a 3-month rolling average of revenue AND flag months where actual is >20% above the rolling average.",
         "concepts":["Moving Average","ROWS BETWEEN","CASE"],
         "sql":"""WITH monthly AS (
    SELECT DATE_TRUNC('month', pickup_datetime::DATE) AS month,
           SUM(trip_fare_pkr) AS revenue
    FROM trips WHERE status = 'Completed'
    GROUP BY 1
)
SELECT month, ROUND(revenue,0) AS revenue_pkr,
    ROUND(AVG(revenue) OVER (ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW),0) AS rolling_3m,
    CASE WHEN revenue > AVG(revenue) OVER (ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)*1.2
         THEN '📈 Spike' ELSE '✅ Normal' END AS flag
FROM monthly ORDER BY month;"""},
        {"cat":"Window Functions","diff":"Expert","q":"Implement a running total that resets each year (partition by year, running sum within year).",
         "concepts":["Running Total","PARTITION BY year","Window"],
         "sql":"""SELECT pickup_datetime::DATE AS trip_date,
    trip_fare_pkr,
    DATE_PART('year', pickup_datetime::DATE)::INT AS yr,
    ROUND(SUM(trip_fare_pkr) OVER (
        PARTITION BY DATE_PART('year', pickup_datetime::DATE)::INT
        ORDER BY pickup_datetime
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ),0) AS ytd_revenue
FROM trips WHERE status = 'Completed'
ORDER BY trip_date LIMIT 30;"""},
        # ── CTES ──
        {"cat":"CTEs","diff":"Easy","q":"Use a CTE to find the average fare per booking type, then filter for types above the overall average.",
         "concepts":["CTE","AVG","Subquery comparison"],
         "sql":"""WITH type_avg AS (
    SELECT booking_type, ROUND(AVG(trip_fare_pkr),0) AS avg_fare, COUNT(*) AS trips
    FROM trips WHERE status = 'Completed'
    GROUP BY booking_type
),
overall AS (
    SELECT AVG(trip_fare_pkr) AS grand_avg FROM trips WHERE status = 'Completed'
)
SELECT t.booking_type, t.avg_fare, t.trips
FROM type_avg t, overall o
WHERE t.avg_fare > o.grand_avg
ORDER BY t.avg_fare DESC;"""},
        {"cat":"CTEs","diff":"Medium","q":"Use a recursive CTE to generate a monthly date spine from 2022 to 2026.",
         "concepts":["Recursive CTE","Date spine","UNION ALL"],
         "sql":"""WITH RECURSIVE months AS (
    SELECT DATE '2022-01-01' AS m
    UNION ALL
    SELECT m + INTERVAL '1 month' FROM months WHERE m < DATE '2026-12-01'
)
SELECT STRFTIME(m,'%Y-%m') AS year_month,
       COALESCE(t.trips, 0) AS trip_count
FROM months ms
LEFT JOIN (
    SELECT DATE_TRUNC('month', pickup_datetime::DATE) AS m, COUNT(*) AS trips
    FROM trips WHERE status='Completed' GROUP BY 1
) t ON ms.m = t.m
ORDER BY ms.m LIMIT 24;"""},
        {"cat":"CTEs","diff":"Hard","q":"Customer funnel analysis: bookings → confirmed → completed. Calculate drop-off % at each stage.",
         "concepts":["CTE","Multiple aggregations","Funnel"],
         "sql":"""WITH totals AS (
    SELECT COUNT(*) AS total_bookings,
           COUNT(*) FILTER(WHERE status IN ('Confirmed','In Progress','Completed')) AS confirmed,
           COUNT(*) FILTER(WHERE status = 'Completed') AS completed,
           COUNT(*) FILTER(WHERE status = 'Cancelled') AS cancelled
    FROM trips
)
SELECT total_bookings,
    confirmed,
    completed,
    cancelled,
    ROUND(confirmed*100.0/total_bookings,1) AS confirm_rate,
    ROUND(completed*100.0/NULLIF(confirmed,0),1) AS completion_rate,
    ROUND(cancelled*100.0/total_bookings,1) AS cancel_rate
FROM totals;"""},
        # ── AGGREGATION ──
        {"cat":"Aggregation","diff":"Easy","q":"Count trips, total revenue, and average fare by status.",
         "concepts":["GROUP BY","COUNT","SUM","AVG"],
         "sql":"""SELECT status,
    COUNT(*) AS trips,
    ROUND(SUM(trip_fare_pkr),0) AS total_revenue_pkr,
    ROUND(AVG(trip_fare_pkr),0) AS avg_fare_pkr,
    ROUND(MIN(trip_fare_pkr),0) AS min_fare,
    ROUND(MAX(trip_fare_pkr),0) AS max_fare
FROM trips GROUP BY status ORDER BY trips DESC;"""},
        {"cat":"Aggregation","diff":"Medium","q":"Show revenue by fleet AND booking type as a pivot (years as columns using conditional aggregation).",
         "concepts":["FILTER","Conditional aggregation","PIVOT"],
         "sql":"""SELECT fleet_id,
    ROUND(SUM(trip_fare_pkr) FILTER(WHERE DATE_PART('year',pickup_datetime::DATE)=2023),0) AS rev_2023,
    ROUND(SUM(trip_fare_pkr) FILTER(WHERE DATE_PART('year',pickup_datetime::DATE)=2024),0) AS rev_2024,
    ROUND(SUM(trip_fare_pkr) FILTER(WHERE DATE_PART('year',pickup_datetime::DATE)=2025),0) AS rev_2025,
    ROUND(SUM(trip_fare_pkr) FILTER(WHERE DATE_PART('year',pickup_datetime::DATE)=2026),0) AS rev_2026,
    ROUND(SUM(trip_fare_pkr),0) AS total
FROM trips WHERE status = 'Completed'
GROUP BY fleet_id ORDER BY total DESC;"""},
        {"cat":"Aggregation","diff":"Medium","q":"Using ROLLUP, show revenue by city with subtotals and a grand total.",
         "concepts":["ROLLUP","GROUPING","Subtotals"],
         "sql":"""SELECT COALESCE(pickup_city,'ALL CITIES') AS city,
    COUNT(*) AS trips,
    ROUND(SUM(trip_fare_pkr),0) AS revenue_pkr,
    GROUPING(pickup_city) AS is_total
FROM trips WHERE status = 'Completed'
GROUP BY ROLLUP(pickup_city)
ORDER BY is_total, revenue_pkr DESC NULLS LAST;"""},
        {"cat":"Aggregation","diff":"Hard","q":"Calculate median, P25, P75, and IQR for trip fare by booking type.",
         "concepts":["PERCENTILE_CONT","IQR","Statistical aggregation"],
         "sql":"""SELECT booking_type, COUNT(*) AS trips,
    ROUND(AVG(trip_fare_pkr),0) AS mean_fare,
    ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY trip_fare_pkr),0) AS p25,
    ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY trip_fare_pkr),0) AS median,
    ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY trip_fare_pkr),0) AS p75,
    ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY trip_fare_pkr)
         -PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY trip_fare_pkr),0) AS iqr
FROM trips WHERE status = 'Completed'
GROUP BY booking_type ORDER BY median DESC;"""},
        # ── DQ/ETL ──
        {"cat":"DQ/ETL","diff":"Easy","q":"Find all trips where dropoff_datetime is before pickup_datetime (timeline violation).",
         "concepts":["DQ check","Date comparison"],
         "sql":"""SELECT trip_id, pickup_datetime, dropoff_datetime,
    DATE_DIFF('hour', pickup_datetime, dropoff_datetime) AS dur_hours
FROM trips
WHERE CAST(dropoff_datetime AS TIMESTAMP) < CAST(pickup_datetime AS TIMESTAMP)
ORDER BY dur_hours LIMIT 20;"""},
        {"cat":"DQ/ETL","diff":"Medium","q":"Deduplicate trips keeping the most recent record per trip_id.",
         "concepts":["ROW_NUMBER","QUALIFY","Deduplication"],
         "sql":"""SELECT * FROM trips
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY trip_id
    ORDER BY pickup_datetime DESC NULLS LAST
) = 1
ORDER BY pickup_datetime DESC LIMIT 20;"""},
        {"cat":"DQ/ETL","diff":"Medium","q":"Find the null rate for each column in the trips table.",
         "concepts":["NULL check","Dynamic aggregation","DQ metrics"],
         "sql":"""SELECT
    'trip_id'           AS col, COUNT(*) FILTER(WHERE trip_id IS NULL)*100.0/COUNT(*) AS null_pct FROM trips
UNION ALL SELECT 'customer_id',   COUNT(*) FILTER(WHERE customer_id IS NULL)*100.0/COUNT(*) FROM trips
UNION ALL SELECT 'vehicle_id',    COUNT(*) FILTER(WHERE vehicle_id IS NULL)*100.0/COUNT(*) FROM trips
UNION ALL SELECT 'trip_fare_pkr', COUNT(*) FILTER(WHERE trip_fare_pkr IS NULL OR CAST(trip_fare_pkr AS DOUBLE)=0)*100.0/COUNT(*) FROM trips
UNION ALL SELECT 'status',        COUNT(*) FILTER(WHERE status IS NULL)*100.0/COUNT(*) FROM trips
ORDER BY null_pct DESC;"""},
        {"cat":"DQ/ETL","diff":"Hard","q":"Implement an SCD Type 2 change detection: identify which customers changed city since a hypothetical previous load.",
         "concepts":["SCD2","Change detection","MD5 hash"],
         "sql":"""-- Simulate: detect customers whose city has changed
-- In production, compare staging vs dim_customer
WITH staging_data AS (
    -- Simulate 'new' data with some city changes
    SELECT customer_id, city AS new_city FROM customers
),
current_data AS (
    SELECT customer_id, city AS current_city FROM customers
),
changes AS (
    SELECT s.customer_id, c.current_city, s.new_city
    FROM staging_data s
    JOIN current_data c ON s.customer_id = c.customer_id
    WHERE s.new_city != c.current_city  -- attribute changed
)
SELECT customer_id, current_city, new_city,
    'EXPIRE old → INSERT new' AS scd2_action
FROM changes LIMIT 10;"""},
        # ── DATE FUNCTIONS ──
        {"cat":"Date Functions","diff":"Easy","q":"Extract year, month, weekday, and hour from pickup_datetime.",
         "concepts":["DATE_PART","STRFTIME","Date extraction"],
         "sql":"""SELECT pickup_datetime,
    DATE_PART('year',  pickup_datetime::DATE)::INT AS yr,
    DATE_PART('month', pickup_datetime::DATE)::INT AS mo,
    STRFTIME(pickup_datetime::DATE,'%A')            AS weekday,
    DATE_PART('hour',  pickup_datetime)::INT        AS hr,
    DATE_DIFF('day', pickup_datetime::DATE, current_date) AS days_ago
FROM trips WHERE status = 'Completed'
ORDER BY pickup_datetime DESC LIMIT 10;"""},
        {"cat":"Date Functions","diff":"Medium","q":"Find trips that started on a weekend vs weekday and compare average fare.",
         "concepts":["DAYOFWEEK","CASE","DATE_PART"],
         "sql":"""SELECT
    CASE WHEN DATE_PART('dayofweek', pickup_datetime::DATE) IN (0,6)
         THEN 'Weekend' ELSE 'Weekday' END AS day_type,
    COUNT(*) AS trips,
    ROUND(AVG(trip_fare_pkr),0) AS avg_fare,
    ROUND(SUM(trip_fare_pkr),0) AS total_revenue
FROM trips WHERE status = 'Completed'
GROUP BY day_type ORDER BY day_type;"""},
        # ── SUBQUERIES ──
        {"cat":"Subqueries","diff":"Medium","q":"Find all trips with fare above the fleet's own average fare (correlated subquery vs window function — show both).",
         "concepts":["Correlated subquery","Window Function","Performance"],
         "sql":"""-- Method 1: Correlated subquery (slow)
SELECT trip_id, fleet_id, trip_fare_pkr,
    (SELECT AVG(i.trip_fare_pkr) FROM trips i WHERE i.fleet_id = t.fleet_id AND i.status='Completed') AS fleet_avg
FROM trips t
WHERE status = 'Completed'
  AND trip_fare_pkr > (SELECT AVG(i.trip_fare_pkr) FROM trips i WHERE i.fleet_id = t.fleet_id AND i.status='Completed')
LIMIT 10;

-- Method 2: Window function (fast — ONE pass)
SELECT trip_id, fleet_id, trip_fare_pkr,
    ROUND(AVG(trip_fare_pkr) OVER (PARTITION BY fleet_id),0) AS fleet_avg
FROM trips WHERE status = 'Completed'
QUALIFY trip_fare_pkr > AVG(trip_fare_pkr) OVER (PARTITION BY fleet_id)
LIMIT 10;"""},
        {"cat":"Subqueries","diff":"Hard","q":"Find customers whose total spend is in the top 10% (using PERCENTILE_CONT or NTILE).",
         "concepts":["NTILE","PERCENTILE","Subquery","Top N percent"],
         "sql":"""WITH spend AS (
    SELECT customer_id, SUM(trip_fare_pkr) AS total_spend
    FROM trips WHERE status = 'Completed'
    GROUP BY customer_id
)
SELECT s.customer_id, c.full_name, ROUND(s.total_spend,0) AS total_spend_pkr,
    NTILE(10) OVER (ORDER BY s.total_spend) AS decile
FROM spend s JOIN customers c ON s.customer_id = c.customer_id
QUALIFY decile = 10  -- top 10%
ORDER BY total_spend_pkr DESC LIMIT 20;"""},
        # ── PERFORMANCE ──
        {"cat":"Performance","diff":"Medium","q":"Rewrite this slow query using a window function instead of a correlated subquery: find each customer's latest trip.",
         "concepts":["Performance","Window Function","QUALIFY"],
         "sql":"""-- SLOW: correlated subquery
-- SELECT * FROM trips t WHERE pickup_datetime = (SELECT MAX(pickup_datetime) FROM trips WHERE customer_id=t.customer_id)

-- FAST: window function
SELECT customer_id, trip_id, pickup_datetime, trip_fare_pkr, status
FROM trips
QUALIFY ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY pickup_datetime DESC) = 1
ORDER BY pickup_datetime DESC LIMIT 20;"""},
        {"cat":"Performance","diff":"Hard","q":"Show how to use EXPLAIN ANALYZE to find a bottleneck, then optimize with column pruning.",
         "concepts":["EXPLAIN ANALYZE","Query plan","Optimization"],
         "sql":"""-- Step 1: Baseline (reads ALL 23 columns)
EXPLAIN ANALYZE
SELECT * FROM trips WHERE status = 'Completed' AND fleet_id = 'FL001';

-- Step 2: Optimized (reads only 4 columns)
EXPLAIN ANALYZE
SELECT trip_id, fleet_id, trip_fare_pkr, pickup_datetime
FROM trips
WHERE status = 'Completed' AND fleet_id = 'FL001';

-- In DuckDB columnar storage, Step 2 scans ~83% less data!
-- Look for: "Rows Removed", "Actual Time" in EXPLAIN output"""},
        # ── DATA MODELING ──
        {"cat":"Data Modeling","diff":"Medium","q":"Write the SQL to detect if a row in dim_customer needs an SCD Type 2 update (city or customer_type changed).",
         "concepts":["SCD2","Change detection","Hashing"],
         "sql":"""-- Detect changed rows using hash comparison
WITH incoming AS (
    SELECT customer_id, city, customer_type,
           MD5(COALESCE(city,'') || COALESCE(customer_type,'')) AS new_hash
    FROM customers  -- staging data
),
current_dim AS (
    SELECT customer_id, city, customer_type,
           MD5(COALESCE(city,'') || COALESCE(customer_type,'')) AS curr_hash
    FROM customers  -- simulating dim_customer
)
SELECT i.customer_id, c.city AS old_city, i.city AS new_city,
       c.customer_type AS old_type, i.customer_type AS new_type
FROM incoming i
JOIN current_dim c ON i.customer_id = c.customer_id
WHERE i.new_hash != c.curr_hash  -- something changed
LIMIT 10;"""},
        {"cat":"Data Modeling","diff":"Hard","q":"Design a query to validate star schema grain — confirm fact_trips has one row per trip with no fanout from dimension joins.",
         "concepts":["Grain validation","Row count check","Data modeling"],
         "sql":"""-- Grain check: joining dims should not multiply rows
-- Step 1: baseline fact count
SELECT COUNT(*) AS fact_rows FROM trips;

-- Step 2: join all dims and count — should be same!
SELECT COUNT(*) AS after_joins
FROM trips t
JOIN customers c  ON t.customer_id = c.customer_id
JOIN vehicles v   ON t.vehicle_id  = v.vehicle_id
JOIN fleets f     ON t.fleet_id    = f.fleet_id
WHERE t.status = 'Completed';

-- If after_joins > fact_rows: FANOUT! Debug which dim has duplicates
-- Check: SELECT customer_id, COUNT(*) FROM customers GROUP BY 1 HAVING COUNT(*)>1;"""},
    ]

    # Apply filters
    _filtered_sql = SQL_QS
    if _topic_f != "All": _filtered_sql = [q for q in SQL_QS if q["cat"]==_topic_f]
    if _diff_f  != "All": _filtered_sql = [q for q in SQL_QS if q["diff"]==_diff_f]

    st.caption(f"Showing {len(_filtered_sql)} of {len(SQL_QS)} questions")
    for i,q in enumerate(_filtered_sql):
        _pid = f"sql_{i}_{hash(q['q'])}"
        _solved = st.session_state.intv_progress.get(_pid, False)
        _label  = f"{'✅ ' if _solved else ''}Q{i+1}: {q['q'][:65]}…" if len(q['q'])>65 else f"{'✅ ' if _solved else ''}Q{i+1}: {q['q']}"
        with st.expander(_label):
            st.markdown(_card(f"{_diff(q['diff'])} &nbsp; <span style='font-size:.7rem;color:{STEEL};'>{q['cat']}</span><br><br>"
                              f"<b style='color:{TEXT};font-size:.84rem;'>{q['q']}</b><br><br>"
                              f"<span style='font-size:.7rem;color:{M};'>Concepts: {', '.join(q['concepts'])}</span>",l=BRAND,p="10px 14px"), unsafe_allow_html=True)
            _show = st.checkbox("Show Answer",key=f"show_{_pid}")
            if _show:
                st.code(q["sql"].strip(), language="sql")
                if st.button("▶ Run",key=f"run_{_pid}"):
                    try:
                        # run first statement
                        _stmts = [s.strip() for s in q["sql"].split(";") if s.strip() and not s.strip().startswith("--")]
                        for _stmt in _stmts:
                            try:
                                _r = conn.execute(_stmt).fetchdf()
                                if not _r.empty:
                                    st.dataframe(_r, use_container_width=True, height=220, hide_index=True)
                            except: pass
                    except Exception as e:
                        st.error(str(e))
            if st.checkbox("Mark as done",key=f"done_{_pid}", value=_solved):
                st.session_state.intv_progress[_pid] = True
            else:
                st.session_state.intv_progress[_pid] = False


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2: PYTHON QUESTIONS (20)
# ══════════════════════════════════════════════════════════════════════════════
with TAB[2]:
    st.markdown(_h2("Python Interview Questions (20)","🐍"), unsafe_allow_html=True)
    PY_QS = [
        ("Easy","pandas basics","Read a CSV, display shape, and show first 5 rows",
         """import pandas as pd
trips = dfs["trips"].copy()
print(f"Shape: {trips.shape}")
print(f"Columns: {list(trips.columns)}")
print(f"Dtypes:\n{trips.dtypes}")
result = trips.head(5)"""),
        ("Easy","pandas filter","Filter completed trips and show top 5 by fare",
         """trips = dfs["trips"].copy()
trips["trip_fare_pkr"] = pd.to_numeric(trips["trip_fare_pkr"], errors="coerce")
result = (trips[trips["status"]=="Completed"]
          .nlargest(5,"trip_fare_pkr")
          [["trip_id","pickup_city","dropoff_city","trip_fare_pkr"]])
print(result.to_string(index=False))"""),
        ("Medium","groupby + merge","Top 3 revenue customers per city",
         """import pandas as pd
trips = dfs["trips"].copy(); cust = dfs["customers"].copy()
trips["trip_fare_pkr"] = pd.to_numeric(trips["trip_fare_pkr"], errors="coerce").fillna(0)
merged = trips[trips["status"]=="Completed"].merge(cust[["customer_id","full_name","city"]],on="customer_id")
result = (merged.groupby(["city","customer_id","full_name"])["trip_fare_pkr"]
          .sum().reset_index()
          .sort_values("trip_fare_pkr",ascending=False)
          .groupby("city").head(3)
          .round(0))
print(result.to_string(index=False))"""),
        ("Medium","datetime ops","Calculate trip duration and flag trips > 7 days",
         """import pandas as pd
trips = dfs["trips"].copy()
trips["pickup_datetime"]  = pd.to_datetime(trips["pickup_datetime"],  errors="coerce")
trips["dropoff_datetime"] = pd.to_datetime(trips["dropoff_datetime"], errors="coerce")
trips["actual_duration_hrs"] = (trips["dropoff_datetime"] - trips["pickup_datetime"]).dt.total_seconds() / 3600
trips["long_trip_flag"] = trips["actual_duration_hrs"] > 168  # > 7 days
print(f"Long trips (>7 days): {trips['long_trip_flag'].sum()}")
result = trips[trips["long_trip_flag"]][["trip_id","actual_duration_hrs","pickup_city","dropoff_city"]].head(5)"""),
        ("Medium","outlier detection","Detect fare outliers using IQR method",
         """import pandas as pd, numpy as np
trips = dfs["trips"].copy()
fares = pd.to_numeric(trips["trip_fare_pkr"], errors="coerce").dropna()
Q1, Q3 = fares.quantile(0.25), fares.quantile(0.75)
IQR = Q3 - Q1; lower, upper = Q1-1.5*IQR, Q3+1.5*IQR
trips["is_outlier"] = (trips["trip_fare_pkr"].astype(float) < lower) | (trips["trip_fare_pkr"].astype(float) > upper)
print(f"Q1={Q1:,.0f}  Q3={Q3:,.0f}  IQR={IQR:,.0f}")
print(f"Bounds: [{lower:,.0f}, {upper:,.0f}]")
print(f"Outliers: {trips['is_outlier'].sum()} ({trips['is_outlier'].mean()*100:.1f}%)")
result = trips[trips["is_outlier"]][["trip_id","trip_fare_pkr","pickup_city"]].head(10)"""),
        ("Medium","apply + lambda","Classify customers into fare tiers using apply",
         """import pandas as pd
trips = dfs["trips"].copy()
trips["trip_fare_pkr"] = pd.to_numeric(trips["trip_fare_pkr"], errors="coerce").fillna(0)
completed = trips[trips["status"]=="Completed"]
def tier(fare):
    if fare < 5000:   return "Budget"
    elif fare < 15000: return "Economy"
    elif fare < 50000: return "Standard"
    else:              return "Premium"
completed = completed.copy()
completed["fare_tier"] = completed["trip_fare_pkr"].apply(tier)
result = completed.groupby("fare_tier").agg(trips=("trip_id","count"),avg_fare=("trip_fare_pkr","mean")).round(0)
print(result.to_string())"""),
        ("Hard","RFM segmentation","Full RFM analysis with scoring",
         """import pandas as pd
from datetime import datetime
trips = dfs["trips"].copy()
trips["pickup_datetime"] = pd.to_datetime(trips["pickup_datetime"], errors="coerce")
trips["trip_fare_pkr"]   = pd.to_numeric(trips["trip_fare_pkr"],    errors="coerce").fillna(0)
c = trips[trips["status"]=="Completed"]
snap = c["pickup_datetime"].max()
rfm = c.groupby("customer_id").agg(
    Recency=("pickup_datetime", lambda x: (snap-x.max()).days),
    Frequency=("trip_id","count"),
    Monetary=("trip_fare_pkr","sum"),
).reset_index()
for col in ["Recency","Frequency","Monetary"]:
    asc = col == "Recency"
    try:
        rfm[f"{col}_Score"] = pd.qcut(rfm[col], 4, labels=[4,3,2,1] if asc else [1,2,3,4], duplicates="drop")
    except:
        rfm[f"{col}_Score"] = 2
rfm["RFM"] = rfm["Recency_Score"].astype(int)+rfm["Frequency_Score"].astype(int)+rfm["Monetary_Score"].astype(int)
rfm["Segment"] = pd.cut(rfm["RFM"],[0,4,7,10,12],labels=["At Risk","Regular","Loyal","Champion"])
print(rfm["Segment"].value_counts().to_string())
result = rfm.sort_values("RFM",ascending=False).head(10)"""),
        ("Hard","ETL transform","Complete ETL transform: cast, clean, validate, flag",
         """import pandas as pd, numpy as np
raw = dfs["trips"].copy()
print(f"Raw shape: {raw.shape}")
# Type casting
raw["pickup_datetime"]  = pd.to_datetime(raw["pickup_datetime"],  errors="coerce")
raw["dropoff_datetime"] = pd.to_datetime(raw["dropoff_datetime"], errors="coerce")
raw["trip_fare_pkr"]    = pd.to_numeric(raw["trip_fare_pkr"],     errors="coerce").fillna(0).clip(lower=0)
raw["distance_km"]      = pd.to_numeric(raw["distance_km"],       errors="coerce").fillna(0).clip(lower=0)
# Derived columns
raw["duration_hrs"] = (raw["dropoff_datetime"] - raw["pickup_datetime"]).dt.total_seconds() / 3600
raw["revenue_per_km"] = (raw["trip_fare_pkr"] / raw["distance_km"].replace(0, np.nan)).round(2)
# DQ flags
raw["_dq_reversed"]  = raw["dropoff_datetime"] < raw["pickup_datetime"]
raw["_dq_zero_fare"] = raw["trip_fare_pkr"] <= 0
# Dedup
staged = raw.sort_values("pickup_datetime",ascending=False).drop_duplicates("trip_id")
print(f"Staged: {staged.shape}")
print(f"DQ issues: reversed={raw['_dq_reversed'].sum()}, zero_fare={raw['_dq_zero_fare'].sum()}")
result = staged.head(5)"""),
        ("Hard","machine learning prep","Prepare features for a fare prediction model",
         """import pandas as pd, numpy as np
trips = dfs["trips"].copy()
trips["trip_fare_pkr"]    = pd.to_numeric(trips["trip_fare_pkr"], errors="coerce").fillna(0)
trips["distance_km"]      = pd.to_numeric(trips["distance_km"],  errors="coerce").fillna(0)
trips["pickup_datetime"]  = pd.to_datetime(trips["pickup_datetime"], errors="coerce")
trips["duration_days"]    = pd.to_numeric(trips["duration_days"], errors="coerce").fillna(0)
c = trips[trips["status"]=="Completed"].copy()
# Feature engineering
c["hour"]        = c["pickup_datetime"].dt.hour
c["day_of_week"] = c["pickup_datetime"].dt.dayofweek
c["is_weekend"]  = (c["day_of_week"] >= 5).astype(int)
c["is_intercity"]= (c["pickup_city"] != c["dropoff_city"]).astype(int)
c["with_driver_int"] = pd.to_numeric(c["with_driver"].map({"True":1,"False":0,"true":1,"false":0}),errors="coerce").fillna(0).astype(int)
features = ["distance_km","duration_days","hour","day_of_week","is_weekend","is_intercity","with_driver_int"]
X = c[features].dropna()
y = c.loc[X.index,"trip_fare_pkr"]
print(f"Training set: {X.shape[0]} rows, {X.shape[1]} features")
print(f"Target mean: PKR {y.mean():,.0f}")
result = X.describe().round(2)"""),
        ("Expert","custom DQ framework","Build a reusable DQ check class",
         """import pandas as pd
from dataclasses import dataclass
from typing import Callable, List

@dataclass
class DQCheck:
    name: str
    check_fn: Callable
    threshold: float = 0.0  # max allowed fail rate

class DQFramework:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.results = []

    def add_check(self, check: DQCheck):
        fail_mask = check.check_fn(self.df)
        fail_rate = fail_mask.mean()
        self.results.append({
            "Check": check.name,
            "Fails": int(fail_mask.sum()),
            "Fail Rate": f"{fail_rate*100:.2f}%",
            "Threshold": f"{check.threshold*100:.1f}%",
            "Status": "✅ PASS" if fail_rate <= check.threshold else "❌ FAIL"
        })

    def report(self): return pd.DataFrame(self.results)

trips = dfs["trips"].copy()
trips["trip_fare_pkr"] = pd.to_numeric(trips["trip_fare_pkr"], errors="coerce").fillna(0)
trips["pickup_datetime"] = pd.to_datetime(trips["pickup_datetime"], errors="coerce")
trips["dropoff_datetime"] = pd.to_datetime(trips["dropoff_datetime"], errors="coerce")

dq = DQFramework(trips)
dq.add_check(DQCheck("trip_id not null",     lambda d: d["trip_id"].isna(), threshold=0.0))
dq.add_check(DQCheck("fare >= 0",            lambda d: d["trip_fare_pkr"] < 0, threshold=0.01))
dq.add_check(DQCheck("timeline valid",       lambda d: d["dropoff_datetime"] < d["pickup_datetime"], threshold=0.05))
dq.add_check(DQCheck("status not null",      lambda d: d["status"].isna(), threshold=0.0))

result = dq.report()
print(result.to_string(index=False))"""),
    ]

    import numpy as np
    for i,(diff,cat,title,code) in enumerate(PY_QS[:20]):
        _pid2 = f"py_{i}_{hash(title)}"
        _solved2 = st.session_state.intv_progress.get(_pid2, False)
        with st.expander(f"{'✅ ' if _solved2 else ''}{diff} [{cat}] — {title}"):
            st.markdown(f"{_diff(diff)} &nbsp; <span style='font-size:.7rem;color:{STEEL};'>{cat}</span>", unsafe_allow_html=True)
            _show2 = st.checkbox("Show Code", key=f"show_py_{_pid2}")
            if _show2:
                st.code(code.strip(), language="python")
                if st.button("▶ Run", key=f"run_py_{_pid2}"):
                    buf = io.StringIO()
                    ns  = {"dfs":dfs,"pd":pd,"np":np,"result":None}
                    with contextlib.redirect_stdout(buf):
                        try: exec(compile(code,"<q>","exec"),ns)
                        except Exception as e: print(f"Error: {e}")
                    if buf.getvalue(): st.code(buf.getvalue(), language="text")
                    if isinstance(ns.get("result"),pd.DataFrame):
                        st.dataframe(ns["result"], use_container_width=True, height=200, hide_index=True)
            if st.checkbox("Mark done",key=f"done_py_{_pid2}",value=_solved2):
                st.session_state.intv_progress[_pid2] = True


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3: PYSPARK QUESTIONS (15)
# ══════════════════════════════════════════════════════════════════════════════
with TAB[3]:
    st.markdown(_h2("PySpark Interview Questions (15)","⚡"), unsafe_allow_html=True)
    st.markdown(_card("PySpark code is shown for learning — execution requires a Spark cluster. Code is conceptually correct against the Rent-A-Car schema.",l=TEAL,p="9px 14px"), unsafe_allow_html=True)

    SPARK_QS = [
        ("Easy","What is the difference between RDD, DataFrame, and Dataset in Spark?",
"""# RDD: low-level, untyped, no optimiser
rdd = sc.textFile("trips.csv").filter(lambda l: "Completed" in l)

# DataFrame: SQL-like API with Catalyst optimiser
df = spark.read.csv("trips.csv", header=True, inferSchema=True)
df.filter(df.status == "Completed").select("trip_id","trip_fare_pkr")

# Dataset (Scala/Java): typed DataFrame — not in PySpark
# In Python, use DataFrame — it's the recommended API
print("Key: Always prefer DataFrame over RDD in modern PySpark")"""),
        ("Easy","How do you read a CSV file and register it as a temp view?",
"""trips_df = spark.read.csv(
    "data/csv/oltp/oltp_trips.csv",
    header=True,
    inferSchema=True
)
trips_df.createOrReplaceTempView("trips")  # register for SQL queries
result = spark.sql("SELECT COUNT(*) FROM trips WHERE status = 'Completed'")
result.show()"""),
        ("Easy","What is lazy evaluation in Spark? Give an example.",
"""from pyspark.sql import functions as F

# LAZY: these transformations don't execute yet
df = spark.read.parquet("trips.parquet")  # no execution
filtered = df.filter(F.col("status") == "Completed")  # no execution
selected = filtered.select("trip_id","trip_fare_pkr")  # no execution

# ACTION: this triggers execution of the entire chain
selected.show(5)   # NOW it runs
count = selected.count()  # another action = another scan!

# Optimise: cache if multiple actions on same data
selected.cache()
selected.show(5)
selected.count()  # reads from cache, not disk"""),
        ("Medium","How do you perform a GROUP BY aggregation in PySpark?",
"""from pyspark.sql import functions as F

trips = spark.read.csv("trips.csv", header=True, inferSchema=True)

# PySpark DataFrame API
result = (trips
    .filter(F.col("status") == "Completed")
    .groupBy("booking_type")
    .agg(
        F.count("trip_id").alias("trips"),
        F.round(F.sum("trip_fare_pkr"),0).alias("revenue_pkr"),
        F.round(F.avg("trip_fare_pkr"),0).alias("avg_fare"),
    )
    .orderBy(F.col("revenue_pkr").desc())
)
result.show()

# Equivalent SQL
spark.sql("""
    SELECT booking_type, COUNT(*) as trips, 
           ROUND(SUM(trip_fare_pkr),0) as revenue_pkr
    FROM trips WHERE status='Completed' 
    GROUP BY booking_type ORDER BY revenue_pkr DESC
""").show()"""),
        ("Medium","How do you use window functions in PySpark?",
"""from pyspark.sql import functions as F
from pyspark.sql.window import Window

trips = spark.read.csv("trips.csv", header=True, inferSchema=True)

# Window spec: partition by fleet, order by pickup datetime
w = Window.partitionBy("fleet_id").orderBy("pickup_datetime")
w_unb = Window.partitionBy("fleet_id").orderBy("pickup_datetime").rowsBetween(
    Window.unboundedPreceding, Window.currentRow)

result = trips.filter(F.col("status")=="Completed").select(
    "trip_id","fleet_id","pickup_datetime","trip_fare_pkr",
    F.row_number().over(w).alias("trip_number_in_fleet"),
    F.lag("trip_fare_pkr",1).over(w).alias("prev_fare"),
    F.sum("trip_fare_pkr").over(w_unb).alias("fleet_cumulative_rev"),
)
result.show(10)"""),
        ("Medium","Explain the difference between narrow and wide transformations.",
"""# NARROW: each partition produces output from ONE input partition
# No shuffle needed — fast!
narrow_examples = [
    "map()",     # row → row
    "filter()",  # remove rows
    "flatMap()", # row → multiple rows
    "select()",  # column projection
    "withColumn()" # add column
]

# WIDE: requires data from MULTIPLE partitions — causes a SHUFFLE
# Shuffle = most expensive operation in Spark!
wide_examples = [
    "groupBy().agg()",  # needs all same-key rows on one partition
    "join()",           # needs matching keys co-located
    "distinct()",       # needs to compare all rows
    "repartition()",    # redistributes data
    "orderBy()",        # global sort requires full shuffle
]

print("Minimise wide transformations. Filter early to reduce shuffle size.")
print("Use partitionBy() wisely to control how data is distributed.")"""),
        ("Medium","How do you handle skewed data (data skew) in Spark joins?",
"""from pyspark.sql import functions as F

# Problem: one key has millions of rows, others have few
# Result: one task runs for hours, others finish in seconds

# SOLUTION 1: Broadcast join for small table (< 10MB)
from pyspark.sql.functions import broadcast
small_df = spark.read.csv("fleets.csv", header=True)
trips_df = spark.read.csv("trips.csv", header=True, inferSchema=True)
result = trips_df.join(broadcast(small_df), "fleet_id")  # no shuffle for small side!

# SOLUTION 2: Salting for skewed keys
import random
N_SALT = 10
# Add random salt to the big table key
trips_salted = trips_df.withColumn("salt", (F.rand()*N_SALT).cast("int"))
trips_salted = trips_salted.withColumn("salted_key", F.concat("fleet_id", F.lit("_"), "salt"))

# Explode the small table to match all salt values
from pyspark.sql.functions import array, explode, lit
fleet_expanded = (small_df
    .withColumn("salt_arr", array([lit(i) for i in range(N_SALT)]))
    .withColumn("salt", explode("salt_arr"))
    .withColumn("salted_key", F.concat("fleet_id", F.lit("_"), "salt")))

result = trips_salted.join(fleet_expanded, "salted_key")
print("Salting distributes skewed key across", N_SALT, "partitions")"""),
        ("Hard","Implement an incremental load pattern in PySpark",
"""from pyspark.sql import functions as F
from pyspark.sql.types import *

# Read existing DWH fact table (Parquet — Delta Lake in production)
existing = spark.read.parquet("s3://bucket/dwh/fact_trips/")

# Get watermark: max date already loaded
watermark = existing.agg(F.max("pickup_datetime")).collect()[0][0]
print(f"Watermark: {watermark}")

# Read only NEW records from source
new_data = (spark.read.csv("s3://bucket/raw/trips/*.csv", header=True, inferSchema=True)
            .filter(F.col("pickup_datetime") > watermark))

print(f"New rows: {new_data.count()}")

# Transform new data
new_staged = new_data.select(
    F.col("trip_id"),
    F.to_timestamp("pickup_datetime").alias("pickup_datetime"),
    F.col("trip_fare_pkr").cast(DoubleType()),
    F.col("status"),
    F.current_timestamp().alias("_loaded_at"),
    F.lit("incremental").alias("_load_type"),
)

# UPSERT: Delta Lake merge (production pattern)
# DeltaTable.forPath(spark,"s3://bucket/dwh/fact_trips/").alias("target")
#   .merge(new_staged.alias("src"), "target.trip_id = src.trip_id")
#   .whenMatchedUpdateAll()
#   .whenNotMatchedInsertAll()
#   .execute()

# Simplified: append-only for non-Delta
new_staged.write.mode("append").parquet("s3://bucket/dwh/fact_trips/")
print("Incremental load complete")"""),
        ("Hard","How do you use PySpark with Delta Lake for ACID transactions?",
"""# Delta Lake = ACID transactions on cloud storage (S3/ADLS)
# from delta.tables import DeltaTable (pip install delta-spark)

# Write as Delta
trips_df.write.format("delta").mode("overwrite").save("s3://bucket/dwh/trips_delta/")

# Read Delta
trips_delta = spark.read.format("delta").load("s3://bucket/dwh/trips_delta/")

# UPSERT (MERGE) — like SQL MERGE statement
from delta.tables import DeltaTable
dt = DeltaTable.forPath(spark, "s3://bucket/dwh/trips_delta/")
dt.alias("target").merge(
    new_data.alias("source"),
    "target.trip_id = source.trip_id"
).whenMatchedUpdate(set={
    "trip_fare_pkr": "source.trip_fare_pkr",
    "_loaded_at": "current_timestamp()",
}).whenNotMatchedInsert(values={
    "trip_id": "source.trip_id",
    "trip_fare_pkr": "source.trip_fare_pkr",
}).execute()

# Time travel: read data as of yesterday
trips_yesterday = spark.read.format("delta").option("timestampAsOf","2026-09-25").load("s3://bucket/dwh/trips_delta/")"""),
        ("Hard","Explain Spark partitioning strategy for a DWH load",
"""from pyspark.sql import functions as F

# Problem: writing 18,000 trips to Parquet for daily analytics
# Bad: 1 huge file = no parallelism, no partition pruning
trips_df.coalesce(1).write.parquet("s3://trips/")  # ← WRONG

# Good: partition by date for efficient filtering
trips_df.write.partitionBy("pickup_year","pickup_month").parquet("s3://trips/")
# Creates: s3://trips/pickup_year=2026/pickup_month=9/part-0001.parquet
# Query with date filter → Spark skips irrelevant partitions!

# Even better: partition by date + bucket by fleet for join efficiency
trips_df.write \
    .partitionBy("pickup_year") \
    .bucketBy(8, "fleet_id") \
    .sortBy("fleet_id","pickup_datetime") \
    .saveAsTable("trips_bucketed")
# Queries joining on fleet_id avoid shuffle → co-located!

# Rules:
# 1. Partition by the most common filter column (usually date)
# 2. Partition cardinality: aim for 128MB-1GB per partition file
# 3. Don't over-partition (millions of tiny files = metadata overhead)
# 4. Bucket for frequently joined columns"""),
        ("Expert","Structured Streaming: process new trip events in real time",
"""from pyspark.sql import functions as F
from pyspark.sql.types import *

schema = StructType([
    StructField("trip_id",       StringType()),
    StructField("fleet_id",      StringType()),
    StructField("trip_fare_pkr", DoubleType()),
    StructField("pickup_datetime", TimestampType()),
    StructField("status",        StringType()),
])

# Read streaming data from Kafka
stream = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers","kafka:9092") \
    .option("subscribe","trips-events") \
    .load()

# Parse JSON events
trips_stream = stream.select(
    F.from_json(F.col("value").cast("string"), schema).alias("data")
).select("data.*")

# Aggregate: revenue per fleet per 5-minute window
revenue_stream = trips_stream \
    .filter(F.col("status") == "Completed") \
    .withWatermark("pickup_datetime","10 minutes") \
    .groupBy(
        F.window("pickup_datetime","5 minutes"),
        F.col("fleet_id")
    ) \
    .agg(F.sum("trip_fare_pkr").alias("window_revenue"))

# Write to Delta Lake
query = revenue_stream.writeStream \
    .format("delta") \
    .outputMode("append") \
    .option("checkpointLocation","s3://bucket/checkpoints/") \
    .start("s3://bucket/streaming/revenue_5min/")

query.awaitTermination()"""),
    ]

    for i,(diff,title,code) in enumerate(SPARK_QS):
        _pid3 = f"spark_{i}_{hash(title)}"
        _solved3 = st.session_state.intv_progress.get(_pid3,False)
        with st.expander(f"{'✅ ' if _solved3 else ''}{diff} — {title[:65]}…" if len(title)>65 else f"{'✅ ' if _solved3 else ''}{diff} — {title}"):
            _show3 = st.checkbox("Show Code",key=f"show_spark_{_pid3}")
            if _show3:
                st.code(code.strip(), language="python")
            if st.checkbox("Mark done",key=f"done_spark_{_pid3}",value=_solved3):
                st.session_state.intv_progress[_pid3] = True


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4: CONCEPTS & TERMS
# ══════════════════════════════════════════════════════════════════════════════
with TAB[4]:
    st.markdown(_h2("Concepts & Terms","📚"), unsafe_allow_html=True)
    _cterm = st.text_input("Search:", placeholder="e.g. watermark, SCD, partition...", key="concept_search")

    CONCEPTS = {
        "Core DE Concepts": [
            ("ETL vs ELT","ETL: transform BEFORE loading (in separate tool like Spark). ELT: load raw THEN transform inside DWH (dbt, SQL). Modern DWH favour ELT — compute inside DWH is cheap."),
            ("Idempotency","Running a pipeline multiple times gives the same result. Essential for safe retries. Use INSERT OR REPLACE or INSERT WHERE NOT EXISTS."),
            ("Watermark","The timestamp of the last successfully processed event. Incremental loads use: WHERE event_time > watermark."),
            ("Late-arriving data","Events that arrive after their logical time window has passed. Handle with grace periods and reprocessing capabilities."),
            ("Backfill","Re-processing historical data, usually after a bug fix or new metric definition. Requires idempotent pipelines."),
            ("CDC (Change Data Capture)","Capturing database changes (INSERT/UPDATE/DELETE) in real-time. Tools: Debezium, AWS DMS. Enables streaming ingestion from OLTP."),
            ("Schema evolution","Handling changes to data schemas over time without breaking downstream consumers. Delta Lake and Iceberg support this natively."),
            ("Data lineage","Tracking where data came from, how it was transformed, and where it flows to. Critical for debugging and compliance."),
        ],
        "Architecture": [
            ("Lambda Architecture","Two pipelines: Batch (accurate, slow) + Speed (fast, approximate). Merge in serving layer. Complex but handles both batch accuracy and real-time needs."),
            ("Kappa Architecture","Single streaming pipeline for both real-time and historical. Simpler than Lambda but reprocessing is expensive."),
            ("Medallion (Bronze/Silver/Gold)","Three-layer quality refinement: Bronze (raw) → Silver (cleaned) → Gold (business-ready). Used by Databricks."),
            ("Data Lakehouse","Combines data lake storage (cheap, S3/ADLS) with ACID transactions and SQL. Delta Lake, Iceberg, Hudi."),
            ("Data Mesh","Decentralised architecture. Each domain team owns their data as a product. Requires strong governance."),
            ("OLTP","Optimised for writes. Row-stored. Normalised (3NF). High concurrency. Low latency. Source of truth."),
            ("OLAP","Optimised for reads. Column-stored. Denormalised. Complex queries. Historical analysis."),
        ],
        "Data Modeling": [
            ("Star Schema","Kimball. One central fact table + dimension tables. Fast queries, simple JOINs. Industry standard for DWH."),
            ("Snowflake Schema","Star schema with normalised dimensions (sub-dimensions). More storage efficient, more JOINs needed."),
            ("Data Vault 2.0","Hub-Link-Satellite. Hubs=business keys, Links=relationships, Satellites=attributes. Fully auditable, handles schema changes."),
            ("SCD Type 1","Overwrite. No history kept. Fast and simple."),
            ("SCD Type 2","Add new row. Full history preserved via valid_from/valid_to/is_current. Most common for analytics."),
            ("SCD Type 6","Hybrid: new row (T2) + update all rows with current value (T1) + previous column (T3). Most flexible."),
            ("Grain","What ONE row represents in a fact table. Always define grain before designing."),
            ("Surrogate Key","System-generated integer PK in DWH. Stable, independent of source system."),
            ("Conformed Dimension","Dimension shared across multiple fact tables. Enables cross-fact queries."),
            ("Bridge Table","Handles many-to-many relationships in dimensional modeling."),
            ("Junk Dimension","Consolidates multiple low-cardinality flags into one dimension."),
            ("Degenerate Dimension","Dimension key stored in fact table with no dimension table (e.g., order_number)."),
        ],
        "Cloud & Tools": [
            ("Snowflake","Cloud DWH. Separation of storage and compute. Virtual warehouses. Zero-copy cloning. Time Travel. SQL-based. Best for BI/analytics."),
            ("Databricks","Apache Spark managed platform. Delta Lake. MLflow for ML. Unity Catalog for governance. Best for data engineering + ML."),
            ("dbt","Transform data with SQL SELECTs. Tests, documentation, lineage, CI/CD. Works inside your DWH."),
            ("Airflow","Workflow orchestration. DAGs. Schedule and monitor pipelines. Python-based. Most popular open-source orchestrator."),
            ("Kafka","Distributed event streaming. High throughput. Durable. Publish-subscribe. Used for real-time data pipelines."),
            ("Delta Lake","Open format for ACID transactions on data lakes. Time travel. Schema enforcement. Built into Databricks."),
            ("Apache Iceberg","Open table format. Multi-engine (Spark, Flink, Trino). Partition evolution. Time travel."),
            ("Great Expectations","Python data quality library. Define expectations, validate data, generate documentation."),
            ("DuckDB","In-process columnar analytical database. SQL. Reads Parquet/CSV natively. Perfect for local analytics."),
        ],
        "SQL & Performance": [
            ("Predicate pushdown","Query optimizer pushes WHERE filters to the data scan level, reducing bytes read. Automatic in columnar DBs."),
            ("Column pruning","Only reading columns actually needed by the query. SELECT * is anti-pattern in columnar storage."),
            ("Partition pruning","Skipping partitions that don't match filter conditions. Requires filtering on partition key."),
            ("Materialised view","Pre-computed query result stored as a table. Fast to query. Must be refreshed. Good for slow aggregations."),
            ("Index (B-tree)","Sorted data structure enabling O(log n) lookups. Good for high-cardinality equality/range queries. Slower writes."),
            ("Broadcast join","Small table is broadcast to all workers, avoiding expensive shuffle. Use for tables < 10MB."),
            ("Hash join","Build hash table on smaller side, probe with larger. O(n+m) time. Used when both sides are large."),
            ("Z-order clustering","DuckDB/Delta: sort data by multiple columns to improve multi-dimensional filtering."),
        ],
    }

    for cat, terms in CONCEPTS.items():
        _filtered_terms = [(t,d) for t,d in terms if not _cterm or _cterm.lower() in t.lower() or _cterm.lower() in d.lower()]
        if not _filtered_terms: continue
        st.markdown(_h3(cat, TEAL), unsafe_allow_html=True)
        for term,defn in _filtered_terms:
            st.markdown(_card(f'<b style="color:{AMBER};font-size:.84rem;">{term}</b><br>'
                              f'<span style="font-size:.77rem;color:{TEXT};">{defn}</span>',l=AMBER,p="9px 14px"), unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 5: SYSTEM DESIGN
# ══════════════════════════════════════════════════════════════════════════════
with TAB[5]:
    st.markdown(_h2("System Design Questions","🏗️"), unsafe_allow_html=True)
    DESIGNS = [
        ("Design a data pipeline for a ride-hailing app at 1M trips/day",
         """ANSWER:
1. REQUIREMENTS:
   - 1M trips/day (~12 trips/sec avg, 50 trips/sec peak)
   - Real-time: driver positions (< 5 sec latency)
   - Analytical: daily revenue, fleet KPIs (< 1 hr latency)
   - GDPR: anonymise PII, right to erasure

2. ARCHITECTURE: Lambda (batch accuracy + real-time speed)

3. INGESTION:
   Mobile app → Kafka (trip events: start, GPS updates, payment, end)
   Backend DB → Debezium CDC → Kafka (customer/driver changes)
   
4. BATCH LAYER (our platform does this):
   Kafka → S3 (raw Parquet) → Spark/dbt → Snowflake/Redshift
   Medallion: Bronze (raw) → Silver (cleaned) → Gold (star schema)
   
5. SPEED LAYER:
   Kafka → Flink/Spark Streaming → Redis (live positions)
   Aggregate revenue every 5min → real-time dashboard
   
6. SERVING:
   Batch: Tableau/Power BI via Snowflake SQL
   Real-time: REST API → mobile app, ops dashboard

7. SCHEMA:
   fact_trips (1 row/trip, daily batch)
   fact_gps_events (1 row/GPS ping, streaming)
   dim_driver, dim_vehicle, dim_customer (SCD2)

8. GDPR:
   Anonymise location after 24hrs
   Right to erasure: soft delete → anonymise PII
   Retention: 3yr trips, 5yr customers, 7yr invoices"""),
        ("Design Snowflake schema for a multi-region e-commerce DWH",
         """1. REQUIREMENTS: 50M orders/day, 5 regions, multi-currency

2. FACT TABLES:
   fact_orders: grain=1 order, measures=amount,discount,tax
   fact_order_items: grain=1 line item (sub-fact)
   fact_returns: grain=1 return event

3. DIMENSIONS:
   dim_date (conformed)
   dim_customer (SCD2: changes tracked)
   dim_product (SCD1: overwrite prices)
   dim_location (country/region/city hierarchy)
   dim_promotion (effective dates)
   dim_currency (exchange rates by date)

4. SLOWLY CHANGING:
   Prices: SCD Type 1 (overwrite — don't need historical price)
   Customer address: SCD Type 2 (track where they were at order time)
   Product category: SCD Type 2 (reclassifications affect history)

5. SNOWFLAKE SPECIFICS:
   Multi-cluster virtual warehouse (scale out for peak loads)
   Zero-copy clones for dev/test environments
   Dynamic data masking for PII fields
   Row access policies for regional data isolation

6. PARTITIONING:
   Cluster key: (order_date, region_id) → fast by date + region
   Micro-partition pruning eliminates most data automatically"""),
    ]
    for title, answer in DESIGNS:
        with st.expander(f"**{title[:70]}**"):
            if st.checkbox("Show Answer", key=f"design_{hash(title)}"):
                st.code(answer.strip(), language="text")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 6: SCENARIO PROBLEMS
# ══════════════════════════════════════════════════════════════════════════════
with TAB[6]:
    st.markdown(_h2("Scenario-Based Problems","🧩"), unsafe_allow_html=True)
    SCENARIOS = [
        ("Your daily ETL failed silently — revenue shows zero. How do you debug?",
         """STEP-BY-STEP DEBUGGING:
1. Check load_log:   SELECT * FROM meta.load_log ORDER BY started_at DESC LIMIT 5;
2. Check source exists: SELECT COUNT(*) FROM trips WHERE pickup_datetime::DATE = yesterday
3. Check staging: SELECT COUNT(*) FROM staging.stg_trips WHERE _loaded_at::DATE = today
4. Check facts: SELECT COUNT(*) FROM fact_trips WHERE pickup_date_key = YYYYMMDD
5. Check DQ: SELECT * FROM meta.dq_issues WHERE detected_at::DATE = today
6. Check schema: Did source add/drop a column? TRY_CAST would silently produce NULLs
7. Check row counts vs yesterday: compare COUNT(*) day-over-day

PREVENTION:
- Assert row counts after each step: fail if < 95% of yesterday
- Never allow silent failures — always catch and log
- Set up Slack/email alerts for ETL failures"""),
        ("A dashboard metric is wrong. The SQL looks correct. How do you trace the issue?",
         """ROOT CAUSE ANALYSIS:
1. Reproduce: Run the exact dashboard SQL manually — same wrong result?
2. Check grain: Is the fact table grain correct? Are there duplicate rows?
   SELECT trip_id, COUNT(*) FROM fact_trips GROUP BY 1 HAVING COUNT(*)>1
3. Check fan-out: Did a JOIN multiply rows?
   SELECT COUNT(*) FROM fact_trips ft JOIN dim_customer dc ON ft.customer_sk=dc.customer_sk
   -- If > COUNT(*) FROM fact_trips → SCD2 dim has multiple current rows!
4. Check SCD2 filter: WHERE is_current = true missing?
5. Check date filter: is it picking up correct time window?
6. Check NULL handling: AVG ignores NULLs, SUM treats NULL as 0 after COALESCE
7. Lineage: trace from mart → fact → staging → raw → CSV"""),
    ]
    for scenario, answer in SCENARIOS:
        with st.expander(f"**{scenario[:70]}**"):
            if st.checkbox("Show Answer", key=f"scen_{hash(scenario)}"):
                st.code(answer.strip(), language="text")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 7: BEHAVIOURAL
# ══════════════════════════════════════════════════════════════════════════════
with TAB[7]:
    st.markdown(_h2("Behavioural Questions (STAR Method)","💬"), unsafe_allow_html=True)
    st.markdown(_card("<b>STAR:</b> <b>S</b>ituation, <b>T</b>ask, <b>A</b>ction, <b>R</b>esult. Always quantify results. Practice out loud.",l=TEAL,p="9px 14px"), unsafe_allow_html=True)
    BQ = [
        ("Tell me about a time you improved a slow pipeline.","S: Monthly revenue report took 4 hours.\nT: Reduce to under 30 minutes.\nA: Profiled with EXPLAIN ANALYZE. Found full table scan on 50M rows. Added date partitioning, pre-aggregated mart layer, replaced DISTINCT with ROW_NUMBER dedup.\nR: 4 hours → 18 minutes. Dashboard available by 7am."),
        ("Describe a data quality issue you found and fixed.","S: Finance noticed revenue 15% higher than expected.\nT: Investigate discrepancy.\nA: DQ check found duplicate invoices — CDC double-fire. Added QUALIFY dedup to staging. Added uniqueness test.\nR: Revenue corrected. Test prevents recurrence."),
        ("How do you handle disagreements about data definitions?","S: Marketing: active=logged in. Data: active=trip in 30 days.\nT: Align on definition.\nA: Facilitated meeting. Documented both in data dictionary. Created two metrics: logged_in_users + active_customers_30d.\nR: Both teams satisfied. No more definitional arguments."),
        ("Tell me about a time you had to learn a new technology quickly.","S: Team adopted dbt with 2-week deadline.\nT: Learn dbt and migrate 30 SQL transforms.\nA: Completed dbt fundamentals cert. Paired with senior engineer. Migrated models incrementally, added tests.\nR: All 30 models migrated in 10 days. Test coverage went from 0% to 85%."),
        ("Describe how you ensure data pipeline reliability.","S: Production pipelines failing every few weeks.\nT: Improve reliability to 99.9% uptime.\nA: Added circuit breakers (halt pipeline if DQ drops >5%). Monitoring dashboard. Alerting for row count anomalies. Idempotent loads with retry logic.\nR: Pipeline failures reduced 90%. Mean time to recovery from 4 hours to 20 minutes."),
    ]
    for q,a in BQ:
        with st.expander(f"**{q}**"):
            if st.checkbox("Show STAR Answer", key=f"bq_{hash(q)}"):
                st.markdown(_card(a.replace("\n","<br>"),l=STEEL,p="10px 14px"), unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 8: PROGRESS TRACKER
# ══════════════════════════════════════════════════════════════════════════════
with TAB[8]:
    st.markdown(_h2("Progress Tracker","📊"), unsafe_allow_html=True)
    _prog = st.session_state.intv_progress
    _total_q = len(SQL_QS) + len(PY_QS) + len(SPARK_QS)
    _done_q  = sum(1 for v in _prog.values() if v)
    st.progress(_done_q/_total_q if _total_q else 0, text=f"{_done_q}/{_total_q} questions completed")
    _sql_done = sum(1 for k,v in _prog.items() if k.startswith("sql_") and v)
    _py_done  = sum(1 for k,v in _prog.items() if k.startswith("py_")  and v)
    _sp_done  = sum(1 for k,v in _prog.items() if k.startswith("spark_") and v)
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Total Done",    str(_done_q))
    c2.metric("SQL Done",      f"{_sql_done}/{len(SQL_QS)}")
    c3.metric("Python Done",   f"{_py_done}/{len(PY_QS)}")
    c4.metric("PySpark Done",  f"{_sp_done}/{len(SPARK_QS)}")
    _prog_data = pd.DataFrame([
        {"Category":"SQL",    "Completed":_sql_done,  "Total":len(SQL_QS)},
        {"Category":"Python", "Completed":_py_done,   "Total":len(PY_QS)},
        {"Category":"PySpark","Completed":_sp_done,   "Total":len(SPARK_QS)},
    ])
    _prog_data["Remaining"] = _prog_data["Total"] - _prog_data["Completed"]
    fig_prog = px.bar(_prog_data, x="Category", y=["Completed","Remaining"],
                      barmode="stack", template="plotly_dark",
                      color_discrete_sequence=[TEAL,BD],
                      title="Progress by Category")
    fig_prog.update_layout(height=280,paper_bgcolor="rgba(0,0,0,0)",
                           plot_bgcolor="rgba(0,0,0,0)",margin=dict(t=40,b=0,l=0,r=0))
    st.plotly_chart(fig_prog, use_container_width=True)
    if st.button("Reset All Progress", key="reset_progress"):
        st.session_state.intv_progress = {}
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 9: STUDY PLAN
# ══════════════════════════════════════════════════════════════════════════════
with TAB[9]:
    st.markdown(_h2("8-Week Study Plan","📋"), unsafe_allow_html=True)
    PLAN = [
        ("Week 1","SQL Fundamentals","Joins (all 6 types), GROUP BY, HAVING, subqueries, NULL handling",     "Complete SQL Easy + Medium questions"),
        ("Week 2","Advanced SQL",    "Window functions, CTEs, ROLLUP, CUBE, EXPLAIN, performance tuning",    "SQL Hard + Expert + Performance Lab page"),
        ("Week 3","Data Modeling",   "3NF vs Star vs Vault, SCD types 1-6, fact patterns, bridge tables",    "Data Modeling page + Kimball book ch.1-4"),
        ("Week 4","Python + pandas", "ETL transforms, group/merge, outlier detection, RFM, DQ framework",    "Python Questions tab + Data Profiling page"),
        ("Week 5","PySpark",         "RDD vs DF, lazy eval, partitioning, skew, streaming, Delta Lake",       "PySpark tab + PySpark page"),
        ("Week 6","Architecture",    "Lambda/Kappa/Medallion, Snowflake, Databricks, Airflow, Kafka",         "Architecture page + Snowflake page"),
        ("Week 7","Governance/Security","GDPR rights, PII, masking, RLS, data contracts, observability",     "Governance + Security + Contracts pages"),
        ("Week 8","Interview Practice","System design, scenarios, behavioural STAR, mock interviews",         "All interview tabs + AI Tutor for practice"),
    ]
    plan_df = pd.DataFrame(PLAN, columns=["Week","Topic","Focus","Platform Resources"])
    st.dataframe(plan_df, use_container_width=True, height=320, hide_index=True)

    st.markdown(_h3("🏆 Certifications to Target",AMBER), unsafe_allow_html=True)
    certs = [
        ("dbt Analytics Engineering","Free + paid tier","dbtlabs.com — SQL transforms, testing, docs","Most in-demand for analytics engineers"),
        ("Databricks Data Engineer Associate","$200","Spark, Delta Lake, MLflow","Widely recognised for data engineering roles"),
        ("Snowflake SnowPro Core","$175","Snowflake SQL, DWH, performance","Popular for analytics/cloud DWH roles"),
        ("AWS Data Engineer Associate","$300","S3, Glue, Redshift, Kinesis","Good for cloud-native DE roles"),
        ("Google Professional Data Engineer","$200","BigQuery, Dataflow, Pub/Sub","Strong for GCP stack"),
        ("Azure Data Engineer Associate","$165","Azure Data Factory, Synapse, Databricks","Good for Microsoft shops"),
    ]
    c1,c2 = st.columns(2)
    for i,(cert,cost,skills,note) in enumerate(certs):
        (c1 if i%2==0 else c2).markdown(_card(
            f'<b style="color:{TEAL};">{cert}</b> <span style="font-size:.68rem;color:{M};">— {cost}</span><br>'
            f'<span style="font-size:.74rem;color:{TEXT};">Skills: {skills}</span><br>'
            f'<span style="font-size:.7rem;color:{M};">{note}</span>',l=TEAL,p="9px 12px"), unsafe_allow_html=True)
