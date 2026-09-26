"""
p20_architecture.py — Data Architecture Patterns
Lambda · Kappa · Medallion · Lakehouse · Decision guide
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from page_modules._shared import inject, get_data, BRAND, STEEL, GREEN, AMBER, ORANGE, TEXT
inject()
M="#5a7a96"; CB="#141e2b"; BD="#1e2f44"; TEAL="#2A9D8F"; PUR="#6A4C93"
def _card(b,l=BRAND,p="14px 16px"): return f'<div style="background:{CB};border:1px solid {BD};border-left:3px solid {l};border-radius:10px;padding:{p};margin:6px 0;">{b}</div>'
def _h2(t,i=""): return f'<div style="font-size:1.22rem;font-weight:800;color:{TEXT};margin:16px 0 4px;"><span style="color:{BRAND};">{i} </span>{t}</div>'
def _h3(t,c=STEEL): return f'<div style="font-size:.9rem;font-weight:700;color:{c};border-left:3px solid {c};padding-left:8px;margin:10px 0 6px;">{t}</div>'
def _flow(steps, colors): return "".join(f'<div style="display:inline-flex;align-items:center;gap:4px;margin:3px;"><div style="background:{c}33;color:{c};border:1px solid {c}88;border-radius:6px;padding:6px 12px;font-size:.74rem;font-weight:700;">{s}</div>{"<span style=color:"+M+";>→</span>" if i<len(steps)-1 else ""}</div>' for i,(s,c) in enumerate(zip(steps,colors)))

st.markdown(f'<div style="font-size:1.6rem;font-weight:900;color:{BRAND};">🏛️ Data Architecture</div>'
            f'<div style="font-size:.8rem;color:{M};">Lambda · Kappa · Medallion · Lakehouse · This Platform Architecture</div>',
            unsafe_allow_html=True)
st.markdown(f"<hr style='border-color:{BD};margin:6px 0 10px'>",unsafe_allow_html=True)

TAB = st.tabs(["🏗️ Architectures","⚡ Lambda","🌊 Kappa","🥇 Medallion","🏠 Lakehouse","🔍 This Platform","📐 Decision Guide"])

with TAB[0]:
    st.markdown(_h2("Data Architecture Overview","🏗️"), unsafe_allow_html=True)
    archs = [
        ("Lambda","Batch layer + Speed layer + Serving layer. Two separate codebases for batch and real-time.","✅ Battle-tested\n✅ Handles late data\n⚠️ Two codebases to maintain\n⚠️ Consistency challenges","Ride-hailing apps, financial fraud detection",BRAND),
        ("Kappa","Streaming only — treat batch as slow streaming. Simpler, single codebase.","✅ Single codebase\n✅ Simpler operations\n⚠️ Reprocessing is expensive\n⚠️ Not all data is streaming",  "IoT telemetry, clickstream analytics",TEAL),
        ("Medallion (Bronze/Silver/Gold)","Three-layer data quality refinement. Raw → Validated → Business-ready. Used by Databricks/Delta Lake.","✅ Clear quality progression\n✅ Easy to debug\n✅ Re-processable\n⚠️ Storage cost (3 copies)","Enterprise data lakes, Databricks environments",AMBER),
        ("Lakehouse","Combines data lake (cheap storage) with data warehouse (ACID, SQL). Best of both worlds.","✅ ACID on cheap storage\n✅ Supports BI + ML\n✅ One copy of data\n⚠️ Newer technology","Delta Lake, Apache Iceberg, AWS Lake Formation",ORANGE),
        ("Data Mesh","Decentralised. Each domain team owns their data as a product. Federation model.","✅ Scales with org size\n✅ Domain ownership\n⚠️ Governance complexity\n⚠️ Requires mature org","Large enterprises with multiple business domains",PUR),
    ]
    for aname,desc,pros,ex,clr in archs:
        with st.expander(f"**{aname}**"):
            c1,c2 = st.columns(2)
            with c1: st.markdown(_card(f'<b style="color:{clr};">{aname}</b><br><span style="font-size:.76rem;color:{TEXT};">{desc}</span>',l=clr,p="10px 14px"), unsafe_allow_html=True)
            with c2: st.markdown(_card(f'<b style="font-size:.74rem;color:{TEXT};">Pros/Cons:</b><br><code style="font-size:.7rem;">{pros}</code><br><br><b style="font-size:.74rem;color:{M};">Real-world: {ex}</b>',l=STEEL,p="10px 14px"), unsafe_allow_html=True)

with TAB[1]:
    st.markdown(_h2("Lambda Architecture","⚡"), unsafe_allow_html=True)
    st.markdown(_card("Lambda solves the challenge of processing massive data sets that require both batch accuracy AND real-time speed. It runs TWO parallel pipelines and merges results.",l=BRAND), unsafe_allow_html=True)
    st.markdown(_h3("Architecture Flow",STEEL), unsafe_allow_html=True)
    st.markdown('<div style="overflow-x:auto;">'+_flow(
        ["Source Data","Batch Layer\n(Spark/DWH)","Batch View\n(accurate, slow)","Serving Layer\n(merged result)","Query"],
        [M,BRAND,BRAND,TEAL,TEAL]
    )+'<br>'+_flow(
        ["Source Data","Speed Layer\n(Kafka/Flink)","Real-time View\n(fast, approximate)","Serving Layer\n(merged result)","Query"],
        [M,AMBER,AMBER,TEAL,TEAL]
    )+'</div>', unsafe_allow_html=True)
    st.markdown(_h3("Rent-A-Car Lambda Example",BRAND), unsafe_allow_html=True)
    c1,c2 = st.columns(2)
    with c1:
        st.markdown(_card(f'<b style="color:{BRAND};">Batch Layer (our current setup)</b><br><span style="font-size:.75rem;color:{TEXT};">• CSVs → ELT pipeline → DWH<br>• Runs hourly/daily<br>• Accurate revenue/analytics<br>• 1+ hour latency<br>• <b>This is what we built!</b></span>',l=BRAND,p="10px 14px"), unsafe_allow_html=True)
    with c2:
        st.markdown(_card(f'<b style="color:{AMBER};">Speed Layer (what we would add)</b><br><span style="font-size:.75rem;color:{TEXT};">• Streaming events from generator<br>• Process every 10 seconds<br>• Approximate KPIs (live booking count)<br>• &lt;1 minute latency<br>• <b>Our streaming tab simulates this</b></span>',l=AMBER,p="10px 14px"), unsafe_allow_html=True)

with TAB[2]:
    st.markdown(_h2("Kappa Architecture","🌊"), unsafe_allow_html=True)
    st.markdown(_card("Kappa simplifies Lambda by eliminating the batch layer. Everything is a stream — batch is just a stream that happens slowly. Single codebase, easier to maintain.",l=TEAL), unsafe_allow_html=True)
    st.markdown(_h3("Architecture Flow",STEEL), unsafe_allow_html=True)
    st.markdown('<div style="overflow-x:auto;">'+_flow(
        ["Events\n(Kafka)","Stream\nProcessor","Real-time\nView","Reprocess\nfrom start","Updated\nView"],
        [BRAND,TEAL,TEAL,AMBER,TEAL]
    )+'</div>', unsafe_allow_html=True)
    c1,c2 = st.columns(2)
    with c1: st.markdown(_card(f'<b style="color:{TEAL};">When Kappa beats Lambda</b><br><span style="font-size:.75rem;color:{TEXT};">✅ Data naturally arrives as streams<br>✅ Team can maintain one codebase<br>✅ Low latency is required (&lt;1min)<br>✅ Business logic is the same for batch and real-time</span>',l=TEAL,p="10px 14px"), unsafe_allow_html=True)
    with c2: st.markdown(_card(f'<b style="color:{AMBER};">When Lambda beats Kappa</b><br><span style="font-size:.75rem;color:{TEXT};">✅ Complex batch transforms hard to stream<br>✅ Reprocessing cost is very high<br>✅ Historical data arrives late frequently<br>✅ Team expertise in batch tools (Spark)</span>',l=AMBER,p="10px 14px"), unsafe_allow_html=True)

with TAB[3]:
    st.markdown(_h2("Medallion Architecture (Bronze/Silver/Gold)","🥇"), unsafe_allow_html=True)
    st.markdown(_card("The Medallion architecture organises data into three quality layers. Each layer adds more curation. Used natively by Databricks Delta Lake and AWS Lake Formation.",l=AMBER), unsafe_allow_html=True)
    c1,c2,c3 = st.columns(3)
    with c1: st.markdown(_card(f'<b style="color:{BRAND};">🥉 Bronze (Raw)</b><br><span style="font-size:.75rem;color:{TEXT};">Exact copy of source data. Nothing changed. Full history. Same as our raw.v_* views.<br><br><b>Rules:</b> Append-only. No deletes. No transforms. Schema on read.<br><br><code>SELECT * FROM raw.v_trips</code></span>',l=BRAND,p="10px 14px"), unsafe_allow_html=True)
    with c2: st.markdown(_card(f'<b style="color:{STEEL};">🥈 Silver (Validated)</b><br><span style="font-size:.75rem;color:{TEXT};">Cleaned, typed, deduplicated. DQ flags applied. Conformed schemas. Same as our staging.stg_* tables.<br><br><b>Rules:</b> Idempotent loads. DQ checks. Dedup. Type casting.<br><br><code>SELECT * FROM staging.stg_trips</code></span>',l=STEEL,p="10px 14px"), unsafe_allow_html=True)
    with c3: st.markdown(_card(f'<b style="color:{AMBER};">🥇 Gold (Business)</b><br><span style="font-size:.75rem;color:{TEXT};">Aggregated, modelled, business-ready. Star schema facts & dims. Marts. Same as our dwh.* + mart.*<br><br><b>Rules:</b> Documented, tested, SLA-guaranteed.<br><br><code>SELECT * FROM mart.daily_revenue</code></span>',l=AMBER,p="10px 14px"), unsafe_allow_html=True)
    st.markdown(_card(f'<b style="color:{TEAL};">This platform IS a Medallion architecture!</b><br><span style="font-size:.75rem;color:{TEXT};">raw.v_* = Bronze &nbsp;|&nbsp; staging.stg_* = Silver &nbsp;|&nbsp; dwh.fact_*/dim_* = Gold &nbsp;|&nbsp; mart.* = Platinum (serving layer)</span>',l=TEAL,p="8px 14px"), unsafe_allow_html=True)

with TAB[4]:
    st.markdown(_h2("Lakehouse Architecture","🏠"), unsafe_allow_html=True)
    st.markdown(_card("A Lakehouse combines cheap object storage (S3/ADLS) with ACID transactions, schema enforcement, and SQL query performance. Eliminates the need for a separate data lake AND data warehouse.",l=TEAL), unsafe_allow_html=True)
    LAKEHOUSES = [("Delta Lake","Databricks","ACID on S3, time travel, schema evolution","Open source, most popular"),("Apache Iceberg","Netflix origin","Table format for huge analytics tables","Multi-engine support"),("Apache Hudi","Uber origin","Upserts and incremental processing on data lake","Good for CDC patterns"),("DuckDB (our choice!)","MotherDuck","In-process analytical database, reads Parquet/CSV natively","Perfect for learning + small-medium scale")]
    for name,org,feat,note in LAKEHOUSES:
        st.markdown(_card(f'<b style="color:{AMBER};">{name}</b> <span style="font-size:.7rem;color:{M};">({org})</span><br><span style="font-size:.75rem;color:{TEXT};">{feat}</span><br><span style="font-size:.7rem;color:{M};">Note: {note}</span>',l=AMBER,p="9px 14px"), unsafe_allow_html=True)

with TAB[5]:
    st.markdown(_h2("This Platform's Architecture","🔍"), unsafe_allow_html=True)
    st.markdown(_card("This Rent-A-Car platform implements a <b>Medallion + ELT + Kimball Star Schema</b> architecture running entirely on DuckDB. Here is the exact design:",l=BRAND), unsafe_allow_html=True)
    st.markdown('<div style="overflow-x:auto;font-family:monospace;font-size:.76rem;background:#0d1117;border-radius:8px;padding:16px;line-height:2.1;">'+
        f'<span style="color:{BRAND};">📡 GENERATORS</span> (Batch + Streaming Python scripts)<br>'+
        '&nbsp;&nbsp;&nbsp;&nbsp;↓<br>'+
        f'<span style="color:{BRAND};">📂 data/csv/oltp/</span> (21 CSV files — Bronze layer)<br>'+
        '&nbsp;&nbsp;&nbsp;&nbsp;↓ read_csv_auto() zero-copy views<br>'+
        f'<span style="color:{AMBER};">🔍 raw.v_*</span> (DuckDB views — Bronze)<br>'+
        '&nbsp;&nbsp;&nbsp;&nbsp;↓ TRY_CAST · COALESCE · QUALIFY dedup · DQ flags<br>'+
        f'<span style="color:{STEEL};">🧹 staging.stg_*</span> (Cleaned tables — Silver)<br>'+
        '&nbsp;&nbsp;&nbsp;&nbsp;↓ Surrogate keys · SCD2 · Conformed dims<br>'+
        f'<span style="color:{TEAL};">🌟 dwh.dim_* + dwh.fact_*</span> (Kimball Star Schema — Gold)<br>'+
        '&nbsp;&nbsp;&nbsp;&nbsp;↓ Pre-aggregated views<br>'+
        f'<span style="color:{PUR};">📈 mart.*</span> (Analytical marts — Platinum)<br>'+
        '&nbsp;&nbsp;&nbsp;&nbsp;↓ Streamlit + DuckDB in-memory<br>'+
        f'<span style="color:{GREEN};">🖥️ Dashboard</span> (8 BI pages + Academy + Parking)<br>',
        unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with TAB[6]:
    st.markdown(_h2("Architecture Decision Guide","📐"), unsafe_allow_html=True)
    st.markdown(_h3("Answer these questions to choose your architecture",STEEL), unsafe_allow_html=True)
    questions = [
        ("Q1: Data volume?","< 1TB → DuckDB/PostgreSQL | 1-100TB → Redshift/Snowflake | > 100TB → Spark/Databricks"),
        ("Q2: Latency requirement?","< 1 second → Kafka + Redis | 1-60 seconds → Kafka + Flink | 1 min-1 hr → Micro-batch | > 1 hr → Batch ETL"),
        ("Q3: Number of data sources?","1-3 sources → Simple ETL pipeline | 3-10 → Orchestrated ELT | 10+ → Data Vault or Data Mesh"),
        ("Q4: Team size?","1-3 engineers → dbt + DuckDB/Snowflake | 4-10 → Airflow + Spark | 10+ → Databricks/Azure Synapse"),
        ("Q5: Historical tracking needed?","No → SCD Type 1 | Some attributes → SCD Type 2 | Full audit → Data Vault"),
        ("Q6: Real-time dashboards?","No → Batch daily → Star Schema | Yes → Lambda or Kappa | Approximate OK → Streaming to metrics store"),
        ("Q7: Regulatory requirements?","GDPR → Data Vault + full audit log | HIPAA → Encrypted Lakehouse | SOX → Immutable audit trail"),
        ("Q8: Budget?","Minimal → DuckDB + local files (like this platform) | Medium → Snowflake/BigQuery | Large → Azure/AWS full stack"),
    ]
    for q,a in questions:
        st.markdown(_card(f'<b style="color:{TEAL};font-size:.82rem;">{q}</b><br><span style="font-size:.76rem;color:{TEXT};">{a}</span>',l=TEAL,p="9px 14px"), unsafe_allow_html=True)
