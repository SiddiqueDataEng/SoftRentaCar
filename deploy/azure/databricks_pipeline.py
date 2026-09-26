"""
Soft Rent a Car — Databricks Pipeline
Run this notebook in Azure Databricks to:
1. Generate data and write to Delta Lake (ADLS Gen2)
2. Train ML models and register in MLflow
3. Create Databricks SQL views for reporting
"""

# ── Cell 1: Configuration ──────────────────────────────────────────────
STORAGE_ACCOUNT = "softrentacaradls"
CONTAINER       = "processed"
ADLS_PATH       = f"abfss://{CONTAINER}@{STORAGE_ACCOUNT}.dfs.core.windows.net"
CATALOG         = "softrentacar"
SCHEMA          = "fleet_data"

# Mount ADLS (run once)
# dbutils.fs.mount(
#     source=f"abfss://{CONTAINER}@{STORAGE_ACCOUNT}.dfs.core.windows.net/",
#     mount_point="/mnt/softrentacar",
#     extra_configs={
#         f"fs.azure.account.key.{STORAGE_ACCOUNT}.dfs.core.windows.net":
#             dbutils.secrets.get("softrentacar", "adls-key")
#     }
# )

# ── Cell 2: Generate Data ──────────────────────────────────────────────
import sys
import random
import numpy as np

sys.path.insert(0, "/Workspace/Repos/softrentacar")
random.seed(42); np.random.seed(42)

from generators.fleets      import generate_fleets, generate_vehicle_types, generate_vehicles
from generators.staff       import generate_drivers, generate_staff
from generators.customers   import generate_customers
from generators.trips       import generate_trips
from generators.billing     import generate_billing
from generators.fuel        import generate_fuel_logs, generate_operating_expenses
from generators.maintenance import generate_maintenance
from generators.rates       import generate_rate_cards

print("Generating data...")
fleets_raw = generate_fleets()
vtype_rows = generate_vehicle_types()
vehicles_raw, vattrs_raw, fleets_raw = generate_vehicles(fleets_raw)
drivers_raw = generate_drivers()
staff_raw   = generate_staff()
customers_raw = generate_customers()
trips_raw, legs_raw, telem_raw = generate_trips(vehicles_raw, drivers_raw, customers_raw)
invoices_raw, lines_raw = generate_billing(trips_raw)
fuel_raw    = generate_fuel_logs(trips_raw, vehicles_raw)
opex_raw    = generate_operating_expenses(fleets_raw, drivers_raw, staff_raw)
maint_raw   = generate_maintenance(vehicles_raw)
rates_raw   = generate_rate_cards()

print(f"Generated: {len(trips_raw):,} trips, {len(invoices_raw):,} invoices")

# ── Cell 3: Write to Delta Lake ────────────────────────────────────────
import pandas as pd
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("SoftRentaCar").getOrCreate()

# Create catalog and schema
spark.sql(f"CREATE CATALOG IF NOT EXISTS {CATALOG}")
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.{SCHEMA}")

tables = {
    "fleets":             fleets_raw,
    "vehicle_types":      vtype_rows,
    "vehicles":           vehicles_raw,
    "vehicle_attributes": vattrs_raw,
    "drivers":            drivers_raw,
    "staff":              staff_raw,
    "customers":          customers_raw,
    "trips":              trips_raw,
    "trip_legs":          legs_raw,
    "telematics":         telem_raw,
    "invoices":           invoices_raw,
    "billing_line_items": lines_raw,
    "fuel_logs":          fuel_raw,
    "operating_expenses": opex_raw,
    "maintenance":        maint_raw,
    "rate_cards":         rates_raw,
}

for name, data in tables.items():
    df_pd     = pd.DataFrame(data)
    spark_df  = spark.createDataFrame(df_pd)
    full_name = f"{CATALOG}.{SCHEMA}.{name}"

    spark_df.write \
        .format("delta") \
        .mode("overwrite") \
        .option("overwriteSchema", "true") \
        .saveAsTable(full_name)

    print(f"  ✅ {full_name}: {len(df_pd):,} rows")

print("\nAll tables written to Delta Lake!")

# ── Cell 4: Train Driver Safety Model with MLflow ──────────────────────
import mlflow
import mlflow.sklearn

mlflow.set_experiment(f"/Users/{dbutils.notebook.entry_point.getDbutils().notebook().getContext().userName().get()}/SoftRentaCar")

telem_df  = spark.table(f"{CATALOG}.{SCHEMA}.telematics").toPandas()
driver_df = spark.table(f"{CATALOG}.{SCHEMA}.drivers").toPandas()

with mlflow.start_run(run_name="driver_safety_rf"):
    import warnings; warnings.filterwarnings("ignore")
    from app.ml_models import train_driver_safety_model

    clf, le, feat_imp, report, features = train_driver_safety_model(
        telem_df, driver_df
    )
    acc = report.get("accuracy", 0)

    mlflow.log_param("n_estimators", 150)
    mlflow.log_param("max_depth", 8)
    mlflow.log_param("features", features)
    mlflow.log_metric("accuracy", acc)
    mlflow.log_dict(report, "classification_report.json")
    mlflow.sklearn.log_model(
        clf, "driver_safety_model",
        registered_model_name="SoftRentaCar_DriverSafety"
    )
    print(f"Driver Safety Model: {acc*100:.1f}% accuracy — logged to MLflow")

# ── Cell 5: Create Analytics Views ────────────────────────────────────
spark.sql(f"""
CREATE OR REPLACE VIEW {CATALOG}.{SCHEMA}.v_monthly_revenue AS
SELECT
    DATE_TRUNC('MONTH', CAST(invoice_date AS DATE)) AS month,
    SUM(total_amount_pkr)  AS total_billed,
    SUM(paid_amount_pkr)   AS total_collected,
    SUM(outstanding_pkr)   AS outstanding,
    COUNT(*)               AS invoice_count
FROM {CATALOG}.{SCHEMA}.invoices
GROUP BY 1 ORDER BY 1
""")

spark.sql(f"""
CREATE OR REPLACE VIEW {CATALOG}.{SCHEMA}.v_driver_safety AS
SELECT
    t.driver_id,
    d.full_name,
    d.behavior_profile,
    AVG(t.safety_score)               AS avg_safety_score,
    COUNT(*)                          AS total_trips,
    SUM(t.harsh_brake_events)         AS total_harsh_brakes,
    SUM(CAST(t.accident_occurred AS INT)) AS accidents,
    AVG(t.customer_rating)            AS avg_rating
FROM {CATALOG}.{SCHEMA}.telematics t
JOIN {CATALOG}.{SCHEMA}.drivers d ON t.driver_id = d.driver_id
GROUP BY 1, 2, 3
""")

spark.sql(f"""
CREATE OR REPLACE VIEW {CATALOG}.{SCHEMA}.v_fleet_kpis AS
SELECT
    (SELECT SUM(total_amount_pkr) FROM {CATALOG}.{SCHEMA}.invoices) AS total_revenue,
    (SELECT SUM(paid_amount_pkr)  FROM {CATALOG}.{SCHEMA}.invoices) AS total_collected,
    (SELECT COUNT(*)              FROM {CATALOG}.{SCHEMA}.trips WHERE status='Completed') AS completed_trips,
    (SELECT AVG(safety_score)     FROM {CATALOG}.{SCHEMA}.telematics) AS avg_safety_score,
    (SELECT COUNT(*)              FROM {CATALOG}.{SCHEMA}.vehicles WHERE status != 'Retired') AS active_vehicles
""")

print("✅ Analytics views created in Databricks SQL")
print(f"\nPipeline complete! Open Databricks SQL to query {CATALOG}.{SCHEMA}.*")
