"""
Authentication — Soft Rent a Car
Simple, reliable session-based auth with optional cookie persistence.
"""
import hashlib
import streamlit as st

ROLES = {
    "admin":   {"label":"Administrator","icon":"👑","color":"#E63946","pages":"all"},
    "manager": {"label":"Fleet Manager","icon":"🏢","color":"#457B9D",
                "pages":["executive","finance","operations","fleet","alerts","map","settings"]},
    "analyst": {"label":"Data Analyst","icon":"📊","color":"#2A9D8F",
                "pages":["executive","finance","operations","forecast","stories","sql","chat"]},
    "viewer":  {"label":"View Only","icon":"👁️","color":"#E9C46A",
                "pages":["executive","operations"]},
    "driver":  {"label":"Driver Portal","icon":"🚗","color":"#8AC926",
                "pages":["drivers"]},
}

_USERS = {
    "admin":    {"name":"Admin User",        "password":"Admin@2026",    "role":"admin",   "fleet":"all"},
    "siddique": {"name":"Muhammad Siddique", "password":"Siddique@2026", "role":"admin",   "fleet":"all"},
    "manager1": {"name":"Fleet Manager",     "password":"Manager@2026",  "role":"manager", "fleet":"FL001"},
    "analyst1": {"name":"Data Analyst",      "password":"Analyst@2026",  "role":"analyst", "fleet":"all"},
    "viewer1":  {"name":"View Only User",    "password":"Viewer@2026",   "role":"viewer",  "fleet":"FL002"},
}

def _get_users():
    try:
        raw = dict(st.secrets.get("users", {}))
        if raw: return {k: dict(v) for k, v in raw.items()}
    except Exception:
        pass
    return _USERS

def verify(username: str, password: str):
    u = _get_users().get(username.strip().lower())
    if u and password.strip() == u.get("password",""):
        return u
    return None

def get_user_meta(username: str) -> dict:
    u = _get_users().get(str(username).lower(), {})
    return {"username":username,"name":u.get("name",username),
            "role":u.get("role","viewer"),"fleet":u.get("fleet","all")}

def is_logged_in() -> bool:
    return st.session_state.get("_auth_ok") is True

def current_user() -> dict:
    return get_user_meta(st.session_state.get("_auth_user","")) if is_logged_in() else {}

def current_role() -> str:
    return current_user().get("role","viewer")

def do_logout():
    for k in ["_auth_ok","_auth_user","_auth_name","current_page",
              "chat_history","api_keys"]:
        st.session_state.pop(k, None)
    st.rerun()
