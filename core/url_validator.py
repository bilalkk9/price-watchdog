import time
import urllib.parse

import requests
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects

from config import REQUEST_TIMEOUT

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def validate_url(url: str) -> dict:
    """
    Check URL format and reachability.

    Returns:
        {
            "valid": bool,
            "status": "Up" | "Down" | "Invalid",
            "status_code": int | None,
            "response_time_ms": float | None,
            "message": str,
        }
    """
    # ── 1. Format check ──────────────────────────────────────────────────────
    parsed = urllib.parse.urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return {
            "valid": False,
            "status": "Invalid",
            "status_code": None,
            "response_time_ms": None,
            "message": f"Invalid URL format: '{url}' — must start with http:// or https://",
        }
    if parsed.scheme not in ("http", "https"):
        return {
            "valid": False,
            "status": "Invalid",
            "status_code": None,
            "response_time_ms": None,
            "message": f"Unsupported scheme '{parsed.scheme}' — only http/https are allowed",
        }

    # ── 2. Reachability check (HEAD first, GET fallback) ─────────────────────
    start = time.monotonic()
    try:
        response = requests.head(
            url,
            headers=_HEADERS,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True,
        )
        # Some servers return 405 Method Not Allowed for HEAD — fall back to GET
        if response.status_code == 405:
            response = requests.get(
                url,
                headers=_HEADERS,
                timeout=REQUEST_TIMEOUT,
                allow_redirects=True,
                stream=True,   # don't download the body
            )
            response.close()

        elapsed_ms = (time.monotonic() - start) * 1000

        if response.status_code < 400:
            return {
                "valid": True,
                "status": "Up",
                "status_code": response.status_code,
                "response_time_ms": round(elapsed_ms, 1),
                "message": f"URL is reachable (HTTP {response.status_code}, {elapsed_ms:.0f}ms)",
            }
        else:
            return {
                "valid": False,
                "status": "Down",
                "status_code": response.status_code,
                "response_time_ms": round(elapsed_ms, 1),
                "message": f"URL returned HTTP {response.status_code}",
            }

    except Timeout:
        elapsed_ms = (time.monotonic() - start) * 1000
        return {
            "valid": False,
            "status": "Down",
            "status_code": None,
            "response_time_ms": round(elapsed_ms, 1),
            "message": f"URL timed out after {REQUEST_TIMEOUT}s",
        }
    except ConnectionError as exc:
        return {
            "valid": False,
            "status": "Down",
            "status_code": None,
            "response_time_ms": None,
            "message": f"Connection error: {exc}",
        }
    except TooManyRedirects:
        return {
            "valid": False,
            "status": "Down",
            "status_code": None,
            "response_time_ms": None,
            "message": "Too many redirects",
        }
    except Exception as exc:
        return {
            "valid": False,
            "status": "Down",
            "status_code": None,
            "response_time_ms": None,
            "message": f"Unexpected error: {exc}",
        }
