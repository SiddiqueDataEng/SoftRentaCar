"""SQL Analytics — 50+ Production-Grade Queries"""
import streamlit as st
import pandas as pd
import duckdb
import plotly.graph_objects as go
from page_modules._shared import (
    inject, get_data, fmt, sec, alert_box, dark_layout,
    BRAND, NAVY, STEEL, GREEN, AMBER, ORANGE, TEXT, GRID, BG, COLORS,
)
from app.storytelling import insight

inject()
dfs = get_data()

st.markdown(f'<div style="font-size:1.5rem;font-weight:800;color:{BRAND};margin-bottom:4px;">🔍 SQL Analytics</div>', unsafe_allow_html=True)
st.markdown(f'<div style="font-size:.8rem;color:#5a7a96;">50+ production-grade SQL queries — Window Functions, CTEs, Analytical Functions, aggregations and more</div>', unsafe_allow_html=True)
st.markdown("<hr style='border-color:#1e2f44;margin:6px 0 14px 0'>", unsafe_allow_html=True)

# ── Register tables in DuckDB in-memory ───────────────────────────────
@st.cache_resource
def get_db(dfs: dict):
    conn = duckdb.connect(":memory:")
    for name, df in dfs.items():
        conn.register(name, df)
    return conn

conn = get_db(dfs)

# ── SQL Query catalogue ────────────────────────────────────────────────
QUERIES = {

    # ── REVENUE & BILLING ─────────────────────────────────────────────
    "01 · Monthly Revenue with MoM Growth (Window)": {
        "category": "Revenue",
        "description": "Monthly billed revenue with month-over-month growth % using LAG window function.",
        "sql": """
WITH monthly AS (
    SELECT
        DATE_TRUNC('month', invoice_date)          AS month,
        SUM(total_amount_pkr)                       AS total_billed,
        SUM(paid_amount_pkr)                        AS total_collected,
        SUM(outstanding_pkr)                        AS outstanding,
        COUNT(*)                                    AS invoice_count
    FROM invoices
    GROUP BY 1
)
SELECT
    month,
    total_billed,
    total_collected,
    outstanding,
    invoice_count,
    ROUND(
        (total_billed - LAG(total_billed) OVER (ORDER BY month))
        / NULLIF(LAG(total_billed) OVER (ORDER BY month), 0) * 100, 2
    )                                               AS mom_growth_pct,
    SUM(total_billed) OVER (ORDER BY month)        AS cumulative_revenue
FROM monthly
ORDER BY month
""",
    },

    "02 · Revenue by Fleet with Rank (Window)": {
        "category": "Revenue",
        "description": "Revenue per fleet ranked using RANK() and DENSE_RANK(), with % share.",
        "sql": """
SELECT
    f.fleet_name,
    ROUND(SUM(i.total_amount_pkr), 0)               AS total_revenue,
    ROUND(SUM(i.paid_amount_pkr), 0)                AS collected,
    ROUND(AVG(i.total_amount_pkr), 0)               AS avg_invoice,
    COUNT(i.invoice_id)                             AS invoice_count,
    RANK()       OVER (ORDER BY SUM(i.total_amount_pkr) DESC) AS revenue_rank,
    DENSE_RANK() OVER (ORDER BY SUM(i.total_amount_pkr) DESC) AS dense_rank,
    ROUND(
        SUM(i.total_amount_pkr)
        / SUM(SUM(i.total_amount_pkr)) OVER () * 100, 2
    )                                               AS revenue_share_pct
FROM invoices i
JOIN fleets f ON i.fleet_id = f.fleet_id
GROUP BY f.fleet_name
ORDER BY total_revenue DESC
""",
    },

    "03 · Running Total Revenue by Month (Window)": {
        "category": "Revenue",
        "description": "Cumulative revenue running total with rolling 3-month average.",
        "sql": """
WITH monthly AS (
    SELECT
        DATE_TRUNC('month', invoice_date) AS month,
        SUM(total_amount_pkr)              AS monthly_rev
    FROM invoices
    GROUP BY 1
)
SELECT
    month,
    monthly_rev,
    SUM(monthly_rev) OVER (ORDER BY month ROWS UNBOUNDED PRECEDING)    AS running_total,
    AVG(monthly_rev) OVER (ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS rolling_3m_avg,
    MAX(monthly_rev) OVER (ORDER BY month ROWS BETWEEN 5 PRECEDING AND CURRENT ROW) AS rolling_6m_peak
FROM monthly
ORDER BY month
""",
    },

    "04 · Revenue Percentile Buckets (NTILE)": {
        "category": "Revenue",
        "description": "Classify invoices into quartiles by value using NTILE().",
        "sql": """
SELECT
    invoice_id,
    customer_id,
    total_amount_pkr,
    NTILE(4) OVER (ORDER BY total_amount_pkr)        AS quartile,
    NTILE(10) OVER (ORDER BY total_amount_pkr)       AS decile,
    PERCENT_RANK() OVER (ORDER BY total_amount_pkr)  AS percent_rank,
    CUME_DIST()    OVER (ORDER BY total_amount_pkr)  AS cumulative_dist
FROM invoices
WHERE payment_status = 'Paid'
ORDER BY total_amount_pkr DESC
LIMIT 100
""",
    },

    "05 · Payment Method Revenue Share (CTE)": {
        "category": "Revenue",
        "description": "CTE to compute revenue and outstanding by payment method.",
        "sql": """
WITH payment_summary AS (
    SELECT
        payment_method,
        COUNT(*)                          AS invoice_count,
        SUM(total_amount_pkr)             AS total_billed,
        SUM(paid_amount_pkr)              AS total_paid,
        SUM(outstanding_pkr)              AS total_outstanding
    FROM invoices
    GROUP BY payment_method
),
totals AS (
    SELECT SUM(total_billed) AS grand_total FROM payment_summary
)
SELECT
    ps.payment_method,
    ps.invoice_count,
    ps.total_billed,
    ps.total_paid,
    ps.total_outstanding,
    ROUND(ps.total_paid / NULLIF(ps.total_billed, 0) * 100, 2) AS collection_rate_pct,
    ROUND(ps.total_billed / t.grand_total * 100, 2)            AS share_of_total_pct
FROM payment_summary ps, totals t
ORDER BY total_billed DESC
""",
    },

    "06 · Invoice Aging Buckets (CASE + CTE)": {
        "category": "Revenue",
        "description": "AR aging analysis: Current, 1-30d, 31-60d, 61-90d, 90d+.",
        "sql": """
WITH aging AS (
    SELECT
        invoice_id,
        customer_id,
        total_amount_pkr,
        outstanding_pkr,
        due_date,
        DATE_DIFF('day', due_date, DATE '2026-07-01') AS days_overdue,
        CASE
            WHEN DATE_DIFF('day', due_date, DATE '2026-07-01') <= 0  THEN 'Current'
            WHEN DATE_DIFF('day', due_date, DATE '2026-07-01') <= 30 THEN '1-30 Days'
            WHEN DATE_DIFF('day', due_date, DATE '2026-07-01') <= 60 THEN '31-60 Days'
            WHEN DATE_DIFF('day', due_date, DATE '2026-07-01') <= 90 THEN '61-90 Days'
            ELSE '90+ Days'
        END AS aging_bucket
    FROM invoices
    WHERE outstanding_pkr > 0
)
SELECT
    aging_bucket,
    COUNT(*)                       AS invoices,
    ROUND(SUM(outstanding_pkr), 0) AS outstanding_pkr,
    ROUND(AVG(outstanding_pkr), 0) AS avg_outstanding
FROM aging
GROUP BY aging_bucket
ORDER BY
    CASE aging_bucket
        WHEN 'Current'    THEN 1
        WHEN '1-30 Days'  THEN 2
        WHEN '31-60 Days' THEN 3
        WHEN '61-90 Days' THEN 4
        ELSE 5
    END
""",
    },

    "07 · YoY Revenue Comparison (PIVOT-style CTE)": {
        "category": "Revenue",
        "description": "Year-over-year revenue comparison using conditional aggregation.",
        "sql": """
SELECT
    DATE_PART('month', invoice_date)                        AS month_num,
    STRFTIME(invoice_date, '%b')                            AS month_name,
    ROUND(SUM(CASE WHEN YEAR(invoice_date) = 2022 THEN total_amount_pkr ELSE 0 END), 0) AS rev_2022,
    ROUND(SUM(CASE WHEN YEAR(invoice_date) = 2023 THEN total_amount_pkr ELSE 0 END), 0) AS rev_2023,
    ROUND(SUM(CASE WHEN YEAR(invoice_date) = 2024 THEN total_amount_pkr ELSE 0 END), 0) AS rev_2024,
    ROUND(SUM(CASE WHEN YEAR(invoice_date) = 2025 THEN total_amount_pkr ELSE 0 END), 0) AS rev_2025,
    ROUND(SUM(CASE WHEN YEAR(invoice_date) = 2026 THEN total_amount_pkr ELSE 0 END), 0) AS rev_2026
FROM invoices
GROUP BY 1, 2
ORDER BY 1
""",
    },

    # ── TRIPS & OPERATIONS ────────────────────────────────────────────
    "08 · Trip Duration Percentiles (PERCENTILE_CONT)": {
        "category": "Operations",
        "description": "P25, P50, P75, P90, P99 of trip duration and distance.",
        "sql": """
SELECT
    booking_type,
    COUNT(*)                                                  AS trip_count,
    ROUND(AVG(duration_days), 3)                              AS avg_duration_days,
    ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY duration_days), 3) AS p25,
    ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY duration_days), 3) AS p50_median,
    ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY duration_days), 3) AS p75,
    ROUND(PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY duration_days), 3) AS p90,
    ROUND(PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY duration_days), 3) AS p99,
    ROUND(AVG(distance_km), 1)                                AS avg_km,
    ROUND(AVG(trip_fare_pkr), 0)                              AS avg_fare_pkr
FROM trips
WHERE status = 'Completed'
GROUP BY booking_type
ORDER BY trip_count DESC
""",
    },

    "09 · Hourly Demand Heatmap Data": {
        "category": "Operations",
        "description": "Trip count by day-of-week × hour for demand heatmap visualisation.",
        "sql": """
SELECT
    STRFTIME(pickup_datetime, '%A')      AS day_of_week,
    DATE_PART('hour', pickup_datetime)   AS hour_of_day,
    COUNT(*)                             AS trip_count,
    ROUND(AVG(trip_fare_pkr), 0)         AS avg_fare,
    SUM(trip_fare_pkr)                   AS total_revenue
FROM trips
WHERE status = 'Completed'
GROUP BY 1, 2
ORDER BY
    CASE STRFTIME(pickup_datetime, '%A')
        WHEN 'Monday'    THEN 1 WHEN 'Tuesday'   THEN 2
        WHEN 'Wednesday' THEN 3 WHEN 'Thursday'  THEN 4
        WHEN 'Friday'    THEN 5 WHEN 'Saturday'  THEN 6
        ELSE 7
    END, 2
""",
    },

    "10 · Top Routes by Revenue (CTE + RANK)": {
        "category": "Operations",
        "description": "Intercity route revenue ranking with trip volume and avg fare.",
        "sql": """
WITH route_stats AS (
    SELECT
        pickup_city || ' → ' || dropoff_city   AS route,
        COUNT(*)                                AS trip_count,
        ROUND(SUM(trip_fare_pkr), 0)            AS total_revenue,
        ROUND(AVG(trip_fare_pkr), 0)            AS avg_fare,
        ROUND(AVG(distance_km), 1)              AS avg_km,
        ROUND(AVG(duration_days), 2)            AS avg_duration
    FROM trips
    WHERE status = 'Completed'
      AND pickup_city <> dropoff_city
    GROUP BY route
)
SELECT
    route,
    trip_count,
    total_revenue,
    avg_fare,
    avg_km,
    avg_duration,
    RANK() OVER (ORDER BY total_revenue DESC)   AS revenue_rank,
    RANK() OVER (ORDER BY trip_count DESC)      AS volume_rank
FROM route_stats
ORDER BY total_revenue DESC
LIMIT 20
""",
    },

    "11 · Cancellation Rate by City & Month": {
        "category": "Operations",
        "description": "Monthly cancellation rate per city — identifying problem locations.",
        "sql": """
SELECT
    pickup_city,
    DATE_TRUNC('month', pickup_datetime)    AS month,
    COUNT(*)                                AS total_trips,
    SUM(CASE WHEN status = 'Cancelled' THEN 1 ELSE 0 END) AS cancellations,
    ROUND(
        SUM(CASE WHEN status = 'Cancelled' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2
    )                                       AS cancellation_rate_pct
FROM trips
GROUP BY 1, 2
HAVING COUNT(*) >= 10
ORDER BY cancellation_rate_pct DESC
LIMIT 30
""",
    },

    "12 · Consecutive Booking Gaps (LAG/LEAD)": {
        "category": "Operations",
        "description": "Gap between consecutive bookings per customer using LAG to find churning patterns.",
        "sql": """
WITH customer_trips AS (
    SELECT
        customer_id,
        pickup_datetime,
        LAG(pickup_datetime)  OVER (PARTITION BY customer_id ORDER BY pickup_datetime) AS prev_trip,
        LEAD(pickup_datetime) OVER (PARTITION BY customer_id ORDER BY pickup_datetime) AS next_trip
    FROM trips
    WHERE status = 'Completed'
)
SELECT
    customer_id,
    pickup_datetime,
    prev_trip,
    DATE_DIFF('day', prev_trip, pickup_datetime)  AS days_since_last,
    DATE_DIFF('day', pickup_datetime, next_trip)  AS days_to_next
FROM customer_trips
WHERE prev_trip IS NOT NULL
ORDER BY days_since_last DESC
LIMIT 50
""",
    },

    "13 · First & Last Trip per Customer (FIRST_VALUE / LAST_VALUE)": {
        "category": "Operations",
        "description": "Customer first and last booking dates using FIRST_VALUE / LAST_VALUE window functions.",
        "sql": """
SELECT DISTINCT
    customer_id,
    FIRST_VALUE(pickup_datetime) OVER w        AS first_trip_date,
    LAST_VALUE(pickup_datetime)  OVER w        AS last_trip_date,
    COUNT(*) OVER (PARTITION BY customer_id)   AS total_trips,
    DATE_DIFF('day',
        FIRST_VALUE(pickup_datetime) OVER w,
        LAST_VALUE(pickup_datetime)  OVER w
    )                                          AS customer_lifespan_days
FROM trips
WHERE status = 'Completed'
WINDOW w AS (
    PARTITION BY customer_id
    ORDER BY pickup_datetime
    ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
)
ORDER BY total_trips DESC
LIMIT 50
""",
    },

    "14 · Booking Type Seasonality Index": {
        "category": "Operations",
        "description": "Monthly seasonality index per booking type — values > 1 = above-average demand.",
        "sql": """
WITH monthly_counts AS (
    SELECT
        booking_type,
        DATE_PART('month', pickup_datetime) AS month_num,
        COUNT(*) AS trip_count
    FROM trips
    GROUP BY 1, 2
),
avg_per_type AS (
    SELECT booking_type, AVG(trip_count) AS avg_monthly
    FROM monthly_counts
    GROUP BY booking_type
)
SELECT
    mc.booking_type,
    mc.month_num,
    mc.trip_count,
    ROUND(mc.trip_count / NULLIF(a.avg_monthly, 0), 3) AS seasonality_index
FROM monthly_counts mc
JOIN avg_per_type a ON mc.booking_type = a.booking_type
ORDER BY mc.booking_type, mc.month_num
""",
    },

    # ── DRIVER ANALYTICS ─────────────────────────────────────────────
    "15 · Driver Safety Score Trend (Window)": {
        "category": "Drivers",
        "description": "Rolling 5-trip average safety score per driver with improvement flag.",
        "sql": """
WITH driver_scores AS (
    SELECT
        t.driver_id,
        t.trip_date,
        t.safety_score,
        AVG(t.safety_score) OVER (
            PARTITION BY t.driver_id
            ORDER BY t.trip_date
            ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
        )                                           AS rolling_5trip_avg,
        LAG(t.safety_score, 1) OVER (
            PARTITION BY t.driver_id ORDER BY t.trip_date
        )                                           AS prev_score
    FROM telematics t
)
SELECT
    ds.driver_id,
    d.full_name,
    d.behavior_profile,
    ds.trip_date,
    ds.safety_score,
    ROUND(ds.rolling_5trip_avg, 2)                  AS rolling_avg,
    ds.prev_score,
    CASE
        WHEN ds.safety_score > ds.prev_score THEN 'Improving'
        WHEN ds.safety_score < ds.prev_score THEN 'Declining'
        ELSE 'Stable'
    END                                             AS trend
FROM driver_scores ds
JOIN drivers d ON ds.driver_id = d.driver_id
ORDER BY ds.driver_id, ds.trip_date
LIMIT 200
""",
    },

    "16 · Driver Risk Composite Score (CTE)": {
        "category": "Drivers",
        "description": "Weighted composite risk score from multiple telematics KPIs.",
        "sql": """
WITH driver_kpis AS (
    SELECT
        driver_id,
        COUNT(*)                                  AS total_trips,
        AVG(safety_score)                         AS avg_safety,
        SUM(harsh_brake_events)                   AS total_harsh_brakes,
        SUM(harsh_accel_events)                   AS total_harsh_accels,
        AVG(idle_time_minutes)                    AS avg_idle_min,
        SUM(speeding_km)                          AS total_speeding_km,
        SUM(CAST(accident_occurred AS INT))       AS accidents,
        SUM(CAST(complaint_filed AS INT))         AS complaints,
        AVG(customer_rating)                      AS avg_rating
    FROM telematics
    GROUP BY driver_id
),
scored AS (
    SELECT
        dk.*,
        ROUND(
            (100 - dk.avg_safety) * 0.35
            + (dk.total_harsh_brakes / NULLIF(dk.total_trips,0)) * 15
            + (dk.total_harsh_accels / NULLIF(dk.total_trips,0)) * 10
            + dk.avg_idle_min * 0.05
            + (dk.total_speeding_km / NULLIF(dk.total_trips,0)) * 0.10
            + dk.accidents * 8
            + dk.complaints * 3
        , 2)                                      AS composite_risk_score
    FROM driver_kpis dk
)
SELECT
    s.*,
    d.full_name,
    d.behavior_profile,
    d.base_salary_pkr,
    RANK() OVER (ORDER BY composite_risk_score DESC) AS risk_rank,
    CASE
        WHEN composite_risk_score < 20  THEN 'Low Risk'
        WHEN composite_risk_score < 45  THEN 'Medium Risk'
        WHEN composite_risk_score < 70  THEN 'High Risk'
        ELSE 'Critical'
    END                                          AS risk_category
FROM scored s
JOIN drivers d ON s.driver_id = d.driver_id
ORDER BY composite_risk_score DESC
""",
    },

    "17 · Driver Idle Time vs Fuel Waste (JOIN + CTE)": {
        "category": "Drivers",
        "description": "Correlate driver idle time with actual fuel cost impact.",
        "sql": """
WITH idle_summary AS (
    SELECT
        driver_id,
        SUM(idle_time_minutes)              AS total_idle_min,
        COUNT(*)                            AS trips,
        AVG(idle_time_minutes)              AS avg_idle_per_trip
    FROM telematics
    GROUP BY driver_id
),
fuel_by_driver AS (
    SELECT
        driver_id,
        SUM(fuel_cost_pkr)                  AS total_fuel_cost,
        AVG(fuel_efficiency_kmpl)           AS avg_efficiency
    FROM fuel_logs
    WHERE driver_id IS NOT NULL
    GROUP BY driver_id
)
SELECT
    i.driver_id,
    d.full_name,
    d.behavior_profile,
    i.total_idle_min,
    i.avg_idle_per_trip,
    f.total_fuel_cost,
    f.avg_efficiency,
    -- Estimated fuel wasted at idle: ~0.5 L/hr × avg PKR/l
    ROUND(i.total_idle_min / 60.0 * 0.5 * 260, 0) AS est_idle_fuel_cost_pkr,
    ROUND(i.total_idle_min / 60.0 * 0.5 * 260
          / NULLIF(f.total_fuel_cost, 0) * 100, 2) AS idle_pct_of_fuel
FROM idle_summary i
JOIN drivers d ON i.driver_id = d.driver_id
LEFT JOIN fuel_by_driver f ON i.driver_id = f.driver_id
ORDER BY total_idle_min DESC
LIMIT 30
""",
    },

    "18 · Driver Accident Recurrence (Window)": {
        "category": "Drivers",
        "description": "Identify drivers with repeated accidents using COUNT over partition.",
        "sql": """
WITH accident_trips AS (
    SELECT
        driver_id,
        trip_date,
        safety_score,
        accident_occurred,
        SUM(CAST(accident_occurred AS INT)) OVER (
            PARTITION BY driver_id
            ORDER BY trip_date
            ROWS UNBOUNDED PRECEDING
        )                                       AS cumulative_accidents,
        COUNT(*) OVER (PARTITION BY driver_id) AS total_trips
    FROM telematics
)
SELECT
    at.driver_id,
    d.full_name,
    d.behavior_profile,
    at.total_trips,
    at.cumulative_accidents,
    ROUND(at.cumulative_accidents * 100.0 / NULLIF(at.total_trips, 0), 3) AS accident_rate_pct
FROM accident_trips at
JOIN drivers d ON at.driver_id = d.driver_id
WHERE at.cumulative_accidents > 0
QUALIFY ROW_NUMBER() OVER (PARTITION BY at.driver_id ORDER BY at.trip_date DESC) = 1
ORDER BY cumulative_accidents DESC
""",
    },

    "19 · Top Drivers by Customer Rating (Window + CTE)": {
        "category": "Drivers",
        "description": "Average customer rating per driver with percentile ranking.",
        "sql": """
WITH ratings AS (
    SELECT
        driver_id,
        COUNT(*)              AS rated_trips,
        AVG(customer_rating)  AS avg_rating,
        MIN(customer_rating)  AS min_rating,
        MAX(customer_rating)  AS max_rating,
        STDDEV(customer_rating) AS rating_stddev
    FROM telematics
    GROUP BY driver_id
    HAVING COUNT(*) >= 5
)
SELECT
    r.driver_id,
    d.full_name,
    d.behavior_profile,
    r.rated_trips,
    ROUND(r.avg_rating, 3)                                     AS avg_rating,
    r.min_rating,
    r.max_rating,
    ROUND(r.rating_stddev, 3)                                  AS consistency,
    RANK()         OVER (ORDER BY r.avg_rating DESC)           AS rating_rank,
    PERCENT_RANK() OVER (ORDER BY r.avg_rating)                AS rating_percentile
FROM ratings r
JOIN drivers d ON r.driver_id = d.driver_id
ORDER BY avg_rating DESC
LIMIT 20
""",
    },

    # ── FLEET & VEHICLES ──────────────────────────────────────────────
    "20 · Vehicle Utilisation Rate by Month (CTE)": {
        "category": "Fleet",
        "description": "Monthly utilisation % per vehicle — days on trip / days in month.",
        "sql": """
WITH monthly_usage AS (
    SELECT
        vehicle_id,
        DATE_TRUNC('month', pickup_datetime) AS month,
        SUM(duration_days)                   AS days_in_use
    FROM trips
    WHERE status = 'Completed'
    GROUP BY 1, 2
)
SELECT
    mu.vehicle_id,
    v.make,
    v.model,
    v.year,
    mu.month,
    ROUND(mu.days_in_use, 2)                    AS days_in_use,
    ROUND(mu.days_in_use / 30.0 * 100, 2)       AS utilisation_pct,
    ROUND(AVG(mu.days_in_use / 30.0 * 100) OVER (
        PARTITION BY mu.vehicle_id
    ), 2)                                        AS avg_util_pct_all_time
FROM monthly_usage mu
JOIN vehicles v ON mu.vehicle_id = v.vehicle_id
ORDER BY mu.month DESC, utilisation_pct DESC
LIMIT 100
""",
    },

    "21 · Vehicle Revenue per KM (CTE + Window)": {
        "category": "Fleet",
        "description": "Revenue per KM driven per vehicle, ranked within vehicle type.",
        "sql": """
WITH vehicle_stats AS (
    SELECT
        t.vehicle_id,
        SUM(t.trip_fare_pkr)    AS total_revenue,
        SUM(t.distance_km)      AS total_km,
        COUNT(*)                AS trip_count
    FROM trips t
    WHERE t.status = 'Completed'
    GROUP BY t.vehicle_id
)
SELECT
    vs.vehicle_id,
    v.make,
    v.model,
    v.year,
    vt.category,
    vs.total_revenue,
    vs.total_km,
    vs.trip_count,
    ROUND(vs.total_revenue / NULLIF(vs.total_km, 0), 2) AS revenue_per_km,
    RANK() OVER (
        PARTITION BY vt.category
        ORDER BY vs.total_revenue / NULLIF(vs.total_km, 0) DESC
    )                                                   AS rank_in_category
FROM vehicle_stats vs
JOIN vehicles v  ON vs.vehicle_id = v.vehicle_id
JOIN vehicle_types vt ON v.vehicle_type_id = vt.vehicle_type_id
ORDER BY revenue_per_km DESC
LIMIT 40
""",
    },

    "22 · Maintenance Cost per Vehicle (Cumulative Window)": {
        "category": "Fleet",
        "description": "Cumulative maintenance spend per vehicle over time.",
        "sql": """
SELECT
    m.vehicle_id,
    v.make,
    v.model,
    m.maintenance_date,
    m.maintenance_type,
    m.total_cost_pkr,
    SUM(m.total_cost_pkr) OVER (
        PARTITION BY m.vehicle_id
        ORDER BY m.maintenance_date
        ROWS UNBOUNDED PRECEDING
    )                                   AS cumulative_cost,
    AVG(m.total_cost_pkr) OVER (
        PARTITION BY m.vehicle_id
    )                                   AS avg_maint_cost
FROM maintenance m
JOIN vehicles v ON m.vehicle_id = v.vehicle_id
ORDER BY m.vehicle_id, m.maintenance_date
LIMIT 200
""",
    },

    "23 · Days Since Last Maintenance (CTE)": {
        "category": "Fleet",
        "description": "Days since last maintenance per vehicle — for service overdue alerts.",
        "sql": """
WITH last_service AS (
    SELECT
        vehicle_id,
        MAX(maintenance_date)                                   AS last_maint_date,
        COUNT(*)                                                AS total_services,
        SUM(total_cost_pkr)                                     AS lifetime_maint_cost
    FROM maintenance
    GROUP BY vehicle_id
)
SELECT
    v.vehicle_id,
    v.make,
    v.model,
    v.year,
    v.odometer_km,
    v.status,
    ls.last_maint_date,
    DATE_DIFF('day', ls.last_maint_date, DATE '2026-07-01')    AS days_since_last_service,
    ls.total_services,
    ls.lifetime_maint_cost,
    CASE
        WHEN DATE_DIFF('day', ls.last_maint_date, DATE '2026-07-01') > 180 THEN 'Overdue'
        WHEN DATE_DIFF('day', ls.last_maint_date, DATE '2026-07-01') > 90  THEN 'Due Soon'
        ELSE 'OK'
    END                                                        AS service_status
FROM vehicles v
LEFT JOIN last_service ls ON v.vehicle_id = ls.vehicle_id
ORDER BY days_since_last_service DESC NULLS FIRST
LIMIT 50
""",
    },

    "24 · Fleet Age Profile with Cost Correlation": {
        "category": "Fleet",
        "description": "Vehicle age vs maintenance cost — identifying which age groups cost most.",
        "sql": """
WITH age_cost AS (
    SELECT
        v.vehicle_id,
        v.make,
        v.model,
        2026 - v.year                       AS vehicle_age,
        v.odometer_km,
        SUM(m.total_cost_pkr)               AS total_maint_cost,
        COUNT(m.maint_id)                   AS service_count
    FROM vehicles v
    LEFT JOIN maintenance m ON v.vehicle_id = m.vehicle_id
    GROUP BY 1,2,3,4,5
)
SELECT
    vehicle_age,
    COUNT(*)                                AS vehicle_count,
    ROUND(AVG(total_maint_cost), 0)         AS avg_maint_cost,
    ROUND(AVG(odometer_km), 0)              AS avg_odometer,
    ROUND(SUM(total_maint_cost), 0)         AS total_maint_cost,
    ROUND(AVG(service_count), 1)            AS avg_services
FROM age_cost
GROUP BY vehicle_age
ORDER BY vehicle_age
""",
    },

    "25 · Fuel Efficiency Z-Score Anomalies (Window)": {
        "category": "Fleet",
        "description": "Detect fuel efficiency anomalies using Z-score (>2σ from vehicle mean).",
        "sql": """
WITH vehicle_fuel_stats AS (
    SELECT
        vehicle_id,
        AVG(fuel_efficiency_kmpl)   AS mean_eff,
        STDDEV(fuel_efficiency_kmpl) AS std_eff
    FROM fuel_logs
    GROUP BY vehicle_id
    HAVING COUNT(*) >= 3
)
SELECT
    fl.fuel_id,
    fl.vehicle_id,
    fl.trip_id,
    fl.fill_date,
    fl.fuel_type,
    fl.fuel_efficiency_kmpl,
    vfs.mean_eff,
    vfs.std_eff,
    ROUND((fl.fuel_efficiency_kmpl - vfs.mean_eff) / NULLIF(vfs.std_eff, 0), 3) AS z_score,
    CASE
        WHEN ABS((fl.fuel_efficiency_kmpl - vfs.mean_eff) / NULLIF(vfs.std_eff, 0)) > 3 THEN 'Severe Anomaly'
        WHEN ABS((fl.fuel_efficiency_kmpl - vfs.mean_eff) / NULLIF(vfs.std_eff, 0)) > 2 THEN 'Anomaly'
        ELSE 'Normal'
    END                                                                           AS anomaly_flag
FROM fuel_logs fl
JOIN vehicle_fuel_stats vfs ON fl.vehicle_id = vfs.vehicle_id
WHERE ABS((fl.fuel_efficiency_kmpl - vfs.mean_eff) / NULLIF(vfs.std_eff, 0)) > 2
ORDER BY ABS(z_score) DESC
LIMIT 50
""",
    },

    # ── CUSTOMER ANALYTICS ────────────────────────────────────────────
    "26 · Customer Lifetime Value (CTE + Window)": {
        "category": "Customers",
        "description": "Customer LTV: total spend, trip count, avg order value, and LTV rank.",
        "sql": """
WITH customer_ltv AS (
    SELECT
        i.customer_id,
        COUNT(DISTINCT i.invoice_id)           AS total_invoices,
        SUM(i.total_amount_pkr)                AS total_spend,
        AVG(i.total_amount_pkr)                AS avg_order_value,
        SUM(i.paid_amount_pkr)                 AS total_paid,
        MIN(i.invoice_date)                    AS first_purchase,
        MAX(i.invoice_date)                    AS last_purchase,
        DATE_DIFF('day', MIN(i.invoice_date), MAX(i.invoice_date)) AS customer_age_days
    FROM invoices i
    GROUP BY i.customer_id
)
SELECT
    cl.*,
    c.full_name,
    c.customer_type,
    c.city,
    RANK()    OVER (ORDER BY cl.total_spend DESC)        AS ltv_rank,
    NTILE(5)  OVER (ORDER BY cl.total_spend DESC)        AS ltv_quintile,
    ROUND(cl.total_spend / NULLIF(cl.customer_age_days, 0) * 365, 0) AS annualised_spend
FROM customer_ltv cl
JOIN customers c ON cl.customer_id = c.customer_id
ORDER BY total_spend DESC
LIMIT 30
""",
    },

    "27 · Customer Churn Risk (CTE + CASE)": {
        "category": "Customers",
        "description": "Identify at-risk customers based on recency of last booking.",
        "sql": """
WITH recency AS (
    SELECT
        customer_id,
        MAX(pickup_datetime)                                 AS last_trip,
        COUNT(*)                                            AS total_trips,
        DATE_DIFF('day', MAX(pickup_datetime), TIMESTAMP '2026-07-01 00:00:00') AS days_inactive
    FROM trips
    WHERE status = 'Completed'
    GROUP BY customer_id
)
SELECT
    r.customer_id,
    c.full_name,
    c.customer_type,
    c.city,
    r.last_trip,
    r.total_trips,
    r.days_inactive,
    CASE
        WHEN r.days_inactive <= 30  THEN 'Active'
        WHEN r.days_inactive <= 90  THEN 'At Risk'
        WHEN r.days_inactive <= 180 THEN 'Lapsing'
        ELSE 'Churned'
    END                                                     AS churn_segment,
    i.total_spend
FROM recency r
JOIN customers c ON r.customer_id = c.customer_id
LEFT JOIN (
    SELECT customer_id, SUM(total_amount_pkr) AS total_spend
    FROM invoices GROUP BY customer_id
) i ON r.customer_id = i.customer_id
ORDER BY days_inactive DESC
LIMIT 50
""",
    },

    "28 · RFM Segmentation (CTE Chain)": {
        "category": "Customers",
        "description": "RFM (Recency, Frequency, Monetary) customer segmentation using CTEs.",
        "sql": """
WITH rfm_raw AS (
    SELECT
        i.customer_id,
        DATE_DIFF('day', MAX(i.invoice_date), DATE '2026-07-01') AS recency_days,
        COUNT(DISTINCT i.invoice_id)                             AS frequency,
        SUM(i.total_amount_pkr)                                  AS monetary
    FROM invoices i
    GROUP BY i.customer_id
),
rfm_scored AS (
    SELECT *,
        NTILE(5) OVER (ORDER BY recency_days ASC)  AS r_score,
        NTILE(5) OVER (ORDER BY frequency DESC)    AS f_score,
        NTILE(5) OVER (ORDER BY monetary DESC)     AS m_score
    FROM rfm_raw
)
SELECT
    rs.customer_id,
    c.full_name,
    c.customer_type,
    rs.recency_days,
    rs.frequency,
    rs.monetary,
    rs.r_score,
    rs.f_score,
    rs.m_score,
    rs.r_score + rs.f_score + rs.m_score           AS rfm_total,
    CASE
        WHEN rs.r_score >= 4 AND rs.f_score >= 4 THEN 'Champion'
        WHEN rs.r_score >= 3 AND rs.f_score >= 3 THEN 'Loyal'
        WHEN rs.r_score >= 4 AND rs.f_score < 2  THEN 'New Customer'
        WHEN rs.r_score < 2 AND rs.f_score >= 3  THEN 'At Risk'
        WHEN rs.r_score < 2 AND rs.f_score < 2   THEN 'Lost'
        ELSE 'Potential'
    END                                            AS rfm_segment
FROM rfm_scored rs
JOIN customers c ON rs.customer_id = c.customer_id
ORDER BY rfm_total DESC
LIMIT 50
""",
    },

    # ── ADVANCED WINDOW FUNCTIONS ─────────────────────────────────────
    "29 · Revenue Contribution Pareto (80/20 Rule)": {
        "category": "Advanced",
        "description": "Pareto analysis: which customers contribute 80% of revenue? (cumulative sum window).",
        "sql": """
WITH customer_rev AS (
    SELECT
        customer_id,
        SUM(total_amount_pkr) AS total_revenue
    FROM invoices
    GROUP BY customer_id
),
pareto AS (
    SELECT
        cr.customer_id,
        c.full_name,
        c.customer_type,
        cr.total_revenue,
        SUM(cr.total_revenue) OVER (ORDER BY cr.total_revenue DESC
            ROWS UNBOUNDED PRECEDING)               AS running_total,
        SUM(cr.total_revenue) OVER ()               AS grand_total,
        ROUND(
            SUM(cr.total_revenue) OVER (ORDER BY cr.total_revenue DESC
                ROWS UNBOUNDED PRECEDING)
            / SUM(cr.total_revenue) OVER () * 100, 2
        )                                           AS cumulative_pct
    FROM customer_rev cr
    JOIN customers c ON cr.customer_id = c.customer_id
)
SELECT *,
    CASE WHEN cumulative_pct <= 80 THEN 'Top 80%' ELSE 'Tail 20%' END AS pareto_group
FROM pareto
ORDER BY total_revenue DESC
LIMIT 40
""",
    },

    "30 · Moving Average Forecast Baseline": {
        "category": "Advanced",
        "description": "7-day and 30-day moving average for trip demand — simple forecast baseline.",
        "sql": """
WITH daily_trips AS (
    SELECT
        CAST(pickup_datetime AS DATE) AS trip_date,
        COUNT(*)                       AS trip_count,
        SUM(trip_fare_pkr)             AS daily_revenue
    FROM trips
    GROUP BY 1
)
SELECT
    trip_date,
    trip_count,
    daily_revenue,
    ROUND(AVG(trip_count) OVER (
        ORDER BY trip_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ), 2)                                        AS ma_7d_trips,
    ROUND(AVG(trip_count) OVER (
        ORDER BY trip_date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ), 2)                                        AS ma_30d_trips,
    ROUND(AVG(daily_revenue) OVER (
        ORDER BY trip_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ), 0)                                        AS ma_7d_revenue,
    MAX(trip_count) OVER (
        ORDER BY trip_date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    )                                            AS peak_30d
FROM daily_trips
ORDER BY trip_date DESC
LIMIT 100
""",
    },

    "31 · Booking Channel Cohort Analysis (CTE)": {
        "category": "Advanced",
        "description": "Monthly cohort retention by booking type — how many customers return.",
        "sql": """
WITH first_booking AS (
    SELECT
        customer_id,
        booking_type,
        DATE_TRUNC('month', pickup_datetime) AS cohort_month
    FROM trips
    QUALIFY ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY pickup_datetime) = 1
),
subsequent AS (
    SELECT
        t.customer_id,
        fb.cohort_month,
        DATE_TRUNC('month', t.pickup_datetime) AS activity_month,
        DATE_DIFF('month', fb.cohort_month,
            DATE_TRUNC('month', t.pickup_datetime)) AS months_since_first
    FROM trips t
    JOIN first_booking fb ON t.customer_id = fb.customer_id
    WHERE t.status = 'Completed'
)
SELECT
    cohort_month,
    months_since_first,
    COUNT(DISTINCT customer_id)           AS active_customers
FROM subsequent
GROUP BY 1, 2
ORDER BY 1, 2
LIMIT 100
""",
    },

    "32 · Session-Based Trip Grouping (Gaps & Islands)": {
        "category": "Advanced",
        "description": "Group trips into 'sessions' (within 7 days of each other) per customer — classic gaps and islands pattern.",
        "sql": """
WITH trip_gaps AS (
    SELECT
        customer_id,
        pickup_datetime,
        trip_fare_pkr,
        LAG(pickup_datetime) OVER (PARTITION BY customer_id ORDER BY pickup_datetime) AS prev_trip,
        DATE_DIFF('day',
            LAG(pickup_datetime) OVER (PARTITION BY customer_id ORDER BY pickup_datetime),
            pickup_datetime
        ) AS days_gap
    FROM trips
    WHERE status = 'Completed'
),
session_flags AS (
    SELECT *,
        SUM(CASE WHEN days_gap IS NULL OR days_gap > 7 THEN 1 ELSE 0 END)
            OVER (PARTITION BY customer_id ORDER BY pickup_datetime) AS session_id
    FROM trip_gaps
)
SELECT
    customer_id,
    session_id,
    MIN(pickup_datetime)          AS session_start,
    MAX(pickup_datetime)          AS session_end,
    COUNT(*)                      AS trips_in_session,
    SUM(trip_fare_pkr)            AS session_revenue,
    DATE_DIFF('day', MIN(pickup_datetime), MAX(pickup_datetime)) AS session_span_days
FROM session_flags
GROUP BY customer_id, session_id
ORDER BY session_revenue DESC
LIMIT 50
""",
    },

    "33 · Pivoted Monthly KPIs (CASE aggregation)": {
        "category": "Advanced",
        "description": "Monthly KPI pivot table — trips, revenue, avg fare all in one row per month.",
        "sql": """
SELECT
    DATE_TRUNC('month', t.pickup_datetime)       AS month,
    COUNT(*)                                     AS total_trips,
    SUM(CASE WHEN t.status='Completed'  THEN 1 ELSE 0 END) AS completed,
    SUM(CASE WHEN t.status='Cancelled'  THEN 1 ELSE 0 END) AS cancelled,
    ROUND(SUM(CASE WHEN t.status='Completed' THEN t.trip_fare_pkr ELSE 0 END), 0) AS trip_revenue,
    ROUND(AVG(CASE WHEN t.status='Completed' THEN t.trip_fare_pkr END), 0)        AS avg_fare,
    ROUND(AVG(CASE WHEN t.status='Completed' THEN t.distance_km END), 1)          AS avg_km,
    COUNT(DISTINCT t.customer_id)               AS unique_customers,
    COUNT(DISTINCT t.vehicle_id)                AS vehicles_used
FROM trips t
GROUP BY 1
ORDER BY 1 DESC
LIMIT 30
""",
    },

    "34 · Fleet P&L Summary (Multi-CTE)": {
        "category": "Advanced",
        "description": "Full P&L per fleet — revenue minus all cost buckets.",
        "sql": """
WITH fleet_revenue AS (
    SELECT fleet_id, SUM(total_amount_pkr) AS total_revenue
    FROM invoices GROUP BY fleet_id
),
fleet_fuel AS (
    SELECT fleet_id, SUM(fuel_cost_pkr) AS fuel_cost
    FROM fuel_logs GROUP BY fleet_id
),
fleet_maint AS (
    SELECT fleet_id, SUM(total_cost_pkr) AS maint_cost
    FROM maintenance GROUP BY fleet_id
),
fleet_salaries AS (
    SELECT fleet_id, SUM(amount_pkr) AS salary_cost
    FROM operating_expenses
    WHERE category IN ('Driver Salaries','Staff Salaries')
    GROUP BY fleet_id
),
fleet_other AS (
    SELECT fleet_id, SUM(amount_pkr) AS other_opex
    FROM operating_expenses
    WHERE category NOT IN ('Driver Salaries','Staff Salaries')
    GROUP BY fleet_id
)
SELECT
    f.fleet_name,
    ROUND(COALESCE(r.total_revenue, 0), 0)  AS revenue,
    ROUND(COALESCE(fu.fuel_cost, 0), 0)     AS fuel_cost,
    ROUND(COALESCE(m.maint_cost, 0), 0)     AS maint_cost,
    ROUND(COALESCE(s.salary_cost, 0), 0)    AS salary_cost,
    ROUND(COALESCE(o.other_opex, 0), 0)     AS other_opex,
    ROUND(
        COALESCE(r.total_revenue, 0)
        - COALESCE(fu.fuel_cost, 0)
        - COALESCE(m.maint_cost, 0)
        - COALESCE(s.salary_cost, 0)
        - COALESCE(o.other_opex, 0)
    , 0)                                    AS net_profit,
    ROUND(
        (COALESCE(r.total_revenue, 0)
        - COALESCE(fu.fuel_cost, 0)
        - COALESCE(m.maint_cost, 0)
        - COALESCE(s.salary_cost, 0)
        - COALESCE(o.other_opex, 0))
        / NULLIF(r.total_revenue, 0) * 100
    , 2)                                    AS profit_margin_pct
FROM fleets f
LEFT JOIN fleet_revenue  r  ON f.fleet_id = r.fleet_id
LEFT JOIN fleet_fuel     fu ON f.fleet_id = fu.fleet_id
LEFT JOIN fleet_maint    m  ON f.fleet_id = m.fleet_id
LEFT JOIN fleet_salaries s  ON f.fleet_id = s.fleet_id
LEFT JOIN fleet_other    o  ON f.fleet_id = o.fleet_id
ORDER BY net_profit DESC
""",
    },

    "35 · City-Level Demand Forecast Baseline (Window)": {
        "category": "Advanced",
        "description": "30-day rolling demand baseline per city for forecasting.",
        "sql": """
WITH daily_city AS (
    SELECT
        pickup_city,
        CAST(pickup_datetime AS DATE)   AS trip_date,
        COUNT(*)                        AS trips
    FROM trips
    GROUP BY 1, 2
)
SELECT
    pickup_city,
    trip_date,
    trips,
    ROUND(AVG(trips) OVER (
        PARTITION BY pickup_city
        ORDER BY trip_date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ), 2) AS ma_30d,
    MAX(trips) OVER (
        PARTITION BY pickup_city
        ORDER BY trip_date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    )     AS peak_30d,
    ROUND(trips / NULLIF(AVG(trips) OVER (PARTITION BY pickup_city), 0), 3) AS demand_index
FROM daily_city
ORDER BY pickup_city, trip_date DESC
LIMIT 200
""",
    },

    "36 · Rate Card Effectiveness Analysis": {
        "category": "Advanced",
        "description": "Compare actual trip fares vs rate card daily rates to measure pricing adherence.",
        "sql": """
WITH actual_rates AS (
    SELECT
        t.vehicle_id,
        t.booking_type,
        t.pickup_city,
        t.trip_fare_pkr,
        t.duration_days,
        ROUND(t.trip_fare_pkr / NULLIF(t.duration_days, 0), 0) AS actual_daily_rate
    FROM trips t
    WHERE t.status = 'Completed' AND t.duration_days > 0
),
rate_lookup AS (
    SELECT
        vt.category,
        rc.booking_type,
        rc.daily_rate_pkr        AS listed_rate
    FROM rate_cards rc
    JOIN vehicle_types vt ON rc.vehicle_type_id = vt.vehicle_type_id
)
SELECT
    ar.booking_type,
    ar.pickup_city,
    ROUND(AVG(ar.actual_daily_rate), 0)     AS avg_actual_rate,
    ROUND(AVG(rl.listed_rate), 0)           AS avg_listed_rate,
    ROUND(AVG(ar.actual_daily_rate)
        - AVG(rl.listed_rate), 0)           AS rate_gap_pkr,
    ROUND((AVG(ar.actual_daily_rate)
        - AVG(rl.listed_rate))
        / NULLIF(AVG(rl.listed_rate),0)*100,2) AS rate_gap_pct,
    COUNT(*)                                AS trip_count
FROM actual_rates ar
LEFT JOIN rate_lookup rl
    ON ar.booking_type = rl.booking_type
GROUP BY ar.booking_type, ar.pickup_city
HAVING COUNT(*) >= 5
ORDER BY ABS(rate_gap_pct) DESC
LIMIT 30
""",
    },

    "37 · Vehicle Downtime Analysis (CTE)": {
        "category": "Fleet",
        "description": "Estimate vehicle downtime between trips using LEAD window function.",
        "sql": """
WITH trip_timeline AS (
    SELECT
        vehicle_id,
        pickup_datetime,
        dropoff_datetime,
        LEAD(pickup_datetime) OVER (
            PARTITION BY vehicle_id ORDER BY pickup_datetime
        ) AS next_pickup
    FROM trips
    WHERE status = 'Completed'
)
SELECT
    vehicle_id,
    dropoff_datetime,
    next_pickup,
    DATE_DIFF('hour', dropoff_datetime, next_pickup)   AS idle_hours,
    CASE
        WHEN DATE_DIFF('hour', dropoff_datetime, next_pickup) < 2   THEN 'Immediate'
        WHEN DATE_DIFF('hour', dropoff_datetime, next_pickup) < 24  THEN 'Same Day'
        WHEN DATE_DIFF('hour', dropoff_datetime, next_pickup) < 168 THEN 'Within Week'
        ELSE 'Extended Downtime'
    END                                                AS downtime_category
FROM trip_timeline
WHERE next_pickup IS NOT NULL
ORDER BY idle_hours DESC
LIMIT 50
""",
    },

    "38 · Operating Expense Variance (CTE + Window)": {
        "category": "Revenue",
        "description": "Month-over-month expense variance per category using LAG.",
        "sql": """
WITH monthly_opex AS (
    SELECT
        DATE_TRUNC('month', expense_month) AS month,
        category,
        SUM(amount_pkr)                    AS monthly_spend
    FROM operating_expenses
    GROUP BY 1, 2
)
SELECT
    month,
    category,
    monthly_spend,
    LAG(monthly_spend) OVER (PARTITION BY category ORDER BY month) AS prev_month_spend,
    ROUND(monthly_spend
        - LAG(monthly_spend) OVER (PARTITION BY category ORDER BY month), 0) AS variance_pkr,
    ROUND(
        (monthly_spend - LAG(monthly_spend) OVER (PARTITION BY category ORDER BY month))
        / NULLIF(LAG(monthly_spend) OVER (PARTITION BY category ORDER BY month), 0) * 100
    , 2) AS variance_pct
FROM monthly_opex
ORDER BY month DESC, category
LIMIT 100
""",
    },

    "39 · Self-Drive vs With-Driver Revenue Split": {
        "category": "Operations",
        "description": "Revenue, trip count, and efficiency comparison — self-drive vs chauffeur.",
        "sql": """
SELECT
    CASE WHEN with_driver THEN 'With Driver' ELSE 'Self-Drive' END AS rental_mode,
    COUNT(*)                                                        AS trip_count,
    ROUND(SUM(trip_fare_pkr), 0)                                    AS total_revenue,
    ROUND(AVG(trip_fare_pkr), 0)                                    AS avg_fare,
    ROUND(AVG(distance_km), 1)                                      AS avg_distance_km,
    ROUND(AVG(duration_days), 3)                                    AS avg_duration_days,
    ROUND(SUM(trip_fare_pkr)
        / NULLIF(SUM(SUM(trip_fare_pkr)) OVER (), 0) * 100, 2)     AS revenue_share_pct,
    SUM(CASE WHEN status='Cancelled' THEN 1 ELSE 0 END)             AS cancellations,
    ROUND(
        SUM(CASE WHEN status='Cancelled' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2
    )                                                               AS cancel_rate_pct
FROM trips
GROUP BY with_driver
""",
    },

    "40 · Vehicle Category Performance Matrix": {
        "category": "Fleet",
        "description": "Full performance matrix by vehicle category — revenue, utilisation, efficiency.",
        "sql": """
SELECT
    vt.category,
    COUNT(DISTINCT v.vehicle_id)                         AS vehicle_count,
    COUNT(t.trip_id)                                     AS total_trips,
    ROUND(SUM(t.trip_fare_pkr), 0)                       AS total_revenue,
    ROUND(AVG(t.trip_fare_pkr), 0)                       AS avg_fare,
    ROUND(AVG(t.distance_km), 1)                         AS avg_km,
    ROUND(AVG(f.fuel_efficiency_kmpl), 2)                AS avg_fuel_eff,
    ROUND(SUM(m.total_cost_pkr), 0)                      AS total_maint_cost,
    ROUND(SUM(t.trip_fare_pkr) / NULLIF(SUM(m.total_cost_pkr), 0), 2) AS revenue_to_maint_ratio
FROM vehicle_types vt
JOIN vehicles v  ON v.vehicle_type_id = vt.vehicle_type_id
LEFT JOIN trips t     ON t.vehicle_id = v.vehicle_id AND t.status = 'Completed'
LEFT JOIN fuel_logs f ON f.vehicle_id = v.vehicle_id
LEFT JOIN maintenance m ON m.vehicle_id = v.vehicle_id
GROUP BY vt.category
ORDER BY total_revenue DESC
""",
    },

    "41 · Weekend vs Weekday Revenue": {
        "category": "Operations",
        "description": "Revenue, volume and avg fare split by weekend vs weekday.",
        "sql": """
SELECT
    CASE WHEN DAYOFWEEK(pickup_datetime) IN (1,7) THEN 'Weekend' ELSE 'Weekday' END AS day_type,
    DATE_PART('hour', pickup_datetime)     AS hour_of_day,
    COUNT(*)                               AS trip_count,
    ROUND(AVG(trip_fare_pkr), 0)           AS avg_fare,
    ROUND(SUM(trip_fare_pkr), 0)           AS total_revenue
FROM trips
WHERE status = 'Completed'
GROUP BY 1, 2
ORDER BY 1, 2
""",
    },

    "42 · Customer Segment Revenue (GROUPING SETS)": {
        "category": "Customers",
        "description": "Revenue across all combinations of customer type and city using GROUPING SETS.",
        "sql": """
SELECT
    c.customer_type,
    c.city,
    COUNT(DISTINCT i.customer_id)           AS customers,
    ROUND(SUM(i.total_amount_pkr), 0)       AS total_revenue,
    ROUND(AVG(i.total_amount_pkr), 0)       AS avg_invoice
FROM invoices i
JOIN customers c ON i.customer_id = c.customer_id
GROUP BY GROUPING SETS (
    (c.customer_type, c.city),
    (c.customer_type),
    (c.city),
    ()
)
ORDER BY total_revenue DESC NULLS LAST
LIMIT 40
""",
    },

    "43 · Surcharge Revenue by Type (Billing Lines)": {
        "category": "Revenue",
        "description": "Breakdown of surcharge revenue from billing line items.",
        "sql": """
SELECT
    charge_type,
    description,
    COUNT(*)                                AS occurrences,
    ROUND(SUM(amount_pkr), 0)               AS total_pkr,
    ROUND(AVG(amount_pkr), 0)               AS avg_pkr,
    ROUND(SUM(amount_pkr) / SUM(SUM(amount_pkr)) OVER () * 100, 2) AS share_pct
FROM billing_line_items
WHERE charge_type IN ('Surcharge','Discount')
GROUP BY charge_type, description
ORDER BY total_pkr DESC
""",
    },

    "44 · Driver Salary ROI": {
        "category": "Drivers",
        "description": "Revenue generated per driver vs their annual salary cost — ROI metric.",
        "sql": """
WITH driver_revenue AS (
    SELECT
        t.driver_id,
        SUM(t.trip_fare_pkr)    AS total_trip_revenue,
        COUNT(t.trip_id)        AS trips_driven
    FROM trips t
    WHERE t.status = 'Completed' AND t.driver_id IS NOT NULL
    GROUP BY t.driver_id
)
SELECT
    d.driver_id,
    d.full_name,
    d.behavior_profile,
    d.base_salary_pkr,
    d.base_salary_pkr * 12                                  AS annual_salary,
    COALESCE(dr.total_trip_revenue, 0)                      AS revenue_generated,
    COALESCE(dr.trips_driven, 0)                            AS trips_driven,
    ROUND(COALESCE(dr.total_trip_revenue, 0)
        / NULLIF(d.base_salary_pkr * 12, 0), 2)            AS roi_ratio,
    ROUND(COALESCE(dr.total_trip_revenue, 0)
        - d.base_salary_pkr * 12, 0)                        AS net_contribution_pkr
FROM drivers d
LEFT JOIN driver_revenue dr ON d.driver_id = dr.driver_id
ORDER BY roi_ratio DESC NULLS LAST
LIMIT 30
""",
    },

    "45 · Monthly Cancellation Cohort": {
        "category": "Operations",
        "description": "Cancellation trends with 3-month rolling average cancellation rate.",
        "sql": """
WITH monthly_cancel AS (
    SELECT
        DATE_TRUNC('month', pickup_datetime) AS month,
        booking_type,
        COUNT(*) AS total,
        SUM(CASE WHEN status='Cancelled' THEN 1 ELSE 0 END) AS cancelled
    FROM trips
    GROUP BY 1, 2
)
SELECT
    month,
    booking_type,
    total,
    cancelled,
    ROUND(cancelled * 100.0 / NULLIF(total, 0), 2) AS cancel_rate_pct,
    ROUND(AVG(cancelled * 100.0 / NULLIF(total, 0)) OVER (
        PARTITION BY booking_type
        ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ), 2)                                           AS rolling_3m_cancel_rate
FROM monthly_cancel
ORDER BY month DESC, cancel_rate_pct DESC
LIMIT 80
""",
    },

    "46 · GPS Route Heat (Top Lat/Lon Clusters)": {
        "category": "Operations",
        "description": "Cluster pickup coordinates into geographic demand zones.",
        "sql": """
SELECT
    pickup_city,
    ROUND(pickup_lat, 2)                    AS lat_bucket,
    ROUND(pickup_lon, 2)                    AS lon_bucket,
    COUNT(*)                                AS trip_count,
    ROUND(SUM(trip_fare_pkr), 0)            AS zone_revenue,
    ROUND(AVG(distance_km), 1)              AS avg_distance
FROM trips
WHERE status = 'Completed'
  AND pickup_lat IS NOT NULL
GROUP BY 1, 2, 3
ORDER BY trip_count DESC
LIMIT 40
""",
    },

    "47 · Vehicle Insurance Compliance Status": {
        "category": "Fleet",
        "description": "Insurance and fitness cert compliance audit for all vehicles.",
        "sql": """
SELECT
    v.vehicle_id,
    v.make,
    v.model,
    v.year,
    v.registration_no,
    v.fleet_id,
    v.insurance_expiry,
    v.fitness_cert_expiry,
    DATE_DIFF('day', v.insurance_expiry,    DATE '2026-07-01') AS insurance_days_overdue,
    DATE_DIFF('day', v.fitness_cert_expiry, DATE '2026-07-01') AS fitness_days_overdue,
    CASE WHEN v.insurance_expiry    < DATE '2026-07-01' THEN 'EXPIRED' ELSE 'Valid' END AS insurance_status,
    CASE WHEN v.fitness_cert_expiry < DATE '2026-07-01' THEN 'EXPIRED' ELSE 'Valid' END AS fitness_status,
    CASE
        WHEN v.insurance_expiry    < DATE '2026-07-01'
          OR v.fitness_cert_expiry < DATE '2026-07-01' THEN 'NON-COMPLIANT'
        ELSE 'COMPLIANT'
    END                                                        AS compliance_flag
FROM vehicles v
ORDER BY insurance_days_overdue DESC NULLS LAST
LIMIT 60
""",
    },

    "48 · Trip Fare vs Distance Regression Data": {
        "category": "Advanced",
        "description": "Prepare fare vs distance data by vehicle category for regression analysis.",
        "sql": """
SELECT
    vt.category,
    t.booking_type,
    t.distance_km,
    t.duration_days,
    t.trip_fare_pkr,
    ROUND(t.trip_fare_pkr / NULLIF(t.distance_km, 0), 2)    AS fare_per_km,
    ROUND(t.trip_fare_pkr / NULLIF(t.duration_days, 0), 0)   AS fare_per_day,
    t.with_driver,
    t.pickup_city
FROM trips t
JOIN vehicles v    ON t.vehicle_id = v.vehicle_id
JOIN vehicle_types vt ON v.vehicle_type_id = vt.vehicle_type_id
WHERE t.status = 'Completed'
  AND t.distance_km > 0
  AND t.duration_days > 0
ORDER BY RANDOM()
LIMIT 500
""",
    },

    "49 · Staff Headcount & Salary by Fleet (CTE)": {
        "category": "Revenue",
        "description": "Headcount and total salary bill per fleet, split by role.",
        "sql": """
WITH staff_costs AS (
    SELECT
        fleet_id,
        role,
        COUNT(*)                    AS headcount,
        SUM(base_salary_pkr)        AS monthly_salary,
        AVG(base_salary_pkr)        AS avg_salary,
        MIN(base_salary_pkr)        AS min_salary,
        MAX(base_salary_pkr)        AS max_salary
    FROM staff
    WHERE active = true
    GROUP BY fleet_id, role
),
driver_costs AS (
    SELECT
        fleet_id,
        'Driver' AS role,
        COUNT(*)                    AS headcount,
        SUM(base_salary_pkr)        AS monthly_salary,
        AVG(base_salary_pkr)        AS avg_salary,
        MIN(base_salary_pkr)        AS min_salary,
        MAX(base_salary_pkr)        AS max_salary
    FROM drivers
    WHERE active = true
    GROUP BY fleet_id
)
SELECT f.fleet_name, u.role, u.headcount, u.monthly_salary, u.avg_salary
FROM (SELECT * FROM staff_costs UNION ALL SELECT * FROM driver_costs) u
JOIN fleets f ON u.fleet_id = f.fleet_id
ORDER BY f.fleet_name, u.monthly_salary DESC
""",
    },

    "50 · Full KPI Dashboard Query (Multi-CTE)": {
        "category": "Advanced",
        "description": "Single query producing all key business KPIs — the ultimate dashboard query.",
        "sql": """
WITH revenue_kpi AS (
    SELECT
        SUM(total_amount_pkr)                                   AS total_billed,
        SUM(paid_amount_pkr)                                    AS total_collected,
        SUM(outstanding_pkr)                                    AS outstanding,
        ROUND(SUM(paid_amount_pkr)/SUM(total_amount_pkr)*100,2) AS collection_rate
    FROM invoices
),
trip_kpi AS (
    SELECT
        COUNT(*)                                                AS total_trips,
        SUM(CASE WHEN status='Completed' THEN 1 ELSE 0 END)    AS completed,
        SUM(CASE WHEN status='Cancelled' THEN 1 ELSE 0 END)    AS cancelled,
        ROUND(AVG(CASE WHEN status='Completed' THEN trip_fare_pkr END),0) AS avg_fare,
        ROUND(AVG(CASE WHEN status='Completed' THEN distance_km END),1)   AS avg_km
    FROM trips
),
fleet_kpi AS (
    SELECT
        COUNT(*)                                                AS total_vehicles,
        SUM(CASE WHEN status='Available' THEN 1 ELSE 0 END)    AS available,
        SUM(CASE WHEN status='On Trip'   THEN 1 ELSE 0 END)    AS on_trip
    FROM vehicles
),
safety_kpi AS (
    SELECT
        ROUND(AVG(safety_score),2)                              AS avg_safety_score,
        SUM(CAST(accident_occurred AS INT))                     AS total_accidents,
        SUM(CAST(complaint_filed AS INT))                       AS total_complaints
    FROM telematics
),
fuel_kpi AS (
    SELECT
        ROUND(AVG(fuel_efficiency_kmpl),2)                      AS avg_efficiency_kmpl,
        ROUND(SUM(fuel_cost_pkr),0)                             AS total_fuel_cost
    FROM fuel_logs
)
SELECT
    r.total_billed,
    r.total_collected,
    r.outstanding,
    r.collection_rate,
    t.total_trips,
    t.completed,
    t.cancelled,
    ROUND(t.cancelled * 100.0 / NULLIF(t.total_trips,0), 2)    AS cancel_rate_pct,
    t.avg_fare,
    t.avg_km,
    f.total_vehicles,
    f.available,
    f.on_trip,
    s.avg_safety_score,
    s.total_accidents,
    s.total_complaints,
    fu.avg_efficiency_kmpl,
    fu.total_fuel_cost
FROM revenue_kpi r, trip_kpi t, fleet_kpi f, safety_kpi s, fuel_kpi fu
""",
    },
}

# ── Add openai to requirements if needed ──────────────────────────────
try:
    import duckdb
except ImportError:
    st.error("DuckDB not installed. Add `duckdb` to requirements.txt")
    st.stop()

# ── Sidebar: category filter + query selector ──────────────────────────
categories = sorted(set(v["category"] for v in QUERIES.values()))
sel_cat = st.sidebar.selectbox("📂 Category", ["All"] + categories, key="sql_cat")

filtered = {
    k: v for k, v in QUERIES.items()
    if sel_cat == "All" or v["category"] == sel_cat
}

sec(f"📋 Query Library ({len(filtered)} queries)")
col_q, col_info = st.columns([2, 1])

with col_q:
    sel_query = st.selectbox(
        "Select Query",
        list(filtered.keys()),
        key="sql_query_sel",
        label_visibility="collapsed",
    )

query_meta = filtered[sel_query]

with col_info:
    cat_colors = {
        "Revenue":"#E63946","Operations":"#457B9D","Drivers":"#2A9D8F",
        "Fleet":"#E9C46A","Customers":"#6A4C93","Advanced":"#F4A261",
    }
    c = cat_colors.get(query_meta["category"], BRAND)
    st.markdown(f"""
<div style="background:rgba(30,42,58,.8);border:1px solid {c};border-radius:8px;padding:10px 12px;">
  <div style="font-size:.72rem;font-weight:700;color:{c};text-transform:uppercase;letter-spacing:.06em;">{query_meta['category']}</div>
  <div style="font-size:.8rem;color:#c8dff0;margin-top:4px;">{query_meta['description']}</div>
</div>""", unsafe_allow_html=True)

# ── SQL editor ─────────────────────────────────────────────────────────
sec("✏️ SQL Editor")

# Clear stale results when user switches query
if st.session_state.get("_last_sql_q") != sel_query:
    st.session_state.pop("sql_result", None)
    st.session_state.pop("sql_error",  None)
    st.session_state["_last_sql_q"] = sel_query

# Safe widget key — no spaces or special chars
_safe_key = "".join(c if c.isalnum() else "_" for c in sel_query)[:40]

sql_code = st.text_area(
    "SQL",
    value=query_meta["sql"].strip(),
    height=280,
    key=f"sq_{_safe_key}",
    label_visibility="collapsed",
)

run_col, explain_col, dl_col, _ = st.columns([1, 1, 1, 3])
run_btn     = run_col.button("▶ Run Query",  type="primary",   key="sql_run",     use_container_width=True)
explain_btn = explain_col.button("🔍 Explain", type="secondary", key="sql_explain", use_container_width=True)

# ── Execute ────────────────────────────────────────────────────────────
if explain_btn and sql_code.strip():
    with st.spinner("Generating plan …"):
        try:
            plan = conn.execute(f"EXPLAIN {sql_code}").fetchall()
            plan_text = "\n".join(row[1] for row in plan)
            st.session_state["sql_result"] = None
            st.session_state["sql_error"]  = None
            st.code(plan_text, language="text")
        except Exception as e:
            st.error(f"EXPLAIN error: {e}")

if run_btn and sql_code.strip():
    with st.spinner("Executing …"):
        try:
            result_df = conn.execute(sql_code).df()
            st.session_state["sql_result"] = result_df
            st.session_state["sql_error"]  = None
        except Exception as e:
            st.session_state["sql_result"] = None
            st.session_state["sql_error"]  = str(e)

# ── Results ────────────────────────────────────────────────────────────
if "sql_result" in st.session_state:
    if st.session_state["sql_error"]:
        st.error(f"SQL Error: {st.session_state['sql_error']}")
    elif st.session_state["sql_result"] is not None:
        df_res = st.session_state["sql_result"]
        sec(f"📊 Results — {len(df_res):,} rows × {len(df_res.columns)} columns")

        # Download — use st.download_button directly (dl_col no longer exists)
        st.download_button(
            "⬇ Download CSV",
            df_res.to_csv(index=False),
            f"{sel_query[:30].replace(' ','_')}.csv",
            "text/csv",
            key="sql_dl",
        )

        # Smart auto-visualisation
        num_cols = df_res.select_dtypes("number").columns.tolist()
        str_cols = df_res.select_dtypes("object").columns.tolist()

        if len(num_cols) >= 1 and len(str_cols) >= 1:
            st.markdown("<br>", unsafe_allow_html=True)
            vc1, vc2, vc3 = st.columns(3)
            x_col  = vc1.selectbox("X axis",  str_cols + num_cols, key="sql_xax")
            y_col  = vc2.selectbox("Y axis",  num_cols,             key="sql_yax")
            chart_type = vc3.selectbox("Chart", ["Bar","Line","Scatter","Area"], key="sql_chart")

            plot_df = df_res.head(50)
            if chart_type == "Bar":
                fig = go.Figure(go.Bar(x=plot_df[x_col], y=plot_df[y_col],
                    marker_color=BRAND, opacity=.85))
            elif chart_type == "Line":
                fig = go.Figure(go.Scatter(x=plot_df[x_col], y=plot_df[y_col],
                    mode="lines+markers", line=dict(color=BRAND,width=2.5)))
            elif chart_type == "Scatter":
                fig = go.Figure(go.Scatter(x=plot_df[x_col], y=plot_df[y_col],
                    mode="markers", marker=dict(color=BRAND,size=8,opacity=.7)))
            else:  # Area
                fig = go.Figure(go.Scatter(x=plot_df[x_col], y=plot_df[y_col],
                    fill="tozeroy", fillcolor="rgba(230,57,70,.15)",
                    line=dict(color=BRAND,width=2.5)))
            dark_layout(fig, f"{y_col} by {x_col}", height=340)
            fig.update_xaxes(tickangle=-35)
            st.plotly_chart(fig, width='stretch')

        # Table
        st.dataframe(df_res, width='stretch', height=380)

        # Query context insight
        cat = query_meta.get("category","")
        desc = query_meta.get("description","")
        rows = len(df_res)
        num_cols_count = len(df_res.select_dtypes("number").columns)
        insight(
            f"Query <strong>{sel_query}</strong> returned <strong>{rows:,} rows</strong> × "
            f"{len(df_res.columns)} columns. "
            f"<strong>Category:</strong> {cat}. "
            f"{desc} "
            f"Use the chart selector above to visualise the {num_cols_count} numeric column(s). "
            f"Download CSV to use in Excel, Power BI or dbt.",
            "🔍", "info",
            "💡 Combine this with another query using a CTE for deeper cross-table analysis."
        )

# ── Category quick-launch grid ─────────────────────────────────────────
st.markdown("<hr style='border-color:#1e2f44;margin:20px 0'>", unsafe_allow_html=True)
sec("📚 Query Library Overview")

for cat in categories:
    cat_queries = {k: v for k, v in QUERIES.items() if v["category"] == cat}
    c = cat_colors.get(cat, BRAND)
    with st.expander(f"{cat} — {len(cat_queries)} queries"):
        for qname, qmeta in cat_queries.items():
            st.markdown(f"""
<div style="border-left:3px solid {c};padding:4px 10px;margin:4px 0;background:rgba(30,42,58,.4);border-radius:0 6px 6px 0;">
  <div style="font-size:.82rem;font-weight:600;color:#c8dff0;">{qname}</div>
  <div style="font-size:.74rem;color:#5a7a96;">{qmeta['description']}</div>
</div>""", unsafe_allow_html=True)

