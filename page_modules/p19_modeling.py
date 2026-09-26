"""
p19_modeling.py — Data Modeling Deep Dive
3NF vs Star vs Data Vault · SCD Types 1-6
Fact patterns · Bridge tables · Junk dimensions
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
trips = dfs["trips"].copy(); customers = dfs["customers"].copy()

st.markdown(f'<div style="font-size:1.6rem;font-weight:900;color:{BRAND};">🏗️ Data Modeling</div>'
            f'<div style="font-size:.8rem;color:{M};">3NF · Star Schema · Data Vault 2.0 · SCD Types · Fact Patterns · Bridge Tables</div>',
            unsafe_allow_html=True)
st.markdown(f"<hr style='border-color:{BD};margin:6px 0 10px'>",unsafe_allow_html=True)

TAB = st.tabs(["📐 Schema Comparison","🔄 SCD Types 1-6","📊 Fact Patterns","🔗 Advanced Patterns","🏛️ Data Vault 2.0","🎯 Modeling Rules"])

# ── TAB 0: SCHEMA COMPARISON ─────────────────────────────────────────────────
with TAB[0]:
    st.markdown(_h2("3NF vs Star Schema vs Data Vault","📐"), unsafe_allow_html=True)
    c1,c2,c3 = st.columns(3)
    schemas = [
        (c1,"3NF (OLTP)","Eliminates ALL redundancy. Every non-key attribute depends only on the whole key (2NF) and nothing but the key (3NF). Optimised for writes.",["No duplicate data","Easy to update","Many JOINs for reads","Poor query performance for analytics"],BRAND,"Use for: Operational systems, apps"),
        (c2,"Star Schema (OLAP)","Denormalised. One central fact table surrounded by dimension tables. Optimised for reads/analytics. Redundancy is intentional.",["Fast analytical queries","Few JOINs needed","Redundant data","Hard to update"],TEAL,"Use for: DWH, BI reports"),
        (c3,"Data Vault 2.0","Hub-Link-Satellite pattern. Auditable, flexible, load-in-any-order. Best for enterprise DWH with many sources.",["Fully auditable","Handles schema changes","Complex to query","Needs business vault layer"],AMBER,"Use for: Enterprise DWH, regulated industries"),
    ]
    for col,name,desc,pros,clr,when in schemas:
        col.markdown(_card(f'<b style="font-size:.9rem;color:{clr};">{name}</b><br>'
                           f'<span style="font-size:.74rem;color:{TEXT};">{desc}</span><br><br>'
                           +''.join(f'<span style="font-size:.72rem;color:{TEXT};">{"✅" if i<2 else "⚠️"} {p}<br></span>' for i,p in enumerate(pros))
                           +f'<br><span style="font-size:.7rem;color:{M};">{when}</span>',l=clr,p="12px 14px"), unsafe_allow_html=True)

    st.markdown(_h3("📝 3NF → Star Schema Transformation Example",STEEL), unsafe_allow_html=True)
    c1,c2 = st.columns(2)
    with c1:
        st.markdown("**3NF (normalised)**")
        st.code("""-- Three separate tables, fully normalised
CREATE TABLE customers (customer_id PK, name, city, type);
CREATE TABLE vehicles  (vehicle_id  PK, make, model, fleet_id FK);
CREATE TABLE fleets    (fleet_id    PK, fleet_name, city);
CREATE TABLE trips (
    trip_id PK,
    customer_id FK → customers,
    vehicle_id  FK → vehicles,
    pickup_dt, dropoff_dt, fare
);
-- Query needs 3 JOINs for basic analysis""", language="sql")

    with c2:
        st.markdown("**Star Schema (denormalised)**")
        st.code("""-- Denormalised dimensions — all context in one place
CREATE TABLE dim_customer (
    customer_sk PK,  -- surrogate key
    customer_id,     -- natural key
    full_name, city, customer_type,
    valid_from, valid_to, is_current  -- SCD2
);
CREATE TABLE dim_vehicle (
    vehicle_sk PK, vehicle_id,
    make, model,
    fleet_name,    -- ← denormalised from fleets!
    fleet_city,    -- ← denormalised!
    category
);
CREATE TABLE fact_trips (
    trip_sk PK,
    pickup_date_key FK → dim_date,
    customer_sk FK → dim_customer,
    vehicle_sk  FK → dim_vehicle,
    fare_pkr, distance_km  -- measures
);""", language="sql")

# ── TAB 1: SCD TYPES ─────────────────────────────────────────────────────────
with TAB[1]:
    st.markdown(_h2("Slowly Changing Dimensions (SCD) Types 1-6","🔄"), unsafe_allow_html=True)
    st.markdown(_card("A dimension 'slowly changes' when its attributes change over time — e.g. a customer moves city, changes customer type, or a vehicle changes fleet. SCDs define how to handle these changes.",l=TEAL), unsafe_allow_html=True)

    SCD_TYPES = [
        ("Type 1 — Overwrite","Simply update the row. No history kept. Old value is lost forever.","city: Lahore → Islamabad  (Lahore gone forever)","❌ No history","Fast, simple. Use when history doesn't matter.",BRAND,"UPDATE dim_customer SET city='Islamabad' WHERE customer_id='CU001';"),
        ("Type 2 — Add New Row","Insert a new row with new value. Mark old row as expired. MOST COMMON for analytics.",  "Row 1: Lahore | valid_to=today | is_current=F\nRow 2: Islamabad | valid_from=today | is_current=T","✅ Full history","Complex queries, table grows. Use when history matters for point-in-time analysis.",TEAL,
         "UPDATE dim_customer SET valid_to=current_date-1, is_current=false WHERE customer_id='CU001' AND is_current=true;\nINSERT INTO dim_customer (customer_id,city,valid_from,valid_to,is_current) VALUES ('CU001','Islamabad',current_date,'9999-12-31',true);"),
        ("Type 3 — Add Column","Add a 'previous value' column. Only 1 level of history.",  "city_current: Islamabad\ncity_previous: Lahore","⚠️ One change","Simple but limited. Use for 'current vs previous' reporting.",AMBER,"ALTER TABLE dim_customer ADD COLUMN city_previous VARCHAR;\nUPDATE dim_customer SET city_previous=city, city='Islamabad' WHERE customer_id='CU001';"),
        ("Type 4 — History Table","Keep current in main table; all history in separate audit table.",  "dim_customer: current only\ndim_customer_hist: all versions","✅ Full history","Good separation. Use when history is rarely queried.",ORANGE,"INSERT INTO dim_customer_history SELECT *, current_timestamp FROM dim_customer WHERE customer_id='CU001';\nUPDATE dim_customer SET city='Islamabad' WHERE customer_id='CU001';"),
        ("Type 6 — Hybrid (1+2+3)","Combines Types 1,2,3: new row (Type 2) + update all rows with current value (Type 1) + add previous column (Type 3).",  "Full flexibility: history rows + quick current lookup","✅ Full history","Most powerful but most complex.",PUR,"-- Same as Type 2 insert, but also update current_city on ALL rows for this customer:\nUPDATE dim_customer SET current_city='Islamabad' WHERE customer_id='CU001';"),
    ]

    for scd_name,desc,example,hist,when,clr,sql_ex in SCD_TYPES:
        with st.expander(f"**{scd_name}** — {hist}", expanded=False):
            ec1,ec2 = st.columns(2)
            with ec1:
                st.markdown(_card(f'<b style="color:{clr};">{scd_name}</b><br>'
                                  f'<span style="font-size:.76rem;color:{TEXT};">{desc}</span><br><br>'
                                  f'<b style="font-size:.72rem;color:{M};">Example:</b><br>'
                                  f'<code style="font-size:.7rem;color:{AMBER};">{example}</code><br><br>'
                                  f'<span style="font-size:.72rem;color:{M};">When to use: {when}</span>',l=clr,p="10px 14px"), unsafe_allow_html=True)
            with ec2:
                st.code(sql_ex, language="sql")

    # SCD2 live demo
    st.markdown(_h3("🔬 SCD Type 2 Live Demo",TEAL), unsafe_allow_html=True)
    _cid = st.selectbox("Customer:", customers["customer_id"].head(10).tolist(), key="scd_cust")
    _cust = customers[customers["customer_id"]==_cid].iloc[0]
    _new_city = st.selectbox("Customer moves to:", ["Islamabad","Lahore","Karachi","Peshawar","Multan"], key="scd_city")
    if st.button("Apply SCD Type 2 Change", key="scd_apply"):
        scd2_before = pd.DataFrame([{"customer_sk":1,"customer_id":_cid,"city":_cust.get("city","Lahore"),"valid_from":"2022-01-01","valid_to":"9999-12-31","is_current":True}])
        st.markdown("**Before:**"); st.dataframe(scd2_before, use_container_width=True, hide_index=True)
        scd2_after = pd.DataFrame([
            {"customer_sk":1,"customer_id":_cid,"city":_cust.get("city","Lahore"),"valid_from":"2022-01-01","valid_to":"2026-09-26","is_current":False},
            {"customer_sk":2,"customer_id":_cid,"city":_new_city,"valid_from":"2026-09-27","valid_to":"9999-12-31","is_current":True},
        ])
        st.markdown("**After SCD2 update:**"); st.dataframe(scd2_after, use_container_width=True, hide_index=True)
        st.success(f"Customer {_cid} city change tracked. Old version expired, new version active.")

# ── TAB 2: FACT PATTERNS ──────────────────────────────────────────────────────
with TAB[2]:
    st.markdown(_h2("Fact Table Patterns","📊"), unsafe_allow_html=True)
    fact_patterns = [
        ("Transaction Fact","One row per business event (1 row = 1 trip). Most common. Additive measures.",
         "fact_trips: 1 row = 1 trip\nfact_payments: 1 row = 1 payment",
         "trip_fare_pkr, distance_km","Fully additive — SUM across any dimension",BRAND),
        ("Periodic Snapshot Fact","One row per entity per time period. Captures state at regular intervals.",
         "fact_monthly_vehicle: 1 row = 1 vehicle × month\nShows: trips_this_month, revenue, utilisation%",
         "utilisation_pct, revenue_pkr","Semi-additive — SUM across time is wrong!",TEAL),
        ("Accumulating Snapshot Fact","One row per process instance. Updated as the process moves through stages.",
         "fact_booking_pipeline:\n1 row = 1 booking through all stages\nBooking → Confirmed → Dispatched → In Progress → Completed",
         "duration_booking_to_dispatch, duration_total","Non-additive — AVG is meaningful, SUM is not",AMBER),
    ]
    for pname,desc,example,measures,additivity,clr in fact_patterns:
        with st.expander(f"**{pname}**"):
            c1,c2 = st.columns(2)
            with c1: st.markdown(_card(f'<b style="color:{clr};">{pname}</b><br><span style="font-size:.76rem;color:{TEXT};">{desc}</span><br><br><b style="font-size:.72rem;color:{M};">Example:</b> <code style="font-size:.7rem;color:{AMBER};">{example}</code>',l=clr,p="10px 14px"), unsafe_allow_html=True)
            with c2: st.markdown(_card(f'<b style="font-size:.76rem;color:{TEXT};">Measures:</b> {measures}<br><b style="font-size:.76rem;color:{TEXT};">Additivity:</b> {additivity}',l=STEEL,p="10px 14px"), unsafe_allow_html=True)

    st.markdown(_h3("📝 Accumulating Snapshot Example",AMBER), unsafe_allow_html=True)
    snap_df = pd.DataFrame([
        {"booking_id":"BK001","booked_at":"2024-01-01 09:00","confirmed_at":"2024-01-01 09:15","dispatched_at":"2024-01-01 11:00","completed_at":"2024-01-01 14:30","booking_to_confirm_min":15,"confirm_to_dispatch_min":105,"total_duration_hrs":5.5,"status":"Completed"},
        {"booking_id":"BK002","booked_at":"2024-01-02 14:00","confirmed_at":"2024-01-02 14:05","dispatched_at":"2024-01-02 15:30","completed_at":None,"booking_to_confirm_min":5,"confirm_to_dispatch_min":85,"total_duration_hrs":None,"status":"In Progress"},
    ])
    st.dataframe(snap_df, use_container_width=True, height=120, hide_index=True)

# ── TAB 3: ADVANCED PATTERNS ─────────────────────────────────────────────────
with TAB[3]:
    st.markdown(_h2("Advanced Modeling Patterns","🔗"), unsafe_allow_html=True)
    advanced = [
        ("Bridge Table","Handles many-to-many relationships. A customer can have multiple loyalty tiers; a vehicle can serve multiple fleets over time.",
         """-- Customer ↔ LoyaltyTier is M:N
CREATE TABLE bridge_customer_tier (
    customer_sk     INT FK → dim_customer,
    tier_sk         INT FK → dim_tier,
    weight_factor   FLOAT,  -- for weighted aggregation
    valid_from DATE, valid_to DATE
);""",TEAL),
        ("Junk Dimension","Combine multiple low-cardinality flag columns into one dimension to avoid flag columns in the fact table.",
         """-- Instead of 4 flag columns in fact_trips:
-- with_driver, self_drive, is_intercity, is_weekend
-- Create ONE junk dimension:
CREATE TABLE dim_trip_flags (
    flag_sk  INT PK,
    with_driver   BOOLEAN,
    self_drive    BOOLEAN,
    is_intercity  BOOLEAN,
    is_weekend    BOOLEAN
);  -- Only 16 rows (2^4 combinations)!
-- fact_trips has ONE FK: flag_sk""",AMBER),
        ("Role-Playing Dimension","Same dimension used in different roles. dim_date used as pickup_date_key AND dropoff_date_key.",
         """-- dim_date is used in TWO roles in fact_trips:
SELECT
    t.trip_id,
    pickup_d.month_name   AS pickup_month,   -- role 1
    dropoff_d.month_name  AS dropoff_month   -- role 2
FROM fact_trips t
JOIN dim_date pickup_d  ON t.pickup_date_key  = pickup_d.date_key
JOIN dim_date dropoff_d ON t.dropoff_date_key = dropoff_d.date_key;""",BRAND),
        ("Degenerate Dimension","A dimension key stored directly in the fact table with no dimension table. e.g. booking_id in fact_trips.",
         """-- booking_id is a dimension (it's a natural key from source)
-- but it has no attributes — no need for dim_booking table
-- It lives directly in fact_trips as a degenerate dimension:
SELECT trip_id,
    booking_id,        -- ← degenerate dimension
    trip_fare_pkr
FROM fact_trips;
-- Used for: drill-back to OLTP source system""",STEEL),
    ]
    for pname,desc,sql_ex,clr in advanced:
        with st.expander(f"**{pname}**"):
            c1,c2 = st.columns([1,2])
            with c1: st.markdown(_card(f'<b style="color:{clr};">{pname}</b><br><span style="font-size:.76rem;color:{TEXT};">{desc}</span>',l=clr,p="10px 14px"), unsafe_allow_html=True)
            with c2: st.code(sql_ex.strip(), language="sql")

# ── TAB 4: DATA VAULT ────────────────────────────────────────────────────────
with TAB[4]:
    st.markdown(_h2("Data Vault 2.0","🏛️"), unsafe_allow_html=True)
    st.markdown(_card("Data Vault 2.0 is a modelling methodology for enterprise DWH. It separates business keys (Hubs), relationships (Links), and descriptive attributes (Satellites). Enables: parallel loading, full auditability, schema flexibility.",l=PUR), unsafe_allow_html=True)
    c1,c2,c3 = st.columns(3)
    with c1: st.markdown(_card(f'<b style="color:{TEAL};">🔵 HUB</b><br><span style="font-size:.74rem;color:{TEXT};">Business keys only. One row per unique business entity.<br><br>hub_customer(customer_hk PK, customer_id BK, load_date, record_source)<br><br>hub_vehicle(vehicle_hk PK, vehicle_id BK, load_date, record_source)</span>',l=TEAL,p="10px 14px"), unsafe_allow_html=True)
    with c2: st.markdown(_card(f'<b style="color:{AMBER};">🔴 LINK</b><br><span style="font-size:.74rem;color:{TEXT};">Relationships between hubs. Many-to-many supported natively.<br><br>link_trip(trip_hk PK, customer_hk FK, vehicle_hk FK, driver_hk FK, load_date)<br><br>Always insert-only — never update!</span>',l=AMBER,p="10px 14px"), unsafe_allow_html=True)
    with c3: st.markdown(_card(f'<b style="color:{BRAND};">🟢 SATELLITE</b><br><span style="font-size:.74nm;color:{TEXT};">Descriptive attributes. One row per change — full history automatically.<br><br>sat_customer_detail(customer_hk FK, load_date, load_end_date, full_name, city, email, hash_diff)</span>',l=BRAND,p="10px 14px"), unsafe_allow_html=True)

    st.code("""-- DATA VAULT: Loading a customer record
-- Step 1: Insert into Hub (business key)
INSERT INTO hub_customer (customer_hk, customer_id, load_date, record_source)
SELECT MD5(customer_id), customer_id, current_timestamp, 'oltp_customers'
FROM staging.stg_customers
WHERE customer_id NOT IN (SELECT customer_id FROM hub_customer);

-- Step 2: Insert into Satellite (attributes — only if changed)
INSERT INTO sat_customer_detail
  (customer_hk, load_date, full_name, city, email, hash_diff)
SELECT
    MD5(s.customer_id),
    current_timestamp,
    s.full_name, s.city, s.email,
    MD5(s.full_name || s.city || s.email)  -- hash of attributes for change detection
FROM staging.stg_customers s
JOIN hub_customer h ON h.customer_id = s.customer_id
WHERE MD5(s.full_name || s.city || s.email)
    != (SELECT hash_diff FROM sat_customer_detail WHERE customer_hk = h.customer_hk AND load_end_date IS NULL);""", language="sql")

    st.markdown(_h3("3NF vs Star vs Vault — Decision Guide",STEEL), unsafe_allow_html=True)
    dec_df = pd.DataFrame([
        {"Factor":"Source system data model","3NF OLTP":"Design around this","Star Schema DWH":"Denormalise for analytics","Data Vault":"Load as-is, model later"},
        {"Factor":"Schema changes over time","3NF OLTP":"Disruptive","Star Schema DWH":"Requires ETL rework","Data Vault":"Add satellites, no breakage"},
        {"Factor":"Auditability requirement","3NF OLTP":"None","Star Schema DWH":"SCD2 for history","Data Vault":"Full load_date on every record"},
        {"Factor":"Query complexity","3NF OLTP":"High (many JOINs)","Star Schema DWH":"Low (simple star join)","Data Vault":"High (needs business vault layer)"},
        {"Factor":"Number of source systems","3NF OLTP":"1","Star Schema DWH":"1-5","Data Vault":"5+ (enterprise)"},
        {"Factor":"Team expertise needed","3NF OLTP":"Standard DBA","Star Schema DWH":"DWH/BI developer","Data Vault":"Specialist + tooling"},
    ])
    st.dataframe(dec_df, use_container_width=True, height=250, hide_index=True)

# ── TAB 5: MODELING RULES ────────────────────────────────────────────────────
with TAB[5]:
    st.markdown(_h2("The Golden Rules of Data Modeling","🎯"), unsafe_allow_html=True)
    rules = [
        ("1","Define grain FIRST","Before writing any SQL, write one sentence: 'One row = ____'. Get sign-off. Everything follows from grain.",BRAND),
        ("2","Facts are numeric, additive","Fact columns should be numbers you can SUM. Non-additive values belong in dimensions.",TEAL),
        ("3","Never put measures in dimensions","Dimensions describe. Facts measure. Customer's 'total bookings' is a measure — put it in a fact or mart, not dim_customer.",AMBER),
        ("4","Use surrogate keys in dimensions","Never use source system natural keys as dimension PKs. They can change. Integer surrogate keys are stable.",STEEL),
        ("5","Every dimension needs a row for Unknown","Add row with SK=-1 and values 'Unknown'. Fact table FKs can always reference it without NULL.",PUR),
        ("6","Date dimension is always needed","Never store dates as raw values in fact tables. Always use a date dimension with pre-computed attributes.",TEAL),
        ("7","Choose SCD type deliberately","Type 1 = overwrite. Type 2 = history. Type 6 = both. Wrong choice = data loss or unusable DWH.",BRAND),
        ("8","Test grain consistency","After loading, GROUP BY all dimension FKs in the fact table — each combination should appear at most once per grain.",AMBER),
        ("9","Document everything","Every table, column, and metric needs a business definition. 'trip_fare_pkr' = base rental charge, excludes driver allowance.",ORANGE),
        ("10","Name things consistently","Table: fact_trips (fact prefix). Dimension: dim_customer. Column: customer_sk (surrogate), customer_id (natural). Date: date_key (YYYYMMDD).",STEEL),
    ]
    for num,name,desc,clr in rules:
        st.markdown(_card(f'<span style="font-size:1.1rem;font-weight:900;color:{clr};margin-right:8px;">#{num}</span>'
                          f'<b style="color:{clr};font-size:.86rem;">{name}</b><br>'
                          f'<span style="font-size:.76rem;color:{TEXT};">{desc}</span>',l=clr,p="10px 14px"), unsafe_allow_html=True)
