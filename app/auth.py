"""
Authentication — Soft Rent a Car
Uses streamlit-authenticator for cookie-based persistent sessions.
"""
import streamlit as st
import streamlit_authenticator as stauth

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
    "usernames": {
        "admin":    {"name": "Admin User",        "password": "Admin@2026",    "role": "admin",   "fleet": "all"},
        "siddique": {"name": "Muhammad Siddique", "password": "Siddique@2026", "role": "admin",   "fleet": "all"},
        "manager1": {"name": "Fleet Manager",     "password": "Manager@2026",  "role": "manager", "fleet": "FL001"},
        "analyst1": {"name": "Data Analyst",      "password": "Analyst@2026",  "role": "analyst", "fleet": "all"},
        "viewer1":  {"name": "View Only User",    "password": "Viewer@2026",   "role": "viewer",  "fleet": "FL002"},
    }
}


def _get_creds():
    try:
        raw = dict(st.secrets.get("users", {}))
        if raw:
            return {"usernames": {k: dict(v) for k, v in raw.items()}}
    except Exception:
        pass
    return _USERS


def get_authenticator():
    creds = _get_creds()
    return stauth.Authenticate(
        credentials        = creds,
        cookie_name        = "soft_rentacar_session",
        cookie_key         = "soft_rentacar_key_2026_xyz",
        cookie_expiry_days = 7,
    )


def get_user_meta(username: str) -> dict:
    creds = _get_creds()
    u = creds["usernames"].get(str(username).lower(), {})
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
