# Stack & Paths

Python 3.12 · venv at `venv/` · run via `venv/bin/python`

| Layer | Library | Notes |
|-------|---------|-------|
| Agent | crewai ≥1.14 | ReAct pattern |
| LLM | google-genai | model: gemini-2.5-flash |
| Scrape | requests + bs4 | no JS execution |
| DB | sqlite3 (stdlib) | file: data/price_history.db |
| UI | streamlit + plotly | `streamlit run dashboard/app.py` |
| Notify | smtplib (stdlib) | Gmail SMTP port 587 TLS |
| Scheduler | schedule | `main.py monitor` |

Key paths: `config.py` · `core/` · `agents/` · `dashboard/` · `tests/`
Env vars: `GEMINI_API_KEY` `GMAIL_ADDRESS` `GMAIL_APP_PASSWORD` `CHECK_INTERVAL_HOURS`
