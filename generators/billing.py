"""
Generator: billing / invoices and billing line items
"""

import random
from datetime import datetime, timedelta
from generators.base import make_id, jitter
from config import PAYMENT_METHODS, SURCHARGE_TYPES


def _get_fuel_price(trip_date_str: str) -> tuple[float, float]:
    """Return (petrol_pkr, diesel_pkr) based on approximate date."""
    from config import FUEL_PRICES_TIMELINE
    from datetime import date
    d = date.fromisoformat(trip_date_str[:10])
    petrol = diesel = 220.0
    for entry in FUEL_PRICES_TIMELINE:
        entry_date = date.fromisoformat(entry[0])
        if d >= entry_date:
            petrol = entry[1]
            diesel = entry[2]
    return petrol, diesel


def generate_billing(
    trips: list[dict],
) -> tuple[list[dict], list[dict]]:
    """
    Returns:
      invoices         – one per completed/partially cancelled trip
      billing_line_items – surcharge & base charge breakdown
    """
    invoices   = []
    line_items = []

    for trip in trips:
        if trip["status"] not in ("Completed", "Cancelled"):
            if trip["status"] == "In Progress":
                pass   # generate a partial invoice
            else:
                continue

        inv_id  = make_id("INV", len(invoices) + 1, 6)
        base    = trip["trip_fare_pkr"]

        # Surcharges
        surchs = []
        total_surcharge = 0.0

        if trip["booking_type"] == "Airport Transfer":
            amt = random.choice([3500, 4000, 4500])
            surchs.append(("Airport Pickup/Drop", amt))
            total_surcharge += amt

        if datetime.fromisoformat(trip["pickup_datetime"]).hour >= 22 or \
           datetime.fromisoformat(trip["pickup_datetime"]).hour < 6:
            amt = round(base * 0.10, 0)
            surchs.append(("Night Surcharge", amt))
            total_surcharge += amt

        # Randomly add a few more surcharges
        n_extra = random.choices([0, 1, 2], weights=[0.55, 0.35, 0.10])[0]
        for _ in range(n_extra):
            stype = random.choice(SURCHARGE_TYPES)
            amt   = random.choice([500, 1000, 1500, 2000, 2500, 3000, 4000, 5000])
            surchs.append((stype, amt))
            total_surcharge += amt

        # Discounts
        discount = 0.0
        if random.random() < 0.15:
            discount = round(base * random.uniform(0.05, 0.25), 0)

        subtotal = base + total_surcharge - discount
        tax      = round(subtotal * 0.0, 0)   # no GST in most small rentals
        total    = subtotal + tax + trip.get("driver_allowance_pkr", 0)

        pay_method  = random.choices(PAYMENT_METHODS, weights=[0.35, 0.25, 0.15, 0.18, 0.07])[0]
        paid_amount = total if random.random() < 0.88 else round(total * random.uniform(0.20, 0.90), 0)
        outstanding = round(total - paid_amount, 0)

        issue_date  = trip["dropoff_datetime"][:10] if trip["status"] == "Completed" else trip["pickup_datetime"][:10]
        due_date    = str((datetime.fromisoformat(issue_date) + timedelta(days=7)).date())

        invoices.append({
            "invoice_id":         inv_id,
            "trip_id":            trip["trip_id"],
            "customer_id":        trip["customer_id"],
            "fleet_id":           trip["fleet_id"],
            "invoice_date":       issue_date,
            "due_date":           due_date,
            "base_fare_pkr":      base,
            "total_surcharge_pkr":round(total_surcharge, 0),
            "discount_pkr":       discount,
            "driver_allowance_pkr": trip.get("driver_allowance_pkr", 0),
            "tax_pkr":            tax,
            "total_amount_pkr":   round(total, 0),
            "paid_amount_pkr":    paid_amount,
            "outstanding_pkr":    outstanding,
            "payment_method":     pay_method,
            "payment_status":     "Paid" if outstanding == 0 else ("Partial" if paid_amount > 0 else "Unpaid"),
            "advance_paid_pct":   round(random.choice([0, 20, 50, 100]), 0),
        })

        # Line items
        line_items.append({
            "line_id":     make_id("LI", len(line_items) + 1, 7),
            "invoice_id":  inv_id,
            "charge_type": "Base Rental Fare",
            "description": f"{trip['booking_type']} – {trip['duration_days']} day(s)",
            "qty":         trip["duration_days"],
            "unit_price":  float(base / max(trip["duration_days"], 0.1)),
            "amount_pkr":  base,
        })
        for stype, amt in surchs:
            line_items.append({
                "line_id":     make_id("LI", len(line_items) + 1, 7),
                "invoice_id":  inv_id,
                "charge_type": "Surcharge",
                "description": stype,
                "qty":         1,
                "unit_price":  float(amt),
                "amount_pkr":  float(amt),
            })
        if discount > 0:
            line_items.append({
                "line_id":     make_id("LI", len(line_items) + 1, 7),
                "invoice_id":  inv_id,
                "charge_type": "Discount",
                "description": "Promotional / Loyalty Discount",
                "qty":         1,
                "unit_price":  float(-discount),
                "amount_pkr":  float(-discount),
            })

    return invoices, line_items
