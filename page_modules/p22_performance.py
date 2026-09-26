"""
p22_performance.py — Query Performance Optimization Lab
Same query 5 ways · Indexing · Partitioning · Column pruning
Predicate pushdown · Materialised views · Anti-patterns
"""
import pandas as pd
import plotly.express as px
import streamlit as st
import duckdb, time
from page_modules._shared import inject, get_data, BRAND, STEEL, GREEN, AMBER, ORANGE, TEXT
inject()
M="#5a7a96"; CB="#141e2b"; BD="#1e2f44"; TEAL="#2A9D8F"; PUR="#6A4C93"
def _card(b,l=BRAND,p="14px 16px"): return f'<div style="background:{CB};border:1px solid {BD};border-left:3px solid {l};border-radius:10px;padding:{p};margin:6px 0;">{b}</div>'
def _h2(t,i=""): return f'<div style="font-size:1.22rem;font-weight:800;color:{TEXT};margin:16px 0 4px;"><span style="color:{BRAND};">{i} </span>{t}</div>'
def _h3(t,c=STEEL): return f'<div style="font-size:.9rem;font-weight:700;color:{c};border-left:3px solid {c};padding-left:8px;margin:10px 0 6px;">{t}</div>'

dfs = get_data()

st.markdown(f'<div style="font-size:1.6rem;font-weight:900;color:{BRAND};">⚡ Query Performance Lab</div>'
            f'<div style="font-size:.8rem;color:{M};">Same query 5 ways · Anti-patterns · Indexing · Column pruning · Optimisation techniques</div>',
            unsafe_allow_html=True)
st.markdown(f"<hr style='border-color:{BD};margin:6px 0 10px'>",unsafe_allow_html=True)

TAB = st.tabs(["🔬 Query Comparison","❌ Anti-Patterns","🗂️ Indexing","✂️ Column Pruning","📦 Materialised Views","💡 Optimisation Rules"])

# ── TAB 0: QUERY COMPARISON ──────────────────────────────────────────────────
with TAB[0]:
    st.markdown(_h2("5 Ways to Write the Same Query","🔬"), unsafe_allow_html=True)
    st.markdown(_card("Goal: Find total revenue per city for completed trips. See how different approaches affect readability and explain output.",l=TEAL), unsafe_allow_html=True)

    QUERIES = {
        "1. Subquery in WHERE (slow)": {
            "sql": """SELECT pickup_city, SUM(trip_fare_pkr) AS revenue
FROM trips
WHERE trip_id IN (
    SELECT trip_id FROM trips WHERE status = 'Completed'
)
GROUP BY pickup_city ORDER BY revenue DESC LIMIT 10""",
            "note": "Subquery in IN() re-executes per row. Avoid for large tables.",
            "good": False
        },
        "2. Correlated subquery (very slow)": {
            "sql": """SELECT DISTINCT pickup_city,
    (SELECT SUM(t2.trip_fare_pkr) FROM trips t2
     WHERE t2.pickup_city = t.pickup_city AND t2.status = 'Completed') AS revenue
FROM trips t
WHERE status = 'Completed'
ORDER BY revenue DESC LIMIT 10""",
            "note": "Executes the subquery once per outer row. N² complexity. Never use this pattern.",
            "good": False
        },
        "3. Simple WHERE + GROUP BY (good)": {
            "sql": """SELECT pickup_city,
    COUNT(*) AS trips,
    ROUND(SUM(trip_fare_pkr), 0) AS revenue
FROM trips
WHERE status = 'Completed'
GROUP BY pickup_city
ORDER BY revenue DESC
LIMIT 10""",
            "note": "Clean, simple, efficient. DuckDB pushes the WHERE filter to the scan.",
            "good": True
        },
        "4. CTE (readable, same performance)": {
            "sql": """WITH completed AS (
    SELECT pickup_city, trip_fare_pkr
    FROM trips
    WHERE status = 'Completed'
)
SELECT pickup_city,
    COUNT(*) AS trips,
    ROUND(SUM(trip_fare_pkr), 0) AS revenue
FROM completed
GROUP BY pickup_city
ORDER BY revenue DESC
LIMIT 10""",
            "note": "CTE improves readability. DuckDB inlines it — same execution plan as approach 3.",
            "good": True
        },
        "5. Pre-aggregated view (best for dashboards)": {
            "sql": """-- Create once (in mart layer):
-- CREATE OR REPLACE VIEW mart.city_revenue AS
-- SELECT pickup_city, COUNT(*) AS trips, SUM(trip_fare_pkr) AS revenue
-- FROM trips WHERE status='Completed' GROUP BY pickup_city;

-- Dashboard query (instant):
SELECT pickup_city, trips, ROUND(revenue, 0) AS revenue
FROM (
    SELECT pickup_city, COUNT(*) AS trips, SUM(trip_fare_pkr) AS revenue
    FROM trips WHERE status='Completed' GROUP BY pickup_city
) t
ORDER BY revenue DESC LIMIT 10""",
            "note": "Pre-aggregate in mart layer. Dashboard queries scan tiny aggregated data, not raw trips.",
            "good": True
        }
    }

    @st.cache_resource
    def get_bench_conn(dfs):
        c = duckdb.connect(":memory:")
        for n,df in dfs.items():
            try: c.register(n,df)
            except: pass
        return c
    _bc = get_bench_conn(dfs)

    _sel = st.selectbox("Select approach:", list(QUERIES.keys()), key="perf_sel")
    _q   = QUERIES[_sel]
    st.code(_q["sql"], language="sql")
    _icon = "✅" if _q["good"] else "❌"
    st.markdown(_card(f'{_icon} <b>Assessment:</b> {_q["note"]}', l=TEAL if _q["good"] else BRAND, p="9px 14px"), unsafe_allow_html=True)

    if st.button("▶ Run + Time It", key="run_bench"):
        _t0 = time.time()
        try:
            _res = _bc.execute(_q["sql"]).fetchdf()
            _t1 = time.time()
            st.metric("Execution time", f"{(_t1-_t0)*1000:.1f} ms")
            st.dataframe(_res, use_container_width=True, height=250, hide_index=True)
        except Exception as e:
            st.error(str(e))

# ── TAB 1: ANTI-PATTERNS ─────────────────────────────────────────────────────
with TAB[1]:
    st.markdown(_h2("SQL Anti-Patterns to Avoid","❌"), unsafe_allow_html=True)
    ANTI = [
        ("SELECT *","Reads ALL columns — even ones you don't need. Wastes I/O on columnar DBs.","SELECT trip_id, trip_fare_pkr, status FROM trips WHERE status='Completed'",BRAND),
        ("COUNT(*) without GROUP BY","Scans entire table just to count rows.","Use COUNT(*) with a WHERE clause or pre-aggregate in a mart view.",AMBER),
        ("NOT IN with NULLs","NOT IN returns empty set if the subquery contains ANY NULL. Silently wrong!","Use NOT EXISTS or LEFT JOIN ... WHERE IS NULL instead.",BRAND),
        ("Implicit type conversion","WHERE customer_id = 42 when customer_id is VARCHAR forces a cast on every row.","Always match types: WHERE customer_id = 'CU00042'",AMBER),
        ("DISTINCT as a bug fix","Adding DISTINCT to fix row multiplication from bad JOINs hides the real problem.","Fix the JOIN — find why rows multiply. DISTINCT is a symptom, not a fix.",BRAND),
        ("ORDER BY in subquery","ORDER BY in a subquery is meaningless (result set order not guaranteed) and wastes CPU.","Only ORDER BY in the outermost query or when using LIMIT.",AMBER),
        ("LIKE '%value%' on large tables","Leading wildcard prevents index use — full table scan every time.","Use full-text search, or restructure query to use a leading constant.",BRAND),
        ("Function on indexed column in WHERE","WHERE YEAR(pickup_datetime) = 2024 prevents index use.","Use range: WHERE pickup_datetime >= '2024-01-01' AND < '2025-01-01'",AMBER),
    ]
    for name,problem,fix,clr in ANTI:
        st.markdown(_card(f'<b style="color:{clr};">❌ {name}</b><br>'
                          f'<span style="font-size:.75rem;color:{TEXT};">Problem: {problem}</span><br>'
                          f'<span style="font-size:.73rem;color:{TEAL};">Fix: {fix}</span>',l=clr,p="9px 14px"), unsafe_allow_html=True)

# ── TAB 2: INDEXING ──────────────────────────────────────────────────────────
with TAB[2]:
    st.markdown(_h2("Indexing Strategy","🗂️"), unsafe_allow_html=True)
    st.markdown(_card("DuckDB is a columnar analytical database — it scans columns, not rows. Indexes work differently than in OLTP databases.",l=STEEL), unsafe_allow_html=True)
    INDEX_GUIDE = [
        ("DuckDB: Column Ordering","DuckDB doesn't use traditional B-tree indexes. Instead, it benefits from physical sort order — if data is sorted by date, date range queries skip entire row groups.","""-- DuckDB: order your data for the most common filter
-- If you always filter by date, order by date:
COPY trips TO 'trips_sorted.parquet' (ORDER BY pickup_datetime);
-- DuckDB will skip row groups outside your date range"""),
        ("PostgreSQL: B-Tree Index","B-tree indexes work well for equality and range queries on high-cardinality columns.","""-- Create index on frequently filtered column
CREATE INDEX idx_trips_status ON trips(status);
CREATE INDEX idx_trips_pickup_dt ON trips(pickup_datetime);
-- Composite index for common query pattern:
CREATE INDEX idx_trips_fleet_date ON trips(fleet_id, pickup_datetime);"""),
        ("Partial Index","Index only a subset of rows — saves space and speeds up common filtered queries.","""-- Index only completed trips (most queries filter on this)
CREATE INDEX idx_completed_trips
ON trips(pickup_datetime, fleet_id)
WHERE status = 'Completed';  -- partial index"""),
        ("When NOT to index","Indexes slow down writes. Don't index columns with low cardinality (e.g. boolean, 2-value status).","""-- BAD: indexing a low-cardinality boolean
CREATE INDEX idx_with_driver ON trips(with_driver);  -- only 2 values!

-- GOOD: index on high-cardinality, frequently filtered
CREATE INDEX idx_customer_id ON trips(customer_id);  -- thousands of values"""),
    ]
    for iname,desc,sql_ex in INDEX_GUIDE:
        with st.expander(f"**{iname}**"):
            c1,c2 = st.columns([1,2])
            with c1: st.markdown(_card(f'<b style="color:{TEAL};">{iname}</b><br><span style="font-size:.75rem;color:{TEXT};">{desc}</span>',l=TEAL,p="10px 14px"), unsafe_allow_html=True)
            with c2: st.code(sql_ex.strip(), language="sql")

# ── TAB 3: COLUMN PRUNING ────────────────────────────────────────────────────
with TAB[3]:
    st.markdown(_h2("Column Pruning & Predicate Pushdown","✂️"), unsafe_allow_html=True)
    st.markdown(_card("In columnar databases (DuckDB, Parquet, BigQuery), only selected columns are read from disk. Selecting fewer columns = dramatically less I/O.",l=AMBER), unsafe_allow_html=True)
    c1,c2 = st.columns(2)
    with c1:
        st.markdown("**❌ Reads 23 columns**")
        st.code("SELECT *\nFROM trips\nWHERE status = 'Completed'\nLIMIT 100", language="sql")
    with c2:
        st.markdown("**✅ Reads only 4 columns (83% less I/O)**")
        st.code("SELECT trip_id, pickup_city, dropoff_city, trip_fare_pkr\nFROM trips\nWHERE status = 'Completed'\nLIMIT 100", language="sql")

    st.markdown(_h3("Predicate Pushdown",TEAL), unsafe_allow_html=True)
    st.markdown(_card("DuckDB automatically pushes WHERE filters as close to the data scan as possible. You can help it by writing WHERE clauses that reference physical ordering columns.",l=TEAL), unsafe_allow_html=True)
    st.code("""-- DuckDB pushes this filter to the Parquet row-group level:
SELECT trip_id, trip_fare_pkr
FROM read_parquet('trips.parquet')
WHERE pickup_datetime >= '2025-01-01'   -- ← pushed to scan
  AND pickup_datetime <  '2026-01-01'   -- ← pushed to scan
  AND status = 'Completed';             -- ← filtered after scan

-- EXPLAIN shows: Filter pushdown: pickup_datetime [2025-2026]
-- Row groups outside that range are skipped entirely""", language="sql")

# ── TAB 4: MATERIALISED VIEWS ────────────────────────────────────────────────
with TAB[4]:
    st.markdown(_h2("Materialised Views vs Regular Views","📦"), unsafe_allow_html=True)
    c1,c2 = st.columns(2)
    with c1: st.markdown(_card(f'<b style="color:{STEEL};">Regular View</b><br><span style="font-size:.76rem;color:{TEXT};">Definition stored, not data. Re-executes query on every SELECT. Always fresh but can be slow for complex aggregations.<br><br>Use when: Source data changes frequently and query is simple.</span>',l=STEEL,p="10px 14px"), unsafe_allow_html=True)
    with c2: st.markdown(_card(f'<b style="color:{TEAL};">Materialised View</b><br><span style="font-size:.76rem;color:{TEXT};">Data is pre-computed and stored. Fast to query. Must be refreshed when source changes. Use REFRESH MATERIALIZED VIEW.<br><br>Use when: Complex aggregation, queried frequently, stale data OK.</span>',l=TEAL,p="10px 14px"), unsafe_allow_html=True)
    st.code("""-- Create a materialised aggregate for dashboards
-- (Use CREATE TABLE for DuckDB equivalent):
CREATE TABLE mart.daily_revenue_mat AS
SELECT
    pickup_datetime::DATE AS trip_date,
    fleet_id,
    COUNT(*)                     AS trips,
    SUM(trip_fare_pkr)           AS revenue_pkr,
    AVG(trip_fare_pkr)           AS avg_fare
FROM trips
WHERE status = 'Completed'
GROUP BY 1, 2;

-- Dashboard queries hit this tiny table instead of scanning all trips:
SELECT * FROM mart.daily_revenue_mat
WHERE trip_date >= '2026-01-01'
ORDER BY revenue_pkr DESC;

-- Refresh: truncate and reload after ETL
DELETE FROM mart.daily_revenue_mat WHERE trip_date >= current_date - 7;
INSERT INTO mart.daily_revenue_mat ... (last 7 days only)""", language="sql")

# ── TAB 5: RULES ─────────────────────────────────────────────────────────────
with TAB[5]:
    st.markdown(_h2("10 Golden Rules of Query Optimisation","💡"), unsafe_allow_html=True)
    rules = [
        ("Select only needed columns","Never SELECT *. Name every column. Columnar DBs only read what you ask for.","✂️",BRAND),
        ("Filter early, filter often","Put WHERE conditions on the smallest possible dataset. Push filters into CTEs.",    "🎯",TEAL),
        ("Join in the right order","Join small → large. Put the smallest table on the left of a JOIN if possible.","🔗",AMBER),
        ("Avoid functions on filter columns","WHERE YEAR(date_col)=2024 breaks pushdown. Use BETWEEN instead.","📅",BRAND),
        ("Use EXPLAIN ANALYZE","Always check the query plan before optimising. Measure, don't guess.","🔍",STEEL),
        ("Aggregate before joining","Pre-aggregate large tables in CTEs before joining. Fewer rows to join.","📊",TEAL),
        ("Materialise repeated subqueries","If you use the same CTE twice, DuckDB may re-execute it. Create a temp table.","📦",AMBER),
        ("Avoid correlated subqueries","Replace with JOINs or window functions. Correlated = N scans per outer row.","🚫",BRAND),
        ("Partition large tables by date","If queries always filter by date, partition by year/month for scan skipping.","📂",STEEL),
        ("Use LIMIT for exploration","Always add LIMIT 100 when exploring. Never scan 18M rows to look at data.","⬇️",TEAL),
    ]
    c1,c2 = st.columns(2)
    for i,(name,desc,ic,c) in enumerate(rules):
        (c1 if i%2==0 else c2).markdown(_card(f'<span style="font-size:1rem;">{ic}</span> <b style="color:{c};font-size:.82rem;">{name}</b><br><span style="font-size:.74rem;color:{TEXT};">{desc}</span>',l=c,p="9px 14px"), unsafe_allow_html=True)
