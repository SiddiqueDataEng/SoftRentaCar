"""
Main entry point – generates all tables and saves them as CSV + Parquet.

Usage:
    python generate_data.py

Output folders:
    data/csv/     – CSV files (human-readable)
    data/parquet/ – Parquet files (analytics-optimised)
    data/json/    – JSON samples (first 500 rows per table)
"""

import random
import sys
import os
from pathlib import Path

import pandas as pd
import numpy as np
from rich.console import Console
from rich.table   import Table
from rich.progress import track

# Seed for reproducibility
random.seed(42)
np.random.seed(42)

console = Console()

# ── Output paths ──────────────────────────────────────────────────────
OUT_CSV     = Path("data/csv")
OUT_PARQUET = Path("data/parquet")
OUT_JSON    = Path("data/json")

for p in [OUT_CSV, OUT_PARQUET, OUT_JSON]:
    p.mkdir(parents=True, exist_ok=True)


# ── Import generators ─────────────────────────────────────────────────
from generators.fleets      import generate_fleets, generate_vehicle_types, generate_vehicles
from generators.staff       import generate_drivers, generate_staff
from generators.customers   import generate_customers
from generators.trips       import generate_trips
from generators.billing     import generate_billing
from generators.fuel        import generate_fuel_logs, generate_operating_expenses
from generators.maintenance import generate_maintenance
from generators.rates       import generate_rate_cards


def save_table(name: str, rows: list[dict]) -> pd.DataFrame:
    """Convert list of dicts → DataFrame and save to all formats."""
    if not rows:
        console.print(f"  [yellow]⚠  {name}: 0 rows – skipped[/yellow]")
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    # CSV
    df.to_csv(OUT_CSV / f"{name}.csv", index=False)
    # Parquet
    df.to_parquet(OUT_PARQUET / f"{name}.parquet", index=False)
    # JSON sample
    df.head(500).to_json(OUT_JSON / f"{name}_sample.json", orient="records", indent=2)

    return df


def main():
    console.rule("[bold cyan]Pakistan Rent-a-Car Data Generator[/bold cyan]")

    summary = Table(title="Generated Tables", show_lines=True)
    summary.add_column("Table",       style="cyan",  min_width=30)
    summary.add_column("Rows",        style="green", justify="right")
    summary.add_column("Columns",     style="yellow",justify="right")
    summary.add_column("CSV Size",    style="white", justify="right")

    def record(name: str, df: pd.DataFrame):
        if df.empty:
            summary.add_row(name, "0", "–", "–")
            return
        csv_path = OUT_CSV / f"{name}.csv"
        size_kb  = round(csv_path.stat().st_size / 1024, 1) if csv_path.exists() else 0
        summary.add_row(name, f"{len(df):,}", str(len(df.columns)), f"{size_kb} KB")

    # ── Step 1: Fleets & vehicles ────────────────────────────────────
    console.print("\n[bold]Step 1:[/bold] Generating fleets & vehicles …")
    fleets      = generate_fleets()
    vtype_rows  = generate_vehicle_types()
    vehicles, vehicle_attrs, fleets = generate_vehicles(fleets)

    df_fleets   = save_table("fleets",             fleets)
    df_vtypes   = save_table("vehicle_types",      vtype_rows)
    df_vehicles = save_table("vehicles",           vehicles)
    df_vattrs   = save_table("vehicle_attributes", vehicle_attrs)

    record("fleets",             df_fleets)
    record("vehicle_types",      df_vtypes)
    record("vehicles",           df_vehicles)
    record("vehicle_attributes", df_vattrs)

    # ── Step 2: Staff & drivers ──────────────────────────────────────
    console.print("[bold]Step 2:[/bold] Generating drivers & staff …")
    drivers = generate_drivers()
    staff   = generate_staff()

    # (drivers & staff aggregates filled after trips)

    # ── Step 3: Customers ────────────────────────────────────────────
    console.print("[bold]Step 3:[/bold] Generating customers …")
    customers = generate_customers()

    # ── Step 4: Trips (core fact table) ─────────────────────────────
    console.print("[bold]Step 4:[/bold] Generating trips / travel data …")
    trips, trip_legs, telematics = generate_trips(vehicles, drivers, customers)

    # Now save drivers and customers (aggregates filled by trips)
    df_drivers   = save_table("drivers",   drivers)
    df_staff     = save_table("staff",     staff)
    df_customers = save_table("customers", customers)

    df_trips     = save_table("trips",      trips)
    df_legs      = save_table("trip_legs",  trip_legs)
    df_telems    = save_table("telematics", telematics)

    record("drivers",    df_drivers)
    record("staff",      df_staff)
    record("customers",  df_customers)
    record("trips",      df_trips)
    record("trip_legs",  df_legs)
    record("telematics", df_telems)

    # ── Step 5: Billing ──────────────────────────────────────────────
    console.print("[bold]Step 5:[/bold] Generating billing & invoices …")
    invoices, line_items = generate_billing(trips)

    df_invoices   = save_table("invoices",          invoices)
    df_line_items = save_table("billing_line_items", line_items)

    record("invoices",          df_invoices)
    record("billing_line_items",df_line_items)

    # ── Step 6: Fuel ─────────────────────────────────────────────────
    console.print("[bold]Step 6:[/bold] Generating fuel logs & operating expenses …")
    fuel_logs  = generate_fuel_logs(trips, vehicles)
    op_expenses= generate_operating_expenses(fleets, drivers, staff)

    df_fuel    = save_table("fuel_logs",          fuel_logs)
    df_opex    = save_table("operating_expenses", op_expenses)

    record("fuel_logs",          df_fuel)
    record("operating_expenses", df_opex)

    # ── Step 7: Maintenance ──────────────────────────────────────────
    console.print("[bold]Step 7:[/bold] Generating maintenance records …")
    maint_rows = generate_maintenance(vehicles)
    df_maint   = save_table("maintenance", maint_rows)
    record("maintenance", df_maint)

    # ── Step 8: Rate cards ───────────────────────────────────────────
    console.print("[bold]Step 8:[/bold] Generating rate cards …")
    rate_cards = generate_rate_cards()
    df_rates   = save_table("rate_cards", rate_cards)
    record("rate_cards", df_rates)

    # ── Summary ──────────────────────────────────────────────────────
    console.print("\n")
    console.print(summary)

    # Print quick revenue snapshot
    if not df_invoices.empty:
        total_rev = df_invoices["total_amount_pkr"].sum()
        total_paid= df_invoices["paid_amount_pkr"].sum()
        console.print(f"\n[bold green]💰 Total billed revenue :[/bold green] PKR {total_rev:,.0f}")
        console.print(f"[bold green]💰 Total collected      :[/bold green] PKR {total_paid:,.0f}")
        console.print(f"[bold yellow]⚠  Outstanding          :[/bold yellow] PKR {total_rev - total_paid:,.0f}")

    if not df_telems.empty:
        avg_score = df_telems["safety_score"].mean()
        accidents = df_telems["accident_occurred"].sum()
        console.print(f"\n[bold cyan]🚗 Avg driver safety score:[/bold cyan] {avg_score:.1f}/100")
        console.print(f"[bold red]🚨 Total accident events  :[/bold red] {int(accidents)}")

    console.print("\n[bold green]✅ All data saved to data/csv/, data/parquet/, data/json/[/bold green]\n")


if __name__ == "__main__":
    main()
