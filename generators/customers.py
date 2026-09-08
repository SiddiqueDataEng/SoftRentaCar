"""
Generator: customers
"""

import random
from datetime import date
from generators.base import (
    make_id, pak_male_name, pak_female_name, pak_phone,
    pak_cnic, pak_license_no, random_date,
)
from config import NUM_CUSTOMERS, CITIES, SIM_START, SIM_END

NATIONALITIES = ["Pakistani"] * 80 + [
    "British Pakistani", "American Pakistani", "Canadian Pakistani",
    "Saudi", "UAE", "UK", "USA", "France", "Germany", "Australia",
]

CUSTOMER_TYPES = ["Individual", "Corporate", "Tourist", "Overseas Pakistani", "Government"]
CUSTOMER_WEIGHTS = [0.50, 0.20, 0.12, 0.12, 0.06]


def generate_customers() -> list[dict]:
    rows = []
    for i in range(1, NUM_CUSTOMERS + 1):
        gender  = random.choices(["M", "F"], weights=[0.65, 0.35])[0]
        name    = pak_male_name() if gender == "M" else pak_female_name()
        dob     = random_date(date(1960, 1, 1), date(2002, 12, 31))
        city    = random.choices(CITIES, weights=[c["demand"] for c in CITIES])[0]
        ctype   = random.choices(CUSTOMER_TYPES, weights=CUSTOMER_WEIGHTS)[0]
        nat     = random.choice(NATIONALITIES)

        has_license = random.random() < 0.68
        rows.append({
            "customer_id":     make_id("CU", i, 5),
            "full_name":       name,
            "gender":          gender,
            "dob":             str(dob),
            "cnic":            pak_cnic() if nat.lower() in ("pakistani", "british pakistani", "american pakistani", "canadian pakistani") else "N/A",
            "nationality":     nat,
            "phone":           pak_phone(),
            "email":           f"{name.lower().replace(' ', '.')}{random.randint(1,999)}@gmail.com",
            "city":            city["name"],
            "customer_type":   ctype,
            "license_no":      pak_license_no() if has_license else None,
            "has_own_license": has_license,
            "loyalty_points":  random.randint(0, 5000),
            "total_bookings":  0,   # filled later
            "registration_date": str(random_date(SIM_START, SIM_END)),
        })
    return rows
