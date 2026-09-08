"""
Generator: rate cards and pricing rules
"""

import random
from generators.base import make_id
from config import VEHICLE_TYPES, FLEET_COMPANIES, BOOKING_TYPES


def generate_rate_cards() -> list[dict]:
    """
    One rate card row per (fleet × vehicle_type × booking_type) combination.
    """
    rows = []
    fleet_ids = [f"FL{str(i+1).zfill(3)}" for i in range(len(FLEET_COMPANIES))]

    for fi, fid in enumerate(fleet_ids):
        for vt_idx, vt in enumerate(VEHICLE_TYPES, start=1):
            vt_id = f"VT{str(vt_idx).zfill(3)}"
            for btype in BOOKING_TYPES:
                # Adjust rates per booking type
                multiplier = {
                    "City Ride":               1.00,
                    "Airport Transfer":        1.10,
                    "Intercity":               1.15,
                    "Wedding":                 1.25,
                    "Corporate":               1.05,
                    "Tourism / Northern Areas":1.20,
                    "Monthly Contract":        0.75,
                    "Event":                   1.20,
                }.get(btype, 1.0)

                daily = round(
                    random.uniform(vt["daily_rate_min"], vt["daily_rate_max"]) * multiplier, 0
                )
                rows.append({
                    "rate_id":             make_id("RC", len(rows) + 1, 6),
                    "fleet_id":            fid,
                    "vehicle_type_id":     vt_id,
                    "booking_type":        btype,
                    "daily_rate_pkr":      daily,
                    "hourly_rate_pkr":     vt["hourly_rate"],
                    "km_rate_pkr":         vt["km_rate"],
                    "outstation_mult":     1.2,
                    "night_surcharge_pct": 10,
                    "airport_surcharge_pkr": 4000,
                    "security_deposit_pkr":  vt["deposit_pkr"],
                    "min_hours":           4,
                    "cancellation_fee_pct":15,
                    "fuel_included":       False,
                    "driver_included":     btype not in ("City Ride",),
                    "effective_from":      "2022-01-01",
                    "effective_to":        "2026-12-31",
                })
    return rows
