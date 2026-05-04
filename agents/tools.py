"""CrewAI tool definitions — callable actions the agent uses during reasoning."""
import json
import logging
from typing import Optional

from crewai.tools import tool

from config import GMAIL_ADDRESS
from core.database import (
    add_alert,
    add_price_check,
    get_all_products,
    get_latest_price,
    get_price_history,
    get_product_by_url,
    init_db,
    update_product,
)
from core.llm_client import extract_product_info
from core.notifier import notify
from core.scraper import scrape_url
from core.url_validator import validate_url

logger = logging.getLogger(__name__)

# Ensure DB is ready whenever tools are imported
init_db()


# ── FR1: URL validation ────────────────────────────────────────────────────────

@tool("Validate URL")
def validate_url_tool(url: str) -> str:
    """Check if a product URL is valid and the site is reachable.
    Returns status: Up, Down, or Invalid."""
    result = validate_url(url)
    return (
        f"URL Status: {result['status']} | "
        f"Valid: {result['valid']} | "
        f"HTTP: {result.get('status_code', 'N/A')} | "
        f"Response time: {result.get('response_time_ms', 'N/A')}ms | "
        f"Message: {result['message']}"
    )


# ── FR2: Scraping ──────────────────────────────────────────────────────────────

@tool("Scrape Product Page")
def scrape_page_tool(url: str) -> str:
    """Fetch the full text content of a product page for analysis.
    Returns page title and text content (scripts/ads stripped)."""
    result = scrape_url(url)
    if not result["success"]:
        return f"SCRAPE_FAILED: {result['error']}"
    return json.dumps({
        "title": result["title"],
        "meta_description": result["meta_description"],
        "text_content": result["text_content"],
    })


# ── FR2 + FR3: Extraction ──────────────────────────────────────────────────────

@tool("Extract Product Info")
def extract_product_info_tool(page_content: str) -> str:
    """Use AI to extract product name, current price, currency, variants, and
    availability from page text. Ignores sidebar/related items."""
    try:
        data = extract_product_info(page_content)
        return json.dumps(data)
    except ValueError as exc:
        return f"EXTRACTION_FAILED: {exc}"


# ── FR4: Price comparison ──────────────────────────────────────────────────────

@tool("Compare Price")
def compare_price_tool(current_price: float, target_price: float, currency: str = "PKR") -> str:
    """Compare the extracted price against the user's target price.
    Returns percentage difference and whether an alert should be triggered."""
    if target_price <= 0:
        return "ERROR: target_price must be positive"

    diff_pct = ((target_price - current_price) / target_price) * 100
    drop_pct = ((current_price - target_price) / target_price) * 100  # positive = above target

    if current_price <= target_price:
        action = "ALERT"
        summary = (
            f"TARGET REACHED — current {currency} {current_price:,.0f} is "
            f"{abs(diff_pct):.1f}% below target {currency} {target_price:,.0f}"
        )
    else:
        action = "NO_ALERT"
        summary = (
            f"Price {currency} {current_price:,.0f} is {drop_pct:.1f}% ABOVE "
            f"target {currency} {target_price:,.0f} — no alert needed"
        )

    return json.dumps({
        "action": action,
        "current_price": current_price,
        "target_price": target_price,
        "currency": currency,
        "difference_pct": round(diff_pct, 2),
        "summary": summary,
    })


# ── FR7: History ───────────────────────────────────────────────────────────────

@tool("Check Price History")
def check_history_tool(product_url: str) -> str:
    """Retrieve recent price history for a product to detect trends.
    Returns last 5 price checks or 'No history' if first check."""
    product = get_product_by_url(product_url)
    if not product:
        return "No history found — this is the first check for this product."

    history = get_price_history(product["id"], limit=5)
    if not history:
        return "Product exists in database but no price checks recorded yet."

    lines = [f"Last {len(history)} price checks (newest first):"]
    for h in history:
        lines.append(
            f"  • {h['checked_at']} — {h['currency']} {h['price']:,.0f} "
            f"| {h['availability']} | variant: {h['variant'] or 'N/A'}"
        )
    return "\n".join(lines)


# ── FR7: Save check ────────────────────────────────────────────────────────────

@tool("Save Price Check")
def save_price_check_tool(
    product_url: str,
    product_name: str,
    price: float,
    currency: str,
    variant: str,
    availability: str,
    reasoning: str,
) -> str:
    """Save the result of this price check to the database. Also updates the product name."""
    product = get_product_by_url(product_url)
    if not product:
        return f"SAVE_FAILED: Product not found for URL {product_url!r}. Add it first."

    # Update product name if we now know it and it was missing
    if product_name and not product.get("name"):
        update_product(product["id"], name=product_name)

    check_id = add_price_check(
        product_id=product["id"],
        price=price,
        currency=currency,
        variant=variant if variant else None,
        availability=availability,
        reasoning=reasoning,
        raw=None,
    )
    return f"Saved price check #{check_id} — {currency} {price:,.0f} | {availability}"


# ── FR6: Notification ──────────────────────────────────────────────────────────

@tool("Send Notification")
def send_notification_tool(
    product_name: str,
    product_url: str,
    old_price: float,
    new_price: float,
    drop_percentage: float,
    target_price: float,
    availability: str,
    reasoning: str,
    currency: str = "PKR",
) -> str:
    """Send a price drop or back-in-stock alert via console (and email if configured)."""
    old = old_price if old_price > 0 else None
    channels = notify(
        product_name=product_name,
        product_url=product_url,
        old_price=old,
        new_price=new_price,
        drop_percentage=drop_percentage,
        target_price=target_price,
        availability=availability,
        reasoning=reasoning,
        recipient_email=GMAIL_ADDRESS if GMAIL_ADDRESS else None,
        currency=currency,
    )

    # Save the alert to the database so the Alerts page shows it
    product = get_product_by_url(product_url)
    if product:
        alert_type = "target_reached" if new_price <= target_price else "back_in_stock"
        add_alert(
            product_id=product["id"],
            alert_type=alert_type,
            old_price=old,
            new_price=new_price,
            drop_pct=drop_percentage,
            message=reasoning[:500],
            sent_via=channels,
        )

    return f"Notification sent via: {channels}"
