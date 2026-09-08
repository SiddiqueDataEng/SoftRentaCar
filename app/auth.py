"""
Authentication — Soft Rent a Car
Uses streamlit-authenticator for cookie-based persistent sessions.
Falls back to simple session auth if package unavailable.
"""
import streamlit as st

ROLES = {
    "admin": {
        "label": "Administrator", "icon": "👑", "color": "#E63946",
        "pages": "all",
        "description": "Full access to all features",
    },
    "manager": {
        "label": "Fleet Manager", "icon": "🏢", "color": "#457B9D",
        "pages": ["executive","finance","operations","fleet","alerts","map","settings"],
        "description": "Fleet operations, finance and alerts",
    },
    "analyst": {
        "label": "Data Analyst", "icon": "📊", "color": "#2A9D8F",
        "pages": ["executive","finance","operations","forecast","stories","sql","chat"],
        "description": "Analytics, forecasting and SQL",
    },
    "viewer": {
        "label": "View Only", "icon": "👁️", "color": "#E9C46A",
        "pages": ["executive","operations"],
        "description": "Read-only dashboard access",
    },
    "driver": {
        "label": "Driver Portal", "icon": "🚗", "color": "#8AC926",
        "pages": ["drivers"],
        "description": "Driver safety and trips",
    },
}

_USERS = {
    "admin":    {"name": "Admin User",        "password": "Admin@2026",    "role": "admin",   "fleet": "all"},
    "siddique": {"name": "Muhammad Siddique", "password": "Siddique@2026", "role": "admin",   "fleet": "all"},
    "manager1": {"name": "Fleet Manager",     "password": "Manager@2026",  "role": "manager", "fleet": "FL001"},
    "analyst1": {"name": "Data Analyst",      "password": "Analyst@2026",  "role": "analyst", "fleet": "all"},
    "viewer1":  {"name": "View Only User",    "password": "Viewer@2026",   "role": "viewer",  "fleet": "FL002"},
}

# ── Try to import streamlit-authenticator ──────────────────────────────
try:
    import streamlit_authenticator as stauth
    _HAS_STAUTH = True
except ImportError:
    _HAS_STAUTH = False


def _get_users():
    """Load users from secrets or defaults."""
    try:
        raw = dict(st.secrets.get("users", {}))
        if raw:
            return {k: dict(v) for k, v in raw.items()}
    except Exception:
        pass
    return _USERS


def get_authenticator():
    """Return stauth.Authenticate instance, or a simple fallback object."""
    if _HAS_STAUTH:
        users = _get_users()
        creds = {"usernames": users}
        return stauth.Authenticate(
            credentials        = creds,
            cookie_name        = "soft_rentacar_session",
            cookie_key         = "soft_rentacar_key_2026_xyz",
            cookie_expiry_days = 7,
        )
    return _FallbackAuth()


class _FallbackAuth:
    """Simple auth fallback when streamlit-authenticator is not installed."""

    def login(self, location="main", key="login_form", **kwargs):
        """Render a simple login form. Returns (name, status, username) or None."""
        users = _get_users()
        with st.form(key):
            uname = st.text_input("Username", placeholder="e.g. admin")
            passw = st.text_input("Password", type="password")
            ok    = st.form_submit_button("🔐  Sign In",
                                          use_container_width=True,
                                          type="primary")
        if ok:
            u = users.get(uname.strip().lower())
            if u and passw.strip() == u.get("password",""):
                st.session_state["authentication_status"] = True
                st.session_state["username"]              = uname.strip().lower()
                st.session_state["name"]                  = u.get("name", uname)
                return u.get("name"), True, uname.strip().lower()
            elif ok:
                st.session_state["authentication_status"] = False
                return None, False, None
        return None, st.session_state.get("authentication_status"), \
               st.session_state.get("username")

    def logout(self, button_name="Sign Out", location="sidebar",
               key="logout_btn", **kwargs):
        if st.button(f"🚪  {button_name}", key=key):
            for k in ["authentication_status","username","name"]:
                st.session_state.pop(k, None)
            st.rerun()


def get_user_meta(username: str) -> dict:
    users = _get_users()
    u     = users.get(str(username).lower(), {})
    return {
        "username": username,
        "name":     u.get("name", username),
        "role":     u.get("role", "viewer"),
        "fleet":    u.get("fleet", "all"),
    }


def is_logged_in() -> bool:
    return st.session_state.get("authentication_status") is True


def current_user() -> dict:
    if not is_logged_in():
        return {}
    return get_user_meta(st.session_state.get("username", ""))


def current_role() -> str:
    return current_user().get("role", "viewer")
