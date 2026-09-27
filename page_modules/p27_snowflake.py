"""
p27_snowflake.py — Snowflake Cloud Data Warehouse
Architecture · Virtual Warehouses · Time Travel · Zero-Copy Clone
Performance · Pricing · vs Databricks · SQL patterns · Certification prep
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from page_modules._shared import inject, get_data, BRAND, STEEL, GREEN, AMBER, ORANGE, TEXT
inject()
M="#5a7a96"; CB="#141e2b"; BD="#1e2f44"; TEAL="#2A9D8F"; PUR="#6A4C93"
def _card(b,l=BRAND,p="14px 16px"): return f'<div style="background:{CB};border:1px solid {BD};border-left:3px solid {l};border-radius:10px;padding:{p};margin:6px 0;">{b}</div>'
def _h2(t,i=""): return f'<div style="font-size:1.22rem;font-weight:800;color:{TEXT};margin:16px 0 4px;"><span style="color:{BRAND};">{i} </span>{t}</div>'
def _h3(t,c=STEEL): return f'<div style="font-size:.9rem;font-weight:700;color:{c};border-left:3px solid {c};padding-left:8px;margin:10px 0 6px;">{t}</div>'

dfs = get_data()

st.markdown(
    f'<div style="font-size:1.6rem;font-weight:900;color:{BRAND};">❄️ Snowflake</div>'
    f'<div style="font-size:.8rem;color:{M};">Architecture · Virtual Warehouses · Time Travel · Cloning · Performance · vs Databricks · Certification</div>',
    unsafe_allow_html=True)
st.markdown(f"<hr style='border-color:{BD};margin:6px 0 10px'>", unsafe_allow_html=True)

TAB = st.tabs([
    "🏗️ Architecture",
    "⚡ Virtual Warehouses",
    "⏮️ Time Travel",
    "📋 SQL Patterns",
    "🔐 Security",
    "❄️ vs Databricks",
    "💰 Pricing",
    "🎓 Cert Prep",
])

# ── TAB 0: ARCHITECTURE ──────────────────────────────────────────────────────
with TAB[0]:
    st.markdown(_h2("Snowflake Architecture","🏗️"), unsafe_allow_html=True)
    st.markdown(_card(
        "Snowflake is a cloud-native DWH built on a <b>multi-cluster shared data architecture</b>. "
        "Unlike traditional databases, storage and compute are <b>completely separated</b>. "
        "You pay for storage (S3/ADLS/GCS) and compute (virtual warehouses) independently.",
        l=TEAL), unsafe_allow_html=True)

    layers = [
        ("Cloud Services Layer","The brain. Query compilation, optimisation, metadata management, authentication, security. Always running, no cost to you.",BRAND),
        ("Query Processing Layer","Virtual warehouses — independent compute clusters. Each VW has its own CPU/RAM. Multiple VWs can query the SAME data simultaneously without contention.",TEAL),
        ("Database Storage Layer","Columnar compressed storage on cloud object store (S3/ADLS/GCS). Micro-partitions (~50-500MB). Automatic clustering.",AMBER),
    ]
    for t,d,c in layers:
        st.markdown(_card(f'<b style="color:{c};font-size:.88rem;">{t}</b><br>'
                          f'<span style="font-size:.76rem;color:{TEXT};">{d}</span>',l=c,p="10px 14px"), unsafe_allow_html=True)

    st.markdown(_h3("Key Architectural Concepts",STEEL), unsafe_allow_html=True)
    concepts = [
        ("Micro-Partitioning","All data automatically divided into micro-partitions (~16MB compressed, 50-500MB uncompressed). Immutable. Stored in columnar format. Automatic cluster pruning.",BRAND),
        ("Automatic Clustering","Snowflake tracks min/max values per column per micro-partition. Range queries skip irrelevant partitions automatically.",TEAL),
        ("Result Cache","Query results cached for 24hrs. Identical query = instant result, zero compute cost. Automatically invalidated when data changes.",AMBER),
        ("Metadata Cache","Column stats, min/max values stored in Cloud Services layer. Used for partition pruning before data is read.",STEEL),
        ("Multi-Cluster Warehouse","Auto-scale: add/remove clusters automatically based on queue depth. Handle variable concurrent workloads.",PUR),
        ("Columnar Storage","Each column stored separately. Only read columns you SELECT. Massive I/O reduction for analytical queries.",ORANGE),
    ]
    c1,c2 = st.columns(2)
    for i,(t,d,c) in enumerate(concepts):
        (c1 if i%2==0 else c2).markdown(_card(f'<b style="color:{c};font-size:.82rem;">{t}</b><br>'
                                              f'<span style="font-size:.74rem;color:{TEXT};">{d}</span>',l=c,p="9px 12px"), unsafe_allow_html=True)

# ── TAB 1: VIRTUAL WAREHOUSES ────────────────────────────────────────────────
with TAB[1]:
    st.markdown(_h2("Virtual Warehouses","⚡"), unsafe_allow_html=True)
    st.markdown(_card(
        "A Virtual Warehouse (VW) is an independent compute cluster. "
        "You can have multiple VWs querying the same data simultaneously with zero contention. "
        "Each VW has its own cache. Size determines query speed AND cost.",
        l=AMBER), unsafe_allow_html=True)

    sizes = [
        ("XS","1 server","~$0.15/credit","Dev/test, small queries, < 1M rows"),
        ("S","2 servers","~$0.30/credit","Light BI, simple aggregations"),
        ("M","4 servers","~$0.60/credit","Standard analytics, most workloads"),
        ("L","8 servers","~$1.20/credit","Complex joins, large aggregations"),
        ("XL","16 servers","~$2.40/credit","Heavy ETL, large table scans"),
        ("2XL","32 servers","~$4.80/credit","Very large datasets, complex ML prep"),
        ("4XL","128 servers","~$19.20/credit","Massive batch jobs"),
    ]
    size_df = pd.DataFrame(sizes, columns=["Size","Servers","Cost/Credit","Best For"])
    st.dataframe(size_df, use_container_width=True, height=260, hide_index=True)

    st.code("""-- Create virtual warehouses for different workloads
CREATE WAREHOUSE etl_wh
    WAREHOUSE_SIZE = 'LARGE'
    AUTO_SUSPEND = 60          -- suspend after 60s idle (save cost)
    AUTO_RESUME = TRUE          -- auto-start on query
    MIN_CLUSTER_COUNT = 1
    MAX_CLUSTER_COUNT = 3       -- scale to 3 clusters under load
    SCALING_POLICY = 'ECONOMY'; -- wait for queue before adding cluster

-- BI dashboard warehouse: small but always-on
CREATE WAREHOUSE bi_wh
    WAREHOUSE_SIZE = 'SMALL'
    AUTO_SUSPEND = 300          -- 5 min idle timeout
    AUTO_RESUME = TRUE;

-- Switch warehouses in session
USE WAREHOUSE etl_wh;
SELECT ...  -- runs on large ETL warehouse

USE WAREHOUSE bi_wh;
SELECT ...  -- runs on small BI warehouse""", language="sql")

    st.markdown(_h3("Cost Optimisation Tips",TEAL), unsafe_allow_html=True)
    tips = [
        "Set AUTO_SUSPEND to 60 seconds — warehouses idle = money wasted",
        "Use RESULT CACHE: identical queries return instantly for free",
        "Right-size: start with XS, scale up only if query > 30 seconds",
        "Separate ETL warehouse from BI warehouse — different SLAs",
        "Use Resource Monitors to cap credit spend by warehouse",
        "Schedule ETL on ECONOMY scaling policy — cheaper than STANDARD",
    ]
    for tip in tips:
        st.markdown(_card(f'<span style="font-size:.78rem;color:{TEXT};">✅ {tip}</span>',l=TEAL,p="7px 14px"), unsafe_allow_html=True)

# ── TAB 2: TIME TRAVEL ───────────────────────────────────────────────────────
with TAB[2]:
    st.markdown(_h2("Time Travel & Zero-Copy Clone","⏮️"), unsafe_allow_html=True)
    c1,c2 = st.columns(2)
    with c1:
        st.markdown(_card(f'<b style="color:{TEAL};">Time Travel</b><br>'
                          f'<span style="font-size:.76rem;color:{TEXT};">Access data from any point in the past (up to 90 days on Enterprise).<br>'
                          f'• Recover accidentally deleted data<br>'
                          f'• Compare data before and after a batch<br>'
                          f'• Audit historical values<br>'
                          f'• Free — uses micro-partition versioning</span>',l=TEAL,p="10px 14px"), unsafe_allow_html=True)
    with c2:
        st.markdown(_card(f'<b style="color:{AMBER};">Zero-Copy Clone</b><br>'
                          f'<span style="font-size:.76rem;color:{TEXT};">Instant copy of table/schema/database with NO data duplication.<br>'
                          f'• Copy only stores changed data (copy-on-write)<br>'
                          f'• Create dev/test environments instantly<br>'
                          f'• Clone before dangerous migrations<br>'
                          f'• Cost: almost zero until you modify the clone</span>',l=AMBER,p="10px 14px"), unsafe_allow_html=True)

    st.code("""-- TIME TRAVEL: query data at a specific point
-- By offset (seconds ago)
SELECT * FROM trips AT (OFFSET => -3600);  -- 1 hour ago

-- By timestamp
SELECT * FROM trips AT (TIMESTAMP => '2026-09-25 14:00:00'::TIMESTAMP);

-- By query ID (before a specific change)
SELECT * FROM trips BEFORE (STATEMENT => '01b3c4d5-...');

-- Restore accidentally deleted data
CREATE TABLE trips_restored AS
SELECT * FROM trips AT (TIMESTAMP => '2026-09-25 10:00:00'::TIMESTAMP);

-- Compare yesterday vs today
SELECT today.fleet_id,
    today.revenue - yesterday.revenue AS change
FROM (SELECT fleet_id, SUM(trip_fare_pkr) AS revenue FROM trips GROUP BY 1) today
JOIN (SELECT fleet_id, SUM(trip_fare_pkr) AS revenue
      FROM trips AT (OFFSET => -86400) GROUP BY 1) yesterday
USING (fleet_id);

-- ZERO-COPY CLONE: instant dev environment
CREATE DATABASE dev_rentacar CLONE prod_rentacar;   -- whole DB!
CREATE SCHEMA dev.dwh CLONE prod.dwh;               -- whole schema
CREATE TABLE trips_backup CLONE trips;               -- single table
-- Clone is independent — changes to clone don't affect source""", language="sql")

# ── TAB 3: SQL PATTERNS ──────────────────────────────────────────────────────
with TAB[3]:
    st.markdown(_h2("Snowflake SQL Patterns","📋"), unsafe_allow_html=True)
    SNOW_SQL = {
        "QUALIFY (Snowflake native)": """-- QUALIFY: filter window function results inline (no subquery!)
SELECT vehicle_id, trip_id, pickup_datetime, trip_fare_pkr,
    ROW_NUMBER() OVER (PARTITION BY vehicle_id ORDER BY trip_fare_pkr DESC) AS rn
FROM trips
WHERE status = 'Completed'
QUALIFY rn = 1;  -- top trip per vehicle, no subquery needed!""",

        "FLATTEN (semi-structured)": """-- FLATTEN: explode arrays in VARIANT columns
-- If trip metadata stored as JSON:
SELECT t.trip_id,
    f.value:city::VARCHAR  AS waypoint_city,
    f.value:lat::FLOAT     AS lat,
    f.index                AS stop_number
FROM trips t,
LATERAL FLATTEN(input => t.route_json:waypoints) f;""",

        "MATCH_RECOGNIZE (pattern detection)": """-- MATCH_RECOGNIZE: find sequential patterns in data
-- Find customers who cancelled THEN completed a trip (recovered)
SELECT *
FROM trips
MATCH_RECOGNIZE (
    PARTITION BY customer_id
    ORDER BY booking_datetime
    MEASURES
        FIRST(trip_id) AS first_cancel_trip,
        LAST(trip_id)  AS recovery_trip
    ONE ROW PER MATCH
    PATTERN (cancelled+ completed+)
    DEFINE
        cancelled AS status = 'Cancelled',
        completed AS status = 'Completed'
);""",

        "Dynamic Data Masking": """-- Create masking policy for CNIC
CREATE MASKING POLICY cnic_mask AS (val STRING) RETURNS STRING ->
    CASE
        WHEN CURRENT_ROLE() IN ('ADMIN','COMPLIANCE') THEN val
        WHEN CURRENT_ROLE() = 'ANALYST' THEN CONCAT(SUBSTR(val,1,5),'-*******-*')
        ELSE '*****-*******-*'
    END;

-- Apply to column
ALTER TABLE customers
    MODIFY COLUMN cnic SET MASKING POLICY cnic_mask;

-- Analyst query: SELECT cnic FROM customers → sees '*****-*******-*'
-- Admin query:   SELECT cnic FROM customers → sees '35202-1234567-8'""",

        "MERGE for SCD Type 2": """-- Snowflake MERGE: upsert pattern for SCD2
MERGE INTO dim_customer AS target
USING staging.stg_customers AS source
ON target.customer_id = source.customer_id AND target.is_current = TRUE
WHEN MATCHED AND (target.city != source.city OR target.customer_type != source.customer_type) THEN
    -- Expire the old record
    UPDATE SET valid_to = CURRENT_DATE - 1, is_current = FALSE
WHEN NOT MATCHED THEN
    -- Insert new record (handles both new customers and new versions)
    INSERT (customer_id, city, customer_type, valid_from, valid_to, is_current)
    VALUES (source.customer_id, source.city, source.customer_type,
            CURRENT_DATE, '9999-12-31', TRUE);""",

        "Clustering Key": """-- Define clustering key for frequently filtered column
CREATE TABLE fact_trips (
    trip_id        VARCHAR,
    pickup_date    DATE,
    fleet_id       VARCHAR,
    trip_fare_pkr  FLOAT
)
CLUSTER BY (pickup_date, fleet_id);
-- Snowflake uses this to sort micro-partitions → faster range queries

-- Check clustering depth
SELECT SYSTEM$CLUSTERING_DEPTH('fact_trips', '(pickup_date, fleet_id)');

-- Re-cluster manually if needed
ALTER TABLE fact_trips RECLUSTER;""",
    }
    _sel = st.selectbox("SQL Pattern:", list(SNOW_SQL.keys()), key="snow_sql_sel")
    st.code(SNOW_SQL[_sel], language="sql")

# ── TAB 4: SECURITY ──────────────────────────────────────────────────────────
with TAB[4]:
    st.markdown(_h2("Snowflake Security Features","🔐"), unsafe_allow_html=True)
    security_features = [
        ("Role-Based Access (RBAC)","Hierarchical roles. Users → Roles → Privileges on Objects. Principle of least privilege enforced.",BRAND),
        ("Dynamic Data Masking","Column-level masking policies. Different users see different data from the same query.",TEAL),
        ("Row Access Policies","Row-level security. Filter rows based on current user/role. Transparent to queries.",AMBER),
        ("Network Policies","IP allowlisting. Restrict access to corporate network or specific IP ranges.",STEEL),
        ("End-to-End Encryption","Data encrypted at rest (AES-256) and in transit (TLS 1.2+). Customer-managed keys (Tri-Secret Secure).",PUR),
        ("Private Link","VPC endpoint — traffic never leaves cloud provider network. No public internet.",ORANGE),
        ("Column-Level Security","Restrict SELECT on specific columns per role without masking.",BRAND),
        ("Object Tagging","Tag sensitive columns (PII, GDPR) and audit tag propagation through query results.",TEAL),
    ]
    c1,c2 = st.columns(2)
    for i,(t,d,c) in enumerate(security_features):
        (c1 if i%2==0 else c2).markdown(_card(f'<b style="color:{c};font-size:.82rem;">{t}</b><br>'
                                              f'<span style="font-size:.74rem;color:{TEXT};">{d}</span>',l=c,p="9px 12px"), unsafe_allow_html=True)

    st.code("""-- RBAC: create roles and grant privileges
CREATE ROLE analyst_role;
CREATE ROLE etl_role;

-- Grant object-level privileges
GRANT USAGE ON DATABASE rentacar TO ROLE analyst_role;
GRANT USAGE ON SCHEMA rentacar.dwh TO ROLE analyst_role;
GRANT SELECT ON ALL TABLES IN SCHEMA rentacar.dwh TO ROLE analyst_role;

GRANT INSERT, UPDATE ON TABLE rentacar.staging.stg_trips TO ROLE etl_role;

-- Row Access Policy: analysts see only their fleet
CREATE ROW ACCESS POLICY fleet_filter AS (fleet_id VARCHAR) RETURNS BOOLEAN ->
    CURRENT_ROLE() = 'ADMIN' OR
    fleet_id = (SELECT fleet_id FROM user_fleet_map WHERE username = CURRENT_USER());

ALTER TABLE trips ADD ROW ACCESS POLICY fleet_filter ON (fleet_id);""", language="sql")

# ── TAB 5: VS DATABRICKS ─────────────────────────────────────────────────────
with TAB[5]:
    st.markdown(_h2("Snowflake vs Databricks","❄️"), unsafe_allow_html=True)
    compare_df = pd.DataFrame([
        ("Primary Use Case","SQL analytics, BI, DWH","Data engineering, ML, streaming"),
        ("Language","SQL-first","Python/Scala/SQL"),
        ("Compute Engine","Proprietary (Photon optional)","Apache Spark"),
        ("Storage Format","Proprietary (Snowflake internal)","Delta Lake (open format)"),
        ("Streaming","Snowpipe (micro-batch ingest)","Spark Structured Streaming (native)"),
        ("ML/AI","Snowpark ML (newer)","MLflow (native, mature)"),
        ("Time Travel","Up to 90 days","Delta Lake (configurable)"),
        ("Cloning","Zero-copy clone (instant)","Delta clone (similar)"),
        ("Governance","Native RBAC + masking policies","Unity Catalog (newer)"),
        ("Pricing model","Per-credit compute + storage","DBUs + cloud VM cost"),
        ("Best for","BI teams, SQL-heavy workloads","DE teams, Python, ML pipelines"),
        ("Learning curve","Low (SQL knowledge sufficient)","Higher (need Spark knowledge)"),
        ("Concurrency","Excellent (multi-cluster VW)","Good (auto-scaling clusters)"),
        ("Maturity","Very mature (10+ years)","Mature (Databricks est. 2013)"),
    ], columns=["Factor","Snowflake ❄️","Databricks ⚡"])
    st.dataframe(compare_df, use_container_width=True, height=520, hide_index=True)

    st.markdown(_h3("When to choose which?",TEAL), unsafe_allow_html=True)
    c1,c2 = st.columns(2)
    with c1:
        st.markdown(_card(f'<b style="color:{TEAL};">Choose Snowflake when:</b><br>'
                          f'<span style="font-size:.76rem;color:{TEXT};">✅ Team is SQL-first (analysts, not engineers)<br>'
                          f'✅ Primary use case is BI and reporting<br>'
                          f'✅ Need easy data sharing across orgs<br>'
                          f'✅ Concurrency is key (many users simultaneously)<br>'
                          f'✅ Want fully managed, minimal ops overhead</span>',l=TEAL,p="10px 14px"), unsafe_allow_html=True)
    with c2:
        st.markdown(_card(f'<b style="color:{BRAND};">Choose Databricks when:</b><br>'
                          f'<span style="font-size:.76rem;color:{TEXT};">✅ Team builds complex ETL pipelines (Python/Spark)<br>'
                          f'✅ ML/AI workloads alongside data engineering<br>'
                          f'✅ Real-time streaming pipelines required<br>'
                          f'✅ Want open formats (no vendor lock-in)<br>'
                          f'✅ Large-scale data processing (PB scale)</span>',l=BRAND,p="10px 14px"), unsafe_allow_html=True)

    st.markdown(_card(f'<b style="color:{AMBER};">Many enterprises use BOTH</b><br>'
                      f'<span style="font-size:.76rem;color:{TEXT};">Databricks for ETL/ML → writes to Snowflake → analysts query via BI tools.<br>'
                      f'Modern stack: Kafka → Databricks (Delta Lake) → dbt → Snowflake → Tableau/Power BI</span>',
                      l=AMBER,p="9px 14px"), unsafe_allow_html=True)

# ── TAB 6: PRICING ───────────────────────────────────────────────────────────
with TAB[6]:
    st.markdown(_h2("Snowflake Pricing","💰"), unsafe_allow_html=True)
    st.markdown(_card("Snowflake charges for: <b>Compute</b> (credits/hr by warehouse size) + <b>Storage</b> (~$23/TB/month compressed). No charge for ingestion or loading.",l=STEEL), unsafe_allow_html=True)

    editions = [
        ("Standard","$2/credit","Time Travel: 1 day, Basic RBAC, No Dynamic Masking","Dev/test, small teams"),
        ("Enterprise","$3/credit","Time Travel: 90 days, Multi-cluster VW, Dynamic Masking, Column-level security","Most production deployments"),
        ("Business Critical","$4/credit","HIPAA/PCI compliance, Private Link, Tri-Secret Secure encryption","Healthcare, finance, regulated"),
        ("VPS","Custom","Single-tenant dedicated deployment","Government, extreme compliance"),
    ]
    ed_df = pd.DataFrame(editions, columns=["Edition","Base Price","Key Features","Best For"])
    st.dataframe(ed_df, use_container_width=True, height=180, hide_index=True)

    st.markdown(_h3("Cost Optimisation Checklist",TEAL), unsafe_allow_html=True)
    cost_tips = [
        ("AUTO_SUSPEND","Set to 60 seconds for most warehouses. Never set to 0 (never suspends).","🔌"),
        ("Right-sizing","Start XS. Scale up only if p99 query > 30s. Most BI queries fit on XS-S.","📏"),
        ("Result Cache","Identical queries are free. Design dashboards to use same parameterised queries.","⚡"),
        ("Resource Monitors","Set credit limits per warehouse + alert when 80% consumed.","💰"),
        ("Clustering","Add cluster keys only when query improvement exceeds re-clustering cost.","🔑"),
        ("Storage classes","Use Fail-safe only what you need. Consider shorter retention for dev tables.","💾"),
        ("Query Optimization","Check QUERY_HISTORY for expensive queries. Use EXPLAIN to find full scans.","🔍"),
        ("Idle Warehouses","Review WAREHOUSE_METERING_HISTORY weekly. Kill unused warehouses.","🗑️"),
    ]
    c1,c2 = st.columns(2)
    for i,(tip,desc,ic) in enumerate(cost_tips):
        (c1 if i%2==0 else c2).markdown(_card(f'{ic} <b style="color:{TEAL};font-size:.82rem;">{tip}</b><br>'
                                              f'<span style="font-size:.73rem;color:{TEXT};">{desc}</span>',l=TEAL,p="8px 12px"), unsafe_allow_html=True)

# ── TAB 7: CERT PREP ─────────────────────────────────────────────────────────
with TAB[7]:
    st.markdown(_h2("SnowPro Core Certification Prep","🎓"), unsafe_allow_html=True)
    st.markdown(_card("SnowPro Core = 100 questions, 115 minutes, $175, passing score ~65%. Tests Snowflake architecture, SQL, security, performance, and administration.",l=AMBER), unsafe_allow_html=True)

    CERT_TOPICS = [
        ("20-25%","Snowflake Overview & Architecture","Separation of storage/compute, micro-partitions, cloud services, result cache, metadata cache"),
        ("15-20%","Account Access & Security","RBAC, system-defined roles, MFA, network policies, SSO, key-pair auth"),
        ("15-20%","Performance Concepts","Virtual warehouses, caching layers, clustering keys, query profiling, resource monitors"),
        ("5-10%",  "Data Loading","COPY INTO, stages (internal/external), Snowpipe, file formats, load history"),
        ("10-15%","Data Transformations","DML, DDL, sequences, streams, tasks, procedures"),
        ("5-10%",  "Data Sharing","Direct sharing, Data Exchange, Reader Accounts"),
        ("5-10%",  "Account Management","Organizations, databases, schemas, warehouses, billing"),
        ("5-10%",  "Snowflake Ecosystem","Snowpark, dbt integration, BI tool connectors"),
    ]
    cert_df = pd.DataFrame(CERT_TOPICS, columns=["Exam Weight","Domain","Key Topics"])
    st.dataframe(cert_df, use_container_width=True, height=300, hide_index=True)

    st.markdown(_h3("Sample Exam Questions",BRAND), unsafe_allow_html=True)
    CERT_QS = [
        ("What are the three layers of Snowflake's architecture?",
         "Cloud Services, Query Processing (Virtual Warehouses), and Database Storage. Key point: storage and compute are completely separated."),
        ("What is a micro-partition?",
         "Snowflake's fundamental unit of data storage. 50-500MB uncompressed, 16MB compressed. Immutable. Stored in columnar format. Snowflake automatically maintains metadata (min/max per column) for partition pruning."),
        ("How long is Time Travel available by default on Standard edition?",
         "1 day (default). Enterprise edition: up to 90 days. Configured per table with DATA_RETENTION_TIME_IN_DAYS."),
        ("What is Fail-safe?",
         "7-day period AFTER Time Travel expires where Snowflake can recover data (internal use only). NOT accessible by customers. Adds to storage cost."),
        ("What is a zero-copy clone?",
         "Creates an instant copy of a table/schema/database without duplicating data. Uses copy-on-write — only stores changes. Initial cost is near zero."),
        ("What is the ACCOUNTADMIN role?",
         "Top-level system role. Full control over entire account. Best practice: only 2-3 users. Never use for daily work. Create custom roles for regular use."),
        ("What caching layers does Snowflake have?",
         "1. Result Cache (Cloud Services): exact query results, 24hrs. 2. Local Disk Cache (Virtual Warehouse): data from recently scanned micro-partitions. 3. Metadata Cache: stats for partition pruning."),
    ]
    for q,a in CERT_QS:
        with st.expander(f"**{q}**"):
            st.markdown(_card(a,l=TEAL,p="9px 14px"), unsafe_allow_html=True)

    st.markdown(_h3("Study Resources",STEEL), unsafe_allow_html=True)
    resources = [
        ("Official Docs","docs.snowflake.com","Most up-to-date. Read Architecture, Security, Performance sections."),
        ("SnowPro Study Guide","training.snowflake.com","Free official guide with exam blueprints."),
        ("Snowflake University","training.snowflake.com","Free self-paced courses. 'Snowflake Fundamentals' is essential."),
        ("Practice Exams","udemy.com","Multiple practice test courses. Aim for 80%+ before real exam."),
        ("Hands-on Trial","trial.snowflake.com","Free 30-day trial, $400 credits. Build the data platform concepts here."),
    ]
    for name,url,desc in resources:
        st.markdown(_card(f'<b style="color:{AMBER};">{name}</b> <span style="font-size:.68rem;color:{M};">— {url}</span><br>'
                          f'<span style="font-size:.74rem;color:{TEXT};">{desc}</span>',l=AMBER,p="8px 12px"), unsafe_allow_html=True)
