"""
Soft Rent a Car — Single-file router.
Pure manual routing — NO st.navigation() — so auth works correctly.
Flow: inject CSS → auth gate (login) → sidebar + role-aware home → page exec
"""

import streamlit as st
import sys
from pathlib import Path

st.set_page_config(
    page_title="Soft Rent a Car",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded",
)

sys.path.insert(0, str(Path(__file__).parent))

from app.auth   import verify_login, is_logged_in, current_user, current_role, logout, ROLES
from app.themes import THEMES, DEFAULT_THEME, get_theme_css, FOOTER_HTML
from page_modules._shared import get_data

# ── Session defaults ───────────────────────────────────────────────────
for k, v in [("selected_theme", DEFAULT_THEME),
              ("current_page",   "home"),
              ("login_error",    ""),
              ("chat_history",   [])]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── Inject theme CSS ───────────────────────────────────────────────────
theme = THEMES[st.session_state.selected_theme]
st.markdown(get_theme_css(theme), unsafe_allow_html=True)

a     = theme["accent"]
a2    = theme["accent2"]
txt   = theme["text"]
muted = theme["text_muted"]
cbg   = theme["card_bg"]
cb    = theme["card_bdr"]
bg    = theme["app_bg"]
succ  = theme["success"]
warn  = theme["warning"]
dang  = theme["danger"]


# ══════════════════════════════════════════════════════════════════════
#  LOGIN  (shown when not authenticated)
# ══════════════════════════════════════════════════════════════════════
if not is_logged_in():

    st.markdown("""
<style>
[data-testid="stSidebar"]  { display:none !important; }
[data-testid="stSidebarNav"]{ display:none !important; }
</style>""", unsafe_allow_html=True)

    st.markdown(f"""
<style>
.stApp {{
    background: radial-gradient(ellipse at 25% 45%,
        {a}20 0%, {bg} 55%) !important;
}}
.lcard {{
    max-width:420px; margin:44px auto 0;
    background:{cbg}; border:1px solid {cb};
    border-radius:22px; padding:38px 34px 28px;
    box-shadow: 0 24px 80px rgba(0,0,0,.6), 0 0 0 1px {a}12;
}}
.ltitle {{ font-size:1.65rem;font-weight:800;color:{a};text-align:center;margin-bottom:2px; }}
.lsub   {{ font-size:.78rem;color:{muted};text-align:center;letter-spacing:.04em;margin-bottom:22px; }}
.rpill  {{ display:inline-flex;align-items:center;gap:4px;padding:4px 10px;border-radius:20px;
           font-size:.65rem;font-weight:600;border:1px solid;margin:2px; }}
.lhint  {{ font-size:.69rem;color:{muted};text-align:center;margin-top:12px;line-height:1.75;
           background:{bg};border:1px solid {cb};border-radius:8px;padding:9px 12px; }}
.lerror {{ background:{a}18;border:1px solid {a};border-radius:8px;padding:9px 14px;
           font-size:.82rem;color:{a};text-align:center;margin-top:8px; }}
.lfooter{{ text-align:center;margin-top:18px;font-size:.67rem;color:{muted};line-height:1.9; }}
.lfooter a {{ color:{a2};text-decoration:none; }}
.lfooter a:hover {{ color:{a}; }}
code {{ background:{cb}33;padding:1px 6px;border-radius:4px;font-size:.75em;color:{txt}; }}
</style>""", unsafe_allow_html=True)

    _, lc, _ = st.columns([1, 1.55, 1])
    with lc:
        # Header
        st.markdown(f"""
<div style="text-align:center;margin-bottom:16px;">
  <div style="font-size:3rem;">🚗</div>
  <div class="ltitle">Soft Rent a Car</div>
  <div class="lsub">Fleet Intelligence Platform</div>
</div>""", unsafe_allow_html=True)

        # Role pills
        pills = "".join(
            f'<span class="rpill" style="color:{rv["color"]};border-color:{rv["color"]}55;'
            f'background:{rv["color"]}12;">{rv["icon"]} {rv["label"]}</span>'
            for rv in ROLES.values()
        )
        st.markdown(f'<div style="text-align:center;margin-bottom:16px;">{pills}</div>',
                    unsafe_allow_html=True)

        # Login form
        with st.form("lf", clear_on_submit=False):
            uname = st.text_input("Username", placeholder="e.g. admin",      key="l_u")
            passw = st.text_input("Password", placeholder="Enter password",
                                  type="password",                             key="l_p")
            ok = st.form_submit_button("🔐  Sign In",
                                       use_container_width=True, type="primary")

        if ok:
            if not uname.strip() or not passw.strip():
                st.session_state.login_error = "Please enter both username and password."
            else:
                u = verify_login(uname.strip(), passw.strip())
                if u:
                    st.session_state.user         = u
                    st.session_state.current_page = "home"
                    st.session_state.login_error  = ""
                    st.rerun()
                else:
                    st.session_state.login_error = "❌ Invalid username or password."

        if st.session_state.login_error:
            st.markdown(f'<div class="lerror">{st.session_state.login_error}</div>',
                        unsafe_allow_html=True)

        st.markdown(f"""
<div class="lhint">
  <strong style="color:{txt};">Demo accounts</strong><br>
  <code>admin</code>&nbsp;/&nbsp;Admin@2026 &nbsp;·&nbsp;
  <code>manager1</code>&nbsp;/&nbsp;Manager@2026<br>
  <code>analyst1</code>&nbsp;/&nbsp;Analyst@2026 &nbsp;·&nbsp;
  <code>viewer1</code>&nbsp;/&nbsp;Viewer@2026
</div>
<div class="lfooter">
  Developed by <strong style="color:{txt};">Muhammad Siddique</strong><br>
  <a href="tel:+923229948042">+92 322 9948042</a> ·
  <a href="mailto:siddique.dea@gmail.com">siddique.dea@gmail.com</a><br>
  <a href="https://www.datawithms.top" target="_blank">datawithms.top</a> ·
  <a href="https://www.linkedin.com/in/siddique-datalover" target="_blank">LinkedIn</a>
</div>""", unsafe_allow_html=True)

    st.stop()   # ← Nothing below runs unless authenticated


# ══════════════════════════════════════════════════════════════════════
#  AUTHENTICATED APP
# ══════════════════════════════════════════════════════════════════════
user      = current_user()
role      = current_role()
role_meta = ROLES.get(role, ROLES["viewer"])

PAGE_CATALOG = {
    "home":      {"title": "Home",                "icon": "🏠"},
    "executive": {"title": "Executive Dashboard", "icon": "📊"},
    "finance":   {"title": "Finance & Revenue",   "icon": "💰"},
    "operations":{"title": "Operations & Trips",  "icon": "🚗"},
    "map":       {"title": "Demand Map",          "icon": "🗺️"},
    "drivers":   {"title": "Driver Safety & AI",  "icon": "🚦"},
    "fleet":     {"title": "Fleet Health",        "icon": "🔧"},
    "forecast":  {"title": "Forecasting",         "icon": "📈"},
    "stories":   {"title": "Data Storytelling",   "icon": "📖"},
    "chat":      {"title": "AI Chat",             "icon": "🤖"},
    "alerts":    {"title": "Alerts",              "icon": "⚠️"},
    "sql":       {"title": "SQL Analytics",       "icon": "🔍"},
}

PAGE_FILES = {
    "executive": "page_modules/p1_executive.py",
    "finance":   "page_modules/p2_finance.py",
    "operations":"page_modules/p3_operations.py",
    "map":       "page_modules/p7_map.py",
    "drivers":   "page_modules/p4_drivers.py",
    "fleet":     "page_modules/p5_fleet.py",
    "forecast":  "page_modules/p6_forecast.py",
    "stories":   "page_modules/p8_stories.py",
    "chat":      "page_modules/p9_chat.py",
    "alerts":    "page_modules/p10_alerts.py",
    "sql":       "page_modules/p11_sql.py",
}

NAV_GROUPS = {
    "📌 Overview":       ["home", "executive"],
    "💰 Finance":        ["finance"],
    "🚗 Operations":     ["operations", "map"],
    "👤 People":         ["drivers"],
    "🔧 Fleet":          ["fleet"],
    "🧠 Intelligence":   ["forecast", "stories"],
    "🛠️ Tools":          ["chat", "alerts", "sql"],
}

def _allowed(k):
    if role == "admin": return True
    p = role_meta.get("pages", [])
    return p == "all" or k in p

# ── Sidebar ─────────────────────────────────────────────────────────────
with st.sidebar:
    # Logo
    st.markdown(f"""
<div style="padding:10px 0 6px;display:flex;align-items:center;gap:9px;">
  <span style="font-size:1.8rem;">🚗</span>
  <div>
    <div style="font-size:1.05rem;font-weight:800;color:{a};line-height:1.15;">
      Soft Rent a Car</div>
    <div style="font-size:.57rem;letter-spacing:.1em;text-transform:uppercase;
                color:{muted};">Fleet Intelligence</div>
  </div>
</div><hr style="border-color:{cb};margin:4px 0 8px;">""", unsafe_allow_html=True)

    # User badge
    st.markdown(f"""
<div style="background:{cbg};border:1px solid {cb};border-radius:10px;
            padding:9px 11px;margin-bottom:8px;">
  <div style="display:flex;align-items:center;gap:8px;">
    <span style="font-size:1.3rem;line-height:1;">{role_meta['icon']}</span>
    <div>
      <div style="font-size:.82rem;font-weight:700;color:{txt};">{user['name']}</div>
      <div style="font-size:.61rem;color:{role_meta['color']};font-weight:600;
                  text-transform:uppercase;letter-spacing:.06em;">{role_meta['label']}</div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

    # Navigation buttons
    cur_page = st.session_state.current_page
    for grp, keys in NAV_GROUPS.items():
        visible = [k for k in keys if _allowed(k)]
        if not visible: continue
        st.markdown(
            f'<div style="font-size:.6rem;font-weight:700;color:{muted};'
            f'text-transform:uppercase;letter-spacing:.07em;padding:7px 0 2px 1px;">'
            f'{grp}</div>', unsafe_allow_html=True)
        for key in visible:
            info = PAGE_CATALOG[key]
            is_cur = (key == cur_page)
            btn_style = (f"background:{a}22;border-left:3px solid {a};"
                         if is_cur else "")
            label = f"{info['icon']}  {info['title']}"
            st.markdown(
                f'<style>.nav-btn-{key} button{{'
                f'{btn_style}color:{a if is_cur else txt}!important;}}</style>',
                unsafe_allow_html=True)
            if st.button(label, key=f"nav_{key}", use_container_width=True):
                st.session_state.current_page = key
                st.rerun()

    st.markdown(f"<hr style='border-color:{cb};margin:8px 0;'>", unsafe_allow_html=True)

    # Theme picker — horizontal radio
    st.markdown(
        f'<div style="font-size:.6rem;font-weight:700;color:{muted};'
        f'text-transform:uppercase;letter-spacing:.07em;margin-bottom:4px;">'
        f'🎨 Theme</div>', unsafe_allow_html=True)
    theme_keys   = list(THEMES.keys())
    theme_labels = ["🌑 Navy","🌿 Green","🔥 Red","💜 Purple","🌊 Blue"]
    cur_tidx     = theme_keys.index(st.session_state.selected_theme)
    picked = st.radio("_th", theme_labels, index=cur_tidx,
                      key="th_radio", label_visibility="collapsed",
                      horizontal=True)
    picked_full = theme_keys[theme_labels.index(picked)]
    if picked_full != st.session_state.selected_theme:
        st.session_state.selected_theme = picked_full
        st.rerun()

    st.markdown(f"<hr style='border-color:{cb};margin:8px 0;'>", unsafe_allow_html=True)

    # Sign out
    if st.button("🚪  Sign Out", use_container_width=True, key="so_btn"):
        logout()

    # Dev card
    st.markdown(f"""
<div style="margin-top:8px;background:{cbg};border:1px solid {cb};
            border-radius:10px;padding:9px 11px;">
  <div style="font-size:.62rem;font-weight:700;color:{a};margin-bottom:3px;">
    👨‍💻 Developer</div>
  <div style="font-size:.63rem;color:{txt};font-weight:600;">Muhammad Siddique</div>
  <div style="font-size:.59rem;color:{muted};margin-top:3px;line-height:1.75;">
    <a href="tel:+923229948042" style="color:{a2};text-decoration:none;">
      📞 +92 322 9948042</a><br>
    <a href="mailto:siddique.dea@gmail.com" style="color:{a2};text-decoration:none;">
      ✉️ siddique.dea@gmail.com</a><br>
    <a href="https://www.datawithms.top" target="_blank"
       style="color:{a2};text-decoration:none;">🌐 datawithms.top</a>&nbsp;·&nbsp;
    <a href="https://www.linkedin.com/in/siddique-datalover" target="_blank"
       style="color:{a2};text-decoration:none;">💼 LinkedIn</a>
  </div>
</div>""", unsafe_allow_html=True)


# ── Role-specific HOME dashboards ─────────────────────────────────────
def render_home():
    dfs = get_data()

    if role == "admin":
        _home_admin(dfs)
    elif role == "manager":
        _home_manager(dfs)
    elif role == "analyst":
        _home_analyst(dfs)
    elif role == "viewer":
        _home_viewer(dfs)
    elif role == "driver":
        _home_driver(dfs, user)
    else:
        _home_viewer(dfs)


def _kpi(col, value, label, delta="", pos=True):
    dc = "kpi-delta-up" if pos else "kpi-delta-down"
    if not delta: dc = "kpi-delta-neu"
    col.markdown(f"""
<div class="kpi-card">
  <div class="kpi-val">{value}</div>
  <div class="kpi-lbl">{label}</div>
  <div class="{dc}">{delta}</div>
</div>""", unsafe_allow_html=True)


def _fmt(v):
    v = float(v)
    if v >= 1e9: return f"PKR {v/1e9:.2f}B"
    if v >= 1e6: return f"PKR {v/1e6:.1f}M"
    if v >= 1e3: return f"PKR {v/1e3:.0f}K"
    return f"PKR {v:,.0f}"


def _sec(title):
    st.markdown(f'<div class="sec-hdr">{title}</div>', unsafe_allow_html=True)


def _alert(msg, level="info"):
    st.markdown(f'<div class="alert-{level}">{msg}</div>', unsafe_allow_html=True)


def _hex_to_rgba(hex_color: str, alpha: float) -> str:
    """Convert #RRGGBB to rgba(r,g,b,alpha) — required by Plotly 6+."""
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c*2 for c in h)
    r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    return f"rgba({r},{g},{b},{alpha})"


# ── ADMIN HOME ─────────────────────────────────────────────────────────
def _home_admin(dfs):
    import plotly.graph_objects as go
    from page_modules._shared import dark_layout
    import pandas as pd

    st.markdown(f"""
<div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
  <span style="font-size:2rem;">👑</span>
  <div>
    <div style="font-size:1.5rem;font-weight:800;color:{a};">
      Welcome back, {user['name']}</div>
    <div style="font-size:.8rem;color:{muted};">
      Administrator · Full platform access · All {len(dfs['fleets'])} fleets</div>
  </div>
</div><hr style="border-color:{cb};margin:6px 0 14px;">""", unsafe_allow_html=True)

    inv = dfs["invoices"]; trips = dfs["trips"]
    veh = dfs["vehicles"]; tel   = dfs["telematics"]
    fuel= dfs["fuel_logs"]; maint= dfs["maintenance"]

    total_rev = inv["total_amount_pkr"].sum()
    collected = inv["paid_amount_pkr"].sum()
    completed = (trips["status"]=="Completed").sum()
    avg_score = tel["safety_score"].mean()
    accidents = int(tel["accident_occurred"].sum())
    fleet_act = (veh["status"]!="Retired").sum()
    risky_drv = dfs["drivers"]["behavior_profile"].isin(["poor","dangerous"]).sum()

    c = st.columns(4)
    _kpi(c[0], _fmt(total_rev),     "Total Revenue",      "↑ 12% YoY", True)
    _kpi(c[1], f"{completed:,}",    "Completed Trips",    f"{(trips['status']=='Cancelled').mean()*100:.1f}% cancel", True)
    _kpi(c[2], f"{avg_score:.1f}",  "Safety Score /100",  "Target ≥ 70", avg_score>=70)
    _kpi(c[3], f"{fleet_act}",      "Active Vehicles",    f"{accidents} accidents", accidents==0)

    st.markdown("<br>", unsafe_allow_html=True)
    c2 = st.columns(4)
    _kpi(c2[0], _fmt(collected),                   "Collected",         f"{collected/total_rev*100:.1f}%", True)
    _kpi(c2[1], _fmt(fuel["fuel_cost_pkr"].sum()), "Total Fuel Spend",  "")
    _kpi(c2[2], _fmt(maint["total_cost_pkr"].sum()),"Maintenance Spend","")
    _kpi(c2[3], str(risky_drv),                    "High-Risk Drivers", "poor/dangerous", risky_drv==0)

    st.markdown("<hr style='border-color:{};margin:14px 0;'>".format(cb), unsafe_allow_html=True)

    # Revenue trend
    _sec("📈 Revenue Trend")
    inv["_m"] = inv["invoice_date"].dt.to_period("M")
    mr = inv.groupby("_m").agg(b=("total_amount_pkr","sum"),c=("paid_amount_pkr","sum")).reset_index()
    mr["_m"] = mr["_m"].astype(str)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=mr["_m"],y=mr["b"]/1e6,name="Billed",
        fill="tozeroy",fillcolor=_hex_to_rgba(a,0.12),line=dict(color=a,width=2.5),mode="lines+markers",marker=dict(size=4)))
    fig.add_trace(go.Scatter(x=mr["_m"],y=mr["c"]/1e6,name="Collected",
        fill="tozeroy",fillcolor=_hex_to_rgba(succ,0.10),line=dict(color=succ,width=2),mode="lines+markers",marker=dict(size=4)))
    dark_layout(fig,"Monthly Revenue (PKR M)",xangle=-45)
    st.plotly_chart(fig, use_container_width=True)

    # Quick alerts
    _sec("⚠️ Active Alerts")
    import pandas as _pd
    TODAY = _pd.Timestamp("2026-07-01")
    exp = veh[veh["insurance_expiry"]<TODAY]
    exp_lic = dfs["drivers"][dfs["drivers"]["license_expiry"]<TODAY]
    outs = inv[inv["outstanding_pkr"]>0]["outstanding_pkr"].sum()
    if len(exp):    _alert(f"🔴 {len(exp)} vehicles with expired insurance","critical")
    if risky_drv:   _alert(f"🔴 {risky_drv} high-risk drivers on fleet","critical")
    if len(exp_lic):_alert(f"🟠 {len(exp_lic)} driver licences expired","warning")
    if outs>0:      _alert(f"🟡 {_fmt(outs)} outstanding receivables","warning")
    if not (len(exp) or risky_drv or len(exp_lic) or outs):
        _alert("✅ No critical alerts","success")

    # Quick links
    _sec("🚀 Quick Actions")
    qc = st.columns(4)
    for i,(lbl,pg) in enumerate([("💰 Finance","finance"),("🚗 Operations","operations"),
                                   ("🔧 Fleet","fleet"),("🚦 Drivers","drivers")]):
        if qc[i].button(lbl, key=f"qa_{pg}", use_container_width=True):
            st.session_state.current_page = pg; st.rerun()


# ── MANAGER HOME ───────────────────────────────────────────────────────
def _home_manager(dfs):
    import plotly.graph_objects as go
    from page_modules._shared import dark_layout
    fleet_id = user.get("fleet","all")

    st.markdown(f"""
<div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
  <span style="font-size:2rem;">🏢</span>
  <div>
    <div style="font-size:1.5rem;font-weight:800;color:{a};">
      Fleet Manager Dashboard</div>
    <div style="font-size:.8rem;color:{muted};">
      {user['name']} · {f"Fleet {fleet_id}" if fleet_id!="all" else "All Fleets"}</div>
  </div>
</div><hr style="border-color:{cb};margin:6px 0 14px;">""", unsafe_allow_html=True)

    inv   = dfs["invoices"]
    trips = dfs["trips"]
    veh   = dfs["vehicles"]
    maint = dfs["maintenance"]
    TODAY = __import__("pandas").Timestamp("2026-07-01")

    # Filter to own fleet
    if fleet_id != "all":
        inv   = inv[inv["fleet_id"]==fleet_id]
        trips = trips[trips["fleet_id"]==fleet_id]
        veh   = veh[veh["fleet_id"]==fleet_id]
        maint = maint[maint["fleet_id"]==fleet_id]

    sc = veh["status"].value_counts()
    c = st.columns(4)
    _kpi(c[0], str(len(veh)),              "My Fleet Size",      f"{sc.get('Available',0)} available")
    _kpi(c[1], str(sc.get("On Trip",0)),   "On Trip Now",        "")
    _kpi(c[2], _fmt(inv["total_amount_pkr"].sum()), "Total Revenue", "")
    _kpi(c[3], str((maint["status"]=="Scheduled").sum()), "Pending Services","", (maint["status"]=="Scheduled").sum()==0)

    st.markdown("<br>", unsafe_allow_html=True)
    c2 = st.columns(4)
    _kpi(c2[0], str((trips["status"]=="Completed").sum()), "Completed Trips","")
    _kpi(c2[1], str((trips["status"]=="Cancelled").sum()), "Cancellations",  "", False)
    _kpi(c2[2], _fmt(inv["outstanding_pkr"].sum()),        "Outstanding",    "", inv["outstanding_pkr"].sum()==0)
    exp = veh[veh["insurance_expiry"]<TODAY]
    _kpi(c2[3], str(len(exp)), "Expired Insurance", "", len(exp)==0)

    st.markdown("<hr style='border-color:{};margin:14px 0;'>".format(cb), unsafe_allow_html=True)
    _sec("⚠️ My Fleet Alerts")
    if len(exp):     _alert(f"🔴 {len(exp)} vehicles with expired insurance","critical")
    sched = (maint["status"]=="Scheduled").sum()
    if sched:        _alert(f"🟠 {sched} maintenance jobs scheduled","warning")
    outs_inv = inv[inv["outstanding_pkr"]>0]
    if len(outs_inv):_alert(f"🟡 {_fmt(outs_inv['outstanding_pkr'].sum())} overdue","warning")
    if not (len(exp) or sched or len(outs_inv)):
        _alert("✅ Fleet operating normally","success")

    _sec("🚀 Quick Actions")
    qc = st.columns(3)
    for i,(lbl,pg) in enumerate([("💰 Finance","finance"),("🔧 Fleet Health","fleet"),("⚠️ Alerts","alerts")]):
        if qc[i].button(lbl, key=f"qam_{pg}", use_container_width=True):
            st.session_state.current_page = pg; st.rerun()


# ── ANALYST HOME ───────────────────────────────────────────────────────
def _home_analyst(dfs):
    import plotly.graph_objects as go
    from page_modules._shared import dark_layout

    st.markdown(f"""
<div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
  <span style="font-size:2rem;">📊</span>
  <div>
    <div style="font-size:1.5rem;font-weight:800;color:{a};">
      Analytics Workspace</div>
    <div style="font-size:.8rem;color:{muted};">
      {user['name']} · Data Analyst · Full analytics access</div>
  </div>
</div><hr style="border-color:{cb};margin:6px 0 14px;">""", unsafe_allow_html=True)

    inv   = dfs["invoices"]; trips = dfs["trips"]
    tel   = dfs["telematics"]; fuel = dfs["fuel_logs"]

    c = st.columns(4)
    _kpi(c[0], _fmt(inv["total_amount_pkr"].sum()), "Total Revenue",   "")
    _kpi(c[1], f"{len(trips):,}",                   "Total Bookings",  "")
    _kpi(c[2], f"{tel['safety_score'].mean():.1f}","Avg Safety Score","")
    _kpi(c[3], f"{fuel['fuel_efficiency_kmpl'].mean():.1f} km/l","Avg Fuel Eff","")

    st.markdown("<hr style='border-color:{};margin:14px 0;'>".format(cb), unsafe_allow_html=True)

    # Revenue trend
    _sec("📈 Revenue Trend")
    inv["_m"] = inv["invoice_date"].dt.to_period("M")
    mr = inv.groupby("_m")["total_amount_pkr"].sum().reset_index()
    mr["_m"] = mr["_m"].astype(str)
    fig = go.Figure(go.Scatter(x=mr["_m"],y=mr["total_amount_pkr"]/1e6,
        fill="tozeroy",fillcolor=_hex_to_rgba(a,0.10),line=dict(color=a,width=2.5),
        mode="lines+markers",marker=dict(size=4)))
    dark_layout(fig,"Monthly Revenue (PKR M)",xangle=-45)
    st.plotly_chart(fig, use_container_width=True)

    _sec("🚀 Quick Actions")
    qc = st.columns(4)
    for i,(lbl,pg) in enumerate([("📈 Forecasting","forecast"),("🔍 SQL Analytics","sql"),
                                   ("📖 Stories","stories"),("🤖 AI Chat","chat")]):
        if qc[i].button(lbl, key=f"qaa_{pg}", use_container_width=True):
            st.session_state.current_page = pg; st.rerun()


# ── VIEWER HOME ────────────────────────────────────────────────────────
def _home_viewer(dfs):
    st.markdown(f"""
<div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
  <span style="font-size:2rem;">👁️</span>
  <div>
    <div style="font-size:1.5rem;font-weight:800;color:{a};">Read-Only Dashboard</div>
    <div style="font-size:.8rem;color:{muted};">{user['name']} · View Only</div>
  </div>
</div><hr style="border-color:{cb};margin:6px 0 14px;">""", unsafe_allow_html=True)

    inv = dfs["invoices"]; trips = dfs["trips"]; veh = dfs["vehicles"]
    c = st.columns(3)
    _kpi(c[0], _fmt(inv["total_amount_pkr"].sum()), "Total Revenue","")
    _kpi(c[1], f"{(trips['status']=='Completed').sum():,}", "Completed Trips","")
    _kpi(c[2], str((veh["status"]=="Available").sum()),    "Available Vehicles","")

    _sec("🚀 Pages Available to You")
    qc = st.columns(2)
    for i,(lbl,pg) in enumerate([("📊 Executive Dashboard","executive"),("🚗 Operations","operations")]):
        if qc[i].button(lbl, key=f"qav_{pg}", use_container_width=True):
            st.session_state.current_page = pg; st.rerun()


# ── DRIVER HOME ────────────────────────────────────────────────────────
def _home_driver(dfs, u):
    st.markdown(f"""
<div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
  <span style="font-size:2rem;">🚗</span>
  <div>
    <div style="font-size:1.5rem;font-weight:800;color:{a};">Driver Portal</div>
    <div style="font-size:.8rem;color:{muted};">{u['name']} · Driver</div>
  </div>
</div><hr style="border-color:{cb};margin:6px 0 14px;">""", unsafe_allow_html=True)

    tel = dfs["telematics"]
    c = st.columns(3)
    _kpi(c[0], f"{tel['safety_score'].mean():.1f}/100","Fleet Avg Safety Score","")
    _kpi(c[1], str(int(tel["accident_occurred"].sum())), "Accident Events","")
    _kpi(c[2], str(int(tel["complaint_filed"].sum())),   "Complaints Filed","")

    if st.button("🚦 View Driver Safety Details", use_container_width=True, key="drv_go"):
        st.session_state.current_page = "drivers"; st.rerun()


# ══════════════════════════════════════════════════════════════════════
#  PAGE ROUTER
# ══════════════════════════════════════════════════════════════════════
page = st.session_state.current_page

# Security check — can't access pages not in your role
if page not in ("home",) and not _allowed(page):
    st.session_state.current_page = "home"
    st.warning("⚠️ You don't have access to that page.")
    st.rerun()

if page == "home":
    render_home()
else:
    filepath = PAGE_FILES.get(page)
    if filepath:
        try:
            code = Path(filepath).read_text(encoding="utf-8")
            exec(compile(code, filepath, "exec"), {"__name__": "__main__"})
        except Exception as e:
            st.error(f"Error loading page `{page}`: {e}")
            import traceback; st.code(traceback.format_exc())
    else:
        st.error(f"Page `{page}` not found.")

# ── Footer ─────────────────────────────────────────────────────────────
st.markdown(FOOTER_HTML, unsafe_allow_html=True)
