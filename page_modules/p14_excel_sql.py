"""Excel activity to SQL workspace."""

from pathlib import Path

import streamlit as st

from app.ai_chat import _resolve_key
from app.excel_sql import build_sql, load_workbook, save_sql, table_name, validate_sql
from page_modules._shared import BRAND, inject


def _ai_sql(instructions: str, sheet: str, frame) -> str:
    """Ask the configured model for read-only SQL when available."""
    key = _resolve_key()
    if not key:
        return ""
    from openai import OpenAI

    schema = ", ".join(f"{col} ({dtype})" for col, dtype in frame.dtypes.items())
    prompt = (
        "Convert the requested Excel activity into one DuckDB SQL SELECT query. "
        "Use only the supplied table and columns. Return SQL only, no markdown. "
        "Never generate INSERT, UPDATE, DELETE, DROP, ALTER, or multiple statements.\n\n"
        f"Table: {table_name(sheet)}\nSchema: {schema}\nRequest: {instructions}"
    )
    response = OpenAI(api_key=key).chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        messages=[{"role": "user", "content": prompt}],
    )
    sql = response.choices[0].message.content or ""
    return sql.replace("```sql", "").replace("```", "").strip()


inject()
st.markdown(f'<div style="font-size:1.5rem;font-weight:800;color:{BRAND};">Excel to SQL</div>', unsafe_allow_html=True)
st.caption("Turn workbook filters, summaries, and pivot tables into repeatable DuckDB SQL files.")

uploaded = st.file_uploader("Upload an Excel workbook", type=["xlsx", "xls"])
local_path = st.text_input("Or enter a local workbook path", placeholder=r"C:\Users\Siddique\Desktop\rent-a-car\Trips.xlsx")
source = uploaded if uploaded is not None else (local_path.strip() if local_path.strip() else None)

if source is None:
    st.info("Choose a workbook to begin. Generated SQL is saved under generated/sql_exports.")
    st.stop()

try:
    sheets = load_workbook(source.getvalue() if uploaded is not None else source)
except Exception as exc:
    st.error(f"Could not read the workbook: {exc}")
    st.stop()

sheet = st.selectbox("Worksheet", list(sheets))
frame = sheets[sheet]
st.caption(f"{len(frame):,} rows · {len(frame.columns):,} columns · SQL table: `{table_name(sheet)}`")
st.dataframe(frame.head(100), hide_index=True)

action = st.segmented_control("Excel activity", ["Preview", "Filter", "Aggregate", "Pivot"], default="Preview")
columns = [str(column) for column in frame.columns]
filter_column = filter_value = group_column = aggregate_column = pivot_column = None
pivot_values = []
aggregate_function = "COUNT"

if action in {"Filter", "Aggregate", "Pivot"}:
    with st.container(border=True):
        if action == "Filter":
            filter_column = st.selectbox("Filter column", columns)
            choices = frame[filter_column].dropna().drop_duplicates().head(100).tolist()
            filter_value = st.selectbox("Equals", choices) if choices else st.text_input("Equals")
        elif action == "Aggregate":
            group_column = st.selectbox("Group rows by", columns)
            aggregate_function = st.selectbox("Calculation", ["COUNT", "SUM", "AVG", "MIN", "MAX"])
            aggregate_column = st.selectbox("Value column", ["(row count)"] + columns)
            if aggregate_column == "(row count)":
                aggregate_column = None
        else:
            group_column = st.selectbox("Pivot row field", columns)
            pivot_column = st.selectbox("Pivot column field", columns)
            choices = frame[pivot_column].dropna().drop_duplicates().head(30).tolist()
            pivot_values = st.multiselect("Pivot values", choices, default=choices[:8])
        instructions = st.text_area("Optional AI instruction", placeholder="Example: show completed trips by pickup city and month")
else:
    instructions = st.text_area("Describe an Excel activity", placeholder="Example: filter rows where status is Completed, then total fare by pickup city")

if st.button("Generate SQL", type="primary"):
    sql = ""
    if instructions.strip():
        try:
            sql = _ai_sql(instructions, sheet, frame)
            if sql:
                validate_sql(sql, sheets)
        except Exception as exc:
            st.warning(f"AI SQL was not usable ({exc}); using the selected activity instead.")
            sql = ""
    if not sql:
        sql = build_sql(
            frame, sheet, action=action, filter_column=filter_column,
            filter_value=filter_value, group_column=group_column,
            aggregate_column=aggregate_column, aggregate_function=aggregate_function,
            pivot_column=pivot_column, pivot_values=pivot_values,
        )
    try:
        result = validate_sql(sql, sheets)
        workbook_name = uploaded.name if uploaded is not None else Path(source).name
        saved = save_sql(sql, workbook_name, action)
        st.session_state["excel_sql"] = sql
        st.session_state["excel_sql_path"] = str(saved)
        st.success(f"SQL generated and saved to `{saved}`")
        st.dataframe(result.head(500), hide_index=True)
    except Exception as exc:
        st.error(f"Generated SQL could not run: {exc}")

if st.session_state.get("excel_sql"):
    st.subheader("Generated SQL")
    st.code(st.session_state["excel_sql"], language="sql")