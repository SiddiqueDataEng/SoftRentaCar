# 🚗 Pakistan Rent-a-Car — Synthetic Data Generator

A complete, realistic synthetic dataset for a **Pakistani car rental business**, purpose-built for:

- **Data Engineering** – pipeline ingestion, data modelling, warehouse design
- **Analytical Engineering** – dbt models, KPI dashboards, OLAP cubes
- **ML / AI** – Driver Behavior Analytics, Demand Prediction, Dynamic Pricing, Predictive Maintenance
---

## Quick Start

```bash
# Install dependencies
pip install faker pandas numpy pyarrow rich python-dateutil

# Generate all data
python generate_data.py
```

Output appears in:
```
data/
  csv/        ← 16 CSV files (human-readable, Excel-compatible)
  parquet/    ← 16 Parquet files (Spark / DuckDB / BigQuery optimised)
  json/       ← 16 JSON sample files (first 500 rows each)
```

---

## What's Generated

| Table | Rows | Description |
|-------|------|-------------|
| `fleets` | 4 | Rental companies |
| `vehicle_types` | 18 | Vehicle catalogue with rates |
| `vehicles` | 120 | Individual cars |
| `vehicle_attributes` | 1,320 | EAV specs (airbags, sunroof, etc.) |
| `drivers` | 60 | Drivers with behavior profiles |
| `staff` | 30 | Non-driver employees |
| `customers` | 2,000 | Individual & corporate renters |
| `trips` | 18,000 | Core rental fact table |
| `trip_legs` | ~23,000 | Intercity waypoints / GPS stops |
| `telematics` | ~7,800 | Per-trip driving KPIs |
| `invoices` | ~17,400 | Billing documents |
| `billing_line_items` | ~35,000 | Itemised charges |
| `fuel_logs` | ~14,400 | Fuel consumption per trip |
| `operating_expenses` | 2,160 | Monthly fleet costs |
| `maintenance` | 800 | Vehicle service records |
| `rate_cards` | 576 | Fleet × type × booking type rates |

**Total: ~123,000 rows across 16 tables**

---

## Vehicle Segments (Real PKR Rates)

| Segment | Examples | Daily Rate (PKR) |
|---------|----------|-----------------|
| Economy Mini | Suzuki Alto | 3,500 – 5,000 |
| Economy Hatchback | Suzuki Wagon R, Cultus | 4,500 – 6,000 |
| Economy Sedan | Toyota Corolla GLI/Altis | 5,000 – 9,000 |
| Economy Sedan | Honda City | 6,000 – 8,000 |
| Executive Sedan | Honda Civic 11th Gen | 9,000 – 12,000 |
| Executive Crossover | Honda BR-V | 6,000 – 8,500 |
| Executive SUV | Hyundai Tucson, MG HS | 12,000 – 16,000 |
| Premium 4×4 | Toyota Hilux Revo | 16,000 – 20,000 |
| Premium 4×4 | Toyota Fortuner | 17,000 – 22,000 |
| Luxury 4×4 | Toyota Land Cruiser Prado | 22,000 – 28,000 |
| Luxury Full-Size | Land Cruiser V8 / ZX LC300 | 25,000 – 40,000 |
| Luxury Sedan | Audi A5/A6 | 28,000 – 35,000 |
| Luxury Sedan | Mercedes E-Class / S-Class | 35,000 – 80,000 |
| Ultra Luxury | Range Rover Autobiography | 100,000 – 175,000 |
| Van / MPV | Suzuki APV | 5,000 – 7,000 |
| Minibus | Toyota Hiace Grand Cabin | 10,000 – 16,000 |
| Coach | Toyota Coaster 30-seater | 15,000 – 20,000 |

---

## ML/AI Use Cases

### 🚦 Driver Behavior Analytics (Safety & Efficiency)
**Tables**: `telematics`, `drivers`, `trips`

Key features:
- `harsh_brake_events`, `harsh_accel_events` — aggressive driving signals
- `idle_time_minutes` — fuel waste / inefficiency
- `speeding_km` — safety risk
- `safety_score` — composite 0–100 score
- `behavior_profile` — ground-truth label (excellent / good / average / poor / dangerous)

Use for: driver coaching, accident risk prediction, fuel savings coaching.

### 📈 Dynamic Fleet Optimization & Demand Prediction
**Tables**: `trips`, `rate_cards`, `customers`, `vehicles`

Key features:
- `pickup_city`, `pickup_lat/lon` — heat-map demand zones
- `booking_datetime` — temporal patterns (hour, day, season)
- `booking_type` — segment-level demand
- `status` — utilisation gaps

Use for: sub-1-hour delivery SLAs, fleet rebalancing, peak pricing.

### 🔧 Predictive Maintenance
**Tables**: `maintenance`, `fuel_logs`, `vehicles`, `telematics`

Key features:
- `odometer_km`, `next_due_km` — service interval tracking
- `maintenance_type`, `total_cost_pkr` — failure cost modelling
- `fuel_efficiency_kmpl` — degradation signal
- `harsh_brake_events` — brake wear proxy

### 💰 Revenue & Billing Analytics
**Tables**: `invoices`, `billing_line_items`, `operating_expenses`, `fuel_logs`

Key metrics:
- Revenue per vehicle per day
- Outstanding receivables by fleet
- Fuel cost as % of revenue
- Surcharge contribution analysis

---

## Project Structure

```
rent-a-car/
├── config.py                  # All constants: rates, cities, vehicle types
├── generate_data.py           # Main orchestrator
├── generators/
│   ├── base.py                # Shared helpers (names, IDs, dates)
│   ├── fleets.py              # Fleets, vehicle types, vehicles
│   ├── staff.py               # Drivers and staff
│   ├── customers.py           # Customer profiles
│   ├── trips.py               # Trips, legs, telematics
│   ├── billing.py             # Invoices and line items
│   ├── fuel.py                # Fuel logs and operating expenses
│   ├── maintenance.py         # Maintenance records
│   └── rates.py               # Rate cards
├── data/
│   ├── csv/                   # ← CSV output
│   ├── parquet/               # ← Parquet output
│   └── json/                  # ← JSON samples
├── DATA_DICTIONARY.md         # Full column-level documentation
└── README.md
```

---

## Reproducibility

Set `RANDOM_SEED = 42` in `config.py`. Change `NUM_TRIPS`, `NUM_VEHICLES`, etc. to scale up or down.

---

## Data Sources (Real-World Rates)

- [haxnrentacar.com](https://haxnrentacar.com) — fleet rates Toyota Corolla PKR 5,000 to Range Rover PKR 150,000
- [carsrental247.com](https://carsrental247.com) — self-drive rates Honda Civic PKR 9,000–12,000 / Prado PKR 22,000
- [rentka.co](https://rentka.co) — chauffeur rates starting PKR 4,500/day, 20% advance policy
- [carrentpk.com](http://carrentpk.com) — economy rates Suzuki Alto PKR 1,500–3,500 / Corolla PKR 2,800+
