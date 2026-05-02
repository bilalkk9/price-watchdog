"""CrewAI Task factory — builds a price-check task for the agent."""
from crewai import Task

from agents.price_agent import price_watchdog_agent


def create_price_check_task(
    product_url: str,
    target_price: float,
    currency: str = "PKR",
) -> Task:
    """Return a fully-described Task for one product price check."""
    return Task(
        description=f"""
Perform a complete price check for the following product:

  Product URL  : {product_url}
  Target Price : {target_price:,.0f} {currency}

Follow these steps IN ORDER — do not skip any:

1. **Validate URL** — use the Validate URL tool. If the site is Down or Invalid, stop and report why.
2. **Scrape page** — use the Scrape Product Page tool to get the page text.
3. **Extract product info** — use the Extract Product Info tool on the text content.
   - Identify the MAIN product's price (not related items, not sidebar prices).
   - Note any variants (storage, colour, size) and which one you are tracking.
   - Confirm availability status.
4. **Compare price** — use the Compare Price tool with the extracted price and target {target_price:,.0f} {currency}.
5. **Check history** — use the Check Price History tool to see if the price changed since last check.
6. **Save check** — use the Save Price Check tool to record this check in the database.
7. **Send notification** — if Compare Price returned ALERT (price at or below target),
   OR if the product was previously Out of Stock and is now In Stock,
   use the Send Notification tool.

At every step explain your reasoning, especially if you see multiple prices on the page.
""",
        expected_output="""
A structured price check report containing:
- Product name and URL
- Current price and currency
- Variant being tracked (or "No variants detected")
- Availability status
- Comparison result: current vs target price with percentage difference
- History summary: price trend since last check (or "First check")
- Alert status: triggered or not, and why
- Full reasoning chain: how you identified the correct price among all prices on the page
""",
        agent=price_watchdog_agent,
    )
