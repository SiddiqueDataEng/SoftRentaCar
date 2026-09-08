"""
Generator: vehicle maintenance records
"""

import random
from datetime import date, timedelta
from generators.base import make_id, random_date, jitter
from config import MAINTENANCE_TYPES, NUM_MAINTENANCE_RECORDS, SIM_START, SIM_END


_WORKSHOPS = [
    "Official Toyota Service Center Islamabad",
    "Honda Authorized Workshop Lahore",
    "Al-Hamd Auto Workshop",
    "City Motors Rawalpindi",
    "Premier Auto Care Karachi",
    "Fast Lube Islamabad",
    "CarPro Workshop F-10",
    "Bilal Tyre & Battery",
    "National Auto Parts & Repair",
    "Pak Euro Motors",
    "Workshop In-House (Fleet Mechanic)",
]

_STATUSES = ["Completed", "In Progress", "Scheduled", "Warranty Claim"]
_STATUS_W  = [0.75, 0.08, 0.12, 0.05]


def generate_maintenance(vehicles: list[dict]) -> list[dict]:
    rows = []
    active = [v for v in vehicles if v["status"] != "Retired"]

    for i in range(1, NUM_MAINTENANCE_RECORDS + 1):
        vehicle  = random.choice(active)
        mtype    = random.choice(MAINTENANCE_TYPES)
        maint_dt = random_date(SIM_START, SIM_END)

        cost     = round(mtype["avg_cost"] * random.uniform(0.70, 1.50), 0)
        parts    = round(cost * random.uniform(0.3, 0.6), 0)
        labour   = round(cost - parts, 0)

        # KM at which maintenance happened
        km_trigger = vehicle["odometer_km"] + random.randint(0, 80_000)

        rows.append({
            "maint_id":          make_id("MN", i, 5),
            "vehicle_id":        vehicle["vehicle_id"],
            "fleet_id":          vehicle["fleet_id"],
            "maintenance_type":  mtype["type"],
            "maintenance_date":  str(maint_dt),
            "odometer_km":       km_trigger,
            "workshop":          random.choice(_WORKSHOPS),
            "parts_cost_pkr":    parts,
            "labour_cost_pkr":   labour,
            "total_cost_pkr":    cost,
            "currency":          "PKR",
            "status":            random.choices(_STATUSES, weights=_STATUS_W)[0],
            "next_due_km":       km_trigger + (mtype["interval_km"] or 50_000),
            "next_due_date":     str(maint_dt + timedelta(days=random.randint(90, 365))),
            "technician_name":   f"Tech-{random.randint(1, 20)}",
            "remarks":           random.choice([
                None, "Minor wear observed", "Urgent – advised immediate action",
                "Replaced as per schedule", "Customer-reported issue resolved",
                "Warranty covered – no cost to fleet",
            ]),
        })

    return rows
