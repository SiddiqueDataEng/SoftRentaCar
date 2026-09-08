"""
Generator: fleets, vehicles, vehicle_types, vehicle_attributes
"""

import random
from datetime import date
from generators.base import make_id, random_date, jitter
from config import (
    FLEET_COMPANIES, VEHICLE_TYPES, NUM_VEHICLES, SIM_START, SIM_END,
    CITIES,
)


# ── 1. Fleets ─────────────────────────────────────────────────────────

def generate_fleets() -> list[dict]:
    rows = []
    for i, fc in enumerate(FLEET_COMPANIES, start=1):
        rows.append({
            "fleet_id":           make_id("FL", i, 3),
            "fleet_name":         fc["name"],
            "city":               fc["city"],
            "website":            fc["website"],
            "secp_registered":    fc["secp_registered"],
            "ntn_registered":     fc["ntn_registered"],
            "established_year":   fc["established_year"],
            "focus_segment":      fc["focus"],
            "total_vehicles":     0,       # filled later
            "active":             True,
        })
    return rows


# ── 2. Vehicle types (dimension table) ───────────────────────────────

def generate_vehicle_types() -> list[dict]:
    rows = []
    for i, vt in enumerate(VEHICLE_TYPES, start=1):
        rows.append({
            "vehicle_type_id":      make_id("VT", i, 3),
            "category":             vt["category"],
            "sub_type":             vt["sub_type"],
            "make":                 vt["make"],
            "seats":                vt["seats"],
            "fuel_type":            vt["fuel_type"],
            "transmission":         vt["transmission"],
            "daily_rate_min_pkr":   vt["daily_rate_min"],
            "daily_rate_max_pkr":   vt["daily_rate_max"],
            "hourly_rate_pkr":      vt["hourly_rate"],
            "km_rate_pkr":          vt["km_rate"],
            "fuel_eff_min_kmpl":    vt["fuel_eff_min"],
            "fuel_eff_max_kmpl":    vt["fuel_eff_max"],
            "security_deposit_pkr": vt["deposit_pkr"],
        })
    return rows


# ── 3. Vehicles ────────────────────────────────────────────────────────

_COLORS = [
    "White", "Silver", "Pearl White", "Midnight Black", "Graphite Grey",
    "Beige", "Red", "Blue", "Dark Blue", "Golden", "Brown",
]

_CONDITION_LABELS = ["Excellent", "Good", "Fair", "Needs Attention"]

def _plate_no(city_code: str, idx: int) -> str:
    """Generate a Pakistan-style number plate: ABC-123 or LEA-1234."""
    letters = "".join(random.choices("ABCDEFGHJKLMNPQRSTUVWXYZ", k=3))
    digits  = str(random.randint(100, 9999))
    return f"{city_code}-{letters}-{digits}"

_CITY_PLATE_CODES = {
    "Islamabad":  "ISB",
    "Rawalpindi": "RWP",
    "Lahore":     "LHR",
    "Karachi":    "KHI",
    "Peshawar":   "PEW",
    "Murree":     "MRR",
    "Multan":     "MTN",
    "Faisalabad": "FSD",
}

def generate_vehicles(fleets: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    """
    Returns:
      vehicles            – fact table
      vehicle_attributes  – EAV-style extra attributes
      updated fleets      – total_vehicles counts patched
    """
    fleet_ids = [f["fleet_id"] for f in fleets]
    # Distribute vehicles across fleets (roughly proportional)
    weights = [0.35, 0.30, 0.25, 0.10]  # Hassan, RentKA, Haxn, Cars247
    vt_rows  = generate_vehicle_types()
    vt_map   = {v["vehicle_type_id"]: v for v in vt_rows}

    vehicles    = []
    attributes  = []
    fleet_count = {fid: 0 for fid in fleet_ids}

    for idx in range(1, NUM_VEHICLES + 1):
        fleet_id = random.choices(fleet_ids, weights=weights)[0]
        fleet_count[fleet_id] += 1

        vt = random.choice(VEHICLE_TYPES)
        vt_id = f"VT{str(VEHICLE_TYPES.index(vt)+1).zfill(3)}"

        year      = random.randint(*vt["year_range"])
        model     = random.choice(vt["models"])
        city_name = next(f["city"] for f in fleets if f["fleet_id"] == fleet_id)
        city_code = _CITY_PLATE_CODES.get(city_name, "PKR")
        plate     = _plate_no(city_code, idx)

        purchase_date = date(year, random.randint(1, 12), random.randint(1, 28))
        odometer      = random.randint(10_000, 180_000)
        daily_rate    = int(random.uniform(vt["daily_rate_min"], vt["daily_rate_max"]))
        # Insurance renewal (annually)
        ins_start  = purchase_date
        ins_expiry = date(ins_start.year + 1 + random.randint(0, 3),
                          ins_start.month, ins_start.day)

        status = random.choices(
            ["Available", "On Trip", "Under Maintenance", "Reserved", "Retired"],
            weights=[0.55, 0.20, 0.12, 0.10, 0.03]
        )[0]

        v = {
            "vehicle_id":          make_id("VH", idx),
            "fleet_id":            fleet_id,
            "vehicle_type_id":     vt_id,
            "make":                vt["make"],
            "model":               model,
            "year":                year,
            "registration_no":     plate,
            "color":               random.choice(_COLORS),
            "fuel_type":           vt["fuel_type"],
            "transmission":        vt["transmission"],
            "seats":               vt["seats"],
            "odometer_km":         odometer,
            "purchase_date":       str(purchase_date),
            "daily_rate_pkr":      daily_rate,
            "hourly_rate_pkr":     vt["hourly_rate"],
            "km_rate_pkr":         vt["km_rate"],
            "insurance_expiry":    str(ins_expiry),
            "fitness_cert_expiry": str(date(SIM_END.year, random.randint(1, 12), 1)),
            "status":              status,
            "condition_rating":    random.choices(
                                       _CONDITION_LABELS,
                                       weights=[0.30, 0.45, 0.18, 0.07]
                                   )[0],
            "gps_enabled":         random.random() < 0.75,
            "telematics_enabled":  random.random() < 0.55,
            "ac_working":          random.random() < 0.92,
        }
        vehicles.append(v)

        # EAV attributes (extra specs)
        specs = [
            ("engine_cc",         str(random.choice([660, 1000, 1200, 1300, 1500, 1600, 2000, 2700, 3000, 4000]))),
            ("abs",               str(random.random() < 0.70)),
            ("airbags",           str(random.choice([0, 2, 4, 6]))),
            ("central_locking",   str(random.random() < 0.88)),
            ("reverse_camera",    str(random.random() < 0.60)),
            ("sunroof",           str(random.random() < 0.25)),
            ("push_start",        str(random.random() < 0.55)),
            ("heated_seats",      str(random.random() < 0.15)),
            ("leather_interior",  str(random.random() < 0.35)),
            ("infotainment",      str(random.choice(["None", "Basic", "Android", "Apple CarPlay"]))),
            ("child_seat_avail",  str(random.random() < 0.20)),
        ]
        for attr_name, attr_val in specs:
            attributes.append({
                "attr_id":    make_id("VA", len(attributes) + 1),
                "vehicle_id": v["vehicle_id"],
                "attr_name":  attr_name,
                "attr_value": attr_val,
            })

    # Patch fleet totals
    for f in fleets:
        f["total_vehicles"] = fleet_count[f["fleet_id"]]

    return vehicles, attributes, fleets
