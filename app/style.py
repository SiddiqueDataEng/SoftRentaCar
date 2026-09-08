"""
Global CSS + theme constants for Soft Rent a Car.
"""

BRAND_COLOR    = "#E63946"   # signature red
BRAND_DARK     = "#1D3557"   # navy blue
BRAND_ACCENT   = "#457B9D"   # steel blue
BRAND_LIGHT    = "#F1FAEE"   # off-white
BRAND_GOLD     = "#F4A261"   # warm amber
SUCCESS_COLOR  = "#2A9D8F"
WARNING_COLOR  = "#E9C46A"
DANGER_COLOR   = "#E76F51"
_TEXT          = "#c8dff0"   # chart text colour (exported for page imports)

PLOTLY_TEMPLATE = "plotly_white"
PLOTLY_COLORS   = [
    BRAND_COLOR, BRAND_DARK, BRAND_ACCENT,
    BRAND_GOLD, SUCCESS_COLOR, WARNING_COLOR,
    "#6A4C93", "#1982C4", "#8AC926",
]

GLOBAL_CSS = """
<style>
/* ── Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
}

/* ── Hide default Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }

/* ── Page background ── */
.stApp {
    background: #0f1117;
    color: #e8eaf0;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(160deg, #1D3557 0%, #14253a 100%);
    border-right: 1px solid #2d4a6b;
}
[data-testid="stSidebar"] * { color: #d0dff0 !important; }
[data-testid="stSidebar"] .stRadio label { color: #aec6e0 !important; }

/* ── KPI cards ── */
.kpi-card {
    background: linear-gradient(135deg, #1e2a3a 0%, #162030 100%);
    border: 1px solid #2d4a6b;
    border-radius: 12px;
    padding: 18px 20px;
    text-align: center;
    transition: transform 0.2s, box-shadow 0.2s;
}
.kpi-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 24px rgba(230,57,70,0.18);
}
.kpi-value {
    font-size: 2rem;
    font-weight: 700;
    color: #E63946;
    line-height: 1.1;
}
.kpi-label {
    font-size: 0.78rem;
    color: #8eaac4;
    margin-top: 4px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
.kpi-delta {
    font-size: 0.82rem;
    margin-top: 6px;
    font-weight: 500;
}
.delta-up   { color: #2A9D8F; }
.delta-down { color: #E76F51; }

/* ── Section headers ── */
.section-header {
    font-size: 1.15rem;
    font-weight: 600;
    color: #c8dff0;
    border-left: 3px solid #E63946;
    padding-left: 10px;
    margin: 20px 0 12px 0;
}

/* ── Alert cards ── */
.alert-critical {
    background: rgba(231,111,81,0.15);
    border: 1px solid #E76F51;
    border-radius: 8px;
    padding: 10px 14px;
    margin: 6px 0;
    color: #f0a090;
}
.alert-warning {
    background: rgba(233,196,106,0.12);
    border: 1px solid #E9C46A;
    border-radius: 8px;
    padding: 10px 14px;
    margin: 6px 0;
    color: #f0d88a;
}
.alert-info {
    background: rgba(69,123,157,0.15);
    border: 1px solid #457B9D;
    border-radius: 8px;
    padding: 10px 14px;
    margin: 6px 0;
    color: #90bdd4;
}

/* ── Chat bubbles ── */
.chat-user {
    background: linear-gradient(135deg, #E63946, #c0272e);
    color: #fff;
    padding: 12px 16px;
    border-radius: 18px 18px 4px 18px;
    margin: 8px 0 8px auto;
    max-width: 78%;
    font-size: 0.93rem;
    width: fit-content;
    margin-left: auto;
}
.chat-ai {
    background: linear-gradient(135deg, #1e2a3a, #253344);
    color: #d8eaf6;
    padding: 12px 16px;
    border-radius: 18px 18px 18px 4px;
    margin: 8px auto 8px 0;
    max-width: 85%;
    font-size: 0.93rem;
    border: 1px solid #2d4a6b;
}
.chat-timestamp {
    font-size: 0.68rem;
    color: #5a7a96;
    margin-top: 3px;
}

/* ── Story card ── */
.story-card {
    background: linear-gradient(135deg, #1a2840, #1e2f44);
    border-radius: 14px;
    border: 1px solid #2a3f58;
    padding: 20px 24px;
    margin: 10px 0;
}
.story-number {
    font-size: 2.8rem;
    font-weight: 800;
    color: #E63946;
    line-height: 1;
}
.story-title {
    font-size: 1.05rem;
    font-weight: 600;
    color: #b8d4e8;
    margin-top: 4px;
}
.story-body {
    font-size: 0.88rem;
    color: #7a9ab4;
    margin-top: 8px;
    line-height: 1.55;
}

/* ── Logo banner ── */
.logo-banner {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 14px 0 20px 0;
}
.logo-icon {
    font-size: 2.4rem;
}
.logo-text-main {
    font-size: 1.5rem;
    font-weight: 800;
    color: #E63946;
    line-height: 1;
}
.logo-text-sub {
    font-size: 0.72rem;
    color: #6a8faa;
    letter-spacing: 0.14em;
    text-transform: uppercase;
}

/* ── Tables ── */
.dataframe thead th {
    background-color: #1D3557 !important;
    color: #c8dff0 !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #0f1117; }
::-webkit-scrollbar-thumb { background: #2d4a6b; border-radius: 4px; }
</style>
"""


def inject_css():
    import streamlit as st
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


def kpi_card(value: str, label: str, delta: str = "", delta_positive: bool = True) -> str:
    delta_class = "delta-up" if delta_positive else "delta-down"
    delta_html  = f'<div class="kpi-delta {delta_class}">{delta}</div>' if delta else ""
    return f"""
    <div class="kpi-card">
      <div class="kpi-value">{value}</div>
      <div class="kpi-label">{label}</div>
      {delta_html}
    </div>
    """


def section_header(title: str) -> str:
    return f'<div class="section-header">{title}</div>'


def alert(msg: str, level: str = "info") -> str:
    return f'<div class="alert-{level}">{msg}</div>'
