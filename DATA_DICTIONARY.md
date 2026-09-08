# Pakistan Rent-a-Car – Data Dictionary

Generated dataset for Data Engineering, Analytical Engineering, and ML/AI projects.
Modeled after real Pakistani operators.

---

## Schema Overview (Star / Snowflake)

```
fleets ──┬── vehicles ──┬── trips ──┬── invoices ──── billing_line_items
         │              │           ├── telematics
         │    vehicle_types         ├── trip_legs
         │    vehicle_attributes    └── fuel_logs
         │
         ├── drivers
         ├── staff
         └── operating_expenses

customers ──── trips
rate_cards ──── (pricing reference)
maintenance ──── vehicles
```

---

## Tables

### `fleets`
4 rows — one per rental company

| Column | Type | Description |
|--------|------|-------------|
| fleet_id | string | PK – e.g. `FL001` |
| fleet_name | string | Company name |
| city | string | HQ city |
| website | string | Website domain |
| secp_registered | bool | SECP registration status |
| ntn_registered | bool | NTN tax registration |
| established_year | int | Year founded |
| focus_segment | string | Business focus (self_drive, chauffeur_driven, etc.) |
| total_vehicles | int | Vehicle count (aggregated) |
| active | bool | Operating status |

---

### `vehicle_types`
18 rows — dimension / catalogue

| Column | Type | Description |
|--------|------|-------------|
| vehicle_type_id | string | PK – `VT001`…`VT018` |
| category | string | Economy / Executive / Premium_4x4 / Luxury_4x4 / Luxury_Sedan / Ultra_Luxury / Van_Minibus |
| sub_type | string | Mini / Hatchback / Sedan / SUV / Grand_Cabin / Coaster etc. |
| make | string | Suzuki / Toyota / Honda / MG / Hyundai / Audi / Mercedes-Benz / Land Rover |
| seats | int | Passenger capacity |
| fuel_type | string | Petrol / Diesel / CNG |
| transmission | string | Manual / Automatic |
| daily_rate_min_pkr | int | Minimum daily rate (PKR) |
| daily_rate_max_pkr | int | Maximum daily rate (PKR) |
| hourly_rate_pkr | int | Per-hour rate (PKR) |
| km_rate_pkr | int | Per-km surcharge (PKR) |
| fuel_eff_min_kmpl | float | Min fuel efficiency (km/l) |
| fuel_eff_max_kmpl | float | Max fuel efficiency (km/l) |
| security_deposit_pkr | int | Refundable deposit (PKR) |

**Rate reference (real market, mid-2025):**
| Segment | Daily Rate (PKR) |
|---------|-----------------|
| Suzuki Alto | 3,500 – 5,000 |
| Toyota Corolla | 5,000 – 9,000 |
| Honda Civic | 9,000 – 12,000 |
| Toyota Prado | 22,000 – 28,000 |
| Land Cruiser V8 | 25,000 – 40,000 |
| Mercedes E-Class | 35,000 – 80,000 |
| Range Rover Autobiography | 100,000 – 175,000 |

---

### `vehicles`
120 rows — one per car

| Column | Type | Description |
|--------|------|-------------|
| vehicle_id | string | PK – `VH00001`…`VH00120` |
| fleet_id | string | FK → fleets |
| vehicle_type_id | string | FK → vehicle_types |
| make / model / year | string/int | Vehicle identity |
| registration_no | string | Pakistan number plate |
| color | string | Vehicle colour |
| fuel_type / transmission | string | From type catalogue |
| seats | int | Capacity |
| odometer_km | int | Current odometer reading |
| purchase_date | date | When fleet acquired it |
| daily_rate_pkr | int | Fleet-specific daily rate |
| hourly_rate_pkr | int | Hourly rate |
| km_rate_pkr | int | Per-km rate |
| insurance_expiry | date | Insurance renewal date |
| fitness_cert_expiry | date | Route Permit / Fitness cert |
| status | string | Available / On Trip / Under Maintenance / Reserved / Retired |
| condition_rating | string | Excellent / Good / Fair / Needs Attention |
| gps_enabled | bool | GPS fitted |
| telematics_enabled | bool | OBD/telematics device fitted |
| ac_working | bool | AC functional |

---

### `vehicle_attributes`
1,320 rows — EAV extra specs per vehicle

| Column | Type | Description |
|--------|------|-------------|
| attr_id | string | PK |
| vehicle_id | string | FK → vehicles |
| attr_name | string | engine_cc / abs / airbags / central_locking / reverse_camera / sunroof / push_start / infotainment / etc. |
| attr_value | string | Attribute value (as string) |

---

### `drivers`
60 rows

| Column | Type | Description |
|--------|------|-------------|
| driver_id | string | PK – `DR0001`…`DR0060` |
| fleet_id | string | FK → fleets |
| full_name / gender / dob | string/date | Demographics |
| cnic | string | National ID (DDDDD-DDDDDDD-D) |
| phone | string | Pakistani mobile number |
| license_no | string | Driving licence number |
| license_expiry | date | Licence expiry |
| hire_date | date | Joining date |
| experience_years | int | Years of driving experience |
| base_salary_pkr | int | Monthly salary (PKR) |
| behavior_profile | string | excellent / good / average / poor / dangerous |
| harsh_brake_rate | float | Baseline harsh-brake events per km |
| harsh_accel_rate | float | Baseline harsh-acceleration events per km |
| idle_time_pct | float | Fraction of trip time spent idling |
| speeding_pct | float | Fraction of km driven above speed limit |
| total_trips | int | Aggregated trip count |
| total_km_driven | float | Aggregated km driven |
| accidents_count | int | Total accidents |
| complaints_count | int | Total customer complaints |
| ratings_avg | float | Average customer rating (1–5) |
| active | bool | Currently employed |

---

### `staff`
30 rows — non-driver employees

| Column | Type | Description |
|--------|------|-------------|
| staff_id | string | PK |
| fleet_id | string | FK → fleets |
| full_name / gender / dob | string/date | Demographics |
| role | string | Fleet Manager / Accountant / Dispatcher / Mechanic / etc. |
| hire_date | date | Joining date |
| base_salary_pkr | int | Monthly salary (PKR) |
| active | bool | Currently employed |

---

### `customers`
2,000 rows

| Column | Type | Description |
|--------|------|-------------|
| customer_id | string | PK – `CU00001`…`CU02000` |
| full_name / gender / dob | string/date | Demographics |
| cnic | string | National ID |
| nationality | string | Pakistani / British Pakistani / UAE / etc. |
| phone / email | string | Contact |
| city | string | Home city |
| customer_type | string | Individual / Corporate / Tourist / Overseas Pakistani / Government |
| license_no | string | Driving licence (nullable) |
| has_own_license | bool | Eligibility for self-drive |
| loyalty_points | int | Accumulated loyalty points |
| total_bookings | int | Aggregated booking count |
| registration_date | date | Account creation date |

---

### `trips`
18,000 rows — **core fact table**

| Column | Type | Description |
|--------|------|-------------|
| trip_id | string | PK – `TR000001`…`TR018000` |
| fleet_id | string | FK → fleets |
| vehicle_id | string | FK → vehicles |
| driver_id | string | FK → drivers (null for self-drive) |
| customer_id | string | FK → customers |
| booking_type | string | City Ride / Airport Transfer / Intercity / Wedding / Corporate / Tourism / Monthly Contract / Event |
| booking_datetime | datetime | When booking was made |
| pickup_datetime | datetime | Actual pickup time |
| dropoff_datetime | datetime | Actual drop-off time |
| duration_days | float | Trip duration in days |
| pickup_city / dropoff_city | string | Origin and destination |
| pickup_lat / pickup_lon | float | GPS coordinates |
| dropoff_lat / dropoff_lon | float | GPS coordinates |
| distance_km | float | Total distance driven |
| trip_fare_pkr | float | Calculated fare |
| driver_allowance_pkr | float | Driver daily allowance |
| with_driver / self_drive | bool | Rental mode |
| status | string | Completed / Cancelled / In Progress / No Show |
| cancellation_reason | string | Reason if cancelled |

---

### `trip_legs`
~23,000 rows — waypoints for intercity trips (>100 km)

| Column | Type | Description |
|--------|------|-------------|
| leg_id | string | PK |
| trip_id | string | FK → trips |
| leg_sequence | int | Stop order |
| lat / lon | float | GPS position |
| km_so_far | float | Cumulative distance |
| stop_type | string | Fuel Stop / Rest Stop / Toll / Waypoint |
| stop_duration_min | int | Time spent at stop (minutes) |

---

### `telematics`
~7,800 rows — driver behaviour per completed trip (telematics-enabled vehicles only)

| Column | Type | Description |
|--------|------|-------------|
| telem_id | string | PK |
| trip_id | string | FK → trips |
| driver_id | string | FK → drivers |
| vehicle_id | string | FK → vehicles |
| trip_date | date | Date of trip |
| distance_km | float | Distance covered |
| duration_hours | float | Duration |
| avg_speed_kmh | float | Average speed |
| max_speed_kmh | int | Maximum recorded speed |
| harsh_brake_events | int | Count of hard braking events |
| harsh_accel_events | int | Count of hard acceleration events |
| idle_time_minutes | int | Total idle engine time |
| speeding_km | float | Distance above speed limit |
| safety_score | float | Composite score 0–100 |
| accident_occurred | bool | Whether an accident was recorded |
| customer_rating | float | Rating given by customer (1–5) |
| complaint_filed | bool | Whether a complaint was filed |

**Safety score formula:**
`score = 100 − (harsh_brakes × 1.5) − harsh_accels − (idle_min × 0.05) − (speeding_km × 0.3)`

---

### `invoices`
~17,400 rows

| Column | Type | Description |
|--------|------|-------------|
| invoice_id | string | PK |
| trip_id | string | FK → trips |
| customer_id | string | FK → customers |
| fleet_id | string | FK → fleets |
| invoice_date | date | Issue date |
| due_date | date | Payment due |
| base_fare_pkr | float | Core rental fare |
| total_surcharge_pkr | float | All surcharges combined |
| discount_pkr | float | Discount applied |
| driver_allowance_pkr | float | Driver cost passed to customer |
| tax_pkr | float | GST/tax |
| total_amount_pkr | float | Grand total |
| paid_amount_pkr | float | Amount collected |
| outstanding_pkr | float | Balance due |
| payment_method | string | Cash / JazzCash / EasyPaisa / Bank Transfer / Card (POS) |
| payment_status | string | Paid / Partial / Unpaid |
| advance_paid_pct | float | Advance % paid at booking |

---

### `billing_line_items`
~35,000 rows — itemised invoice lines

| Column | Type | Description |
|--------|------|-------------|
| line_id | string | PK |
| invoice_id | string | FK → invoices |
| charge_type | string | Base Rental Fare / Surcharge / Discount |
| description | string | Human-readable description |
| qty | float | Quantity (days / 1) |
| unit_price | float | Rate per unit |
| amount_pkr | float | Line total (negative for discounts) |

---

### `fuel_logs`
~14,400 rows — one per completed trip

| Column | Type | Description |
|--------|------|-------------|
| fuel_id | string | PK |
| trip_id | string | FK → trips |
| vehicle_id | string | FK → vehicles |
| fleet_id | string | FK → fleets |
| driver_id | string | FK → drivers (nullable) |
| fill_date | date | Date of fuel purchase |
| fuel_type | string | Petrol / Diesel / CNG |
| litres_filled | float | Litres consumed |
| price_per_litre_pkr | float | PKR/litre (historical price) |
| fuel_cost_pkr | float | Total fuel cost |
| km_driven | float | KM this fill covers |
| fuel_efficiency_kmpl | float | Effective efficiency |
| odometer_at_fill | int | Odometer reading |
| fill_station | string | Station name |
| paid_by | string | Driver Cash / Fleet Card / Petty Cash |

---

### `operating_expenses`
2,160 rows — monthly per fleet

| Column | Type | Description |
|--------|------|-------------|
| expense_id | string | PK |
| fleet_id | string | FK → fleets |
| expense_month | date | Month (YYYY-MM-01) |
| category | string | Staff Salaries / Driver Salaries / Office Rent / Utilities / Marketing / Insurance Premium / Depreciation / Miscellaneous / Communication / Parking |
| amount_pkr | float | Monthly expense (PKR) |
| description | string | Human-readable label |
| approved_by | string | Approving role |

---

### `maintenance`
800 rows

| Column | Type | Description |
|--------|------|-------------|
| maint_id | string | PK |
| vehicle_id | string | FK → vehicles |
| fleet_id | string | FK → fleets |
| maintenance_type | string | Oil Change / Tyre Replacement / Brake Pad / AC Service / Battery / Engine Tune-Up / Accident Repair / etc. |
| maintenance_date | date | Date of service |
| odometer_km | int | KM at time of service |
| workshop | string | Service center name |
| parts_cost_pkr | float | Parts cost |
| labour_cost_pkr | float | Labour cost |
| total_cost_pkr | float | Total cost |
| status | string | Completed / In Progress / Scheduled / Warranty Claim |
| next_due_km | int | Next service trigger KM |
| next_due_date | date | Next service date |
| technician_name | string | Technician assigned |
| remarks | string | Notes |

---

### `rate_cards`
576 rows — (4 fleets × 18 vehicle types × 8 booking types)

| Column | Type | Description |
|--------|------|-------------|
| rate_id | string | PK |
| fleet_id | string | FK → fleets |
| vehicle_type_id | string | FK → vehicle_types |
| booking_type | string | Booking category |
| daily_rate_pkr | float | Applicable daily rate |
| hourly_rate_pkr | int | Hourly rate |
| km_rate_pkr | int | Per-km charge |
| outstation_mult | float | Multiplier for outstation trips |
| night_surcharge_pct | int | Night surcharge % |
| airport_surcharge_pkr | int | Fixed airport surcharge |
| security_deposit_pkr | int | Refundable deposit |
| min_hours | int | Minimum booking hours |
| cancellation_fee_pct | int | Cancellation penalty % |
| fuel_included | bool | Whether fuel is included |
| driver_included | bool | Whether driver is included |
| effective_from / effective_to | date | Rate validity window |

---

## ML/AI Use Cases

| Use Case | Key Tables | Target Variable |
|----------|-----------|----------------|
| Driver Behavior Scoring | telematics, drivers | safety_score |
| Accident Prediction | telematics, drivers, trips | accident_occurred |
| Demand Forecasting | trips, rate_cards | trip_count per zone/hour |
| Dynamic Pricing | trips, invoices, rate_cards | optimal_rate_pkr |
| Maintenance Prediction | maintenance, fuel_logs, vehicles | next_failure_date |
| Revenue Forecasting | invoices, operating_expenses | net_revenue_pkr |
| Customer Churn | customers, trips, invoices | churn_flag |
| Fleet Utilisation Optimisation | trips, vehicles, fleets | utilisation_rate |
| Fuel Efficiency Anomaly Detection | fuel_logs, telematics | anomaly_flag |
| Payment Default Prediction | invoices, customers | outstanding_pkr > 0 |
