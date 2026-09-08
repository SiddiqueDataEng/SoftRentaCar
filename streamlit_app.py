"""
Soft Rent a Car — Main Entry Point
Uses st.navigation() for Streamlit 1.45+ multi-page routing.
Run with: streamlit run streamlit_app.py
"""

import streamlit as st

st.set_page_config(
    page_title="Soft Rent a Car",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Navigation (Streamlit 1.45+ API) ──────────────────────────────────
pg = st.navigation(
    {
        "Overview": [
            st.Page("page_modules/p1_executive.py",  title="Executive Dashboard",    icon="🏠"),
        ],
        "Finance": [
            st.Page("page_modules/p2_finance.py",    title="Finance & Revenue",      icon="💰"),
        ],
        "Operations": [
            st.Page("page_modules/p3_operations.py", title="Operations & Trips",     icon="🚗"),
            st.Page("page_modules/p7_map.py",        title="Demand Map",             icon="🗺️"),
        ],
        "People & Safety": [
            st.Page("page_modules/p4_drivers.py",    title="Driver Safety & AI",     icon="🚦"),
        ],
        "Fleet": [
            st.Page("page_modules/p5_fleet.py",      title="Fleet Health",           icon="🔧"),
        ],
        "Intelligence": [
            st.Page("page_modules/p6_forecast.py",   title="Forecasting & Trends",   icon="📈"),
            st.Page("page_modules/p8_stories.py",    title="Data Storytelling",      icon="📖"),
        ],
        "Tools": [
            st.Page("page_modules/p9_chat.py",       title="AI Chat Assistant",      icon="🤖"),
            st.Page("page_modules/p10_alerts.py",    title="Alerts & Watchlist",     icon="⚠️"),
        ],
    },
    position="sidebar",
)

# ── Sidebar branding (shown on every page) ────────────────────────────
with st.sidebar:
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
section[data-testid="stSidebar"] { background: linear-gradient(160deg,#1D3557 0%,#0f1a2b 100%); }
section[data-testid="stSidebar"] * { font-family:'Inter',sans-serif !important; }
</style>
<div style="padding:14px 0 18px 0; display:flex; align-items:center; gap:10px;">
  <span style="font-size:2rem;">🚗</span>
  <div>
    <div style="font-size:1.25rem;font-weight:800;color:#E63946;line-height:1;">Soft Rent a Car</div>
    <div style="font-size:0.65rem;color:#5a7a96;letter-spacing:.12em;text-transform:uppercase;">Fleet Intelligence</div>
  </div>
</div>
""", unsafe_allow_html=True)

pg.run()
