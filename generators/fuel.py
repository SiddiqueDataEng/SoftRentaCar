"""
Generator: fuel consumption log and general operating expenses
"""

import random
from datetime import date, datetime, timedelta
from generators.base import make_id, jitter, random_date
from config import FUEL_PRICES_TIMELINE, SIM_START, SIM_END, VEHICLE_TYPES


def _fuel_price_on(d: date) -> tuple[float, float, float]:
    """Return (petrol, diesel, cng) PKR/litre for a given date."""
    petrol = diesel = cng = 200.0
    for entry in FUEL_PRICES_TIMELINE:
        entry_date = date.fromisoformat(entry[0])
        if d >= entry_date:
            petrol, diesel, cng = entry[1], entry[2], entry[3]
    return petrol, diesel, cng


def _vt_for_vehicle(vehicle: dict) -> dict:
    for vt_idx, vt in enumerate(VEHICLE_TYPES, start=1):
        if f"VT{str(vt_idx).zfill(3)}" == vehicle["vehicle_type_id"]:
            return vt
    return VEHICLE_TYPES[0]


def generate_fuel_logs(
    trips: list[dict],
    vehicles: list[dict],
) -> list[dict]:
    """
    One fuel log entry per completed trip.
    """
    veh_map = {v["vehicle_id"]: v for v in vehicles}
    rows = []

    for trip in trips:
        if trip["status"] != "Completed" or trip["distance_km"] == 0:
            continue

        vehicle = veh_map.get(trip["vehicle_id"])
        if not vehicle:
            continue

        vt     = _vt_for_vehicle(vehicle)
        kmpl   = random.uniform(vt["fuel_eff_min"], vt["fuel_eff_max"])
        km     = trip["distance_km"]
        litres = round(km / kmpl, 2)

        fill_date = date.fromisoformat(trip["pickup_datetime"][:10])
        petrol, diesel, cng = _fuel_price_on(fill_date)

        if vehicle["fuel_type"] == "Diesel":
            price_per_l = diesel
        elif vehicle["fuel_type"] == "CNG":
            price_per_l = cng
        else:
            price_per_l = petrol

        # Simulate idle/AC overhead: add 5-20%
        actual_litres = round(litres * random.uniform(1.05, 1.20), 2)
        cost_pkr      = round(actual_litres * price_per_l, 2)

        rows.append({
            "fuel_id":           make_id("FU", len(rows) + 1, 7),
            "trip_id":           trip["trip_id"],
            "vehicle_id":        vehicle["vehicle_id"],
            "fleet_id":          vehicle["fleet_id"],
            "driver_id":         trip.get("driver_id"),
            "fill_date":         str(fill_date),
            "fuel_type":         vehicle["fuel_type"],
            "litres_filled":     actual_litres,
            "price_per_litre_pkr": round(price_per_l, 2),
            "fuel_cost_pkr":     cost_pkr,
            "km_driven":         km,
            "fuel_efficiency_kmpl": round(km / actual_litres, 2),
            "odometer_at_fill":  vehicle["odometer_km"] + int(random.uniform(0, 5000)),
            "fill_station":      random.choice([
                "PSO Islamabad", "Shell G-11", "Total Parco F-8",
                "HASCOL Lahore", "Attock Petroleum Rawalpindi",
                "PSO Karachi", "Shell Gulshan", "Total Parco DHA",
            ]),
            "paid_by":           random.choice(["Driver Cash", "Fleet Card", "Petty Cash"]),
        })

    return rows


def generate_operating_expenses(
    fleets: list[dict],
    drivers: list[dict],
    staff:   list[dict],
) -> list[dict]:
    """
    Monthly operating expenses per fleet: salaries, rent, utilities, insurance, etc.
    """
    from dateutil.relativedelta import relativedelta

    rows = []
    exp_categories = [
        ("Staff Salaries",    0.40),
        ("Driver Salaries",   0.20),
        ("Office Rent",       0.08),
        ("Utilities",         0.02),
        ("Marketing",         0.04),
        ("Insurance Premium", 0.06),
        ("Depreciation",      0.08),
        ("Miscellaneous",     0.04),
        ("Communication",     0.02),
        ("Parking / Garage",  0.06),
    ]

    fleet_driver_sal = {}
    fleet_staff_sal  = {}
    for f in fleets:
        fid = f["fleet_id"]
        fleet_driver_sal[fid] = sum(d["base_salary_pkr"] for d in drivers if d["fleet_id"] == fid)
        fleet_staff_sal[fid]  = sum(s["base_salary_pkr"] for s in staff  if s["fleet_id"] == fid)

    current = date(SIM_START.year, SIM_START.month, 1)
    end_mo  = date(SIM_END.year,   SIM_END.month,   1)

    while current <= end_mo:
        for f in fleets:
            fid = f["fleet_id"]
            base_monthly = fleet_driver_sal.get(fid, 200_000) + fleet_staff_sal.get(fid, 150_000)
            base_monthly = max(base_monthly, 200_000)

            for cat, pct in exp_categories:
                if cat == "Driver Salaries":
                    amt = fleet_driver_sal.get(fid, 100_000) * random.uniform(0.95, 1.05)
                elif cat == "Staff Salaries":
                    amt = fleet_staff_sal.get(fid, 80_000) * random.uniform(0.95, 1.05)
                else:
                    amt = base_monthly * pct * random.uniform(0.80, 1.20)

                rows.append({
                    "expense_id":    make_id("EX", len(rows) + 1, 7),
                    "fleet_id":      fid,
                    "expense_month": str(current),
                    "category":      cat,
                    "amount_pkr":    round(amt, 0),
                    "description":   f"{cat} for {current.strftime('%B %Y')}",
                    "approved_by":   "Fleet Manager",
                })

        current = (current + relativedelta(months=1))

    return rows
