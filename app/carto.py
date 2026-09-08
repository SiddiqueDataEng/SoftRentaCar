"""
Carto API key resolver — Soft Rent a Car
Priority:
  1. st.secrets["CARTO_API_KEY"]
  2. os.environ["CARTO_API_KEY"]
  3. Built-in default key
"""

import os

_DEFAULT_CARTO_KEY = (
    "eyJhbGciOiJIUzI1NiJ9"
    ".eyJhIjoiYWNfMjc2MWIwcmQiLCJqdGkiOiJlZjE1YzE4YiIsImV4cCI6MTc4OTQ3MjAxMH0"
    ".0liB2vFwQuLxtCo4r9nTtQAf9JN0kMN-l7B_23tAPvg"
)


def get_carto_key() -> str:
    """Return the best available Carto API key."""
    # 1. Streamlit secrets
    try:
        import streamlit as st
        key = st.secrets.get("CARTO_API_KEY", "")
        if key and len(key) > 20:
            return key
    except Exception:
        pass
    # 2. Environment variable
    key = os.getenv("CARTO_API_KEY", "")
    if key and len(key) > 20:
        return key
    # 3. Default
    return _DEFAULT_CARTO_KEY


def carto_map_style(style: str = "dark_matter") -> dict:
    """
    Return a Plotly mapbox style dict using Carto authenticated tiles.
    Available styles:
        dark_matter, dark_matter_nolabels,
        voyager, voyager_nolabels,
        positron, positron_nolabels,
        rastertiles/voyager, rastertiles/positron
    """
    key = get_carto_key()
    return {
        "style": {
            "version": 8,
            "sources": {
                "carto-tiles": {
                    "type":        "raster",
                    "tiles":       [
                        f"https://{{s}}.basemaps.cartocdn.com/{style}/{{z}}/{{x}}/{{y}}@2x.png"
                        .replace("{s}", "a"),
                    ],
                    "tileSize": 256,
                    "attribution": "© CARTO",
                }
            },
            "layers": [{
                "id":     "carto-tiles",
                "type":   "raster",
                "source": "carto-tiles",
                "minzoom": 0,
                "maxzoom": 22,
            }],
        }
    }


# Simpler approach: use Plotly's built-in carto styles with the token
CARTO_STYLES = {
    "Dark Matter":        "carto-darkmatter",
    "Dark (no labels)":   "carto-darkmatter-nolabels",
    "Voyager":            "carto-positron",          # closest built-in
    "Positron (light)":   "carto-positron",
    "Positron (no lbl)":  "carto-positron-nolabels",
}
