"""
pages/Settings.py
Configure the AI provider, API key and model, toggle appearance and clear
saved history. Changes are held in session state for the current run.
"""

from __future__ import annotations

import streamlit as st

from history.storage import HistoryManager
from utils.helpers import get_config, page_header


def render() -> None:
    page_header("Settings", "Configure the AI provider and manage your data.")

    config = get_config()

    left, right = st.columns(2, gap="large")

    # ---- AI provider ----------------------------------------------------- #
    with left:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("**AI provider**")

        provider = st.selectbox(
            "Provider", ["openai", "gemini"],
            index=0 if config.provider == "openai" else 1,
            format_func=lambda p: "OpenAI" if p == "openai" else "Google Gemini",
        )

        if provider == "openai":
            key = st.text_input("OpenAI API key", value=config.openai_key,
                                type="password")
            model = st.selectbox(
                "Model", ["gpt-4o", "gpt-4-turbo", "gpt-4o-mini"],
                index=_safe_index(["gpt-4o", "gpt-4-turbo", "gpt-4o-mini"],
                                  config.openai_model),
            )
        else:
            key = st.text_input("Gemini API key", value=config.gemini_key,
                                type="password")
            model = st.selectbox(
                "Model", ["gemini-1.5-flash", "gemini-1.5-pro"],
                index=_safe_index(["gemini-1.5-flash", "gemini-1.5-pro"],
                                  config.gemini_model),
            )

        if st.button("Save settings", type="primary", use_container_width=True):
            config.provider = provider
            if provider == "openai":
                config.openai_key, config.openai_model = key, model
            else:
                config.gemini_key, config.gemini_model = key, model
            st.markdown(
                "<div class='ok-card'>Settings saved for this session.</div>",
                unsafe_allow_html=True,
            )

        status = ("Connected" if config.configured
                  else "Not configured — the app uses offline mode")
        css = "pill-ok" if config.configured else "pill-danger"
        st.markdown(
            f"<div style='margin-top:10px;'><span class='pill {css}'>{status}</span>"
            "</div>",
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    # ---- Appearance & data ---------------------------------------------- #
    with right:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("**Appearance**")
        st.toggle("Compact spacing", value=False, key="compact_mode")
        st.markdown(
            "<span class='muted'>The interface uses a light, minimalist theme "
            "by design for maximum readability.</span>",
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

        st.write("")
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("**Data**")
        count = HistoryManager().count()
        st.markdown(
            f"<span class='muted'>{count} queries in history.</span>",
            unsafe_allow_html=True,
        )
        st.write("")
        if st.button("Clear query history", use_container_width=True):
            HistoryManager().clear()
            st.markdown(
                "<div class='ok-card'>History cleared.</div>",
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)


def _safe_index(options: list[str], value: str) -> int:
    """Return the index of ``value`` in ``options`` or 0 if absent."""
    return options.index(value) if value in options else 0
