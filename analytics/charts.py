"""
analytics/charts.py
Auto-detect chart opportunities in a result DataFrame and build clean,
minimalist Plotly figures. Recommends bar / pie / line / scatter based
on column types and cardinality.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

ACCENT = "#2563EB"
# A restrained, mostly-monochrome-with-one-accent palette.
PALETTE = ["#2563EB", "#93B4FF", "#1E3A8A", "#60A5FA", "#3B82F6", "#BFDBFE"]

_LAYOUT = dict(
    font=dict(family="Inter, sans-serif", color="#0A0A0A"),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=10, r=10, t=30, b=10),
    colorway=PALETTE,
)


def _numeric_cols(df: pd.DataFrame) -> list[str]:
    return df.select_dtypes(include="number").columns.tolist()


def _categorical_cols(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c not in _numeric_cols(df)]


def recommend_charts(df: pd.DataFrame) -> list[str]:
    """Return an ordered list of suitable chart types for ``df``."""
    if df is None or df.empty:
        return []

    num = _numeric_cols(df)
    cat = _categorical_cols(df)
    options: list[str] = []

    if num and cat:
        options.append("Bar")
        if df[cat[0]].nunique() <= 8:
            options.append("Pie")
    if len(num) >= 2:
        options.append("Scatter")
    if num and (cat or _looks_temporal(df)):
        options.append("Line")

    # Always allow a bar chart when there is at least one numeric column.
    if num and "Bar" not in options:
        options.append("Bar")
    return options or (["Bar"] if num else [])


def _looks_temporal(df: pd.DataFrame) -> bool:
    for c in df.columns:
        if "date" in c.lower() or "time" in c.lower() or "month" in c.lower():
            return True
    return False


def build_chart(df: pd.DataFrame, kind: str) -> go.Figure | None:
    """Build a Plotly figure of ``kind`` from ``df``, or None if impossible."""
    if df is None or df.empty:
        return None

    num = _numeric_cols(df)
    cat = _categorical_cols(df)
    fig: go.Figure | None = None

    try:
        if kind == "Bar" and num:
            x = cat[0] if cat else df.index.astype(str)
            fig = px.bar(df.head(25), x=x if cat else None, y=num[0],
                         color_discrete_sequence=[ACCENT])
            if not cat:
                fig = px.bar(df.head(25), y=num[0], color_discrete_sequence=[ACCENT])

        elif kind == "Pie" and num and cat:
            fig = px.pie(df.head(8), names=cat[0], values=num[0],
                         color_discrete_sequence=PALETTE, hole=0.45)

        elif kind == "Line" and num:
            x = None
            for c in df.columns:
                if "date" in c.lower() or "time" in c.lower() or "month" in c.lower():
                    x = c
                    break
            x = x or (cat[0] if cat else None)
            fig = px.line(df.head(200), x=x, y=num[0],
                          color_discrete_sequence=[ACCENT], markers=True)

        elif kind == "Scatter" and len(num) >= 2:
            fig = px.scatter(df.head(500), x=num[0], y=num[1],
                             color_discrete_sequence=[ACCENT])
    except Exception:  # noqa: BLE001 - never break the UI over a chart
        return None

    if fig is not None:
        fig.update_layout(**_LAYOUT)
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(showgrid=True, gridcolor="#F1F1F1")
    return fig
