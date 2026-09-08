"""
Soft Rent a Car — Main Entry Point
Uses st.navigation() (Streamlit 1.45+).
Run locally:  streamlit run streamlit_app.py
"""

import streamlit as st
from app.themes import THEMES, DEFAULT_THEME, get_theme_css, FOOTER_HTML

st.set_page_config(
    page_title="Soft Rent a Car",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Theme picker (persisted in session state) ──────────────────────────
if "selected_theme" not in st.session_state:
    st.session_state.selected_theme = DEFAULT_THEME

# Inject theme CSS globally (before page renders)
theme = THEMES[st.session_state.selected_theme]
st.markdown(get_theme_css(theme), unsafe_allow_html=True)

# ── Navigation ─────────────────────────────────────────────────────────
pg = st.navigation(
    {
        "Overview": [
            st.Page("page_modules/p1_executive.py",  title="Executive Dashboard",  icon="🏠"),
        ],
        "Finance": [
            st.Page("page_modules/p2_finance.py",    title="Finance & Revenue",    icon="💰"),
        ],
        "Operations": [
            st.Page("page_modules/p3_operations.py", title="Operations & Trips",   icon="🚗"),
            st.Page("page_modules/p7_map.py",        title="Demand Map",           icon="🗺️"),
        ],
        "People & Safety": [
            st.Page("page_modules/p4_drivers.py",    title="Driver Safety & AI",   icon="🚦"),
        ],
        "Fleet": [
            st.Page("page_modules/p5_fleet.py",      title="Fleet Health",         icon="🔧"),
        ],
        "Intelligence": [
            st.Page("page_modules/p6_forecast.py",   title="Forecasting & Trends", icon="📈"),
            st.Page("page_modules/p8_stories.py",    title="Data Storytelling",    icon="📖"),
        ],
        "Tools": [
            st.Page("page_modules/p9_chat.py",       title="AI Chat Assistant",    icon="🤖"),
            st.Page("page_modules/p10_alerts.py",    title="Alerts & Watchlist",   icon="⚠️"),
            st.Page("page_modules/p11_sql.py",       title="SQL Analytics",        icon="🔍"),
        ],
    },
    position="sidebar",
)

# ── Sidebar: logo + theme picker ───────────────────────────────────────
with st.sidebar:
    # Logo
    st.markdown(f"""
<div style="padding:14px 0 10px 0;display:flex;align-items:center;gap:10px;">
  <span style="font-size:2rem;">🚗</span>
  <div>
    <div style="font-size:1.2rem;font-weight:800;color:{theme['accent']};line-height:1;">
      Soft Rent a Car
    </div>
    <div style="font-size:0.62rem;letter-spacing:.12em;text-transform:uppercase;
                color:{theme['text_muted']};">Fleet Intelligence</div>
  </div>
</div>
""", unsafe_allow_html=True)

    st.markdown("<hr style='margin:6px 0 10px 0;'>", unsafe_allow_html=True)

    # Theme selector
    st.markdown(
        f'<div style="font-size:.72rem;font-weight:700;color:{theme["text_muted"]};'
        f'text-transform:uppercase;letter-spacing:.06em;margin-bottom:4px;">🎨 Theme</div>',
        unsafe_allow_html=True,
    )
    chosen = st.selectbox(
        "theme",
        list(THEMES.keys()),
        index=list(THEMES.keys()).index(st.session_state.selected_theme),
        label_visibility="collapsed",
        key="theme_picker",
    )
    if chosen != st.session_state.selected_theme:
        st.session_state.selected_theme = chosen
        st.rerun()

    # Theme preview swatches
    t = THEMES[chosen]
    swatches = "".join(
        f'<div style="width:16px;height:16px;border-radius:4px;background:{c};'
        f'display:inline-block;margin-right:3px;border:1px solid rgba(255,255,255,.12);"></div>'
        for c in t["plotly_colors"][:6]
    )
    st.markdown(
        f'<div style="margin:4px 0 10px 0;display:flex;align-items:center;gap:2px;">'
        f'{swatches}</div>',
        unsafe_allow_html=True,
    )

    st.markdown("<hr style='margin:6px 0 10px 0;'>", unsafe_allow_html=True)

    # Developer info in sidebar footer
    st.markdown(f"""
<div style="position:absolute;bottom:14px;left:0;right:0;padding:0 14px;">
  <div style="font-size:.65rem;color:{theme['text_muted']};line-height:1.7;
              border-top:1px solid {theme['card_bdr']};padding-top:8px;">
    <div style="font-weight:700;color:{theme['accent']};font-size:.7rem;margin-bottom:3px;">
      👨‍💻 Developer
    </div>
    <div>Muhammad Siddique</div>
    <div><a href="tel:+923229948042"
            style="color:{theme['accent2']};text-decoration:none;">
      +92 322 9948042</a></div>
    <div><a href="mailto:siddique.dea@gmail.com"
            style="color:{theme['accent2']};text-decoration:none;">
      siddique.dea@gmail.com</a></div>
    <div><a href="https://www.datawithms.top" target="_blank"
            style="color:{theme['accent2']};text-decoration:none;">
      🌐 datawithms.top</a></div>
    <div><a href="https://www.linkedin.com/in/siddique-datalover" target="_blank"
            style="color:{theme['accent2']};text-decoration:none;">
      💼 LinkedIn</a></div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Run the selected page ───────────────────────────────────────────────
pg.run()

# ── Footer (injected after page renders) ──────────────────────────────
st.markdown(FOOTER_HTML, unsafe_allow_html=True)
