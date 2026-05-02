import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATABASE_PATH = DATA_DIR / "price_history.db"
EXPORTS_DIR = DATA_DIR / "exports"

DATA_DIR.mkdir(exist_ok=True)
EXPORTS_DIR.mkdir(exist_ok=True)

# API keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

# Scheduler
CHECK_INTERVAL_HOURS = int(os.getenv("CHECK_INTERVAL_HOURS", "6"))

# Scraper / HTTP settings
REQUEST_TIMEOUT = 10          # seconds
MAX_RETRIES = 3
MAX_PAGE_CHARS = 20000        # ~5000 tokens; keeps Gemini free-tier safe

# Gemini model
GEMINI_MODEL = "gemini-2.5-flash"

# Notification
DEFAULT_CURRENCY = "PKR"


def validate_config() -> None:
    """Raise at startup if mandatory env vars are missing."""
    missing = []
    if not GEMINI_API_KEY:
        missing.append("GEMINI_API_KEY")
    if missing:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing)}. "
            "Copy .env.example to .env and fill in the values."
        )
