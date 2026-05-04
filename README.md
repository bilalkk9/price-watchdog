# Price Watchdog

**Autonomous AI price tracker for Pakistani e-commerce**

> Live Demo: [https://price-watchdog.streamlit.app/](https://price-watchdog.streamlit.app/)

Price Watchdog is an intelligent AI agent that autonomously tracks product prices across Pakistani e-commerce websites (PriceOye, Daraz, Sapphire, Khaadi, and more). Unlike traditional scrapers that break when a website updates its layout, Price Watchdog uses **Google Gemini AI** to semantically read and understand page content — just like a human would.

---

## Features

- **AI-powered extraction** — Gemini reads the page and identifies the main product price, ignoring ads, sidebar items, and related products
- **Variant detection** — detects colors, storage sizes, and other variants
- **Price comparison** — calculates % difference against your target price
- **Availability monitoring** — tracks In Stock / Out of Stock / Limited Stock status
- **Alerts** — console notification + Gmail email when price drops to your target
- **Price history** — SQLite database with trend charts (Plotly)
- **Streamlit dashboard** — 5-page web UI for managing tracked products
- **Scheduler** — automated checks every N hours

---

## Tech Stack

| Tool | Purpose |
|------|---------|
| Python 3.12 | Core language |
| CrewAI | ReAct agent framework |
| Google Gemini 2.5 Flash | LLM for price extraction & reasoning |
| BeautifulSoup4 | Web scraping |
| SQLite | Local price history database |
| Streamlit | Web dashboard |
| Plotly | Price trend charts |
| smtplib | Gmail email alerts |

---

## Setup

### 1. Clone and install

```bash
git clone https://github.com/bilalkk9/price-watchdog.git
cd price-watchdog
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

### 2. Configure

```bash
copy .env.example .env
```

Edit `.env`:

```
GEMINI_API_KEY=your_gemini_api_key_here
GMAIL_ADDRESS=your_email@gmail.com
GMAIL_APP_PASSWORD=your_app_password_here
CHECK_INTERVAL_HOURS=6
```

Get a free Gemini API key at [aistudio.google.com](https://aistudio.google.com) — no credit card required.

### 3. Run

```bash
# Launch dashboard
venv\Scripts\python.exe main.py dashboard

# One-time price check
venv\Scripts\python.exe main.py check --url "https://priceoye.pk/samsung-galaxy-s24" --target 50000

# Continuous monitoring (every 6 hours)
venv\Scripts\python.exe main.py monitor --interval 6

# List all tracked products
venv\Scripts\python.exe main.py list
```

---

## Project Structure

```
price-watchdog/
├── config.py               # Environment variables & settings
├── crew.py                 # CrewAI orchestrator
├── main.py                 # CLI entry point & scheduler
├── agents/
│   ├── price_agent.py      # CrewAI agent definition
│   ├── tasks.py            # Task definitions
│   └── tools.py            # Tools: scrape, extract, compare, notify
├── core/
│   ├── database.py         # SQLite CRUD operations
│   ├── llm_client.py       # Gemini API wrapper
│   ├── notifier.py         # Console + email alerts
│   ├── scraper.py          # BeautifulSoup4 scraper
│   └── url_validator.py    # URL validation
├── dashboard/
│   ├── app.py              # Streamlit dashboard (5 pages)
│   └── components.py       # Reusable UI components
└── data/
    ├── price_history.db    # SQLite database (auto-created)
    └── exports/            # CSV / JSON exports
```

---

## How It Works

Price Watchdog follows the **ReAct (Reasoning + Acting)** architecture:

1. **Validate** — checks the URL is reachable
2. **Scrape** — fetches page HTML and extracts clean text
3. **Extract** — Gemini AI identifies the main product price (ignoring related items)
4. **Compare** — calculates % difference vs your target price
5. **History** — checks previous prices to detect changes
6. **Save** — records the result to SQLite
7. **Notify** — sends alert if price dropped to or below target

---

## Functional Requirements

| # | Requirement | Status |
|---|-------------|--------|
| FR1 | URL validation (Up/Down/Invalid) | Done |
| FR2 | Intelligent content extraction (ignores ads/sidebar) | Done |
| FR3 | Variant detection (color, storage, size) | Done |
| FR4 | Autonomous price comparison with % difference | Done |
| FR5 | Availability monitoring | Done |
| FR6 | Console + email notifications | Done |
| FR7 | SQLite history, price trend chart, CSV/JSON export | Done |

---

## Notes

- Free tier Gemini API: 20 requests/day for `gemini-2.5-flash`
- Each price check uses ~8-10 API calls
- For more capacity, create additional Google Cloud projects (each gets its own free quota)

---

## University Project

**Domain:** Artificial Intelligence / Web Programming / Web Automation  
**Supervisor:** Faizan Tahir — fazitahir@vu.edu.pk
