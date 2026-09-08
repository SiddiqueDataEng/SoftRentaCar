"""Integration test — Soft Rent a Car"""
import sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, ".")

# Data
from page_modules._shared import get_data
dfs = get_data()
print("data: OK —", len(dfs), "tables")

# Storytelling
from app.storytelling import (
    insight, revenue_insight, trips_insight, driver_safety_insight,
    fleet_utilisation_insight, fuel_insight, maintenance_insight,
    city_demand_insight, route_insight, customer_insight,
    forecast_insight, kpi_insight,
)
txt, sub, lvl = revenue_insight(dfs["invoices"])
print("storytelling: OK — revenue level:", lvl)

# Auth
from app.auth import get_authenticator, get_user_meta, ROLES, is_logged_in
u = get_user_meta("admin")
print("auth: OK —", u["name"], "/", u["role"])
print("roles:", list(ROLES.keys()))

# Carto
from app.carto import get_carto_key, CARTO_STYLES
k = get_carto_key()
print("carto: OK — key length:", len(k), "| styles:", list(CARTO_STYLES.keys()))

# Themes
from app.themes import THEMES, get_theme_css
print("themes: OK —", list(THEMES.keys()))

# Insight generators
for fn, args in [
    (trips_insight,              (dfs["trips"],)),
    (driver_safety_insight,      (dfs["telematics"], dfs["drivers"])),
    (fuel_insight,               (dfs["fuel_logs"],)),
    (maintenance_insight,        (dfs["maintenance"],)),
    (city_demand_insight,        (dfs["trips"],)),
    (route_insight,              (dfs["trips"],)),
    (customer_insight,           (dfs["customers"], dfs["invoices"])),
    (fleet_utilisation_insight,  (dfs["trips"], dfs["vehicles"])),
]:
    t, s, l = fn(*args)
    print(f"  {fn.__name__}: {l}")

print("\nAll tests passed!")
