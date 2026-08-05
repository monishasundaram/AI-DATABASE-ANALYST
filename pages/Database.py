"""
pages/Database.py
Upload a SQLite database or generate the bundled sample, then explore the
auto-detected schema in a clean hierarchical view.
"""

from __future__ import annotations

import os

import streamlit as st

from database.loader import DatabaseLoader, generate_sample_db
from database.schema_reader import SchemaReader
from utils.helpers import ACCENT, human_int, page_header

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sample_database")


def _load_schema(path: str, name: str) -> None:
    """Connect to a database, cache its schema and update session state."""
    loader = DatabaseLoader(path)
    with loader.connect() as conn:
        schema = SchemaReader(conn).build()
    st.session_state.db_path = path
    st.session_state.db_name = name
    st.session_state.schema = schema


def render() -> None:
    page_header(
        "Database",
        "Upload a SQLite file or generate the sample database. Tables, keys "
        "and relationships are detected automatically.",
    )

    col_a, col_b = st.columns(2, gap="large")

    # ---- Upload ---------------------------------------------------------- #
    with col_a:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("**Upload a database**")
        st.markdown(
            "<span class='muted'>Accepted: .db, .sqlite, .sqlite3</span>",
            unsafe_allow_html=True,
        )
        uploaded = st.file_uploader(
            "SQLite file", type=["db", "sqlite", "sqlite3"], label_visibility="collapsed"
        )
        if uploaded is not None:
            try:
                path = DatabaseLoader.save_upload(uploaded, UPLOAD_DIR)
                if not DatabaseLoader(path).is_valid_sqlite():
                    st.markdown(
                        "<div class='err-card'>That file is not a valid SQLite "
                        "database.</div>",
                        unsafe_allow_html=True,
                    )
                else:
                    _load_schema(path, uploaded.name)
                    st.markdown(
                        f"<div class='ok-card'>Loaded <b>{uploaded.name}</b>.</div>",
                        unsafe_allow_html=True,
                    )
            except Exception as exc:  # noqa: BLE001
                st.markdown(
                    f"<div class='err-card'>Upload failed: {exc}</div>",
                    unsafe_allow_html=True,
                )
        st.markdown("</div>", unsafe_allow_html=True)

    # ---- Sample ---------------------------------------------------------- #
    with col_b:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("**Use the sample database**")
        st.markdown(
            "<span class='muted'>Customers, Products, Orders, Employees, "
            "Suppliers and Payments with realistic data.</span>",
            unsafe_allow_html=True,
        )
        st.write("")
        if st.button("Generate & load sample", use_container_width=True):
            try:
                path = generate_sample_db(overwrite=True)
                _load_schema(path, "sample.db")
                st.markdown(
                    "<div class='ok-card'>Sample database ready.</div>",
                    unsafe_allow_html=True,
                )
            except Exception as exc:  # noqa: BLE001
                st.markdown(
                    f"<div class='err-card'>Could not create sample: {exc}</div>",
                    unsafe_allow_html=True,
                )
        st.markdown("</div>", unsafe_allow_html=True)

    schema = st.session_state.get("schema")
    if not schema:
        return

    # ---- Schema overview ------------------------------------------------- #
    st.write("")
    stats = schema["stats"]
    cols = st.columns(4)
    kpis = [
        ("Tables", stats["table_count"]),
        ("Rows", stats["row_count"]),
        ("Columns", stats["column_count"]),
        ("Relationships", stats["relationship_count"]),
    ]
    for col, (label, value) in zip(cols, kpis):
        col.markdown(
            f"<div class='kpi-card'><div class='kpi-label'>{label}</div>"
            f"<div class='kpi-value kpi-accent'>{human_int(value)}</div></div>",
            unsafe_allow_html=True,
        )

    # ---- Hierarchical schema view --------------------------------------- #
    st.write("")
    st.markdown("**Schema**")
    search = st.text_input(
        "Search tables or columns", placeholder="Filter by table or column name…",
        label_visibility="collapsed",
    ).strip().lower()

    for tname, tinfo in schema["tables"].items():
        col_names = [c["name"] for c in tinfo["columns"]]
        if search and search not in tname.lower() and not any(
            search in c.lower() for c in col_names
        ):
            continue

        rel = len(tinfo["foreign_keys"])
        header = (
            f"{tname}  ·  {len(tinfo['columns'])} cols  ·  "
            f"{human_int(tinfo['row_count'])} rows"
            + (f"  ·  {rel} FK" if rel else "")
        )
        with st.expander(header):
            for c in tinfo["columns"]:
                tags = []
                if c["primary_key"]:
                    tags.append("<span class='pill'>PK</span>")
                if c["not_null"]:
                    tags.append("<span class='pill'>NOT NULL</span>")
                st.markdown(
                    f"<div style='display:flex;justify-content:space-between;"
                    f"padding:4px 0;border-bottom:1px solid #F3F4F6;'>"
                    f"<span><b>{c['name']}</b> "
                    f"<span class='muted'>{c['type']}</span></span>"
                    f"<span>{' '.join(tags)}</span></div>",
                    unsafe_allow_html=True,
                )
            for fk in tinfo["foreign_keys"]:
                st.markdown(
                    f"<div class='muted' style='margin-top:6px;'>↳ "
                    f"<span style='color:{ACCENT};'>{fk['from']}</span> references "
                    f"{fk['to_table']}.{fk['to_column']}</div>",
                    unsafe_allow_html=True,
                )