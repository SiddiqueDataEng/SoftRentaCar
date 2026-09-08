"""
Theme definitions for Soft Rent a Car.
Each theme defines CSS variables + Plotly colours.
"""

THEMES = {
    "🌑 Dark Navy (Default)": {
        "id": "dark_navy",
        "app_bg":       "#0f1117",
        "sidebar_bg":   "linear-gradient(160deg,#1D3557 0%,#0f1a2b 100%)",
        "sidebar_bdr":  "#2d4a6b",
        "card_bg":      "linear-gradient(135deg,#1e2a3a 0%,#162030 100%)",
        "card_bdr":     "#2d4a6b",
        "accent":       "#E63946",
        "accent2":      "#457B9D",
        "text":         "#c8dff0",
        "text_muted":   "#5a7a96",
        "success":      "#2A9D8F",
        "warning":      "#E9C46A",
        "danger":       "#E76F51",
        "scrollbar":    "#2d4a6b",
        "plotly_colors": ["#E63946","#1D3557","#457B9D","#2A9D8F","#E9C46A","#E76F51","#6A4C93","#1982C4"],
    },
    "🌿 Forest Green": {
        "id": "forest_green",
        "app_bg":       "#0a1210",
        "sidebar_bg":   "linear-gradient(160deg,#1a3028 0%,#0a1a14 100%)",
        "sidebar_bdr":  "#1e4a34",
        "card_bg":      "linear-gradient(135deg,#162820 0%,#0e1c18 100%)",
        "card_bdr":     "#1e4a34",
        "accent":       "#2ECC71",
        "accent2":      "#27AE60",
        "text":         "#c0e8d0",
        "text_muted":   "#4a7a5a",
        "success":      "#1abc9c",
        "warning":      "#f39c12",
        "danger":       "#e74c3c",
        "scrollbar":    "#1e4a34",
        "plotly_colors": ["#2ECC71","#27AE60","#1ABC9C","#16A085","#F39C12","#E74C3C","#8E44AD","#2980B9"],
    },
    "🔥 Crimson Red": {
        "id": "crimson_red",
        "app_bg":       "#120808",
        "sidebar_bg":   "linear-gradient(160deg,#3d0f0f 0%,#1a0606 100%)",
        "sidebar_bdr":  "#5a1a1a",
        "card_bg":      "linear-gradient(135deg,#2a1010 0%,#1c0a0a 100%)",
        "card_bdr":     "#5a1a1a",
        "accent":       "#FF4444",
        "accent2":      "#FF8C00",
        "text":         "#f0c8c8",
        "text_muted":   "#8a4a4a",
        "success":      "#FF8C00",
        "warning":      "#FFD700",
        "danger":       "#FF2222",
        "scrollbar":    "#5a1a1a",
        "plotly_colors": ["#FF4444","#FF8C00","#FFD700","#FF6B6B","#FFA07A","#DC143C","#B8860B","#CD5C5C"],
    },
    "💜 Royal Purple": {
        "id": "royal_purple",
        "app_bg":       "#0e0a18",
        "sidebar_bg":   "linear-gradient(160deg,#2d1b4e 0%,#0e0a18 100%)",
        "sidebar_bdr":  "#4a2d7a",
        "card_bg":      "linear-gradient(135deg,#1e1030 0%,#140c24 100%)",
        "card_bdr":     "#4a2d7a",
        "accent":       "#9B59B6",
        "accent2":      "#8E44AD",
        "text":         "#e0c8f0",
        "text_muted":   "#7a5a9a",
        "success":      "#1ABC9C",
        "warning":      "#F39C12",
        "danger":       "#E74C3C",
        "scrollbar":    "#4a2d7a",
        "plotly_colors": ["#9B59B6","#8E44AD","#6C3483","#1ABC9C","#F39C12","#E74C3C","#3498DB","#E91E63"],
    },
    "🌊 Ocean Blue": {
        "id": "ocean_blue",
        "app_bg":       "#080e18",
        "sidebar_bg":   "linear-gradient(160deg,#0a2a4a 0%,#050e1a 100%)",
        "sidebar_bdr":  "#0d3d6b",
        "card_bg":      "linear-gradient(135deg,#0e2038 0%,#081628 100%)",
        "card_bdr":     "#0d3d6b",
        "accent":       "#00BFFF",
        "accent2":      "#1E90FF",
        "text":         "#b0d8f0",
        "text_muted":   "#3a6a8a",
        "success":      "#00CED1",
        "warning":      "#FFD700",
        "danger":       "#FF6347",
        "scrollbar":    "#0d3d6b",
        "plotly_colors": ["#00BFFF","#1E90FF","#00CED1","#4169E1","#00FA9A","#FFD700","#FF6347","#DA70D6"],
    },
}

DEFAULT_THEME = "🌑 Dark Navy (Default)"


def get_theme_css(theme: dict) -> str:
    """Generate complete CSS for a given theme dict."""
    a   = theme["accent"]
    a2  = theme["accent2"]
    bg  = theme["app_bg"]
    sbg = theme["sidebar_bg"]
    sb  = theme["sidebar_bdr"]
    cbg = theme["card_bg"]
    cb  = theme["card_bdr"]
    txt = theme["text"]
    muted = theme["text_muted"]
    succ  = theme["success"]
    warn  = theme["warning"]
    dang  = theme["danger"]
    scr   = theme["scrollbar"]

    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
html, body, [class*="css"] {{ font-family:'Inter',sans-serif !important; }}
#MainMenu, header {{ visibility:hidden; }}

/* ── App background ── */
.stApp {{ background:{bg}; color:{txt}; }}

/* ── Sidebar ── */
[data-testid="stSidebar"] {{
    background:{sbg};
    border-right:1px solid {sb};
}}
[data-testid="stSidebar"] * {{ color:{txt} !important; }}

/* ── KPI cards ── */
.kpi-card {{
    background:{cbg}; border:1px solid {cb};
    border-radius:12px; padding:16px 18px; text-align:center;
    transition:transform .18s, box-shadow .18s;
}}
.kpi-card:hover {{
    transform:translateY(-2px);
    box-shadow:0 6px 24px {a}33;
}}
.kpi-val  {{ font-size:1.75rem; font-weight:800; color:{a}; line-height:1.1; }}
.kpi-lbl  {{ font-size:0.72rem; color:{muted}; margin-top:3px; text-transform:uppercase; letter-spacing:.06em; }}
.kpi-delta-up   {{ font-size:0.78rem; color:{succ}; margin-top:4px; }}
.kpi-delta-down {{ font-size:0.78rem; color:{dang}; margin-top:4px; }}
.kpi-delta-neu  {{ font-size:0.78rem; color:{muted}; margin-top:4px; }}

/* ── Section headers ── */
.sec-hdr {{
    font-size:1rem; font-weight:700; color:{txt};
    border-left:3px solid {a};
    padding-left:10px; margin:18px 0 10px 0;
}}

/* ── Alert boxes ── */
.alert-critical {{ background:{dang}26; border:1px solid {dang}; border-radius:8px; padding:10px 14px; margin:5px 0; color:{dang}; font-size:.85rem; }}
.alert-warning  {{ background:{warn}20; border:1px solid {warn}; border-radius:8px; padding:10px 14px; margin:5px 0; color:{warn}; font-size:.85rem; }}
.alert-info     {{ background:{a2}26;   border:1px solid {a2};   border-radius:8px; padding:10px 14px; margin:5px 0; color:{a2};   font-size:.85rem; }}
.alert-success  {{ background:{succ}26; border:1px solid {succ}; border-radius:8px; padding:10px 14px; margin:5px 0; color:{succ}; font-size:.85rem; }}

/* ── Story cards ── */
.story-card {{
    background:{cbg}; border-radius:14px;
    border:1px solid {cb}; padding:20px 24px; margin:10px 0;
}}
.story-num {{ font-size:2.8rem; font-weight:800; color:{a}; line-height:1; }}
.story-ttl {{ font-size:1rem; font-weight:700; color:{txt}; margin-top:4px; }}
.story-bdy {{ font-size:.86rem; color:{muted}; margin-top:8px; line-height:1.6; }}

/* ── HR dividers ── */
hr {{ border-color:{cb} !important; }}

/* ── Scrollbar ── */
::-webkit-scrollbar       {{ width:5px; height:5px; }}
::-webkit-scrollbar-track {{ background:{bg}; }}
::-webkit-scrollbar-thumb {{ background:{scr}; border-radius:4px; }}

/* ── Dataframes ── */
.stDataFrame thead th {{
    background:{cbg} !important; color:{txt} !important;
}}

/* ── Buttons ── */
.stButton > button {{
    border:1px solid {cb} !important;
    background:{cbg} !important;
    color:{txt} !important;
    border-radius:8px !important;
    transition:all .18s !important;
}}
.stButton > button:hover {{
    border-color:{a} !important;
    color:{a} !important;
    background:{bg} !important;
}}

/* ── Theme radio as clean list ── */
div[data-testid="stRadio"] label {{
    font-size:.76rem !important; padding:3px 0 !important;
    color:{txt} !important; cursor:pointer;
}}
div[data-testid="stRadio"] > div {{
    gap:2px !important;
}}

/* ── Footer ── */
.dev-footer {{
    position:fixed; bottom:0; left:0; right:0; z-index:9999;
    background:linear-gradient(90deg, {bg}ee, {cbg}ee);
    border-top:1px solid {cb};
    backdrop-filter:blur(12px);
    padding:7px 24px;
    display:flex; align-items:center; justify-content:space-between;
    flex-wrap:wrap; gap:8px;
}}
.dev-footer-left {{
    display:flex; align-items:center; gap:10px;
    font-size:.72rem; color:{muted};
}}
.dev-footer-brand {{
    font-weight:700; color:{a}; font-size:.76rem;
}}
.dev-footer-sep {{
    color:{cb}; font-size:.9rem;
}}
.dev-footer-link {{
    color:{a2}; text-decoration:none; font-size:.72rem;
    transition:color .15s;
}}
.dev-footer-link:hover {{ color:{a}; }}
.dev-footer-right {{
    font-size:.68rem; color:{muted};
    display:flex; align-items:center; gap:6px;
}}
.dev-footer-copy {{
    font-size:.66rem; color:{cb};
}}

/* ── Page bottom padding so footer doesn't cover content ── */
.main .block-container {{ padding-bottom:52px !important; }}
</style>
"""


FOOTER_HTML = """
<div class="dev-footer">
  <div class="dev-footer-left">
    <span style="font-size:1rem;">🚗</span>
    <span class="dev-footer-brand">Soft Rent a Car</span>
    <span class="dev-footer-sep">·</span>
    <span>Built by <strong>Muhammad Siddique</strong></span>
    <span class="dev-footer-sep">·</span>
    <a href="tel:+923229948042"   class="dev-footer-link">📞 +92 322 9948042</a>
    <span class="dev-footer-sep">·</span>
    <a href="mailto:siddique.dea@gmail.com" class="dev-footer-link">✉️ siddique.dea@gmail.com</a>
    <span class="dev-footer-sep">·</span>
    <a href="https://www.datawithms.top" target="_blank" class="dev-footer-link">🌐 datawithms.top</a>
    <span class="dev-footer-sep">·</span>
    <a href="https://www.linkedin.com/in/siddique-datalover" target="_blank" class="dev-footer-link">💼 LinkedIn</a>
  </div>
  <div style="font-size:.65rem;" class="dev-footer-copy">
    © 2026 Soft Rent a Car · Fleet Intelligence Platform
  </div>
</div>
"""
