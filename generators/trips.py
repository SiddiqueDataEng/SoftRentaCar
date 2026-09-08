"""
Generator: bookings / trips (rental travel data)
Produces:
  trips          – one row per rental booking
  trip_legs      – GPS-stop / waypoint detail for intercity trips
  telematics     – per-trip driver behaviour KPIs
"""

import random
import math
from datetime import date, timedelta, datetime
from generators.base import (
    make_id, random_datetime, jitter, pak_phone,
)
from config import (
    NUM_TRIPS, CITIES, INTERCITY_ROUTES, BOOKING_TYPES,
    VEHICLE_TYPES, SIM_START, SIM_END,
    DRIVER_BEHAVIOR_PROFILES,
)


def _haversine(lat1, lon1, lat2, lon2) -> float:
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _city_by_name(name: str) -> dict:
    return next((c for c in CITIES if c["name"] == name), CITIES[0])


def _pick_cities() -> tuple[dict, dict]:
    weights = [c["demand"] for c in CITIES]
    origin  = random.choices(CITIES, weights=weights)[0]
    dest    = random.choices(CITIES, weights=weights)[0]
    # avoid same-city for routes (allow for city rides)
    if random.random() < 0.60 or origin == dest:
        return origin, origin   # city ride
    return origin, dest


def _km_between(c1: dict, c2: dict) -> float:
    if c1["name"] == c2["name"]:
        return round(random.uniform(10, 80), 1)
    # Try known routes first
    for r in INTERCITY_ROUTES:
        if (r["from"] == c1["name"] and r["to"] == c2["name"]) or \
           (r["from"] == c2["name"] and r["to"] == c1["name"]):
            return round(jitter(r["km"], 0.05), 1)
    return round(_haversine(c1["lat"], c1["lon"], c2["lat"], c2["lon"]) * 1.3, 1)


# Seasonal demand multipliers (month 1-12)
_SEASON = {1: 0.90, 2: 0.88, 3: 0.95, 4: 1.00, 5: 1.05, 6: 1.10,
           7: 1.20, 8: 1.25, 9: 1.05, 10: 1.00, 11: 0.95, 12: 1.15}

# Booking type → typical duration (days) range
_DURATION = {
    "City Ride":             (0.3, 1),
    "Airport Transfer":      (0.1, 0.5),
    "Intercity":             (1, 3),
    "Wedding":               (1, 3),
    "Corporate":             (1, 7),
    "Tourism / Northern Areas": (3, 10),
    "Monthly Contract":      (28, 35),
    "Event":                 (0.5, 2),
}

_BOOKING_WEIGHTS = [0.25, 0.20, 0.18, 0.08, 0.12, 0.08, 0.05, 0.04]

_STATUSES = ["Completed", "Cancelled", "In Progress", "No Show"]
_STATUS_W  = [0.80, 0.09, 0.08, 0.03]


def generate_trips(
    vehicles: list[dict],
    drivers:  list[dict],
    customers: list[dict],
) -> tuple[list[dict], list[dict], list[dict]]:
    """
    Returns:
      trips
      trip_legs   (intercity waypoints)
      telematics  (per-trip driving KPIs)
    """
    trips      = []
    trip_legs  = []
    telems     = []

    active_vehicles = [v for v in vehicles if v["status"] != "Retired"]
    active_drivers  = [d for d in drivers  if d["active"]]
    active_customers= customers  # all customers eligible

    vt_lookup = {}
    for vt_idx, vt in enumerate(VEHICLE_TYPES, start=1):
        vt_id = f"VT{str(vt_idx).zfill(3)}"
        vt_lookup[vt_id] = vt

    # Track driver/vehicle usage for summary statistics
    driver_stats  = {d["driver_id"]: {"trips": 0, "km": 0, "accidents": 0, "complaints": 0} for d in active_drivers}
    customer_stats = {c["customer_id"]: 0 for c in active_customers}

    for trip_num in range(1, NUM_TRIPS + 1):
        trip_id = make_id("TR", trip_num, 6)

        # Pick a random booking datetime (weighted by season)
        month = random.choices(range(1, 13), weights=[_SEASON[m] for m in range(1, 13)])[0]
        year  = random.randint(SIM_START.year, SIM_END.year)
        if year == SIM_END.year:
            month = random.randint(1, SIM_END.month)
        day   = random.randint(1, 28)
        hour  = random.choices(range(0, 24),
                               weights=[0.5,0.3,0.2,0.2,0.3,0.8,2.5,4.0,4.5,3.5,
                                        3.0,2.8,2.5,2.5,2.8,3.2,4.0,4.5,3.5,2.5,
                                        2.0,1.5,1.0,0.7])[0]
        booking_dt = datetime(year, month, day, hour, random.randint(0,59))

        btype     = random.choices(BOOKING_TYPES, weights=_BOOKING_WEIGHTS)[0]
        dur_range = _DURATION.get(btype, (1, 2))
        duration_days = round(random.uniform(*dur_range), 2)

        pickup_dt   = booking_dt + timedelta(minutes=random.randint(30, 240))
        dropoff_dt  = pickup_dt + timedelta(days=duration_days)
        if dropoff_dt > datetime(SIM_END.year, SIM_END.month, 28, 23, 59):
            dropoff_dt = pickup_dt + timedelta(hours=random.randint(2, 8))

        # Vehicle & driver
        vehicle  = random.choice(active_vehicles)
        driver   = random.choice(active_drivers) if random.random() < 0.80 else None
        customer = random.choice(active_customers)

        # Cities / distance
        origin, dest = _pick_cities()
        if btype == "Airport Transfer":
            dest = _city_by_name("Islamabad") if random.random() < 0.70 else _city_by_name("Lahore")
        elif btype == "Intercity":
            origin = _city_by_name(random.choice(["Islamabad", "Lahore", "Karachi"]))
            dest   = _city_by_name(random.choice([c["name"] for c in CITIES if c["name"] != origin["name"]]))

        km_distance = _km_between(origin, dest)

        # Rate calculation
        vt    = vt_lookup.get(vehicle["vehicle_type_id"], VEHICLE_TYPES[0])
        daily = vehicle["daily_rate_pkr"]
        trip_fare = round(daily * duration_days + km_distance * vt["km_rate"], 0)
        if btype == "Monthly Contract":
            trip_fare = round(daily * 28 * 0.75, 0)   # 25% monthly discount
        driver_allowance = round(random.uniform(500, 3000), 0) if driver else 0

        status = random.choices(_STATUSES, weights=_STATUS_W)[0]
        if status == "Cancelled":
            trip_fare *= random.uniform(0, 0.30)   # cancellation fee only
            km_distance = 0

        # Telematics (only for completed trips with telematics vehicle)
        telem_row = None
        if status == "Completed" and vehicle.get("telematics_enabled") and driver:
            profile = DRIVER_BEHAVIOR_PROFILES.get(driver["behavior_profile"], DRIVER_BEHAVIOR_PROFILES["average"])
            events_total = max(1, int(km_distance / 5))  # rough event count per 5 km
            harsh_brakes   = int(events_total * profile["harsh_brake_rate"] * random.uniform(0.7, 1.3))
            harsh_accels   = int(events_total * profile["harsh_accel_rate"] * random.uniform(0.7, 1.3))
            idle_minutes   = int(duration_days * 24 * 60 * profile["idle_pct"] * random.uniform(0.5, 1.5))
            speeding_km    = round(km_distance * profile["speeding_pct"] * random.uniform(0.5, 1.5), 1)
            max_speed      = random.randint(80, 180)
            avg_speed      = round(km_distance / (duration_days * 22), 1) if duration_days > 0 else 0
            telem_score    = max(0, 100 - harsh_brakes*1.5 - harsh_accels - idle_minutes*0.05 - speeding_km*0.3)
            telem_score    = round(min(100, telem_score), 1)
            accident       = random.random() < (0.005 if profile == DRIVER_BEHAVIOR_PROFILES["dangerous"] else 0.001)
            complaint      = random.random() < 0.04
            rating         = round(random.gauss(4.2, 0.6), 1)
            rating         = max(1.0, min(5.0, rating))

            telem_row = {
                "telem_id":           make_id("TL", trip_num, 6),
                "trip_id":            trip_id,
                "driver_id":          driver["driver_id"],
                "vehicle_id":         vehicle["vehicle_id"],
                "trip_date":          str(pickup_dt.date()),
                "distance_km":        km_distance,
                "duration_hours":     round(duration_days * 24, 2),
                "avg_speed_kmh":      avg_speed,
                "max_speed_kmh":      max_speed,
                "harsh_brake_events": harsh_brakes,
                "harsh_accel_events": harsh_accels,
                "idle_time_minutes":  idle_minutes,
                "speeding_km":        speeding_km,
                "safety_score":       telem_score,
                "accident_occurred":  accident,
                "customer_rating":    rating,
                "complaint_filed":    complaint,
            }
            telems.append(telem_row)

            # Update driver aggregates
            if driver["driver_id"] in driver_stats:
                driver_stats[driver["driver_id"]]["trips"] += 1
                driver_stats[driver["driver_id"]]["km"]    += km_distance
                if accident:
                    driver_stats[driver["driver_id"]]["accidents"] += 1
                if complaint:
                    driver_stats[driver["driver_id"]]["complaints"] += 1

        if customer["customer_id"] in customer_stats:
            customer_stats[customer["customer_id"]] += 1

        trips.append({
            "trip_id":            trip_id,
            "fleet_id":           vehicle["fleet_id"],
            "vehicle_id":         vehicle["vehicle_id"],
            "driver_id":          driver["driver_id"] if driver else None,
            "customer_id":        customer["customer_id"],
            "booking_type":       btype,
            "booking_datetime":   str(booking_dt),
            "pickup_datetime":    str(pickup_dt),
            "dropoff_datetime":   str(dropoff_dt),
            "duration_days":      duration_days,
            "pickup_city":        origin["name"],
            "dropoff_city":       dest["name"],
            "pickup_lat":         round(origin["lat"] + random.gauss(0, 0.01), 6),
            "pickup_lon":         round(origin["lon"] + random.gauss(0, 0.01), 6),
            "dropoff_lat":        round(dest["lat"]   + random.gauss(0, 0.01), 6),
            "dropoff_lon":        round(dest["lon"]   + random.gauss(0, 0.01), 6),
            "distance_km":        km_distance,
            "trip_fare_pkr":      round(trip_fare, 0),
            "driver_allowance_pkr": driver_allowance,
            "with_driver":        driver is not None,
            "self_drive":         driver is None,
            "status":             status,
            "cancellation_reason": random.choice([
                "Customer Request", "Vehicle Issue", "Driver Unavailable",
                "Weather", "No Show", None
            ]) if status == "Cancelled" else None,
        })

        # Trip legs (waypoints for intercity > 100 km)
        if km_distance > 100 and status == "Completed":
            num_legs = random.randint(2, 5)
            seg_km   = km_distance / num_legs
            for leg in range(1, num_legs + 1):
                lat = origin["lat"] + (dest["lat"] - origin["lat"]) * leg / num_legs + random.gauss(0, 0.05)
                lon = origin["lon"] + (dest["lon"] - origin["lon"]) * leg / num_legs + random.gauss(0, 0.05)
                trip_legs.append({
                    "leg_id":        make_id("LG", len(trip_legs) + 1, 7),
                    "trip_id":       trip_id,
                    "leg_sequence":  leg,
                    "city":          f"Waypoint-{leg}",
                    "lat":           round(lat, 6),
                    "lon":           round(lon, 6),
                    "km_so_far":     round(seg_km * leg, 1),
                    "stop_type":     random.choice(["Fuel Stop", "Rest Stop", "Toll", "Waypoint"]),
                    "stop_duration_min": random.randint(5, 45),
                })

    # Propagate driver stats back
    for d in drivers:
        s = driver_stats.get(d["driver_id"], {})
        d["total_trips"]      = s.get("trips", 0)
        d["total_km_driven"]  = round(s.get("km", 0), 1)
        d["accidents_count"]  = s.get("accidents", 0)
        d["complaints_count"] = s.get("complaints", 0)

    # Propagate customer booking counts
    for c in customers:
        c["total_bookings"] = customer_stats.get(c["customer_id"], 0)

    return trips, trip_legs, telems
