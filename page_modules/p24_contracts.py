"""
p24_contracts.py — Data Contracts
Define, validate, and version data contracts.
Schema contracts · Column tests · Breaking changes · Versioning
"""
import json
import pandas as pd
import streamlit as st
from datetime import datetime
from pathlib import Path
from page_modules._shared import inject, get_data, BRAND, STEEL, GREEN, AMBER, ORANGE, TEXT
inject()
M="#5a7a96"; CB="#141e2b"; BD="#1e2f44"; TEAL="#2A9D8F"; PUR="#6A4C93"
def _card(b,l=BRAND,p="14px 16px"): return f'<div style="background:{CB};border:1px solid {BD};border-left:3px solid {l};border-radius:10px;padding:{p};margin:6px 0;">{b}</div>'
def _h2(t,i=""): return f'<div style="font-size:1.22rem;font-weight:800;color:{TEXT};margin:16px 0 4px;"><span style="color:{BRAND};">{i} </span>{t}</div>'
def _h3(t,c=STEEL): return f'<div style="font-size:.9rem;font-weight:700;color:{c};border-left:3px solid {c};padding-left:8px;margin:10px 0 6px;">{t}</div>'

dfs = get_data()
CONTRACT_DIR = Path("data/contracts")
CONTRACT_DIR.mkdir(parents=True, exist_ok=True)

st.markdown(f'<div style="font-size:1.6rem;font-weight:900;color:{BRAND};">📄 Data Contracts</div>'
            f'<div style="font-size:.8rem;color:{M};">Define · Validate · Version · Breaking changes · Producer/Consumer agreement</div>',
            unsafe_allow_html=True)
st.markdown(f"<hr style='border-color:{BD};margin:6px 0 10px'>",unsafe_allow_html=True)

TAB = st.tabs(["📋 Concepts","📝 Contract Definition","✅ Contract Validation","⚠️ Breaking Changes","📚 Examples"])

# ── TAB 0: CONCEPTS ──────────────────────────────────────────────────────────
with TAB[0]:
    st.markdown(_h2("What is a Data Contract?","📋"), unsafe_allow_html=True)
    st.markdown(_card("A <b>data contract</b> is a formal, versioned agreement between a data <b>producer</b> (who creates data) and a <b>consumer</b> (who uses it). It specifies: schema, quality expectations, SLAs, and semantics.",l=TEAL), unsafe_allow_html=True)
    c1,c2 = st.columns(2)
    with c1:
        st.markdown(_card(f'<b style="color:{BRAND};">Without Data Contracts</b><br>'
                          f'<span style="font-size:.76rem;color:{TEXT};">• Producer renames a column → consumer pipeline breaks<br>'
                          f'• No agreed definition of "active customer"<br>'
                          f'• NULL appears where consumer expected NOT NULL<br>'
                          f'• No warning before schema changes<br>'
                          f'• "Who broke my dashboard?" blame game</span>',l=BRAND,p="10px 14px"), unsafe_allow_html=True)
    with c2:
        st.markdown(_card(f'<b style="color:{TEAL};">With Data Contracts</b><br>'
                          f'<span style="font-size:.76rem;color:{TEXT};">• Schema changes require versioning + notification<br>'
                          f'• Business definitions agreed and documented<br>'
                          f'• Quality thresholds enforced at producer side<br>'
                          f'• Breaking changes detected before they break pipelines<br>'
                          f'• Autonomous teams, safe to evolve independently</span>',l=TEAL,p="10px 14px"), unsafe_allow_html=True)

    COMPONENTS = [
        ("Schema","Column names, data types, nullability. The foundation.",BRAND),
        ("Semantics","Business definitions — what does 'active customer' mean exactly?",TEAL),
        ("Quality","Nullability, uniqueness, referential integrity, value ranges.",AMBER),
        ("SLA","Freshness (updated by 6am), completeness (>99.5% non-null), latency.",STEEL),
        ("Versioning","Semantic versioning (1.0.0). Minor = backwards compatible. Major = breaking.",PUR),
        ("Ownership","Who is responsible for the data? Data owner contact, team.",ORANGE),
    ]
    c1,c2,c3 = st.columns(3)
    for i,(t,d,c) in enumerate(COMPONENTS):
        [c1,c2,c3][i%3].markdown(_card(f'<b style="color:{c};font-size:.82rem;">{t}</b><br><span style="font-size:.74rem;color:{TEXT};">{d}</span>',l=c,p="9px 12px"), unsafe_allow_html=True)

# ── TAB 1: CONTRACT DEFINITION ───────────────────────────────────────────────
with TAB[1]:
    st.markdown(_h2("Define a Data Contract","📝"), unsafe_allow_html=True)
    TRIPS_CONTRACT = {
        "contract_id": "trips_v1",
        "version": "1.2.0",
        "table": "trips",
        "description": "One row per completed/cancelled/in-progress rental trip",
        "owner": "Operations Team",
        "sla": {"freshness_hours": 1, "completeness_pct": 99.5},
        "schema": [
            {"column":"trip_id","type":"VARCHAR","nullable":False,"unique":True,"description":"Unique trip identifier. Format: TR######"},
            {"column":"fleet_id","type":"VARCHAR","nullable":False,"unique":False,"description":"FK → fleets.fleet_id"},
            {"column":"vehicle_id","type":"VARCHAR","nullable":False,"unique":False,"description":"FK → vehicles.vehicle_id"},
            {"column":"customer_id","type":"VARCHAR","nullable":False,"unique":False,"description":"FK → customers.customer_id"},
            {"column":"pickup_datetime","type":"TIMESTAMP","nullable":False,"unique":False,"description":"Trip start. Must be before dropoff_datetime"},
            {"column":"dropoff_datetime","type":"TIMESTAMP","nullable":True,"unique":False,"description":"Trip end. NULL if trip still in progress"},
            {"column":"trip_fare_pkr","type":"DOUBLE","nullable":False,"unique":False,"description":"Base fare in PKR. Must be >= 0"},
            {"column":"status","type":"VARCHAR","nullable":False,"unique":False,"description":"One of: Completed, Cancelled, In Progress, Confirmed"},
        ],
        "quality_rules": [
            {"rule":"trip_id is unique","sql":"SELECT COUNT(*) = COUNT(DISTINCT trip_id) FROM trips"},
            {"rule":"trip_fare_pkr >= 0","sql":"SELECT COUNT(*) FILTER(WHERE trip_fare_pkr < 0) = 0 FROM trips"},
            {"rule":"dropoff after pickup","sql":"SELECT COUNT(*) FILTER(WHERE dropoff_datetime < pickup_datetime) = 0 FROM trips"},
            {"rule":"status in valid set","sql":"SELECT COUNT(*) FILTER(WHERE status NOT IN ('Completed','Cancelled','In Progress','Confirmed')) = 0 FROM trips"},
        ]
    }
    st.json(TRIPS_CONTRACT)
    _contract_json = json.dumps(TRIPS_CONTRACT, indent=2)
    st.download_button("⬇ Download Contract (JSON)", data=_contract_json, file_name="trips_contract_v1.json", mime="application/json", key="dl_contract")

    # Contract YAML view
    st.markdown(_h3("📄 YAML Format (dbt-style)",STEEL), unsafe_allow_html=True)
    st.code("""# trips.yml — dbt schema file (data contract)
version: 2

models:
  - name: trips
    description: "One row per rental trip"
    config:
      contract:
        enforced: true  # dbt will validate schema on run

    columns:
      - name: trip_id
        data_type: varchar
        constraints:
          - type: not_null
          - type: unique
        description: "Unique trip identifier TR######"
        tests:
          - unique
          - not_null

      - name: trip_fare_pkr
        data_type: float
        constraints:
          - type: not_null
        tests:
          - not_null
          - dbt_expectations.expect_column_values_to_be_between:
              min_value: 0
              max_value: 10000000

      - name: status
        data_type: varchar
        tests:
          - accepted_values:
              values: ['Completed', 'Cancelled', 'In Progress', 'Confirmed']""", language="yaml")

# ── TAB 2: CONTRACT VALIDATION ───────────────────────────────────────────────
with TAB[2]:
    st.markdown(_h2("Contract Validation — Live","✅"), unsafe_allow_html=True)
    import duckdb as _ddb
    @st.cache_resource
    def _get_c(dfs):
        c = _ddb.connect(":memory:")
        for n,df in dfs.items():
            try: c.register(n,df)
            except: pass
        return c
    _vc = _get_c(dfs)

    VALIDATION_RULES = [
        ("trip_id uniqueness",     "SELECT COUNT(*) = COUNT(DISTINCT trip_id) AS passed FROM trips",           "uniqueness"),
        ("trip_id not null",       "SELECT COUNT(*) FILTER(WHERE trip_id IS NULL) = 0 AS passed FROM trips",   "not_null"),
        ("fare >= 0",              "SELECT COUNT(*) FILTER(WHERE CAST(trip_fare_pkr AS DOUBLE)<0)=0 AS passed FROM trips", "range"),
        ("status valid values",    "SELECT COUNT(*) FILTER(WHERE status NOT IN ('Completed','Cancelled','In Progress','Confirmed'))=0 AS passed FROM trips", "accepted_values"),
        ("pickup before dropoff",  "SELECT COUNT(*) FILTER(WHERE CAST(dropoff_datetime AS TIMESTAMP)<CAST(pickup_datetime AS TIMESTAMP))=0 AS passed FROM trips", "consistency"),
        ("customer_id not null",   "SELECT COUNT(*) FILTER(WHERE customer_id IS NULL OR customer_id='')=0 AS passed FROM trips", "not_null"),
        ("vehicle_id not null",    "SELECT COUNT(*) FILTER(WHERE vehicle_id IS NULL OR vehicle_id='')=0 AS passed FROM trips",   "not_null"),
    ]
    if st.button("▶ Run All Contract Tests", type="primary", key="run_contract"):
        _results = []
        for rule,sql,rtype in VALIDATION_RULES:
            try:
                _r = _vc.execute(sql).fetchone()
                _passed = bool(_r[0]) if _r else False
            except Exception as e:
                _passed = False
            _results.append({"Rule":rule,"Type":rtype,"Result":"✅ PASS" if _passed else "❌ FAIL","SQL":sql[:60]+"..."})
        _res_df = pd.DataFrame(_results)
        _p = len(_res_df[_res_df["Result"].str.startswith("✅")])
        _f = len(_res_df[_res_df["Result"].str.startswith("❌")])
        c1,c2,c3 = st.columns(3)
        c1.metric("Total Tests", str(len(_res_df)))
        c2.metric("Passed", str(_p))
        c3.metric("Failed", str(_f))
        st.dataframe(_res_df[["Rule","Type","Result"]], use_container_width=True, height=280, hide_index=True)
        if _f == 0: st.success("✅ All contract tests passed!")
        else: st.error(f"❌ {_f} contract test(s) failed — notify data producer!")

# ── TAB 3: BREAKING CHANGES ──────────────────────────────────────────────────
with TAB[3]:
    st.markdown(_h2("Breaking vs Non-Breaking Changes","⚠️"), unsafe_allow_html=True)
    BREAKING = [
        ("❌ Breaking","Column renamed","trip_fare → base_fare","All downstream queries break. Requires major version bump (1.x → 2.0).",BRAND),
        ("❌ Breaking","Column removed","dropoff_city column deleted","Any query selecting dropoff_city fails.",BRAND),
        ("❌ Breaking","Type changed (narrowing)","VARCHAR → DATE","Values that aren't valid dates break the cast.",BRAND),
        ("❌ Breaking","Nullability changed","NOT NULL → NULL allowed","Consumers expecting non-null now get NULLs.",AMBER),
        ("✅ Non-Breaking","New column added","Add driver_rating column","Old queries still work — they just don't use it.",TEAL),
        ("✅ Non-Breaking","Type widened","INT → BIGINT","All existing values still fit.",TEAL),
        ("✅ Non-Breaking","New accepted value","Add 'Postponed' to status values","Old consumers may ignore it but won't break.",TEAL),
        ("✅ Non-Breaking","New table added","Add new dim_weather table","Existing consumers unaffected.",TEAL),
    ]
    for change_type,name,example,impact,clr in BREAKING:
        st.markdown(_card(f'<b style="color:{clr};">{change_type}: {name}</b><br>'
                          f'<span style="font-size:.76rem;color:{TEXT};">Example: {example}</span><br>'
                          f'<span style="font-size:.73rem;color:{M};">Impact: {impact}</span>',l=clr,p="9px 14px"), unsafe_allow_html=True)

    st.markdown(_h3("📝 Semantic Versioning for Data Contracts",STEEL), unsafe_allow_html=True)
    st.code("""# Data Contract Versioning
# Format: MAJOR.MINOR.PATCH

MAJOR version: breaking changes
  trips v1.0.0 → v2.0.0 (renamed trip_fare_pkr column)

MINOR version: backwards-compatible additions
  trips v1.0.0 → v1.1.0 (added driver_rating column)

PATCH version: backwards-compatible fixes (docs, descriptions)
  trips v1.1.0 → v1.1.1 (fixed description typo)

# Migration strategy for breaking changes:
# 1. Announce deprecation (give consumers 4 weeks notice)
# 2. Run v1 (old) and v2 (new) in parallel
# 3. Consumers migrate to v2
# 4. Decommission v1 after migration window""", language="text")

# ── TAB 4: EXAMPLES ──────────────────────────────────────────────────────────
with TAB[4]:
    st.markdown(_h2("Real-World Data Contract Examples","📚"), unsafe_allow_html=True)
    st.markdown(_card(f'<b style="color:{TEAL};">How major companies use data contracts</b><br>'
                      f'<span style="font-size:.76rem;color:{TEXT};">Netflix: Data Mesh — each domain owns contracts for their data products<br>'
                      f'Uber: Protobuf schemas for real-time events + dbt contracts for warehouse tables<br>'
                      f'Airbnb: Schema registry (Confluent) for Kafka, dbt tests for DWH<br>'
                      f'LinkedIn: DataHub as the data catalogue and contract registry</span>',l=TEAL,p="10px 14px"), unsafe_allow_html=True)

    st.markdown(_h3("Tools for Data Contracts",AMBER), unsafe_allow_html=True)
    tools = [
        ("dbt","Schema contracts in YAML. Tests: not_null, unique, accepted_values, relationships. CI/CD integration."),
        ("Great Expectations","Python-native expectations library. Run DQ tests against any DataFrame or SQL table."),
        ("Soda Core","SQL-based data quality checks. YAML-defined tests. Connects to 20+ data sources."),
        ("DataHub","Data catalogue + contract registry. Lineage, ownership, schema history."),
        ("Monte Carlo","Automated data observability. Learns normal patterns, alerts on anomalies."),
        ("OpenMetadata","Open-source data catalogue. Contracts, lineage, profiling in one tool."),
    ]
    c1,c2 = st.columns(2)
    for i,(t,d) in enumerate(tools):
        (c1 if i%2==0 else c2).markdown(_card(f'<b style="color:{AMBER};font-size:.82rem;">{t}</b><br><span style="font-size:.74rem;color:{TEXT};">{d}</span>',l=AMBER,p="9px 12px"), unsafe_allow_html=True)
