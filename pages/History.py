"""
pages/History.py
Browse, search, bookmark, reuse and delete previously executed queries.
"""

from __future__ import annotations

import streamlit as st

from history.storage import HistoryManager
from utils.helpers import page_header


def render() -> None:
    page_header("History", "Every query you run is saved here automatically.")

    manager = HistoryManager()

    top = st.columns([3, 1])
    search = top[0].text_input(
        "Search", placeholder="Search questions or SQL…", label_visibility="collapsed"
    ).strip()
    bookmarked_only = top[1].toggle("Bookmarked only")

    items = manager.all(search=search, bookmarked_only=bookmarked_only)

    if not items:
        st.markdown(
            "<div class='card'><span class='muted'>No matching history yet.</span>"
            "</div>",
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        f"<span class='muted'>{len(items)} saved queries</span>",
        unsafe_allow_html=True,
    )
    st.write("")

    for item in items:
        star = "★" if item.bookmarked else "☆"
        st.markdown(
            f"<div class='card'>"
            f"<div style='display:flex;justify-content:space-between;'>"
            f"<b>{item.question}</b>"
            f"<span class='muted'>{item.timestamp}</span></div>"
            f"<div class='muted' style='margin-top:2px;'>"
            f"{item.rows} rows · {item.exec_ms:.0f} ms</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
        st.code(item.sql, language="sql")

        c1, c2, c3, _ = st.columns([1, 1, 1, 3])
        if c1.button("Reuse", key=f"reuse_{item.id}", use_container_width=True):
            st.session_state.reuse_question = item.question
            st.markdown(
                "<div class='ok-card'>Loaded into Chat — open the Chat page to run "
                "it.</div>",
                unsafe_allow_html=True,
            )
        if c2.button(f"{star} Bookmark", key=f"bm_{item.id}",
                     use_container_width=True):
            manager.toggle_bookmark(item.id)
            st.rerun()
        if c3.button("Delete", key=f"del_{item.id}", use_container_width=True):
            manager.delete(item.id)
            st.rerun()
        st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)
