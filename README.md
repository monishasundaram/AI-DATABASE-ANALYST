# AI Database Analyst

A premium, minimalist **natural-language-to-SQL** assistant for SQLite databases.
Ask questions in plain English; the app writes safe SQL, executes it, explains the
result, visualises it, and surfaces optimisation tips and business insights — all
behind a clean, Notion/Linear-inspired interface.

---

## Overview

AI Database Analyst turns everyday questions into validated SQLite queries. It ships
with a fully offline heuristic engine so it runs end-to-end **without any API key**,
and upgrades to GPT-4o / GPT-4 Turbo or Google Gemini the moment you add credentials
in Settings.

The application is built with **Streamlit**, styled with a strict minimalist design
system (white surfaces, black type, a single blue accent `#2563EB`, 12px radii,
generous whitespace), and organised into small, single-responsibility modules.

## Architecture

```
              ┌──────────────────────────────────────────────┐
   Sidebar →  │  app.py  (router · streamlit-option-menu)     │
              └───────────────┬──────────────────────────────┘
                              │  renders one of
        ┌─────────────┬───────┴───────┬─────────────┬──────────────┐
     Dashboard      Chat            Database       History        Settings
                     │
                     ▼   NL → SQL pipeline
   ┌───────────┐  ┌────────────┐  ┌───────────┐  ┌────────────┐  ┌──────────┐
   │  llm/     │→ │ security/  │→ │ database/ │→ │ analytics/ │→ │ history/ │
   │ generator │  │ validator  │  │ executor  │  │ charts +   │  │ storage  │
   │ explainer │  │ risk_check │  │ schema    │  │ insights   │  │ (SQLite) │
   │ optimizer │  └────────────┘  └───────────┘  └────────────┘  └──────────┘
   └───────────┘
```

Flow: a question flows from the **LLM layer** (SQL generation) into the **security
layer** (allow-list validation + advisory risk checks), then the **database layer**
(read-only execution against SQLite), and finally the **analytics layer**
(auto-charts + insights). Every executed query is persisted by the **history layer**.

## Features

- **Dashboard** — KPI cards (tables, rows, columns, relationships), recent queries,
  database information and AI optimisation suggestions.
- **Database upload & auto-detection** — upload any `.db`/`.sqlite` file or generate a
  realistic six-table sample database; schema, primary keys and foreign-key
  relationships are detected automatically and shown in a hierarchical view.
- **AI chat** — session-based conversation memory; ask follow-up questions naturally.
- **Full SQL pipeline** — natural language → generated SQL (syntax highlighted) →
  tabular result → plain-English explanation (≤ 80 words) → execution time in ms.
- **Strict safety validation** — only `SELECT` / `WITH` run; `INSERT`, `UPDATE`,
  `DELETE`, `DROP`, `ALTER`, `CREATE`, `TRUNCATE`, `PRAGMA`, `ATTACH`, `DETACH`,
  `VACUUM` and stacked statements are blocked with a clear warning card.
- **AI optimisation** — flags `SELECT *`, suggests indexes, detects unnecessary
  joins/columns and shows an estimated performance-improvement percentage.
- **Auto-charts** — detects numeric data and recommends bar / pie / line / scatter
  charts (interactive Plotly); switch types on the fly.
- **Business insights** — contextual, number-aware takeaways from each result.
- **Query history** — auto-saved with search, delete, reuse and bookmark, backed by a
  persistent SQLite store.
- **Export** — download any result as CSV, Excel or PDF.
- **Global search** — filter tables/columns on the Database page and queries on the
  History page.
- **Settings** — provider (OpenAI / Gemini), API key, model selection and clear-history.

## Installation

```bash
# 1. (optional) create a virtual environment
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate

# 2. install dependencies
pip install -r requirements.txt

# 3. (optional) configure an AI provider
cp .env.example .env          # then edit .env with your key

# 4. run
streamlit run app.py
```

The app opens at `http://localhost:8501`.

## Usage

1. Open the **Database** page and click **Generate & load sample** (or upload your own
   SQLite file).
2. Go to **Chat** and ask something like *"Show the top 10 customers by total payment"*.
3. Review the generated SQL, result table, explanation, charts, insights and
   optimisation tips.
4. Export the result, or revisit it later from **History**.
5. Add an OpenAI or Gemini key in **Settings** for smarter, fully AI-generated SQL.
   Without a key, a built-in heuristic engine keeps everything working offline.

## Folder structure

```
AI-Database-Analyst/
├── app.py                  # Router + sidebar navigation
├── requirements.txt        # Pinned dependencies
├── README.md
├── .env.example            # Provider keys & config template
├── .streamlit/config.toml  # Theme + native-nav disabled
│
├── pages/                  # One render() per screen
│   ├── Dashboard.py  Chat.py  Database.py  History.py  Settings.py
│
├── database/               # loader (+ sample generator), schema_reader, executor
├── llm/                    # prompts, sql_generator, sql_explainer, optimizer
├── security/               # validator (allow-list), risk_checker (advisory)
├── analytics/              # charts (Plotly), insights
├── history/                # persistent SQLite history store
├── utils/                  # helpers (config/styles), exporters (CSV/Excel/PDF)
├── assets/
└── sample_database/        # generated sample.db lives here
```

## Future enhancements

- Multi-database and non-SQLite backends (PostgreSQL, MySQL) via SQLAlchemy.
- Query result caching and pagination for very large tables.
- Saved dashboards composed from bookmarked queries.
- Role-based access control and audit logging for team use.
- Streaming token-by-token SQL generation and inline query auto-correction.
- Natural-language chart configuration ("make this a stacked bar by month").

---
