# PRICE WATCHDOG — Complete Project Specification & Development Guide

> **Purpose of this document**: This is a comprehensive specification for the "Price Watchdog: Autonomous Multi-Platform E-commerce Agent" project. It is written so that an AI coding assistant (Claude Code in VS Code) can understand every requirement, architectural decision, and implementation detail needed to build this project from scratch. Read this document fully before writing any code.

---

## 1. PROJECT OVERVIEW

### 1.1 What is Price Watchdog?

Price Watchdog is an intelligent AI agent that autonomously tracks product prices across Pakistani e-commerce websites. Unlike traditional web scrapers that use brittle CSS selectors and break when a website changes its layout, Price Watchdog uses a **Reasoning Agent** powered by a Large Language Model (LLM) that semantically understands web page content.

The agent can visit a product URL, distinguish the **main product's price** from "Related Products," "Advertisements," or "Similar Items" on the page, and compare it against a user-defined target price. When a price drop is detected, the agent generates a structured alert with its reasoning.

### 1.2 Architecture Pattern

This project follows the **ReAct (Reasoning + Acting)** architecture:
1. **Reasoning**: The agent thinks step-by-step about what it sees on a web page
2. **Acting**: The agent takes actions using tools (scrape URL, extract price, compare, notify)
3. **Observing**: The agent observes the results of its actions and reasons about the next step

This is an **agentic AI** system — the LLM is not just answering questions, it is autonomously making decisions and executing a workflow.

### 1.3 Target E-commerce Sites (Pakistan)
- PriceOye.pk (electronics, mobiles)
- Daraz.pk (general marketplace)
- Sapphire.pk (clothing/fashion)
- Khaadi.com (clothing/fashion)
- iShopping.pk (electronics)
- Any other URL the user provides

### 1.4 Project Domain
Artificial Intelligence / Web Programming / Web Automation

### 1.5 Supervisor
- **Name**: Faizan Tahir
- **Email**: fazitahir@vu.edu.pk
- **MS Teams**: faizan.vu@outlook.com

---

## 2. FUNCTIONAL REQUIREMENTS (MANDATORY — ALL 7 MUST BE IMPLEMENTED)

These are the exact requirements from the project proposal. Every single one must be implemented.

### FR1: URL Processing & Validation
- The system must accept a single product URL from the user
- It must verify the URL's status (Up/Down) before proceeding
- Must handle invalid URLs, timeouts, connection errors gracefully
- Must return clear status messages: "URL is reachable", "URL is down", "Invalid URL format"

### FR2: Intelligent Content Extraction
- The agent must use an LLM (Gemini) to extract from raw web data:
  - **Product Name** (full name, not abbreviated)
  - **Current Price** (numeric value)
  - **Currency** (PKR, USD, etc.)
- The agent must **specifically ignore**:
  - Sidebar prices
  - "Similar items" or "Related products" prices
  - Advertisement prices
  - "You may also like" section prices
- The extraction must be **semantic** — the LLM reads the page content and understands which price belongs to the main product, not through CSS selectors

### FR3: Variant Detection
- If a product has multiple versions/variants (e.g., iPhone 128GB vs 256GB, different colors, different sizes), the agent must:
  - Detect that variants exist
  - Identify **which specific variant's price** it is tracking
  - Log this choice clearly (e.g., "Tracking: Samsung Galaxy S24 - 256GB - Phantom Black - PKR 249,999")
- If no variants exist, the agent should note "No variants detected"

### FR4: Autonomous Comparison Logic
- The system must compare the extracted price against the user's "Target Price"
- It must calculate the **percentage difference** between current and target price
- It must determine if an alert is necessary based on:
  - Price dropped **below** or **equal to** target → ALERT
  - Price dropped but still **above** target → LOG but no alert
  - Price **increased** since last check → LOG the increase
- The agent must provide a **reasoning summary** explaining WHY an alert was or wasn't triggered

### FR5: Availability Monitoring
- The agent must detect and report if a product goes "Out of Stock" or "Unavailable"
- It must NOT simply fail silently when no price is found
- Possible statuses: "In Stock", "Out of Stock", "Limited Stock", "Pre-Order", "Unknown"
- If a product was out of stock and comes **back in stock**, this should also trigger a notification

### FR6: Notification Trigger
- The system must generate a structured alert containing:
  - Product name
  - Previous price (if available)
  - Current price
  - Price drop **percentage**
  - Direct link to the product
  - Agent's reasoning (why the alert was triggered)
  - Timestamp
- Alert channels (implement at least one, ideally both):
  - **Console output** (always — for demo/viva purposes)
  - **Email via SMTP** (Gmail — free, uses Python's built-in smtplib)
- Alert format should be clean and readable, not raw JSON dumps

### FR7: History Management
- The system must store **all** previous price checks in a local database/file
- Storage format: SQLite database (preferred) OR JSON/CSV files
- Each record must include:
  - Product URL
  - Product name
  - Price extracted
  - Currency
  - Variant (if applicable)
  - Availability status
  - Timestamp of check
  - Agent's reasoning summary
- The system must be able to show a **simple price trend** to the user (price over time)
- Export to JSON/CSV must be supported

---

## 3. TECH STACK (ALL FREE — NO PAID TOOLS)

### 3.1 Core Technologies

| Tool | Version | Purpose | Cost |
|------|---------|---------|------|
| Python | 3.10+ (recommend 3.11 or 3.12) | Core programming language | Free |
| CrewAI | Latest stable (currently ~1.14.x) | AI Agent framework — defines agents, tasks, tools, crew | Free (open-source) |
| Google Gemini API | 2.5 Flash (free tier) | LLM brain — reasoning, content extraction, comparison | Free (no credit card needed) |
| BeautifulSoup4 | Latest | Web scraping — fetching and parsing HTML | Free |
| Requests | Latest | HTTP requests to product URLs | Free |
| SQLite | Built-in (Python stdlib) | Local database for price history | Free |
| Streamlit | Latest | Web dashboard UI | Free |
| Plotly | Latest | Interactive price trend charts | Free |
| smtplib | Built-in (Python stdlib) | Email notifications via Gmail SMTP | Free |
| python-dotenv | Latest | Environment variable management (.env file) | Free |
| schedule | Latest | Periodic price checking on intervals | Free |

### 3.2 Gemini API Setup Details

- **Sign up**: Go to https://aistudio.google.com → Click "Get API Key" → Create in new project
- **No credit card required** for free tier
- **Model to use**: `gemini-2.5-flash` (stable, free tier)
- **Free tier limits (as of 2026)**:
  - Gemini 2.5 Flash: ~10-15 RPM (requests per minute), 100-1000 RPD (requests per day)
  - 250,000 tokens per minute
  - This is MORE than enough for a price tracker that checks a few URLs every few hours
- **SDK**: Use the new `google-genai` SDK (the old `google-generativeai` package was deprecated Nov 2025)
- **Store API key in `.env` file**, never hardcode it

### 3.3 CrewAI Setup Details

- **Install**: `pip install crewai`
- CrewAI requires Python >=3.10 <3.14
- CrewAI uses the concept of **Agents**, **Tasks**, **Tools**, and **Crews**
- An **Agent** has: role, goal, backstory, LLM, tools
- A **Task** has: description, expected_output, agent
- A **Tool** is a Python function the agent can call (decorated with @tool)
- A **Crew** combines agents and tasks and executes them
- CrewAI supports Gemini natively via LiteLLM integration — use `model="gemini/gemini-2.5-flash"`

### 3.4 Development Environment
- **IDE**: VS Code with Python extension
- **Version Control**: Git + GitHub
- **Virtual Environment**: Use `venv` or `uv` (CrewAI prefers uv)

---

## 4. PROJECT STRUCTURE

```
price-watchdog/
│
├── .env                          # API keys and config (NEVER commit this)
├── .env.example                  # Template for .env (commit this)
├── .gitignore                    # Ignore .env, __pycache__, .db files, etc.
├── requirements.txt              # All Python dependencies
├── README.md                     # Project documentation
│
├── config.py                     # Load environment variables, app settings
│
├── core/
│   ├── __init__.py
│   ├── scraper.py                # Web scraping with BeautifulSoup4/requests
│   ├── llm_client.py             # Gemini API wrapper (send prompts, get responses)
│   ├── database.py               # SQLite database operations (CRUD for price history)
│   ├── notifier.py               # Email (smtplib) and console notification system
│   └── url_validator.py          # URL validation and status checking (FR1)
│
├── agents/
│   ├── __init__.py
│   ├── tools.py                  # CrewAI @tool definitions (scrape, extract, compare, etc.)
│   ├── price_agent.py            # CrewAI Agent definition (role, goal, backstory)
│   └── tasks.py                  # CrewAI Task definitions (what the agent does)
│
├── crew.py                       # CrewAI Crew definition — orchestrates agents + tasks
│
├── dashboard/
│   ├── app.py                    # Streamlit main dashboard
│   └── components.py             # Reusable Streamlit UI components (charts, cards, etc.)
│
├── data/
│   ├── price_history.db          # SQLite database file (auto-created)
│   └── exports/                  # JSON/CSV export directory
│
├── main.py                       # Entry point: CLI interface + scheduler
│
└── tests/
    ├── __init__.py
    ├── test_url_validator.py     # Test URL validation
    ├── test_scraper.py           # Test scraping real URLs
    ├── test_extraction.py        # Test LLM extraction accuracy
    └── test_database.py          # Test database operations
```

---

## 5. DETAILED IMPLEMENTATION GUIDE

### 5.1 Phase 1: Foundation (config, URL validation, scraping, database)

#### 5.1.1 `.env` File Structure
```
GEMINI_API_KEY=your_gemini_api_key_here
GMAIL_ADDRESS=your_email@gmail.com
GMAIL_APP_PASSWORD=your_app_password_here
CHECK_INTERVAL_HOURS=6
```

#### 5.1.2 `config.py`
- Load all environment variables using `python-dotenv`
- Define constants: DEFAULT_CHECK_INTERVAL, MAX_RETRIES, REQUEST_TIMEOUT, DATABASE_PATH
- Validate that required env vars exist on startup

#### 5.1.3 `core/url_validator.py` (FR1)
- Function `validate_url(url: str) -> dict` that:
  - Checks URL format using `urllib.parse`
  - Sends a HEAD request (with timeout=10s) to check if site is reachable
  - Returns: `{"valid": True/False, "status": "Up"/"Down"/"Invalid", "status_code": 200, "response_time_ms": 145}`
  - Handles exceptions: ConnectionError, Timeout, InvalidURL, etc.
  - Uses a realistic User-Agent header to avoid being blocked

#### 5.1.4 `core/scraper.py`
- Function `scrape_url(url: str) -> dict` that:
  - Sends a GET request to the URL with headers mimicking a real browser
  - Parses the HTML with BeautifulSoup4
  - Extracts the **text content** of the page (strips all HTML tags, scripts, styles)
  - Also extracts the page `<title>` and any `<meta>` description
  - Returns: `{"success": True, "text_content": "...", "title": "...", "url": url}`
  - Truncates text content to ~4000-6000 tokens to stay within Gemini free tier limits
  - Handles: SSL errors, encoding issues, JavaScript-heavy pages (note: BS4 doesn't execute JS — for JS-rendered pages, we rely on whatever static HTML the server returns)
- Include retry logic (3 attempts with exponential backoff)
- Set User-Agent to a recent Chrome browser string

#### 5.1.5 `core/database.py` (FR7)
- Uses Python's built-in `sqlite3` module
- Database schema:

```sql
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL UNIQUE,
    name TEXT,
    target_price REAL NOT NULL,
    currency TEXT DEFAULT 'PKR',
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS price_checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    price REAL,
    currency TEXT DEFAULT 'PKR',
    variant TEXT,
    availability TEXT DEFAULT 'Unknown',
    agent_reasoning TEXT,
    raw_extraction TEXT,
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    alert_type TEXT NOT NULL,  -- 'price_drop', 'back_in_stock', 'target_reached'
    old_price REAL,
    new_price REAL,
    drop_percentage REAL,
    message TEXT,
    sent_via TEXT,  -- 'console', 'email', 'both'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id)
);
```

- Implement CRUD functions:
  - `add_product(url, target_price, currency='PKR') -> product_id`
  - `get_product(product_id) -> dict`
  - `get_product_by_url(url) -> dict`
  - `get_all_products(active_only=True) -> list[dict]`
  - `update_product(product_id, **kwargs)`
  - `deactivate_product(product_id)`
  - `add_price_check(product_id, price, currency, variant, availability, reasoning, raw) -> check_id`
  - `get_price_history(product_id, limit=50) -> list[dict]`
  - `get_latest_price(product_id) -> dict`
  - `add_alert(product_id, alert_type, old_price, new_price, drop_pct, message, sent_via)`
  - `get_alerts(product_id=None, limit=20) -> list[dict]`
  - `export_history_json(product_id, filepath)`
  - `export_history_csv(product_id, filepath)`

#### 5.1.6 `core/llm_client.py`
- Wrapper around the Google GenAI SDK
- Uses `google-genai` (NOT the deprecated `google-generativeai`)
- Install: `pip install google-genai`
- Function `ask_gemini(prompt: str, system_instruction: str = None) -> str`
  - Sends a prompt to Gemini 2.5 Flash
  - Returns the text response
  - Handles rate limiting (429 errors) with exponential backoff
  - Handles API errors gracefully
- Function `extract_product_info(page_content: str) -> dict`
  - Sends a carefully crafted prompt asking Gemini to extract product info from the page text
  - The prompt must specifically instruct the LLM to:
    1. Find the MAIN product on the page (not related/similar items)
    2. Extract: product_name, current_price (numeric only), currency, availability_status
    3. Detect variants (if any) and note which variant the price belongs to
    4. Return the response as a structured JSON
  - Parse the LLM response as JSON
  - Validate the parsed data (price should be a number, name shouldn't be empty)

**Critical Prompt for FR2 + FR3 (Intelligent Content Extraction + Variant Detection):**

```
You are a product price extraction specialist. You are given the text content of an e-commerce product page. Your job is to extract ONLY the main product's information, ignoring all sidebar items, related products, advertisements, "you may also like" sections, and similar/recommended products.

Analyze the text carefully and extract:

1. product_name: The full name of the MAIN product being sold on this page
2. current_price: The current selling price as a NUMBER ONLY (no currency symbols, no commas). If there's a sale/discount price and an original price, use the SALE price.
3. original_price: The original/strikethrough price if a discount is shown, otherwise null
4. currency: The currency code (PKR, USD, etc.)
5. availability: One of: "In Stock", "Out of Stock", "Limited Stock", "Pre-Order", "Unknown"
6. variants: A list of detected variants (e.g., storage sizes, colors, etc.) or empty list if none
7. tracked_variant: Which specific variant this price belongs to, or null if no variants

IMPORTANT RULES:
- There may be MANY prices on the page from related products. ONLY extract the main product's price.
- The main product is typically the one in the page title, the one with the largest price display, or the one with "Add to Cart" button nearby.
- If you see multiple prices for the same product (e.g., "Rs. 45,999" crossed out and "Rs. 39,999"), the lower one is the current price and the higher one is the original price.
- Return ONLY valid JSON, no markdown, no explanation, no backticks.

PAGE CONTENT:
{page_content}

Respond with ONLY this JSON structure:
{
  "product_name": "...",
  "current_price": 39999,
  "original_price": 45999,
  "currency": "PKR",
  "availability": "In Stock",
  "variants": ["128GB", "256GB"],
  "tracked_variant": "256GB"
}
```

### 5.2 Phase 2: AI Agent (CrewAI integration)

#### 5.2.1 `agents/tools.py`
Define CrewAI tools using the `@tool` decorator. Each tool is a Python function the agent can call during its reasoning process.

```python
from crewai import tool

@tool("Validate URL")
def validate_url_tool(url: str) -> str:
    """Checks if a product URL is valid and reachable. Returns status (Up/Down/Invalid)."""
    # Call core/url_validator.py
    ...

@tool("Scrape Product Page")
def scrape_page_tool(url: str) -> str:
    """Fetches the content of a product page and returns the text content for analysis."""
    # Call core/scraper.py
    ...

@tool("Extract Product Info")
def extract_product_info_tool(page_content: str) -> str:
    """Uses AI to extract product name, price, currency, variants from page content. Ignores sidebar/related items."""
    # Call core/llm_client.py extract_product_info()
    ...

@tool("Compare Price")
def compare_price_tool(current_price: float, target_price: float) -> str:
    """Compares current price with target price. Returns comparison result with percentage difference."""
    ...

@tool("Check Price History")
def check_history_tool(product_url: str) -> str:
    """Retrieves the price history for a product to identify trends."""
    # Call core/database.py get_price_history()
    ...

@tool("Save Price Check")
def save_price_check_tool(product_url: str, price: float, currency: str, variant: str, availability: str, reasoning: str) -> str:
    """Saves the current price check result to the database."""
    # Call core/database.py add_price_check()
    ...

@tool("Send Notification")
def send_notification_tool(product_name: str, old_price: float, new_price: float, drop_percentage: float, product_url: str, reasoning: str) -> str:
    """Sends a price drop alert via console and optionally email."""
    # Call core/notifier.py
    ...
```

#### 5.2.2 `agents/price_agent.py`
Define the CrewAI Agent:

```python
from crewai import Agent

price_watchdog_agent = Agent(
    role="E-commerce Price Intelligence Analyst",
    goal="Accurately track product prices across Pakistani e-commerce platforms by visiting product URLs, extracting the MAIN product's price (ignoring related/sidebar items), detecting variants, comparing with target prices, and alerting users about price drops.",
    backstory="""You are an expert e-commerce analyst specializing in the Pakistani online retail market. 
    You understand the layout of sites like PriceOye, Daraz, Sapphire, and Khaadi. 
    You know that product pages contain many prices — from the main product, related items, ads, and bundles — 
    and your specialty is identifying the CORRECT main product price. 
    You always explain your reasoning clearly so users understand why you extracted a specific price.""",
    tools=[validate_url_tool, scrape_page_tool, extract_product_info_tool, compare_price_tool, check_history_tool, save_price_check_tool, send_notification_tool],
    llm="gemini/gemini-2.5-flash",
    verbose=True,  # Important: shows the agent's reasoning chain in console
    allow_delegation=False,
    max_iter=10
)
```

#### 5.2.3 `agents/tasks.py`
Define the CrewAI Task:

```python
from crewai import Task

def create_price_check_task(product_url: str, target_price: float, currency: str = "PKR"):
    return Task(
        description=f"""
        Perform a complete price check for the following product:
        
        Product URL: {product_url}
        Target Price: {target_price} {currency}
        
        Follow these steps IN ORDER:
        1. Validate that the URL is reachable
        2. Scrape the product page to get its text content  
        3. Extract the product info (name, price, currency, variants, availability) using AI
        4. Compare the extracted price with the target price of {target_price} {currency}
        5. Check the price history to see if the price changed since the last check
        6. Save this price check to the database
        7. If the price dropped to or below the target, OR if the product came back in stock, send a notification
        
        IMPORTANT: You must explain your reasoning at each step. If you see multiple prices on the page, explain WHY you chose the one you did.
        """,
        expected_output="""A detailed price check report containing:
        - Product name and URL
        - Current price and currency
        - Variant being tracked (if applicable)
        - Availability status
        - Comparison with target price (percentage difference)
        - Whether an alert was triggered and why
        - Your reasoning chain (how you identified the correct price)
        """,
        agent=price_watchdog_agent
    )
```

#### 5.2.4 `crew.py`
```python
from crewai import Crew

def run_price_check(product_url: str, target_price: float, currency: str = "PKR"):
    task = create_price_check_task(product_url, target_price, currency)
    
    crew = Crew(
        agents=[price_watchdog_agent],
        tasks=[task],
        verbose=True  # Shows full ReAct chain in console — great for demos
    )
    
    result = crew.kickoff()
    return result
```

### 5.3 Phase 3: Notifications (FR6)

#### 5.3.1 `core/notifier.py`

**Console Notification:**
```
╔══════════════════════════════════════════════════════╗
║              🐕 PRICE WATCHDOG ALERT                ║
╠══════════════════════════════════════════════════════╣
║ Product: Samsung Galaxy S24 Ultra 256GB              ║
║ URL: https://priceoye.pk/...                         ║
║ Previous Price: PKR 279,999                          ║
║ Current Price:  PKR 249,999                          ║
║ Drop: ▼ 10.71%                                      ║
║ Target Price: PKR 250,000 ✅ TARGET REACHED!         ║
║ Status: In Stock                                     ║
║ Time: 2026-05-02 14:30:00                            ║
║                                                      ║
║ Agent Reasoning:                                     ║
║ "I found 7 prices on the page. The main product      ║
║ (Galaxy S24 Ultra) was listed at PKR 249,999 with    ║
║ Add to Cart button. Other prices (PKR 189,999,       ║
║ PKR 159,999) were from the 'Similar Products'        ║
║ section. The 256GB variant was selected as it was    ║
║ pre-selected on the page."                           ║
╚══════════════════════════════════════════════════════╝
```

**Email Notification:**
- Use Python's built-in `smtplib` and `email.mime` modules
- Gmail SMTP: `smtp.gmail.com`, port 587, TLS
- User must create a Gmail App Password (free, no phone verification needed):
  - Go to Google Account → Security → 2-Step Verification → App Passwords
  - Generate a password for "Mail" → "Other (Custom Name)" → "Price Watchdog"
  - Store in `.env` as `GMAIL_APP_PASSWORD`
- Send clean HTML email with all alert details

### 5.4 Phase 4: Streamlit Dashboard

#### 5.4.1 `dashboard/app.py`

The Streamlit dashboard is the **primary demo interface** for the viva. It should have:

**Page 1: Dashboard (Home)**
- Summary cards at top: Total Products Tracked, Active Checks, Alerts Triggered Today, Last Check Time
- Table/list of all tracked products with: Name, Current Price, Target Price, Status (In Stock/Out of Stock), Last Checked, Price Trend arrow (▲/▼)
- Click on a product to see detailed history

**Page 2: Add Product**
- Input field: Product URL
- Input field: Target Price
- Dropdown: Currency (PKR default, USD, EUR, GBP)
- Button: "Start Tracking"
- When clicked: runs the full agent pipeline and shows the agent's reasoning in real-time
- Shows success/error message

**Page 3: Product Detail**
- Product name, URL (clickable link), target price
- **Price trend chart** (Plotly line chart showing price over time)
- Table of all price checks with timestamps
- List of all alerts triggered for this product
- Agent reasoning for each check
- Buttons: Edit Target Price, Pause/Resume, Remove, Export CSV, Export JSON

**Page 4: Alerts**
- Chronological list of all alerts across all products
- Filter by: product, alert type, date range
- Each alert shows: product name, old price, new price, drop %, reasoning, timestamp

**Page 5: Settings**
- Check interval (hours)
- Email notification toggle + email address
- Manual "Check All Now" button

#### 5.4.2 Streamlit Run Command
```bash
streamlit run dashboard/app.py
```

### 5.5 Phase 5: Scheduler & Entry Point

#### 5.5.1 `main.py`
The main entry point supports two modes:

**Mode 1: CLI (one-time check)**
```bash
python main.py check --url "https://priceoye.pk/..." --target 45000
```

**Mode 2: Scheduler (continuous monitoring)**
```bash
python main.py monitor --interval 6
```
This starts a background loop that:
1. Every N hours (default 6), iterate through all active products
2. For each product, run the full agent pipeline
3. Log results to database
4. Send notifications if needed
5. Sleep until next interval

Use the `schedule` library for this.

**Mode 3: Dashboard**
```bash
python main.py dashboard
```
This launches the Streamlit app.

---

## 6. KEY DESIGN DECISIONS & NOTES

### 6.1 Why BeautifulSoup4 over Firecrawl?
The project proposal mentions Firecrawl as an option, but BeautifulSoup4 is preferred because:
- It's completely free with no API limits
- No account signup needed
- Works offline
- Firecrawl's free tier has limited requests
- BS4 is well-documented and battle-tested

### 6.2 Why SQLite over JSON/CSV?
The proposal says "JSON/CSV", but SQLite is better because:
- Built into Python (no installation)
- Supports proper queries (get price history between dates, etc.)
- No file corruption issues with concurrent access
- Still a single file — easy to backup and move
- We ALSO support JSON/CSV **export** from SQLite for the user

### 6.3 Handling JavaScript-Rendered Pages
Some sites (especially Daraz) render content via JavaScript. BeautifulSoup4 cannot execute JS. Options:
- Many sites serve enough static HTML content for price extraction to work
- The LLM is smart enough to extract info even from partially loaded pages
- If a page absolutely needs JS, we can add `requests-html` or `playwright` as a fallback, but start with BS4 and see how far it gets
- For the viva, focus on sites that work well with BS4 (PriceOye, Sapphire, Khaadi usually work fine)

### 6.4 Rate Limiting Awareness
- Gemini free tier: ~10-15 RPM, ~100-1000 RPD
- Each price check uses ~2-3 Gemini API calls (extraction + reasoning)
- With 10 products checked every 6 hours = 4 checks/day × 10 products × 3 calls = 120 calls/day
- This is well within the free tier limits
- Add a 2-second delay between API calls to be safe

### 6.5 Error Handling Philosophy
- Never crash silently — always log what happened
- If scraping fails, log the error and try again next cycle
- If Gemini API is unavailable, use cached last-known price and log a warning
- If email sending fails, fall back to console-only notification
- All errors should be visible in the Streamlit dashboard

---

## 7. DEPENDENCIES (requirements.txt)

```
crewai>=1.14.0
google-genai>=1.0.0
beautifulsoup4>=4.12.0
requests>=2.31.0
streamlit>=1.30.0
plotly>=5.18.0
python-dotenv>=1.0.0
schedule>=1.2.0
lxml>=5.0.0
```

---

## 8. .gitignore

```
# Environment
.env
*.env.local

# Python
__pycache__/
*.pyc
*.pyo
.venv/
venv/
env/

# Database
data/*.db

# Exports
data/exports/*.json
data/exports/*.csv

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db
```

---

## 9. TESTING CHECKLIST

Before submission, verify ALL of these work:

### FR1 Tests:
- [ ] Valid URL (https://priceoye.pk/some-product) → returns "Up"
- [ ] Invalid URL (not-a-url) → returns "Invalid"
- [ ] Down URL (https://nonexistent-site-xyz.com) → returns "Down"
- [ ] URL with timeout → handles gracefully

### FR2 Tests:
- [ ] PriceOye product page → correctly extracts main product price (ignoring "similar" items)
- [ ] Daraz product page → correctly extracts main product price (ignoring "related" items)
- [ ] Sapphire product page → correctly extracts clothing price
- [ ] Page with multiple prices → agent explains WHY it chose the specific price

### FR3 Tests:
- [ ] Product with color variants → detects variants, logs tracked variant
- [ ] Product with storage variants (128GB/256GB) → detects variants, logs tracked variant
- [ ] Product with NO variants → logs "No variants detected"

### FR4 Tests:
- [ ] Price below target → alert triggered with reasoning
- [ ] Price above target → no alert, logged with reasoning
- [ ] Price exactly at target → alert triggered
- [ ] Price increased since last check → logged as increase

### FR5 Tests:
- [ ] "Out of Stock" product → correctly reports availability
- [ ] In-stock product → correctly reports "In Stock"
- [ ] Product goes from "Out of Stock" to "In Stock" → triggers back-in-stock alert

### FR6 Tests:
- [ ] Console notification → displays formatted alert box
- [ ] Email notification → sends clean email (test with your own Gmail)
- [ ] Alert contains all required fields (name, prices, %, link, reasoning)

### FR7 Tests:
- [ ] Price check saved to SQLite → verify with DB browser
- [ ] Price history retrieved correctly → shows chronological trend
- [ ] Export to JSON → valid JSON file
- [ ] Export to CSV → valid CSV file
- [ ] Streamlit chart shows price trend correctly

### Dashboard Tests:
- [ ] Add new product → shows in product list
- [ ] Product detail page → shows price chart
- [ ] Alerts page → shows all triggered alerts
- [ ] Manual "Check Now" → runs agent and updates data
- [ ] Remove product → removed from active tracking

---

## 10. VIVA PREPARATION

### 10.1 Demo Flow (2-3 minutes)
1. Open Streamlit dashboard — show 3-4 products already being tracked with 2+ weeks of price history
2. Show price trend charts for each product
3. Show alert history — "this alert was triggered 3 days ago when the price dropped 12%"
4. Live demo: Paste a NEW product URL → Click "Start Tracking" → Watch the agent reason in real-time in the terminal
5. Show the agent's output: "I found 7 prices on this page. The main product is X at PKR Y. I chose this price because it was associated with the Add to Cart button. Variant: 256GB."

### 10.2 Key Concepts to Explain
- What is a **ReAct agent** and how does it differ from a simple API call?
- What is **tool-calling** — the agent decides WHICH tool to use and in WHAT order
- What is **prompt engineering** — how you designed the extraction prompt to ignore sidebar items
- Why is this better than traditional CSS-selector scraping?
- What happens when a website changes its layout? (Answer: the agent adapts because it reads semantically, not by selectors)

### 10.3 Questions You Might Get
- "What model are you using and why?" → Gemini 2.5 Flash — free tier, fast, good at extraction
- "What if the website blocks your scraper?" → We use realistic headers, and the agent detects and reports errors
- "How accurate is the price extraction?" → Show test results across different sites
- "What are the limitations?" → JS-only sites, CAPTCHA-protected pages, free tier rate limits
- "Can this scale to 100 products?" → Would need paid Gemini tier for rate limits, but architecture supports it

---

## 11. QUICK START COMMANDS

```bash
# 1. Clone and setup
git clone https://github.com/YOUR_USERNAME/price-watchdog.git
cd price-watchdog
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env with your Gemini API key and Gmail credentials

# 3. One-time price check
python main.py check --url "https://priceoye.pk/samsung-galaxy-s24" --target 200000

# 4. Start monitoring (checks every 6 hours)
python main.py monitor --interval 6

# 5. Launch dashboard
python main.py dashboard
# or: streamlit run dashboard/app.py
```

---

## 12. MILESTONE TIMELINE (12 weeks, 5-10 hrs/week)

| Week | Milestone | Deliverable |
|------|-----------|-------------|
| 1-2 | Foundation | config.py, url_validator.py, scraper.py, database.py working |
| 3-4 | LLM Integration | llm_client.py working, extraction prompt tested on 3+ sites |
| 5 | CrewAI Agent | Agent + tools + tasks defined, first full pipeline runs end-to-end |
| 6-7 | Comparison + Alerts | FR4 + FR5 + FR6 complete, console + email alerts working |
| 8-9 | Streamlit Dashboard | All dashboard pages working, charts rendering |
| 10 | Scheduler + Polish | main.py entry point, scheduled monitoring, edge case handling |
| 11 | Testing + Documentation | All FRs tested, SRS document, README written |
| 12 | Viva Prep | Pre-loaded demo data, demo rehearsed, backup video recorded |

---

*This document is complete. An AI coding assistant reading this should be able to build the entire project without needing additional context.*
