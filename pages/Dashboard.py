"""
pages/Dashboard.py
An at-a-glance overview: KPI cards, recent queries, database information and
AI-generated optimisation suggestions.
"""

from __future__ import annotations

import streamlit as st

from history.storage import HistoryManager
from llm.optimizer import SQLOptimizer
from utils.helpers import ACCENT, human_int, page_header, require_database


def render() -> None:
    page_header("Dashboard", "A snapshot of your database and recent activity.")

    if not require_database():
        return

    schema = st.session_state.schema
    stats = schema["stats"]

    # ---- KPI cards ------------------------------------------------------- #
    kpis = [
        ("Tables", stats["table_count"]),
        ("Rows", stats["row_count"]),
        ("Columns", stats["column_count"]),
        ("Relationships", stats["relationship_count"]),
    ]
    cols = st.columns(4)
    for col, (label, value) in zip(cols, kpis):
        col.markdown(
            f"<div class='kpi-card'><div class='kpi-label'>{label}</div>"
            f"<div class='kpi-value kpi-accent'>{human_int(value)}</div></div>",
            unsafe_allow_html=True,
        )

    st.write("")
    left, right = st.columns([1.3, 1], gap="large")

    # ---- Recent queries -------------------------------------------------- #
    with left:
        st.markdown("**Recent queries**")
        recent = HistoryManager().recent(6)
        if not recent:
            st.markdown(
                "<div class='card'><span class='muted'>No queries yet. Head to the "
                "Chat page to ask your first question.</span></div>",
                unsafe_allow_html=True,
            )
        for item in recent:
            if st.button(
                f"↺  {item.question}",
                key=f"recent_{item.id}",
                use_container_width=True,
            ):
                st.session_state.reuse_question = item.question
                st.session_state["_go_chat"] = True
            st.markdown(
                f"<div class='muted' style='margin:-6px 0 10px 6px;'>"
                f"{item.timestamp} · {item.rows} rows · {item.exec_ms:.0f} ms</div>",
                unsafe_allow_html=True,
            )
        if st.session_state.get("_go_chat"):
            st.session_state.pop("_go_chat")
            st.markdown(
                "<div class='ok-card'>Question queued — open the <b>Chat</b> page "
                "to run it.</div>",
                unsafe_allow_html=True,
            )

    # ---- Database information + AI suggestions --------------------------- #
    with right:
        st.markdown("**Database information**")
        st.markdown(
            f"<div class='card'>"
            f"<div style='display:flex;justify-content:space-between;padding:3px 0;'>"
            f"<span class='muted'>Name</span><span><b>{st.session_state.db_name}</b>"
            f"</span></div>"
            f"<div style='display:flex;justify-content:space-between;padding:3px 0;'>"
            f"<span class='muted'>Tables</span><span>{stats['table_count']}</span></div>"
            f"<div style='display:flex;justify-content:space-between;padding:3px 0;'>"
            f"<span class='muted'>Total rows</span>"
            f"<span>{human_int(stats['row_count'])}</span></div>"
            f"<div style='display:flex;justify-content:space-between;padding:3px 0;'>"
            f"<span class='muted'>Relationships</span>"
            f"<span>{stats['relationship_count']}</span></div>"
            f"</div>",
            unsafe_allow_html=True,
        )

        st.write("")
        st.markdown("**AI suggestions**")
        suggestions = _suggestions_from_last()
        st.markdown(
            "<div class='card'>"
            + "".join(
                f"<div style='padding:5px 0;border-bottom:1px solid #F3F4F6;'>"
                f"<span style='color:{ACCENT};'>◆</span> {s}</div>"
                for s in suggestions
            )
            + "</div>",
            unsafe_allow_html=True,
        )


def _suggestions_from_last() -> list[str]:
    """Optimisation tips based on the last executed SQL, or general advice."""
    last_sql = st.session_state.get("last_sql")
    if last_sql:
        report = SQLOptimizer().analyze(last_sql, st.session_state.get("schema"))
        return report.suggestions[:4]
    return [
        "Ask a question on the Chat page to get tailored optimisation tips.",
        "Prefer selecting specific columns over SELECT * for faster queries.",
        "Add indexes on columns you filter or join on frequently.",
        "Use LIMIT while exploring to keep result sets responsive.",
    ]