"""Settings & API Key Management"""
import streamlit as st
import os
from page_modules._shared import inject, get_data, sec, alert_box, BRAND, STEEL, GREEN, AMBER, TEXT

inject()

st.markdown(
    f'<div style="font-size:1.5rem;font-weight:800;color:{BRAND};margin-bottom:4px;">⚙️ Settings & API Keys</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div style="font-size:.8rem;color:#5a7a96;">Configure AI, map and integration keys — saved for this session</div>',
    unsafe_allow_html=True,
)
st.markdown("<hr style='border-color:#1e2f44;margin:6px 0 16px 0'>", unsafe_allow_html=True)

# ── Session key store ─────────────────────────────────────────────────
if "api_keys" not in st.session_state:
    st.session_state.api_keys = {}


def _resolve(name: str, default: str = "") -> str:
    """Priority: session → st.secrets → env → default."""
    if st.session_state.api_keys.get(name):
        return st.session_state.api_keys[name]
    try:
        v = st.secrets.get(name, "")
        if v: return v
    except Exception:
        pass
    return os.getenv(name, default)


# ── OpenAI ────────────────────────────────────────────────────────────
sec("🤖 OpenAI — GPT-4o Chat")
st.markdown(
    '<div style="font-size:.8rem;color:#5a7a96;margin-bottom:8px;">'
    'Powers the AI Chat Assistant with natural language fleet analytics. '
    'Get a key at <a href="https://platform.openai.com/api-keys" target="_blank" '
    'style="color:#457B9D;">platform.openai.com</a></div>',
    unsafe_allow_html=True,
)
current_oai = _resolve("OPENAI_API_KEY")
oai_status  = "✅ Configured" if current_oai else "❌ Not set — Chat uses rule-based fallback"
st.markdown(f'<div style="font-size:.78rem;color:{GREEN if current_oai else AMBER};">{oai_status}</div>',
            unsafe_allow_html=True)

with st.form("oai_form"):
    new_oai = st.text_input(
        "OpenAI API Key",
        type="password",
        placeholder="sk-proj-...",
        help="Your OpenAI API key (starts with sk-)",
    )
    if st.form_submit_button("💾 Save OpenAI Key", type="primary"):
        if new_oai.strip().startswith("sk-"):
            st.session_state.api_keys["OPENAI_API_KEY"] = new_oai.strip()
            os.environ["OPENAI_API_KEY"] = new_oai.strip()
            st.success("✅ OpenAI key saved for this session!")
        else:
            st.error("Key must start with 'sk-'")

st.markdown("<hr style='border-color:#1e2f44;margin:14px 0'>", unsafe_allow_html=True)

# ── Carto ─────────────────────────────────────────────────────────────
sec("🗺️ Carto — Map Tiles")
st.markdown(
    '<div style="font-size:.8rem;color:#5a7a96;margin-bottom:8px;">'
    'Powers the interactive Pakistan map with dark/voyager/positron tile styles. '
    'Get a key at <a href="https://carto.com/developers" target="_blank" '
    'style="color:#457B9D;">carto.com/developers</a></div>',
    unsafe_allow_html=True,
)
current_carto = _resolve("CARTO_API_KEY")
carto_status  = "✅ Configured (default key active)" if current_carto else "❌ Not set"
st.markdown(f'<div style="font-size:.78rem;color:{GREEN};">{carto_status}</div>',
            unsafe_allow_html=True)

with st.form("carto_form"):
    new_carto = st.text_input(
        "Carto API Key",
        type="password",
        placeholder="eyJhbGciOiJIUzI1NiJ9...",
        help="Your Carto API key (JWT format)",
    )
    if st.form_submit_button("💾 Save Carto Key"):
        if new_carto.strip():
            st.session_state.api_keys["CARTO_API_KEY"] = new_carto.strip()
            os.environ["CARTO_API_KEY"] = new_carto.strip()
            st.success("✅ Carto key saved for this session!")
        else:
            st.error("Please enter a valid key.")

st.markdown("<hr style='border-color:#1e2f44;margin:14px 0'>", unsafe_allow_html=True)

# ── Theme & Display ───────────────────────────────────────────────────
sec("🎨 Current Configuration")
from app.themes import THEMES
theme_name = st.session_state.get("selected_theme", "🌑 Dark Navy (Default)")
t = THEMES.get(theme_name, {})

cols = st.columns(3)
cols[0].markdown(f"""
<div style="background:{t.get('card_bg','#1e2a3a')};border:1px solid {t.get('card_bdr','#2d4a6b')};
            border-radius:10px;padding:12px 14px;">
  <div style="font-size:.7rem;color:{t.get('text_muted','#5a7a96')};text-transform:uppercase;
              letter-spacing:.06em;margin-bottom:4px;">Active Theme</div>
  <div style="font-size:.9rem;font-weight:700;color:{t.get('text','#c8dff0')};">{theme_name}</div>
</div>""", unsafe_allow_html=True)

from app.auth import current_user, ROLES
u    = current_user()
role = u.get("role","viewer")
rm   = ROLES.get(role,{})
cols[1].markdown(f"""
<div style="background:{t.get('card_bg','#1e2a3a')};border:1px solid {t.get('card_bdr','#2d4a6b')};
            border-radius:10px;padding:12px 14px;">
  <div style="font-size:.7rem;color:{t.get('text_muted','#5a7a96')};text-transform:uppercase;
              letter-spacing:.06em;margin-bottom:4px;">Logged In As</div>
  <div style="font-size:.9rem;font-weight:700;color:{rm.get('color','#E63946')};">
    {rm.get('icon','')} {u.get('name','')}
  </div>
  <div style="font-size:.72rem;color:{t.get('text_muted','#5a7a96')};">{rm.get('label','')} · {u.get('fleet','')}</div>
</div>""", unsafe_allow_html=True)

cols[2].markdown(f"""
<div style="background:{t.get('card_bg','#1e2a3a')};border:1px solid {t.get('card_bdr','#2d4a6b')};
            border-radius:10px;padding:12px 14px;">
  <div style="font-size:.7rem;color:{t.get('text_muted','#5a7a96')};text-transform:uppercase;
              letter-spacing:.06em;margin-bottom:4px;">API Status</div>
  <div style="font-size:.82rem;color:{t.get('text','#c8dff0')};">
    {'✅' if current_oai else '❌'} GPT-4o<br>
    {'✅' if current_carto else '⚠️'} Carto Maps
  </div>
</div>""", unsafe_allow_html=True)

st.markdown("<hr style='border-color:#1e2f44;margin:14px 0'>", unsafe_allow_html=True)

# ── For Streamlit Cloud deployment ────────────────────────────────────
sec("☁️ Streamlit Cloud Deployment")
st.markdown("""
<div style="background:rgba(69,123,157,.1);border:1px solid #457B9D;border-radius:8px;
            padding:14px 16px;font-size:.82rem;color:#90bdd4;line-height:1.8;">
  <strong style="color:#c8dff0;">To persist API keys across sessions on Streamlit Cloud:</strong><br>
  Go to your app → <strong>Settings → Secrets</strong> and add:<br><br>
  <code style="background:#0f1a24;padding:3px 8px;border-radius:4px;display:block;
               font-size:.78rem;color:#7dd8cc;margin:4px 0;">OPENAI_API_KEY = "sk-proj-..."</code>
  <code style="background:#0f1a24;padding:3px 8px;border-radius:4px;display:block;
               font-size:.78rem;color:#7dd8cc;margin:4px 0;">CARTO_API_KEY = "eyJhbGci..."</code>
  <br>Also add user credentials under <code>[users.username]</code> sections.
</div>
""", unsafe_allow_html=True)

# ── Clear session ─────────────────────────────────────────────────────
st.markdown("<hr style='border-color:#1e2f44;margin:14px 0'>", unsafe_allow_html=True)
sec("🗑️ Session Management")
col_a, col_b, _ = st.columns([1, 1, 3])
if col_a.button("🔄 Clear API Keys", width='stretch'):
    st.session_state.api_keys = {}
    st.success("API keys cleared from session.")
if col_b.button("🔃 Reload Data Cache", width='stretch'):
    get_data.clear()
    st.success("Data cache cleared — will regenerate on next load.")

