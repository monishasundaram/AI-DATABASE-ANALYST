"""
llm/prompts.py
Centralised prompt templates used across the LLM layer.
"""

# System / instruction prompt used for natural-language -> SQL generation.
SQL_SYSTEM_PROMPT = """You are an expert SQLite SQL assistant.
Generate only valid SQLite SELECT queries.
Use only the supplied schema provided.
Never invent tables.
Never invent columns.
Return response as JSON with exactly this structure:
{
  "sql": "[valid SQLite SELECT query]",
  "explanation": "[plain English explanation, max 80 words]",
  "safe": true
}"""


def build_generation_prompt(schema_text: str, question: str, history: str = "") -> str:
    """Compose the user prompt for SQL generation."""
    context = f"\nConversation so far:\n{history}\n" if history else ""
    return (
        f"Database schema:\n{schema_text}\n{context}\n"
        f"User question: {question}\n\n"
        "Respond with ONLY the JSON object described in the system instructions."
    )


def build_explanation_prompt(sql: str) -> str:
    """Prompt for a concise, bullet-point explanation of a query."""
    return (
        "Explain the following SQLite query in plain English for a "
        "non-technical reader. Use short bullet points and a maximum of "
        f"80 words total.\n\nSQL:\n{sql}"
    )


def build_insight_prompt(question: str, table_preview: str) -> str:
    """Prompt for business insights derived from a result preview."""
    return (
        "You are a data analyst. Given the user's question and a preview of "
        "the result table, produce 3 short, specific business insights as "
        "bullet points. Reference concrete numbers where possible. Keep each "
        "insight to one sentence.\n\n"
        f"Question: {question}\n\nResult preview (CSV):\n{table_preview}"
    )
