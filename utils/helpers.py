"""
utils/helpers.py
General-purpose helpers: configuration management, session-state
bootstrapping, styling injection and small formatting utilities.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

import streamlit as st
from dotenv import load_dotenv

# Load environment variables from a local .env file (if present).
load_dotenv()

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

ACCENT = "#2563EB"


@dataclass
class AppConfig:
    """Runtime configuration resolved from environment + session overrides."""

    provider: str = field(default_factory=lambda: os.getenv("AI_PROVIDER", "openai"))
    openai_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    openai_model: str = field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o"))
    gemini_key: str = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    gemini_model: str = field(
        default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    )

    @property
    def active_key(self) -> str:
        return self.openai_key if self.provider == "openai" else self.gemini_key

    @property
    def active_model(self) -> str:
        return self.openai_model if self.provider == "openai" else self.gemini_model

    @property
    def configured(self) -> bool:
        """True when the selected provider has a usable API key."""
        return bool(self.active_key and not self.active_key.startswith("sk-your"))


def get_config() -> AppConfig:
    """Return the AppConfig held in session state, creating it if needed.

    Settings changed on the Settings page are persisted into this object so
    they survive page navigation within a session.
    """
    if "config" not in st.session_state:
        st.session_state.config = AppConfig()
    return st.session_state.config


# --------------------------------------------------------------------------- #
# Session bootstrapping
# --------------------------------------------------------------------------- #

def init_session() -> None:
    """Idempotently initialise all shared session-state keys."""
    ss = st.session_state
    ss.setdefault("db_path", None)          # active SQLite file path
    ss.setdefault("db_name", None)          # friendly name for the DB
    ss.setdefault("schema", None)           # cached schema dict
    ss.setdefault("chat", [])               # list of chat turns
    ss.setdefault("last_result", None)      # last query DataFrame
    ss.setdefault("last_sql", None)         # last generated SQL
    get_config()


# --------------------------------------------------------------------------- #
# Formatting helpers
# --------------------------------------------------------------------------- #

def human_int(value: int) -> str:
    """Format an integer with thousands separators (e.g. 12,340)."""
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return str(value)


def ms(seconds: float) -> str:
    """Convert seconds to a millisecond string, e.g. '12.4 ms'."""
    return f"{seconds * 1000:.1f} ms"


# --------------------------------------------------------------------------- #
# Styling
# --------------------------------------------------------------------------- #

def inject_styles() -> None:
    """Inject the global minimalist design system (Inter + custom CSS)."""
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        html, body, [class*="css"] {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            color: #0A0A0A;
        }}
        .stApp {{ background: #FFFFFF; }}

        /* Sidebar */
        section[data-testid="stSidebar"] {{
            background: #FAFAFA;
            border-right: 1px solid #ECECEC;
        }}

        h1, h2, h3, h4 {{ color: #0A0A0A; font-weight: 600; letter-spacing: -0.01em; }}
        .muted {{ color: #6B7280; font-size: 0.9rem; }}

        /* Card primitives */
        .card {{
            background: #FFFFFF;
            border: 1px solid #ECECEC;
            border-radius: 12px;
            padding: 20px 22px;
            box-shadow: 0 1px 2px rgba(16,24,40,0.04);
            transition: box-shadow .2s ease, transform .2s ease;
        }}
        .card:hover {{ box-shadow: 0 6px 20px rgba(16,24,40,0.08); }}

        .kpi-label {{ color: #6B7280; font-size: .8rem; font-weight: 500;
                      text-transform: uppercase; letter-spacing: .04em; }}
        .kpi-value {{ color: #0A0A0A; font-size: 2rem; font-weight: 700; margin-top: 4px; }}
        .kpi-accent {{ color: {ACCENT}; }}

        .pill {{
            display: inline-block; padding: 3px 10px; border-radius: 999px;
            font-size: .72rem; font-weight: 600; background: #EFF4FF; color: {ACCENT};
        }}
        .pill-danger {{ background: #FEF2F2; color: #DC2626; }}
        .pill-ok {{ background: #ECFDF3; color: #059669; }}

        .warn-card {{
            background: #FFFBEB; border: 1px solid #FDE68A; border-radius: 12px;
            padding: 16px 18px; color: #92400E;
        }}
        .err-card {{
            background: #FEF2F2; border: 1px solid #FECACA; border-radius: 12px;
            padding: 16px 18px; color: #991B1B;
        }}
        .ok-card {{
            background: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 12px;
            padding: 16px 18px; color: #166534;
        }}

        /* Buttons */
        .stButton > button {{
            border-radius: 10px; border: 1px solid #E5E7EB; font-weight: 500;
            transition: all .15s ease;
        }}
        .stButton > button:hover {{ border-color: {ACCENT}; color: {ACCENT}; }}

        /* Inputs */
        .stTextInput input, .stTextArea textarea {{ border-radius: 10px; }}

        /* Tighten default padding */
        .block-container {{ padding-top: 2.2rem; max-width: 1150px; }}
        #MainMenu, footer {{ visibility: hidden; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str = "") -> None:
    """Render a consistent page title + subtitle block."""
    st.markdown(f"### {title}")
    if subtitle:
        st.markdown(f"<div class='muted'>{subtitle}</div>", unsafe_allow_html=True)
    st.write("")


def require_database() -> bool:
    """Return True if a DB is loaded; otherwise show a friendly notice."""
    if st.session_state.get("db_path"):
        return True
    st.markdown(
        "<div class='warn-card'>No database loaded yet. Open the "
        "<b>Database</b> page to upload a SQLite file or generate the "
        "sample database.</div>",
        unsafe_allow_html=True,
    )
    return False
