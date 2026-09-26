"""
p18_security.py — Data Security
Row-level security · Column masking · SQL injection prevention
Role-based access · Encryption concepts · Security audit
"""
from datetime import datetime
import pandas as pd
import plotly.express as px
import streamlit as st
from page_modules._shared import inject, get_data, BRAND, STEEL, GREEN, AMBER, ORANGE, TEXT
inject()
M="#5a7a96"; CB="#141e2b"; BD="#1e2f44"; TEAL="#2A9D8F"; PUR="#6A4C93"
def _card(b,l=BRAND,p="14px 16px"): return f'<div style="background:{CB};border:1px solid {BD};border-left:3px solid {l};border-radius:10px;padding:{p};margin:6px 0;">{b}</div>'
def _h2(t,i=""): return f'<div style="font-size:1.22rem;font-weight:800;color:{TEXT};margin:16px 0 4px;"><span style="color:{BRAND};">{i} </span>{t}</div>'
def _h3(t,c=STEEL): return f'<div style="font-size:.9rem;font-weight:700;color:{c};border-left:3px solid {c};padding-left:8px;margin:10px 0 6px;">{t}</div>'

dfs       = get_data()
customers = dfs["customers"].copy()
trips     = dfs["trips"].copy()

st.markdown(f'<div style="font-size:1.6rem;font-weight:900;color:{BRAND};">🔐 Data Security</div>'
            f'<div style="font-size:.8rem;color:{M};">Row-level security · Column masking · SQL injection · RBAC · Encryption · Audit</div>',
            unsafe_allow_html=True)
st.markdown(f"<hr style='border-color:{BD};margin:6px 0 10px'>",unsafe_allow_html=True)

TAB = st.tabs(["🏠 Concepts","🔒 Column Masking","🛡️ Row-Level Security","💉 SQL Injection","🔑 RBAC","🔐 Encryption","🔍 Security Audit"])

# ── TAB 0: CONCEPTS ──────────────────────────────────────────────────────────
with TAB[0]:
    st.markdown(_h2("Data Security Principles","🏠"), unsafe_allow_html=True)
    concepts = [
        ("CIA Triad","<b>Confidentiality</b>: only authorised users see data<br><b>Integrity</b>: data is accurate and unaltered<br><b>Availability</b>: data is accessible when needed","🔐",BRAND),
        ("Defence in Depth","Multiple security layers — if one fails, others protect. Network → Application → Database → Data level.",  "🛡️",TEAL),
        ("Least Privilege","Give users only the minimum permissions they need to do their job. No more.",  "⬇️",AMBER),
        ("Zero Trust","Never trust, always verify. Even internal users must authenticate and authorise every request.","🚫",PUR),
        ("Data at Rest","Encryption of stored data — database files, backups, exports. AES-256 standard.","💾",STEEL),
        ("Data in Transit","TLS/HTTPS encryption for data moving between systems. Prevents man-in-the-middle attacks.","🌐",ORANGE),
        ("Audit Logging","Record every access, modification, export of sensitive data. Who, what, when, from where.","📋",BRAND),
        ("Tokenisation","Replace sensitive value with a non-sensitive token. Unlike encryption, token reveals nothing.","🎫",TEAL),
    ]
    c1,c2 = st.columns(2)
    for i,(t,b,ic,c) in enumerate(concepts):
        (c1 if i%2==0 else c2).markdown(_card(f'<div style="display:flex;gap:10px;"><span style="font-size:1.1rem;">{ic}</span><div><b style="color:{c};font-size:.82rem;">{t}</b><br><span style="font-size:.74rem;color:{TEXT};">{b}</span></div></div>',l=c,p="10px 14px"), unsafe_allow_html=True)

# ── TAB 1: COLUMN MASKING ────────────────────────────────────────────────────
with TAB[1]:
    st.markdown(_h2("Column-Level Masking","🔒"), unsafe_allow_html=True)
    st.markdown(_card("Masking shows obscured values to unauthorised users while authorised users see the real data. Implemented as SQL views or virtual columns.",l=TEAL), unsafe_allow_html=True)
    _role = st.selectbox("Simulated user role:", ["admin (full access)","analyst (partial mask)","viewer (full mask)"], key="mask_role")
    _cust_sample = customers.head(8).copy()

    if "admin" in _role:
        _display = _cust_sample[["customer_id","full_name","email","phone","cnic"]].copy()
        st.success("Admin: Full access — all PII visible")
    elif "analyst" in _role:
        _display = _cust_sample[["customer_id","full_name","email","phone","cnic"]].copy()
        _display["email"] = _display["email"].apply(lambda e: str(e)[:2]+"***@"+str(e).split("@")[-1] if "@" in str(e) else "***")
        _display["phone"] = _display["phone"].apply(lambda p: str(p)[:4]+"*******")
        _display["cnic"]  = "*****-*******-*"
        st.warning("Analyst: Email domain visible, phone/CNIC masked")
    else:
        _display = _cust_sample[["customer_id","full_name","email","phone","cnic"]].copy()
        _display["full_name"] = "*** ***"
        _display["email"]     = "***@***.***"
        _display["phone"]     = "****-*******"
        _display["cnic"]      = "*****-*******-*"
        st.error("Viewer: All PII fully masked")

    st.dataframe(_display, use_container_width=True, height=260, hide_index=True)
    st.markdown(_h3("📝 Masking SQL Pattern",STEEL), unsafe_allow_html=True)
    st.code("""-- Create a masked view for analyst role
CREATE OR REPLACE VIEW secure.customers_analyst AS
SELECT
    customer_id,
    full_name,
    -- Partial email: r***@gmail.com
    SUBSTR(email, 1, 1) || '***@' || SPLIT_PART(email, '@', 2)  AS email,
    -- Partial phone: 0300-*******
    SUBSTR(phone, 1, 4) || '-*******'                           AS phone,
    -- CNIC fully masked
    '*****-*******-*'                                            AS cnic,
    city,            -- not PII
    customer_type,   -- not PII
    registration_date
FROM customers;

-- Grant analyst role access to the view, NOT the base table
GRANT SELECT ON secure.customers_analyst TO ROLE analyst;
REVOKE SELECT ON customers FROM ROLE analyst;""", language="sql")

# ── TAB 2: ROW-LEVEL SECURITY ────────────────────────────────────────────────
with TAB[2]:
    st.markdown(_h2("Row-Level Security (RLS)","🛡️"), unsafe_allow_html=True)
    st.markdown(_card("RLS restricts which ROWS a user can see based on their identity. A fleet manager can only see their own fleet's data — the SQL returns a filtered result automatically, transparently.",l=PUR), unsafe_allow_html=True)
    _fleet = st.selectbox("Simulated manager fleet:", sorted(trips["fleet_id"].dropna().unique().tolist()), key="rls_fleet")
    _rls_data = trips[trips["fleet_id"]==_fleet][["trip_id","fleet_id","pickup_city","dropoff_city","trip_fare_pkr","status"]].head(10)
    _full_count = len(trips)
    st.info(f"RLS applied: showing {len(_rls_data)} rows for fleet {_fleet} (hidden: {_full_count - len(trips[trips['fleet_id']==_fleet])} rows from other fleets)")
    st.dataframe(_rls_data, use_container_width=True, height=240, hide_index=True)
    st.code(f"""-- RLS policy: manager sees only their fleet
CREATE POLICY fleet_manager_policy ON trips
    USING (fleet_id = current_setting('app.current_fleet_id'));

-- Set context at login
SET app.current_fleet_id = '{_fleet}';

-- Now this query automatically filters:
SELECT * FROM trips;  -- returns only fleet_id = '{_fleet}'""", language="sql")

# ── TAB 3: SQL INJECTION ─────────────────────────────────────────────────────
with TAB[3]:
    st.markdown(_h2("SQL Injection Prevention","💉"), unsafe_allow_html=True)
    st.markdown(_card("SQL injection is the #1 database attack. An attacker inserts malicious SQL into an input field to bypass authentication or extract/destroy data.",l=BRAND), unsafe_allow_html=True)
    c1,c2 = st.columns(2)
    with c1:
        st.markdown(_h3("❌ Vulnerable Code",BRAND), unsafe_allow_html=True)
        st.code("""# DANGEROUS: string concatenation
def get_customer(customer_id):
    sql = f\"\"\"SELECT * FROM customers
    WHERE customer_id = '{customer_id}'\"\"\"
    return conn.execute(sql)

# Attack: pass this as customer_id:
# ' OR '1'='1
# Resulting SQL:
# SELECT * FROM customers WHERE customer_id = '' OR '1'='1'
# Returns ALL customers!

# Worse attack:
# '; DROP TABLE customers; --
# Destroys the entire table!""", language="python")

    with c2:
        st.markdown(_h3("✅ Safe Parameterised Code",TEAL), unsafe_allow_html=True)
        st.code("""# SAFE: parameterised query
def get_customer(customer_id):
    sql = \"\"\"SELECT * FROM customers
    WHERE customer_id = ?\"\"\"
    # Value is passed separately, never concatenated
    return conn.execute(sql, [customer_id])

# Attack attempt:  ' OR '1'='1
# DuckDB treats it as a literal string value
# Returns 0 rows — no injection possible

# Additional defences:
# 1. Input validation (allow only CU[0-9]{5})
# 2. Least privilege (read-only DB user)
# 3. WAF at application layer
# 4. Prepared statements always""", language="python")

    # Live demo
    st.markdown(_h3("🔬 Live Injection Demo",AMBER), unsafe_allow_html=True)
    _user_input = st.text_input("Enter a customer_id:", value="CU00001", key="inj_input")
    import re as _re
    _safe = bool(_re.match(r'^CU\d{5}$', _user_input.strip()))
    if _safe:
        st.success(f"✅ Input VALID — matches pattern CU##### — safe to use")
        _result = customers[customers["customer_id"]==_user_input][["customer_id","full_name","customer_type"]].head(1)
        if len(_result): st.dataframe(_result, use_container_width=True, hide_index=True)
    else:
        st.error(f"❌ Input REJECTED — '{_user_input}' does not match expected pattern CU#####")
        st.warning("In production: log this as a suspicious request and block the IP after N attempts")

# ── TAB 4: RBAC ──────────────────────────────────────────────────────────────
with TAB[4]:
    st.markdown(_h2("Role-Based Access Control (RBAC)","🔑"), unsafe_allow_html=True)
    RBAC = {
        "admin":        {"Tables": "ALL", "Columns": "ALL", "Actions": "SELECT, INSERT, UPDATE, DELETE, GRANT", "PII Access": "Full"},
        "fleet_manager":{"Tables": "trips (own fleet), vehicles, drivers, invoices", "Columns": "All except CNIC, DOB", "Actions": "SELECT, UPDATE (own fleet)", "PII Access": "Partial"},
        "data_analyst": {"Tables": "trips (agg), invoices (agg), telematics, fuel_logs", "Columns": "No CNIC, masked email/phone", "Actions": "SELECT only", "PII Access": "Masked"},
        "report_viewer":{"Tables": "mart.* (pre-aggregated views only)", "Columns": "No PII whatsoever", "Actions": "SELECT on views only", "PII Access": "None"},
        "app_service":  {"Tables": "customers, trips, bookings", "Columns": "Required columns only", "Actions": "SELECT, INSERT (new trips)", "PII Access": "Minimal"},
    }
    rbac_df = pd.DataFrame(RBAC).T.reset_index().rename(columns={"index":"Role"})
    st.dataframe(rbac_df, use_container_width=True, height=220, hide_index=True)
    st.code("""-- Create roles in DuckDB / PostgreSQL
CREATE ROLE admin;
CREATE ROLE fleet_manager;
CREATE ROLE data_analyst;
CREATE ROLE report_viewer;

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO admin;
GRANT SELECT ON trips TO fleet_manager;
GRANT SELECT ON secure.customers_analyst TO data_analyst;  -- masked view
GRANT SELECT ON mart.daily_revenue TO report_viewer;

-- Assign users to roles
GRANT fleet_manager TO manager1;
GRANT data_analyst   TO analyst1;
GRANT report_viewer  TO viewer1;""", language="sql")

# ── TAB 5: ENCRYPTION ────────────────────────────────────────────────────────
with TAB[5]:
    st.markdown(_h2("Encryption Concepts","🔐"), unsafe_allow_html=True)
    ENC = [
        ("AES-256","Symmetric encryption for data at rest. Used for database files, backups, exports. Industry standard.","Encrypt entire DB file · Encrypt specific columns · Encrypted backups","Fast, strong. Key management critical."),
        ("TLS 1.3","Transport Layer Security for data in transit. All API calls, database connections must use TLS.","HTTPS for web app · SSL for DB connections · Certificate validation","Prevents eavesdropping and MITM attacks."),
        ("Hashing (SHA-256)","One-way irreversible. Use for passwords — never store plain text. Also used for data fingerprinting.","Password storage · File integrity · Pseudonymisation tokens","Not encryption — cannot be reversed."),
        ("Tokenisation","Replace sensitive value (credit card, CNIC) with a random token. Token stored locally; real value in secure vault.","Payment processing · CNIC storage · API keys","Different from encryption — token has no mathematical relation to original."),
    ]
    for enc_name,desc,uses,note in ENC:
        st.markdown(_card(f'<b style="color:{TEAL};font-size:.86rem;">{enc_name}</b><br>'
                          f'<span style="font-size:.76rem;color:{TEXT};">{desc}</span><br>'
                          f'<span style="font-size:.72rem;color:{M};">Uses: {uses} | Note: {note}</span>',l=TEAL,p="10px 14px"), unsafe_allow_html=True)

    st.code("""-- Conceptual: column-level encryption in SQL
-- (DuckDB doesn't natively support it — shown for learning)

-- Encrypt on INSERT:
INSERT INTO customers_secure (customer_id, cnic_encrypted)
VALUES ('CU00001', encrypt('35202-1234567-8', 'AES_KEY_256'));

-- Decrypt for authorised queries:
SELECT customer_id, decrypt(cnic_encrypted, 'AES_KEY_256') AS cnic
FROM customers_secure
WHERE current_role() = 'admin';

-- Hash passwords (NEVER store plain text):
INSERT INTO users (username, password_hash)
VALUES ('analyst1', sha256('MyP@ssword123'));""", language="sql")

# ── TAB 6: SECURITY AUDIT ────────────────────────────────────────────────────
with TAB[6]:
    st.markdown(_h2("Security Audit Checklist","🔍"), unsafe_allow_html=True)
    checks = [
        ("Are passwords hashed (SHA-256 / bcrypt)?","✅ Yes — auth.py uses plain comparison (demo only — use bcrypt in prod)","🔴"),
        ("Is HTTPS/TLS enforced?","✅ Streamlit serves over HTTP locally (use reverse proxy with TLS in prod)","🟡"),
        ("Are PII columns masked for non-admin roles?","⚠️ Partially — column masking views created in SQL but not enforced in app","🟡"),
        ("Is SQL built with parameterised queries?","✅ DuckDB conn.execute(sql, params) used throughout","✅"),
        ("Are unused accounts disabled?","⚠️ Demo: viewer1/driver accounts exist but limited pages","🟡"),
        ("Is audit logging enabled?","⚠️ meta.load_log exists for ETL — extend for data access logging","🟡"),
        ("Are backups encrypted?","📋 DuckDB .db file — encrypt at OS level with BitLocker/LUKS in prod","🟡"),
        ("Is least privilege applied?","⚠️ Role-based pages enforced — add DB-level GRANT statements in prod","🟡"),
        ("Are security headers set?","⚠️ Streamlit default headers — add CSP/HSTS via reverse proxy","🟡"),
        ("Is sensitive data in logs?","✅ No PII written to application logs","✅"),
    ]
    check_df = pd.DataFrame(checks, columns=["Check","Finding","Status"])
    st.dataframe(check_df, use_container_width=True, height=380, hide_index=True)
    _pass = sum(1 for _,_,s in checks if s=="✅")
    _warn = sum(1 for _,_,s in checks if s=="🟡")
    _fail = sum(1 for _,_,s in checks if s=="🔴")
    c1,c2,c3 = st.columns(3)
    c1.metric("Passed",str(_pass))
    c2.metric("Warnings",str(_warn))
    c3.metric("Failures",str(_fail))
