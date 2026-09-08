"""
Generator: drivers and non-driver staff
"""

import random
from datetime import date, timedelta
from generators.base import (
    make_id, pak_male_name, pak_female_name, pak_phone,
    pak_cnic, pak_license_no, random_date, weighted_choice
)
from config import (
    NUM_DRIVERS, NUM_STAFF, FLEET_COMPANIES, DRIVER_BEHAVIOR_PROFILES,
    STAFF_ROLES, SIM_START, SIM_END,
)

_FLEET_IDS = [f"FL{str(i+1).zfill(3)}" for i in range(len(FLEET_COMPANIES))]

# ── Drivers ────────────────────────────────────────────────────────────

def generate_drivers() -> list[dict]:
    rows = []
    behavior_weights = {
        "excellent": 0.10,
        "good":      0.30,
        "average":   0.40,
        "poor":      0.15,
        "dangerous": 0.05,
    }

    for i in range(1, NUM_DRIVERS + 1):
        gender  = random.choices(["M", "F"], weights=[0.92, 0.08])[0]
        name    = pak_male_name() if gender == "M" else pak_female_name()
        dob     = random_date(date(1975, 1, 1), date(2000, 12, 31))
        hire_dt = random_date(SIM_START - timedelta(days=365*4), SIM_END - timedelta(days=90))
        profile = random.choices(
            list(behavior_weights.keys()),
            weights=list(behavior_weights.values())
        )[0]

        fleet_id = random.choice(_FLEET_IDS)
        exp_yrs  = max(1, (hire_dt - dob).days // 365 - 18)

        rows.append({
            "driver_id":             make_id("DR", i, 4),
            "fleet_id":              fleet_id,
            "full_name":             name,
            "gender":                gender,
            "dob":                   str(dob),
            "cnic":                  pak_cnic(),
            "phone":                 pak_phone(),
            "license_no":            pak_license_no(),
            "license_expiry":        str(random_date(SIM_START, date(SIM_END.year + 3, 12, 31))),
            "hire_date":             str(hire_dt),
            "experience_years":      exp_yrs,
            "base_salary_pkr":       random.randint(30_000, 75_000),
            "behavior_profile":      profile,
            # Telematics KPIs (baseline per driver)
            "harsh_brake_rate":      round(DRIVER_BEHAVIOR_PROFILES[profile]["harsh_brake_rate"] + random.gauss(0, 0.01), 4),
            "harsh_accel_rate":      round(DRIVER_BEHAVIOR_PROFILES[profile]["harsh_accel_rate"] + random.gauss(0, 0.01), 4),
            "idle_time_pct":         round(DRIVER_BEHAVIOR_PROFILES[profile]["idle_pct"] + random.gauss(0, 0.02), 4),
            "speeding_pct":          round(DRIVER_BEHAVIOR_PROFILES[profile]["speeding_pct"] + random.gauss(0, 0.02), 4),
            "total_trips":           0,   # filled later
            "total_km_driven":       0,   # filled later
            "accidents_count":       0,   # filled later
            "complaints_count":      0,   # filled later
            "ratings_avg":           round(random.uniform(3.2, 5.0), 2),
            "active":                random.random() < 0.90,
        })
    return rows


# ── Non-driver staff ───────────────────────────────────────────────────

def generate_staff() -> list[dict]:
    rows = []
    for i in range(1, NUM_STAFF + 1):
        gender = random.choices(["M", "F"], weights=[0.75, 0.25])[0]
        name   = pak_male_name() if gender == "M" else pak_female_name()
        dob    = random_date(date(1970, 1, 1), date(1998, 12, 31))
        hire_dt = random_date(SIM_START - timedelta(days=365*5), SIM_END - timedelta(days=60))
        role   = random.choice(STAFF_ROLES)
        sal_map = {
            "Fleet Manager":       (80_000, 150_000),
            "Operations Manager":  (70_000, 130_000),
            "Booking Coordinator": (35_000, 60_000),
            "Accountant":          (45_000, 80_000),
            "Dispatcher":          (30_000, 50_000),
            "Mechanic":            (40_000, 70_000),
            "Cleaner / Detailer":  (20_000, 35_000),
            "Customer Service Rep":(30_000, 50_000),
            "HR Manager":          (60_000, 100_000),
            "IT / Data Analyst":   (60_000, 120_000),
        }
        lo, hi = sal_map.get(role, (30_000, 60_000))

        rows.append({
            "staff_id":       make_id("ST", i, 4),
            "fleet_id":       random.choice(_FLEET_IDS),
            "full_name":      name,
            "gender":         gender,
            "dob":            str(dob),
            "cnic":           pak_cnic(),
            "phone":          pak_phone(),
            "role":           role,
            "hire_date":      str(hire_dt),
            "base_salary_pkr":random.randint(lo, hi),
            "active":         random.random() < 0.88,
        })
    return rows
