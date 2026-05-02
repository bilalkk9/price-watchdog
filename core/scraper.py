"""Web scraping: fetch a product page and return clean text content."""
import logging
import time
from typing import Optional

import requests
from bs4 import BeautifulSoup
from requests.exceptions import ConnectionError, RequestException, Timeout

from config import MAX_PAGE_CHARS, MAX_RETRIES, REQUEST_TIMEOUT

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# Tags whose text content is irrelevant noise
_NOISE_TAGS = {"script", "style", "noscript", "svg", "path", "meta", "link", "head"}


def scrape_url(url: str) -> dict:
    """Fetch a product page and return cleaned text content.

    Returns:
        {
            "success": bool,
            "url": str,
            "title": str | None,
            "meta_description": str | None,
            "text_content": str | None,   # truncated to MAX_PAGE_CHARS
            "error": str | None,
        }
    """
    last_error: Optional[str] = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(
                url,
                headers=_HEADERS,
                timeout=REQUEST_TIMEOUT,
                allow_redirects=True,
            )
            response.raise_for_status()
            return _parse_response(url, response)

        except Timeout:
            last_error = f"Request timed out after {REQUEST_TIMEOUT}s"
        except ConnectionError:
            last_error = "Connection failed"
        except requests.HTTPError as exc:
            last_error = f"HTTP {exc.response.status_code}"
            # Don't retry 4xx — it won't change
            if exc.response.status_code < 500:
                break
        except RequestException as exc:
            last_error = f"Request error: {type(exc).__name__}"

        if attempt < MAX_RETRIES:
            backoff = 2 ** attempt
            logger.warning("scrape attempt %d/%d failed (%s) — retrying in %ds",
                           attempt, MAX_RETRIES, last_error, backoff)
            time.sleep(backoff)

    logger.error("scrape_url failed for %s: %s", url, last_error)
    return {"success": False, "url": url, "title": None,
            "meta_description": None, "text_content": None, "error": last_error}


def _parse_response(url: str, response: requests.Response) -> dict:
    """Parse HTML response into structured text data."""
    # Detect encoding from HTTP header first, fallback to apparent encoding
    if response.encoding and response.encoding.lower() != "iso-8859-1":
        encoding = response.encoding
    else:
        encoding = response.apparent_encoding or "utf-8"

    try:
        html = response.content.decode(encoding, errors="replace")
    except (LookupError, UnicodeDecodeError):
        html = response.content.decode("utf-8", errors="replace")

    soup = BeautifulSoup(html, "lxml")

    # Extract metadata BEFORE removing noise tags (title/meta live in <head>)
    title = soup.title.get_text(strip=True) if soup.title else None

    meta_desc: Optional[str] = None
    meta_tag = soup.find("meta", attrs={"name": "description"})
    if meta_tag and meta_tag.get("content"):
        meta_desc = str(meta_tag["content"]).strip()

    # Remove noise tags in-place
    for tag in soup.find_all(_NOISE_TAGS):
        tag.decompose()

    # Collapse whitespace and truncate
    raw_text = soup.get_text(separator=" ", strip=True)
    text_content = " ".join(raw_text.split())[:MAX_PAGE_CHARS]

    logger.info("scraped %s — %d chars (title: %s)", url, len(text_content), title)
    return {
        "success": True,
        "url": url,
        "title": title,
        "meta_description": meta_desc,
        "text_content": text_content,
        "error": None,
    }
