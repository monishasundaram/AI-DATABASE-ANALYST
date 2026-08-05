"""
pages/Chat.py
The AI chat interface and the full NL -> SQL -> result -> explanation
pipeline, including safety validation, optimisation, charts, insights and
exports. Conversation memory is kept per session.
"""

from __future__ import annotations

import streamlit as st

from analytics.charts import build_chart, recommend_charts
from analytics.insights import InsightEngine
from database.executor import QueryExecutor
from database.schema_reader import SchemaReader
from database.loader import DatabaseLoader
from history.storage import HistoryManager
from llm.optimizer import SQLOptimizer
from llm.sql_explainer import SQLExplainer
from llm.sql_generator import SQLGenerator
from security.risk_checker import RiskChecker
from security.validator import SQLValidator
from utils.exporters import to_csv_bytes, to_excel_bytes, to_pdf_bytes
from utils.helpers import ACCENT, get_config, ms, page_header, require_database

EXAMPLES = [
    "Show the top 10 customers by total payment",
    "How many orders were placed?",
    "Average unit price by product category",
    "List the 5 most recent orders",
]


def _schema_text() -> str:
    """Return the cached schema serialised for prompts."""
    loader = DatabaseLoader(st.session_state.db_path)
    with loader.connect() as conn:
        return SchemaReader(conn).to_prompt_text(st.session_state.schema)


def _run_pipeline(question: str) -> None:
    """Execute the complete NL->SQL pipeline for a single question."""
    config = get_config()

    # Build short conversation memory (last 3 questions).
    history_lines = [t["question"] for t in st.session_state.chat[-3:]]
    memory = "\n".join(history_lines)

    schema_text = _schema_text()
    generator = SQLGenerator(config)
    gen = generator.generate(question, schema_text, st.session_state.schema, memory)

    turn: dict = {"question": question, "gen": gen}

    # --- Safety validation ------------------------------------------------ #
    validator = SQLValidator()
    verdict = validator.validate(gen.sql)
    turn["verdict"] = verdict

    if verdict.safe:
        executor = QueryExecutor(st.session_state.db_path)
        result = executor.run(verdict.normalized)
        turn["result"] = result

        if result.ok:
            # Persist to history and cache for other pages.
            HistoryManager().add(question, verdict.normalized,
                                 result.elapsed * 1000, result.row_count)
            st.session_state.last_result = result.dataframe
            st.session_state.last_sql = verdict.normalized

            turn["explanation"] = gen.explanation or SQLExplainer(config).explain(
                verdict.normalized
            )
            turn["optimization"] = SQLOptimizer().analyze(
                verdict.normalized, st.session_state.schema
            )
            turn["risk"] = RiskChecker().check(verdict.normalized)
            turn["insights"] = InsightEngine(config).generate(
                result.dataframe, question
            )

    st.session_state.chat.append(turn)


def _render_turn(turn: dict, idx: int) -> None:
    """Render one full pipeline turn as a sequence of cards."""
    gen = turn["gen"]
    verdict = turn["verdict"]

    # 1. Natural language.
    st.markdown(
        f"<div class='card'><div class='kpi-label'>You asked</div>"
        f"<div style='font-size:1.05rem;margin-top:4px;'>{turn['question']}</div>"
        f"<span class='pill' style='margin-top:8px;display:inline-block;'>"
        f"{gen.source}</span></div>",
        unsafe_allow_html=True,
    )
    if gen.error:
        st.markdown(
            f"<div class='warn-card'>{gen.error}</div>", unsafe_allow_html=True
        )

    # 2. Generated SQL.
    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
    st.markdown("**Generated SQL**")
    st.code(gen.sql, language="sql")

    # 3. Safety gate.
    if not verdict.safe:
        st.markdown(
            f"<div class='warn-card'><b>Unsafe query blocked.</b><br>{verdict.reason}"
            "<br><span>Only read-only SELECT / WITH queries are executed.</span></div>",
            unsafe_allow_html=True,
        )
        return

    result = turn.get("result")
    if result is None:
        return
    if not result.ok:
        st.markdown(
            f"<div class='err-card'><b>Query error.</b><br>{result.error}"
            "<br><span class='muted'>Check the table and column names, then try "
            "rephrasing your question.</span></div>",
            unsafe_allow_html=True,
        )
        return

    # 4. Result + execution time.
    top = st.columns([3, 1])
    top[0].markdown("**Result**")
    top[1].markdown(
        f"<div style='text-align:right;'><span class='pill-ok pill'>"
        f"{ms(result.elapsed)}</span></div>",
        unsafe_allow_html=True,
    )
    st.dataframe(result.dataframe, use_container_width=True, height=280)
    st.markdown(
        f"<span class='muted'>{result.row_count:,} rows</span>",
        unsafe_allow_html=True,
    )

    # 5. AI explanation.
    st.markdown("**Explanation**")
    st.markdown(
        f"<div class='card'>{turn['explanation'].replace(chr(10), '<br>')}</div>",
        unsafe_allow_html=True,
    )

    # 6. Charts, insights, optimisation, export in tabs.
    tab_chart, tab_insight, tab_opt, tab_export = st.tabs(
        ["Charts", "Insights", "Optimization", "Export"]
    )

    with tab_chart:
        options = recommend_charts(result.dataframe)
        if options:
            kind = st.radio(
                "Chart type", options, horizontal=True, key=f"chart_{idx}",
                label_visibility="collapsed",
            )
            fig = build_chart(result.dataframe, kind)
            if fig is not None:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.markdown("<span class='muted'>Cannot chart this result.</span>",
                            unsafe_allow_html=True)
        else:
            st.markdown("<span class='muted'>No numeric columns to visualise.</span>",
                        unsafe_allow_html=True)

    with tab_insight:
        for ins in turn.get("insights", []):
            st.markdown(f"- {ins}")

    with tab_opt:
        opt = turn["optimization"]
        st.markdown(
            f"<span class='pill'>Estimated gain ~{opt.estimated_gain}%</span>",
            unsafe_allow_html=True,
        )
        st.write("")
        for s in opt.suggestions:
            st.markdown(f"- {s}")
        risk = turn.get("risk")
        if risk and risk.findings:
            st.markdown(
                f"<div class='warn-card' style='margin-top:10px;'>"
                f"<b>Risk: {risk.level}</b><br>"
                + "<br>".join(f"• {f}" for f in risk.findings) + "</div>",
                unsafe_allow_html=True,
            )

    with tab_export:
        df = result.dataframe
        c1, c2, c3 = st.columns(3)
        c1.download_button("CSV", to_csv_bytes(df), "result.csv", "text/csv",
                           use_container_width=True, key=f"csv_{idx}")
        c2.download_button(
            "Excel", to_excel_bytes(df), "result.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True, key=f"xlsx_{idx}",
        )
        try:
            pdf_bytes = to_pdf_bytes(df, turn["question"][:60])
            c3.download_button("PDF", pdf_bytes, "result.pdf", "application/pdf",
                               use_container_width=True, key=f"pdf_{idx}")
        except Exception:  # noqa: BLE001
            c3.markdown("<span class='muted'>PDF unavailable</span>",
                        unsafe_allow_html=True)


def render() -> None:
    page_header("Chat", "Ask a question in plain English. I will write the SQL, "
                        "run it and explain the result.")

    if not require_database():
        return

    # Reuse-from-history hook.
    prefill = st.session_state.pop("reuse_question", "")

    # Example chips.
    st.markdown("<span class='muted'>Try:</span>", unsafe_allow_html=True)
    chip_cols = st.columns(len(EXAMPLES))
    clicked_example = None
    for col, ex in zip(chip_cols, EXAMPLES):
        if col.button(ex, key=f"ex_{ex}", use_container_width=True):
            clicked_example = ex

    with st.form("ask", clear_on_submit=True):
        question = st.text_input(
            "Your question", value=prefill,
            placeholder="e.g. Show the top 10 customers by total payment",
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button("Ask", type="primary")

    to_run = None
    if submitted and question.strip():
        to_run = question.strip()
    elif clicked_example:
        to_run = clicked_example
    elif prefill:
        to_run = prefill

    if to_run:
        with st.spinner("Thinking…"):
            try:
                _run_pipeline(to_run)
            except Exception as exc:  # noqa: BLE001
                st.markdown(
                    f"<div class='err-card'><b>Could not process that question.</b>"
                    f"<br>{exc}</div>",
                    unsafe_allow_html=True,
                )

    # Render conversation, newest first.
    if st.session_state.chat:
        if st.button("Clear conversation"):
            st.session_state.chat = []
            st.rerun()
        st.write("")
        for i, turn in reversed(list(enumerate(st.session_state.chat))):
            _render_turn(turn, i)
            st.markdown("<div style='height:26px;'></div>", unsafe_allow_html=True)
