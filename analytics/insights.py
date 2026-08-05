"""
analytics/insights.py
Generate short, contextual business insights from a result DataFrame.
Works fully offline using descriptive statistics; if an AI provider is
configured it is used to phrase richer narrative insights.
"""

from __future__ import annotations

import pandas as pd

from llm.prompts import build_insight_prompt


class InsightEngine:
    """Derive human-readable insights from tabular query results."""

    def __init__(self, config=None):
        self.config = config

    def generate(self, df: pd.DataFrame, question: str = "") -> list[str]:
        """Return a list of insight strings for the given result."""
        if df is None or df.empty:
            return ["No rows returned, so there is nothing to summarise."]

        if self.config is not None and getattr(self.config, "configured", False):
            try:
                return self._ai_insights(df, question)
            except Exception:  # noqa: BLE001 - fall back to statistics
                pass
        return self._stat_insights(df)

    # ------------------------------------------------------------------ #
    def _ai_insights(self, df: pd.DataFrame, question: str) -> list[str]:
        preview = df.head(30).to_csv(index=False)
        prompt = build_insight_prompt(question, preview)

        if self.config.provider == "openai":
            from openai import OpenAI

            client = OpenAI(api_key=self.config.openai_key)
            resp = client.chat.completions.create(
                model=self.config.openai_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            text = resp.choices[0].message.content
        else:
            import google.generativeai as genai

            genai.configure(api_key=self.config.gemini_key)
            model = genai.GenerativeModel(self.config.gemini_model)
            text = model.generate_content(prompt).text

        lines = [l.strip("-• \t") for l in text.splitlines() if l.strip()]
        return lines[:4] or self._stat_insights(df)

    # ------------------------------------------------------------------ #
    def _stat_insights(self, df: pd.DataFrame) -> list[str]:
        """Descriptive-statistics insights that always work offline."""
        insights: list[str] = [f"Result contains {len(df):,} rows and "
                               f"{len(df.columns)} columns."]

        numeric = df.select_dtypes(include="number")
        categorical = df.select_dtypes(exclude="number")

        for col in numeric.columns[:2]:
            series = df[col].dropna()
            if series.empty:
                continue
            total = series.sum()
            avg = series.mean()
            top = series.max()
            insights.append(
                f"'{col}': total {total:,.2f}, average {avg:,.2f}, peak {top:,.2f}."
            )
            # Concentration insight: share of the largest value.
            if total:
                share = top / total * 100
                insights.append(
                    f"The largest '{col}' value represents {share:.1f}% of the total."
                )

        for col in categorical.columns[:1]:
            vc = df[col].value_counts()
            if not vc.empty:
                lead = vc.index[0]
                pct = vc.iloc[0] / len(df) * 100
                insights.append(
                    f"'{lead}' is the most common {col} ({pct:.1f}% of rows)."
                )

        return insights[:5]
