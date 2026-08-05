"""Standalone smoke test of the core (non-Streamlit) pipeline."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))

from database.loader import generate_sample_db, DatabaseLoader
from database.schema_reader import SchemaReader
from database.executor import QueryExecutor
from security.validator import SQLValidator
from security.risk_checker import RiskChecker
from llm.optimizer import SQLOptimizer
from llm.sql_explainer import SQLExplainer
from llm.sql_generator import SQLGenerator
from analytics.charts import recommend_charts, build_chart
from analytics.insights import InsightEngine
from history.storage import HistoryManager
from utils.exporters import to_csv_bytes, to_excel_bytes, to_pdf_bytes


class Cfg:  # minimal stand-in for AppConfig (offline)
    provider = "openai"; configured = False
    openai_key = ""; openai_model = "gpt-4o"; gemini_key = ""; gemini_model = "x"


def main():
    path = generate_sample_db(overwrite=True)
    assert DatabaseLoader(path).is_valid_sqlite(), "sample db invalid"

    with DatabaseLoader(path).connect() as conn:
        reader = SchemaReader(conn)
        schema = reader.build()
        schema_text = reader.to_prompt_text(schema)
    s = schema["stats"]
    print("schema:", s)
    assert s["table_count"] == 6 and s["row_count"] > 0 and s["relationship_count"] >= 5

    gen = SQLGenerator(Cfg())
    for q in ["Show top customers by payment", "How many orders?",
              "average unit price", "list recent orders", "employees"]:
        r = gen.generate(q, schema_text, schema)
        v = SQLValidator().validate(r.sql)
        assert v.safe, f"unsafe for {q}: {r.sql}"
        res = QueryExecutor(path).run(v.normalized)
        assert res.ok, f"exec failed {q}: {res.error}"
        print(f"OK  {q!r:42} -> {res.row_count} rows in {res.elapsed*1000:.1f}ms")

    # Safety: forbidden statements blocked
    for bad in ["DROP TABLE Orders", "DELETE FROM Orders",
                "SELECT * FROM Orders; DROP TABLE Orders", "PRAGMA table_info(Orders)"]:
        assert not SQLValidator().validate(bad).safe, f"should block: {bad}"
    print("safety: all forbidden statements blocked")

    # Optimizer / explainer / risk
    sql = "SELECT * FROM Orders ORDER BY quantity DESC"
    opt = SQLOptimizer().analyze(sql, schema)
    print("optimizer gain:", opt.estimated_gain, "| suggestions:", len(opt.suggestions))
    print("explain:", SQLExplainer(Cfg()).explain(sql).replace("\n", " | "))
    print("risk:", RiskChecker().check(sql).level)

    # Analytics + exports on a real result
    df = QueryExecutor(path).run(
        "SELECT category, COUNT(*) n, AVG(unit_price) avg_price "
        "FROM Products GROUP BY category").dataframe
    print("chart options:", recommend_charts(df))
    assert build_chart(df, "Bar") is not None
    print("insights:", InsightEngine(Cfg()).generate(df, "by category")[:2])
    assert len(to_csv_bytes(df)) > 0
    assert len(to_excel_bytes(df)) > 0
    assert len(to_pdf_bytes(df, "Test")) > 0
    print("exports: csv/excel/pdf OK")

    # History store
    h = HistoryManager(os.path.join(os.path.dirname(__file__), "history", "_test.db"))
    h.clear(); h.add("q1", sql, 12.3, 5)
    assert h.count() == 1 and len(h.recent()) == 1 and h.all(search="q1")
    hid = h.all()[0].id; h.toggle_bookmark(hid); assert h.all(bookmarked_only=True)
    h.delete(hid); assert h.count() == 0
    os.remove(os.path.join(os.path.dirname(__file__), "history", "_test.db"))
    print("history: crud OK")

    print("\nALL SMOKE TESTS PASSED")


if __name__ == "__main__":
    main()
