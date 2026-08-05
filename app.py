"""
app.py
Entry point for the AI Database Analyst. Renders a minimalist sidebar
navigation (streamlit-option-menu) and dispatches to the page modules.

Run with:  streamlit run app.py
"""

from __future__ import annotations

import streamlit as st
from streamlit_option_menu import option_menu

from utils.helpers import ACCENT, init_session, inject_styles
from pages import Dashboard, Chat, Database, History, Settings

# --------------------------------------------------------------------------- #
# Page configuration
# --------------------------------------------------------------------------- #
st.set_page_config(
    page_title="AI Database Analyst",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_styles()
init_session()

# Map of nav label -> render function.
PAGES = {
    "Dashboard": Dashboard.render,
    "Chat": Chat.render,
    "Database": Database.render,
    "History": History.render,
    "Settings": Settings.render,
}

ICONS = ["grid", "chat-dots", "hdd-stack", "clock-history", "gear"]

# --------------------------------------------------------------------------- #
# Sidebar
# --------------------------------------------------------------------------- #
with st.sidebar:
    st.markdown(
        f"""
        <div style="padding:6px 4px 18px 4px;">
          <div style="font-size:1.15rem;font-weight:700;letter-spacing:-0.02em;">
            <span style="color:{ACCENT};">◆</span>&nbsp;AI Database Analyst
          </div>
          <div class="muted" style="margin-top:2px;">Natural language to SQL</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    selected = option_menu(
        menu_title=None,
        options=list(PAGES.keys()),
        icons=ICONS,
        default_index=0,
        styles={
            "container": {"padding": "0", "background-color": "transparent"},
            "icon": {"color": "#6B7280", "font-size": "15px"},
            "nav-link": {
                "font-size": "14px",
                "font-weight": "500",
                "color": "#374151",
                "padding": "10px 14px",
                "border-radius": "10px",
                "margin": "2px 0",
                "--hover-color": "#EFF4FF",
            },
            "nav-link-selected": {
                "background-color": "#EFF4FF",
                "color": ACCENT,
                "font-weight": "600",
            },
        },
    )

    # Small database status footer.
    db_name = st.session_state.get("db_name")
    status = f"Connected · {db_name}" if db_name else "No database loaded"
    dot = ACCENT if db_name else "#D1D5DB"
    st.markdown(
        f"""
        <div style="position:fixed;bottom:18px;left:16px;right:16px;">
          <div class="card" style="padding:12px 14px;">
            <span style="color:{dot};">●</span>
            <span class="muted" style="margin-left:6px;">{status}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# --------------------------------------------------------------------------- #
# Route to the selected page (each handles its own errors gracefully).
# --------------------------------------------------------------------------- #
try:
    PAGES[selected]()
except Exception as exc:  # noqa: BLE001 - last-resort guard, never crash
    st.markdown(
        f"<div class='err-card'><b>Something went wrong.</b><br>{exc}"
        "<br><span class='muted'>Try reloading the page or reselecting the "
        "database.</span></div>",
        unsafe_allow_html=True,
    )
