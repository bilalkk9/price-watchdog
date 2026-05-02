"""Gemini API wrapper — extraction and reasoning (FR2, FR3)."""
import json
import logging
import re
import time
from typing import Optional

from google import genai
from google.genai import types as genai_types

from config import GEMINI_API_KEY, GEMINI_MODEL

logger = logging.getLogger(__name__)

_BACKOFF_SECONDS = (2, 4, 8)   # three retries with exponential backoff

# Lazy singleton — created on first use so tests can avoid needing a real key
_client: Optional[genai.Client] = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        if not GEMINI_API_KEY:
            raise EnvironmentError(
                "GEMINI_API_KEY is not set. Add it to your .env file."
            )
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client


# ── Low-level call ─────────────────────────────────────────────────────────────

def ask_gemini(prompt: str, system_instruction: Optional[str] = None) -> str:
    """Send a prompt to Gemini and return the text response.

    Retries on rate-limit (429) with exponential backoff.
    """
    client = _get_client()
    config_kwargs: dict = {}
    if system_instruction:
        config_kwargs["system_instruction"] = system_instruction

    for attempt, wait in enumerate((*_BACKOFF_SECONDS, None), start=1):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config=genai_types.GenerateContentConfig(**config_kwargs)
                if config_kwargs
                else None,
            )
            time.sleep(2)   # respect free-tier rate limit between calls
            return response.text or ""

        except Exception as exc:
            status = getattr(exc, "status_code", None) or getattr(
                getattr(exc, "response", None), "status_code", None
            )
            if status == 429 and wait is not None:
                logger.warning("Gemini rate-limited (attempt %d) — waiting %ds", attempt, wait)
                time.sleep(wait)
                continue
            logger.error("Gemini API error: %s", exc)
            raise

    raise RuntimeError("Gemini API failed after all retries")


# ── Extraction prompt ──────────────────────────────────────────────────────────

_EXTRACTION_SYSTEM = (
    "You are a product price extraction specialist for Pakistani e-commerce websites. "
    "You respond ONLY with valid JSON — no markdown, no backticks, no explanation."
)

_EXTRACTION_PROMPT = """\
You are given the text content of an e-commerce product page. Extract ONLY the MAIN product's \
information. Ignore sidebar items, related products, ads, "you may also like" sections, \
and recommended products.

RULES:
- The main product is typically named in the page title and has an "Add to Cart" button nearby.
- If there are two prices (strikethrough + sale), current_price is the LOWER (sale) price.
- current_price must be a NUMBER with no currency symbols or commas.
- Return ONLY the JSON object below — no other text.

PAGE CONTENT:
{page_content}

Respond with ONLY this JSON (fill every field):
{{
  "product_name": "...",
  "current_price": 0,
  "original_price": null,
  "currency": "PKR",
  "availability": "In Stock",
  "variants": [],
  "tracked_variant": null
}}

availability must be one of: "In Stock", "Out of Stock", "Limited Stock", "Pre-Order", "Unknown"
"""


def extract_product_info(page_content: str) -> dict:
    """Use Gemini to extract product name, price, variants, and availability.

    Returns a validated dict. Raises ValueError if the response cannot be parsed.
    """
    if not page_content or not page_content.strip():
        raise ValueError("page_content is empty")

    prompt = _EXTRACTION_PROMPT.format(page_content=page_content[:20_000])
    raw_response = ask_gemini(prompt, system_instruction=_EXTRACTION_SYSTEM)

    data = _parse_json_response(raw_response)
    _validate_extraction(data)
    return data


def _parse_json_response(text: str) -> dict:
    """Extract JSON from LLM response, tolerating minor markdown wrapping."""
    text = text.strip()

    # Strip ```json ... ``` fences if the model adds them despite instructions
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1)

    # Try direct parse first; if that fails, find first {...} block
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise ValueError(f"No JSON object found in LLM response: {text[:200]!r}")


def _validate_extraction(data: dict) -> None:
    """Raise ValueError if required fields are missing or malformed."""
    if not data.get("product_name"):
        raise ValueError("Extraction missing product_name")

    price = data.get("current_price")
    if price is None:
        raise ValueError("Extraction missing current_price")
    try:
        data["current_price"] = float(price)
    except (TypeError, ValueError):
        raise ValueError(f"current_price is not numeric: {price!r}")

    orig = data.get("original_price")
    if orig is not None:
        try:
            data["original_price"] = float(orig)
        except (TypeError, ValueError):
            data["original_price"] = None

    valid_statuses = {"In Stock", "Out of Stock", "Limited Stock", "Pre-Order", "Unknown"}
    if data.get("availability") not in valid_statuses:
        data["availability"] = "Unknown"

    if not isinstance(data.get("variants"), list):
        data["variants"] = []
