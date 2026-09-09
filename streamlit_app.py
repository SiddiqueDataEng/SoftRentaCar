"""Soft Rent a Car — Main App"""
import streamlit as st
import os
from pathlib import Path

st.set_page_config(
    page_title="Soft Rent a Car",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded",
)

from app.auth   import verify, is_logged_in, current_user, current_role, \
                       do_logout, ROLES, get_user_meta
from app.themes import THEMES, DEFAULT_THEME, get_theme_css, FOOTER_HTML

# ── Session defaults ───────────────────────────────────────────────────
if "selected_theme" not in st.session_state: st.session_state.selected_theme = DEFAULT_THEME
if "current_page"   not in st.session_state: st.session_state.current_page   = "executive"
if "api_keys"       not in st.session_state: st.session_state.api_keys       = {}
if "login_error"    not in st.session_state: st.session_state.login_error    = ""

for k, v in st.session_state.api_keys.items():
    if v: os.environ[k] = v

theme = THEMES[st.session_state.selected_theme]
st.markdown(get_theme_css(theme), unsafe_allow_html=True)
a=theme["accent"]; a2=theme["accent2"]; txt=theme["text"]
muted=theme["text_muted"]; cbg=theme["card_bg"]
cb=theme["card_bdr"]; bg=theme["app_bg"]

# ══════════════════════════════════════════════════════════════════════
#  LOGIN
# ══════════════════════════════════════════════════════════════════════
if not is_logged_in():
    st.markdown("""
<style>
[data-testid="stSidebar"],[data-testid="stSidebarNav"],
button[data-testid="stBaseButton-headerNoPadding"]{display:none!important;}
</style>""", unsafe_allow_html=True)

    st.markdown(f"""
<style>
.stApp{{background:radial-gradient(ellipse at 25% 45%,{a}22 0%,{bg} 60%)!important;}}
.lcard{{max-width:420px;margin:40px auto 0;background:{cbg};border:1px solid {cb};
        border-radius:22px;padding:36px 32px 28px;
        box-shadow:0 24px 80px rgba(0,0,0,.65);}}
.ltitle{{font-size:1.6rem;font-weight:800;color:{a};text-align:center;}}
.lsub{{font-size:.76rem;color:{muted};text-align:center;margin-bottom:18px;}}
.rpill{{display:inline-flex;align-items:center;gap:4px;padding:3px 9px;
        border-radius:20px;font-size:.63rem;font-weight:600;border:1px solid;margin:2px;}}
.lhint{{font-size:.68rem;color:{muted};text-align:center;margin-top:10px;line-height:1.75;
        background:{bg};border:1px solid {cb};border-radius:8px;padding:8px 12px;}}
code{{background:{cb}33;padding:1px 5px;border-radius:4px;font-size:.75em;color:{txt};}}
.lftr{{text-align:center;margin-top:14px;font-size:.65rem;color:{muted};line-height:1.9;}}
.lftr a{{color:{a2};text-decoration:none;}}
</style>""", unsafe_allow_html=True)

    _, lc, _ = st.columns([1, 1.55, 1])
    with lc:
        st.markdown(f"""
<div style="text-align:center;margin-bottom:14px;">
  <div style="font-size:3rem;margin-bottom:6px;">🚗</div>
  <div class="ltitle">Soft Rent a Car</div>
  <div class="lsub">Fleet Intelligence Platform</div>
</div>""", unsafe_allow_html=True)

        pills = "".join(
            f'<span class="rpill" style="color:{rv["color"]};border-color:{rv["color"]}55;'
            f'background:{rv["color"]}11;">{rv["icon"]} {rv["label"]}</span>'
            for rv in ROLES.values()
        )
        st.markdown(f'<div style="text-align:center;margin-bottom:16px;">{pills}</div>',
                    unsafe_allow_html=True)

        # ── Login form ────────────────────────────────────────────────
        with st.form("login_form", clear_on_submit=False):
            uname = st.text_input("Username", placeholder="e.g. admin", key="l_u")
            passw = st.text_input("Password", type="password",
                                  placeholder="Enter password", key="l_p")
            submitted = st.form_submit_button(
                "🔐  Sign In", use_container_width=True, type="primary"
            )

        if submitted:
            if not uname.strip() or not passw.strip():
                st.session_state.login_error = "Please enter username and password."
            else:
                u = verify(uname.strip(), passw.strip())
                if u:
                    st.session_state._auth_ok   = True
                    st.session_state._auth_user = uname.strip().lower()
                    st.session_state._auth_name = u["name"]
                    st.session_state.login_error = ""
                    st.rerun()
                else:
                    st.session_state.login_error = "❌ Incorrect username or password."

        if st.session_state.login_error:
            st.error(st.session_state.login_error)

        st.markdown(f"""
<div class="lhint">
  <strong style="color:{txt};">Demo accounts</strong><br>
  <code>admin</code> / Admin@2026 &nbsp;·&nbsp;
  <code>manager1</code> / Manager@2026<br>
  <code>analyst1</code> / Analyst@2026 &nbsp;·&nbsp;
  <code>viewer1</code> / Viewer@2026
</div>
<div class="lftr">
  Developed by <strong style="color:{txt};">Muhammad Siddique</strong><br>
  <a href="tel:+923229948042">+92 322 9948042</a> ·
  <a href="mailto:siddique.dea@gmail.com">siddique.dea@gmail.com</a><br>
  <a href="https://www.datawithms.top" target="_blank">datawithms.top</a> ·
  <a href="https://www.linkedin.com/in/siddique-datalover" target="_blank">LinkedIn</a>
</div>""", unsafe_allow_html=True)

    st.stop()


# ══════════════════════════════════════════════════════════════════════
#  AUTHENTICATED
# ══════════════════════════════════════════════════════════════════════
user = current_user()
role = current_role()
rm   = ROLES.get(role, ROLES["viewer"])

def _ok(k):
    if role == "admin": return True
    p = rm.get("pages", [])
    return p == "all" or k in p

NAV_GROUPS = [
    ("Overview",        [("executive","🏠","Executive Dashboard")]),
    ("Finance",         [("finance","💰","Finance & Revenue")]),
    ("Operations",      [("operations","🚗","Operations & Trips"),
                         ("map","🗺️","Demand Map")]),
    ("People & Safety", [("drivers","🚦","Driver Safety & AI")]),
    ("Fleet",           [("fleet","🔧","Fleet Health")]),
    ("Intelligence",    [("forecast","📈","Forecasting & Trends"),
                         ("stories","📖","Data Storytelling")]),
    ("Tools",           [("chat","🤖","AI Chat Assistant"),
                         ("alerts","⚠️","Alerts & Watchlist"),
                         ("sql","🔍","SQL Analytics"),
                         ("settings","⚙️","Settings & API Keys")]),
]

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
    "settings":  "page_modules/p12_settings.py",
}

# ── Sidebar CSS ────────────────────────────────────────────────────────
st.markdown(f"""
<style>
[data-testid="stSidebarNav"]{{display:none!important;}}
button[data-testid="stBaseButton-headerNoPadding"]{{display:none!important;}}
[data-testid="stSidebar"]{{
    background:{theme['sidebar_bg']}!important;
    border-right:1px solid {cb}!important;
    width:258px!important;min-width:258px!important;
}}
[data-testid="stSidebar"]>div:first-child{{
    padding:0 0 40px 0!important;
    overflow-y:auto!important;height:100vh!important;
}}
.nav-grp{{font-size:.58rem;font-weight:700;color:{muted};text-transform:uppercase;
          letter-spacing:.1em;padding:10px 14px 2px;display:block;}}
div[data-testid="stSidebar"] .stButton button{{
    width:100%!important;text-align:left!important;background:transparent!important;
    border:none!important;border-radius:7px!important;padding:7px 12px!important;
    font-size:.84rem!important;font-weight:500!important;color:{txt}!important;
    transition:background .14s,color .14s!important;margin:1px 0!important;
    justify-content:flex-start!important;
}}
div[data-testid="stSidebar"] .stButton button:hover{{
    background:{a}22!important;color:{txt}!important;
}}
div[data-testid="stSidebar"] .nav-active .stButton button{{
    background:{a}28!important;color:{a}!important;font-weight:700!important;
    border-left:3px solid {a}!important;padding-left:9px!important;
}}
div[data-testid="stSidebar"] div[data-testid="stRadio"]{{padding:0 14px!important;}}
div[data-testid="stSidebar"] div[data-testid="stRadio"] label{{
    font-size:.72rem!important;color:{txt}!important;
}}
.logout-wrap .stButton button{{
    background:{a}18!important;color:{a}!important;
    border:1px solid {a}44!important;border-radius:7px!important;
    font-weight:600!important;margin:0 10px!important;
    width:calc(100% - 20px)!important;
}}
.main .block-container{{padding-top:1.2rem!important;padding-bottom:60px!important;}}
@media(max-width:768px){{
    [data-testid="stSidebar"]{{
        position:fixed!important;z-index:9998!important;
        width:85vw!important;max-width:300px!important;
        height:100vh!important;top:0!important;left:0!important;
        box-shadow:4px 0 24px rgba(0,0,0,.55)!important;
        transition:transform .25s ease!important;
    }}
    [data-testid="stSidebar"][aria-expanded="false"]{{transform:translateX(-100%)!important;}}
    .main .block-container{{padding:.8rem .6rem 60px!important;}}
}}
</style>
""", unsafe_allow_html=True)

# ── Sidebar content ────────────────────────────────────────────────────
with st.sidebar:

    # Logo
    st.markdown(f"""
<div style="padding:16px 14px 12px;border-bottom:1px solid {cb};margin-bottom:4px;">
  <div style="display:flex;align-items:center;gap:10px;">
    <div style="background:linear-gradient(135deg,{a},{a}aa);border-radius:10px;
                width:38px;height:38px;display:flex;align-items:center;
                justify-content:center;font-size:1.3rem;flex-shrink:0;">🚗</div>
    <div>
      <div style="font-size:1rem;font-weight:800;color:{a};line-height:1.2;">
        Soft Rent a Car</div>
      <div style="font-size:.55rem;color:{muted};letter-spacing:.1em;
                  text-transform:uppercase;">Fleet Intelligence</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    # User badge
    st.markdown(f"""
<div style="margin:8px 10px 4px;padding:9px 12px;background:{cbg};
            border:1px solid {cb};border-radius:10px;
            display:flex;align-items:center;gap:8px;">
  <div style="font-size:1.4rem;line-height:1;flex-shrink:0;">{rm['icon']}</div>
  <div style="min-width:0;">
    <div style="font-size:.81rem;font-weight:700;color:{txt};
                white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
      {user.get('name','')}</div>
    <div style="font-size:.59rem;color:{rm['color']};font-weight:600;
                text-transform:uppercase;letter-spacing:.05em;">{rm['label']}</div>
  </div>
</div>
""", unsafe_allow_html=True)

    # Nav
    cur_page = st.session_state.current_page
    for group_name, items in NAV_GROUPS:
        visible = [(k, ic, lb) for k, ic, lb in items if _ok(k)]
        if not visible: continue
        st.markdown(f'<span class="nav-grp">{group_name}</span>', unsafe_allow_html=True)
        for key, icon, label in visible:
            is_active = (key == cur_page)
            st.markdown(f'<div class="{"nav-active" if is_active else "nav-item"}">',
                        unsafe_allow_html=True)
            if st.button(f"{icon}  {label}", key=f"nb_{key}"):
                st.session_state.current_page = key
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(f"<hr style='border-color:{cb};margin:10px 10px 4px;'>",
                unsafe_allow_html=True)

    # Theme
    st.markdown(f"""
<div style="padding:0 14px 3px;">
  <div style="font-size:.58rem;font-weight:700;color:{muted};
              text-transform:uppercase;letter-spacing:.1em;">🎨 Theme</div>
</div>
""", unsafe_allow_html=True)
    tkeys = list(THEMES.keys())
    tlbls = ["🌑 Navy","🌿 Green","🔥 Red","💜 Purple","🌊 Blue"]
    tidx  = tkeys.index(st.session_state.selected_theme)
    pick  = st.radio("_th", tlbls, index=tidx, key="th_radio",
                     label_visibility="collapsed", horizontal=True)
    pfull = tkeys[tlbls.index(pick)]
    if pfull != st.session_state.selected_theme:
        st.session_state.selected_theme = pfull
        st.rerun()

    st.markdown(f"<hr style='border-color:{cb};margin:6px 10px 8px;'>",
                unsafe_allow_html=True)

    # Logout
    st.markdown('<div class="logout-wrap">', unsafe_allow_html=True)
    if st.button("🚪  Sign Out", key="logout_btn", use_container_width=True):
        do_logout()
    st.markdown("</div>", unsafe_allow_html=True)

    # Dev card
    st.markdown(f"""
<div style="margin:8px 10px 16px;padding:10px 12px;background:{cbg};
            border:1px solid {cb};border-radius:10px;">
  <div style="font-size:.61rem;font-weight:700;color:{a};margin-bottom:3px;">
    👨‍💻 Developer</div>
  <div style="font-size:.66rem;color:{txt};font-weight:600;margin-bottom:2px;">
    Muhammad Siddique</div>
  <div style="font-size:.59rem;color:{muted};line-height:1.8;">
    <a href="tel:+923229948042" style="color:{a2};text-decoration:none;">
      📞 +92 322 9948042</a><br>
    <a href="mailto:siddique.dea@gmail.com" style="color:{a2};text-decoration:none;">
      ✉️ siddique.dea@gmail.com</a><br>
    <a href="https://www.datawithms.top" target="_blank" style="color:{a2};text-decoration:none;">
      🌐 datawithms.top</a> ·
    <a href="https://www.linkedin.com/in/siddique-datalover" target="_blank"
       style="color:{a2};text-decoration:none;">💼 LinkedIn</a>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Page routing ───────────────────────────────────────────────────────
page = st.session_state.current_page
if not _ok(page):
    st.session_state.current_page = "executive"
    page = "executive"

filepath = PAGE_FILES.get(page)
if filepath and Path(filepath).exists():
    try:
        exec(compile(Path(filepath).read_text(encoding="utf-8"), filepath, "exec"),
             {"__name__": "__main__"})
    except Exception as e:
        st.error(f"Error loading `{page}`: {e}")
        import traceback; st.code(traceback.format_exc())
else:
    st.error(f"Page `{page}` not found.")

st.markdown(FOOTER_HTML, unsafe_allow_html=True)
