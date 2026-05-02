"""Crew orchestrator — assembles agents + tasks and kicks off a price check."""
import logging

from crewai import Crew, Process

from agents.price_agent import price_watchdog_agent
from agents.tasks import create_price_check_task
from core.database import add_product, get_product_by_url, init_db

logger = logging.getLogger(__name__)


def run_price_check(
    product_url: str,
    target_price: float,
    currency: str = "PKR",
) -> str:
    """Run a full agent price check for one product URL.

    Adds the product to the database if not already tracked.
    Returns the agent's final report as a string.
    """
    if not product_url or not product_url.startswith(("http://", "https://")):
        raise ValueError(f"Invalid URL: {product_url!r}")
    if target_price <= 0:
        raise ValueError(f"target_price must be positive, got {target_price}")

    init_db()

    # Register product if new
    if not get_product_by_url(product_url):
        pid = add_product(product_url, target_price, currency)
        logger.info("registered new product id=%d url=%s", pid, product_url)
    else:
        logger.info("product already tracked: %s", product_url)

    task = create_price_check_task(product_url, target_price, currency)

    crew = Crew(
        agents=[price_watchdog_agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
    )

    result = crew.kickoff()
    return str(result)
