"""
Soft Rent a Car — AWS Glue ETL Job
Reads generated CSV/Parquet from S3, writes to processed Delta/Parquet layer.
Configure in AWS Glue Studio or run via boto3.
"""

import sys
import boto3
import json
from datetime import datetime

# ── Glue context (runs in Glue job environment) ─────────────────────────
try:
    from awsglue.context import GlueContext
    from awsglue.job import Job
    from awsglue.utils import getResolvedOptions
    from pyspark.context import SparkContext

    args  = getResolvedOptions(sys.argv, ["JOB_NAME", "S3_INPUT", "S3_OUTPUT"])
    sc    = SparkContext()
    glue  = GlueContext(sc)
    spark = glue.spark_session
    job   = Job(glue)
    job.init(args["JOB_NAME"], args)

    S3_INPUT  = args["S3_INPUT"]   # e.g. s3://softrentacar-data-123456/csv/
    S3_OUTPUT = args["S3_OUTPUT"]  # e.g. s3://softrentacar-data-123456-processed/parquet/

except ImportError:
    # Local testing fallback
    print("Running locally — Glue context not available")
    S3_INPUT  = "s3://softrentacar-data/csv/"
    S3_OUTPUT = "s3://softrentacar-data-processed/parquet/"
    spark     = None
    job       = None


TABLES = [
    "fleets", "vehicle_types", "vehicles", "vehicle_attributes",
    "drivers", "staff", "customers", "trips", "trip_legs",
    "telematics", "invoices", "billing_line_items",
    "fuel_logs", "operating_expenses", "maintenance", "rate_cards",
]

DATE_COLUMNS = {
    "trips":              ["booking_datetime","pickup_datetime","dropoff_datetime"],
    "invoices":           ["invoice_date","due_date"],
    "fuel_logs":          ["fill_date"],
    "maintenance":        ["maintenance_date","next_due_date"],
    "operating_expenses": ["expense_month"],
    "telematics":         ["trip_date"],
    "vehicles":           ["insurance_expiry","fitness_cert_expiry","purchase_date"],
    "drivers":            ["dob","hire_date","license_expiry"],
    "customers":          ["dob","registration_date"],
}


def transform_table(df, table_name):
    """Apply transformations to each table."""
    from pyspark.sql import functions as F
    from pyspark.sql.types import DoubleType, LongType, BooleanType

    # Cast date columns
    for col in DATE_COLUMNS.get(table_name, []):
        if col in df.columns:
            df = df.withColumn(col, F.to_timestamp(col))

    # Cast PKR money columns to double
    for col in df.columns:
        if col.endswith("_pkr") or col.endswith("_cost") or "amount" in col or "fare" in col:
            df = df.withColumn(col, df[col].cast(DoubleType()))

    # Cast boolean columns
    for col in ["with_driver","self_drive","gps_enabled","telematics_enabled",
                "ac_working","active","secp_registered","ntn_registered",
                "has_own_license","accident_occurred","complaint_filed","fuel_included"]:
        if col in df.columns:
            df = df.withColumn(col, df[col].cast(BooleanType()))

    # Add audit columns
    df = df.withColumn("_etl_timestamp", F.current_timestamp())
    df = df.withColumn("_source_table",  F.lit(table_name))

    return df


if spark:
    results = {}
    for table in TABLES:
        print(f"Processing {table}...")
        try:
            # Read CSV from S3
            df_raw = spark.read \
                .option("header", "true") \
                .option("inferSchema", "true") \
                .csv(f"{S3_INPUT}{table}.csv")

            row_count = df_raw.count()

            # Transform
            df_clean = transform_table(df_raw, table)

            # Write Parquet to S3
            df_clean.write \
                .mode("overwrite") \
                .parquet(f"{S3_OUTPUT}{table}/")

            results[table] = {"rows": row_count, "status": "success"}
            print(f"  ✅ {table}: {row_count:,} rows → {S3_OUTPUT}{table}/")

        except Exception as e:
            results[table] = {"rows": 0, "status": f"error: {str(e)}"}
            print(f"  ❌ {table}: {e}")

    # Write run summary to S3
    summary = {
        "run_time": datetime.utcnow().isoformat(),
        "tables": results,
        "total_rows": sum(v["rows"] for v in results.values()),
    }
    s3 = boto3.client("s3")
    bucket = S3_OUTPUT.replace("s3://","").split("/")[0]
    s3.put_object(
        Bucket=bucket,
        Key=f"_etl_summary/run_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json",
        Body=json.dumps(summary, indent=2),
    )
    print(f"\nETL complete. Total rows processed: {summary['total_rows']:,}")

    if job:
        job.commit()
