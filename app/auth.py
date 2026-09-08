"""
Authentication & Role-based Access Control — Soft Rent a Car
Credentials stored in st.secrets (Streamlit Cloud) or .streamlit/secrets.toml locally.

secrets.toml format:
[users]
admin       = { password = "Admin@2026",    role = "admin",   name = "Admin User",         fleet = "all" }
siddique    = { password = "Siddique@2026", role = "admin",   name = "Muhammad Siddique",  fleet = "all" }
manager1    = { password = "Manager@2026",  role = "manager", name = "Fleet Manager",       fleet = "FL001" }
analyst1    = { password = "Analyst@2026",  role = "analyst", name = "Data Analyst",        fleet = "all" }
viewer1     = { password = "Viewer@2026",   role = "viewer",  name = "View Only User",      fleet = "FL002" }
driver_app  = { password = "Driver@2026",   role = "driver",  name = "Driver Portal",       fleet = "all" }
"""

import hashlib
import streamlit as st

# ── Role definitions ──────────────────────────────────────────────────
ROLES = {
    "admin": {
        "label":       "Administrator",
        "icon":        "👑",
        "color":       "#E63946",
        "pages":       "all",   # access to everything
        "description": "Full access to all features, data and settings",
    },
    "manager": {
        "label":       "Fleet Manager",
        "icon":        "🏢",
        "color":       "#457B9D",
        "pages":       ["executive", "finance", "operations", "fleet", "alerts", "map"],
        "description": "Fleet operations, finance, and alerts",
    },
    "analyst": {
        "label":       "Data Analyst",
        "icon":        "📊",
        "color":       "#2A9D8F",
        "pages":       ["executive", "finance", "operations", "forecast", "stories", "sql", "chat"],
        "description": "Analytics, forecasting and SQL access",
    },
    "viewer": {
        "label":       "View Only",
        "icon":        "👁️",
        "color":       "#E9C46A",
        "pages":       ["executive", "operations"],
        "description": "Read-only access to dashboards",
    },
    "driver": {
        "label":       "Driver Portal",
        "icon":        "🚗",
        "color":       "#8AC926",
        "pages":       ["drivers"],
        "description": "Driver safety scores and trip history",
    },
}

# ── Fallback user store (used when secrets not configured) ─────────────
_DEFAULT_USERS = {
    "admin":      {"password": "Admin@2026",    "role": "admin",   "name": "Admin User",        "fleet": "all"},
    "siddique":   {"password": "Siddique@2026", "role": "admin",   "name": "Muhammad Siddique", "fleet": "all"},
    "manager1":   {"password": "Manager@2026",  "role": "manager", "name": "Fleet Manager",      "fleet": "FL001"},
    "analyst1":   {"password": "Analyst@2026",  "role": "analyst", "name": "Data Analyst",       "fleet": "all"},
    "viewer1":    {"password": "Viewer@2026",   "role": "viewer",  "name": "View Only",          "fleet": "FL002"},
}


def _get_users() -> dict:
    """Load users from st.secrets if available, else fallback."""
    try:
        raw = dict(st.secrets.get("users", {}))
        if raw:
            return {k: dict(v) for k, v in raw.items()}
    except Exception:
        pass
    return _DEFAULT_USERS


def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def verify_login(username: str, password: str) -> dict | None:
    """Return user dict if credentials valid, else None."""
    users = _get_users()
    u = users.get(username.strip().lower())
    if not u:
        return None
    stored = u.get("password", "")
    # Accept plain text (secrets.toml) or sha256 hash
    if password == stored or _hash(password) == stored:
        return {
            "username": username.lower(),
            "name":     u.get("name", username),
            "role":     u.get("role", "viewer"),
            "fleet":    u.get("fleet", "all"),
        }
    return None


def is_logged_in() -> bool:
    return bool(st.session_state.get("user"))


def current_user() -> dict:
    return st.session_state.get("user", {})


def current_role() -> str:
    return current_user().get("role", "viewer")


def require_login():
    """Call at the top of any page that needs auth. Redirects to login if not authenticated."""
    if not is_logged_in():
        st.stop()


def has_access(page_key: str) -> bool:
    role = current_role()
    if role == "admin":
        return True
    allowed = ROLES.get(role, {}).get("pages", [])
    if allowed == "all":
        return True
    return page_key in allowed


def logout():
    for key in ["user", "chat_history", "selected_theme"]:
        st.session_state.pop(key, None)
    st.rerun()
