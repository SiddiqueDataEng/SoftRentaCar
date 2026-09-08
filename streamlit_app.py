"""
Soft Rent a Car — Main Streamlit Application Entry Point
Run with:  streamlit run streamlit_app.py
"""

import streamlit as st

st.set_page_config(
    page_title="Soft Rent a Car",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded",
)

from app.style import inject_css
inject_css()

from app.data_loader import load_all
import importlib

# ── Load data (globally cached) ────────────────────────────────────────
with st.spinner("Loading fleet data …"):
    dfs = load_all()

# ── Sidebar navigation ─────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="logo-banner">
        <div class="logo-icon">🚗</div>
        <div>
            <div class="logo-text-main">Soft Rent a Car</div>
            <div class="logo-text-sub">Fleet Intelligence Platform</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    pages = {
        "🏠 Executive Dashboard":     "pages.p1_executive",
        "💰 Finance & Revenue":        "pages.p2_finance",
        "🚗 Operations & Trips":       "pages.p3_operations",
        "🚦 Driver Safety & AI":       "pages.p4_drivers",
        "🔧 Fleet Health":             "pages.p5_fleet",
        "📈 Forecasting & Trends":     "pages.p6_forecast",
        "🗺️  Demand Map":              "pages.p7_map",
        "📖 Data Storytelling":        "pages.p8_stories",
        "🤖 AI Chat Assistant":        "pages.p9_chat",
        "⚠️  Alerts & Watchlist":      "pages.p10_alerts",
    }

    selected = st.radio(
        "Navigation",
        list(pages.keys()),
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown(
        '<div style="font-size:0.7rem;color:#4a6a84;text-align:center;">'
        '© 2026 Soft Rent a Car<br>Powered by AI & Analytics'
        '</div>',
        unsafe_allow_html=True,
    )

# ── Page router ────────────────────────────────────────────────────────
module_name = pages[selected]
try:
    module = importlib.import_module(module_name)
    module.render(dfs)
except Exception as e:
    st.error(f"Error loading page: {e}")
    import traceback
    st.code(traceback.format_exc())
