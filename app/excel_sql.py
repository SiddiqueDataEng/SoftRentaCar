"""Translate common Excel analysis actions into executable DuckDB SQL."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import io
import re
from typing import BinaryIO

import duckdb
import pandas as pd


SQL_EXPORT_DIR = Path(__file__).parent.parent / "generated" / "sql_exports"


def quote_identifier(value: str) -> str:
    return '"' + str(value).replace('"', '""') + '"'


def table_name(sheet_name: str) -> str:
    name = re.sub(r"[^A-Za-z0-9_]+", "_", str(sheet_name)).strip("_").lower()
    return name or "sheet1"


def load_workbook(source: str | Path | bytes | BinaryIO) -> dict[str, pd.DataFrame]:
    """Read all workbook sheets from a path, uploaded bytes, or file object."""
    if isinstance(source, (str, Path)):
        workbook = pd.ExcelFile(source)
    elif isinstance(source, bytes):
        workbook = pd.ExcelFile(io.BytesIO(source))
    else:
        workbook = pd.ExcelFile(source)
    return {sheet: workbook.parse(sheet) for sheet in workbook.sheet_names}


def _value(value: object) -> str:
    if pd.isna(value):
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    return "'" + str(value).replace("'", "''") + "'"


def _column(df: pd.DataFrame, requested: str | None) -> str | None:
    if not requested:
        return None
    matches = {str(col).casefold(): str(col) for col in df.columns}
    return matches.get(str(requested).casefold())


def build_sql(
    df: pd.DataFrame,
    sheet_name: str,
    *,
    action: str = "Preview",
    filter_column: str | None = None,
    filter_value: object | None = None,
    group_column: str | None = None,
    aggregate_column: str | None = None,
    aggregate_function: str = "COUNT",
    pivot_column: str | None = None,
    pivot_values: list[object] | None = None,
    limit: int = 500,
) -> str:
    """Build SQL for the supported Excel actions without raw identifiers."""
    source = quote_identifier(table_name(sheet_name))
    selected_filter = _column(df, filter_column)
    selected_group = _column(df, group_column)
    selected_aggregate = _column(df, aggregate_column)
    selected_pivot = _column(df, pivot_column)
    safe_limit = max(1, min(int(limit), 10000))
    where = ""
    if selected_filter and filter_value not in (None, ""):
        where = f"\nWHERE {quote_identifier(selected_filter)} = {_value(filter_value)}"

    normalized_action = action.casefold()
    if normalized_action == "aggregate" and selected_group:
        function = aggregate_function.upper() if aggregate_function.upper() in {"COUNT", "SUM", "AVG", "MIN", "MAX"} else "COUNT"
        target = "*" if function == "COUNT" or not selected_aggregate else quote_identifier(selected_aggregate)
        alias = f"{function.lower()}_{table_name(selected_aggregate or 'rows')}"
        return (
            f"SELECT {quote_identifier(selected_group)} AS group_value,\n"
            f"       {function}({target}) AS {quote_identifier(alias)}\n"
            f"FROM {source}{where}\nGROUP BY 1\nORDER BY 1\nLIMIT {safe_limit};"
        )

    if normalized_action == "pivot" and selected_group and selected_pivot:
        values = pivot_values or list(df[selected_pivot].dropna().drop_duplicates().head(12))
        expressions = [
            f"SUM(CASE WHEN {quote_identifier(selected_pivot)} = {_value(value)} THEN 1 ELSE 0 END) AS {quote_identifier(str(value))}"
            for value in values
        ] or ["COUNT(*) AS total_rows"]
        return (
            f"SELECT {quote_identifier(selected_group)} AS row_value,\n       "
            + ",\n       ".join(expressions)
            + f"\nFROM {source}{where}\nGROUP BY 1\nORDER BY 1\nLIMIT {safe_limit};"
        )

    return f"SELECT *\nFROM {source}{where}\nLIMIT {safe_limit};"


def is_read_only_sql(sql: str) -> bool:
    """Allow only one SELECT/WITH statement for AI-generated workbook queries."""
    cleaned = re.sub(r"--[^\n]*|/\*.*?\*/", "", sql, flags=re.S).strip().rstrip(";").strip()
    return bool(re.match(r"^(SELECT|WITH)\b", cleaned, flags=re.I)) and ";" not in cleaned


def validate_sql(sql: str, tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    if not is_read_only_sql(sql):
        raise ValueError("Only a single read-only SELECT or WITH query is allowed.")
    connection = duckdb.connect(":memory:")
    try:
        for sheet, frame in tables.items():
            connection.register(table_name(sheet), frame)
        return connection.execute(sql).fetchdf()
    finally:
        connection.close()


def save_sql(sql: str, workbook_name: str, action: str) -> Path:
    """Persist generated SQL as a readable text artifact."""
    SQL_EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    stem = re.sub(r"[^A-Za-z0-9_-]+", "_", Path(workbook_name).stem).strip("_") or "workbook"
    suffix = re.sub(r"[^A-Za-z0-9_-]+", "_", action).strip("_").lower() or "query"
    path = SQL_EXPORT_DIR / f"{stem}_{suffix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    header = (
        f"-- Generated from: {workbook_name}\n"
        f"-- Activity: {action}\n"
        f"-- Generated at (UTC): {datetime.now(timezone.utc).isoformat()}\n\n"
    )
    path.write_text(header + sql.strip() + "\n", encoding="utf-8")
    return path