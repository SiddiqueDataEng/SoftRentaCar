"""
p17_governance.py — Data Governance & GDPR
Complete learning module covering:
- Data governance framework & principles
- GDPR rights simulation (access, erasure, portability)
- PII catalog — which columns hold personal data
- Data classification (Public / Internal / Confidential / Restricted)
- Consent tracking & audit log
- Data retention policies
- Anonymisation & pseudonymisation demos
"""
from datetime import datetime, date
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from page_modules._shared import inject, get_data, BRAND, STEEL, GREEN, AMBER, ORANGE, TEXT
inject()
M=  "#5a7a96"; CB="#141e2b"; BD="#1e2f44"; TEAL="#2A9D8F"; PUR="#6A4C93"

def _card(b,l=BRAND,p="14px 16px"): return f'<div style="background:{CB};border:1px solid {BD};border-left:3px solid {l};border-radius:10px;padding:{p};margin:6px 0;">{b}</div>'
def _h2(t,i=""): return f'<div style="font-size:1.22rem;font-weight:800;color:{TEXT};margin:16px 0 4px;display:flex;align-items:center;gap:8px;"><span style="color:{BRAND};">{i}</span>{t}</div>'
def _h3(t,c=STEEL): return f'<div style="font-size:.9rem;font-weight:700;color:{c};border-left:3px solid {c};padding-left:8px;margin:10px 0 6px;">{t}</div>'
def _badge(label,color): return f'<span style="background:{color}33;color:{color};padding:2px 9px;border-radius:12px;font-size:.7rem;font-weight:700;">{label}</span>'

dfs = get_data()
customers = dfs["customers"].copy()
trips     = dfs["trips"].copy()

st.markdown(f'<div style="font-size:1.6rem;font-weight:900;color:{BRAND};">🛡️ Data Governance & GDPR</div>'
            f'<div style="font-size:.8rem;color:{M};">Data governance framework · GDPR rights · PII catalog · Classification · Consent · Retention</div>',
            unsafe_allow_html=True)
st.markdown(f"<hr style='border-color:{BD};margin:6px 0 10px'>", unsafe_allow_html=True)

TAB = st.tabs(["📋 Framework","🔒 PII Catalog","⚖️ GDPR Rights","🏷️ Classification","📜 Audit Log","🗑️ Retention","🎭 Anonymisation"])

# ── TAB 0: FRAMEWORK ─────────────────────────────────────────────────────────
with TAB[0]:
    st.markdown(_h2("Data Governance Framework","📋"), unsafe_allow_html=True)
    st.markdown(_card(
        f'Data Governance is the <b>set of policies, roles, and processes</b> that ensure data is accurate, '
        f'available, consistent, and secure across the organisation.<br>'
        f'Without governance, data becomes a liability. With it, data becomes a competitive asset.',
        l=TEAL), unsafe_allow_html=True)

    c1,c2,c3 = st.columns(3)
    for col,(icon,title,body,clr) in zip([c1,c2,c3],[
        ("📊","Data Quality","Accuracy, completeness, consistency, timeliness of data. DQ checks, profiling, scorecards.",BRAND),
        ("🏛️","Data Stewardship","Roles: Data Owner (accountable), Data Steward (responsible), Data Consumer (uses data).",TEAL),
        ("📖","Data Catalogue","Centralised inventory of all data assets — tables, columns, owners, sensitivity, lineage.",AMBER),
    ]):
        col.markdown(_card(f'<div style="font-size:1.3rem;text-align:center;">{icon}</div>'
                           f'<b style="color:{clr};">{title}</b><br>'
                           f'<div style="font-size:.76rem;color:{TEXT};margin-top:4px;">{body}</div>', l=clr), unsafe_allow_html=True)

    st.markdown(_h3("🏗️ Governance Pillars",STEEL), unsafe_allow_html=True)
    pillars = [
        ("Data Quality","Profiling, DQ rules, anomaly detection, DQ scorecards","📊",BRAND),
        ("Data Security","Access control, encryption, masking, audit logs","🔐",PUR),
        ("Data Privacy / GDPR","PII handling, consent, rights management, retention","🛡️",TEAL),
        ("Data Lineage","End-to-end traceability: source → transform → consumption","🗺️",STEEL),
        ("Data Architecture","Standards for modelling, naming conventions, schema design","🏗️",AMBER),
        ("Master Data Mgmt","Single source of truth for core entities (customer, vehicle)","📦",ORANGE),
        ("Data Stewardship","Roles & responsibilities for each data domain","👤",GREEN),
        ("Metadata Management","Business definitions, technical metadata, data dictionary","📝",BRAND),
    ]
    c1,c2 = st.columns(2)
    for i,(t,d,ic,c) in enumerate(pillars):
        (c1 if i%2==0 else c2).markdown(_card(
            f'<div style="display:flex;gap:10px;"><span style="font-size:1.2rem;">{ic}</span>'
            f'<div><b style="color:{c};font-size:.84rem;">{t}</b><br>'
            f'<span style="font-size:.74rem;color:{TEXT};">{d}</span></div></div>', l=c), unsafe_allow_html=True)

    st.markdown(_h3("📐 DAMA DMBOK Wheel",STEEL), unsafe_allow_html=True)
    _categories = ["Data Quality","Data Security","Data Integration","Reference & Master Data",
                   "Data Warehousing","Metadata","Document & Content","Data Architecture",
                   "Data Modeling","Data Storage","Data Governance (center)"]
    fig_radar = go.Figure(go.Scatterpolar(
        r=[4,5,4,3,5,4,3,5,5,4,5],
        theta=_categories,
        fill='toself',
        line_color=BRAND,
        fillcolor=BRAND+"44",
        name="This Platform"
    ))
    fig_radar.update_layout(polar=dict(bgcolor=CB, radialaxis=dict(visible=True,range=[0,5],color=M),
                                        angularaxis=dict(color=TEXT)),
                             paper_bgcolor="rgba(0,0,0,0)", height=380,
                             margin=dict(t=20,b=20,l=20,r=20))
    st.plotly_chart(fig_radar, use_container_width=True)

# ── TAB 1: PII CATALOG ───────────────────────────────────────────────────────
with TAB[1]:
    st.markdown(_h2("PII Data Catalog","🔒"), unsafe_allow_html=True)
    st.markdown(_card(
        f'<b>PII (Personally Identifiable Information)</b> is any data that could identify a specific person.<br>'
        f'GDPR requires you to know exactly which columns hold PII, who can access them, '
        f'and how long they are retained.',l=PUR), unsafe_allow_html=True)

    PII_CATALOG = [
        {"Table":"customers","Column":"full_name","PII Type":"Direct Identifier","Sensitivity":"🔴 High","GDPR Art.":"Art.4(1)","Masking":"INITCAP(SPLIT_PART(name,' ',1)) || ' ***'","Retention":"5 years after last trip"},
        {"Table":"customers","Column":"email","PII Type":"Direct Identifier","Sensitivity":"🔴 High","GDPR Art.":"Art.4(1)","Masking":"SUBSTR(email,1,2)||'***@'||SPLIT_PART(email,'@',2)","Retention":"5 years after last trip"},
        {"Table":"customers","Column":"phone","PII Type":"Direct Identifier","Sensitivity":"🔴 High","GDPR Art.":"Art.4(1)","Masking":"SUBSTR(phone,1,4)||'*******'","Retention":"5 years"},
        {"Table":"customers","Column":"cnic","PII Type":"National ID","Sensitivity":"🔴 Critical","GDPR Art.":"Art.9","Masking":"'*****-*******-*'","Retention":"7 years (legal requirement)"},
        {"Table":"customers","Column":"dob","PII Type":"Quasi-Identifier","Sensitivity":"🟡 Medium","GDPR Art.":"Art.4(1)","Masking":"DATE_TRUNC('year',dob)","Retention":"5 years"},
        {"Table":"customers","Column":"city","PII Type":"Quasi-Identifier","Sensitivity":"🟡 Medium","GDPR Art.":"Art.4(1)","Masking":"(no masking needed)","Retention":"5 years"},
        {"Table":"trips","Column":"pickup_lat/lon","PII Type":"Location Data","Sensitivity":"🔴 High","GDPR Art.":"Art.4(1)","Masking":"ROUND(lat,1) — reduce precision","Retention":"3 years"},
        {"Table":"trips","Column":"dropoff_lat/lon","PII Type":"Location Data","Sensitivity":"🔴 High","GDPR Art.":"Art.4(1)","Masking":"ROUND(lon,1)","Retention":"3 years"},
        {"Table":"drivers","Column":"cnic","PII Type":"National ID","Sensitivity":"🔴 Critical","GDPR Art.":"Art.9","Masking":"'*****-*******-*'","Retention":"Duration of employment + 7 years"},
        {"Table":"drivers","Column":"license_no","PII Type":"Gov. ID","Sensitivity":"🔴 High","GDPR Art.":"Art.4(1)","Masking":"'LIC-*****'","Retention":"Duration of employment + 2 years"},
    ]
    pii_df = pd.DataFrame(PII_CATALOG)

    _pf = st.text_input("Search catalog:", placeholder="e.g. email, cnic, location", key="pii_search")
    if _pf:
        pii_df = pii_df[pii_df.apply(lambda r: _pf.lower() in r.to_string().lower(), axis=1)]

    st.dataframe(pii_df, use_container_width=True, height=350, hide_index=True)

    # Live PII scan
    st.markdown(_h3("🔬 Live PII Column Scanner",BRAND), unsafe_allow_html=True)
    _tbl = st.selectbox("Scan table:", ["customers","trips","drivers","invoices"], key="pii_tbl")
    if st.button("🔍 Scan for PII", key="pii_scan"):
        _df = dfs[_tbl].head(5)
        _pii_cols = [c for c in _df.columns if any(x in c.lower() for x in
                     ["name","email","phone","cnic","lat","lon","address","dob","license","nid"])]
        _non_pii  = [c for c in _df.columns if c not in _pii_cols]
        st.markdown(_h3(f"Results for {_tbl}",TEAL), unsafe_allow_html=True)
        c1,c2 = st.columns(2)
        with c1:
            st.markdown(_card(f'<b style="color:{BRAND};">🔴 PII Columns ({len(_pii_cols)})</b><br>'
                              +'<br>'.join(f'• {c}' for c in _pii_cols), l=BRAND, p="10px 14px"), unsafe_allow_html=True)
        with c2:
            st.markdown(_card(f'<b style="color:{TEAL};">✅ Non-PII ({len(_non_pii)})</b><br>'
                              +'<br>'.join(f'• {c}' for c in _non_pii[:10]), l=TEAL, p="10px 14px"), unsafe_allow_html=True)

# ── TAB 2: GDPR RIGHTS ───────────────────────────────────────────────────────
with TAB[2]:
    st.markdown(_h2("GDPR Rights Simulation","⚖️"), unsafe_allow_html=True)
    _cid = st.selectbox("Select Customer:", customers["customer_id"].head(20).tolist(), key="gdpr_cust")
    _cust_row = customers[customers["customer_id"]==_cid].iloc[0] if len(customers[customers["customer_id"]==_cid]) else None

    GDPR_RIGHTS = st.tabs(["Art.15 Access","Art.17 Erasure","Art.20 Portability","Art.16 Rectification","Art.21 Objection"])

    with GDPR_RIGHTS[0]:
        st.markdown(_h3("Right of Access — Article 15",TEAL), unsafe_allow_html=True)
        st.markdown(_card('The data subject has the right to obtain confirmation of whether personal data '
                          'concerning them is being processed and a copy of that data.',l=TEAL), unsafe_allow_html=True)
        if st.button("📋 Generate Subject Access Report",key="sar_gen") and _cust_row is not None:
            _c_trips = trips[trips["customer_id"]==_cid]
            st.markdown(f"### Subject Access Report — {_cust_row['full_name']}")
            st.markdown(f"**Generated:** {datetime.now():%Y-%m-%d %H:%M} | **Customer ID:** {_cid}")
            st.markdown("#### Personal Data Held")
            _sar_data = {k: str(v) for k,v in _cust_row.items()}
            st.json(_sar_data)
            st.markdown(f"#### Transaction History ({len(_c_trips)} trips)")
            if len(_c_trips): st.dataframe(_c_trips[["trip_id","pickup_datetime","pickup_city","dropoff_city","trip_fare_pkr","status"]].head(10), use_container_width=True, hide_index=True)
            _report = f"GDPR SUBJECT ACCESS REPORT\n{'='*50}\nCustomer: {_cust_row['full_name']}\nID: {_cid}\nGenerated: {datetime.now()}\n\nPERSONAL DATA:\n{_sar_data}\n\nTRIPS: {len(_c_trips)} records"
            st.download_button("⬇ Download SAR", data=_report, file_name=f"SAR_{_cid}.txt", mime="text/plain", key="dl_sar")

    with GDPR_RIGHTS[1]:
        st.markdown(_h3("Right to Erasure (Right to be Forgotten) — Article 17",BRAND), unsafe_allow_html=True)
        st.markdown(_card('<b>Conditions:</b> Data no longer necessary · Consent withdrawn · Data unlawfully processed<br>'
                          '<b>Exceptions:</b> Legal obligation · Public interest · Legal claims',l=BRAND), unsafe_allow_html=True)
        st.markdown("**Erasure SQL that would execute:**")
        _erasure_sql = f"""-- GDPR Art.17: Erasure for customer {_cid}
-- Step 1: Anonymise PII (preferred over hard delete to preserve analytics)
UPDATE customers
SET full_name  = 'ANONYMISED',
    email      = 'deleted@gdpr.invalid',
    phone      = '0000-0000000',
    cnic       = '00000-0000000-0'
WHERE customer_id = '{_cid}';

-- Step 2: Nullify location data from trips
UPDATE trips
SET pickup_lat = NULL, pickup_lon = NULL,
    dropoff_lat = NULL, dropoff_lon = NULL
WHERE customer_id = '{_cid}';

-- Step 3: Log erasure in audit table
INSERT INTO meta.gdpr_erasure_log VALUES
    ('{_cid}', current_timestamp, 'Art.17 - Customer request', 'anonymised');"""
        st.code(_erasure_sql, language="sql")
        if st.button("🔴 Simulate Erasure (no real changes)", key="sim_erasure"):
            st.warning(f"SIMULATION ONLY: Would anonymise customer {_cid} and nullify location data.")
            st.success("✅ Erasure logged to meta.gdpr_erasure_log")

    with GDPR_RIGHTS[2]:
        st.markdown(_h3("Right to Data Portability — Article 20",TEAL), unsafe_allow_html=True)
        if _cust_row is not None:
            _c_trips2 = trips[trips["customer_id"]==_cid]
            _portable = {"customer": _cust_row.to_dict(), "trips": _c_trips2.head(20).to_dict(orient="records")}
            import json as _json
            _port_json = _json.dumps(_portable, indent=2, default=str)
            st.code(_port_json[:1000]+"...", language="json")
            st.download_button("⬇ Download My Data (JSON)", data=_port_json, file_name=f"my_data_{_cid}.json", mime="application/json", key="dl_portable")

    with GDPR_RIGHTS[3]:
        st.markdown(_h3("Right to Rectification — Article 16",AMBER), unsafe_allow_html=True)
        st.markdown(_card('Customer can request correction of inaccurate data. Must be corrected without undue delay.',l=AMBER), unsafe_allow_html=True)
        if _cust_row is not None:
            _new_name  = st.text_input("Correct full_name:", value=str(_cust_row.get("full_name","")), key="rect_name")
            _new_email = st.text_input("Correct email:", value=str(_cust_row.get("email","")), key="rect_email")
            if st.button("📝 Generate Rectification SQL", key="rect_sql"):
                st.code(f"""UPDATE customers
SET full_name = '{_new_name}',
    email     = '{_new_email}',
    updated_at = current_timestamp
WHERE customer_id = '{_cid}';
-- Log to audit
INSERT INTO meta.gdpr_rectification_log VALUES ('{_cid}', current_timestamp, 'full_name,email');""", language="sql")

    with GDPR_RIGHTS[4]:
        st.markdown(_h3("Right to Object — Article 21",PUR), unsafe_allow_html=True)
        st.markdown(_card('Data subject can object to processing for direct marketing, profiling, or legitimate interests.',l=PUR), unsafe_allow_html=True)
        _obj_reason = st.selectbox("Objection reason:", ["Direct marketing","Automated profiling","Legitimate interests","Research/statistics"], key="obj_reason")
        if st.button("📋 Generate Objection SQL", key="obj_sql"):
            st.code(f"""-- GDPR Art.21 Objection — stop processing for {_cid}
INSERT INTO meta.gdpr_objections (customer_id, objection_type, received_at, status)
VALUES ('{_cid}', '{_obj_reason}', current_timestamp, 'accepted');

-- Exclude from marketing queries
UPDATE customers
SET marketing_opt_out = true,
    profiling_opt_out = true
WHERE customer_id = '{_cid}';""", language="sql")

# ── TAB 3: CLASSIFICATION ────────────────────────────────────────────────────
with TAB[3]:
    st.markdown(_h2("Data Classification","🏷️"), unsafe_allow_html=True)
    LEVELS = [
        ("🔴 Restricted","CNIC, biometrics, passwords, full credit card","Encrypted at rest+transit, strict RBAC, audit every access","Breach: report to regulator within 72hrs"),
        ("🟠 Confidential","Email, phone, DOB, exact location, salary","Encrypted, role-based, no external sharing without consent","Internal only"),
        ("🟡 Internal","Customer city, fleet names, booking types","Internal networks only, no public exposure","General staff"),
        ("🟢 Public","Fleet website, vehicle categories, pricing","Can be shared publicly","Anyone"),
    ]
    for lvl,ex,control,note in LEVELS:
        st.markdown(_card(
            f'<b style="font-size:.9rem;">{lvl}</b><br>'
            f'<span style="font-size:.76rem;color:{TEXT};"><b>Examples:</b> {ex}</span><br>'
            f'<span style="font-size:.74rem;color:{M};"><b>Controls:</b> {control}</span><br>'
            f'<span style="font-size:.72rem;color:{M};">{note}</span>',
            l=BRAND if "Restricted" in lvl else AMBER if "Confidential" in lvl else TEAL if "Internal" in lvl else GREEN,
            p="10px 14px"), unsafe_allow_html=True)

# ── TAB 4: AUDIT LOG ─────────────────────────────────────────────────────────
with TAB[4]:
    st.markdown(_h2("Governance Audit Log","📜"), unsafe_allow_html=True)
    import random as _r; _r.seed(42)
    _users = ["admin","analyst1","manager1","viewer1"]
    _actions = ["SELECT customers","SELECT trips WHERE customer_id=","UPDATE customers SET","EXPORT data","ACCESS PII field email","GDPR SAR generated","Role changed"]
    _audit_rows = []
    for i in range(50):
        _dt = datetime.now() - __import__("datetime").timedelta(hours=_r.randint(0,720))
        _audit_rows.append({"Timestamp":_dt.strftime("%Y-%m-%d %H:%M"),"User":_r.choice(_users),"Action":_r.choice(_actions),"Table":_r.choice(["customers","trips","invoices","drivers"]),"Rows Accessed":_r.randint(1,5000),"PII Access":_r.choice(["Yes","No","No","No"]),"Status":_r.choice(["Success","Success","Success","Denied"])})
    _audit_df = pd.DataFrame(_audit_rows).sort_values("Timestamp",ascending=False)
    _pii_filter = st.checkbox("Show only PII access events", key="audit_pii_filter")
    if _pii_filter:
        _audit_df = _audit_df[_audit_df["PII Access"]=="Yes"]
    st.dataframe(_audit_df, use_container_width=True, height=400, hide_index=True)
    st.download_button("⬇ Export Audit Log", data=_audit_df.to_csv(index=False), file_name="audit_log.csv", mime="text/csv", key="dl_audit")

# ── TAB 5: RETENTION ─────────────────────────────────────────────────────────
with TAB[5]:
    st.markdown(_h2("Data Retention Policies","🗑️"), unsafe_allow_html=True)
    RETENTION = [
        {"Table":"customers","Retention Period":"5 years after last trip","Legal Basis":"Contract performance","Delete Action":"Anonymise PII, keep aggregate","GDPR Article":"Art.5(1)(e)"},
        {"Table":"trips","Retention Period":"3 years","Legal Basis":"Contract + tax obligations","Delete Action":"Nullify lat/lon, keep for revenue reporting","GDPR Article":"Art.17"},
        {"Table":"invoices","Retention Period":"7 years","Legal Basis":"Tax law (mandatory)","Delete Action":"Cannot delete — legal hold","GDPR Article":"Art.17(3)(b)"},
        {"Table":"drivers","Retention Period":"Employment + 7 years","Legal Basis":"Employment law","Delete Action":"Anonymise after employment ends + 7yr","GDPR Article":"Art.17(3)(b)"},
        {"Table":"telematics","Retention Period":"2 years","Legal Basis":"Legitimate interest","Delete Action":"Hard delete after 2 years","GDPR Article":"Art.6(1)(f)"},
        {"Table":"fuel_logs","Retention Period":"3 years","Legal Basis":"Tax/audit","Delete Action":"Anonymise vehicle ID","GDPR Article":"Art.17"},
        {"Table":"meta.audit_log","Retention Period":"10 years","Legal Basis":"Compliance","Delete Action":"Archive to cold storage","GDPR Article":"Art.5(2)"},
    ]
    st.dataframe(pd.DataFrame(RETENTION), use_container_width=True, height=300, hide_index=True)
    st.markdown(_h3("🔬 Retention Check — Simulate Expiry",AMBER), unsafe_allow_html=True)
    _cutoff = st.slider("Retention cutoff (years ago):", 1, 10, 5, key="ret_cutoff")
    st.code(f"""-- Find records eligible for deletion/anonymisation
SELECT customer_id, full_name, MAX(registration_date) AS registered,
       DATEDIFF('year', MAX(registration_date), current_date) AS years_since_reg
FROM customers
LEFT JOIN trips t ON customers.customer_id = t.customer_id
GROUP BY customer_id, full_name
HAVING MAX(registration_date) < current_date - INTERVAL '{_cutoff} years'
   AND COUNT(t.trip_id) = 0  -- no trips in retention window
ORDER BY years_since_reg DESC;""", language="sql")

# ── TAB 6: ANONYMISATION ─────────────────────────────────────────────────────
with TAB[6]:
    st.markdown(_h2("Anonymisation & Pseudonymisation","🎭"), unsafe_allow_html=True)
    c1,c2 = st.columns(2)
    with c1:
        st.markdown(_card(f'<b style="color:{TEAL};">Pseudonymisation</b><br><span style="font-size:.76rem;color:{TEXT};">Replace direct identifiers with a reversible token/hash. Re-identification possible with key. Reduces risk but still personal data under GDPR.</span>',l=TEAL), unsafe_allow_html=True)
    with c2:
        st.markdown(_card(f'<b style="color:{BRAND};">Anonymisation</b><br><span style="font-size:.76rem;color:{TEXT};">Irreversible removal of all identifying info. No longer personal data under GDPR. Enables free use of data for analytics.</span>',l=BRAND), unsafe_allow_html=True)

    ANON_TECHNIQUES = {"k-Anonymity":"Each record is indistinguishable from at least k-1 others on quasi-identifiers (e.g. age band + city)","l-Diversity":"Each equivalence class has at least l well-represented values of sensitive attributes","Data Masking":"Replace PII with realistic but fake values (e.g. name→ random name, email→ fake@test.com)","Generalisation":"Reduce precision (exact age → age band, full city → province)","Suppression":"Remove records with unique combinations of quasi-identifiers","Noise Addition":"Add small random values to numerical data to prevent exact re-identification"}
    for tech, desc in ANON_TECHNIQUES.items():
        st.markdown(_card(f'<b style="color:{AMBER};font-size:.82rem;">{tech}</b><br><span style="font-size:.76rem;color:{TEXT};">{desc}</span>', l=AMBER, p="9px 14px"), unsafe_allow_html=True)

    st.markdown(_h3("🔬 Live Anonymisation Demo",TEAL), unsafe_allow_html=True)
    _anon_rows = customers.head(5).copy()
    import hashlib as _hl
    _anon_rows["full_name_anon"]  = _anon_rows["full_name"].apply(lambda n: "Person_"+_hl.md5(str(n).encode()).hexdigest()[:6])
    _anon_rows["email_anon"]      = _anon_rows["email"].apply(lambda e: "user_"+_hl.md5(str(e).encode()).hexdigest()[:8]+"@anon.invalid")
    _anon_rows["phone_anon"]      = "0300-*******"
    _anon_rows["cnic_anon"]       = "*****-*******-*"
    _anon_rows["age_band"]        = _anon_rows["dob"].apply(lambda d: "30-40" if d else "Unknown")
    st.markdown("**Original PII:**")
    st.dataframe(_anon_rows[["customer_id","full_name","email","phone","cnic"]].rename(columns={"full_name":"Name","email":"Email","phone":"Phone","cnic":"CNIC"}), use_container_width=True, height=180, hide_index=True)
    st.markdown("**After anonymisation:**")
    st.dataframe(_anon_rows[["customer_id","full_name_anon","email_anon","phone_anon","cnic_anon","age_band"]].rename(columns={"full_name_anon":"Name","email_anon":"Email","phone_anon":"Phone","cnic_anon":"CNIC","age_band":"Age Band"}), use_container_width=True, height=180, hide_index=True)
