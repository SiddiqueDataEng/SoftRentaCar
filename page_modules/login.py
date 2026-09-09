"""Login page — Soft Rent a Car"""
import streamlit as st
from app.auth import verify_login, ROLES
from app.themes import THEMES, DEFAULT_THEME, get_theme_css

# Inject default theme CSS on login page
theme = THEMES[DEFAULT_THEME]
st.markdown(get_theme_css(theme), unsafe_allow_html=True)

# ── Login page CSS ─────────────────────────────────────────────────────
st.markdown(f"""
<style>
.stApp {{ background: radial-gradient(ellipse at 20% 50%, #1D3557 0%, #0f1117 50%, #1a0a0f 100%); }}
[data-testid="stSidebar"] {{ display:none !important; }}
section[data-testid="stSidebarNav"] {{ display:none !important; }}

.login-wrap {{
    max-width: 420px;
    margin: 60px auto 0;
    padding: 0 16px;
}}
.login-card {{
    background: linear-gradient(145deg, #1e2a3a 0%, #14202e 100%);
    border: 1px solid #2d4a6b;
    border-radius: 20px;
    padding: 40px 36px;
    box-shadow: 0 24px 80px rgba(0,0,0,.6), 0 0 0 1px rgba(230,57,70,.08);
}}
.login-logo {{
    text-align: center;
    margin-bottom: 28px;
}}
.login-icon   {{ font-size: 3.2rem; display:block; margin-bottom:8px; }}
.login-title  {{ font-size: 1.7rem; font-weight:800; color:#E63946; }}
.login-sub    {{ font-size: .8rem;  color:#5a7a96; margin-top:3px; letter-spacing:.04em; }}

.role-pills {{
    display:flex; flex-wrap:wrap; gap:6px;
    margin: 18px 0 6px;
    justify-content: center;
}}
.role-pill {{
    font-size:.64rem; padding:3px 10px; border-radius:20px;
    border:1px solid; font-weight:600; letter-spacing:.04em;
    text-transform:uppercase;
}}
.login-hint {{
    font-size:.7rem; color:#3a5a74; text-align:center; margin-top:14px; line-height:1.6;
}}
.login-footer {{
    text-align:center; margin-top:20px;
    font-size:.68rem; color:#2a4a64; line-height:1.8;
}}
.login-footer a {{ color:#457B9D; text-decoration:none; }}
.login-footer a:hover {{ color:#E63946; }}
</style>
""", unsafe_allow_html=True)

# ── Session init ───────────────────────────────────────────────────────
if "login_error" not in st.session_state:
    st.session_state.login_error = ""

# ── Layout ────────────────────────────────────────────────────────────
_, center, _ = st.columns([1, 2, 1])

with center:
    st.markdown('<div class="login-wrap">', unsafe_allow_html=True)

    # Card header
    st.markdown("""
<div class="login-card">
  <div class="login-logo">
    <span class="login-icon">🚗</span>
    <div class="login-title">Soft Rent a Car</div>
    <div class="login-sub">Fleet Intelligence Platform</div>
  </div>
""", unsafe_allow_html=True)

    # Role pills — visual guide
    pills_html = '<div class="role-pills">'
    for key, r in ROLES.items():
        pills_html += (
            f'<span class="role-pill" '
            f'style="color:{r["color"]};border-color:{r["color"]}44;'
            f'background:{r["color"]}11;">'
            f'{r["icon"]} {r["label"]}</span>'
        )
    pills_html += "</div>"
    st.markdown(pills_html, unsafe_allow_html=True)

    # Form
    with st.form("login_form", clear_on_submit=False):
        username = st.text_input(
            "Username",
            placeholder="Enter username",
            key="login_user",
        )
        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter password",
            key="login_pass",
        )
        submit = st.form_submit_button(
            "🔐 Sign In",
            width='stretch',
            type="primary",
        )

    if submit:
        if not username.strip() or not password.strip():
            st.session_state.login_error = "Please enter both username and password."
        else:
            user = verify_login(username.strip(), password.strip())
            if user:
                st.session_state.user        = user
                st.session_state.login_error = ""
                st.rerun()
            else:
                st.session_state.login_error = "❌ Invalid username or password."

    if st.session_state.login_error:
        st.markdown(
            f'<div style="background:rgba(230,57,70,.12);border:1px solid #E63946;'
            f'border-radius:8px;padding:9px 14px;font-size:.82rem;color:#f08090;'
            f'text-align:center;margin-top:6px;">'
            f'{st.session_state.login_error}</div>',
            unsafe_allow_html=True,
        )

    # Demo credentials hint
    st.markdown("""
<div class="login-hint">
  <strong style="color:#5a7a96;">Demo credentials</strong><br>
  admin / Admin@2026 &nbsp;·&nbsp; analyst1 / Analyst@2026<br>
  manager1 / Manager@2026 &nbsp;·&nbsp; viewer1 / Viewer@2026
</div>
""", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)  # close login-card

    # Developer footer
    st.markdown("""
<div class="login-footer">
  Developed by <strong style="color:#c8dff0;">Muhammad Siddique</strong><br>
  <a href="tel:+923229948042">+92 322 9948042</a> ·
  <a href="mailto:siddique.dea@gmail.com">siddique.dea@gmail.com</a><br>
  <a href="https://www.datawithms.top" target="_blank">datawithms.top</a> ·
  <a href="https://www.linkedin.com/in/siddique-datalover" target="_blank">LinkedIn</a>
</div>
""", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)  # close login-wrap

