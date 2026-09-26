"""
dwh_engine.py — Core Data Engineering Engine
Manages the complete data lifecycle:
  - File state tracking (new / processing / processed / archived)
  - Incremental load detection via watermark
  - Batch full-load vs incremental append logic
  - File archiving with datetime stamps
  - Streaming event append + detection
  - DuckDB ETL orchestration with live progress callbacks
  - Load audit log (meta.load_log)
"""

import json
import shutil
import duckdb
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Callable, Optional

# ── Folder layout ──────────────────────────────────────────────────────────────
ROOT       = Path("C:/Users/Siddique/Desktop/rent-a-car/data")
OLTP_DIR   = ROOT / "csv" / "oltp"          # raw OLTP CSVs land here
INBOX_DIR  = ROOT / "csv" / "inbox"         # new / incoming files (not yet processed)
PROCESSING = ROOT / "csv" / "processing"    # files being actively processed
PROCESSED  = ROOT / "csv" / "processed"     # successfully processed, pending archive
ARCHIVE    = ROOT / "csv" / "archive"       # datetime-stamped archive folders
REJECTED   = ROOT / "csv" / "rejected"      # DQ-failed files
STREAM_DIR = ROOT / "csv" / "stream"        # streaming micro-batch landing zone
DB_PATH    = ROOT / "duckdb.db"
STATE_FILE = ROOT / "csv" / "pipeline_state.json"
DWH_DIR    = Path("RunQL/queries/Unassigned/dwh")

# ── Create all folders ─────────────────────────────────────────────────────────
for _d in [OLTP_DIR, INBOX_DIR, PROCESSING, PROCESSED, ARCHIVE, REJECTED, STREAM_DIR]:
    _d.mkdir(parents=True, exist_ok=True)

# ── OLTP table names ───────────────────────────────────────────────────────────
OLTP_TABLES = [
    "oltp_fleets", "oltp_vehicle_types", "oltp_vehicles", "oltp_vehicle_attributes",
    "oltp_drivers", "oltp_staff", "oltp_customers",
    "oltp_bookings", "oltp_trips", "oltp_trip_legs",
    "oltp_invoices", "oltp_payments", "oltp_billing_line_items",
    "oltp_fuel_logs", "oltp_maintenance", "oltp_telematics",
    "oltp_operating_expenses", "oltp_expense_categories",
    "oltp_rate_cards", "oltp_booking_types", "oltp_charge_types",
]

# ── Watermark keys per table ───────────────────────────────────────────────────
WATERMARK_COL = {
    "oltp_trips":              "pickup_datetime",
    "oltp_bookings":           "created_at",
    "oltp_invoices":           "invoice_date",
    "oltp_payments":           "payment_date",
    "oltp_fuel_logs":          "fill_date",
    "oltp_maintenance":        "maintenance_date",
    "oltp_telematics":         "trip_date",
    "oltp_billing_line_items": "line_id",   # no date, use row count
    "oltp_operating_expenses": "expense_month",
    "oltp_customers":          "registration_date",
    "oltp_drivers":            "hire_date",
    "oltp_vehicles":           "purchase_date",
}

Log = Callable[[str], None]   # callback type: takes a message string


# ═══════════════════════════════════════════════════════════════════════════════
# STATE MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

def load_state() -> dict:
    """Load pipeline state from JSON. Tracks watermarks and last run info."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "watermarks": {},        # table → last loaded timestamp/value
        "last_full_load": None,  # ISO datetime of last full reload
        "last_incremental": None,
        "last_stream_event": None,
        "total_rows_loaded": {},  # table → total rows ever loaded
        "run_count": 0,
        "archive_runs": [],       # list of archive run timestamps
    }


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")


def get_watermark(table: str) -> Optional[str]:
    return load_state()["watermarks"].get(table)


def set_watermark(table: str, value: str) -> None:
    state = load_state()
    state["watermarks"][table] = str(value)
    save_state(state)


# ═══════════════════════════════════════════════════════════════════════════════
# FILE LIFECYCLE MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

def scan_inbox() -> list[Path]:
    """Return CSV files in inbox (new files ready to process)."""
    return sorted(INBOX_DIR.glob("*.csv"))


def scan_oltp() -> list[Path]:
    """Return all CSV files currently in the OLTP landing zone."""
    return sorted(OLTP_DIR.glob("*.csv"))


def move_to_processing(files: list[Path], log: Log = print) -> list[Path]:
    """Move files from inbox/oltp into processing folder. Returns new paths."""
    moved = []
    for f in files:
        dest = PROCESSING / f.name
        shutil.copy2(f, dest)
        moved.append(dest)
        log(f"  📋 Copied to processing: {f.name}")
    return moved


def archive_processed(files: list[Path], run_ts: str, log: Log = print) -> str:
    """
    Move processed files into a timestamped archive subfolder.
    e.g. archive/2026-09-26_14-30-00/oltp_trips.csv
    Returns the archive folder path.
    """
    arc_folder = ARCHIVE / run_ts
    arc_folder.mkdir(parents=True, exist_ok=True)
    for f in files:
        if f.exists():
            dest = arc_folder / f.name
            shutil.move(str(f), str(dest))
            log(f"  📦 Archived: {f.name} → archive/{run_ts}/")
    # Write a manifest
    manifest = {
        "archived_at": run_ts,
        "files": [f.name for f in files],
        "count": len(files),
    }
    (arc_folder / "_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    return str(arc_folder)


def reject_file(f: Path, reason: str, log: Log = print) -> None:
    """Move a file to rejected folder with a reason file."""
    dest = REJECTED / f.name
    shutil.move(str(f), str(dest))
    (REJECTED / f"{f.stem}_reason.txt").write_text(
        f"Rejected: {reason}\nTime: {datetime.now()}\n", encoding="utf-8"
    )
    log(f"  ❌ Rejected: {f.name} — {reason}")


def list_archives() -> list[dict]:
    """Return metadata for all archive runs."""
    runs = []
    for folder in sorted(ARCHIVE.iterdir(), reverse=True):
        if folder.is_dir():
            mf = folder / "_manifest.json"
            if mf.exists():
                try:
                    m = json.loads(mf.read_text(encoding="utf-8"))
                    m["folder"] = folder.name
                    runs.append(m)
                except Exception:
                    runs.append({"folder": folder.name, "files": [], "count": 0})
    return runs


def get_file_sizes() -> dict:
    """Return {filename: {rows, kb, modified, status}} for all tracked CSVs."""
    result = {}
    for tbl in OLTP_TABLES:
        fname = f"{tbl}.csv"
        for search_dir, status in [
            (OLTP_DIR,   "📂 In OLTP"),
            (INBOX_DIR,  "📬 In Inbox"),
            (PROCESSING, "⚙️ Processing"),
            (PROCESSED,  "✅ Processed"),
        ]:
            fp = search_dir / fname
            if fp.exists():
                sz = fp.stat().st_size
                mt = datetime.fromtimestamp(fp.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
                try:
                    rc = sum(1 for _ in open(fp, encoding="utf-8")) - 1
                except Exception:
                    rc = 0
                result[fname] = {
                    "rows": rc, "kb": sz // 1024,
                    "modified": mt, "status": status,
                    "path": str(fp),
                }
                break
        else:
            result[fname] = {"rows": 0, "kb": 0, "modified": "—", "status": "❌ Missing", "path": ""}
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# INCREMENTAL LOAD DETECTION
# ═══════════════════════════════════════════════════════════════════════════════

def count_new_rows(table: str, log: Log = print) -> dict:
    """
    Compare current CSV row count vs watermark to detect new rows.
    Returns {new_rows, total_rows, watermark, has_new}.
    """
    fp = OLTP_DIR / f"{table}.csv"
    if not fp.exists():
        return {"new_rows": 0, "total_rows": 0, "watermark": None, "has_new": False}

    state = load_state()
    wm    = state["watermarks"].get(table)
    prev  = state["total_rows_loaded"].get(table, 0)

    try:
        total = sum(1 for _ in open(fp, encoding="utf-8")) - 1
    except Exception:
        total = 0

    new_rows = max(0, total - prev)
    return {
        "new_rows":  new_rows,
        "total_rows": total,
        "watermark": wm,
        "has_new":   new_rows > 0,
    }


def detect_new_files() -> dict:
    """Scan all OLTP tables and return dict of which have new rows since last load."""
    results = {}
    for tbl in OLTP_TABLES:
        info = count_new_rows(tbl)
        if info["has_new"] or info["total_rows"] > 0:
            results[tbl] = info
    return results


# ═══════════════════════════════════════════════════════════════════════════════
# ETL ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════════════════════

def _run_sql_file(conn: duckdb.DuckDBPyConnection, path: Path, log: Log) -> tuple[int, int]:
    """Execute a SQL file statement by statement. Returns (ok_count, err_count)."""
    if not path.exists():
        log(f"  ⏭  File not found: {path.name}")
        return 0, 0

    raw  = path.read_text(encoding="utf-8")
    stmts = [s.strip() for s in raw.split(";")
             if s.strip() and not s.strip().startswith("--")]
    ok = err = 0
    for stmt in stmts:
        try:
            conn.execute(stmt)
            ok += 1
        except Exception as e:
            err += 1
            log(f"    ⚠ stmt error: {str(e)[:80]}")
    return ok, err


class ETLPipeline:
    """
    Orchestrates the full ETL pipeline with:
    - Full load (replace everything)
    - Incremental load (append only new rows)
    - Streaming load (process micro-batch from stream dir)
    - File archiving after successful load
    - Live progress callbacks for UI
    """

    SQL_STEPS = [
        ("Schema Setup",       DWH_DIR / "00_setup/00_create_schemas.sql"),
        ("Raw Ingest Views",   DWH_DIR / "00_setup/01_raw_ingest.sql"),
        ("DQ Checks",          DWH_DIR / "00_setup/02_data_quality_checks.sql"),
        ("Staging ETL",        DWH_DIR / "00_setup/03_staging_etl.sql"),
        ("dim_date",           DWH_DIR / "01_dimensions/01_dim_date.sql"),
        ("dim_customer",       DWH_DIR / "01_dimensions/02_dim_customer.sql"),
        ("dim_vehicle",        DWH_DIR / "01_dimensions/03_dim_vehicle.sql"),
        ("dim_driver",         DWH_DIR / "01_dimensions/04_dim_driver.sql"),
        ("dim_fleet/location", DWH_DIR / "01_dimensions/05_dim_fleet_location.sql"),
        ("fact_trips",         DWH_DIR / "02_facts/01_fact_trips.sql"),
        ("fact_payments",      DWH_DIR / "02_facts/02_fact_payments.sql"),
        ("fact_operations",    DWH_DIR / "02_facts/03_fact_operations.sql"),
    ]

    def __init__(self, on_log: Log = print, on_progress: Callable[[int, str], None] = None):
        self.log         = on_log
        self.on_progress = on_progress or (lambda p, t: None)
        self.run_ts      = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.state       = load_state()

    def _progress(self, pct: int, text: str) -> None:
        self.on_progress(pct, text)

    # ── FULL LOAD ────────────────────────────────────────────────────────────

    def run_full(self, archive_after: bool = True) -> dict:
        """
        Full rebuild: run every SQL file in order, then archive source CSVs.
        Clears all watermarks and restarts from scratch.
        """
        self.log(f"$ ETL FULL LOAD — {self.run_ts}")
        self.log(f"  Mode: Full Rebuild | Archive: {archive_after}")
        self.log("")

        results = {"steps": [], "errors": 0, "archive": None, "success": False}

        try:
            conn = duckdb.connect(str(DB_PATH))
            total = len(self.SQL_STEPS)

            for i, (name, path) in enumerate(self.SQL_STEPS):
                pct = int((i / total) * 90)
                self._progress(pct, f"[{i+1}/{total}] {name}")
                self.log(f"  ── [{i+1:02d}/{total}] {name}")

                ok, err = _run_sql_file(conn, path, self.log)
                results["errors"] += err

                icon = "✅" if err == 0 else "⚠️"
                msg  = f"{icon} {name}  ({ok} stmts OK" + (f", {err} errors" if err else "") + ")"
                self.log(f"     {msg}")
                results["steps"].append({"step": name, "ok": ok, "err": err})

            conn.close()
            self._progress(92, "Updating watermarks…")

            # Update watermarks and row counts
            for tbl in OLTP_TABLES:
                fp = OLTP_DIR / f"{tbl}.csv"
                if fp.exists():
                    try:
                        rc = sum(1 for _ in open(fp, encoding="utf-8")) - 1
                        self.state["total_rows_loaded"][tbl] = rc
                    except Exception:
                        pass

            self.state["last_full_load"]  = self.run_ts
            self.state["run_count"]       = self.state.get("run_count", 0) + 1
            save_state(self.state)

            # Archive
            if archive_after:
                self._progress(95, "Archiving source files…")
                self.log("")
                self.log(f"  📦 Archiving source CSVs to archive/{self.run_ts}/")
                files_to_archive = list(OLTP_DIR.glob("*.csv"))
                arc = archive_processed(files_to_archive, self.run_ts, self.log)
                results["archive"] = arc
                self.state["archive_runs"].append(self.run_ts)
                save_state(self.state)
                self.log(f"  📦 Archived {len(files_to_archive)} files")

            # Export to CSV + Parquet so dashboard sees new data
            self._progress(97, "Exporting to dashboard CSV + Parquet…")
            conn2 = duckdb.connect(str(DB_PATH))
            self._export_to_dashboard(conn2)
            conn2.close()

            self._progress(100, "✅ Full load complete!")
            self.log("")
            self.log(f"✅ Full load finished — {self.run_ts}")
            self.log(f"   Dashboard data exported — reload the page to see updated KPIs/charts")
            results["success"] = True

        except Exception as ex:
            self.log(f"❌ Fatal: {ex}")
            results["success"] = False

        return results

    # ── INCREMENTAL LOAD ─────────────────────────────────────────────────────

    def run_incremental(self) -> dict:
        """
        Incremental load: detect new rows since last run via row count watermark.
        Always runs schema setup + raw ingest first (required for fresh connections).
        Then re-runs staging + dims + facts, and exports updated tables to
        data/csv/ and data/parquet/ so the Streamlit dashboard picks up new data.
        """
        self.log(f"$ ETL INCREMENTAL LOAD — {self.run_ts}")
        self.log(f"  Mode: Incremental | Scanning for new rows…")
        self.log("")

        results = {"tables_checked": 0, "tables_updated": 0,
                   "new_rows_total": 0, "errors": 0, "success": False}

        # Detect which tables have new data
        new_data = {}
        for tbl in OLTP_TABLES:
            info = count_new_rows(tbl)
            results["tables_checked"] += 1
            if info["has_new"]:
                new_data[tbl] = info
                self.log(f"  🆕 {tbl}: {info['new_rows']:,} new rows (total: {info['total_rows']:,})")
                results["new_rows_total"] += info["new_rows"]

        if not new_data:
            self.log("  ℹ️  No new data detected. Nothing to load.")
            self.log("  💡 Run the data generator to produce new rows first.")
            results["success"] = True
            return results

        self.log(f"\n  Found new data in {len(new_data)} tables — processing…\n")
        self._progress(5, f"Found new data in {len(new_data)} tables…")

        try:
            conn = duckdb.connect(str(DB_PATH))

            # ── STEP 1: Always bootstrap schemas first ────────────────────
            # A fresh DuckDB file won't have raw/staging/dwh schemas yet.
            self._progress(8, "Bootstrapping schemas…")
            self.log("  ── [0] Schema Setup (ensure schemas exist)")
            ok, err = _run_sql_file(conn, DWH_DIR / "00_setup/00_create_schemas.sql", self.log)
            self.log(f"     {'✅' if err==0 else '⚠️'} Schema setup ({ok} stmts, {err} errors)")

            # ── STEP 2: Raw ingest views ──────────────────────────────────
            self._progress(15, "Refreshing raw ingest views…")
            self.log("  ── [1] Raw Ingest Views")
            ok, err = _run_sql_file(conn, DWH_DIR / "00_setup/01_raw_ingest.sql", self.log)
            results["errors"] += err
            self.log(f"     {'✅' if err==0 else '⚠️'} Raw views ({ok} stmts, {err} errors)")

            # ── STEP 3: Staging ETL ───────────────────────────────────────
            self._progress(30, "Running incremental staging ETL…")
            self.log("  ── [2] Staging ETL")
            ok, err = _run_sql_file(conn, DWH_DIR / "00_setup/03_staging_etl.sql", self.log)
            results["errors"] += err
            self.log(f"     {'✅' if err==0 else '⚠️'} Staging ({ok} stmts, {err} errors)")

            # ── STEP 4: Dims ──────────────────────────────────────────────
            dim_steps = [
                ("dim_date",           DWH_DIR / "01_dimensions/01_dim_date.sql"),
                ("dim_customer",       DWH_DIR / "01_dimensions/02_dim_customer.sql"),
                ("dim_vehicle",        DWH_DIR / "01_dimensions/03_dim_vehicle.sql"),
                ("dim_driver",         DWH_DIR / "01_dimensions/04_dim_driver.sql"),
                ("dim_fleet/location", DWH_DIR / "01_dimensions/05_dim_fleet_location.sql"),
            ]
            self._progress(50, "Refreshing dimensions…")
            for name, path in dim_steps:
                self.log(f"  ── [3] {name}")
                ok, err = _run_sql_file(conn, path, self.log)
                results["errors"] += err
                self.log(f"     {'✅' if err==0 else '⚠️'} {name} ({ok} stmts, {err} errors)")

            # ── STEP 5: Facts ─────────────────────────────────────────────
            fact_steps = [
                ("fact_trips",    DWH_DIR / "02_facts/01_fact_trips.sql"),
                ("fact_payments", DWH_DIR / "02_facts/02_fact_payments.sql"),
                ("fact_ops",      DWH_DIR / "02_facts/03_fact_operations.sql"),
            ]
            self._progress(70, "Refreshing facts…")
            for name, path in fact_steps:
                self.log(f"  ── [4] {name}")
                ok, err = _run_sql_file(conn, path, self.log)
                results["errors"] += err
                self.log(f"     {'✅' if err==0 else '⚠️'} {name} ({ok} stmts, {err} errors)")

            # ── STEP 6: Export facts back to CSV + Parquet ────────────────
            # This makes the Streamlit dashboard pick up the new data
            self._progress(85, "Exporting to CSV + Parquet for dashboard…")
            self.log("  ── [5] Exporting to data/csv/ + data/parquet/")
            self._export_to_dashboard(conn)

            conn.close()

            # ── STEP 7: Update watermarks ─────────────────────────────────
            self._progress(95, "Updating watermarks…")
            for tbl in new_data:
                fp = OLTP_DIR / f"{tbl}.csv"
                if fp.exists():
                    try:
                        rc = sum(1 for _ in open(fp, encoding="utf-8")) - 1
                        self.state["total_rows_loaded"][tbl] = rc
                    except Exception:
                        pass
            self.state["last_incremental"] = self.run_ts
            self.state["run_count"]        = self.state.get("run_count", 0) + 1
            save_state(self.state)

            self._progress(100, "✅ Incremental load complete!")
            self.log("")
            self.log(f"✅ Incremental load finished — {len(new_data)} tables updated, "
                     f"{results['new_rows_total']:,} new rows processed")
            self.log(f"   Dashboard data exported — reload the page to see updated KPIs/charts")
            results["tables_updated"] = len(new_data)
            results["success"] = True

        except Exception as ex:
            self.log(f"❌ Fatal: {ex}")
            import traceback
            self.log(traceback.format_exc()[:500])
            results["success"] = False

        return results

    def _export_to_dashboard(self, conn: duckdb.DuckDBPyConnection) -> None:
        """
        Export key tables from DuckDB back to data/csv/ and data/parquet/
        so the Streamlit get_data() cache sees updated data on next load.
        The OLTP tables already exist as CSVs; we only need to export
        the core analytical tables the dashboard reads.
        Maps DWH table names back to the names get_data() expects.
        """
        CSV_OUT = ROOT / "data" / "csv"
        PQ_OUT  = ROOT / "data" / "parquet"
        CSV_OUT.mkdir(parents=True, exist_ok=True)
        PQ_OUT.mkdir(parents=True, exist_ok=True)

        # Map: (duckdb_query, output_name)
        # The dashboard reads these table names from data/csv/ or data/parquet/
        exports = [
            # Read from OLTP CSVs directly (already fresh on disk)
            (f"SELECT * FROM read_csv_auto('{OLTP_DIR}/oltp_trips.csv')",        "trips"),
            (f"SELECT * FROM read_csv_auto('{OLTP_DIR}/oltp_customers.csv')",    "customers"),
            (f"SELECT * FROM read_csv_auto('{OLTP_DIR}/oltp_vehicles.csv')",     "vehicles"),
            (f"SELECT * FROM read_csv_auto('{OLTP_DIR}/oltp_drivers.csv')",      "drivers"),
            (f"SELECT * FROM read_csv_auto('{OLTP_DIR}/oltp_fleets.csv')",       "fleets"),
            (f"SELECT * FROM read_csv_auto('{OLTP_DIR}/oltp_invoices.csv')",     "invoices"),
            (f"SELECT * FROM read_csv_auto('{OLTP_DIR}/oltp_fuel_logs.csv')",    "fuel_logs"),
            (f"SELECT * FROM read_csv_auto('{OLTP_DIR}/oltp_maintenance.csv')",  "maintenance"),
            (f"SELECT * FROM read_csv_auto('{OLTP_DIR}/oltp_telematics.csv')",   "telematics"),
            (f"SELECT * FROM read_csv_auto('{OLTP_DIR}/oltp_billing_line_items.csv')", "billing_line_items"),
            (f"SELECT * FROM read_csv_auto('{OLTP_DIR}/oltp_operating_expenses.csv')", "operating_expenses"),
            (f"SELECT * FROM read_csv_auto('{OLTP_DIR}/oltp_vehicle_types.csv')", "vehicle_types"),
            (f"SELECT * FROM read_csv_auto('{OLTP_DIR}/oltp_rate_cards.csv')",   "rate_cards"),
        ]

        exported = 0
        for query, name in exports:
            try:
                df = conn.execute(query).fetchdf()
                df.to_csv(CSV_OUT / f"{name}.csv", index=False)
                df.to_parquet(PQ_OUT / f"{name}.parquet", index=False)
                exported += 1
            except Exception as ex:
                self.log(f"     ⚠ Export skip {name}: {str(ex)[:60]}")

        self.log(f"     ✅ Exported {exported} tables to CSV + Parquet")

    # ── STREAMING MICRO-BATCH ────────────────────────────────────────────────

    def run_stream_batch(self) -> dict:
        """
        Process streaming micro-batch: pick up files from stream/ dir,
        append to OLTP CSVs, run incremental staging, update facts.
        Moves processed stream files to archive.
        """
        self.log(f"$ STREAM MICRO-BATCH — {self.run_ts}")
        stream_files = list(STREAM_DIR.glob("*.csv"))

        if not stream_files:
            self.log("  ℹ️  No stream files pending.")
            return {"files": 0, "success": True}

        self.log(f"  📡 Found {len(stream_files)} stream file(s) to process")

        for sf in stream_files:
            # Append to matching OLTP CSV
            tbl_name = sf.stem.split("_stream_")[0] if "_stream_" in sf.stem else sf.stem
            dest = OLTP_DIR / f"{tbl_name}.csv"
            try:
                new_df  = pd.read_csv(sf)
                if dest.exists():
                    new_df.to_csv(dest, mode="a", header=False, index=False)
                    self.log(f"  📥 Appended {len(new_df):,} rows → {tbl_name}.csv")
                else:
                    new_df.to_csv(dest, index=False)
                    self.log(f"  📥 Created {tbl_name}.csv with {len(new_df):,} rows")
                # Move stream file to archive
                arc = ARCHIVE / self.run_ts
                arc.mkdir(parents=True, exist_ok=True)
                shutil.move(str(sf), str(arc / sf.name))
            except Exception as ex:
                self.log(f"  ❌ Error processing {sf.name}: {ex}")

        # Run incremental to pick up appended rows
        return self.run_incremental()


# ═══════════════════════════════════════════════════════════════════════════════
# DQ SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════

def run_dq_summary(log: Log = print) -> pd.DataFrame:
    """Run a quick DQ scan across all OLTP CSVs. Returns a summary DataFrame."""
    rows = []
    for tbl in ["oltp_trips", "oltp_customers", "oltp_vehicles",
                "oltp_invoices", "oltp_fuel_logs"]:
        fp = OLTP_DIR / f"{tbl}.csv"
        if not fp.exists():
            continue
        try:
            df   = pd.read_csv(fp, nrows=10000)
            total = len(df)
            nulls = int(df.isnull().any(axis=1).sum())
            dupes = int(df.duplicated().sum())
            pct   = round(nulls * 100 / max(total, 1), 2)
            rows.append({
                "Table":       tbl,
                "Rows":        f"{total:,}",
                "Null Rows":   nulls,
                "Duplicates":  dupes,
                "Issue %":     f"{pct}%",
                "Status":      "✅ Good" if pct <= 1 else ("⚠️ Acceptable" if pct <= 5 else "❌ Bad"),
            })
        except Exception as e:
            rows.append({"Table": tbl, "Rows": "—", "Null Rows": 0,
                         "Duplicates": 0, "Issue %": "—", "Status": f"❌ Error: {e}"})
    return pd.DataFrame(rows)
