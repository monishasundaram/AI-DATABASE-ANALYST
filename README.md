<div align="center">

# AI Database Analyst

**Ask your database questions in plain English. Get safe SQL, results, charts, and insights.**

![Python](https://img.shields.io/badge/Python-3.10%2B-2563EB?style=flat-square&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-App-2563EB?style=flat-square&logo=streamlit&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-Read--only-2563EB?style=flat-square&logo=sqlite&logoColor=white)
![Works offline](https://img.shields.io/badge/Works-Offline-2563EB?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-2563EB?style=flat-square)

</div>


---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [How It Works](#how-it-works)
- [Safety Model](#safety-model)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Usage](#usage)
- [Example Questions](#example-questions)
- [Project Structure](#project-structure)
- [Tech Stack](#tech-stack)
- [Troubleshooting](#troubleshooting)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

AI Database Analyst turns everyday questions into **validated, read-only SQLite queries**. It generates the SQL, checks it, runs it, explains the result in plain English, charts it, and suggests how to make the query faster, all in a clean, minimalist interface.

**It works with no API key.** A built-in heuristic engine runs the full pipeline offline. Add an OpenAI or Google Gemini key in Settings and the same app upgrades to fully AI-generated SQL.

| | |
|---|---|
| **Zero setup to try** | Generate a six-table sample database in one click |
| **Safe by design** | Only `SELECT` / `WITH` statements can ever run |
| **Provider-flexible** | Offline engine, OpenAI (GPT-4o, GPT-4 Turbo), or Gemini |
| **More than SQL** | Explanations, auto-charts, business insights, optimization tips |

---

## Features

### Ask
- **AI chat** with session memory, so follow-up questions work naturally.
- **Full pipeline per question:** natural language, syntax-highlighted SQL, result table, plain-English explanation (80 words or fewer), and execution time in ms.

### Understand
- **Auto-charts:** detects numeric data and recommends bar, pie, line, or scatter charts (interactive Plotly). Switch types on the fly.
- **Business insights:** contextual, number-aware takeaways from each result.
- **AI optimization:** flags `SELECT *`, suggests indexes, detects unnecessary joins and columns, and shows an estimated performance improvement.

### Manage
- **Dashboard:** KPI cards (tables, rows, columns, relationships), recent queries, database info, and optimization suggestions.
- **Database upload and auto-detection:** upload any `.db` / `.sqlite` file. Schema, primary keys, and foreign-key relationships are detected and shown hierarchically.
- **Query history:** auto-saved, with search, delete, reuse, and bookmarks, backed by a persistent SQLite store.
- **Export:** download any result as CSV, Excel, or PDF.
- **Global search:** filter tables and columns on the Database page, and queries on the History page.
- **Settings:** provider (OpenAI / Gemini), API key, model selection, and clear history.

---

## How It Works

```
              ┌──────────────────────────────────────────────┐
   Sidebar →  │  app.py  (router · streamlit-option-menu)    │
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

1. **LLM layer** generates SQL from your question (AI provider or offline heuristic engine).
2. **Security layer** validates it against an allow-list and runs advisory risk checks.
3. **Database layer** executes it read-only against SQLite.
4. **Analytics layer** produces charts and insights.
5. **History layer** persists every executed query.

Each module has a single responsibility, so swapping the LLM provider or the database backend touches one layer only.

---

## Safety Model

Generated SQL is never trusted. Every query passes through an **allow-list validator** before it reaches the database.

| Allowed | Blocked (with a clear warning card) |
|---|---|
| `SELECT` | `INSERT`, `UPDATE`, `DELETE` |
| `WITH` (CTEs) | `DROP`, `ALTER`, `CREATE`, `TRUNCATE` |
| | `PRAGMA`, `ATTACH`, `DETACH`, `VACUUM` |
| | Stacked statements (`;` chaining) |

A separate **risk checker** adds advisory warnings (for example, unbounded scans) without blocking valid queries.

---

## Quick Start

**Requirements:** Python 3.10+

```bash
# 1. Clone
git clone https://github.com/monishasundaram/AI-Database-Analyst.git
cd AI-Database-Analyst

# 2. (Recommended) create a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) configure an AI provider
cp .env.example .env             # then edit .env with your key

# 5. Run
streamlit run app.py
```

The app opens at **http://localhost:8501**.

---

## Configuration

AI is optional. With no key, the offline heuristic engine handles everything.

You can configure a provider in two ways:

- **In the app:** open **Settings**, choose OpenAI or Gemini, paste your key, and pick a model.
- **Via `.env`:** copy `.env.example` to `.env` and fill in the values it lists.

| Provider | Models | Needs key |
|---|---|---|
| Offline heuristic | Built in | No |
| OpenAI | GPT-4o, GPT-4 Turbo | Yes |
| Google Gemini | Gemini models | Yes |

> Never commit your `.env` file. Make sure it is listed in `.gitignore`.

---

## Usage

1. Open the **Database** page and click **Generate & load sample**, or upload your own SQLite file.
2. Go to **Chat** and ask a question, for example: *"Show the top 10 customers by total payment."*
3. Review the generated SQL, result table, explanation, charts, insights, and optimization tips.
4. **Export** the result as CSV, Excel, or PDF, or revisit it later from **History**.
5. Add an OpenAI or Gemini key in **Settings** for smarter, fully AI-generated SQL.

---

## Example Questions

```text
Show the top 10 customers by total payment
How many orders were placed each month this year?
Which products have never been ordered?
What is the average order value by country?
List employees along with their manager's name
```

Follow-ups work too: *"Now only show customers from Germany."*

---

## Project Structure

```
AI-Database-Analyst/
├── app.py                  # Router + sidebar navigation
├── requirements.txt        # Pinned dependencies
├── README.md
├── .env.example            # Provider keys & config template
├── .streamlit/config.toml  # Theme + native navigation disabled
│
├── pages/                  # One render() per screen
│   ├── Dashboard.py  Chat.py  Database.py  History.py  Settings.py
│
├── database/               # Loader (+ sample generator), schema reader, executor
├── llm/                    # Prompts, SQL generator, explainer, optimizer
├── security/               # Validator (allow-list), risk checker (advisory)
├── analytics/              # Charts (Plotly), insights
├── history/                # Persistent SQLite history store
├── utils/                  # Helpers (config/styles), exporters (CSV/Excel/PDF)
├── assets/
└── sample_database/        # Generated sample.db lives here
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| UI | Streamlit, streamlit-option-menu |
| Charts | Plotly |
| Data | SQLite |
| AI (optional) | OpenAI API, Google Gemini API |
| Export | CSV, Excel, PDF |

**Design system:** white surfaces, black type, a single blue accent (`#2563EB`), 12px radii, generous whitespace.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `streamlit: command not found` | Activate your virtual environment, or run `python -m streamlit run app.py` |
| Port 8501 already in use | Run `streamlit run app.py --server.port 8502` |
| Query was blocked | Only `SELECT` / `WITH` are allowed. Rephrase as a read-only question |
| AI answers look generic or fail | Check your API key and model in **Settings**. The app falls back to the offline engine |
| Uploaded database shows no tables | Confirm the file is a valid SQLite `.db` / `.sqlite` file |

---

## Roadmap

- [ ] PostgreSQL and MySQL support via SQLAlchemy
- [ ] Query result caching and pagination for large tables
- [ ] Saved dashboards built from bookmarked queries
- [ ] Role-based access control and audit logging for teams
- [ ] Streaming SQL generation and inline auto-correction
- [ ] Natural-language chart configuration (*"make this a stacked bar by month"*)

---

## Contributing

Contributions are welcome.

1. Fork the repo and create a branch: `git checkout -b feature/your-feature`
2. Keep modules single-purpose and follow the existing folder layout.
3. Never loosen the allow-list in `security/validator.py` without discussion.
4. Open a pull request describing what changed and why.

---
