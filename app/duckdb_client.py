from pathlib import Path
from typing import Optional, Tuple, Any

import duckdb
import pandas as pd


# Default on-disk database location (project relative)
DEFAULT_DB_PATH = Path("data/duckdb.db")


def _resolve_path(path: Optional[str]) -> str:
    if path:
        return str(path)
    # ensure parent exists when using default path
    DEFAULT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return str(DEFAULT_DB_PATH)


def get_connection(path: Optional[str] = None) -> duckdb.DuckDBPyConnection:
    """Return a DuckDB connection to the given path (or project default).

    Use `:memory:` to create an in-memory database.
    """
    db = _resolve_path(path)
    return duckdb.connect(database=db, read_only=False)


def query(sql: str, params: Optional[Tuple[Any, ...]] = None, path: Optional[str] = None) -> pd.DataFrame:
    """Execute a SQL query and return a pandas DataFrame.

    Params may be passed as a tuple for parameter substitution.
    """
    conn = get_connection(path)
    try:
        if params:
            res = conn.execute(sql, params).fetchdf()
        else:
            res = conn.execute(sql).fetchdf()
        return res
    finally:
        conn.close()


def execute(sql: str, params: Optional[Tuple[Any, ...]] = None, path: Optional[str] = None) -> None:
    """Run a SQL statement that doesn't return rows (CREATE, INSERT, etc.)."""
    conn = get_connection(path)
    try:
        if params:
            conn.execute(sql, params)
        else:
            conn.execute(sql)
    finally:
        conn.close()


def register_df(df: pd.DataFrame, name: str, path: Optional[str] = None) -> duckdb.DuckDBPyConnection:
    """Register a pandas DataFrame as a table name in DuckDB.

    Returns an open connection; caller is responsible for closing it when done.
    """
    conn = get_connection(path)
    conn.register(name, df)
    return conn
